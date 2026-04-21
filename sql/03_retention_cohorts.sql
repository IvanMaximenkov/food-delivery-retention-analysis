-- 03_retention_cohorts.sql
-- Cohort retention analysis (D1 / D7 / D14 / D30 / D60)

USE food_delivery_analytics;

WITH first_orders AS (
    SELECT
        user_id,
        DATE(MIN(order_ts)) AS cohort_date
    FROM fact_orders
    WHERE order_status = 'delivered'
    GROUP BY user_id
),
user_activity AS (
    SELECT
        fo.user_id,
        fo.cohort_date,
        DATEDIFF(DATE(o.order_ts), fo.cohort_date) AS cohort_day
    FROM first_orders fo
    JOIN fact_orders o
        ON o.user_id = fo.user_id
       AND o.order_status = 'delivered'
    WHERE DATEDIFF(DATE(o.order_ts), fo.cohort_date) BETWEEN 0 AND 90
),
cohort_sizes AS (
    SELECT
        cohort_date,
        COUNT(DISTINCT user_id) AS cohort_size
    FROM first_orders
    GROUP BY cohort_date
),
retention_daily AS (
    SELECT
        cohort_date,
        cohort_day,
        COUNT(DISTINCT user_id) AS retained_users
    FROM user_activity
    GROUP BY cohort_date, cohort_day
),
retention_curve AS (
    SELECT
        r.cohort_date,
        r.cohort_day,
        c.cohort_size,
        r.retained_users,
        ROUND(100.0 * r.retained_users / c.cohort_size, 2) AS retention_pct,
        ROUND(
            AVG(100.0 * r.retained_users / c.cohort_size) OVER (
                PARTITION BY r.cohort_day
                ORDER BY r.cohort_date
                ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
            ),
            2
        ) AS smoothed_retention_pct
    FROM retention_daily r
    JOIN cohort_sizes c
      ON r.cohort_date = c.cohort_date
)
SELECT
    cohort_date,
    cohort_day,
    cohort_size,
    retained_users,
    retention_pct,
    smoothed_retention_pct
FROM retention_curve
ORDER BY cohort_date, cohort_day;


-- Cohort-level pivot to quickly compare milestone retention.
WITH first_orders AS (
    SELECT user_id, DATE(MIN(order_ts)) AS cohort_date
    FROM fact_orders
    WHERE order_status = 'delivered'
    GROUP BY user_id
),
activity AS (
    SELECT
        fo.cohort_date,
        fo.user_id,
        DATEDIFF(DATE(o.order_ts), fo.cohort_date) AS cohort_day
    FROM first_orders fo
    JOIN fact_orders o
      ON fo.user_id = o.user_id
     AND o.order_status = 'delivered'
),
cohort_size AS (
    SELECT cohort_date, COUNT(DISTINCT user_id) AS users_in_cohort
    FROM first_orders
    GROUP BY cohort_date
)
SELECT
    a.cohort_date,
    c.users_in_cohort,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.cohort_day = 1 THEN a.user_id END) / c.users_in_cohort, 2) AS d1_retention_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.cohort_day = 7 THEN a.user_id END) / c.users_in_cohort, 2) AS d7_retention_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.cohort_day = 14 THEN a.user_id END) / c.users_in_cohort, 2) AS d14_retention_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.cohort_day = 30 THEN a.user_id END) / c.users_in_cohort, 2) AS d30_retention_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.cohort_day = 60 THEN a.user_id END) / c.users_in_cohort, 2) AS d60_retention_pct
FROM activity a
JOIN cohort_size c
  ON a.cohort_date = c.cohort_date
GROUP BY a.cohort_date, c.users_in_cohort
ORDER BY a.cohort_date;


-- Main product retention metric for food delivery:
-- share of new users who made at least one repeat delivered order
-- within 30 days after their first delivered order.
WITH anchor AS (
    SELECT MAX(order_ts) AS max_order_ts
    FROM fact_orders
    WHERE order_status = 'delivered'
),
first_orders AS (
    SELECT
        user_id,
        MIN(order_ts) AS first_order_ts,
        DATE_FORMAT(MIN(order_ts), '%Y-%m') AS cohort_month
    FROM fact_orders
    WHERE order_status = 'delivered'
    GROUP BY user_id
),
eligible_users AS (
    SELECT
        fo.user_id,
        fo.first_order_ts,
        fo.cohort_month
    FROM first_orders fo
    CROSS JOIN anchor a
    WHERE fo.first_order_ts <= DATE_SUB(a.max_order_ts, INTERVAL 30 DAY)
),
repeat_users_30d AS (
    SELECT DISTINCT
        e.user_id
    FROM eligible_users e
    JOIN fact_orders o
      ON o.user_id = e.user_id
     AND o.order_status = 'delivered'
     AND o.order_ts > e.first_order_ts
     AND o.order_ts <= DATE_ADD(e.first_order_ts, INTERVAL 30 DAY)
)
SELECT
    e.cohort_month,
    COUNT(DISTINCT e.user_id) AS users_base,
    COUNT(DISTINCT r.user_id) AS repeat_users_30d,
    ROUND(100.0 * COUNT(DISTINCT r.user_id) / COUNT(DISTINCT e.user_id), 2) AS repeat_order_rate_30d_pct
FROM eligible_users e
LEFT JOIN repeat_users_30d r
  ON e.user_id = r.user_id
GROUP BY e.cohort_month
ORDER BY e.cohort_month;
