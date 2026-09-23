
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Feature 04: Live Websites at First Paid
-- Consolidated Discovery & Validation
--
-- Database: saas_website_builder_9h
-- Prediction timestamp: first_paid_at
-- Grain: One row per Ever Paid account
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

    WHERE LOWER(pc.plan_name)
        IN ('standard', 'premium')

    GROUP BY spp.account_id
),

-- ============================================================
-- 2. Identify website creation timestamps
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
-- 3. Reconstruct website state at First Paid
-- ============================================================

website_asof AS (
    SELECT
        fp.account_id,
        fp.first_paid_at,
        w.website_id,
        wc.website_created_at,

        (
            wc.website_created_at < fp.first_paid_at
        ) AS created_before_paid,

        EXISTS (
            SELECT 1

            FROM public.website_live_period AS lp

            WHERE lp.website_id = w.website_id

              AND lp.valid_from < fp.first_paid_at

              AND (
                  lp.valid_to > fp.first_paid_at
                  OR lp.valid_to IS NULL
              )
        ) AS was_live_at_first_paid

    FROM first_paid AS fp

    LEFT JOIN public.website AS w
        ON w.account_id = fp.account_id

    LEFT JOIN website_creation AS wc
        ON wc.website_id = w.website_id
),

-- ============================================================
-- 4. Build one feature row per account
-- ============================================================

account_features AS (
    SELECT
        account_id,

        COUNT(DISTINCT website_id) FILTER (
            WHERE created_before_paid
        ) AS websites_created_before_paid,

        COUNT(DISTINCT website_id) FILTER (
            WHERE created_before_paid
              AND was_live_at_first_paid
        ) AS live_websites_at_first_paid,

        COUNT(website_id) FILTER (
            WHERE website_created_at IS NULL
        ) AS missing_creation_events

    FROM website_asof

    GROUP BY account_id
),

-- ============================================================
-- 5. Calculate summary metrics
-- ============================================================

summary AS (
    SELECT
        COUNT(*) AS ever_paid_accounts,

        COUNT(*) FILTER (
            WHERE websites_created_before_paid > 0
        ) AS accounts_with_prior_websites,

        SUM(websites_created_before_paid)
            AS total_prior_websites,

        COUNT(*) FILTER (
            WHERE live_websites_at_first_paid > 0
        ) AS accounts_with_live_websites,

        COUNT(*) FILTER (
            WHERE live_websites_at_first_paid = 0
        ) AS accounts_without_live_websites,

        SUM(live_websites_at_first_paid)
            AS total_live_websites,

        MIN(live_websites_at_first_paid)
            AS minimum_live_websites,

        MAX(live_websites_at_first_paid)
            AS maximum_live_websites,

        SUM(missing_creation_events)
            AS missing_creation_events,

        COUNT(*) FILTER (
            WHERE live_websites_at_first_paid >
                  websites_created_before_paid
        ) AS accounts_live_exceeds_created

    FROM account_features
),

-- ============================================================
-- 6. Calculate account-level distribution
-- ============================================================

distribution AS (
    SELECT
        live_websites_at_first_paid,
        COUNT(*) AS account_count

    FROM account_features

    GROUP BY live_websites_at_first_paid
),

-- ============================================================
-- 7. Reconcile distribution with summary
-- ============================================================

distribution_checks AS (
    SELECT
        COALESCE(
            SUM(d.account_count), 0
        ) - s.ever_paid_accounts
            AS account_count_difference,

        COALESCE(
            SUM(
                d.live_websites_at_first_paid *
                d.account_count
            ), 0
        ) - s.total_live_websites
            AS live_website_count_difference

    FROM distribution AS d

    CROSS JOIN summary AS s

    GROUP BY
        s.ever_paid_accounts,
        s.total_live_websites
),

-- ============================================================
-- 8. Build one consolidated report
-- ============================================================

report AS (

    -- Summary metrics
    SELECT
        1 AS section_order,
        v.metric_order,

        'SUMMARY'::text AS result_section,

        v.metric::text AS metric,

        v.metric_value AS result_value

    FROM summary AS s

    CROSS JOIN LATERAL (
        VALUES
        (1, 'ever_paid_accounts',
            s.ever_paid_accounts::numeric),

        (2, 'accounts_with_prior_websites',
            s.accounts_with_prior_websites::numeric),

        (3, 'total_prior_websites',
            s.total_prior_websites::numeric),

        (4, 'accounts_with_live_websites',
            s.accounts_with_live_websites::numeric),

        (5, 'accounts_without_live_websites',
            s.accounts_without_live_websites::numeric),

        (6, 'total_live_websites',
            s.total_live_websites::numeric),

        (7, 'minimum_live_websites',
            s.minimum_live_websites::numeric),

        (8, 'maximum_live_websites',
            s.maximum_live_websites::numeric)

    ) AS v(metric_order, metric, metric_value)

    UNION ALL

    -- Distribution
    SELECT
        2 AS section_order,

        d.live_websites_at_first_paid::integer
            AS metric_order,

        'DISTRIBUTION'::text AS result_section,

        (
            'live_websites=' ||
            d.live_websites_at_first_paid::text
        ) AS metric,

        d.account_count::numeric AS result_value

    FROM distribution AS d

    UNION ALL

    -- Data quality and reconciliation checks
    SELECT
        3 AS section_order,

        v.metric_order,

        'CHECK'::text AS result_section,

        v.metric::text AS metric,

        v.metric_value AS result_value

    FROM summary AS s

    CROSS JOIN distribution_checks AS dc

    CROSS JOIN LATERAL (
        VALUES
        (1, 'missing_creation_events',
            s.missing_creation_events::numeric),

        (2, 'accounts_live_exceeds_created',
            s.accounts_live_exceeds_created::numeric),

        (3, 'distribution_account_difference',
            dc.account_count_difference::numeric),

        (4, 'distribution_live_difference',
            dc.live_website_count_difference::numeric)

    ) AS v(metric_order, metric, metric_value)
)

-- ============================================================
-- 9. Final consolidated output
-- ============================================================

SELECT
    result_section,
    metric,
    result_value

FROM report

ORDER BY
    section_order,
    metric_order;