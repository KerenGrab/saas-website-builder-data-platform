
from __future__ import annotations
from pathlib import Path
import argparse, json, math, shutil, hashlib, time
import numpy as np
import pandas as pd

SEED = 20260821
START = pd.Timestamp("2024-01-01 00:00:00")
END = pd.Timestamp("2025-12-31 23:59:59")

def fmt_ts(x):
    if x is None or pd.isna(x):
        return None
    return pd.Timestamp(x).strftime("%Y-%m-%dT%H:%M:%SZ")

def fmt_ts_series(s):
    x = pd.to_datetime(s)
    return x.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def rand_between(rng, start, end):
    start = pd.Timestamp(start); end = pd.Timestamp(end)
    if end <= start:
        return start
    sec = (end - start).total_seconds()
    return start + pd.to_timedelta(float(rng.random()) * sec, unit="s")

def weighted_date(rng, end=END, start=START, later_bias=True):
    span = (end - start).total_seconds()
    u = float(rng.random())
    frac = math.sqrt(u) if later_bias else u
    return start + pd.to_timedelta(frac * span, unit="s")

def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

class Writer:
    def __init__(self, root: Path):
        self.root = root
        self.manifest = []
        self.required_fields = {}
        self.files = {}
        for s in ["core_product","event_tracking","billing_payment","support_ticketing"]:
            (root / s).mkdir(parents=True, exist_ok=True)

    def save(self, num, source, stem, df, jsonl=False):
        fields = list(df.columns)
        ext = "jsonl" if jsonl else "csv"
        path = self.root / source / f"{num:02d}_{stem}.{ext}"
        if jsonl:
            df.to_json(path, orient="records", lines=True, force_ascii=False)
        else:
            df.to_csv(path, index=False, encoding="utf-8")
        item = {
            "number": num, "source": source, "dataset": stem,
            "path": str(path.relative_to(self.root.parent)),
            "format": ext, "rows": int(len(df)),
            "required_fields": fields,
            "sha256": sha256_file(path),
        }
        self.manifest.append(item)
        self.required_fields[num] = fields
        self.files[num] = path
        return path

def main(scale=1.0, out_root=None):
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    package = Path(out_root or Path(__file__).resolve().parent)
    raw = package / "raw"
    if raw.exists():
        shutil.rmtree(raw)
    raw.mkdir(parents=True)
    W = Writer(raw)

    # Canonical scale
    n_accounts = max(200, round(2000*scale))
    n_users = max(n_accounts, round(2700*scale))
    n_memberships = max(n_users, round(3100*scale))
    n_signup = max(n_accounts, round(3300*scale))
    n_visitors = max(1000, round(90000*scale))
    n_sessions = max(n_visitors, round(240000*scale))
    n_product_events = max(5000, round(450000*scale))
    n_audience_events = max(10000, round(1100000*scale))
    n_members = max(500, round(15000*scale))
    n_comments = max(500, round(18000*scale))
    n_ratings = max(500, round(12000*scale))
    n_support = max(100, round(1200*scale))
    target_pages = max(1000, round(14500*scale))
    target_content = max(500, round(6500*scale))

    print("START BATCH 1", round(time.time()-t0,1), flush=True)
    # ---------- Batch 1: Reference foundation ----------
    plans = pd.DataFrame([
        ("PLAN_FREE","free"),
        ("PLAN_STANDARD","standard"),
        ("PLAN_PREMIUM","premium"),
    ], columns=["plan_id","plan_name"])
    W.save(43,"billing_payment","plan_catalog",plans)

    features = pd.DataFrame([
        ("FEAT_01","basic_analytics",0,0.60),
        ("FEAT_02","basic_membership",0,0.50),
        ("FEAT_03","basic_forms",0,0.55),
        ("FEAT_04","site_search",1,0.40),
        ("FEAT_05","custom_domain_tools",1,0.45),
        ("FEAT_06","advanced_forms",1,0.30),
        ("FEAT_07","advanced_analytics",2,0.25),
        ("FEAT_08","premium_video",2,0.18),
    ], columns=["feature_id","feature_name","min_tier","adoption_prob"])
    W.save(17,"core_product","feature",features[["feature_id","feature_name"]])

    plan_tier = {"PLAN_FREE":0,"PLAN_STANDARD":1,"PLAN_PREMIUM":2}
    ent = []
    k=1
    for plan_id,tier in plan_tier.items():
        for r in features.itertuples(index=False):
            if tier >= r.min_tier:
                ent.append((f"ENT_{k:04d}",plan_id,r.feature_id,START,None))
                k+=1
    ent_df = pd.DataFrame(ent, columns=["entitlement_period_id","plan_id","feature_id","valid_from","valid_to"])
    ent_out = ent_df.copy()
    ent_out["valid_from"] = fmt_ts_series(ent_out["valid_from"])
    ent_out["valid_to"] = None
    W.save(18,"core_product","plan_feature_entitlement_history",ent_out)

    print("START BATCH 2", round(time.time()-t0,1), flush=True)
    # ---------- Batch 2: Acquisition + Identity ----------
    # Signup journeys. Converted journeys are selected first and become Accounts.
    latest_signup = END - pd.Timedelta(days=7)
    span_sec = (latest_signup-START).total_seconds()
    u = rng.random(n_signup)
    # mild acquisition growth toward 2025
    signup_starts = START + pd.to_timedelta(np.sqrt(u)*span_sec, unit="s")
    conv_idx = rng.choice(n_signup, size=n_accounts, replace=False)
    conv_idx_set = set(map(int,conv_idx))
    journey_ids = np.array([f"SJ_{i+1:06d}" for i in range(n_signup)], dtype=object)
    resulting = np.array([None]*n_signup, dtype=object)
    account_ids = np.array([f"ACC_{i+1:06d}" for i in range(n_accounts)], dtype=object)
    # Assign accounts ordered by signup time for deterministic chronology
    conv_sorted = conv_idx[np.argsort(signup_starts[conv_idx].values)]
    account_create = {}
    journey_to_account = {}
    for j, idx in enumerate(conv_sorted):
        aid = account_ids[j]
        resulting[idx] = aid
        delay = pd.to_timedelta(float(rng.uniform(5/1440,5)), unit="D")
        ctime = min(pd.Timestamp(signup_starts[idx]) + delay, END)
        account_create[aid] = ctime
        journey_to_account[journey_ids[idx]] = aid

    signup_context = pd.DataFrame({"signup_journey_id":journey_ids,"resulting_account_id":resulting})
    W.save(39,"event_tracking","signup_journey_context",signup_context)

    signup_events = pd.DataFrame({
        "event_id":[f"EV_SIGNUP_{i+1:07d}" for i in range(n_signup)],
        "signup_journey_id":journey_ids,
        "event_type":"signup_started",
        "event_time":[fmt_ts(x) for x in signup_starts],
    })
    # raw event duplicate messiness, same event identity
    dup_n=max(1,int(len(signup_events)*0.001))
    signup_events_raw=pd.concat([signup_events,signup_events.sample(dup_n,random_state=SEED)],ignore_index=True)
    W.save(40,"event_tracking","signup_journey_events",signup_events_raw,jsonl=True)

    acq_sources=np.array(["search","direct","social","referral"])
    acq_probs=np.array([0.34,0.30,0.20,0.16])
    acq = pd.DataFrame({
        "signup_journey_id":journey_ids,
        "acquisition_source":rng.choice(acq_sources,n_signup,p=acq_probs)
    })
    W.save(41,"event_tracking","acquisition_source_attribution",acq)

    accounts = pd.DataFrame({"account_id":account_ids})
    W.save(1,"core_product","account",accounts)

    # Account closure / lifecycle
    closed_ids=set(rng.choice(account_ids,size=max(1,int(n_accounts*0.04)),replace=False))
    account_end={}
    account_lifecycle_periods=[]
    account_events=[]
    for i,aid in enumerate(account_ids):
        created=account_create[aid]
        end=END
        if aid in closed_ids and created < END-pd.Timedelta(days=90):
            end=rand_between(rng,created+pd.Timedelta(days=90),END)
        account_end[aid]=end
        account_events.append((f"EV_ACC_{len(account_events)+1:07d}",aid,"account_created",created))
        # 10% have an inactive spell if enough life
        life_days=(end-created).total_seconds()/86400
        if life_days>150 and rng.random()<0.10:
            inactive_start=rand_between(rng,created+pd.Timedelta(days=60),end-pd.Timedelta(days=45))
            inactive_end=min(inactive_start+pd.Timedelta(days=float(rng.uniform(14,60))),end)
            account_lifecycle_periods.append((f"ALP_{len(account_lifecycle_periods)+1:07d}",aid,"active",created,inactive_start))
            account_lifecycle_periods.append((f"ALP_{len(account_lifecycle_periods)+1:07d}",aid,"inactive",inactive_start,inactive_end))
            if inactive_end < end:
                account_lifecycle_periods.append((f"ALP_{len(account_lifecycle_periods)+1:07d}",aid,"active",inactive_end,end if aid in closed_ids else None))
        else:
            account_lifecycle_periods.append((f"ALP_{len(account_lifecycle_periods)+1:07d}",aid,"active",created,end if aid in closed_ids else None))
        if aid in closed_ids:
            account_events.append((f"EV_ACC_{len(account_events)+1:07d}",aid,"account_closure",end))
            account_lifecycle_periods.append((f"ALP_{len(account_lifecycle_periods)+1:07d}",aid,"closed",end,None))

    alp=pd.DataFrame(account_lifecycle_periods,columns=["account_lifecycle_period_id","account_id","lifecycle_state","valid_from","valid_to"])
    alp["valid_from"]=fmt_ts_series(alp["valid_from"])
    alp["valid_to"]=[fmt_ts(x) for x in alp["valid_to"]]
    W.save(6,"core_product","account_lifecycle_period",alp)

    aev=pd.DataFrame(account_events,columns=["event_id","account_id","event_type","event_time"])
    aev["event_time"]=fmt_ts_series(aev["event_time"])
    W.save(7,"core_product","account_lifecycle_events",aev)

    # Users & Memberships: all account owners unique + extra users.
    user_ids=np.array([f"USR_{i+1:06d}" for i in range(n_users)],dtype=object)
    users=pd.DataFrame({"user_id":user_ids})
    W.save(2,"core_product","saas_user",users)
    owner_user={aid:user_ids[i] for i,aid in enumerate(account_ids)}
    membership_rows=[]
    # owner membership
    for aid in account_ids:
        membership_rows.append([None,owner_user[aid],aid,"owner"])
    # additional unique users each get one membership
    extra_users=list(user_ids[n_accounts:])
    add_needed=n_memberships-n_accounts
    base_extra=min(len(extra_users),add_needed)
    for u in extra_users[:base_extra]:
        aid=str(rng.choice(account_ids))
        membership_rows.append([None,u,aid,None])
    remaining=add_needed-base_extra
    # Concentrate extra memberships on a smaller subset to keep multi-account-user ratio moderate.
    multi_pool=extra_users[:max(1,min(len(extra_users),math.ceil(remaining/2)))]
    cursor=0
    while remaining>0:
        u=multi_pool[cursor % len(multi_pool)]
        existing={r[2] for r in membership_rows if r[1]==u}
        choices=[x for x in account_ids if x not in existing]
        if choices:
            aid=str(rng.choice(choices))
            membership_rows.append([None,u,aid,None])
            remaining-=1
        cursor+=1
    for i,r in enumerate(membership_rows):
        r[0]=f"MEM_{i+1:07d}"
    memberships=pd.DataFrame([r[:3] for r in membership_rows],columns=["membership_id","user_id","account_id"])
    W.save(3,"core_product","user_account_membership",memberships)

    membership_meta={}
    membership_period_rows=[]
    role_period_rows=[]
    join_events=[]
    role_choices=np.array(["editor","viewer"])
    for r in membership_rows:
        mid,uid,aid,owner_flag=r
        astart=account_create[aid]; aend=account_end[aid]
        is_owner=(uid==owner_user[aid])
        if is_owner:
            join=astart
        else:
            latest=max(astart, aend-pd.Timedelta(days=2))
            join=rand_between(rng,astart,latest)
        end=None if aid not in closed_ids else aend
        if not is_owner and (aend-join)>pd.Timedelta(days=60) and rng.random()<0.10:
            leave=rand_between(rng,join+pd.Timedelta(days=30),aend)
            end=leave
        periods=[(join,end)]
        # ~3% non-owner rejoin, if enough time before account end
        if not is_owner and end is not None and (aend-end)>pd.Timedelta(days=40) and rng.random()<0.03:
            rejoin=rand_between(rng,end+pd.Timedelta(days=10),aend)
            periods.append((rejoin,aend if aid in closed_ids else None))
        membership_meta[mid]={"user_id":uid,"account_id":aid,"periods":periods}
        for ps,pe in periods:
            mpid=f"MP_{len(membership_period_rows)+1:08d}"
            membership_period_rows.append((mpid,mid,ps,pe))
            join_events.append((f"EV_MEM_{len(join_events)+1:08d}",mid,uid,aid,"user_joined_account",ps))
            role="owner" if is_owner else str(rng.choice(role_choices,p=[0.72,0.28]))
            actual_end=pe if pe is not None else aend
            if (actual_end-ps)>pd.Timedelta(days=80) and not is_owner and rng.random()<0.08:
                change=rand_between(rng,ps+pd.Timedelta(days=30),actual_end-pd.Timedelta(days=10))
                role_period_rows.append((f"RP_{len(role_period_rows)+1:08d}",mid,role,ps,change))
                new_role="viewer" if role=="editor" else "editor"
                role_period_rows.append((f"RP_{len(role_period_rows)+1:08d}",mid,new_role,change,pe))
            else:
                role_period_rows.append((f"RP_{len(role_period_rows)+1:08d}",mid,role,ps,pe))
    mp=pd.DataFrame(membership_period_rows,columns=["membership_period_id","membership_id","valid_from","valid_to"])
    mp["valid_from"]=fmt_ts_series(mp["valid_from"]); mp["valid_to"]=[fmt_ts(x) for x in mp["valid_to"]]
    W.save(4,"core_product","membership_period",mp)
    rp=pd.DataFrame(role_period_rows,columns=["role_period_id","membership_id","role","valid_from","valid_to"])
    rp["valid_from"]=fmt_ts_series(rp["valid_from"]); rp["valid_to"]=[fmt_ts(x) for x in rp["valid_to"]]
    W.save(5,"core_product","role_assignment_period",rp)
    mev=pd.DataFrame(join_events,columns=["event_id","membership_id","user_id","account_id","event_type","event_time"])
    mev["event_time"]=fmt_ts_series(mev["event_time"])
    W.save(8,"core_product","membership_lifecycle_events",mev)

    print("START BATCH 3", round(time.time()-t0,1), flush=True)
    # ---------- Batch 3: Commercial lifecycle ----------
    eligible_paid=[aid for aid in account_ids if account_create[aid] < END-pd.Timedelta(days=75)]
    n_ever_paid=min(len(eligible_paid),max(1,round(n_accounts*0.30)))
    ever_paid=set(rng.choice(np.array(eligible_paid,dtype=object),size=n_ever_paid,replace=False))
    churn_set=set(rng.choice(np.array(sorted(ever_paid),dtype=object),size=max(1,round(n_ever_paid*0.20)),replace=False))
    react_candidates=np.array([x for x in sorted(churn_set) if account_create[x] < END-pd.Timedelta(days=300)],dtype=object)
    react_set=set(rng.choice(react_candidates,size=min(len(react_candidates),max(1,round(len(churn_set)*0.15))),replace=False)) if len(react_candidates) else set()

    sub_periods=[]
    sub_events=[]
    billing_periods=[]
    commercial_timeline={}
    bill_timeline={}
    for aid in account_ids:
        start=account_create[aid]; hard_end=account_end[aid]
        transitions=[]
        if aid in ever_paid and hard_end-start>pd.Timedelta(days=75):
            paid_start=rand_between(rng,start+pd.Timedelta(days=14),min(start+pd.Timedelta(days=120),hard_end-pd.Timedelta(days=15)))
            first_plan="PLAN_PREMIUM" if rng.random()<0.10 else "PLAN_STANDARD"
            transitions.append((paid_start,first_plan,"subscription_upgraded","PLAN_FREE",first_plan))
            cur_plan=first_plan
            # optional plan change
            if hard_end-paid_start>pd.Timedelta(days=150) and rng.random()<0.28:
                change=rand_between(rng,paid_start+pd.Timedelta(days=60),hard_end-pd.Timedelta(days=45))
                if cur_plan=="PLAN_STANDARD":
                    nxt="PLAN_PREMIUM"; et="subscription_upgraded"
                else:
                    nxt="PLAN_STANDARD"; et="subscription_downgraded"
                transitions.append((change,nxt,et,cur_plan,nxt)); cur_plan=nxt
            if aid in churn_set and hard_end-paid_start>pd.Timedelta(days=120):
                cancel=rand_between(rng,paid_start+pd.Timedelta(days=90),hard_end-pd.Timedelta(days=10))
                transitions=[x for x in transitions if x[0] < cancel]
                # recompute current before cancel
                cur="PLAN_FREE"
                for x in sorted(transitions):
                    cur=x[1]
                transitions.append((cancel,"PLAN_FREE","subscription_cancelled",cur,"PLAN_FREE"))
                if aid in react_set and hard_end-cancel>pd.Timedelta(days=60):
                    react=rand_between(rng,cancel+pd.Timedelta(days=30),hard_end-pd.Timedelta(days=5))
                    nxt="PLAN_STANDARD" if rng.random()<0.8 else "PLAN_PREMIUM"
                    transitions.append((react,nxt,"subscription_reactivated","PLAN_FREE",nxt))
        transitions=sorted(transitions,key=lambda x:x[0])
        points=[(start,"PLAN_FREE")]
        for t,p,et,fp,tp in transitions:
            points.append((t,p))
            sub_events.append((f"EV_SUB_{len(sub_events)+1:08d}",aid,et,t,fp,tp,None,None))
        # Plan periods
        periods=[]
        for i,(ps,plan) in enumerate(points):
            pe=points[i+1][0] if i+1<len(points) else hard_end
            if pe>ps:
                periods.append((ps,pe,plan))
                sub_periods.append((f"SPP_{len(sub_periods)+1:08d}",aid,plan,ps,pe if aid in closed_ids or i+1<len(points) else None))
        commercial_timeline[aid]=periods
        # Paid intervals, merge adjacent paid plan periods
        paid_intervals=[]
        for ps,pe,plan in periods:
            if plan!="PLAN_FREE":
                if paid_intervals and paid_intervals[-1][1]==ps:
                    paid_intervals[-1]=(paid_intervals[-1][0],pe)
                else:
                    paid_intervals.append((ps,pe))
        bperiods=[]
        for pstart,pend in paid_intervals:
            cycle="monthly" if rng.random()<0.70 else "annual"
            if pend-pstart>pd.Timedelta(days=180) and rng.random()<0.08:
                ctime=rand_between(rng,pstart+pd.Timedelta(days=60),pend-pd.Timedelta(days=30))
                newcycle="annual" if cycle=="monthly" else "monthly"
                bperiods.append((pstart,ctime,cycle))
                bperiods.append((ctime,pend,newcycle))
                sub_events.append((f"EV_SUB_{len(sub_events)+1:08d}",aid,"billing_cycle_changed",ctime,None,None,cycle,newcycle))
            else:
                bperiods.append((pstart,pend,cycle))
        bill_timeline[aid]=bperiods
        for bs,be,bc in bperiods:
            billing_periods.append((f"BCP_{len(billing_periods)+1:08d}",aid,bc,bs,be if (aid in closed_ids or be<END) else None))
            step=30 if bc=="monthly" else 365
            rt=bs+pd.Timedelta(days=step)
            while rt < be:
                sub_events.append((f"EV_SUB_{len(sub_events)+1:08d}",aid,"subscription_renewed",rt,None,None,None,None))
                rt += pd.Timedelta(days=step)

    spp=pd.DataFrame(sub_periods,columns=["subscription_plan_period_id","account_id","plan_id","valid_from","valid_to"])
    spp["valid_from"]=fmt_ts_series(spp["valid_from"]); spp["valid_to"]=[fmt_ts(x) for x in spp["valid_to"]]
    W.save(44,"billing_payment","subscription_plan_period",spp)
    bcp=pd.DataFrame(billing_periods,columns=["billing_cycle_period_id","account_id","billing_cycle","valid_from","valid_to"])
    bcp["valid_from"]=fmt_ts_series(bcp["valid_from"]); bcp["valid_to"]=[fmt_ts(x) for x in bcp["valid_to"]]
    W.save(45,"billing_payment","billing_cycle_period",bcp)
    sev=pd.DataFrame(sub_events,columns=["event_id","account_id","event_type","event_time","from_plan_id","to_plan_id","from_billing_cycle","to_billing_cycle"])
    sev["event_time"]=fmt_ts_series(sev["event_time"])
    W.save(46,"billing_payment","subscription_lifecycle_events",sev)

    # Payments: initial + scheduled payments for paid billing periods, retries, refunds, payment-method changes.
    payment_events=[]
    successful=[]
    payment_counter=0
    for aid,bps in bill_timeline.items():
        for bs,be,bc in bps:
            step=30 if bc=="monthly" else 365
            times=[bs]
            x=bs+pd.Timedelta(days=step)
            while x<be:
                times.append(x); x+=pd.Timedelta(days=step)
            for pt in times:
                payment_counter+=1
                pref=f"PAY_{payment_counter:08d}"
                if rng.random()<0.045:
                    payment_events.append((f"EV_PAY_{len(payment_events)+1:08d}",aid,"payment_failed",pt,pref,None))
                    retry=min(pt+pd.Timedelta(days=float(rng.uniform(1,4))),be-pd.Timedelta(seconds=1))
                    payment_counter+=1
                    pref2=f"PAY_{payment_counter:08d}"
                    payment_events.append((f"EV_PAY_{len(payment_events)+1:08d}",aid,"payment_succeeded",retry,pref2,None))
                    successful.append((aid,pref2,retry,be))
                else:
                    payment_events.append((f"EV_PAY_{len(payment_events)+1:08d}",aid,"payment_succeeded",pt,pref,None))
                    successful.append((aid,pref,pt,be))
        if bps and rng.random()<0.38:
            allstart=min(x[0] for x in bps); allend=max(x[1] for x in bps)
            mt=rand_between(rng,allstart,allend)
            payment_events.append((f"EV_PAY_{len(payment_events)+1:08d}",aid,"payment_method_changed",mt,None,None))
    # Refunds: 1.5% of successful payments when enough time remains
    if successful:
        refund_count=max(1,round(len(successful)*0.015))
        for idx in rng.choice(len(successful),size=min(refund_count,len(successful)),replace=False):
            aid,pref,pt,be=successful[int(idx)]
            upper=min(be,END)
            if upper>pt+pd.Timedelta(hours=1):
                rt=rand_between(rng,pt+pd.Timedelta(hours=1),upper)
                payment_events.append((f"EV_PAY_{len(payment_events)+1:08d}",aid,"payment_refunded",rt,None,pref))
    pev=pd.DataFrame(payment_events,columns=["event_id","account_id","event_type","event_time","payment_ref","original_payment_ref"])
    pev["event_time"]=fmt_ts_series(pev["event_time"])
    W.save(47,"billing_payment","payment_refund_activity_events",pev)

    print("START BATCH 4", round(time.time()-t0,1), flush=True)
    # ---------- Batch 4: Website structure ----------
    probs=np.array([0.10,0.48,0.25,0.10,0.025,0.025,0.02])
    wcats=np.array([0,1,2,3,4,5,6])
    website_counts=rng.choice(wcats,size=n_accounts,p=probs)
    website_rows=[]
    website_internal={}
    purposes=np.array(["portfolio_personal_brand","business_services","course_educational","organization_nonprofit","other"])
    purpose_p=np.array([0.22,0.43,0.15,0.10,0.10])
    templates=np.array(["blank","portfolio_template","business_template","course_template","organization_template"])
    wid_counter=0
    for aid,cnt in zip(account_ids,website_counts):
        astart=account_create[aid]; aend=account_end[aid]
        for _ in range(int(cnt)):
            wid_counter+=1
            wid=f"WEB_{wid_counter:07d}"
            if aend<=astart+pd.Timedelta(hours=1):
                ctime=astart
            else:
                ctime=rand_between(rng,astart,min(astart+pd.Timedelta(days=180),aend-pd.Timedelta(minutes=1)))
            will_publish=bool(rng.random()<0.70 and ctime<END-pd.Timedelta(days=2))
            purpose=str(rng.choice(purposes,p=purpose_p))
            template=str(rng.choice(templates,p=[0.22,0.20,0.30,0.16,0.12]))
            website_rows.append((wid,aid,template,purpose))
            website_internal[wid]={"account_id":aid,"created":ctime,"hard_end":aend,"will_publish":will_publish}
    websites=pd.DataFrame(website_rows,columns=["website_id","account_id","template_origin","website_purpose"])
    W.save(9,"core_product","website",websites)
    website_ids=websites.website_id.to_numpy(dtype=object)
    n_web=len(websites)

    # Pages exact target allocated across websites, at least 1 each
    target_pages=max(target_pages,n_web)
    base=np.ones(n_web,dtype=int)
    extra=target_pages-n_web
    page_extra=rng.multinomial(extra,np.ones(n_web)/n_web) if extra>0 else np.zeros(n_web,dtype=int)
    page_counts=base+page_extra
    page_rows=[]; pages_by_web={}; page_to_web={}
    pc=0
    for wid,cnt in zip(website_ids,page_counts):
        arr=[]
        for _ in range(int(cnt)):
            pc+=1; pid=f"PAGE_{pc:08d}"; arr.append(pid)
            page_rows.append((pid,wid)); page_to_web[pid]=wid
        pages_by_web[wid]=arr
    pages=pd.DataFrame(page_rows,columns=["page_id","website_id"])
    W.save(10,"core_product","page",pages)

    # Content exact target, distribute among pages
    page_ids=pages.page_id.to_numpy(dtype=object)
    content_page_idx=rng.choice(len(page_ids),size=target_content,replace=True)
    content_rows=[]; content_by_web_video={}; content_by_web_file={}; content_to_page={}
    for i,pidx in enumerate(content_page_idx):
        pid=page_ids[int(pidx)]; wid=page_to_web[pid]
        ctype="video" if rng.random()<0.55 else "file"
        cid=f"CONT_{i+1:08d}"
        content_rows.append((cid,pid,ctype)); content_to_page[cid]=pid
        d=content_by_web_video if ctype=="video" else content_by_web_file
        d.setdefault(wid,[]).append(cid)
    content=pd.DataFrame(content_rows,columns=["content_item_id","page_id","content_type"])
    W.save(11,"core_product","content_item",content)

    # Preplan which published websites adopt membership so access config can be coherent.
    publish_candidates=[w for w in website_ids if website_internal[w]["will_publish"]]
    membership_site_count=max(1,round(len(publish_candidates)*0.24))
    membership_sites=set(rng.choice(np.array(publish_candidates,dtype=object),size=min(membership_site_count,len(publish_candidates)),replace=False))

    page_access=[]
    for pid,wid in page_rows:
        if wid in membership_sites:
            mode=str(rng.choice(["public","members_only","restricted"],p=[0.78,0.16,0.06]))
        else:
            mode=str(rng.choice(["public","restricted"],p=[0.95,0.05]))
        page_access.append((pid,mode))
    W.save(12,"core_product","page_access",pd.DataFrame(page_access,columns=["page_id","access_mode"]))
    content_access=[]
    for cid,pid,ctype in content_rows:
        wid=page_to_web[pid]
        if wid in membership_sites:
            mode=str(rng.choice(["public","members_only","restricted"],p=[0.78,0.17,0.05]))
        else:
            mode=str(rng.choice(["public","restricted"],p=[0.96,0.04]))
        content_access.append((cid,mode))
    W.save(13,"core_product","content_item_access",pd.DataFrame(content_access,columns=["content_item_id","access_mode"]))

    print("START BATCH 5", round(time.time()-t0,1), flush=True)
    # ---------- Batch 5: Website temporal history ----------
    web_events=[]; live_periods=[]; address_periods=[]
    live_by_web={}; web_end={}
    for wid in website_ids:
        meta=website_internal[wid]; created=meta["created"]; hard_end=meta["hard_end"]
        events=[("website_created",created)]
        lives=[]
        if meta["will_publish"] and hard_end>created+pd.Timedelta(days=2):
            pub=rand_between(rng,created+pd.Timedelta(hours=1),min(created+pd.Timedelta(days=30),hard_end-pd.Timedelta(hours=1)))
            events.append(("published",pub))
            scenario=str(rng.choice(["simple","unpublish_republish","archive_restore","delete"],p=[0.76,0.14,0.07,0.03]))
            if scenario=="simple" or hard_end-pub<pd.Timedelta(days=90):
                lives.append((pub,hard_end if wid in [] else (hard_end if meta["account_id"] in closed_ids else None)))
            elif scenario=="unpublish_republish":
                unp=rand_between(rng,pub+pd.Timedelta(days=30),hard_end-pd.Timedelta(days=30))
                rep=rand_between(rng,unp+pd.Timedelta(days=7),hard_end)
                events += [("unpublished",unp),("published",rep)]
                lives += [(pub,unp),(rep,hard_end if meta["account_id"] in closed_ids else None)]
            elif scenario=="archive_restore":
                arc=rand_between(rng,pub+pd.Timedelta(days=30),hard_end-pd.Timedelta(days=25))
                res=rand_between(rng,arc+pd.Timedelta(days=7),hard_end-pd.Timedelta(days=5))
                rep=min(res+pd.Timedelta(days=float(rng.uniform(1,7))),hard_end)
                events += [("archived",arc),("restored",res)]
                if rep<hard_end:
                    events.append(("published",rep))
                lives += [(pub,arc)]
                if rep<hard_end:
                    lives.append((rep,hard_end if meta["account_id"] in closed_ids else None))
            else: # delete
                dele=rand_between(rng,pub+pd.Timedelta(days=30),hard_end)
                events.append(("deleted",dele)); lives.append((pub,dele)); hard_end=dele
        web_end[wid]=hard_end
        for et,tm in sorted(events,key=lambda x:x[1]):
            web_events.append((f"EV_WEB_{len(web_events)+1:08d}",wid,et,tm))
        live_by_web[wid]=lives
        for ls,le in lives:
            live_periods.append((f"LIVE_{len(live_periods)+1:08d}",wid,ls,le))
        # Address exists from creation; custom switch for some published sites
        platform=f"{wid.lower()}.builder.example"
        if lives and rng.random()<0.35:
            first_live=lives[0][0]
            switch=min(first_live+pd.Timedelta(days=float(rng.uniform(7,90))),hard_end)
            if switch>created:
                address_periods.append((f"ADDR_{len(address_periods)+1:08d}",wid,platform,"platform",created,switch))
                custom=f"{wid.lower().replace('web_','site')}.example.com"
                address_periods.append((f"ADDR_{len(address_periods)+1:08d}",wid,custom,"custom",switch,hard_end if meta["account_id"] in closed_ids or hard_end<END else None))
            else:
                address_periods.append((f"ADDR_{len(address_periods)+1:08d}",wid,platform,"platform",created,hard_end if meta["account_id"] in closed_ids else None))
        else:
            address_periods.append((f"ADDR_{len(address_periods)+1:08d}",wid,platform,"platform",created,hard_end if meta["account_id"] in closed_ids or hard_end<END else None))
    wev=pd.DataFrame(web_events,columns=["event_id","website_id","event_type","event_time"])
    wev["event_time"]=fmt_ts_series(wev["event_time"])
    W.save(14,"core_product","website_lifecycle_events",wev)
    lpd=pd.DataFrame(live_periods,columns=["live_period_id","website_id","valid_from","valid_to"])
    lpd["valid_from"]=fmt_ts_series(lpd["valid_from"]); lpd["valid_to"]=[fmt_ts(x) for x in lpd["valid_to"]]
    W.save(15,"core_product","website_live_period",lpd)
    adh=pd.DataFrame(address_periods,columns=["address_period_id","website_id","address_value","address_type","valid_from","valid_to"])
    adh["valid_from"]=fmt_ts_series(adh["valid_from"]); adh["valid_to"]=[fmt_ts(x) for x in adh["valid_to"]]
    W.save(16,"core_product","website_address_history",adh)

    print("START BATCH 6", round(time.time()-t0,1), flush=True)
    # ---------- Batch 6: Feature enablement ----------
    feature_req={r.feature_id:int(r.min_tier) for r in features.itertuples(index=False)}
    feature_prob={r.feature_id:float(r.adoption_prob) for r in features.itertuples(index=False)}
    feature_ids=features.feature_id.to_list()
    enable_periods=[]; enable_events=[]; enable_by_web_feature={}
    # helper to get first publish time
    first_publish={}
    for wid in website_ids:
        pubs=[pd.Timestamp(t) for et,t in [(x[2],x[3]) for x in web_events if x[1]==wid] if et=="published"]
        if pubs: first_publish[wid]=min(pubs)
    # More efficient event lookup from wev internal source
    pub_map={}
    for _,wid,et,tm in web_events:
        if et=="published" and wid not in pub_map: pub_map[wid]=tm

    for wid in publish_candidates:
        aid=website_internal[wid]["account_id"]
        pub=pub_map.get(wid)
        if pub is None: continue
        for fid in feature_ids:
            req=feature_req[fid]
            eligible=[]
            for ps,pe,plan in commercial_timeline[aid]:
                if plan_tier[plan]>=req:
                    s=max(ps,pub); e=min(pe,web_end[wid])
                    if e>s: eligible.append((s,e))
            # merge contiguous eligible intervals
            merged=[]
            for s,e in sorted(eligible):
                if merged and merged[-1][1]==s:
                    merged[-1]=(merged[-1][0],e)
                else:
                    merged.append((s,e))
            p=feature_prob[fid]
            if fid=="FEAT_02" and wid in membership_sites:
                p=1.0
            for s,e in merged:
                if rng.random()>p: continue
                dur=e-s
                start=s+pd.to_timedelta(float(rng.uniform(0.02,0.25))*dur.total_seconds(),unit="s")
                # Ensure basic membership is available before members arrive.
                if fid=="FEAT_02" and wid in membership_sites:
                    start=min(start,s+pd.Timedelta(days=2))
                end=e
                if e-start>pd.Timedelta(days=60) and rng.random()<0.15 and not (fid=="FEAT_02" and wid in membership_sites):
                    end=rand_between(rng,start+pd.Timedelta(days=30),e)
                epid=f"ENP_{len(enable_periods)+1:08d}"
                enable_periods.append((epid,wid,fid,start,end if end<END else None))
                enable_events.append((f"EV_EN_{len(enable_events)+1:08d}",wid,fid,"feature_enabled",start))
                if end<END and end<=web_end[wid]:
                    enable_events.append((f"EV_EN_{len(enable_events)+1:08d}",wid,fid,"feature_disabled",end))
                enable_by_web_feature.setdefault((wid,fid),[]).append((start,end))
                # occasional re-enable after explicit early disable within same eligibility interval
                if end<e-pd.Timedelta(days=20) and rng.random()<0.20:
                    rs=rand_between(rng,end+pd.Timedelta(days=5),e)
                    epid=f"ENP_{len(enable_periods)+1:08d}"
                    enable_periods.append((epid,wid,fid,rs,e if e<END else None))
                    enable_events.append((f"EV_EN_{len(enable_events)+1:08d}",wid,fid,"feature_enabled",rs))
                    if e<END:
                        enable_events.append((f"EV_EN_{len(enable_events)+1:08d}",wid,fid,"feature_disabled",e))
                    enable_by_web_feature.setdefault((wid,fid),[]).append((rs,e))
    enp=pd.DataFrame(enable_periods,columns=["enablement_period_id","website_id","feature_id","valid_from","valid_to"])
    enp["valid_from"]=fmt_ts_series(enp["valid_from"]); enp["valid_to"]=[fmt_ts(x) for x in enp["valid_to"]]
    W.save(19,"core_product","website_feature_enablement_period",enp)
    ene=pd.DataFrame(enable_events,columns=["event_id","website_id","feature_id","event_type","event_time"])
    ene["event_time"]=fmt_ts_series(ene["event_time"])
    W.save(20,"core_product","feature_enablement_lifecycle_events",ene)

    print("START BATCH 7", round(time.time()-t0,1), flush=True)
    # ---------- Batch 7: Website membership + contributions ----------
    # Allocate exact member count over membership sites with skewed weights.
    msites=np.array(sorted(membership_sites),dtype=object)
    weights=rng.lognormal(mean=0.0,sigma=1.0,size=len(msites))
    weights=weights/weights.sum()
    member_counts=rng.multinomial(n_members,weights)
    member_rows=[]; invitation_rows=[]; invitation_events=[]; reg_success=[]; state_rows=[]; profile_events=[]; membership_beh=[]
    member_meta={}
    member_counter=0; inv_counter=0; reg_attempt_counter=0
    for wid,cnt in zip(msites,member_counts):
        # choose membership feature start as minimum enablement for basic_membership
        enints=enable_by_web_feature.get((wid,"FEAT_02"),[])
        if not enints:
            continue
        available_start=min(x[0] for x in enints)
        wend=web_end[wid]
        for _ in range(int(cnt)):
            member_counter+=1; mid=f"MBR_{member_counter:08d}"
            latest=max(available_start,wend-pd.Timedelta(hours=1))
            reg_time=rand_between(rng,available_start,latest)
            method="invitation" if rng.random()<0.30 else "self"
            invitation_id=None
            if method=="invitation":
                inv_counter+=1; invitation_id=f"INV_{inv_counter:08d}"
                it=max(website_internal[wid]["created"],reg_time-pd.Timedelta(days=float(rng.uniform(1,30))))
                invitation_rows.append((invitation_id,wid,f"invitee_{inv_counter:08d}",it))
            member_rows.append((mid,wid))
            reg_success.append((f"EV_REG_{len(reg_success)+1:08d}",wid,mid,invitation_id,method,reg_time))
            reg_attempt_counter+=1; raid=f"RGA_{reg_attempt_counter:08d}"
            membership_beh.append((f"EV_MBEH_{len(membership_beh)+1:08d}","member_registration_started",reg_time-pd.Timedelta(minutes=float(rng.uniform(1,60))),wid,raid,None))
            # state lifecycle
            state_end=None
            state_rows.append((f"MST_{len(state_rows)+1:08d}",mid,"active",reg_time,None))
            if (wend-reg_time)>pd.Timedelta(days=60) and rng.random()<0.07:
                change=rand_between(rng,reg_time+pd.Timedelta(days=30),wend)
                newstate="suspended" if rng.random()<0.35 else "deactivated"
                state_rows[-1]=(state_rows[-1][0],mid,"active",reg_time,change)
                state_rows.append((f"MST_{len(state_rows)+1:08d}",mid,newstate,change,None if wend>=END else wend))
                state_end=change
                # Some suspended members return to Active.
                if newstate=="suspended" and wend-change>pd.Timedelta(days=30) and rng.random()<0.45:
                    resume=rand_between(rng,change+pd.Timedelta(days=7),wend)
                    state_rows[-1]=(state_rows[-1][0],mid,newstate,change,resume)
                    state_rows.append((f"MST_{len(state_rows)+1:08d}",mid,"active",resume,None if wend>=END else wend))
                    state_end=None
            if rng.random()<0.25 and wend-reg_time>pd.Timedelta(days=10):
                nup=1+(1 if rng.random()<0.15 else 0)
                for _u in range(nup):
                    ut=rand_between(rng,reg_time+pd.Timedelta(days=2),wend)
                    profile_events.append((f"EV_PROF_{len(profile_events)+1:08d}",mid,ut))
            # Logins, observed behaviour
            nlogin=int(rng.poisson(2.5))
            for _l in range(nlogin):
                lt=rand_between(rng,reg_time,wend)
                membership_beh.append((f"EV_MBEH_{len(membership_beh)+1:08d}","member_logged_in",lt,wid,None,mid))
            member_meta[mid]={"website_id":wid,"registered":reg_time,"end":state_end or wend}

    # If some member sites had no valid enablement and exact count dropped, top up on valid sites.
    valid_sites=[w for w in msites if enable_by_web_feature.get((w,"FEAT_02"))]
    while member_counter < n_members:
        wid=str(rng.choice(valid_sites))
        enints=enable_by_web_feature[(wid,"FEAT_02")]
        available_start=min(x[0] for x in enints); wend=web_end[wid]
        member_counter+=1; mid=f"MBR_{member_counter:08d}"
        reg_time=rand_between(rng,available_start,wend)
        member_rows.append((mid,wid))
        reg_success.append((f"EV_REG_{len(reg_success)+1:08d}",wid,mid,None,"self",reg_time))
        reg_attempt_counter+=1; raid=f"RGA_{reg_attempt_counter:08d}"
        membership_beh.append((f"EV_MBEH_{len(membership_beh)+1:08d}","member_registration_started",reg_time-pd.Timedelta(minutes=5),wid,raid,None))
        state_rows.append((f"MST_{len(state_rows)+1:08d}",mid,"active",reg_time,None if wend>=END else wend))
        member_meta[mid]={"website_id":wid,"registered":reg_time,"end":wend}

    # Failed registration attempts ~8% of successful starts
    fail_n=max(1,round(n_members*0.085))
    for _ in range(fail_n):
        wid=str(rng.choice(valid_sites))
        enints=enable_by_web_feature[(wid,"FEAT_02")]
        st=rand_between(rng,min(x[0] for x in enints),web_end[wid])
        reg_attempt_counter+=1; raid=f"RGA_{reg_attempt_counter:08d}"
        membership_beh.append((f"EV_MBEH_{len(membership_beh)+1:08d}","member_registration_started",st,wid,raid,None))
        membership_beh.append((f"EV_MBEH_{len(membership_beh)+1:08d}","member_registration_failed",st+pd.Timedelta(minutes=float(rng.uniform(1,20))),wid,raid,None))

    # Unsuccessful invitation outcomes in addition to accepted invitations.
    unsuccessful_inv=max(1,round(len(invitation_rows)*0.25))
    for _ in range(unsuccessful_inv):
        wid=str(rng.choice(valid_sites)); inv_counter+=1; iid=f"INV_{inv_counter:08d}"
        t=rand_between(rng,pub_map[wid],web_end[wid])
        invitation_rows.append((iid,wid,f"invitee_{inv_counter:08d}",t))
        ot=min(t+pd.Timedelta(days=float(rng.uniform(1,30))),web_end[wid])
        invitation_events.append((f"EV_INV_{len(invitation_events)+1:08d}",iid,str(rng.choice(["rejected","expired","cancelled"],p=[0.45,0.40,0.15])),ot))

    wmem=pd.DataFrame(member_rows,columns=["member_id","website_id"]); W.save(21,"core_product","website_member",wmem)
    inv=pd.DataFrame(invitation_rows,columns=["invitation_id","website_id","invitee_ref","invitation_time"]); inv["invitation_time"]=fmt_ts_series(inv["invitation_time"]); W.save(22,"core_product","membership_invitation",inv)
    invo=pd.DataFrame(invitation_events,columns=["event_id","invitation_id","event_type","event_time"]);
    if len(invo): invo["event_time"]=fmt_ts_series(invo["event_time"])
    W.save(23,"core_product","invitation_outcome_events",invo)
    rs=pd.DataFrame(reg_success,columns=["event_id","website_id","member_id","invitation_id","registration_method","event_time"]); rs["event_time"]=fmt_ts_series(rs["event_time"]); W.save(24,"core_product","member_registration_success_events",rs)
    mst=pd.DataFrame(state_rows,columns=["member_state_period_id","member_id","member_state","valid_from","valid_to"]); mst["valid_from"]=fmt_ts_series(mst["valid_from"]); mst["valid_to"]=[fmt_ts(x) for x in mst["valid_to"]]; W.save(25,"core_product","member_state_history",mst)
    pro=pd.DataFrame(profile_events,columns=["event_id","member_id","event_time"]);
    if len(pro): pro["event_time"]=fmt_ts_series(pro["event_time"])
    W.save(26,"core_product","member_profile_update_events",pro)

    # Contributions
    member_ids_arr=np.array(list(member_meta.keys()),dtype=object)
    comment_rows=[]; comment_events=[]
    for i in range(n_comments):
        mid=str(rng.choice(member_ids_arr)); mm=member_meta[mid]; wid=mm["website_id"]
        pid=str(rng.choice(pages_by_web[wid])); posted=rand_between(rng,mm["registered"],mm["end"])
        cid=f"COM_{i+1:08d}"; comment_rows.append((cid,mid,pid))
        comment_events.append((f"EV_COM_{len(comment_events)+1:08d}",cid,"comment_posted",posted))
        if rng.random()<0.03:
            rpt=min(posted+pd.Timedelta(days=float(rng.uniform(0.1,30))),mm["end"])
            comment_events.append((f"EV_COM_{len(comment_events)+1:08d}",cid,"comment_reported",rpt))
            if rng.random()<0.50:
                rem=min(rpt+pd.Timedelta(days=float(rng.uniform(0.1,10))),mm["end"])
                comment_events.append((f"EV_COM_{len(comment_events)+1:08d}",cid,"comment_removed",rem))
    com=pd.DataFrame(comment_rows,columns=["comment_id","member_id","page_id"]); W.save(27,"core_product","comment",com)
    come=pd.DataFrame(comment_events,columns=["event_id","comment_id","event_type","event_time"]); come["event_time"]=fmt_ts_series(come["event_time"]); W.save(28,"core_product","comment_lifecycle_events",come)

    rating_rows=[]; rating_events=[]
    rating_probs=np.array([0.05,0.08,0.15,0.32,0.40])
    for i in range(n_ratings):
        mid=str(rng.choice(member_ids_arr)); mm=member_meta[mid]; wid=mm["website_id"]; pid=str(rng.choice(pages_by_web[wid]))
        given=rand_between(rng,mm["registered"],mm["end"]); val=int(rng.choice([1,2,3,4,5],p=rating_probs))
        rid=f"RAT_{i+1:08d}"; rating_rows.append((rid,mid,pid,val))
        rating_events.append((f"EV_RAT_{len(rating_events)+1:08d}",rid,"rating_given",given,val))
        if rng.random()<0.12 and mm["end"]>given+pd.Timedelta(days=1):
            ch=rand_between(rng,given+pd.Timedelta(days=1),mm["end"]); newval=int(rng.choice([1,2,3,4,5],p=rating_probs))
            rating_events.append((f"EV_RAT_{len(rating_events)+1:08d}",rid,"rating_changed",ch,newval))
            if rng.random()<0.25 and mm["end"]>ch+pd.Timedelta(days=1):
                rm=rand_between(rng,ch+pd.Timedelta(days=1),mm["end"]); rating_events.append((f"EV_RAT_{len(rating_events)+1:08d}",rid,"rating_removed",rm,None))
        elif rng.random()<0.04 and mm["end"]>given+pd.Timedelta(days=1):
            rm=rand_between(rng,given+pd.Timedelta(days=1),mm["end"]); rating_events.append((f"EV_RAT_{len(rating_events)+1:08d}",rid,"rating_removed",rm,None))
    rat=pd.DataFrame(rating_rows,columns=["rating_id","member_id","page_id","rating_value"]); W.save(29,"core_product","rating",rat)
    rate=pd.DataFrame(rating_events,columns=["event_id","rating_id","event_type","event_time","rating_value"]); rate["event_time"]=fmt_ts_series(rate["event_time"]); W.save(30,"core_product","rating_lifecycle_events",rate)

    mbe=pd.DataFrame(membership_beh,columns=["event_id","event_type","event_time","website_id","registration_attempt_id","member_id"])
    mbe["event_time"]=fmt_ts_series(mbe["event_time"])
    dup=max(1,int(len(mbe)*0.001))
    mbe_raw=pd.concat([mbe,mbe.sample(dup,random_state=SEED+1)],ignore_index=True)
    W.save(42,"event_tracking","membership_behaviour_events",mbe_raw,jsonl=True)

    print("START BATCH 8", round(time.time()-t0,1), flush=True)
    # ---------- Batch 8: Product behaviour ----------
    # Useful maps
    websites_by_account={}
    for wid,aid,_,_ in website_rows:
        websites_by_account.setdefault(aid,[]).append(wid)
    viewers=rp[rp.role=="viewer"].copy()
    # Parse role periods internal for restricted events
    role_internal=[]
    for rr in role_period_rows:
        rpid,mid,role,s,e=rr
        if role=="viewer":
            meta=membership_meta[mid]
            role_internal.append((mid,meta["user_id"],meta["account_id"],s,e if e is not None else account_end[meta["account_id"]]))
    n_access=round(n_product_events*0.55)
    n_usage=round(n_product_events*0.25)
    n_analytics=round(n_product_events*0.08)
    n_locked=round(n_product_events*0.06)
    n_restricted=n_product_events-n_access-n_usage-n_analytics-n_locked
    prod=[]

    # access events sample membership periods
    mp_internal=[(mid,membership_meta[mid]["user_id"],membership_meta[mid]["account_id"],s,e if e is not None else account_end[membership_meta[mid]["account_id"]]) for _,mid,s,e in membership_period_rows]
    for _ in range(n_access):
        mid,uid,aid,s,e=mp_internal[int(rng.integers(len(mp_internal)))]
        t=rand_between(rng,s,e); wid=None
        if websites_by_account.get(aid) and rng.random()<0.60:
            candidates=[w for w in websites_by_account[aid] if website_internal[w]["created"]<=t<=web_end[w]]
            if candidates: wid=str(rng.choice(candidates))
        prod.append((None,"product_accessed",t,uid,aid,wid,None))

    # feature usage from valid enablement periods, owner is valid user context
    en_internal=[x for x in enable_periods]
    for _ in range(n_usage):
        _,wid,fid,s,e0=en_internal[int(rng.integers(len(en_internal)))]
        e=e0 if e0 is not None else web_end[wid]
        t=rand_between(rng,s,e); aid=website_internal[wid]["account_id"]; uid=owner_user[aid]
        prod.append((None,"feature_used",t,uid,aid,wid,fid))

    # analytics views on valid websites, owner context
    pub_webs=np.array(list(pub_map.keys()),dtype=object)
    for _ in range(n_analytics):
        wid=str(rng.choice(pub_webs)); aid=website_internal[wid]["account_id"]; uid=owner_user[aid]
        t=rand_between(rng,pub_map[wid],web_end[wid])
        prod.append((None,"website_analytics_viewed",t,uid,aid,wid,None))

    # locked feature attempts from plan periods, choose a feature above tier
    locked_candidates=[(aid,ps,pe,plan) for aid,periods in commercial_timeline.items() for ps,pe,plan in periods if plan_tier[plan]<2]
    for _ in range(n_locked):
        aid,ps,pe,plan=locked_candidates[int(rng.integers(len(locked_candidates)))]
        tier=plan_tier[plan]; unent=[f for f in feature_ids if feature_req[f]>tier]
        if not unent: continue
        fid=str(rng.choice(unent)); t=rand_between(rng,ps,pe); uid=owner_user[aid]
        candidates=[w for w in websites_by_account.get(aid,[]) if website_internal[w]["created"]<=t<=web_end[w]]
        wid=str(rng.choice(candidates)) if candidates else None
        prod.append((None,"locked_feature_attempted",t,uid,aid,wid,fid))

    # restricted actions from viewer role periods
    if role_internal:
        for _ in range(n_restricted):
            mid,uid,aid,s,e=role_internal[int(rng.integers(len(role_internal)))]
            t=rand_between(rng,s,e)
            candidates=[w for w in websites_by_account.get(aid,[]) if website_internal[w]["created"]<=t<=web_end[w]]
            wid=str(rng.choice(candidates)) if candidates else None
            prod.append((None,"restricted_product_action_attempted",t,uid,aid,wid,None))
    else:
        n_restricted=0

    # Normalize to target if any skipped
    while len(prod)<n_product_events:
        mid,uid,aid,s,e=mp_internal[int(rng.integers(len(mp_internal)))]
        t=rand_between(rng,s,e)
        prod.append((None,"product_accessed",t,uid,aid,None,None))
    prod=prod[:n_product_events]
    for i in range(len(prod)):
        row=list(prod[i]); row[0]=f"EV_PROD_{i+1:09d}"; prod[i]=tuple(row)
    pdf=pd.DataFrame(prod,columns=["event_id","event_type","event_time","user_id","account_id","website_id","feature_id"])
    pdf["event_time"]=fmt_ts_series(pdf["event_time"])
    dup=max(1,int(len(pdf)*0.002))
    pdfraw=pd.concat([pdf,pdf.sample(dup,random_state=SEED+2)],ignore_index=True)
    W.save(31,"event_tracking","product_behaviour_events",pdfraw,jsonl=True)
    del pdfraw,pdf,prod

    print("START BATCH 9", round(time.time()-t0,1), flush=True)
    # ---------- Batch 9: Audience identity + sessions ----------
    live_webs=[w for w,l in live_by_web.items() if l]
    # website popularity
    pop=rng.lognormal(0,1.0,len(live_webs)); pop=pop/pop.sum()
    visitor_web=rng.choice(np.array(live_webs,dtype=object),size=n_visitors,p=pop)
    visitor_ids=np.array([f"VIS_{i+1:08d}" for i in range(n_visitors)],dtype=object)
    vdf=pd.DataFrame({"visitor_id":visitor_ids,"website_id":visitor_web}); W.save(32,"event_tracking","visitor",vdf)

    # Exact returning ratio ~40%; exact total sessions adjusted.
    returning_n=round(n_visitors*0.40)
    counts=np.ones(n_visitors,dtype=int)
    returning_idx=rng.choice(n_visitors,size=returning_n,replace=False)
    counts[returning_idx]=2+rng.poisson(3.2,size=returning_n)
    diff=n_sessions-counts.sum()
    if diff>0:
        add_idx=rng.choice(returning_idx,size=diff,replace=True)
        np.add.at(counts,add_idx,1)
    elif diff<0:
        need=-diff
        candidates=np.where(counts>2)[0].tolist()
        while need>0 and candidates:
            idx=int(rng.choice(candidates)); counts[idx]-=1; need-=1
            if counts[idx]<=2: candidates.remove(idx)
    # final tiny adjustment
    while counts.sum()<n_sessions: counts[int(rng.choice(returning_idx))]+=1
    while counts.sum()>n_sessions:
        idx=int(rng.choice(np.where(counts>1)[0])); counts[idx]-=1

    session_rows=[]; session_events=[]; traffic_rows=[]; session_internal={}
    traffic_vals=np.array(["search","direct","social","referral"]); traffic_p=[0.42,0.27,0.18,0.13]
    sc=0
    for vi,(vid,wid,cnt) in enumerate(zip(visitor_ids,visitor_web,counts)):
        intervals=live_by_web[str(wid)]
        for _ in range(int(cnt)):
            sc+=1; sid=f"SES_{sc:09d}"
            # weighted live period by duration
            ints=[]
            weights=[]
            for s,e0 in intervals:
                e=e0 if e0 is not None else web_end[str(wid)]
                if e>s:
                    ints.append((s,e)); weights.append((e-s).total_seconds())
            weights=np.array(weights,dtype=float); weights/=weights.sum()
            s,e=ints[int(rng.choice(len(ints),p=weights))]
            st=rand_between(rng,s,e)
            dur=float(np.clip(rng.lognormal(mean=np.log(240),sigma=0.9),15,3600))
            et=min(st+pd.Timedelta(seconds=dur),e)
            session_rows.append((sid,vid,wid))
            session_events.append((f"EV_SES_{len(session_events)+1:09d}",sid,"session_started",st))
            session_events.append((f"EV_SES_{len(session_events)+1:09d}",sid,"session_ended",et))
            traffic_rows.append((sid,str(rng.choice(traffic_vals,p=traffic_p))))
            session_internal[sid]={"visitor_id":vid,"website_id":str(wid),"start":st,"end":et}
    sdf=pd.DataFrame(session_rows,columns=["session_id","visitor_id","website_id"]); W.save(33,"event_tracking","audience_session",sdf)
    slev=pd.DataFrame(session_events,columns=["event_id","session_id","event_type","event_time"]); slev["event_time"]=fmt_ts_series(slev["event_time"])
    sdup=max(1,int(len(slev)*0.001)); slevraw=pd.concat([slev,slev.sample(sdup,random_state=SEED+3)],ignore_index=True)
    W.save(34,"event_tracking","session_lifecycle_events",slevraw,jsonl=True)
    traf=pd.DataFrame(traffic_rows,columns=["session_id","traffic_source"]); W.save(35,"event_tracking","session_traffic_attribution",traf)

    # Visitor-member linkages from members to existing visitors on same Website
    visitors_by_web={}
    for vid,wid in zip(visitor_ids,visitor_web):
        visitors_by_web.setdefault(str(wid),[]).append(str(vid))
    member_by_web={}
    for mid,meta in member_meta.items(): member_by_web.setdefault(meta["website_id"],[]).append(mid)
    link_rows=[]; linked_visitor={}
    for wid,mids in member_by_web.items():
        vids=visitors_by_web.get(wid,[])
        if not vids: continue
        take=min(len(vids),round(len(mids)*0.60))
        if take<=0: continue
        sel_m=list(rng.choice(np.array(mids,dtype=object),size=take,replace=False))
        sel_v=list(rng.choice(np.array(vids,dtype=object),size=take,replace=False if len(vids)>=take else True))
        for mid,vid in zip(sel_m,sel_v):
            reg=member_meta[mid]["registered"]
            # linkage can be discovered later
            vf=min(reg+pd.Timedelta(days=float(rng.uniform(0,45))),member_meta[mid]["end"])
            vt=None
            if member_meta[mid]["end"]<END and rng.random()<0.5: vt=member_meta[mid]["end"]
            link_rows.append((f"VML_{len(link_rows)+1:08d}",vid,mid,wid,vf,vt))
            linked_visitor[vid]=(mid,wid,vf,vt)
    vml=pd.DataFrame(link_rows,columns=["visitor_member_link_id","visitor_id","member_id","website_id","valid_from","valid_to"])
    if len(vml):
        vml["valid_from"]=fmt_ts_series(vml["valid_from"]); vml["valid_to"]=[fmt_ts(x) for x in vml["valid_to"]]
    W.save(36,"event_tracking","visitor_member_linkage",vml)

    # Historical session-member attribution, including some late attribution.
    attr_rows=[]
    sessions_by_visitor={}
    for sid,vid,wid in session_rows: sessions_by_visitor.setdefault(vid,[]).append(sid)
    for vid,(mid,wid,vf,vt) in linked_visitor.items():
        for sid in sessions_by_visitor.get(vid,[]):
            si=session_internal[sid]
            # mostly sessions after known linkage; small share older sessions attributed later
            if si["start"]>=vf and rng.random()<0.55:
                at=si["end"]+pd.Timedelta(hours=float(rng.uniform(0,12)))
                attr_rows.append((f"SMA_{len(attr_rows)+1:09d}",sid,mid,at))
            elif si["start"]<vf and rng.random()<0.08:
                at=vf+pd.Timedelta(days=float(rng.uniform(0,15)))
                attr_rows.append((f"SMA_{len(attr_rows)+1:09d}",sid,mid,at))
    sma=pd.DataFrame(attr_rows,columns=["session_member_attribution_id","session_id","member_id","attributed_at"])
    if len(sma): sma["attributed_at"]=fmt_ts_series(sma["attributed_at"])
    W.save(37,"event_tracking","session_member_attribution",sma)

    print("START BATCH 10", round(time.time()-t0,1), flush=True)
    # ---------- Batch 10: Audience interactions ----------
    # Per-session event counts, at least one page-view, exact unique-event target.
    sess_ids=np.array([x[0] for x in session_rows],dtype=object)
    sess_web=np.array([x[2] for x in session_rows],dtype=object)
    sess_start=np.array([session_internal[x]["start"].value for x in sess_ids],dtype=np.int64)
    sess_end=np.array([session_internal[x]["end"].value for x in sess_ids],dtype=np.int64)
    ecounts=1+rng.poisson(3.6,size=len(sess_ids))
    diff=n_audience_events-int(ecounts.sum())
    if diff>0:
        addidx=rng.choice(len(ecounts),size=diff,replace=True); np.add.at(ecounts,addidx,1)
    elif diff<0:
        need=-diff
        while need>0:
            candidates=np.where(ecounts>1)[0]
            take=min(need,len(candidates))
            idx=rng.choice(candidates,size=take,replace=False)
            ecounts[idx]-=1; need-=take
    # Build repeated session indices
    rep_idx=np.repeat(np.arange(len(sess_ids)),ecounts)
    total=len(rep_idx)
    # identify first event in every session
    first=np.zeros(total,dtype=bool)
    starts_idx=np.concatenate(([0],np.cumsum(ecounts)[:-1])); first[starts_idx]=True
    event_types=np.empty(total,dtype=object); event_types[first]="page_viewed"
    other_idx=np.where(~first)[0]
    oth_types=np.array(["page_viewed","link_clicked","video_watched","file_downloaded","form_started","form_submitted","search_performed","search_result_clicked","failure_friction"])
    oth_p=np.array([0.35,0.20,0.06,0.04,0.06,0.05,0.07,0.05,0.12])
    event_types[other_idx]=rng.choice(oth_types,size=len(other_idx),p=oth_p)
    # event time vector
    st_ns=sess_start[rep_idx]; en_ns=sess_end[rep_idx]
    frac=rng.random(total)
    ev_ns=st_ns+((en_ns-st_ns)*frac).astype(np.int64)
    # Allocate pages/content by Website group
    ev_web=sess_web[rep_idx]
    page_col=np.empty(total,dtype=object); page_col[:]=None
    content_col=np.empty(total,dtype=object); content_col[:]=None
    target_col=np.empty(total,dtype=object); target_col[:]=None
    # Full-scale optimization: factorize once instead of scanning all 1.1M events
    # separately for every Website (which is O(websites × events)).
    unique_web, web_codes = np.unique(ev_web, return_inverse=True)
    grouped_order = np.argsort(web_codes, kind="stable")
    grouped_counts = np.bincount(web_codes, minlength=len(unique_web))
    grouped_offsets = np.concatenate(([0], np.cumsum(grouped_counts)))
    for code, wid in enumerate(unique_web):
        idx=grouped_order[grouped_offsets[code]:grouped_offsets[code+1]]
        pgs=np.array(pages_by_web[str(wid)],dtype=object)
        page_col[idx]=rng.choice(pgs,size=len(idx),replace=True)
        # videos/files
        vidx=idx[event_types[idx]=="video_watched"]
        vids=np.array(content_by_web_video.get(str(wid),[]),dtype=object)
        if len(vids):
            content_col[vidx]=rng.choice(vids,size=len(vidx),replace=True)
        else:
            event_types[vidx]="page_viewed"
        fidx=idx[event_types[idx]=="file_downloaded"]
        files=np.array(content_by_web_file.get(str(wid),[]),dtype=object)
        if len(files):
            content_col[fidx]=rng.choice(files,size=len(fidx),replace=True)
        else:
            event_types[fidx]="page_viewed"
        # lightweight generic target refs, not new business entities
        for et,prefix in [("link_clicked","link"),("form_started","form"),("form_submitted","form"),("search_performed","search"),("search_result_clicked","search_result"),("failure_friction","friction")]:
            q=idx[event_types[idx]==et]
            if len(q): target_col[q]=np.array([f"{prefix}_{int(x)%97:03d}" for x in q],dtype=object)
    aud=pd.DataFrame({
        "event_id":[f"EV_AUD_{i+1:010d}" for i in range(total)],
        "event_type":event_types,
        "event_time":pd.to_datetime(ev_ns).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id":sess_ids[rep_idx],
        "page_id":page_col,
        "content_item_id":content_col,
        "interaction_target_ref":target_col,
    })
    adup=max(1,int(len(aud)*0.002))
    audraw=pd.concat([aud,aud.sample(adup,random_state=SEED+4)],ignore_index=True)
    W.save(38,"event_tracking","audience_interaction_events",audraw,jsonl=True)
    del audraw,aud,rep_idx,event_types,page_col,content_col,target_col

    print("START BATCH 11", round(time.time()-t0,1), flush=True)
    # ---------- Batch 11: Support ----------
    support_account_n=max(1,round(n_accounts*0.27))
    support_accounts=np.array(rng.choice(account_ids,size=support_account_n,replace=False),dtype=object)
    sw=rng.lognormal(0,0.8,len(support_accounts)); sw=sw/sw.sum()
    support_counts=np.ones(len(support_accounts),dtype=int)
    remaining_support=n_support-len(support_accounts)
    if remaining_support>0:
        support_counts += rng.multinomial(remaining_support,sw)
    support_rows=[]; support_events=[]
    problem_templates=[
        "customer reported a problem using the product",
        "customer needs help understanding an account action",
        "customer reported a website-related issue",
        "customer reported difficulty completing a product workflow",
        "customer requested help with a commercial account action",
    ]
    # membership periods by account for requester-validity
    mp_by_account={}
    for _,mid,s,e0 in membership_period_rows:
        meta=membership_meta[mid]; e=e0 if e0 is not None else account_end[meta["account_id"]]
        mp_by_account.setdefault(meta["account_id"],[]).append((mid,meta["user_id"],s,e))
    for aid,cnt in zip(support_accounts,support_counts):
        periods=mp_by_account[str(aid)]
        for _ in range(int(cnt)):
            mid,uid,s,e=periods[int(rng.integers(len(periods)))]
            opened=rand_between(rng,s,e)
            candidates=[w for w in websites_by_account.get(str(aid),[]) if website_internal[w]["created"]<=opened<=web_end[w]]
            wid=str(rng.choice(candidates)) if candidates and rng.random()<0.65 else None
            srid=f"SUP_{len(support_rows)+1:07d}"
            agent=f"agent_{int(rng.integers(1,21)):03d}" if rng.random()<0.92 else None
            support_rows.append((srid,str(aid),uid,wid,str(rng.choice(problem_templates)),agent))
            support_events.append((f"EV_SUP_{len(support_events)+1:08d}",srid,"support_request_opened",opened,agent))
            if rng.random()<0.90 and opened<END-pd.Timedelta(hours=2):
                resolved=min(opened+pd.Timedelta(hours=float(np.clip(rng.lognormal(np.log(36),1.0),1,24*14))),END)
                support_events.append((f"EV_SUP_{len(support_events)+1:08d}",srid,"support_request_resolved",resolved,agent))
    sr=pd.DataFrame(support_rows,columns=["support_request_id","account_id","requester_user_id","website_id","problem_context","agent_ref"])
    W.save(48,"support_ticketing","support_request",sr)
    sue=pd.DataFrame(support_events,columns=["event_id","support_request_id","event_type","event_time","agent_ref"]); sue["event_time"]=fmt_ts_series(sue["event_time"])
    W.save(49,"support_ticketing","support_lifecycle_events",sue)

    print("END BATCH 11", round(time.time()-t0,1), flush=True)
    # Manifest and generation metadata
    W.manifest.sort(key=lambda x:x["number"])
    manifest={
        "project":"SaaS Website Builder — Product / Data Platform",
        "part":"Part 6 — Realistic Data Generation / Raw Sources",
        "seed":SEED,
        "canonical_time_range":{"start":fmt_ts(START),"end":fmt_ts(END)},
        "scale_factor":scale,
        "datasets_expected":49,
        "datasets_generated":len(W.manifest),
        "datasets":W.manifest,
    }
    (package/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    summary={
        "seed":SEED,
        "scale_factor":scale,
        "accounts":n_accounts,
        "saas_users":n_users,
        "memberships":len(memberships),
        "websites":len(websites),
        "pages":len(pages),
        "content_items":len(content),
        "website_members":len(wmem),
        "comments":len(com),
        "ratings":len(rat),
        "signup_journeys":len(signup_context),
        "visitors":len(vdf),
        "sessions":len(sdf),
        "product_behaviour_rows_raw":next(x["rows"] for x in W.manifest if x["number"]==31),
        "audience_interaction_rows_raw":next(x["rows"] for x in W.manifest if x["number"]==38),
        "support_requests":len(sr),
        "elapsed_seconds":round(time.time()-t0,2),
    }
    # distribution facts (actual)
    final_plan={}
    for aid,periods in commercial_timeline.items():
        final_plan[aid]=periods[-1][2]
    plan_counts=pd.Series(list(final_plan.values())).value_counts().to_dict()
    summary["final_plan_counts"]=plan_counts
    summary["ever_paid_accounts"]=len(ever_paid)
    summary["published_websites"]=len(pub_map)
    summary["membership_enabled_websites"]=len(membership_sites)
    summary["payment_activity_rows"]=len(pev)
    summary["support_account_count"]=len(set(sr.account_id))
    (package/"generation_summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({"datasets_generated":len(W.manifest),"raw_root":str(raw),"elapsed_seconds":round(time.time()-t0,1)},ensure_ascii=False))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--scale",type=float,default=1.0)
    ap.add_argument("--out",type=str,default=None)
    args=ap.parse_args()
    main(scale=args.scale,out_root=args.out)
