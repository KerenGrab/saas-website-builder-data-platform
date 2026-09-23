
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Work Package 03: M6 Feature Assembly
--
-- Database: saas_website_builder_9h
-- Observation cutoff: 2026-01-01 00:00:00 UTC
--
-- Purpose:
-- Assemble validated historical features with the M6 target.
-- Verify population, labels, uniqueness, feature quality,
-- temporal availability and split compatibility.
--
-- Grain: One row per eligible Ever Paid account.
--
-- READ ONLY: No database modifications.
-- ============================================================

WITH

-- ============================================================
-- 1. Configuration
-- ============================================================

config AS (
    SELECT
        TIMESTAMPTZ '2026-01-01 00:00:00+00'
            AS observation_cutoff
),

-- ============================================================
-- 2. Identify First Paid
-- ============================================================

first_paid AS (
    SELECT
        spp.account_id,
        MIN(spp.valid_from) AS first_paid_at

    FROM public.subscription_plan_period AS spp

    JOIN public.plan_catalog AS pc
        ON pc.plan_id = spp.plan_id

    WHERE LOWER(pc.plan_name)
        IN ('standard', 'premium')

    GROUP BY spp.account_id
),

-- ============================================================
-- 3. M6 eligible population and proposed chronological split
-- ============================================================

eligible_accounts AS (
    SELECT
        fp.account_id,
        fp.first_paid_at,

        fp.first_paid_at + INTERVAL '6 months'
            AS horizon_at,

        CASE

            WHEN fp.first_paid_at >=
                 TIMESTAMPTZ '2024-01-01 00:00:00+00'

             AND fp.first_paid_at <
                 TIMESTAMPTZ '2025-01-01 00:00:00+00'
                THEN 'TRAIN'

            WHEN fp.first_paid_at >=
                 TIMESTAMPTZ '2025-01-01 00:00:00+00'

             AND fp.first_paid_at <
                 TIMESTAMPTZ '2025-04-01 00:00:00+00'
                THEN 'VALIDATION'

            WHEN fp.first_paid_at >=
                 TIMESTAMPTZ '2025-04-01 00:00:00+00'

             AND fp.first_paid_at <
                 TIMESTAMPTZ '2025-07-01 00:00:00+00'
                THEN 'TEST'

            ELSE 'OUTSIDE_SPLIT'

        END AS split_name

    FROM first_paid AS fp

    CROSS JOIN config AS c

    WHERE fp.first_paid_at + INTERVAL '6 months'
          < c.observation_cutoff
),

-- ============================================================
-- 4. Reconstruct subscription state at M6
-- ============================================================

state_flags AS (
    SELECT
        ea.*,

        EXISTS (
            SELECT 1

            FROM public.subscription_plan_period AS spp

            JOIN public.plan_catalog AS pc
                ON pc.plan_id = spp.plan_id

            WHERE spp.account_id = ea.account_id

              AND LOWER(pc.plan_name)
                  IN ('standard', 'premium')

              AND spp.valid_from <= ea.horizon_at

              AND (
                  spp.valid_to > ea.horizon_at
                  OR spp.valid_to IS NULL
              )
        ) AS is_paid,

        EXISTS (
            SELECT 1

            FROM public.subscription_plan_period AS spp

            JOIN public.plan_catalog AS pc
                ON pc.plan_id = spp.plan_id

            WHERE spp.account_id = ea.account_id

              AND LOWER(pc.plan_name) = 'free'

              AND spp.valid_from <= ea.horizon_at

              AND (
                  spp.valid_to > ea.horizon_at
                  OR spp.valid_to IS NULL
              )
        ) AS is_free,

        EXISTS (
            SELECT 1

            FROM public.account_lifecycle_event AS ale

            WHERE ale.account_id = ea.account_id

              AND ale.event_type = 'account_closure'

              AND ale.event_time <= ea.horizon_at
        ) AS is_closed

    FROM eligible_accounts AS ea
),

-- ============================================================
-- 5. M6 Target
-- ============================================================

target_data AS (
    SELECT
        account_id,
        first_paid_at,
        horizon_at,
        split_name,

        CASE

            WHEN is_paid AND (is_free OR is_closed)
                THEN NULL

            WHEN is_paid
                THEN 1

            WHEN is_free OR is_closed
                THEN 0

            ELSE NULL

        END AS target_m6

    FROM state_flags
),

-- ============================================================
-- 6. Account creation timestamps
-- ============================================================

account_creation AS (
    SELECT
        account_id,

        MIN(event_time) AS created_at,

        COUNT(*) AS creation_event_count

    FROM public.account_lifecycle_event

    WHERE event_type = 'account_created'

    GROUP BY account_id
),

-- ============================================================
-- 7. Product activity features before First Paid
-- ============================================================

product_features AS (
    SELECT
        ea.account_id,

        COUNT(e.event_id)
            AS total_product_events,

        COUNT(e.event_id) FILTER (
            WHERE e.event_type = 'product_accessed'
        ) AS product_access_count,

        COUNT(e.event_id) FILTER (
            WHERE e.event_type = 'locked_feature_attempted'
        ) AS locked_attempt_count,

        COUNT(e.event_id) FILTER (
            WHERE e.event_type = 'feature_used'
        ) AS feature_used_count,

        COUNT(e.event_id) FILTER (
            WHERE e.event_type = 'website_analytics_viewed'
        ) AS analytics_view_count,

        COUNT(e.event_id) FILTER (
            WHERE e.event_type NOT IN (
                'product_accessed',
                'locked_feature_attempted',
                'feature_used',
                'website_analytics_viewed'
            )
        ) AS other_event_count

    FROM eligible_accounts AS ea

    LEFT JOIN account_creation AS ac
        ON ac.account_id = ea.account_id

    LEFT JOIN public.product_behaviour_event AS e
        ON e.account_id = ea.account_id

       AND e.event_time >= ac.created_at

       AND e.event_time < ea.first_paid_at

    GROUP BY ea.account_id
),

-- ============================================================
-- 8. Website creation timestamps
-- ============================================================

website_creation AS (
    SELECT
        website_id,

        MIN(event_time) AS website_created_at

    FROM public.website_lifecycle_event

    WHERE event_type = 'website_created'

    GROUP BY website_id
),

-- ============================================================
-- 9. Reconstruct website state at First Paid
-- ============================================================

website_asof AS (
    SELECT
        ea.account_id,
        ea.first_paid_at,

        w.website_id,
        wc.website_created_at,

        (
            wc.website_created_at < ea.first_paid_at
        ) AS created_before_paid,

        EXISTS (
            SELECT 1

            FROM public.website_live_period AS lp

            WHERE lp.website_id = w.website_id

              AND lp.valid_from < ea.first_paid_at

              AND (
                  lp.valid_to > ea.first_paid_at
                  OR lp.valid_to IS NULL
              )
        ) AS was_live_at_first_paid

    FROM eligible_accounts AS ea

    LEFT JOIN public.website AS w
        ON w.account_id = ea.account_id

    LEFT JOIN website_creation AS wc
        ON wc.website_id = w.website_id
),

-- ============================================================
-- 10. Website features at account level
-- ============================================================

website_features AS (
    SELECT
        account_id,

        COUNT(DISTINCT website_id) FILTER (
            WHERE created_before_paid
        ) AS websites_created_before_paid,

        COUNT(DISTINCT website_id) FILTER (
            WHERE created_before_paid
              AND was_live_at_first_paid
        ) AS live_websites_at_first_paid

    FROM website_asof

    GROUP BY account_id
),

-- ============================================================
-- 11. Assemble the logical ML Dataset
-- ============================================================

feature_dataset AS (
    SELECT
        td.account_id,
        td.first_paid_at,
        td.horizon_at,
        td.split_name,

        td.target_m6,

        -- Feature 01
        EXTRACT(
            EPOCH FROM (
                td.first_paid_at - ac.created_at
            )
        ) / 86400.0 AS days_until_first_paid,

        -- Feature 02
        pf.total_product_events,
        pf.product_access_count,
        pf.locked_attempt_count,
        pf.feature_used_count,
        pf.analytics_view_count,
        pf.other_event_count,

        -- Feature 03
        wf.websites_created_before_paid,

        -- Feature 04
        wf.live_websites_at_first_paid,

        -- Quality diagnostics
        ac.creation_event_count,

        (
            pf.account_id IS NULL
            OR wf.account_id IS NULL
        ) AS missing_feature_join

    FROM target_data AS td

    LEFT JOIN account_creation AS ac
        ON ac.account_id = td.account_id

    LEFT JOIN product_features AS pf
        ON pf.account_id = td.account_id

    LEFT JOIN website_features AS wf
        ON wf.account_id = td.account_id
),

-- ============================================================
-- 12. Consolidated quality and population report
-- ============================================================

quality_report AS (
    SELECT
        COALESCE(split_name, 'ALL')
            AS result_group,

        COUNT(*) AS dataset_rows,

        COUNT(DISTINCT account_id)
            AS distinct_accounts,

        COUNT(*) - COUNT(DISTINCT account_id)
            AS duplicate_account_rows,

        -- Target distribution
        COUNT(*) FILTER (
            WHERE target_m6 = 1
        ) AS paid_accounts,

        COUNT(*) FILTER (
            WHERE target_m6 = 0
        ) AS not_paid_accounts,

        COUNT(*) FILTER (
            WHERE target_m6 IS NULL
        ) AS unknown_accounts,

        -- Feature completeness
        COUNT(*) FILTER (
            WHERE days_until_first_paid IS NULL
        ) AS missing_account_age,

        COUNT(*) FILTER (
            WHERE missing_feature_join
        ) AS missing_feature_joins,

        COUNT(*) FILTER (
            WHERE creation_event_count IS DISTINCT FROM 1
        ) AS invalid_creation_event_counts,

        COUNT(*) FILTER (
            WHERE days_until_first_paid < 0
        ) AS negative_account_age,

        -- Product activity reconciliation
        COUNT(*) FILTER (
            WHERE total_product_events IS NULL

               OR total_product_events <> (
                   product_access_count
                   + locked_attempt_count
                   + feature_used_count
                   + analytics_view_count
                   + other_event_count
               )
        ) AS product_count_mismatches,

        -- Website feature reconciliation
        COUNT(*) FILTER (
            WHERE websites_created_before_paid IS NULL

               OR live_websites_at_first_paid IS NULL

               OR live_websites_at_first_paid >
                  websites_created_before_paid
        ) AS website_feature_mismatches,

        -- Split coverage
        COUNT(*) FILTER (
            WHERE split_name = 'OUTSIDE_SPLIT'
        ) AS accounts_outside_split,

        -- Temporal availability diagnostic
        COUNT(*) FILTER (
            WHERE (
                split_name = 'TRAIN'
                AND horizon_at >=
                    TIMESTAMPTZ '2025-01-01 00:00:00+00'
            )

            OR (
                split_name = 'VALIDATION'
                AND horizon_at >=
                    TIMESTAMPTZ '2025-04-01 00:00:00+00'
            )
        ) AS labels_not_ready_at_next_split_start,

        -- Feature summaries
        ROUND(
            AVG(days_until_first_paid)::numeric, 2
        ) AS average_days_until_paid,

        ROUND(
            AVG(total_product_events)::numeric, 2
        ) AS average_product_events,

        SUM(total_product_events)
            AS total_product_events,

        SUM(websites_created_before_paid)
            AS total_prior_websites,

        SUM(live_websites_at_first_paid)
            AS total_live_websites,

        ROUND(
            AVG(websites_created_before_paid)::numeric, 2
        ) AS average_prior_websites,

        ROUND(
            AVG(live_websites_at_first_paid)::numeric, 2
        ) AS average_live_websites

    FROM feature_dataset

    GROUP BY GROUPING SETS (
        (split_name),
        ()
    )
)

-- ============================================================
-- 13. Final consolidated output
-- ============================================================

SELECT *

FROM quality_report

ORDER BY
    CASE result_group
        WHEN 'ALL' THEN 0
        WHEN 'TRAIN' THEN 1
        WHEN 'VALIDATION' THEN 2
        WHEN 'TEST' THEN 3
        ELSE 4
    END;