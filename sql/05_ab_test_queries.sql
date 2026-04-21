-- 05_ab_test_queries.sql
-- A/B test: free_delivery_banner_v1
-- Goal: improve 7-day conversion to order after assignment.

USE food_delivery_analytics;

-- 1) Sample ratio check (SRM guardrail).
SELECT
    variant,
    COUNT(*) AS assigned_users,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM fact_ab_test_assignments
WHERE test_id = 'free_delivery_banner_v1'
GROUP BY variant;


-- 2) Primary metric: 7-day conversion to first delivered order.
WITH exposure AS (
    SELECT
        user_id,
        variant,
        assigned_at
    FROM fact_ab_test_assignments
    WHERE test_id = 'free_delivery_banner_v1'
),
orders_7d AS (
    SELECT
        e.user_id,
        e.variant,
        CASE
            WHEN MIN(o.order_ts) IS NOT NULL THEN 1 ELSE 0
        END AS converted_7d
    FROM exposure e
    LEFT JOIN fact_orders o
      ON o.user_id = e.user_id
     AND o.order_status = 'delivered'
     AND o.order_ts >= e.assigned_at
     AND o.order_ts < DATE_ADD(e.assigned_at, INTERVAL 7 DAY)
    GROUP BY e.user_id, e.variant
),
agg AS (
    SELECT
        variant,
        COUNT(*) AS users_n,
        SUM(converted_7d) AS converted_users_n,
        ROUND(AVG(converted_7d), 4) AS conversion_7d
    FROM orders_7d
    GROUP BY variant
)
SELECT
    variant,
    users_n,
    converted_users_n,
    conversion_7d,
    ROUND(100 * conversion_7d, 2) AS conversion_7d_pct
FROM agg
ORDER BY variant;


-- 3) Statistical test (two-proportion z-test approximation).
WITH exposure AS (
    SELECT user_id, variant, assigned_at
    FROM fact_ab_test_assignments
    WHERE test_id = 'free_delivery_banner_v1'
),
orders_7d AS (
    SELECT
        e.user_id,
        e.variant,
        CASE WHEN MIN(o.order_ts) IS NOT NULL THEN 1 ELSE 0 END AS converted_7d
    FROM exposure e
    LEFT JOIN fact_orders o
      ON o.user_id = e.user_id
     AND o.order_status = 'delivered'
     AND o.order_ts >= e.assigned_at
     AND o.order_ts < DATE_ADD(e.assigned_at, INTERVAL 7 DAY)
    GROUP BY e.user_id, e.variant
),
agg AS (
    SELECT
        variant,
        COUNT(*) AS n_users,
        SUM(converted_7d) AS n_converted,
        AVG(converted_7d) AS conversion_rate
    FROM orders_7d
    GROUP BY variant
),
ctrl AS (
    SELECT n_users AS n_c, n_converted AS x_c, conversion_rate AS p_c
    FROM agg WHERE variant = 'control'
),
trt AS (
    SELECT n_users AS n_t, n_converted AS x_t, conversion_rate AS p_t
    FROM agg WHERE variant = 'treatment'
)
SELECT
    c.n_c,
    t.n_t,
    c.p_c AS control_rate,
    t.p_t AS treatment_rate,
    (t.p_t - c.p_c) AS absolute_uplift,
    100 * (t.p_t - c.p_c) AS uplift_pp,
    ((c.x_c + t.x_t) / (c.n_c + t.n_t)) AS pooled_p,
    (
        (t.p_t - c.p_c) /
        SQRT(
            ((c.x_c + t.x_t) / (c.n_c + t.n_t))
            * (1 - ((c.x_c + t.x_t) / (c.n_c + t.n_t)))
            * (1 / c.n_c + 1 / t.n_t)
        )
    ) AS z_stat,
    CASE
        WHEN ABS(
            (
                (t.p_t - c.p_c) /
                SQRT(
                    ((c.x_c + t.x_t) / (c.n_c + t.n_t))
                    * (1 - ((c.x_c + t.x_t) / (c.n_c + t.n_t)))
                    * (1 / c.n_c + 1 / t.n_t)
                )
            )
        ) >= 1.96 THEN 'significant_at_95'
        ELSE 'not_significant'
    END AS significance_95
FROM ctrl c
CROSS JOIN trt t;


-- 4) Business impact in RUB (monthly projection).
-- Assumptions:
-- - 1 converted user in 7 days leads to 1.8 delivered orders in 30 days.
-- - average gross margin per delivered order = avg(gross_margin_rub).
WITH exposure AS (
    SELECT user_id, variant, assigned_at
    FROM fact_ab_test_assignments
    WHERE test_id = 'free_delivery_banner_v1'
),
orders_7d AS (
    SELECT
        e.user_id,
        e.variant,
        CASE WHEN MIN(o.order_ts) IS NOT NULL THEN 1 ELSE 0 END AS converted_7d
    FROM exposure e
    LEFT JOIN fact_orders o
      ON o.user_id = e.user_id
     AND o.order_status = 'delivered'
     AND o.order_ts >= e.assigned_at
     AND o.order_ts < DATE_ADD(e.assigned_at, INTERVAL 7 DAY)
    GROUP BY e.user_id, e.variant
),
agg AS (
    SELECT
        variant,
        COUNT(*) AS n_users,
        AVG(converted_7d) AS conversion_rate
    FROM orders_7d
    GROUP BY variant
),
ctrl AS (
    SELECT n_users AS n_c, conversion_rate AS p_c
    FROM agg WHERE variant = 'control'
),
trt AS (
    SELECT n_users AS n_t, conversion_rate AS p_t
    FROM agg WHERE variant = 'treatment'
),
econ AS (
    SELECT
        (t.p_t - c.p_c) AS absolute_uplift,
        t.n_t AS treatment_users,
        (
            (t.p_t - c.p_c)
            * t.n_t
            * 1.8
            * (SELECT AVG(gross_margin_rub) FROM fact_orders WHERE order_status = 'delivered')
        ) AS incremental_gross_margin_rub_30d
    FROM ctrl c
    CROSS JOIN trt t
)
SELECT
    ROUND(100 * absolute_uplift, 2) AS uplift_pp,
    treatment_users,
    ROUND(incremental_gross_margin_rub_30d, 2) AS incremental_gross_margin_rub_30d,
    ROUND(incremental_gross_margin_rub_30d * 12, 2) AS projected_incremental_gross_margin_rub_annual
FROM econ;
