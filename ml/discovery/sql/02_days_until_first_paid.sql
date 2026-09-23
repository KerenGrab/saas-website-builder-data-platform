
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Feature 01: Days Until First Paid
--
-- Source database: saas_website_builder_9h
--
-- Purpose:
-- Calculate the number of days between account creation
-- and the first transition to a Paid subscription.
--
-- Prediction timestamp: first_paid_at
-- Grain: One row per Ever Paid account
--
-- READ ONLY: No database modifications.
-- ============================================================

-- Step 1: Identify the creation timestamp for each account
WITH account_creation AS (
    SELECT
        account_id,
        event_time AS created_at

    FROM public.account_lifecycle_event

    WHERE event_type = 'account_created'
),

-- Step 2: Identify the first Paid timestamp for each account
first_paid AS (
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

-- Step 3: Calculate the feature at account level
feature_data AS (
    SELECT
        fp.account_id,
        ac.created_at,
        fp.first_paid_at,

        EXTRACT(
            EPOCH FROM (
                fp.first_paid_at - ac.created_at
            )
        ) / 86400.0 AS days_until_first_paid

    FROM first_paid AS fp

    LEFT JOIN account_creation AS ac
        ON fp.account_id = ac.account_id
)

-- Step 4: Validate the feature
SELECT
    COUNT(*) AS total_paid_accounts,

    COUNT(*) FILTER (
        WHERE created_at IS NULL
    ) AS missing_creation_dates,

    COUNT(*) FILTER (
        WHERE days_until_first_paid < 0
    ) AS negative_durations,

    ROUND(
        MIN(days_until_first_paid)::numeric, 2
    ) AS minimum_days,

    ROUND(
        AVG(days_until_first_paid)::numeric, 2
    ) AS average_days,

    ROUND(
        MAX(days_until_first_paid)::numeric, 2
    ) AS maximum_days

FROM feature_data;