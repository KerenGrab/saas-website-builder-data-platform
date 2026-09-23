
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Feature 03: Websites Created Before First Paid
--
-- Source database: saas_website_builder_9h
--
-- Purpose:
-- Count websites created by each account before its
-- first transition to a Paid subscription.
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

-- Step 2: Identify website creation timestamps
website_creation AS (
    SELECT
        website_id,
        MIN(event_time) AS website_created_at

    FROM public.website_lifecycle_event

    WHERE event_type = 'website_created'

    GROUP BY website_id
),

-- Step 3: Calculate website features per account
account_website_features AS (
    SELECT
        fp.account_id,

        COUNT(DISTINCT w.website_id) FILTER (
            WHERE wc.website_created_at < fp.first_paid_at
        ) AS websites_created_before_paid

    FROM first_paid AS fp

    LEFT JOIN public.website AS w
        ON w.account_id = fp.account_id

    LEFT JOIN website_creation AS wc
        ON wc.website_id = w.website_id

    GROUP BY fp.account_id
)

-- Step 4: Validate the feature distribution
SELECT
    websites_created_before_paid,

    COUNT(*) AS account_count

FROM account_website_features

GROUP BY websites_created_before_paid

ORDER BY websites_created_before_paid;