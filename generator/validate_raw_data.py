from __future__ import annotations
from pathlib import Path
import json, sys, math
import pandas as pd
import numpy as np

PACKAGE=Path(__file__).resolve().parent
RAW=PACKAGE/'raw'
MANIFEST=json.loads((PACKAGE/'manifest.json').read_text())
END=pd.Timestamp('2025-12-31T23:59:59Z')

checks=[]
violations=[]
warnings=[]
metrics={}

def ok(name, detail=''):
    checks.append({'check':name,'status':'PASS','detail':detail})
def fail(name, detail):
    checks.append({'check':name,'status':'FAIL','detail':detail}); violations.append(f'{name}: {detail}')
def warn(name, detail):
    checks.append({'check':name,'status':'WARN','detail':detail}); warnings.append(f'{name}: {detail}')

def read_num(n):
    item=next(x for x in MANIFEST['datasets'] if x['number']==n)
    p=PACKAGE/item['path']
    if item['format']=='jsonl': return pd.read_json(p, lines=True)
    return pd.read_csv(p)

def dt(s):
    x = pd.to_datetime(s, utc=True, errors='coerce')
    return x.dt.as_unit('us') if isinstance(x, pd.Series) else x.as_unit('us')

def overlap_count(df, group_cols, start_col='valid_from', end_col='valid_to'):
    if df.empty: return 0
    x=df.copy(); x['start_ts']=dt(x[start_col]); x['end_ts']=dt(x[end_col]).fillna(END+pd.Timedelta(seconds=1))
    bad=0
    for _,g in x.sort_values(group_cols+['start_ts']).groupby(group_cols, dropna=False):
        prev=None
        for r in g.itertuples():
            s=getattr(r,'start_ts'); e=getattr(r,'end_ts')
            if pd.isna(s) or pd.isna(e) or e<s: bad+=1
            if prev is not None and s < prev: bad+=1
            prev=max(prev,e) if prev is not None else e
    return bad

def within_any(start,end, intervals):
    for s,e in intervals:
        if start>=s and end<=e: return True
    return False

# 1. Structural presence + fields
expected=set(range(1,50)); got={x['number'] for x in MANIFEST['datasets']}
if got==expected and MANIFEST.get('datasets_generated')==49: ok('49 datasets exist','all canonical dataset numbers 1-49 present')
else: fail('49 datasets exist',f'missing={sorted(expected-got)}, extra={sorted(got-expected)}')
D={}
for item in MANIFEST['datasets']:
    p=PACKAGE/item['path']
    if not p.exists(): fail(f"dataset {item['number']} file",'missing file'); continue
    d=read_num(item['number'])
    D[item['number']]=d
    missing=[c for c in item['required_fields'] if c not in d.columns]
    if missing: fail(f"dataset {item['number']} required fields",str(missing))
    else: ok(f"dataset {item['number']} required fields",f"{len(d)} rows")

# Datasets are loaded once and reused by deeper validation. This avoids a
# second full read of the large JSONL event sources at canonical scale.

# Referential helper
refs={
3:[('user_id',2,'user_id',False),('account_id',1,'account_id',False)],
4:[('membership_id',3,'membership_id',False)],5:[('membership_id',3,'membership_id',False)],
6:[('account_id',1,'account_id',False)],7:[('account_id',1,'account_id',False)],
8:[('membership_id',3,'membership_id',False),('user_id',2,'user_id',False),('account_id',1,'account_id',False)],
9:[('account_id',1,'account_id',False)],10:[('website_id',9,'website_id',False)],11:[('page_id',10,'page_id',False)],
12:[('page_id',10,'page_id',False)],13:[('content_item_id',11,'content_item_id',False)],14:[('website_id',9,'website_id',False)],
15:[('website_id',9,'website_id',False)],16:[('website_id',9,'website_id',False)],18:[('plan_id',43,'plan_id',False),('feature_id',17,'feature_id',False)],
19:[('website_id',9,'website_id',False),('feature_id',17,'feature_id',False)],20:[('website_id',9,'website_id',False),('feature_id',17,'feature_id',False)],
21:[('website_id',9,'website_id',False)],22:[('website_id',9,'website_id',False)],23:[('invitation_id',22,'invitation_id',False)],
24:[('website_id',9,'website_id',False),('member_id',21,'member_id',False),('invitation_id',22,'invitation_id',True)],25:[('member_id',21,'member_id',False)],
26:[('member_id',21,'member_id',False)],27:[('member_id',21,'member_id',False),('page_id',10,'page_id',False)],28:[('comment_id',27,'comment_id',False)],
29:[('member_id',21,'member_id',False),('page_id',10,'page_id',False)],30:[('rating_id',29,'rating_id',False)],
31:[('user_id',2,'user_id',False),('account_id',1,'account_id',False),('website_id',9,'website_id',True),('feature_id',17,'feature_id',True)],
32:[('website_id',9,'website_id',False)],33:[('visitor_id',32,'visitor_id',False),('website_id',9,'website_id',False)],34:[('session_id',33,'session_id',False)],
35:[('session_id',33,'session_id',False)],36:[('visitor_id',32,'visitor_id',False),('member_id',21,'member_id',False),('website_id',9,'website_id',False)],
37:[('session_id',33,'session_id',False),('member_id',21,'member_id',False)],38:[('session_id',33,'session_id',False),('page_id',10,'page_id',True),('content_item_id',11,'content_item_id',True)],
39:[('resulting_account_id',1,'account_id',True)],40:[('signup_journey_id',39,'signup_journey_id',False)],41:[('signup_journey_id',39,'signup_journey_id',False)],
42:[('website_id',9,'website_id',False),('member_id',21,'member_id',True)],44:[('account_id',1,'account_id',False),('plan_id',43,'plan_id',False)],
45:[('account_id',1,'account_id',False)],46:[('account_id',1,'account_id',False),('from_plan_id',43,'plan_id',True),('to_plan_id',43,'plan_id',True)],
47:[('account_id',1,'account_id',False)],48:[('account_id',1,'account_id',False),('requester_user_id',2,'user_id',False),('website_id',9,'website_id',True)],
49:[('support_request_id',48,'support_request_id',False)]}
ref_bad=0
for n, specs in refs.items():
    for col,tn,tcol,opt in specs:
        vals=D[n][col]
        if opt: vals=vals.dropna()
        target=set(D[tn][tcol].dropna().astype(str))
        bad=(~vals.astype(str).isin(target)).sum()
        ref_bad+=int(bad)
if ref_bad: fail('mandatory references resolve',f'{ref_bad} unresolved references')
else: ok('mandatory references resolve','0 unresolved mandatory references')

# Temporal overlaps
period_specs=[(4,['membership_id']),(5,['membership_id']),(6,['account_id']),(15,['website_id']),(16,['website_id']),(18,['plan_id','feature_id']),(19,['website_id','feature_id']),(25,['member_id']),(36,['visitor_id','member_id','website_id']),(44,['account_id']),(45,['account_id'])]
total_overlap=0
for n,g in period_specs:
    b=overlap_count(D[n],g); total_overlap+=b
if total_overlap: fail('period overlap validation',f'{total_overlap} invalid/overlapping periods')
else: ok('period overlap validation','0 invalid overlaps')

# Role periods inside Membership periods
mp=D[4].copy(); mp['start_ts']=dt(mp.valid_from); mp['end_ts']=dt(mp.valid_to).fillna(END+pd.Timedelta(seconds=1))
mpmap={k:list(zip(g.start_ts,g.end_ts)) for k,g in mp.groupby('membership_id')}
rp=D[5].copy(); rp['start_ts']=dt(rp.valid_from); rp['end_ts']=dt(rp.valid_to).fillna(END+pd.Timedelta(seconds=1))
bad=0
for r in rp.itertuples():
    if not within_any(r.start_ts,r.end_ts,mpmap.get(r.membership_id,[])): bad+=1
if bad: fail('role periods within membership periods',f'{bad} role periods outside membership validity')
else: ok('role periods within membership periods','all role periods contained')

# Subscription starts Free and no overlaps already checked
sp=D[44].copy(); sp['start_ts']=dt(sp.valid_from)
first=sp.sort_values('start_ts').groupby('account_id').first()
bad=(first.plan_id!='PLAN_FREE').sum()
if bad: fail('subscription history begins Free',f'{bad} accounts do not begin Free')
else: ok('subscription history begins Free','all accounts begin on Free')

# Refund after successful payment
pay=D[47].copy(); pay['event_ts']=dt(pay.event_time)
succ=pay[pay.event_type=='payment_succeeded'].set_index('payment_ref')['event_ts'].to_dict()
bad=0
for r in pay[pay.event_type=='payment_refunded'].itertuples():
    if pd.isna(r.original_payment_ref) or r.original_payment_ref not in succ or succ[r.original_payment_ref]>=r.event_ts: bad+=1
if bad: fail('refund follows prior successful payment',f'{bad} invalid refunds')
else: ok('refund follows prior successful payment','all refunds reference earlier success')

# Same-Website contribution rules
member_web=D[21].set_index('member_id').website_id.to_dict(); page_web=D[10].set_index('page_id').website_id.to_dict()
bad=sum(member_web.get(r.member_id)!=page_web.get(r.page_id) for r in D[27].itertuples())+sum(member_web.get(r.member_id)!=page_web.get(r.page_id) for r in D[29].itertuples())
if bad: fail('comment/rating same-Website rule',f'{bad} violations')
else: ok('comment/rating same-Website rule','0 violations')

# Session visitor + Website consistency
visitor_web=D[32].set_index('visitor_id').website_id.to_dict()
bad=sum(visitor_web.get(r.visitor_id)!=r.website_id for r in D[33].itertuples())
if bad: fail('session visitor/Website consistency',f'{bad} violations')
else: ok('session visitor/Website consistency','0 violations')

# Audience event target Website consistency (vectorized at full scale; raw duplicates allowed)
session_web=D[33].set_index('session_id').website_id
content_page=D[11].set_index('content_item_id').page_id
page_web_s=D[10].set_index('page_id').website_id
content_web=content_page.map(page_web_s)
aud=D[38].drop_duplicates('event_id')
sw=aud['session_id'].map(session_web)
page_mask=aud['page_id'].notna()
content_mask=aud['content_item_id'].notna()
bad_page=(aud.loc[page_mask,'page_id'].map(page_web_s).to_numpy()!=sw.loc[page_mask].to_numpy()).sum()
bad_content=(aud.loc[content_mask,'content_item_id'].map(content_web).to_numpy()!=sw.loc[content_mask].to_numpy()).sum()
bad=int(bad_page+bad_content)
if bad: fail('audience targets same Website as Session',f'{bad} target violations')
else: ok('audience targets same Website as Session','0 violations')

# Support requester membership valid at opening + Website consistency
memrel=D[3].set_index('membership_id')[['user_id','account_id']]
mp2=D[4].copy(); mp2['start_ts']=dt(mp2.valid_from); mp2['end_ts']=dt(mp2.valid_to).fillna(END+pd.Timedelta(seconds=1)); mp2=mp2.join(memrel,on='membership_id')
sup_open=D[49][D[49].event_type=='support_request_opened'].copy(); sup_open['event_ts']=dt(sup_open.event_time)
open_map=sup_open.set_index('support_request_id')['event_ts'].to_dict(); website_account=D[9].set_index('website_id').account_id.to_dict()
bad_mem=0; bad_web=0
for r in D[48].itertuples():
    t=open_map.get(r.support_request_id)
    g=mp2[(mp2.user_id==r.requester_user_id)&(mp2.account_id==r.account_id)]
    if t is None or not ((g.start_ts<=t)&(t<g.end_ts)).any(): bad_mem+=1
    if pd.notna(r.website_id) and website_account.get(r.website_id)!=r.account_id: bad_web+=1
if bad_mem: fail('support requester valid at opening time',f'{bad_mem} violations')
else: ok('support requester valid at opening time','0 violations')
if bad_web: fail('support Website belongs to request Account',f'{bad_web} violations')
else: ok('support Website belongs to request Account','0 violations')

# Feature Usage Plan -> Entitlement -> Enablement + membership validity
# Full-scale implementation uses grouped interval search rather than filtering
# several DataFrames once per individual usage event.
prod=D[31].drop_duplicates('event_id')
usage=prod[prod.event_type=='feature_used'].copy().reset_index(drop=True)
usage['event_ts']=dt(usage.event_time)
sp2=D[44].copy(); sp2['start_ts']=dt(sp2.valid_from); sp2['end_ts']=dt(sp2.valid_to).fillna(END+pd.Timedelta(seconds=1))
ent=D[18].copy(); ent['start_ts']=dt(ent.valid_from); ent['end_ts']=dt(ent.valid_to).fillna(END+pd.Timedelta(seconds=1))
en=D[19].copy(); en['start_ts']=dt(en.valid_from); en['end_ts']=dt(en.valid_to).fillna(END+pd.Timedelta(seconds=1))

def interval_arrays(df, group_cols, payload=None):
    out={}
    cols=group_cols if isinstance(group_cols,list) else [group_cols]
    grouper=cols[0] if len(cols)==1 else cols
    for key,g in df.sort_values(cols+['start_ts']).groupby(grouper, sort=False, dropna=False):
        st=g['start_ts'].astype('int64').to_numpy()
        ed=g['end_ts'].astype('int64').to_numpy()
        pl=g[payload].to_numpy() if payload else None
        out[key]=(st,ed,pl)
    return out

def mark_interval_membership(events, key_cols, groups, payload=False):
    ev_ns=events['event_ts'].astype('int64').to_numpy()
    okarr=np.zeros(len(events),dtype=bool)
    vals=np.empty(len(events),dtype=object) if payload else None
    cols=key_cols if isinstance(key_cols,list) else [key_cols]
    grouper=cols[0] if len(cols)==1 else cols
    for key,idx in events.groupby(grouper,sort=False,dropna=False).indices.items():
        g=groups.get(key)
        if g is None: continue
        starts,ends,pl=g
        ix=np.asarray(idx,dtype=int); times=ev_ns[ix]
        pos=np.searchsorted(starts,times,side='right')-1
        valid=pos>=0
        safe=np.maximum(pos,0)
        valid &= times < ends[safe]
        okarr[ix]=valid
        if payload:
            vv=np.empty(len(ix),dtype=object); vv[:]=None
            vv[valid]=pl[safe[valid]]
            vals[ix]=vv
    return (okarr,vals) if payload else okarr

# applicable Subscription Plan at usage time
sp_groups=interval_arrays(sp2,'account_id','plan_id')
plan_ok,plans_at_use=mark_interval_membership(usage,'account_id',sp_groups,payload=True)
usage['plan_id_at_use']=plans_at_use

# entitlement at usage time for the resolved Plan × Feature
ent_groups=interval_arrays(ent,['plan_id','feature_id'])
ent_key_events=usage.copy()
ent_key_events['plan_id_at_use']=usage['plan_id_at_use']
ent_ok=np.zeros(len(usage),dtype=bool)
ev_ns=usage['event_ts'].astype('int64').to_numpy()
for key,idx in ent_key_events.groupby(['plan_id_at_use','feature_id'],sort=False,dropna=False).indices.items():
    if key[0] is None or pd.isna(key[0]): continue
    g=ent_groups.get(key)
    if g is None: continue
    starts,ends,_=g; ix=np.asarray(idx,dtype=int); times=ev_ns[ix]
    pos=np.searchsorted(starts,times,side='right')-1; safe=np.maximum(pos,0)
    ent_ok[ix]=(pos>=0)&(times<ends[safe])

# Website × Feature enablement validity
en_groups=interval_arrays(en,['website_id','feature_id'])
enable_ok=mark_interval_membership(usage,['website_id','feature_id'],en_groups)

# SaaS User membership validity for Account at event time
mem_groups=interval_arrays(mp2,['user_id','account_id'])
member_ok=mark_interval_membership(usage,['user_id','account_id'],mem_groups)

bad=int((~(plan_ok & ent_ok & enable_ok & member_ok)).sum())
if bad: fail('Feature Usage respects Plan + Entitlement + Enablement',f'{bad} violations')
else: ok('Feature Usage respects Plan + Entitlement + Enablement','0 violations')

# Website Live has a valid address at relevant time
addr=D[16].copy(); addr['start_ts']=dt(addr.valid_from); addr['end_ts']=dt(addr.valid_to).fillna(END+pd.Timedelta(seconds=1))
live=D[15].copy(); live['start_ts']=dt(live.valid_from); live['end_ts']=dt(live.valid_to).fillna(END+pd.Timedelta(seconds=1))
bad=0
for r in live.itertuples():
    g=addr[addr.website_id==r.website_id].sort_values('start_ts')
    cursor=r.start_ts
    for a in g.itertuples():
        if a.end_ts <= cursor: continue
        if a.start_ts > cursor: break
        cursor=max(cursor,a.end_ts)
        if cursor >= r.end_ts: break
    if cursor < r.end_ts: bad+=1
if bad: fail('Live Website has valid Address',f'{bad} live periods contain an address gap')
else: ok('Live Website has valid Address','all live periods continuously address-covered')

# Distribution sanity
accounts=len(D[1]); websites=len(D[9])
published=D[14][D[14].event_type=='published'].website_id.nunique()/websites
spx=D[44].copy(); spx['start_ts']=dt(spx.valid_from); final=spx.sort_values('start_ts').groupby('account_id').tail(1).plan_id.value_counts(normalize=True)
ever=(D[44].plan_id!='PLAN_FREE').groupby(D[44].account_id).any().sum()/accounts
traf=D[35].traffic_source.value_counts(normalize=True)
ret=(D[33].groupby('visitor_id').size()>1).mean()
mem_adopt=D[21].website_id.nunique()/max(1,D[14][D[14].event_type=='published'].website_id.nunique())
payment_attempts=D[47][D[47].event_type.isin(['payment_succeeded','payment_failed'])]
payfail=(payment_attempts.event_type=='payment_failed').mean() if len(payment_attempts) else 0
succ_n=(D[47].event_type=='payment_succeeded').sum(); refund=(D[47].event_type=='payment_refunded').sum()/max(1,succ_n)
support_usage=D[48].account_id.nunique()/accounts
metrics.update({'published_websites':published,'ever_paid_accounts':ever,'final_plan_free':final.get('PLAN_FREE',0),'final_plan_standard':final.get('PLAN_STANDARD',0),'final_plan_premium':final.get('PLAN_PREMIUM',0),'returning_visitors':ret,'membership_adoption':mem_adopt,'payment_failure_rate':payfail,'refund_rate_of_success':refund,'support_account_usage':support_usage})
for k,v in traf.items(): metrics[f'traffic_{k}']=v
ranges={'published_websites':(0.62,0.78),'ever_paid_accounts':(0.25,0.35),'final_plan_free':(0.66,0.82),'final_plan_standard':(0.14,0.27),'final_plan_premium':(0.025,0.11),'returning_visitors':(0.35,0.45),'membership_adoption':(0.18,0.30),'payment_failure_rate':(0.02,0.07),'refund_rate_of_success':(0.005,0.03),'support_account_usage':(0.22,0.32),'traffic_search':(0.36,0.48),'traffic_direct':(0.21,0.33),'traffic_social':(0.13,0.23),'traffic_referral':(0.09,0.18)}
dbad=[]
for k,(lo,hi) in ranges.items():
    v=metrics.get(k,float('nan'))
    if not (lo<=v<=hi): dbad.append(f'{k}={v:.3f} outside [{lo},{hi}]')
if dbad: fail('distribution sanity','; '.join(dbad))
else: ok('distribution sanity','all key distributions within tolerance')

# Controlled imperfection presence
incomplete=D[39].resulting_account_id.isna().sum()
anonymous=len(D[33])-D[37].session_id.nunique()
late=0
if len(D[37]):
    ses_end=dt(D[34][D[34].event_type=='session_ended'].drop_duplicates('session_id').set_index('session_id').event_time)
    attr=D[37].copy(); attr_ts=dt(attr.attributed_at); end_ts=attr.session_id.map(ses_end)
    late=int((attr_ts > end_ts + pd.Timedelta(days=1)).sum())
optional_support=D[48].website_id.isna().sum()
failed_reg=(D[42].event_type=='member_registration_failed').sum()
failed_pay=(D[47].event_type=='payment_failed').sum()
friction=(D[38].event_type=='failure_friction').sum()
open_periods=sum(D[n].valid_to.isna().sum() for n in [4,5,6,15,16,18,19,25,36,44,45] if 'valid_to' in D[n].columns)
duplicates=sum(D[n].event_id.duplicated().sum() for n in [31,34,38,40,42])
mess={'incomplete_signup_journeys':int(incomplete),'anonymous_sessions':int(anonymous),'late_member_attributions':int(late),'support_missing_optional_website':int(optional_support),'failed_registrations':int(failed_reg),'failed_payments':int(failed_pay),'friction_events':int(friction),'open_periods':int(open_periods),'duplicate_tracking_rows':int(duplicates)}
metrics['controlled_imperfection']=mess
if all(v>0 for v in mess.values()): ok('controlled imperfection present',json.dumps(mess))
else: fail('controlled imperfection present',f'missing one or more expected messiness types: {mess}')

# Scale / row count informational sanity
manifest_rows={x['number']:x['rows'] for x in MANIFEST['datasets']}
scale=float(MANIFEST['scale_factor'])
scale_targets={1:2000,2:2700,9:3250,10:14500,11:6500,21:15000,27:18000,29:12000,31:450000,32:90000,33:240000,38:1100000,39:3300,47:7000,48:1200}
scale_info={str(n):{'actual':manifest_rows[n],'scaled_target':round(t*scale)} for n,t in scale_targets.items()}
metrics['scale_row_targets']=scale_info
# Payment is rough-order target; warn only if outside 40%-160% of scaled target.
rowwarn=[]
for n,t in scale_targets.items():
    target=t*scale; actual=manifest_rows[n]
    lo,hi=(0.4*target,1.6*target) if n==47 else (0.75*target,1.25*target)
    if not(lo<=actual<=hi): rowwarn.append(f'dataset {n}: {actual} vs target~{target:.0f}')
if rowwarn: warn('scale row-count sanity','; '.join(rowwarn))
else: ok('scale row-count sanity','key row counts are near scaled targets')

status='PASS' if not violations else 'FAIL'
report={'status':status,'business_rule_violations':len(violations),'warnings':warnings,'checks':checks,'metrics':metrics,'dataset_count':49,'scale_factor':MANIFEST['scale_factor'],'seed':MANIFEST['seed']}
(PACKAGE/'validation_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
lines=['# Raw Data Validation Report','',f'**Status:** {status}',f'**Business-rule violations:** {len(violations)}',f'**Scale factor executed:** {MANIFEST["scale_factor"]}','', '## Checks']
for c in checks: lines.append(f'- {"✅" if c["status"]=="PASS" else "⚠️" if c["status"]=="WARN" else "❌"} **{c["check"]}** — {c["detail"]}')
lines+=['','## Distribution Metrics']
for k,v in metrics.items():
    if isinstance(v,(float,np.floating)): lines.append(f'- `{k}`: {float(v):.4f}')
lines+=['','## Controlled Imperfection', 'These are deliberate raw-data imperfections that do **not** violate canonical business rules.']
for k,v in mess.items(): lines.append(f'- `{k}`: {v}')
if warnings:
    lines+=['','## Warnings']+[f'- {x}' for x in warnings]
(PACKAGE/'validation_report.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'status':status,'business_rule_violations':len(violations),'warnings':len(warnings)},ensure_ascii=False))
sys.exit(0 if status=='PASS' else 1)
