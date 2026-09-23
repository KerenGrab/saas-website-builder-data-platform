
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Work Package 02
-- Training Population & Target Contract
--
-- Horizons: M3 and M6
-- Database: saas_website_builder_9h
--
-- Observation cutoff:
-- 2026-01-01 00:00:00 UTC
--
-- READ ONLY: No database modifications.
-- ============================================================

WITH

-- ============================================================
-- 1. Observation configuration
-- ============================================================

config AS (
    SELECT
        TIMESTAMPTZ '2026-01-01 00:00:00+00'
            AS observation_cutoff
),

-- ============================================================
-- 2. Prediction horizons
-- ============================================================

horizons AS (
    SELECT *
    FROM (
        VALUES
            ('M3', INTERVAL '3 months'),
            ('M6', INTERVAL '6 months')
    ) AS h(horizon, horizon_interval)
),

-- ============================================================
-- 3. First Paid timestamp per account
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
-- 4. Find accounts with a fully observable horizon
-- ============================================================

eligible_accounts AS (
    SELECT
        fp.account_id,
        fp.first_paid_at,

        h.horizon,

        fp.first_paid_at + h.horizon_interval
            AS horizon_at,

        DATE_TRUNC(
            'quarter',
            fp.first_paid_at AT TIME ZONE 'UTC'
        )::date AS first_paid_quarter

    FROM first_paid AS fp

    CROSS JOIN horizons AS h

    CROSS JOIN config AS c

    WHERE fp.first_paid_at + h.horizon_interval
          < c.observation_cutoff
),

-- ============================================================
-- 5. Reconstruct the subscription state at the horizon
-- ============================================================

state_flags AS (
    SELECT
        ea.*,

        -- Is the account in Standard or Premium?
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

        -- Is the account in Free?
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

        -- Was the account closed by the horizon?
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
-- 6. Define the target label
-- ============================================================

classified AS (
    SELECT
        account_id,
        first_paid_at,
        horizon,
        horizon_at,
        first_paid_quarter,

        CASE
            -- Conflicting states require investigation
            WHEN is_paid AND (is_free OR is_closed)
                THEN 'unknown'

            WHEN is_paid
                THEN 'paid'

            WHEN is_free OR is_closed
                THEN 'not_paid'

            ELSE 'unknown'
        END AS target_state

    FROM state_flags
),

-- ============================================================
-- 7. Population summary for each horizon
-- ============================================================

population_summary AS (
    SELECT
        'SUMMARY'::text AS result_section,

        horizon,

        NULL::date AS first_paid_quarter,

        (SELECT COUNT(*) FROM first_paid)
            AS ever_paid_accounts,

        COUNT(*) AS eligible_accounts,

        COUNT(*) FILTER (
            WHERE target_state = 'paid'
        ) AS paid_accounts,

        COUNT(*) FILTER (
            WHERE target_state = 'not_paid'
        ) AS not_paid_accounts,

        COUNT(*) FILTER (
            WHERE target_state = 'unknown'
        ) AS unknown_accounts,

        COUNT(*) - COUNT(DISTINCT account_id)
            AS duplicate_account_rows

    FROM classified

    GROUP BY horizon
),

-- ============================================================
-- 8. Population by First Paid quarter
-- ============================================================

quarterly_summary AS (
    SELECT
        'COHORT_QUARTER'::text AS result_section,

        horizon,

        first_paid_quarter,

        NULL::bigint AS ever_paid_accounts,

        COUNT(*) AS eligible_accounts,

        COUNT(*) FILTER (
            WHERE target_state = 'paid'
        ) AS paid_accounts,

        COUNT(*) FILTER (
            WHERE target_state = 'not_paid'
        ) AS not_paid_accounts,

        COUNT(*) FILTER (
            WHERE target_state = 'unknown'
        ) AS unknown_accounts,

        COUNT(*) - COUNT(DISTINCT account_id)
            AS duplicate_account_rows

    FROM classified

    GROUP BY
        horizon,
        first_paid_quarter
)

-- ============================================================
-- 9. Final consolidated report
-- ============================================================

SELECT *
FROM population_summary

UNION ALL

SELECT *
FROM quarterly_summary

ORDER BY
    horizon,
    result_section DESC,
    first_paid_quarter;