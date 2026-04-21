-- 06_business_metrics.sql
-- Core business metrics and actionable slices.

USE food_delivery_analytics;

-- 1) Daily KPI dashboard: orders, DAU, conversion, AOV, GMV, margin.
WITH sessions_daily AS (
    SELECT
        DATE(session_start_ts) AS dt,
        COUNT(DISTINCT user_id) AS dau,
        COUNT(*) AS sessions_n
    FROM fact_app_sessions
    GROUP BY DATE(session_start_ts)
),
orders_daily AS (
    SELECT
        DATE(order_ts) AS dt,
        COUNT(*) AS delivered_orders_n,
        COUNT(DISTINCT user_id) AS buyers_n,
        ROUND(SUM(basket_value_rub + delivery_fee_rub - discount_rub), 2) AS gmv_rub,
        ROUND(SUM(gross_margin_rub), 2) AS gross_margin_rub,
        ROUND(AVG(basket_value_rub), 2) AS aov_rub
    FROM fact_orders
    WHERE order_status = 'delivered'
    GROUP BY DATE(order_ts)
)
SELECT
    s.dt,
    s.dau,
    s.sessions_n,
    COALESCE(o.delivered_orders_n, 0) AS delivered_orders_n,
    COALESCE(o.buyers_n, 0) AS buyers_n,
    ROUND(COALESCE(o.buyers_n, 0) / NULLIF(s.dau, 0), 4) AS buyer_conversion_from_dau,
    COALESCE(o.aov_rub, 0) AS aov_rub,
    COALESCE(o.gmv_rub, 0) AS gmv_rub,
    COALESCE(o.gross_margin_rub, 0) AS gross_margin_rub
FROM sessions_daily s
LEFT JOIN orders_daily o
  ON s.dt = o.dt
ORDER BY s.dt;


-- 2) Weekly retention proxy and stickiness (WAU/MAU).
WITH users_by_day AS (
    SELECT DATE(session_start_ts) AS dt, user_id
    FROM fact_app_sessions
    GROUP BY DATE(session_start_ts), user_id
),
users_by_week AS (
    SELECT
        STR_TO_DATE(CONCAT(YEARWEEK(dt, 1), ' Monday'), '%X%V %W') AS week_start,
        user_id
    FROM users_by_day
    GROUP BY STR_TO_DATE(CONCAT(YEARWEEK(dt, 1), ' Monday'), '%X%V %W'), user_id
),
users_by_month AS (
    SELECT DATE_FORMAT(dt, '%Y-%m') AS ym, user_id
    FROM users_by_day
    GROUP BY DATE_FORMAT(dt, '%Y-%m'), user_id
),
wau AS (
    SELECT week_start, COUNT(DISTINCT user_id) AS wau
    FROM users_by_week
    GROUP BY week_start
),
mau AS (
    SELECT ym, COUNT(DISTINCT user_id) AS mau
    FROM users_by_month
    GROUP BY ym
)
SELECT
    w.week_start,
    w.wau,
    DATE_FORMAT(w.week_start, '%Y-%m') AS ym,
    m.mau,
    ROUND(w.wau / NULLIF(m.mau, 0), 4) AS stickiness_wau_mau
FROM wau w
JOIN mau m
  ON DATE_FORMAT(w.week_start, '%Y-%m') = m.ym
ORDER BY w.week_start;


-- 3) Repeat purchase rate by acquisition channel.
WITH delivered AS (
    SELECT user_id, COUNT(*) AS delivered_orders_n
    FROM fact_orders
    WHERE order_status = 'delivered'
    GROUP BY user_id
)
SELECT
    u.acquisition_channel,
    COUNT(*) AS users_n,
    ROUND(AVG(CASE WHEN d.delivered_orders_n >= 2 THEN 1 ELSE 0 END), 4) AS repeat_purchase_rate,
    ROUND(AVG(COALESCE(d.delivered_orders_n, 0)), 2) AS avg_orders_per_user
FROM dim_users u
LEFT JOIN delivered d
  ON u.user_id = d.user_id
GROUP BY u.acquisition_channel
ORDER BY repeat_purchase_rate DESC;


-- 4) City-level profitability and SLA quality.
SELECT
    u.city,
    COUNT(*) AS delivered_orders_n,
    ROUND(AVG(o.delivery_minutes), 2) AS avg_delivery_minutes,
    ROUND(AVG(CASE WHEN o.delivery_minutes <= 35 THEN 1 ELSE 0 END), 4) AS on_time_share,
    ROUND(SUM(o.gross_margin_rub), 2) AS total_margin_rub,
    ROUND(AVG(o.gross_margin_rub), 2) AS margin_per_order_rub
FROM fact_orders o
JOIN dim_users u
  ON o.user_id = u.user_id
WHERE o.order_status = 'delivered'
GROUP BY u.city
ORDER BY total_margin_rub DESC;


-- 5) Revenue at risk: users inactive 28+ days, ranked by historical value.
WITH anchor AS (
    SELECT MAX(DATE(order_ts)) AS max_order_date
    FROM fact_orders
    WHERE order_status = 'delivered'
),
user_value AS (
    SELECT
        user_id,
        MAX(DATE(order_ts)) AS last_order_date,
        SUM(gross_margin_rub) AS total_margin_rub,
        COUNT(*) AS delivered_orders_n
    FROM fact_orders
    WHERE order_status = 'delivered'
    GROUP BY user_id
),
churn_risk AS (
    SELECT
        v.user_id,
        DATEDIFF((SELECT max_order_date FROM anchor), v.last_order_date) AS days_inactive,
        v.total_margin_rub,
        v.delivered_orders_n
    FROM user_value v
)
SELECT
    c.user_id,
    c.days_inactive,
    ROUND(c.total_margin_rub, 2) AS total_margin_rub,
    c.delivered_orders_n
FROM churn_risk c
WHERE c.days_inactive >= 28
ORDER BY c.total_margin_rub DESC, c.days_inactive DESC
LIMIT 500;
