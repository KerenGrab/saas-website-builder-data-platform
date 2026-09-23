
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Feature 02: Product Activity Before First Paid
--
-- Source database: saas_website_builder_9h
--
-- Purpose:
-- Calculate account-level product activity features
-- using only events recorded between account creation
-- and the first transition to a Paid subscription.
--
-- Prediction timestamp: first_paid_at
-- Grain: One row per Ever Paid account
--
-- READ ONLY: No database modifications.
-- ============================================================

-- Step 1: Identify First Paid for every account
WITH first_paid AS (
    SELECT
        spp.account_id,
        MIN(spp.valid_from) AS first_paid_at

    FROM public.subscription_plan_period AS spp

    JOIN public.plan_catalog AS pc
        ON spp.plan_id = pc.plan_id

    WHERE LOWER(pc.plan_name)
        IN ('standard', 'premium')

    GROUP BY spp.account_id
),

-- Step 2: Identify account creation timestamps
account_creation AS (
    SELECT
        account_id,
        event_time AS created_at

    FROM public.account_lifecycle_event

    WHERE event_type = 'account_created'
),

-- Step 3: Calculate pre-paid activity per account
account_features AS (
    SELECT
        fp.account_id,

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

    FROM first_paid AS fp

    JOIN account_creation AS ac
        ON ac.account_id = fp.account_id

    LEFT JOIN public.product_behaviour_event AS e
        ON e.account_id = fp.account_id

       -- Include events from account creation onward
       AND e.event_time >= ac.created_at

       -- Exclude events at or after First Paid
       AND e.event_time < fp.first_paid_at

    GROUP BY fp.account_id
)

-- Step 4: Validate account-level features
SELECT
    COUNT(*) AS feature_rows,

    COUNT(DISTINCT account_id)
        AS distinct_accounts,

    SUM(total_product_events)
        AS total_events,

    SUM(product_access_count)
        AS product_access_events,

    SUM(locked_attempt_count)
        AS locked_attempt_events,

    SUM(feature_used_count)
        AS feature_used_events,

    SUM(analytics_view_count)
        AS analytics_view_events,

    SUM(other_event_count)
        AS other_events

FROM account_features;