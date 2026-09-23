
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Work Package 03: M6 Training Dataset Export
--
-- Database: saas_website_builder_9h
-- Observation cutoff: 2026-01-01 00:00:00 UTC
--
-- Output: One row per eligible Ever Paid account
-- Target: Paid state six months after First Paid
--
-- READ ONLY: No database modifications.
-- ============================================================

WITH

-- ============================================================
-- 1. Identify First Paid
-- ============================================================

first_paid AS (
    SELECT
        spp.account_id,
        MIN(spp.valid_from) AS first_paid_at

    FROM public.subscription_plan_period AS spp

    JOIN public.plan_catalog AS pc
        ON pc.plan_id = spp.plan_id

    WHERE LOWER(pc.plan_name) IN ('standard', 'premium')

    GROUP BY spp.account_id
),

-- ============================================================
-- 2. Calculate M6 using UTC calendar arithmetic
-- ============================================================

candidate_accounts AS (
    SELECT
        account_id,
        first_paid_at,

        (
            (first_paid_at AT TIME ZONE 'UTC')
            + INTERVAL '6 months'
        ) AT TIME ZONE 'UTC' AS horizon_at

    FROM first_paid
),

-- ============================================================
-- 3. Keep accounts with a complete M6 observation
-- ============================================================

eligible_accounts AS (
    SELECT
        ca.account_id,
        ca.first_paid_at,
        ca.horizon_at,

        CASE
            WHEN ca.first_paid_at <
                TIMESTAMPTZ '2025-01-01 00:00:00+00'
                THEN 'TRAIN'

            WHEN ca.first_paid_at <
                TIMESTAMPTZ '2025-04-01 00:00:00+00'
                THEN 'VALIDATION'

            WHEN ca.first_paid_at <
                TIMESTAMPTZ '2025-07-01 00:00:00+00'
                THEN 'TEST'

            ELSE 'OUTSIDE_SPLIT'
        END AS split_name

    FROM candidate_accounts AS ca

    WHERE ca.horizon_at <
        TIMESTAMPTZ '2026-01-01 00:00:00+00'
),

-- ============================================================
-- 4. Reconstruct M6 target state
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
-- 5. Define the binary target
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
-- 6. Account creation
-- ============================================================

account_creation AS (
    SELECT
        account_id,
        MIN(event_time) AS created_at

    FROM public.account_lifecycle_event

    WHERE event_type = 'account_created'

    GROUP BY account_id
),

-- ============================================================
-- 7. Historical product activity
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
-- 9. Historical website features
-- ============================================================

website_features AS (
    SELECT
        ea.account_id,

        COUNT(DISTINCT w.website_id) FILTER (
            WHERE wc.website_created_at < ea.first_paid_at
        ) AS websites_created_before_paid,

        COUNT(DISTINCT w.website_id) FILTER (
            WHERE wc.website_created_at < ea.first_paid_at

              AND EXISTS (
                  SELECT 1

                  FROM public.website_live_period AS lp

                  WHERE lp.website_id = w.website_id

                    AND lp.valid_from < ea.first_paid_at

                    AND (
                        lp.valid_to > ea.first_paid_at
                        OR lp.valid_to IS NULL
                    )
              )
        ) AS live_websites_at_first_paid

    FROM eligible_accounts AS ea

    LEFT JOIN public.website AS w
        ON w.account_id = ea.account_id

    LEFT JOIN website_creation AS wc
        ON wc.website_id = w.website_id

    GROUP BY ea.account_id
)

-- ============================================================
-- 10. Export one ML dataset row per account
-- ============================================================

SELECT
    -- Metadata
    td.account_id,
    td.first_paid_at,
    td.horizon_at,
    td.split_name,

    -- Feature 01: Account age
    EXTRACT(
        EPOCH FROM (
            td.first_paid_at - ac.created_at
        )
    ) / 86400.0 AS days_until_first_paid,

    -- Feature 02: Product activity
    pf.total_product_events,
    pf.product_access_count,
    pf.locked_attempt_count,
    pf.feature_used_count,
    pf.analytics_view_count,
    pf.other_event_count,

    -- Feature 03: Created websites
    wf.websites_created_before_paid,

    -- Feature 04: Live websites
    wf.live_websites_at_first_paid,

    -- Target
    td.target_m6

FROM target_data AS td

LEFT JOIN account_creation AS ac
    ON ac.account_id = td.account_id

LEFT JOIN product_features AS pf
    ON pf.account_id = td.account_id

LEFT JOIN website_features AS wf
    ON wf.account_id = td.account_id

ORDER BY
    td.first_paid_at,
    td.account_id;