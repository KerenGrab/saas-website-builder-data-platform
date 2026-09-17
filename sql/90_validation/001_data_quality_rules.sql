-- Canonical data-quality violation queries.
-- Generated from pipeline/dq_rules.py.
-- Each query returns rows that violate the corresponding DQ rule.
-- Zero returned rows means the rule passes.

-- DQ-01 | Identity & Account
-- Role periods contained in and continuously cover Membership periods
WITH contained_roles AS (
                SELECT
                    mp.membership_period_id,
                    mp.membership_id,
                    mp.valid_from AS membership_from,
                    mp.valid_to AS membership_to,
                    rp.role_period_id,
                    rp.valid_from AS role_from,
                    rp.valid_to AS role_to
                FROM public.user_account_membership_period AS mp
                JOIN public.user_account_role_assignment_period AS rp
                  ON rp.membership_id = mp.membership_id
                 AND rp.valid_from >= mp.valid_from
                 AND (
                        mp.valid_to IS NULL
                        OR rp.valid_from < mp.valid_to
                     )
                 AND (
                        rp.valid_to IS NULL
                        OR mp.valid_to IS NULL
                        OR rp.valid_to <= mp.valid_to
                     )
            ),
            ordered_roles AS (
                SELECT
                    cr.*,
                    LAG(cr.role_to) OVER (
                        PARTITION BY cr.membership_period_id
                        ORDER BY cr.role_from, cr.role_period_id
                    ) AS previous_role_to,
                    ROW_NUMBER() OVER (
                        PARTITION BY cr.membership_period_id
                        ORDER BY cr.role_from, cr.role_period_id
                    ) AS rn_first,
                    ROW_NUMBER() OVER (
                        PARTITION BY cr.membership_period_id
                        ORDER BY cr.role_from DESC, cr.role_period_id DESC
                    ) AS rn_last
                FROM contained_roles AS cr
            )

            SELECT
                'role_period_outside_membership' AS violation_type,
                rp.role_period_id::text AS entity_id
            FROM public.user_account_role_assignment_period AS rp
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.user_account_membership_period AS mp
                WHERE mp.membership_id = rp.membership_id
                  AND rp.valid_from >= mp.valid_from
                  AND (
                        mp.valid_to IS NULL
                        OR rp.valid_from < mp.valid_to
                      )
                  AND (
                        rp.valid_to IS NULL
                        OR mp.valid_to IS NULL
                        OR rp.valid_to <= mp.valid_to
                      )
            )

            UNION ALL

            SELECT
                'membership_role_start_gap',
                mp.membership_period_id::text
            FROM public.user_account_membership_period AS mp
            WHERE NOT EXISTS (
                SELECT 1
                FROM contained_roles AS cr
                WHERE cr.membership_period_id = mp.membership_period_id
                  AND cr.role_from = mp.valid_from
            )

            UNION ALL

            SELECT
                'membership_role_internal_gap',
                role_period_id::text
            FROM ordered_roles
            WHERE rn_first > 1
              AND previous_role_to IS DISTINCT FROM role_from

            UNION ALL

            SELECT
                'membership_role_end_gap',
                mp.membership_period_id::text
            FROM public.user_account_membership_period AS mp
            WHERE NOT EXISTS (
                SELECT 1
                FROM ordered_roles AS r
                WHERE r.membership_period_id = mp.membership_period_id
                  AND r.rn_last = 1
                  AND r.role_to IS NOT DISTINCT FROM mp.valid_to
            );

-- DQ-02 | Identity & Account
-- Every active Account is continuously covered by at least one active Owner
WITH active_account_periods AS (
                SELECT
                    alp.account_lifecycle_period_id,
                    alp.account_id,
                    alp.valid_from,
                    alp.valid_to
                FROM public.account_lifecycle_period AS alp
                WHERE alp.lifecycle_state = 'active'
            ),
            boundary_points AS (
                SELECT
                    aap.account_lifecycle_period_id,
                    aap.account_id,
                    aap.valid_from AS boundary_time
                FROM active_account_periods AS aap

                UNION

                SELECT
                    aap.account_lifecycle_period_id,
                    aap.account_id,
                    mp.valid_from
                FROM active_account_periods AS aap
                JOIN public.user_account_membership AS m
                  ON m.account_id = aap.account_id
                JOIN public.user_account_membership_period AS mp
                  ON mp.membership_id = m.membership_id
                WHERE mp.valid_from >= aap.valid_from
                  AND (
                        aap.valid_to IS NULL
                        OR mp.valid_from < aap.valid_to
                      )

                UNION

                SELECT
                    aap.account_lifecycle_period_id,
                    aap.account_id,
                    mp.valid_to
                FROM active_account_periods AS aap
                JOIN public.user_account_membership AS m
                  ON m.account_id = aap.account_id
                JOIN public.user_account_membership_period AS mp
                  ON mp.membership_id = m.membership_id
                WHERE mp.valid_to IS NOT NULL
                  AND mp.valid_to >= aap.valid_from
                  AND (
                        aap.valid_to IS NULL
                        OR mp.valid_to < aap.valid_to
                      )

                UNION

                SELECT
                    aap.account_lifecycle_period_id,
                    aap.account_id,
                    rp.valid_from
                FROM active_account_periods AS aap
                JOIN public.user_account_membership AS m
                  ON m.account_id = aap.account_id
                JOIN public.user_account_role_assignment_period AS rp
                  ON rp.membership_id = m.membership_id
                WHERE rp.valid_from >= aap.valid_from
                  AND (
                        aap.valid_to IS NULL
                        OR rp.valid_from < aap.valid_to
                      )

                UNION

                SELECT
                    aap.account_lifecycle_period_id,
                    aap.account_id,
                    rp.valid_to
                FROM active_account_periods AS aap
                JOIN public.user_account_membership AS m
                  ON m.account_id = aap.account_id
                JOIN public.user_account_role_assignment_period AS rp
                  ON rp.membership_id = m.membership_id
                WHERE rp.valid_to IS NOT NULL
                  AND rp.valid_to >= aap.valid_from
                  AND (
                        aap.valid_to IS NULL
                        OR rp.valid_to < aap.valid_to
                      )
            )
            SELECT
                bp.account_id,
                bp.boundary_time
            FROM boundary_points AS bp
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.user_account_membership AS m
                JOIN public.user_account_membership_period AS mp
                  ON mp.membership_id = m.membership_id
                 AND bp.boundary_time >= mp.valid_from
                 AND (
                        mp.valid_to IS NULL
                        OR bp.boundary_time < mp.valid_to
                     )
                JOIN public.user_account_role_assignment_period AS rp
                  ON rp.membership_id = m.membership_id
                 AND LOWER(rp.role) = 'owner'
                 AND bp.boundary_time >= rp.valid_from
                 AND (
                        rp.valid_to IS NULL
                        OR bp.boundary_time < rp.valid_to
                     )
                WHERE m.account_id = bp.account_id
            );

-- DQ-03 | Identity & Account
-- Account and Membership lifecycle events agree with period histories
WITH account_event_stats AS (
                SELECT
                    a.account_id,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'account_created'
                    ) AS created_count,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'account_closure'
                    ) AS closure_count,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'account_created'
                    ) AS created_time,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'account_closure'
                    ) AS closure_time
                FROM public.account AS a
                LEFT JOIN public.account_lifecycle_event AS e
                  ON e.account_id = a.account_id
                GROUP BY a.account_id
            ),
            account_period_stats AS (
                SELECT
                    a.account_id,
                    COUNT(p.account_lifecycle_period_id) FILTER (
                        WHERE p.lifecycle_state = 'active'
                    ) AS active_count,
                    COUNT(p.account_lifecycle_period_id) FILTER (
                        WHERE p.lifecycle_state = 'closed'
                    ) AS closed_count,
                    MIN(p.valid_from) FILTER (
                        WHERE p.lifecycle_state = 'active'
                    ) AS active_from,
                    MAX(p.valid_to) FILTER (
                        WHERE p.lifecycle_state = 'active'
                    ) AS active_to,
                    MIN(p.valid_from) FILTER (
                        WHERE p.lifecycle_state = 'closed'
                    ) AS closed_from,
                    MAX(p.valid_to) FILTER (
                        WHERE p.lifecycle_state = 'closed'
                    ) AS closed_to
                FROM public.account AS a
                LEFT JOIN public.account_lifecycle_period AS p
                  ON p.account_id = a.account_id
                GROUP BY a.account_id
            ),
            membership_stats AS (
                SELECT
                    m.membership_id,
                    MIN(mp.valid_from) AS first_membership_start,
                    COUNT(DISTINCT me.event_id) FILTER (
                        WHERE me.event_type = 'user_joined_account'
                    ) AS joined_count,
                    MIN(me.event_time) FILTER (
                        WHERE me.event_type = 'user_joined_account'
                    ) AS joined_time
                FROM public.user_account_membership AS m
                LEFT JOIN public.user_account_membership_period AS mp
                  ON mp.membership_id = m.membership_id
                LEFT JOIN public.user_account_membership_event AS me
                  ON me.membership_id = m.membership_id
                GROUP BY m.membership_id
            )
            SELECT
                'account_event_period_mismatch' AS violation_type,
                aes.account_id::text AS entity_id
            FROM account_event_stats AS aes
            JOIN account_period_stats AS aps
              ON aps.account_id = aes.account_id
            WHERE aes.created_count <> 1
               OR aes.closure_count > 1
               OR aps.active_count <> 1
               OR aps.active_from IS DISTINCT FROM aes.created_time
               OR (
                    aes.closure_count = 0
                    AND (
                        aps.active_to IS NOT NULL
                        OR aps.closed_count <> 0
                    )
                  )
               OR (
                    aes.closure_count = 1
                    AND (
                        aps.active_to IS DISTINCT FROM aes.closure_time
                        OR aps.closed_count <> 1
                        OR aps.closed_from IS DISTINCT FROM aes.closure_time
                        OR aps.closed_to IS NOT NULL
                    )
                  )

            UNION ALL

            SELECT
                'membership_joined_event_mismatch',
                ms.membership_id::text
            FROM membership_stats AS ms
            WHERE ms.first_membership_start IS NULL
               OR ms.joined_count <> 1
               OR ms.joined_time IS DISTINCT FROM ms.first_membership_start;

-- DQ-04 | Website & Structure
-- Website publication, Live periods, and Address coverage are coherent
WITH website_created_stats AS (
                SELECT
                    w.website_id,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'website_created'
                    ) AS created_count,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'website_created'
                    ) AS created_time
                FROM public.website AS w
                LEFT JOIN public.website_lifecycle_event AS e
                  ON e.website_id = w.website_id
                GROUP BY w.website_id
            ),
            live_boundaries AS (
                SELECT
                    lp.live_period_id,
                    lp.website_id,
                    lp.valid_from,
                    lp.valid_to,
                    lp.valid_from AS boundary_time
                FROM public.website_live_period AS lp

                UNION

                SELECT
                    lp.live_period_id,
                    lp.website_id,
                    lp.valid_from,
                    lp.valid_to,
                    ap.valid_from
                FROM public.website_live_period AS lp
                JOIN public.website_address_period AS ap
                  ON ap.website_id = lp.website_id
                WHERE ap.valid_from >= lp.valid_from
                  AND (
                        lp.valid_to IS NULL
                        OR ap.valid_from < lp.valid_to
                      )

                UNION

                SELECT
                    lp.live_period_id,
                    lp.website_id,
                    lp.valid_from,
                    lp.valid_to,
                    ap.valid_to
                FROM public.website_live_period AS lp
                JOIN public.website_address_period AS ap
                  ON ap.website_id = lp.website_id
                WHERE ap.valid_to IS NOT NULL
                  AND ap.valid_to >= lp.valid_from
                  AND (
                        lp.valid_to IS NULL
                        OR ap.valid_to < lp.valid_to
                      )
            )
            SELECT
                'website_created_cardinality_or_time' AS violation_type,
                wcs.website_id::text AS entity_id
            FROM website_created_stats AS wcs
            WHERE wcs.created_count <> 1

            UNION ALL

            SELECT
                'website_event_before_created',
                e.event_id::text
            FROM public.website_lifecycle_event AS e
            JOIN website_created_stats AS wcs
              ON wcs.website_id = e.website_id
            WHERE wcs.created_count = 1
              AND e.event_time < wcs.created_time

            UNION ALL

            SELECT
                'live_period_without_published_start',
                lp.live_period_id::text
            FROM public.website_live_period AS lp
            WHERE (
                SELECT COUNT(*)
                FROM public.website_lifecycle_event AS e
                WHERE e.website_id = lp.website_id
                  AND e.event_type = 'published'
                  AND e.event_time = lp.valid_from
            ) <> 1

            UNION ALL

            SELECT
                'published_without_live_period',
                e.event_id::text
            FROM public.website_lifecycle_event AS e
            WHERE e.event_type = 'published'
              AND NOT EXISTS (
                    SELECT 1
                    FROM public.website_live_period AS lp
                    WHERE lp.website_id = e.website_id
                      AND lp.valid_from = e.event_time
              )

            UNION ALL

            SELECT
                'live_period_address_coverage_gap',
                lb.live_period_id::text
            FROM live_boundaries AS lb
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.website_address_period AS ap
                WHERE ap.website_id = lb.website_id
                  AND lb.boundary_time >= ap.valid_from
                  AND (
                        ap.valid_to IS NULL
                        OR lb.boundary_time < ap.valid_to
                      )
            );

-- DQ-05 | Website & Structure
-- Page Access history is contiguous with no gaps
WITH ordered_access AS (
                SELECT
                    p.page_access_period_id,
                    p.page_id,
                    p.valid_from,
                    p.valid_to,
                    LAG(p.valid_to) OVER (
                        PARTITION BY p.page_id
                        ORDER BY p.valid_from, p.page_access_period_id
                    ) AS previous_valid_to,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.page_id
                        ORDER BY p.valid_from, p.page_access_period_id
                    ) AS rn_first,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.page_id
                        ORDER BY p.valid_from DESC, p.page_access_period_id DESC
                    ) AS rn_last
                FROM public.page_access_period AS p
            )
            SELECT
                'page_missing_access_history' AS violation_type,
                p.page_id::text AS entity_id
            FROM public.page AS p
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.page_access_period AS ap
                WHERE ap.page_id = p.page_id
            )

            UNION ALL

            SELECT
                'page_access_internal_gap',
                oa.page_access_period_id::text
            FROM ordered_access AS oa
            WHERE oa.rn_first > 1
              AND oa.previous_valid_to IS DISTINCT FROM oa.valid_from

            UNION ALL

            SELECT
                'page_access_final_period_not_open',
                oa.page_access_period_id::text
            FROM ordered_access AS oa
            WHERE oa.rn_last = 1
              AND oa.valid_to IS NOT NULL;

-- DQ-06 | Website & Structure
-- Content Item Access history is contiguous with no gaps
WITH ordered_access AS (
                SELECT
                    p.content_item_access_period_id,
                    p.content_item_id,
                    p.valid_from,
                    p.valid_to,
                    LAG(p.valid_to) OVER (
                        PARTITION BY p.content_item_id
                        ORDER BY p.valid_from, p.content_item_access_period_id
                    ) AS previous_valid_to,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.content_item_id
                        ORDER BY p.valid_from, p.content_item_access_period_id
                    ) AS rn_first,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.content_item_id
                        ORDER BY p.valid_from DESC, p.content_item_access_period_id DESC
                    ) AS rn_last
                FROM public.content_item_access_period AS p
            )
            SELECT
                'content_missing_access_history' AS violation_type,
                ci.content_item_id::text AS entity_id
            FROM public.content_item AS ci
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.content_item_access_period AS ap
                WHERE ap.content_item_id = ci.content_item_id
            )

            UNION ALL

            SELECT
                'content_access_internal_gap',
                oa.content_item_access_period_id::text
            FROM ordered_access AS oa
            WHERE oa.rn_first > 1
              AND oa.previous_valid_to IS DISTINCT FROM oa.valid_from

            UNION ALL

            SELECT
                'content_access_final_period_not_open',
                oa.content_item_access_period_id::text
            FROM ordered_access AS oa
            WHERE oa.rn_last = 1
              AND oa.valid_to IS NOT NULL;

-- DQ-07 | Feature / Entitlement
-- Feature Enablement is continuously supported by Plan Entitlement
WITH enablement_context AS (
                SELECT
                    ep.enablement_period_id,
                    ep.website_id,
                    ep.feature_id,
                    ep.valid_from,
                    ep.valid_to,
                    w.account_id
                FROM public.website_feature_enablement_period AS ep
                JOIN public.website AS w
                  ON w.website_id = ep.website_id
            ),
            boundary_points AS (
                SELECT
                    ec.enablement_period_id,
                    ec.account_id,
                    ec.feature_id,
                    ec.valid_from,
                    ec.valid_to,
                    ec.valid_from AS boundary_time
                FROM enablement_context AS ec

                UNION

                SELECT
                    ec.enablement_period_id,
                    ec.account_id,
                    ec.feature_id,
                    ec.valid_from,
                    ec.valid_to,
                    sp.valid_from
                FROM enablement_context AS ec
                JOIN public.subscription_plan_period AS sp
                  ON sp.account_id = ec.account_id
                WHERE sp.valid_from >= ec.valid_from
                  AND (
                        ec.valid_to IS NULL
                        OR sp.valid_from < ec.valid_to
                      )

                UNION

                SELECT
                    ec.enablement_period_id,
                    ec.account_id,
                    ec.feature_id,
                    ec.valid_from,
                    ec.valid_to,
                    sp.valid_to
                FROM enablement_context AS ec
                JOIN public.subscription_plan_period AS sp
                  ON sp.account_id = ec.account_id
                WHERE sp.valid_to IS NOT NULL
                  AND sp.valid_to >= ec.valid_from
                  AND (
                        ec.valid_to IS NULL
                        OR sp.valid_to < ec.valid_to
                      )

                UNION

                SELECT
                    ec.enablement_period_id,
                    ec.account_id,
                    ec.feature_id,
                    ec.valid_from,
                    ec.valid_to,
                    ent.valid_from
                FROM enablement_context AS ec
                JOIN public.plan_feature_entitlement_period AS ent
                  ON ent.feature_id = ec.feature_id
                WHERE ent.valid_from >= ec.valid_from
                  AND (
                        ec.valid_to IS NULL
                        OR ent.valid_from < ec.valid_to
                      )

                UNION

                SELECT
                    ec.enablement_period_id,
                    ec.account_id,
                    ec.feature_id,
                    ec.valid_from,
                    ec.valid_to,
                    ent.valid_to
                FROM enablement_context AS ec
                JOIN public.plan_feature_entitlement_period AS ent
                  ON ent.feature_id = ec.feature_id
                WHERE ent.valid_to IS NOT NULL
                  AND ent.valid_to >= ec.valid_from
                  AND (
                        ec.valid_to IS NULL
                        OR ent.valid_to < ec.valid_to
                      )
            )
            SELECT
                bp.enablement_period_id,
                bp.boundary_time
            FROM boundary_points AS bp
            WHERE (
                SELECT COUNT(*)
                FROM public.subscription_plan_period AS sp
                JOIN public.plan_feature_entitlement_period AS ent
                  ON ent.plan_id = sp.plan_id
                 AND ent.feature_id = bp.feature_id
                 AND bp.boundary_time >= ent.valid_from
                 AND (
                        ent.valid_to IS NULL
                        OR bp.boundary_time < ent.valid_to
                     )
                WHERE sp.account_id = bp.account_id
                  AND bp.boundary_time >= sp.valid_from
                  AND (
                        sp.valid_to IS NULL
                        OR bp.boundary_time < sp.valid_to
                      )
            ) <> 1;

-- DQ-08 | Feature / Entitlement
-- Feature Enabled and Disabled events explain Enablement boundaries
SELECT
                'enablement_start_event_mismatch' AS violation_type,
                ep.enablement_period_id::text AS entity_id
            FROM public.website_feature_enablement_period AS ep
            WHERE (
                SELECT COUNT(*)
                FROM public.feature_enablement_lifecycle_event AS e
                WHERE e.website_id = ep.website_id
                  AND e.feature_id = ep.feature_id
                  AND e.event_type = 'feature_enabled'
                  AND e.event_time = ep.valid_from
            ) <> 1

            UNION ALL

            SELECT
                'enabled_event_without_period_start',
                e.event_id::text
            FROM public.feature_enablement_lifecycle_event AS e
            WHERE e.event_type = 'feature_enabled'
              AND NOT EXISTS (
                    SELECT 1
                    FROM public.website_feature_enablement_period AS ep
                    WHERE ep.website_id = e.website_id
                      AND ep.feature_id = e.feature_id
                      AND ep.valid_from = e.event_time
              )

            UNION ALL

            SELECT
                'enablement_end_event_mismatch',
                ep.enablement_period_id::text
            FROM public.website_feature_enablement_period AS ep
            WHERE ep.valid_to IS NOT NULL
              AND (
                    SELECT COUNT(*)
                    FROM public.feature_enablement_lifecycle_event AS e
                    WHERE e.website_id = ep.website_id
                      AND e.feature_id = ep.feature_id
                      AND e.event_type = 'feature_disabled'
                      AND e.event_time = ep.valid_to
              ) <> 1

            UNION ALL

            SELECT
                'disabled_event_without_period_end',
                e.event_id::text
            FROM public.feature_enablement_lifecycle_event AS e
            WHERE e.event_type = 'feature_disabled'
              AND NOT EXISTS (
                    SELECT 1
                    FROM public.website_feature_enablement_period AS ep
                    WHERE ep.website_id = e.website_id
                      AND ep.feature_id = e.feature_id
                      AND ep.valid_to = e.event_time
              );

-- DQ-09 | Product Behaviour
-- Product Behaviour actor, Account, and optional Website context are valid
SELECT
                e.event_id,
                e.event_type
            FROM public.product_behaviour_event AS e
            WHERE e.user_id IS NULL
               OR e.account_id IS NULL
               OR (
                    SELECT COUNT(DISTINCT mp.membership_period_id)
                    FROM public.user_account_membership AS m
                    JOIN public.user_account_membership_period AS mp
                      ON mp.membership_id = m.membership_id
                    WHERE m.user_id = e.user_id
                      AND m.account_id = e.account_id
                      AND e.event_time >= mp.valid_from
                      AND (
                            mp.valid_to IS NULL
                            OR e.event_time < mp.valid_to
                          )
                  ) <> 1
               OR (
                    e.website_id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM public.website AS w
                        WHERE w.website_id = e.website_id
                          AND w.account_id = e.account_id
                    )
                  );

-- DQ-10 | Product Behaviour
-- Feature Used has Membership, Plan, Entitlement, and active Enablement
SELECT
                e.event_id,
                e.event_time
            FROM public.product_behaviour_event AS e
            WHERE e.event_type = 'feature_used'
              AND (
                    e.user_id IS NULL
                    OR e.account_id IS NULL
                    OR e.website_id IS NULL
                    OR e.feature_id IS NULL
                    OR NOT EXISTS (
                        SELECT 1
                        FROM public.website AS w
                        WHERE w.website_id = e.website_id
                          AND w.account_id = e.account_id
                    )
                    OR (
                        SELECT COUNT(DISTINCT mp.membership_period_id)
                        FROM public.user_account_membership AS m
                        JOIN public.user_account_membership_period AS mp
                          ON mp.membership_id = m.membership_id
                        WHERE m.user_id = e.user_id
                          AND m.account_id = e.account_id
                          AND e.event_time >= mp.valid_from
                          AND (
                                mp.valid_to IS NULL
                                OR e.event_time < mp.valid_to
                              )
                    ) <> 1
                    OR (
                        SELECT COUNT(DISTINCT sp.subscription_plan_period_id)
                        FROM public.subscription_plan_period AS sp
                        JOIN public.plan_feature_entitlement_period AS ent
                          ON ent.plan_id = sp.plan_id
                         AND ent.feature_id = e.feature_id
                         AND e.event_time >= ent.valid_from
                         AND (
                                ent.valid_to IS NULL
                                OR e.event_time < ent.valid_to
                             )
                        WHERE sp.account_id = e.account_id
                          AND e.event_time >= sp.valid_from
                          AND (
                                sp.valid_to IS NULL
                                OR e.event_time < sp.valid_to
                              )
                    ) <> 1
                    OR (
                        SELECT COUNT(DISTINCT ep.enablement_period_id)
                        FROM public.website_feature_enablement_period AS ep
                        WHERE ep.website_id = e.website_id
                          AND ep.feature_id = e.feature_id
                          AND e.event_time >= ep.valid_from
                          AND (
                                ep.valid_to IS NULL
                                OR e.event_time < ep.valid_to
                              )
                    ) <> 1
                  );

-- DQ-11 | Product Behaviour
-- Locked Feature Attempt occurs in one Plan context with no Entitlement
SELECT
                e.event_id,
                e.event_time
            FROM public.product_behaviour_event AS e
            WHERE e.event_type = 'locked_feature_attempted'
              AND (
                    e.user_id IS NULL
                    OR e.account_id IS NULL
                    OR e.feature_id IS NULL
                    OR (
                        SELECT COUNT(DISTINCT sp.subscription_plan_period_id)
                        FROM public.subscription_plan_period AS sp
                        WHERE sp.account_id = e.account_id
                          AND e.event_time >= sp.valid_from
                          AND (
                                sp.valid_to IS NULL
                                OR e.event_time < sp.valid_to
                              )
                    ) <> 1
                    OR EXISTS (
                        SELECT 1
                        FROM public.subscription_plan_period AS sp
                        JOIN public.plan_feature_entitlement_period AS ent
                          ON ent.plan_id = sp.plan_id
                         AND ent.feature_id = e.feature_id
                         AND e.event_time >= ent.valid_from
                         AND (
                                ent.valid_to IS NULL
                                OR e.event_time < ent.valid_to
                             )
                        WHERE sp.account_id = e.account_id
                          AND e.event_time >= sp.valid_from
                          AND (
                                sp.valid_to IS NULL
                                OR e.event_time < sp.valid_to
                              )
                    )
                  );

-- DQ-12 | Product Behaviour
-- Restricted Product Action Attempt is performed in active Viewer context
SELECT
                e.event_id,
                e.event_time
            FROM public.product_behaviour_event AS e
            WHERE e.event_type = 'restricted_product_action_attempted'
              AND (
                    e.user_id IS NULL
                    OR e.account_id IS NULL
                    OR (
                        SELECT COUNT(DISTINCT rp.role_period_id)
                        FROM public.user_account_membership AS m
                        JOIN public.user_account_membership_period AS mp
                          ON mp.membership_id = m.membership_id
                         AND e.event_time >= mp.valid_from
                         AND (
                                mp.valid_to IS NULL
                                OR e.event_time < mp.valid_to
                             )
                        JOIN public.user_account_role_assignment_period AS rp
                          ON rp.membership_id = m.membership_id
                         AND e.event_time >= rp.valid_from
                         AND (
                                rp.valid_to IS NULL
                                OR e.event_time < rp.valid_to
                             )
                        WHERE m.user_id = e.user_id
                          AND m.account_id = e.account_id
                          AND LOWER(rp.role) = 'viewer'
                    ) <> 1
                  );

-- DQ-13 | Product Behaviour
-- Website Analytics Viewed is limited to active Owner or Editor context
SELECT
                e.event_id,
                e.event_time
            FROM public.product_behaviour_event AS e
            WHERE e.event_type = 'website_analytics_viewed'
              AND (
                    e.user_id IS NULL
                    OR e.account_id IS NULL
                    OR e.website_id IS NULL
                    OR NOT EXISTS (
                        SELECT 1
                        FROM public.website AS w
                        WHERE w.website_id = e.website_id
                          AND w.account_id = e.account_id
                    )
                    OR (
                        SELECT COUNT(DISTINCT rp.role_period_id)
                        FROM public.user_account_membership AS m
                        JOIN public.user_account_membership_period AS mp
                          ON mp.membership_id = m.membership_id
                         AND e.event_time >= mp.valid_from
                         AND (
                                mp.valid_to IS NULL
                                OR e.event_time < mp.valid_to
                             )
                        JOIN public.user_account_role_assignment_period AS rp
                          ON rp.membership_id = m.membership_id
                         AND e.event_time >= rp.valid_from
                         AND (
                                rp.valid_to IS NULL
                                OR e.event_time < rp.valid_to
                             )
                        WHERE m.user_id = e.user_id
                          AND m.account_id = e.account_id
                          AND LOWER(rp.role) IN ('owner', 'editor')
                    ) <> 1
                  );

-- DQ-14 | Membership & Contributions
-- Invitation resolution and invitation-based registration are coherent
WITH invitation_outcome_stats AS (
                SELECT
                    i.invitation_id,
                    COUNT(o.event_id) AS outcome_count
                FROM public.membership_invitation AS i
                LEFT JOIN public.invitation_outcome_event AS o
                  ON o.invitation_id = i.invitation_id
                GROUP BY i.invitation_id
            ),
            invitation_success_stats AS (
                SELECT
                    i.invitation_id,
                    COUNT(r.event_id) AS success_count
                FROM public.membership_invitation AS i
                LEFT JOIN public.member_registration_success_event AS r
                  ON r.invitation_id = i.invitation_id
                 AND r.registration_method = 'invitation'
                GROUP BY i.invitation_id
            )
            SELECT
                'invitation_resolution_cardinality' AS violation_type,
                i.invitation_id::text AS entity_id
            FROM public.membership_invitation AS i
            JOIN invitation_outcome_stats AS os
              ON os.invitation_id = i.invitation_id
            JOIN invitation_success_stats AS ss
              ON ss.invitation_id = i.invitation_id
            WHERE os.outcome_count + ss.success_count <> 1

            UNION ALL

            SELECT
                'invitation_outcome_before_invitation',
                o.event_id::text
            FROM public.invitation_outcome_event AS o
            JOIN public.membership_invitation AS i
              ON i.invitation_id = o.invitation_id
            WHERE o.event_time < i.invitation_time

            UNION ALL

            SELECT
                'invitation_registration_mismatch',
                r.event_id::text
            FROM public.member_registration_success_event AS r
            JOIN public.membership_invitation AS i
              ON i.invitation_id = r.invitation_id
            WHERE r.registration_method = 'invitation'
              AND (
                    r.website_id IS DISTINCT FROM i.website_id
                    OR r.event_time < i.invitation_time
                  )

            UNION ALL

            SELECT
                'registration_member_website_mismatch',
                r.event_id::text
            FROM public.member_registration_success_event AS r
            JOIN public.website_member AS m
              ON m.member_id = r.member_id
            WHERE r.website_id IS DISTINCT FROM m.website_id;

-- DQ-15 | Membership & Contributions
-- Member State history starts at registration and remains contiguous
WITH registration_stats AS (
                SELECT
                    m.member_id,
                    COUNT(r.event_id) AS registration_count,
                    MIN(r.event_time) AS registration_time
                FROM public.website_member AS m
                LEFT JOIN public.member_registration_success_event AS r
                  ON r.member_id = m.member_id
                GROUP BY m.member_id
            ),
            ordered_states AS (
                SELECT
                    p.member_state_period_id,
                    p.member_id,
                    p.member_state,
                    p.valid_from,
                    p.valid_to,
                    LAG(p.valid_to) OVER (
                        PARTITION BY p.member_id
                        ORDER BY p.valid_from, p.member_state_period_id
                    ) AS previous_valid_to,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.member_id
                        ORDER BY p.valid_from, p.member_state_period_id
                    ) AS rn_first
                FROM public.member_state_period AS p
            )

            SELECT
                'member_registration_cardinality' AS violation_type,
                rs.member_id::text AS entity_id
            FROM registration_stats AS rs
            WHERE rs.registration_count <> 1

            UNION ALL

            SELECT
                'member_state_initial_mismatch',
                os.member_id::text
            FROM ordered_states AS os
            JOIN registration_stats AS rs
              ON rs.member_id = os.member_id
            WHERE os.rn_first = 1
              AND (
                    rs.registration_count <> 1
                    OR os.member_state <> 'active'
                    OR os.valid_from IS DISTINCT FROM rs.registration_time
                  )

            UNION ALL

            SELECT
                'member_state_internal_gap',
                os.member_state_period_id::text
            FROM ordered_states AS os
            WHERE os.rn_first > 1
              AND os.previous_valid_to IS DISTINCT FROM os.valid_from

            UNION ALL

            SELECT
                'member_missing_state_history',
                m.member_id::text
            FROM public.website_member AS m
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.member_state_period AS p
                WHERE p.member_id = m.member_id
            );

-- DQ-16 | Membership & Contributions
-- Registration failures have a preceding start and Member logins have valid registration context
WITH registration_attempt_stats AS (
                SELECT
                    registration_attempt_id,
                    COUNT(*) FILTER (
                        WHERE event_type = 'member_registration_started'
                    ) AS started_count,
                    COUNT(*) FILTER (
                        WHERE event_type = 'member_registration_failed'
                    ) AS failed_count,
                    MIN(event_time) FILTER (
                        WHERE event_type = 'member_registration_started'
                    ) AS started_time,
                    MAX(event_time) FILTER (
                        WHERE event_type = 'member_registration_failed'
                    ) AS failed_time,
                    COUNT(DISTINCT website_id) AS website_count
                FROM public.membership_behaviour_event
                WHERE event_type IN (
                    'member_registration_started',
                    'member_registration_failed'
                )
                  AND registration_attempt_id IS NOT NULL
                GROUP BY registration_attempt_id
            )
            SELECT
                'registration_attempt_mismatch' AS violation_type,
                ras.registration_attempt_id::text AS entity_id
            FROM registration_attempt_stats AS ras
            WHERE ras.started_count <> 1
               OR ras.failed_count > 1
               OR ras.website_count <> 1
               OR (
                    ras.failed_count = 1
                    AND (
                        ras.started_time IS NULL
                        OR ras.failed_time <= ras.started_time
                    )
                  )

            UNION ALL

            SELECT
                'member_login_context_mismatch',
                e.event_id::text
            FROM public.membership_behaviour_event AS e
            LEFT JOIN public.website_member AS m
              ON m.member_id = e.member_id
            WHERE e.event_type = 'member_logged_in'
              AND (
                    e.member_id IS NULL
                    OR m.member_id IS NULL
                    OR m.website_id IS DISTINCT FROM e.website_id
                    OR NOT EXISTS (
                        SELECT 1
                        FROM public.member_registration_success_event AS r
                        WHERE r.member_id = e.member_id
                          AND r.website_id = e.website_id
                          AND r.event_time <= e.event_time
                    )
                  );

-- DQ-17 | Membership & Contributions
-- Every Comment has one posted event and every Rating has one given event
SELECT
                'comment_posted_cardinality' AS violation_type,
                c.comment_id::text AS entity_id
            FROM public.comment AS c
            LEFT JOIN public.comment_lifecycle_event AS e
              ON e.comment_id = c.comment_id
             AND e.event_type = 'comment_posted'
            GROUP BY c.comment_id
            HAVING COUNT(e.event_id) <> 1

            UNION ALL

            SELECT
                'rating_given_cardinality',
                r.rating_id::text
            FROM public.rating AS r
            LEFT JOIN public.rating_lifecycle_event AS e
              ON e.rating_id = r.rating_id
             AND e.event_type = 'rating_given'
            GROUP BY r.rating_id
            HAVING COUNT(e.event_id) <> 1;

-- DQ-18 | Audience
-- Session / Visitor Website consistency
SELECT
                s.session_id,
                s.visitor_id,
                s.website_id AS session_website_id,
                v.website_id AS visitor_website_id
            FROM public.audience_session AS s
            JOIN public.visitor AS v
              ON v.visitor_id = s.visitor_id
            WHERE s.website_id IS DISTINCT FROM v.website_id;

-- DQ-19 | Audience
-- Every Session has exactly one Start and End in valid temporal order
WITH session_stats AS (
                SELECT
                    s.session_id,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'session_started'
                    ) AS started_count,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'session_ended'
                    ) AS ended_count,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'session_started'
                    ) AS started_time,
                    MAX(e.event_time) FILTER (
                        WHERE e.event_type = 'session_ended'
                    ) AS ended_time
                FROM public.audience_session AS s
                LEFT JOIN public.session_lifecycle_event AS e
                  ON e.session_id = s.session_id
                GROUP BY s.session_id
            )
            SELECT
                session_id,
                started_count,
                ended_count,
                started_time,
                ended_time
            FROM session_stats
            WHERE started_count <> 1
               OR ended_count <> 1
               OR ended_time < started_time;

-- DQ-20 | Audience
-- Every Session has exactly one Traffic Attribution
SELECT
                s.session_id,
                COUNT(a.session_id) AS attribution_count
            FROM public.audience_session AS s
            LEFT JOIN public.session_traffic_attribution AS a
              ON a.session_id = s.session_id
            GROUP BY s.session_id
            HAVING COUNT(a.session_id) <> 1;

-- DQ-21 | Audience
-- Audience interactions stay inside Session time and Website context
WITH session_stats AS (
                SELECT
                    s.session_id,
                    s.website_id,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'session_started'
                    ) AS started_count,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'session_ended'
                    ) AS ended_count,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'session_started'
                    ) AS started_time,
                    MAX(e.event_time) FILTER (
                        WHERE e.event_type = 'session_ended'
                    ) AS ended_time
                FROM public.audience_session AS s
                LEFT JOIN public.session_lifecycle_event AS e
                  ON e.session_id = s.session_id
                GROUP BY s.session_id, s.website_id
            )
            SELECT
                i.event_id,
                i.event_type,
                i.event_time
            FROM public.audience_interaction_event AS i
            JOIN session_stats AS ss
              ON ss.session_id = i.session_id
            LEFT JOIN public.page AS p
              ON p.page_id = i.page_id
            LEFT JOIN public.content_item AS ci
              ON ci.content_item_id = i.content_item_id
            LEFT JOIN public.page AS cp
              ON cp.page_id = ci.page_id
            WHERE ss.started_count <> 1
               OR ss.ended_count <> 1
               OR i.event_time < ss.started_time
               OR i.event_time > ss.ended_time
               OR (
                    i.page_id IS NOT NULL
                    AND p.website_id IS DISTINCT FROM ss.website_id
                  )
               OR (
                    i.content_item_id IS NOT NULL
                    AND cp.website_id IS DISTINCT FROM ss.website_id
                  );

-- DQ-22 | Audience
-- Visitor Member linkage and Session Member attribution are identity-consistent
SELECT
                'visitor_member_website_mismatch' AS violation_type,
                vml.visitor_member_link_id::text AS entity_id
            FROM public.visitor_member_linkage AS vml
            JOIN public.visitor AS v
              ON v.visitor_id = vml.visitor_id
            JOIN public.website_member AS m
              ON m.member_id = vml.member_id
            WHERE v.website_id IS DISTINCT FROM m.website_id

            UNION ALL

            SELECT
                'session_member_website_mismatch',
                sma.session_member_attribution_id::text
            FROM public.session_member_attribution AS sma
            JOIN public.audience_session AS s
              ON s.session_id = sma.session_id
            JOIN public.website_member AS m
              ON m.member_id = sma.member_id
            WHERE s.website_id IS DISTINCT FROM m.website_id

            UNION ALL

            SELECT
                'session_member_visitor_linkage_missing',
                sma.session_member_attribution_id::text
            FROM public.session_member_attribution AS sma
            JOIN public.audience_session AS s
              ON s.session_id = sma.session_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.visitor_member_linkage AS vml
                WHERE vml.visitor_id = s.visitor_id
                  AND vml.member_id = sma.member_id
            );

-- DQ-23 | Acquisition
-- Every Signup Journey has one signup_started and one Acquisition Attribution
WITH signup_stats AS (
                SELECT
                    c.signup_journey_id,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'signup_started'
                    ) AS signup_started_count
                FROM public.signup_journey_context AS c
                LEFT JOIN public.signup_journey_event AS e
                  ON e.signup_journey_id = c.signup_journey_id
                GROUP BY c.signup_journey_id
            ),
            attribution_stats AS (
                SELECT
                    c.signup_journey_id,
                    COUNT(a.signup_journey_id) AS attribution_count
                FROM public.signup_journey_context AS c
                LEFT JOIN public.acquisition_source_attribution AS a
                  ON a.signup_journey_id = c.signup_journey_id
                GROUP BY c.signup_journey_id
            )
            SELECT
                s.signup_journey_id,
                s.signup_started_count,
                a.attribution_count
            FROM signup_stats AS s
            JOIN attribution_stats AS a
              ON a.signup_journey_id = s.signup_journey_id
            WHERE s.signup_started_count <> 1
               OR a.attribution_count <> 1;

-- DQ-24 | Acquisition
-- Resulting Account is created exactly once and not before Signup Started
WITH signup_stats AS (
                SELECT
                    c.signup_journey_id,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'signup_started'
                    ) AS signup_started_count,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'signup_started'
                    ) AS signup_started_at
                FROM public.signup_journey_context AS c
                LEFT JOIN public.signup_journey_event AS e
                  ON e.signup_journey_id = c.signup_journey_id
                GROUP BY c.signup_journey_id
            ),
            account_created_stats AS (
                SELECT
                    account_id,
                    COUNT(*) FILTER (
                        WHERE event_type = 'account_created'
                    ) AS created_count,
                    MIN(event_time) FILTER (
                        WHERE event_type = 'account_created'
                    ) AS account_created_at
                FROM public.account_lifecycle_event
                GROUP BY account_id
            )
            SELECT
                c.signup_journey_id,
                c.resulting_account_id
            FROM public.signup_journey_context AS c
            JOIN signup_stats AS s
              ON s.signup_journey_id = c.signup_journey_id
            LEFT JOIN account_created_stats AS ac
              ON ac.account_id = c.resulting_account_id
            WHERE c.resulting_account_id IS NOT NULL
              AND (
                    ac.account_id IS NULL
                    OR ac.created_count <> 1
                    OR s.signup_started_count <> 1
                    OR ac.account_created_at < s.signup_started_at
                  );

-- DQ-25 | Commercial
-- Subscription history starts Free and is continuous through Account lifetime
WITH account_bounds AS (
                SELECT
                    a.account_id,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'account_created'
                    ) AS created_time,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'account_closure'
                    ) AS closure_time
                FROM public.account AS a
                LEFT JOIN public.account_lifecycle_event AS e
                  ON e.account_id = a.account_id
                GROUP BY a.account_id
            ),
            ordered_plan AS (
                SELECT
                    p.*,
                    LAG(p.valid_to) OVER (
                        PARTITION BY p.account_id
                        ORDER BY p.valid_from, p.subscription_plan_period_id
                    ) AS previous_valid_to,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.account_id
                        ORDER BY p.valid_from, p.subscription_plan_period_id
                    ) AS rn_first,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.account_id
                        ORDER BY p.valid_from DESC, p.subscription_plan_period_id DESC
                    ) AS rn_last
                FROM public.subscription_plan_period AS p
            )
            SELECT
                'subscription_missing_history' AS violation_type,
                ab.account_id::text AS entity_id
            FROM account_bounds AS ab
            WHERE NOT EXISTS (
                SELECT 1
                FROM ordered_plan AS op
                WHERE op.account_id = ab.account_id
            )

            UNION ALL

            SELECT
                'subscription_invalid_start',
                op.subscription_plan_period_id::text
            FROM ordered_plan AS op
            JOIN account_bounds AS ab
              ON ab.account_id = op.account_id
            WHERE op.rn_first = 1
              AND (
                    op.plan_id <> 'PLAN_FREE'
                    OR op.valid_from IS DISTINCT FROM ab.created_time
                  )

            UNION ALL

            SELECT
                'subscription_internal_gap',
                op.subscription_plan_period_id::text
            FROM ordered_plan AS op
            WHERE op.rn_first > 1
              AND op.previous_valid_to IS DISTINCT FROM op.valid_from

            UNION ALL

            SELECT
                'subscription_invalid_end',
                op.subscription_plan_period_id::text
            FROM ordered_plan AS op
            JOIN account_bounds AS ab
              ON ab.account_id = op.account_id
            WHERE op.rn_last = 1
              AND (
                    (
                        ab.closure_time IS NULL
                        AND op.valid_to IS NOT NULL
                    )
                    OR (
                        ab.closure_time IS NOT NULL
                        AND op.valid_to IS DISTINCT FROM ab.closure_time
                    )
                  );

-- DQ-26 | Commercial
-- Billing Cycle periods are contained in exactly one Paid Plan interval
SELECT
                b.billing_cycle_period_id,
                b.account_id,
                b.valid_from,
                b.valid_to
            FROM public.billing_cycle_period AS b
            WHERE (
                SELECT COUNT(*)
                FROM public.subscription_plan_period AS p
                JOIN public.plan_catalog AS pc
                  ON pc.plan_id = p.plan_id
                WHERE p.account_id = b.account_id
                  AND pc.plan_name <> 'free'
                  AND b.valid_from >= p.valid_from
                  AND (
                        b.valid_to IS NULL
                        OR (
                            p.valid_to IS NOT NULL
                            AND b.valid_to <= p.valid_to
                        )
                        OR p.valid_to IS NULL
                      )
                  AND NOT (
                        b.valid_to IS NULL
                        AND p.valid_to IS NOT NULL
                      )
            ) <> 1;

-- DQ-27 | Commercial
-- Subscription lifecycle events agree with Plan and Billing history
WITH plan_boundaries AS (
                SELECT
                    old_p.account_id,
                    old_p.valid_to AS boundary_time,
                    old_p.plan_id AS old_plan_id,
                    new_p.plan_id AS new_plan_id
                FROM public.subscription_plan_period AS old_p
                JOIN public.subscription_plan_period AS new_p
                  ON new_p.account_id = old_p.account_id
                 AND old_p.valid_to = new_p.valid_from
            ),
            billing_boundaries AS (
                SELECT
                    old_b.account_id,
                    old_b.valid_to AS boundary_time,
                    old_b.billing_cycle AS old_cycle,
                    new_b.billing_cycle AS new_cycle
                FROM public.billing_cycle_period AS old_b
                JOIN public.billing_cycle_period AS new_b
                  ON new_b.account_id = old_b.account_id
                 AND old_b.valid_to = new_b.valid_from
            ),
            ranked_plan_boundaries AS (
                SELECT
                    pb.*,
                    CASE pb.old_plan_id
                        WHEN 'PLAN_FREE' THEN 0
                        WHEN 'PLAN_STANDARD' THEN 1
                        WHEN 'PLAN_PREMIUM' THEN 2
                    END AS old_rank,
                    CASE pb.new_plan_id
                        WHEN 'PLAN_FREE' THEN 0
                        WHEN 'PLAN_STANDARD' THEN 1
                        WHEN 'PLAN_PREMIUM' THEN 2
                    END AS new_rank
                FROM plan_boundaries AS pb
            )
            SELECT
                'plan_transition_without_boundary' AS violation_type,
                e.event_id::text AS entity_id
            FROM public.subscription_lifecycle_event AS e
            WHERE e.event_type IN (
                'subscription_upgraded',
                'subscription_downgraded',
                'subscription_cancelled',
                'subscription_reactivated'
            )
              AND NOT EXISTS (
                    SELECT 1
                    FROM ranked_plan_boundaries AS pb
                    WHERE pb.account_id = e.account_id
                      AND pb.boundary_time = e.event_time
              )

            UNION ALL

            SELECT
                'plan_transition_context_or_type_mismatch',
                e.event_id::text
            FROM public.subscription_lifecycle_event AS e
            JOIN ranked_plan_boundaries AS pb
              ON pb.account_id = e.account_id
             AND pb.boundary_time = e.event_time
            WHERE e.event_type IN (
                'subscription_upgraded',
                'subscription_downgraded',
                'subscription_cancelled',
                'subscription_reactivated'
            )
              AND (
                    (
                        e.from_plan_id IS NOT NULL
                        AND e.from_plan_id IS DISTINCT FROM pb.old_plan_id
                    )
                    OR (
                        e.to_plan_id IS NOT NULL
                        AND e.to_plan_id IS DISTINCT FROM pb.new_plan_id
                    )
                    OR (
                        e.event_type = 'subscription_upgraded'
                        AND NOT (pb.new_rank > pb.old_rank)
                    )
                    OR (
                        e.event_type = 'subscription_downgraded'
                        AND NOT (pb.new_rank < pb.old_rank)
                    )
                    OR (
                        e.event_type = 'subscription_cancelled'
                        AND NOT (
                            pb.old_plan_id <> 'PLAN_FREE'
                            AND pb.new_plan_id = 'PLAN_FREE'
                        )
                    )
                    OR (
                        e.event_type = 'subscription_reactivated'
                        AND NOT (
                            pb.old_plan_id = 'PLAN_FREE'
                            AND pb.new_plan_id <> 'PLAN_FREE'
                            AND EXISTS (
                                SELECT 1
                                FROM public.subscription_plan_period AS prior
                                WHERE prior.account_id = e.account_id
                                  AND prior.plan_id <> 'PLAN_FREE'
                                  AND prior.valid_to <= e.event_time
                            )
                        )
                    )
                  )

            UNION ALL

            SELECT
                'renewal_outside_paid_billing_context',
                e.event_id::text
            FROM public.subscription_lifecycle_event AS e
            WHERE e.event_type = 'subscription_renewed'
              AND (
                    (
                        SELECT COUNT(*)
                        FROM public.subscription_plan_period AS p
                        JOIN public.plan_catalog AS pc
                          ON pc.plan_id = p.plan_id
                        WHERE p.account_id = e.account_id
                          AND pc.plan_name <> 'free'
                          AND e.event_time >= p.valid_from
                          AND (
                                p.valid_to IS NULL
                                OR e.event_time < p.valid_to
                              )
                    ) <> 1
                    OR
                    (
                        SELECT COUNT(*)
                        FROM public.billing_cycle_period AS b
                        WHERE b.account_id = e.account_id
                          AND e.event_time >= b.valid_from
                          AND (
                                b.valid_to IS NULL
                                OR e.event_time < b.valid_to
                              )
                    ) <> 1
                  )

            UNION ALL

            SELECT
                'billing_cycle_change_without_boundary',
                e.event_id::text
            FROM public.subscription_lifecycle_event AS e
            WHERE e.event_type = 'billing_cycle_changed'
              AND NOT EXISTS (
                    SELECT 1
                    FROM billing_boundaries AS bb
                    WHERE bb.account_id = e.account_id
                      AND bb.boundary_time = e.event_time
                      AND bb.old_cycle IS DISTINCT FROM bb.new_cycle
              )

            UNION ALL

            SELECT
                'billing_cycle_change_context_mismatch',
                e.event_id::text
            FROM public.subscription_lifecycle_event AS e
            JOIN billing_boundaries AS bb
              ON bb.account_id = e.account_id
             AND bb.boundary_time = e.event_time
             AND bb.old_cycle IS DISTINCT FROM bb.new_cycle
            WHERE e.event_type = 'billing_cycle_changed'
              AND (
                    (
                        e.from_billing_cycle IS NOT NULL
                        AND e.from_billing_cycle IS DISTINCT FROM bb.old_cycle
                    )
                    OR (
                        e.to_billing_cycle IS NOT NULL
                        AND e.to_billing_cycle IS DISTINCT FROM bb.new_cycle
                    )
                  );

-- DQ-28 | Cross-domain
-- Account Closure is a hard boundary for Feature and Commercial history
WITH closures AS (
                SELECT
                    account_id,
                    MIN(event_time) AS closure_time
                FROM public.account_lifecycle_event
                WHERE event_type = 'account_closure'
                GROUP BY account_id
            )
            SELECT
                'feature_enablement_beyond_closure' AS violation_type,
                ep.enablement_period_id::text AS entity_id
            FROM public.website_feature_enablement_period AS ep
            JOIN public.website AS w
              ON w.website_id = ep.website_id
            JOIN closures AS c
              ON c.account_id = w.account_id
            WHERE ep.valid_to IS NULL
               OR ep.valid_to > c.closure_time

            UNION ALL

            SELECT
                'feature_event_after_closure',
                e.event_id::text
            FROM public.feature_enablement_lifecycle_event AS e
            JOIN public.website AS w
              ON w.website_id = e.website_id
            JOIN closures AS c
              ON c.account_id = w.account_id
            WHERE e.event_time > c.closure_time

            UNION ALL

            SELECT
                'subscription_period_beyond_closure',
                p.subscription_plan_period_id::text
            FROM public.subscription_plan_period AS p
            JOIN closures AS c
              ON c.account_id = p.account_id
            WHERE p.valid_to IS NULL
               OR p.valid_to > c.closure_time

            UNION ALL

            SELECT
                'billing_period_beyond_closure',
                b.billing_cycle_period_id::text
            FROM public.billing_cycle_period AS b
            JOIN closures AS c
              ON c.account_id = b.account_id
            WHERE b.valid_to IS NULL
               OR b.valid_to > c.closure_time

            UNION ALL

            SELECT
                'subscription_event_after_closure',
                e.event_id::text
            FROM public.subscription_lifecycle_event AS e
            JOIN closures AS c
              ON c.account_id = e.account_id
            WHERE e.event_time > c.closure_time

            UNION ALL

            SELECT
                'payment_event_after_closure',
                e.event_id::text
            FROM public.payment_refund_activity_event AS e
            JOIN closures AS c
              ON c.account_id = e.account_id
            WHERE e.event_time > c.closure_time;

-- DQ-29 | Commercial
-- Payment Succeeded occurs inside Paid Plan and Billing Cycle context
SELECT
                e.event_id,
                e.account_id,
                e.event_time
            FROM public.payment_refund_activity_event AS e
            WHERE e.event_type = 'payment_succeeded'
              AND (
                    (
                        SELECT COUNT(*)
                        FROM public.subscription_plan_period AS p
                        JOIN public.plan_catalog AS pc
                          ON pc.plan_id = p.plan_id
                        WHERE p.account_id = e.account_id
                          AND pc.plan_name <> 'free'
                          AND e.event_time >= p.valid_from
                          AND (
                                p.valid_to IS NULL
                                OR e.event_time < p.valid_to
                              )
                    ) <> 1
                    OR
                    (
                        SELECT COUNT(*)
                        FROM public.billing_cycle_period AS b
                        WHERE b.account_id = e.account_id
                          AND e.event_time >= b.valid_from
                          AND (
                                b.valid_to IS NULL
                                OR e.event_time < b.valid_to
                              )
                    ) <> 1
                  );

-- DQ-30 | Support
-- Support requester is an active Account Member at Opened time
SELECT
                e.event_id,
                sr.support_request_id,
                sr.requester_user_id,
                e.event_time
            FROM public.support_request AS sr
            JOIN public.support_lifecycle_event AS e
              ON e.support_request_id = sr.support_request_id
             AND e.event_type = 'support_request_opened'
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.user_account_membership AS m
                JOIN public.user_account_membership_period AS mp
                  ON mp.membership_id = m.membership_id
                WHERE m.user_id = sr.requester_user_id
                  AND m.account_id = sr.account_id
                  AND e.event_time >= mp.valid_from
                  AND (
                        mp.valid_to IS NULL
                        OR e.event_time < mp.valid_to
                      )
            );

-- DQ-31 | Support
-- Optional Support Website belongs to the Support Request Account
SELECT
                sr.support_request_id,
                sr.account_id,
                sr.website_id,
                w.account_id AS website_account_id
            FROM public.support_request AS sr
            JOIN public.website AS w
              ON w.website_id = sr.website_id
            WHERE sr.website_id IS NOT NULL
              AND w.account_id IS DISTINCT FROM sr.account_id;

-- DQ-32 | Support
-- Support lifecycle has exactly one Opened, at most one Resolved, and valid order
WITH support_stats AS (
                SELECT
                    sr.support_request_id,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'support_request_opened'
                    ) AS opened_count,
                    COUNT(e.event_id) FILTER (
                        WHERE e.event_type = 'support_request_resolved'
                    ) AS resolved_count,
                    MIN(e.event_time) FILTER (
                        WHERE e.event_type = 'support_request_opened'
                    ) AS opened_time,
                    MAX(e.event_time) FILTER (
                        WHERE e.event_type = 'support_request_resolved'
                    ) AS resolved_time
                FROM public.support_request AS sr
                LEFT JOIN public.support_lifecycle_event AS e
                  ON e.support_request_id = sr.support_request_id
                GROUP BY sr.support_request_id
            )
            SELECT
                support_request_id,
                opened_count,
                resolved_count,
                opened_time,
                resolved_time
            FROM support_stats
            WHERE opened_count <> 1
               OR resolved_count > 1
               OR (
                    resolved_count = 1
                    AND (
                        opened_time IS NULL
                        OR resolved_time < opened_time
                    )
                  );
