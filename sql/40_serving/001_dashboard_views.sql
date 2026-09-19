-- Canonical dashboard serving layer.
-- Extracted from the verified PostgreSQL database saas_website_builder_9h.
-- Contains the dashboard schema, 12 serving views, and their documentation comments.
CREATE SCHEMA dashboard;


--
-- Name: SCHEMA dashboard; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA dashboard IS 'Power BI dashboard-serving layer for Part 12. Contains read-only views derived from validated Part 11 and Part 12 analytics.';


--
-- Name: vw_commercial_transition; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_commercial_transition AS
 WITH transitions AS (
         SELECT e.event_id,
            e.account_id,
            e.event_type,
            e.event_time,
            e.from_plan_id,
            fp.plan_name AS from_plan_name,
            e.to_plan_id,
            tp.plan_name AS to_plan_name
           FROM ((public.subscription_lifecycle_event e
             LEFT JOIN public.plan_catalog fp ON (((fp.plan_id)::text = (e.from_plan_id)::text)))
             LEFT JOIN public.plan_catalog tp ON (((tp.plan_id)::text = (e.to_plan_id)::text)))
          WHERE ((e.event_type)::text = ANY ((ARRAY['subscription_upgraded'::character varying, 'subscription_downgraded'::character varying, 'subscription_cancelled'::character varying, 'subscription_reactivated'::character varying])::text[]))
        ), type_totals AS (
         SELECT transitions.event_type,
            count(*) AS type_event_count,
            count(DISTINCT transitions.account_id) AS type_account_count
           FROM transitions
          GROUP BY transitions.event_type
        ), overall_totals AS (
         SELECT count(*) AS all_transition_events,
            count(DISTINCT transitions.account_id) AS all_transition_accounts
           FROM transitions
        ), path_summary AS (
         SELECT transitions.event_type,
            transitions.from_plan_id,
            transitions.from_plan_name,
            transitions.to_plan_id,
            transitions.to_plan_name,
            count(*) AS transition_events,
            count(DISTINCT transitions.account_id) AS distinct_accounts
           FROM transitions
          GROUP BY transitions.event_type, transitions.from_plan_id, transitions.from_plan_name, transitions.to_plan_id, transitions.to_plan_name
        )
 SELECT ps.event_type,
        CASE ps.event_type
            WHEN 'subscription_upgraded'::text THEN 'Upgrade'::text
            WHEN 'subscription_downgraded'::text THEN 'Downgrade'::text
            WHEN 'subscription_cancelled'::text THEN 'Cancel'::text
            WHEN 'subscription_reactivated'::text THEN 'Reactivate'::text
            ELSE NULL::text
        END AS event_type_label,
        CASE ps.event_type
            WHEN 'subscription_upgraded'::text THEN 1
            WHEN 'subscription_downgraded'::text THEN 2
            WHEN 'subscription_cancelled'::text THEN 3
            WHEN 'subscription_reactivated'::text THEN 4
            ELSE NULL::integer
        END AS event_type_order,
    ps.from_plan_id,
    ps.from_plan_name,
    ps.to_plan_id,
    ps.to_plan_name,
    (((ps.from_plan_name)::text || U&' \2192 '::text) || (ps.to_plan_name)::text) AS path_label,
    ps.transition_events,
    ps.distinct_accounts,
    round((((ps.transition_events)::numeric / (NULLIF(tt.type_event_count, 0))::numeric) * (100)::numeric), 2) AS share_within_transition_type_pct,
    round((((ps.transition_events)::numeric / (NULLIF(ot.all_transition_events, 0))::numeric) * (100)::numeric), 2) AS share_of_all_transitions_pct,
    tt.type_event_count,
    tt.type_account_count,
    ot.all_transition_events,
    ot.all_transition_accounts,
    (row_number() OVER (ORDER BY
        CASE ps.event_type
            WHEN 'subscription_upgraded'::text THEN 1
            WHEN 'subscription_downgraded'::text THEN 2
            WHEN 'subscription_cancelled'::text THEN 3
            WHEN 'subscription_reactivated'::text THEN 4
            ELSE NULL::integer
        END, ps.transition_events DESC, ps.from_plan_name, ps.to_plan_name))::integer AS path_sort_order
   FROM ((path_summary ps
     JOIN type_totals tt ON (((tt.event_type)::text = (ps.event_type)::text)))
     CROSS JOIN overall_totals ot);


--
-- Name: VIEW vw_commercial_transition; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_commercial_transition IS 'Power BI serving view for core commercial transition paths: Upgrade, Downgrade, Cancel, Reactivate. Grain: one Event Type Ã— From Plan Ã— To Plan path. Renewal and Billing Cycle Change are intentionally excluded.';


--
-- Name: vw_conversion_horizon; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_conversion_horizon AS
 WITH params AS (
         SELECT '2026-01-01 02:00:00+02'::timestamp with time zone AS observation_end
        ), activation AS (
         SELECT w.account_id,
            min(e.event_time) AS activation_time
           FROM (public.website w
             JOIN public.website_lifecycle_event e ON ((((e.website_id)::text = (w.website_id)::text) AND ((e.event_type)::text = 'published'::text))))
          GROUP BY w.account_id
        ), closure AS (
         SELECT account_lifecycle_event.account_id,
            min(account_lifecycle_event.event_time) AS closure_time
           FROM public.account_lifecycle_event
          WHERE ((account_lifecycle_event.event_type)::text = 'account_closure'::text)
          GROUP BY account_lifecycle_event.account_id
        ), first_plan AS (
         SELECT ranked.account_id,
            ranked.plan_id,
            ranked.plan_name
           FROM ( SELECT spp.account_id,
                    spp.plan_id,
                    pc.plan_name,
                    row_number() OVER (PARTITION BY spp.account_id ORDER BY spp.valid_from, spp.subscription_plan_period_id) AS rn
                   FROM (public.subscription_plan_period spp
                     JOIN public.plan_catalog pc ON (((pc.plan_id)::text = (spp.plan_id)::text)))) ranked
          WHERE (ranked.rn = 1)
        ), plan_boundaries AS (
         SELECT old_p.account_id,
            old_p.valid_to AS boundary_time,
            old_p.plan_id AS from_plan_id,
            old_pc.plan_name AS from_plan_name,
            new_p.plan_id AS to_plan_id,
            new_pc.plan_name AS to_plan_name
           FROM (((public.subscription_plan_period old_p
             JOIN public.subscription_plan_period new_p ON ((((new_p.account_id)::text = (old_p.account_id)::text) AND (new_p.valid_from = old_p.valid_to))))
             JOIN public.plan_catalog old_pc ON (((old_pc.plan_id)::text = (old_p.plan_id)::text)))
             JOIN public.plan_catalog new_pc ON (((new_pc.plan_id)::text = (new_p.plan_id)::text)))
        ), first_paid AS (
         SELECT plan_boundaries.account_id,
            min(plan_boundaries.boundary_time) AS first_paid_time
           FROM plan_boundaries
          WHERE ((lower((plan_boundaries.from_plan_name)::text) = 'free'::text) AND (lower((plan_boundaries.to_plan_name)::text) = ANY (ARRAY['standard'::text, 'premium'::text])))
          GROUP BY plan_boundaries.account_id
        ), journey AS (
         SELECT a.account_id,
            a.activation_time,
            fp.plan_name AS first_plan_name,
            pd.first_paid_time,
            c.closure_time,
            p.observation_end
           FROM ((((activation a
             CROSS JOIN params p)
             JOIN first_plan fp ON (((fp.account_id)::text = (a.account_id)::text)))
             LEFT JOIN first_paid pd ON (((pd.account_id)::text = (a.account_id)::text)))
             LEFT JOIN closure c ON (((c.account_id)::text = (a.account_id)::text)))
        ), eligible_cohort AS (
         SELECT journey.account_id,
            journey.activation_time,
            journey.first_paid_time,
            journey.closure_time
           FROM journey
          WHERE ((lower((journey.first_plan_name)::text) = 'free'::text) AND ((journey.closure_time IS NULL) OR (journey.closure_time >= journey.activation_time)) AND ((journey.first_paid_time IS NULL) OR (journey.first_paid_time >= journey.activation_time)) AND ((journey.observation_end >= (journey.activation_time + '180 days'::interval)) OR ((journey.closure_time IS NOT NULL) AND (journey.closure_time >= journey.activation_time) AND (journey.closure_time < (journey.activation_time + '180 days'::interval)))))
        ), horizons AS (
         SELECT h_1.horizon_days,
            h_1.horizon_label,
            h_1.horizon_order
           FROM ( VALUES (30,'D30'::text,1), (60,'D60'::text,2), (90,'D90'::text,3), (180,'D180'::text,4)) h_1(horizon_days, horizon_label, horizon_order)
        )
 SELECT h.horizon_days,
    h.horizon_label,
    h.horizon_order,
    count(*) FILTER (WHERE ((ec.first_paid_time IS NOT NULL) AND (ec.first_paid_time <= (ec.activation_time + make_interval(days => h.horizon_days))))) AS converted_count,
    count(*) AS cohort_size,
    round((((count(*) FILTER (WHERE ((ec.first_paid_time IS NOT NULL) AND (ec.first_paid_time <= (ec.activation_time + make_interval(days => h.horizon_days))))))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS conversion_rate_pct
   FROM (horizons h
     CROSS JOIN eligible_cohort ec)
  GROUP BY h.horizon_days, h.horizon_label, h.horizon_order;


--
-- Name: VIEW vw_conversion_horizon; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_conversion_horizon IS 'Power BI serving view for canonical Post-Activation First Paid Conversion. Grain: one row per D30/D60/D90/D180 horizon. Fixed 180-day comparable cohort.';


--
-- Name: vw_feature; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_feature AS
 SELECT feature_id,
    feature_name,
    (row_number() OVER (ORDER BY feature_name, feature_id))::integer AS feature_sort
   FROM public.feature f;


--
-- Name: VIEW vw_feature; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_feature IS 'Power BI serving dimension for Page 3 Feature filtering. Grain: one row per canonical Feature.';


--
-- Name: vw_feature_adoption; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_feature_adoption AS
 WITH eligible_pairs AS (
         SELECT DISTINCT spp.account_id,
            ent.feature_id
           FROM (public.subscription_plan_period spp
             JOIN public.plan_feature_entitlement_period ent ON ((((ent.plan_id)::text = (spp.plan_id)::text) AND (spp.valid_from < COALESCE(ent.valid_to, 'infinity'::timestamp with time zone)) AND (ent.valid_from < COALESCE(spp.valid_to, 'infinity'::timestamp with time zone)))))
        ), adopted_pairs AS (
         SELECT DISTINCT pbe.account_id,
            pbe.feature_id
           FROM public.product_behaviour_event pbe
          WHERE (((pbe.event_type)::text = 'feature_used'::text) AND (pbe.account_id IS NOT NULL) AND (pbe.feature_id IS NOT NULL))
        ), feature_pair_status AS (
         SELECT ep.account_id,
            ep.feature_id,
                CASE
                    WHEN (ap.account_id IS NOT NULL) THEN 1
                    ELSE 0
                END AS adopted_flag
           FROM (eligible_pairs ep
             LEFT JOIN adopted_pairs ap ON ((((ap.account_id)::text = (ep.account_id)::text) AND ((ap.feature_id)::text = (ep.feature_id)::text))))
        ), feature_summary AS (
         SELECT fps.feature_id,
            count(*) AS eligible_pairs,
            sum(fps.adopted_flag) AS adopted_pairs
           FROM feature_pair_status fps
          GROUP BY fps.feature_id
        ), feature_rates AS (
         SELECT f.feature_id,
            f.feature_name,
            COALESCE(fs.eligible_pairs, (0)::bigint) AS eligible_pairs,
            COALESCE(fs.adopted_pairs, (0)::bigint) AS adopted_pairs,
                CASE
                    WHEN (COALESCE(fs.eligible_pairs, (0)::bigint) > 0) THEN round((((COALESCE(fs.adopted_pairs, (0)::bigint))::numeric / (fs.eligible_pairs)::numeric) * (100)::numeric), 2)
                    ELSE NULL::numeric
                END AS adoption_rate_pct
           FROM (public.feature f
             LEFT JOIN feature_summary fs ON (((fs.feature_id)::text = (f.feature_id)::text)))
        )
 SELECT feature_id,
    feature_name,
    eligible_pairs,
    adopted_pairs,
    adoption_rate_pct,
    (row_number() OVER (ORDER BY adoption_rate_pct DESC NULLS LAST, adopted_pairs DESC, feature_name, feature_id))::integer AS adoption_rank
   FROM feature_rates;


--
-- Name: VIEW vw_feature_adoption; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_feature_adoption IS 'Power BI serving view for eligibility-aware Account-level Feature Adoption. Grain: one row per Feature. Denominator is distinct historically eligible AccountÃ—Feature pairs; numerator is eligible pairs with at least one actual feature_used event.';


--
-- Name: vw_lifecycle_kpis; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_lifecycle_kpis AS
 SELECT 1 AS summary_id,
    (8074)::bigint AS eligible_feature_pairs,
    (3721)::bigint AS adopted_feature_pairs,
    46.09::numeric(6,2) AS feature_adoption_rate_pct,
    47.45::numeric(6,2) AS avg_adoption_breadth_pct,
    (600)::bigint AS ever_paid_accounts,
    (108)::bigint AS paid_churn_occurrences,
    (108)::bigint AS distinct_churned_accounts,
    152.70::numeric(8,2) AS median_days_to_first_churn,
    181.37::numeric(8,2) AS avg_days_to_first_churn,
    (132)::bigint AS cd1_population_n,
    72.97::numeric(6,2) AS cd1_early_adoption_m12_retention_pct,
    70.69::numeric(6,2) AS cd1_comparison_m12_retention_pct,
    2.28::numeric(6,2) AS cd1_difference_pp;


--
-- Name: VIEW vw_lifecycle_kpis; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_lifecycle_kpis IS 'Power BI one-row serving snapshot for validated Page 1 supporting metrics: Feature Adoption, Paid Churn, and CD-1. Values preserve locked Part 11 analytical outputs; no metric is redefined in this View.';


--
-- Name: vw_locked_feature_signal; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_locked_feature_signal AS
 WITH locked_attempts AS (
         SELECT pbe.event_id,
            pbe.event_time,
            pbe.user_id,
            pbe.account_id,
            pbe.website_id,
            pbe.feature_id
           FROM public.product_behaviour_event pbe
          WHERE ((pbe.event_type)::text = 'locked_feature_attempted'::text)
        ), contextualized_attempts AS (
         SELECT la.event_id,
            la.event_time,
            la.user_id,
            la.account_id,
            la.website_id,
            la.feature_id,
            spp.plan_id,
            pc.plan_name
           FROM ((locked_attempts la
             JOIN public.subscription_plan_period spp ON ((((spp.account_id)::text = (la.account_id)::text) AND (la.event_time >= spp.valid_from) AND ((spp.valid_to IS NULL) OR (la.event_time < spp.valid_to)))))
             JOIN public.plan_catalog pc ON (((pc.plan_id)::text = (spp.plan_id)::text)))
          WHERE (NOT (EXISTS ( SELECT 1
                   FROM public.plan_feature_entitlement_period ent
                  WHERE (((ent.plan_id)::text = (spp.plan_id)::text) AND ((ent.feature_id)::text = (la.feature_id)::text) AND (la.event_time >= ent.valid_from) AND ((ent.valid_to IS NULL) OR (la.event_time < ent.valid_to))))))
        ), feature_summary AS (
         SELECT ca.feature_id,
            count(*) AS attempt_events,
            count(DISTINCT ca.account_id) AS distinct_attempting_accounts,
            count(DISTINCT ca.user_id) AS distinct_attempting_users,
            count(DISTINCT ca.website_id) FILTER (WHERE (ca.website_id IS NOT NULL)) AS distinct_websites,
            count(*) FILTER (WHERE (ca.website_id IS NULL)) AS attempts_without_website,
            round(((count(*))::numeric / (NULLIF(count(DISTINCT ca.account_id), 0))::numeric), 2) AS attempts_per_attempting_account
           FROM contextualized_attempts ca
          GROUP BY ca.feature_id
        ), plan_mix AS (
         SELECT ca.feature_id,
            count(*) FILTER (WHERE (lower((ca.plan_name)::text) = 'free'::text)) AS free_attempt_events,
            count(*) FILTER (WHERE (lower((ca.plan_name)::text) = 'standard'::text)) AS standard_attempt_events,
            count(*) FILTER (WHERE (lower((ca.plan_name)::text) = 'premium'::text)) AS premium_attempt_events,
            count(DISTINCT ca.account_id) FILTER (WHERE (lower((ca.plan_name)::text) = 'free'::text)) AS free_attempting_accounts,
            count(DISTINCT ca.account_id) FILTER (WHERE (lower((ca.plan_name)::text) = 'standard'::text)) AS standard_attempting_accounts,
            count(DISTINCT ca.account_id) FILTER (WHERE (lower((ca.plan_name)::text) = 'premium'::text)) AS premium_attempting_accounts
           FROM contextualized_attempts ca
          GROUP BY ca.feature_id
        ), feature_signals AS (
         SELECT f.feature_id,
            f.feature_name,
            fs.attempt_events,
            fs.distinct_attempting_accounts,
            fs.distinct_attempting_users,
            fs.distinct_websites,
            fs.attempts_without_website,
            fs.attempts_per_attempting_account,
            pm.free_attempt_events,
            pm.standard_attempt_events,
            pm.premium_attempt_events,
            pm.free_attempting_accounts,
            pm.standard_attempting_accounts,
            pm.premium_attempting_accounts,
            round((((pm.free_attempt_events)::numeric / (NULLIF(fs.attempt_events, 0))::numeric) * (100)::numeric), 2) AS free_event_share_pct,
            round((((pm.standard_attempt_events)::numeric / (NULLIF(fs.attempt_events, 0))::numeric) * (100)::numeric), 2) AS standard_event_share_pct,
            round((((pm.premium_attempt_events)::numeric / (NULLIF(fs.attempt_events, 0))::numeric) * (100)::numeric), 2) AS premium_event_share_pct
           FROM ((feature_summary fs
             JOIN public.feature f ON (((f.feature_id)::text = (fs.feature_id)::text)))
             JOIN plan_mix pm ON (((pm.feature_id)::text = (fs.feature_id)::text)))
        )
 SELECT feature_id,
    feature_name,
    attempt_events,
    distinct_attempting_accounts,
    distinct_attempting_users,
    distinct_websites,
    attempts_without_website,
    attempts_per_attempting_account,
    free_attempt_events,
    standard_attempt_events,
    premium_attempt_events,
    free_attempting_accounts,
    standard_attempting_accounts,
    premium_attempting_accounts,
    free_event_share_pct,
    standard_event_share_pct,
    premium_event_share_pct,
    (row_number() OVER (ORDER BY distinct_attempting_accounts DESC, attempt_events DESC, feature_name, feature_id))::integer AS signal_rank
   FROM feature_signals;


--
-- Name: VIEW vw_locked_feature_signal; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_locked_feature_signal IS 'Power BI serving view for validated Locked Feature Access Signals. Grain: one row per Feature with locked attempts. Historical Plan context is resolved at event time and active entitlement is explicitly excluded. Locked attempts are access signals, not proven demand or willingness to pay.';


--
-- Name: vw_paid_retention_horizon; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_paid_retention_horizon AS
 WITH params AS (
         SELECT '2026-01-01 02:00:00+02'::timestamp with time zone AS observation_end
        ), plan_boundaries AS (
         SELECT old_p.account_id,
            old_p.valid_to AS boundary_time,
            old_pc.plan_name AS from_plan_name,
            new_pc.plan_name AS to_plan_name
           FROM (((public.subscription_plan_period old_p
             JOIN public.subscription_plan_period new_p ON ((((new_p.account_id)::text = (old_p.account_id)::text) AND (new_p.valid_from = old_p.valid_to))))
             JOIN public.plan_catalog old_pc ON (((old_pc.plan_id)::text = (old_p.plan_id)::text)))
             JOIN public.plan_catalog new_pc ON (((new_pc.plan_id)::text = (new_p.plan_id)::text)))
        ), first_paid AS (
         SELECT plan_boundaries.account_id,
            min(plan_boundaries.boundary_time) AS first_paid_time
           FROM plan_boundaries
          WHERE ((lower((plan_boundaries.from_plan_name)::text) = 'free'::text) AND (lower((plan_boundaries.to_plan_name)::text) = ANY (ARRAY['standard'::text, 'premium'::text])))
          GROUP BY plan_boundaries.account_id
        ), closure AS (
         SELECT account_lifecycle_event.account_id,
            min(account_lifecycle_event.event_time) AS closure_time
           FROM public.account_lifecycle_event
          WHERE ((account_lifecycle_event.event_type)::text = 'account_closure'::text)
          GROUP BY account_lifecycle_event.account_id
        ), cohort_candidates AS (
         SELECT fp.account_id,
            fp.first_paid_time,
            c.closure_time,
            p.observation_end,
            (date_trunc('month'::text, (fp.first_paid_time + '1 year'::interval)) + '1 mon'::interval) AS m12_snapshot_boundary
           FROM ((first_paid fp
             CROSS JOIN params p)
             LEFT JOIN closure c ON (((c.account_id)::text = (fp.account_id)::text)))
        ), fixed_cohort AS (
         SELECT cohort_candidates.account_id,
            cohort_candidates.first_paid_time,
            cohort_candidates.closure_time
           FROM cohort_candidates
          WHERE ((cohort_candidates.observation_end >= cohort_candidates.m12_snapshot_boundary) OR ((cohort_candidates.closure_time IS NOT NULL) AND (cohort_candidates.closure_time < cohort_candidates.m12_snapshot_boundary)))
        ), horizons AS (
         SELECT h.horizon_months,
            h.horizon_label,
            h.horizon_order
           FROM ( VALUES (1,'M1'::text,1), (3,'M3'::text,2), (6,'M6'::text,3), (12,'M12'::text,4)) h(horizon_months, horizon_label, horizon_order)
        ), account_horizons AS (
         SELECT fc.account_id,
            fc.first_paid_time,
            fc.closure_time,
            h.horizon_months,
            h.horizon_label,
            h.horizon_order,
            ((date_trunc('month'::text, (fc.first_paid_time + make_interval(months => h.horizon_months))) + '1 mon'::interval) - '00:00:01'::interval) AS snapshot_time
           FROM (fixed_cohort fc
             CROSS JOIN horizons h)
        ), states AS (
         SELECT ah.account_id,
            ah.horizon_months,
            ah.horizon_label,
            ah.horizon_order,
            ah.snapshot_time,
                CASE
                    WHEN ((ah.closure_time IS NOT NULL) AND (ah.closure_time <= ah.snapshot_time)) THEN false
                    WHEN (EXISTS ( SELECT 1
                       FROM (public.subscription_plan_period spp
                         JOIN public.plan_catalog pc ON (((pc.plan_id)::text = (spp.plan_id)::text)))
                      WHERE (((spp.account_id)::text = (ah.account_id)::text) AND (ah.snapshot_time >= spp.valid_from) AND ((spp.valid_to IS NULL) OR (ah.snapshot_time < spp.valid_to)) AND (lower((pc.plan_name)::text) = ANY (ARRAY['standard'::text, 'premium'::text]))))) THEN true
                    ELSE false
                END AS is_paid
           FROM account_horizons ah
        )
 SELECT horizon_months,
    horizon_label,
    horizon_order,
    count(*) FILTER (WHERE is_paid) AS retained_count,
    count(*) AS cohort_size,
    round((((count(*) FILTER (WHERE is_paid))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS retention_rate_pct
   FROM states
  GROUP BY horizon_months, horizon_label, horizon_order;


--
-- Name: VIEW vw_paid_retention_horizon; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_paid_retention_horizon IS 'Power BI serving view for canonical Unit 8 headline Paid Retention. Grain: one row per M1/M3/M6/M12 horizon. Fixed M12 cohort. State-based retention; reactivation may occur.';


--
-- Name: vw_product_paid_aligned; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_product_paid_aligned AS
 WITH canonical_counts AS (
         SELECT x.horizon_months,
            x.horizon_label,
            x.horizon_order,
            x.cohort_size,
            x.product_active_count,
            x.paid_count,
            x.both_count,
            x.product_only_count,
            x.paid_only_count,
            x.neither_count
           FROM ( VALUES (1,'M1'::text,1,143,49,140,49,0,91,3), (3,'M3'::text,2,143,86,132,86,0,46,11), (6,'M6'::text,3,143,88,114,83,5,31,24), (12,'M12'::text,4,143,84,97,75,9,22,37)) x(horizon_months, horizon_label, horizon_order, cohort_size, product_active_count, paid_count, both_count, product_only_count, paid_only_count, neither_count)
        )
 SELECT horizon_months,
    horizon_label,
    horizon_order,
    cohort_size,
    product_active_count,
    round((((product_active_count)::numeric / (cohort_size)::numeric) * (100)::numeric), 2) AS product_retention_rate_pct,
    paid_count,
    round((((paid_count)::numeric / (cohort_size)::numeric) * (100)::numeric), 2) AS paid_retention_rate_pct,
    both_count,
    product_only_count,
    paid_only_count,
    neither_count,
    (product_only_count + paid_only_count) AS gross_mismatch_count,
    round(((((product_only_count + paid_only_count))::numeric / (cohort_size)::numeric) * (100)::numeric), 2) AS gross_mismatch_rate_pct,
    round(((((paid_count - product_active_count))::numeric / (cohort_size)::numeric) * (100)::numeric), 2) AS net_gap_pp
   FROM canonical_counts;


--
-- Name: VIEW vw_product_paid_aligned; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_product_paid_aligned IS 'Power BI serving view for the locked Unit 10 Product vs Paid aligned comparison. Grain: one row per M1/M3/M6/M12 horizon; fixed cohort n=143. Preserves the validated Unit 10 analytical artifact without redefining Product Active.';


--
-- Name: vw_rating_snapshot; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_rating_snapshot AS
 WITH ordered_events AS (
         SELECT rle.rating_id,
            rle.event_type,
            rle.event_time,
            rle.rating_value,
            row_number() OVER (PARTITION BY rle.rating_id ORDER BY rle.event_time DESC, rle.event_id DESC) AS event_rank
           FROM public.rating_lifecycle_event rle
        ), latest_event AS (
         SELECT ordered_events.rating_id,
            ordered_events.event_type AS latest_event_type
           FROM ordered_events
          WHERE (ordered_events.event_rank = 1)
        ), latest_value AS (
         SELECT rating_lifecycle_event.rating_id,
            rating_lifecycle_event.rating_value,
            row_number() OVER (PARTITION BY rating_lifecycle_event.rating_id ORDER BY rating_lifecycle_event.event_time DESC, rating_lifecycle_event.event_id DESC) AS value_rank
           FROM public.rating_lifecycle_event
          WHERE (((rating_lifecycle_event.event_type)::text = ANY ((ARRAY['rating_given'::character varying, 'rating_changed'::character varying])::text[])) AND (rating_lifecycle_event.rating_value IS NOT NULL))
        ), current_active_ratings AS (
         SELECT le.rating_id,
            lv.rating_value AS current_rating_value
           FROM (latest_event le
             JOIN latest_value lv ON ((((lv.rating_id)::text = (le.rating_id)::text) AND (lv.value_rank = 1))))
          WHERE ((le.latest_event_type)::text <> 'rating_removed'::text)
        ), rating_distribution AS (
         SELECT current_active_ratings.current_rating_value AS rating_value,
            count(*) AS active_rating_count
           FROM current_active_ratings
          GROUP BY current_active_ratings.current_rating_value
        ), summary AS (
         SELECT count(*) AS total_active_ratings,
            round(avg(current_active_ratings.current_rating_value), 2) AS current_avg_rating,
            count(*) FILTER (WHERE (current_active_ratings.current_rating_value = ANY (ARRAY[4, 5]))) AS high_rating_4_5_count,
            round((((count(*) FILTER (WHERE (current_active_ratings.current_rating_value = ANY (ARRAY[4, 5]))))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS high_rating_4_5_share_pct
           FROM current_active_ratings
        ), rating_scale AS (
         SELECT x.rating_value,
            x.rating_sort
           FROM ( VALUES (1,1), (2,2), (3,3), (4,4), (5,5)) x(rating_value, rating_sort)
        )
 SELECT rs.rating_value,
    rs.rating_sort,
    COALESCE(rd.active_rating_count, (0)::bigint) AS active_rating_count,
    s.total_active_ratings,
    s.current_avg_rating,
    s.high_rating_4_5_count,
    s.high_rating_4_5_share_pct
   FROM ((rating_scale rs
     LEFT JOIN rating_distribution rd ON ((rd.rating_value = rs.rating_value)))
     CROSS JOIN summary s);


--
-- Name: VIEW vw_rating_snapshot; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_rating_snapshot IS 'Power BI serving view for current active Website Member Rating distribution. Grain: one row per rating value 1-5. Removed Ratings are excluded; current values are reconstructed from lifecycle history.';


--
-- Name: vw_support_monthly; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_support_monthly AS
 WITH support_lifecycle AS (
         SELECT sr.support_request_id,
            sr.account_id,
            sr.website_id,
            sr.problem_context,
            min(e.event_time) FILTER (WHERE ((e.event_type)::text = 'support_request_opened'::text)) AS opened_at,
            max(e.event_time) FILTER (WHERE ((e.event_type)::text = 'support_request_resolved'::text)) AS resolved_at
           FROM (public.support_request sr
             JOIN public.support_lifecycle_event e ON (((e.support_request_id)::text = (sr.support_request_id)::text)))
          GROUP BY sr.support_request_id, sr.account_id, sr.website_id, sr.problem_context
        ), support_metrics AS (
         SELECT support_lifecycle.support_request_id,
            support_lifecycle.account_id,
            support_lifecycle.website_id,
            support_lifecycle.problem_context,
            support_lifecycle.opened_at,
            support_lifecycle.resolved_at,
                CASE
                    WHEN ((support_lifecycle.resolved_at IS NOT NULL) AND (support_lifecycle.resolved_at >= support_lifecycle.opened_at)) THEN (EXTRACT(epoch FROM (support_lifecycle.resolved_at - support_lifecycle.opened_at)) / 3600.0)
                    ELSE NULL::numeric
                END AS resolution_hours
           FROM support_lifecycle
        ), support_with_month AS (
         SELECT support_metrics.support_request_id,
            support_metrics.account_id,
            support_metrics.website_id,
            support_metrics.problem_context,
            support_metrics.opened_at,
            support_metrics.resolved_at,
            support_metrics.resolution_hours,
            (date_trunc('month'::text, (support_metrics.opened_at AT TIME ZONE 'Asia/Jerusalem'::text)))::date AS month_start
           FROM support_metrics
          WHERE (support_metrics.opened_at IS NOT NULL)
        ), monthly_support AS (
         SELECT support_with_month.month_start,
            count(*) AS requests_opened,
            count(DISTINCT support_with_month.account_id) AS accounts_with_support,
            count(*) FILTER (WHERE (support_with_month.website_id IS NOT NULL)) AS website_linked_requests,
            count(*) FILTER (WHERE (support_with_month.website_id IS NULL)) AS account_level_requests,
            count(*) FILTER (WHERE (support_with_month.resolved_at IS NOT NULL)) AS resolved_requests,
            count(*) FILTER (WHERE (support_with_month.resolved_at IS NULL)) AS unresolved_requests,
            round((((count(*) FILTER (WHERE (support_with_month.resolved_at IS NOT NULL)))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS resolution_rate_pct,
            round((percentile_cont((0.50)::double precision) WITHIN GROUP (ORDER BY ((support_with_month.resolution_hours)::double precision)) FILTER (WHERE (support_with_month.resolution_hours IS NOT NULL)))::numeric, 2) AS median_resolution_hours,
            round(avg(support_with_month.resolution_hours) FILTER (WHERE (support_with_month.resolution_hours IS NOT NULL)), 2) AS avg_resolution_hours
           FROM support_with_month
          GROUP BY support_with_month.month_start
        )
 SELECT month_start,
    to_char((month_start)::timestamp with time zone, 'Mon YYYY'::text) AS month_label,
    (((EXTRACT(year FROM month_start))::integer * 100) + (EXTRACT(month FROM month_start))::integer) AS month_sort,
        CASE
            WHEN (month_start = '2026-01-01'::date) THEN true
            ELSE false
        END AS is_partial_period,
    requests_opened,
    accounts_with_support,
    website_linked_requests,
    account_level_requests,
    resolved_requests,
    unresolved_requests,
    resolution_rate_pct,
    median_resolution_hours,
    avg_resolution_hours
   FROM monthly_support;


--
-- Name: VIEW vw_support_monthly; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_support_monthly IS 'Power BI monthly Support serving view. Grain: one row per support-request opened month. Resolution rate = resolved/opened; resolution duration applies to resolved requests only. Jan 2026 is explicitly flagged as partial.';


--
-- Name: vw_support_summary; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_support_summary AS
 WITH support_lifecycle AS (
         SELECT sr.support_request_id,
            min(e.event_time) FILTER (WHERE ((e.event_type)::text = 'support_request_opened'::text)) AS opened_at,
            max(e.event_time) FILTER (WHERE ((e.event_type)::text = 'support_request_resolved'::text)) AS resolved_at
           FROM (public.support_request sr
             JOIN public.support_lifecycle_event e ON (((e.support_request_id)::text = (sr.support_request_id)::text)))
          GROUP BY sr.support_request_id
        ), support_metrics AS (
         SELECT support_lifecycle.support_request_id,
            support_lifecycle.opened_at,
            support_lifecycle.resolved_at,
                CASE
                    WHEN ((support_lifecycle.resolved_at IS NOT NULL) AND (support_lifecycle.opened_at IS NOT NULL) AND (support_lifecycle.resolved_at >= support_lifecycle.opened_at)) THEN (EXTRACT(epoch FROM (support_lifecycle.resolved_at - support_lifecycle.opened_at)) / 3600.0)
                    ELSE NULL::numeric
                END AS resolution_hours
           FROM support_lifecycle
        )
 SELECT 1 AS summary_id,
    count(*) AS total_support_requests,
    count(*) FILTER (WHERE (resolved_at IS NOT NULL)) AS resolved_requests,
    count(*) FILTER (WHERE (resolved_at IS NULL)) AS unresolved_requests,
    round((((count(*) FILTER (WHERE (resolved_at IS NOT NULL)))::numeric / (NULLIF(count(*), 0))::numeric) * (100)::numeric), 2) AS resolution_rate_pct,
    round((percentile_cont((0.50)::double precision) WITHIN GROUP (ORDER BY ((resolution_hours)::double precision)) FILTER (WHERE (resolution_hours IS NOT NULL)))::numeric, 2) AS median_resolution_hours,
    round(avg(resolution_hours) FILTER (WHERE (resolution_hours IS NOT NULL)), 2) AS avg_resolution_hours,
    round((percentile_cont((0.95)::double precision) WITHIN GROUP (ORDER BY ((resolution_hours)::double precision)) FILTER (WHERE (resolution_hours IS NOT NULL)))::numeric, 2) AS p95_resolution_hours
   FROM support_metrics;


--
-- Name: VIEW vw_support_summary; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_support_summary IS 'Power BI one-row Support KPI serving view. Overall resolution statistics are calculated directly from request-level lifecycle data; monthly medians are never averaged.';


--
-- Name: vw_website_monthly; Type: VIEW; Schema: dashboard; Owner: -
--

CREATE VIEW dashboard.vw_website_monthly AS
 WITH params AS (
         SELECT ('2024-04-01 00:00:00'::timestamp without time zone AT TIME ZONE 'Asia/Jerusalem'::text) AS observation_start,
            '2026-01-01 02:00:00+02'::timestamp with time zone AS observation_end
        ), bounded_live_periods AS (
         SELECT wlp.website_id,
            GREATEST(wlp.valid_from, p.observation_start) AS effective_valid_from,
            LEAST(COALESCE(wlp.valid_to, p.observation_end), p.observation_end) AS effective_valid_to
           FROM (public.website_live_period wlp
             CROSS JOIN params p)
          WHERE ((wlp.valid_from < p.observation_end) AND (COALESCE(wlp.valid_to, p.observation_end) > p.observation_start))
        ), website_month_base AS (
         SELECT DISTINCT blp.website_id,
            (gs.month_ts)::date AS month_start
           FROM (bounded_live_periods blp
             CROSS JOIN LATERAL ( SELECT generate_series(date_trunc('month'::text, (blp.effective_valid_from AT TIME ZONE 'Asia/Jerusalem'::text)), date_trunc('month'::text, ((blp.effective_valid_to - '00:00:00.000001'::interval) AT TIME ZONE 'Asia/Jerusalem'::text)), '1 mon'::interval) AS month_ts) gs)
          WHERE (blp.effective_valid_to > blp.effective_valid_from)
        ), website_monthly AS (
         SELECT website_month_base.month_start,
            count(*) AS website_month_rows,
            count(DISTINCT website_month_base.website_id) AS websites_observed
           FROM website_month_base
          GROUP BY website_month_base.month_start
        ), session_lifecycle AS (
         SELECT session_lifecycle_event.session_id,
            count(*) FILTER (WHERE ((session_lifecycle_event.event_type)::text = 'session_started'::text)) AS start_count,
            count(*) FILTER (WHERE ((session_lifecycle_event.event_type)::text = 'session_ended'::text)) AS end_count,
            min(session_lifecycle_event.event_time) FILTER (WHERE ((session_lifecycle_event.event_type)::text = 'session_started'::text)) AS started_at,
            max(session_lifecycle_event.event_time) FILTER (WHERE ((session_lifecycle_event.event_type)::text = 'session_ended'::text)) AS ended_at
           FROM public.session_lifecycle_event
          GROUP BY session_lifecycle_event.session_id
        ), session_detail AS (
         SELECT s.session_id,
            s.website_id,
            s.visitor_id,
            sl.started_at,
            sl.ended_at,
                CASE
                    WHEN ((sl.start_count = 1) AND (sl.end_count = 1) AND (sl.started_at IS NOT NULL) AND (sl.ended_at IS NOT NULL) AND (sl.ended_at >= sl.started_at)) THEN EXTRACT(epoch FROM (sl.ended_at - sl.started_at))
                    ELSE NULL::numeric
                END AS duration_seconds
           FROM (public.audience_session s
             JOIN session_lifecycle sl ON (((sl.session_id)::text = (s.session_id)::text)))
          WHERE ((sl.start_count = 1) AND (sl.started_at IS NOT NULL))
        ), session_monthly AS (
         SELECT (date_trunc('month'::text, (session_detail.started_at AT TIME ZONE 'Asia/Jerusalem'::text)))::date AS month_start,
            count(*) AS sessions,
            count(*) FILTER (WHERE (session_detail.duration_seconds IS NOT NULL)) AS valid_duration_sessions,
            round(((percentile_cont((0.50)::double precision) WITHIN GROUP (ORDER BY ((session_detail.duration_seconds)::double precision)) FILTER (WHERE (session_detail.duration_seconds IS NOT NULL)) / (60.0)::double precision))::numeric, 2) AS median_session_minutes,
            round((avg(session_detail.duration_seconds) FILTER (WHERE (session_detail.duration_seconds IS NOT NULL)) / 60.0), 2) AS avg_session_minutes,
            round(((percentile_cont((0.25)::double precision) WITHIN GROUP (ORDER BY ((session_detail.duration_seconds)::double precision)) FILTER (WHERE (session_detail.duration_seconds IS NOT NULL)) / (60.0)::double precision))::numeric, 2) AS p25_session_minutes,
            round(((percentile_cont((0.75)::double precision) WITHIN GROUP (ORDER BY ((session_detail.duration_seconds)::double precision)) FILTER (WHERE (session_detail.duration_seconds IS NOT NULL)) / (60.0)::double precision))::numeric, 2) AS p75_session_minutes,
            round(((percentile_cont((0.95)::double precision) WITHIN GROUP (ORDER BY ((session_detail.duration_seconds)::double precision)) FILTER (WHERE (session_detail.duration_seconds IS NOT NULL)) / (60.0)::double precision))::numeric, 2) AS p95_session_minutes
           FROM session_detail
          GROUP BY ((date_trunc('month'::text, (session_detail.started_at AT TIME ZONE 'Asia/Jerusalem'::text)))::date)
        ), interaction_monthly AS (
         SELECT (date_trunc('month'::text, (e.event_time AT TIME ZONE 'Asia/Jerusalem'::text)))::date AS month_start,
            count(*) FILTER (WHERE ((e.event_type)::text = 'page_viewed'::text)) AS page_views,
            count(*) FILTER (WHERE ((e.event_type)::text = 'form_submitted'::text)) AS forms_submitted,
            count(*) FILTER (WHERE ((e.event_type)::text = 'failure_friction'::text)) AS friction_events
           FROM public.audience_interaction_event e
          GROUP BY ((date_trunc('month'::text, (e.event_time AT TIME ZONE 'Asia/Jerusalem'::text)))::date)
        ), comment_monthly AS (
         SELECT (date_trunc('month'::text, (cle.event_time AT TIME ZONE 'Asia/Jerusalem'::text)))::date AS month_start,
            count(*) AS comments_posted,
            count(DISTINCT p.website_id) AS websites_with_comments
           FROM ((public.comment_lifecycle_event cle
             JOIN public.comment c ON (((c.comment_id)::text = (cle.comment_id)::text)))
             JOIN public.page p ON (((p.page_id)::text = (c.page_id)::text)))
          WHERE ((cle.event_type)::text = 'comment_posted'::text)
          GROUP BY ((date_trunc('month'::text, (cle.event_time AT TIME ZONE 'Asia/Jerusalem'::text)))::date)
        ), all_months AS (
         SELECT website_monthly.month_start
           FROM website_monthly
        UNION
         SELECT session_monthly.month_start
           FROM session_monthly
        UNION
         SELECT interaction_monthly.month_start
           FROM interaction_monthly
        UNION
         SELECT comment_monthly.month_start
           FROM comment_monthly
        )
 SELECT m.month_start,
    to_char((m.month_start)::timestamp with time zone, 'Mon YYYY'::text) AS month_label,
    (((EXTRACT(year FROM m.month_start))::integer * 100) + (EXTRACT(month FROM m.month_start))::integer) AS month_sort,
        CASE
            WHEN (m.month_start = '2026-01-01'::date) THEN true
            ELSE false
        END AS is_partial_period,
    COALESCE(wm.website_month_rows, (0)::bigint) AS website_month_rows,
    COALESCE(wm.websites_observed, (0)::bigint) AS websites_observed,
    COALESCE(sm.sessions, (0)::bigint) AS sessions,
    COALESCE(im.page_views, (0)::bigint) AS page_views,
        CASE
            WHEN (COALESCE(sm.sessions, (0)::bigint) > 0) THEN round(((COALESCE(im.page_views, (0)::bigint))::numeric / (sm.sessions)::numeric), 2)
            ELSE NULL::numeric
        END AS pages_per_session,
    COALESCE(im.forms_submitted, (0)::bigint) AS forms_submitted,
        CASE
            WHEN (COALESCE(sm.sessions, (0)::bigint) > 0) THEN round((((COALESCE(im.forms_submitted, (0)::bigint))::numeric / (sm.sessions)::numeric) * (100)::numeric), 2)
            ELSE NULL::numeric
        END AS forms_per_100_sessions,
    COALESCE(im.friction_events, (0)::bigint) AS friction_events,
        CASE
            WHEN (COALESCE(sm.sessions, (0)::bigint) > 0) THEN round((((COALESCE(im.friction_events, (0)::bigint))::numeric / (sm.sessions)::numeric) * (100)::numeric), 2)
            ELSE NULL::numeric
        END AS friction_per_100_sessions,
    COALESCE(sm.valid_duration_sessions, (0)::bigint) AS valid_duration_sessions,
    sm.median_session_minutes,
    sm.avg_session_minutes,
    sm.p25_session_minutes,
    sm.p75_session_minutes,
    sm.p95_session_minutes,
    COALESCE(cm.comments_posted, (0)::bigint) AS comments_posted,
    COALESCE(cm.websites_with_comments, (0)::bigint) AS websites_with_comments,
        CASE
            WHEN (COALESCE(sm.sessions, (0)::bigint) > 0) THEN round((((COALESCE(cm.comments_posted, (0)::bigint))::numeric / (sm.sessions)::numeric) * (100)::numeric), 2)
            ELSE NULL::numeric
        END AS comments_per_100_sessions
   FROM ((((all_months m
     LEFT JOIN website_monthly wm ON ((wm.month_start = m.month_start)))
     LEFT JOIN session_monthly sm ON ((sm.month_start = m.month_start)))
     LEFT JOIN interaction_monthly im ON ((im.month_start = m.month_start)))
     LEFT JOIN comment_monthly cm ON ((cm.month_start = m.month_start)))
  WHERE (m.month_start >= '2024-04-01'::date);


--
-- Name: VIEW vw_website_monthly; Type: COMMENT; Schema: dashboard; Owner: -
--

COMMENT ON VIEW dashboard.vw_website_monthly IS 'Power BI consolidated monthly serving view for Website Audience Activity, Engagement & Member Comments. Grain: one row per analytical calendar month. Source domains are aggregated separately before joining to prevent fanout. Jan 2026 is explicitly flagged as partial.';


--
