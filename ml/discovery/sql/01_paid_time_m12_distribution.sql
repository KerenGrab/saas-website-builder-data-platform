
-- ============================================================
-- SaaS Website Builder | ML Discovery
-- Target B: Paid Time Distribution - M12
--
-- Source database: saas_website_builder_9h
-- Observation cutoff: 2026-01-01 00:00:00 UTC
--
-- Purpose:
-- Calculate the time spent in Paid plans during the
-- first 12 calendar months after First Paid.
--
-- READ ONLY: No database modifications.
-- ============================================================

WITH config AS (
    SELECT
        TIMESTAMPTZ '2026-01-01 00:00:00+00'
            AS observation_cutoff
),

-- Step 1: Identify First Paid for every Ever Paid account
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

-- Step 2: Keep accounts with a complete M12 horizon
eligible_m12 AS (
    SELECT
        fp.account_id,
        fp.first_paid_at,

        (
            (fp.first_paid_at AT TIME ZONE 'UTC')
            + INTERVAL '12 months'
        ) AT TIME ZONE 'UTC' AS target_at

    FROM first_paid AS fp

    CROSS JOIN config AS c

    WHERE (
        (fp.first_paid_at AT TIME ZONE 'UTC')
        + INTERVAL '12 months'
    ) AT TIME ZONE 'UTC'
        < c.observation_cutoff
),

-- Step 3: Calculate Paid days for each account
paid_time AS (
    SELECT
        e.account_id,
        e.first_paid_at,
        e.target_at,

        EXTRACT(
            EPOCH FROM (e.target_at - e.first_paid_at)
        ) / 86400.0 AS horizon_days,

        COALESCE(
            SUM(
                EXTRACT(
                    EPOCH FROM (
                        LEAST(
                            COALESCE(p.valid_to, e.target_at),
                            e.target_at
                        )
                        -
                        GREATEST(
                            p.valid_from,
                            e.first_paid_at
                        )
                    )
                ) / 86400.0
            ),
            0
        ) AS paid_days_m12

    FROM eligible_m12 AS e

    LEFT JOIN public.subscription_plan_period AS p
        ON p.account_id = e.account_id

        AND p.plan_id IN (
            SELECT plan_id
            FROM public.plan_catalog
            WHERE LOWER(plan_name)
                IN ('standard', 'premium')
        )

        AND p.valid_from < e.target_at

        AND (
            p.valid_to > e.first_paid_at
            OR p.valid_to IS NULL
        )

    GROUP BY
        e.account_id,
        e.first_paid_at,
        e.target_at
)

-- Step 4: Summarize the M12 Paid Time distribution
SELECT
    COUNT(*) AS eligible_accounts,

    ROUND(
        AVG(paid_days_m12)::numeric, 2
    ) AS average_paid_days,

    ROUND(
        MIN(paid_days_m12)::numeric, 2
    ) AS minimum_paid_days,

    ROUND(
        MAX(paid_days_m12)::numeric, 2
    ) AS maximum_paid_days,

    COUNT(*) FILTER (
        WHERE paid_days_m12 = horizon_days
    ) AS fully_paid,

    COUNT(*) FILTER (
        WHERE paid_days_m12 / horizon_days >= 0.95
          AND paid_days_m12 / horizon_days < 1
    ) AS paid_95_to_100_pct,

    COUNT(*) FILTER (
        WHERE paid_days_m12 / horizon_days >= 0.80
          AND paid_days_m12 / horizon_days < 0.95
    ) AS paid_80_to_95_pct,

    COUNT(*) FILTER (
        WHERE paid_days_m12 / horizon_days >= 0.50
          AND paid_days_m12 / horizon_days < 0.80
    ) AS paid_50_to_80_pct,

    COUNT(*) FILTER (
        WHERE paid_days_m12 / horizon_days < 0.50
    ) AS paid_below_50_pct,

    ROUND(
        AVG(paid_days_m12) FILTER (
            WHERE paid_days_m12 < horizon_days
        )::numeric, 2
    ) AS average_partial_paid_days,

    COUNT(*) FILTER (
        WHERE paid_days_m12 < 0
           OR paid_days_m12 > horizon_days
    ) AS invalid_duration_accounts

FROM paid_time;