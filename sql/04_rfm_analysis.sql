-- 04_rfm_analysis.sql
-- RFM scoring + LTV estimation

USE food_delivery_analytics;

WITH delivered_orders AS (
    SELECT *
    FROM fact_orders
    WHERE order_status = 'delivered'
),
global_anchor AS (
    SELECT DATE(MAX(order_ts)) AS anchor_date
    FROM delivered_orders
),
user_metrics AS (
    SELECT
        o.user_id,
        DATEDIFF((SELECT anchor_date FROM global_anchor), DATE(MAX(o.order_ts))) AS recency_days,
        COUNT(*) AS frequency_orders,
        ROUND(SUM(o.basket_value_rub - o.discount_rub + o.delivery_fee_rub), 2) AS monetary_rub,
        ROUND(SUM(o.gross_margin_rub), 2) AS gross_margin_rub,
        ROUND(AVG(o.basket_value_rub), 2) AS avg_order_value_rub,
        DATEDIFF(DATE(MAX(o.order_ts)), DATE(MIN(o.order_ts))) + 1 AS active_days
    FROM delivered_orders o
    GROUP BY o.user_id
),
rfm_scored AS (
    SELECT
        m.*,
        (6 - NTILE(5) OVER (ORDER BY recency_days ASC)) AS r_score,
        NTILE(5) OVER (ORDER BY frequency_orders ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary_rub ASC) AS m_score
    FROM user_metrics m
),
rfm_segmented AS (
    SELECT
        user_id,
        recency_days,
        frequency_orders,
        monetary_rub,
        gross_margin_rub,
        avg_order_value_rub,
        active_days,
        r_score,
        f_score,
        m_score,
        CONCAT(r_score, f_score, m_score) AS rfm_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 4 AND f_score >= 3 THEN 'Loyal'
            WHEN r_score >= 4 AND f_score <= 2 THEN 'Promising'
            WHEN r_score = 3 AND f_score >= 3 THEN 'Needs Attention'
            WHEN r_score <= 2 AND f_score >= 4 THEN 'At Risk High Value'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
            ELSE 'Potential Loyalists'
        END AS segment
    FROM rfm_scored
),
ltv_estimate AS (
    SELECT
        s.*,
        ROUND(monetary_rub / GREATEST(active_days / 30.0, 1), 2) AS monthly_revenue_rub,
        CASE
            WHEN segment = 'Champions' THEN 14
            WHEN segment = 'Loyal' THEN 11
            WHEN segment = 'Potential Loyalists' THEN 9
            WHEN segment = 'Promising' THEN 6
            WHEN segment = 'Needs Attention' THEN 5
            WHEN segment = 'At Risk High Value' THEN 4
            WHEN segment = 'Hibernating' THEN 2
            ELSE 3
        END AS expected_lifetime_months
    FROM rfm_segmented s
)
SELECT
    user_id,
    recency_days,
    frequency_orders,
    monetary_rub,
    gross_margin_rub,
    avg_order_value_rub,
    segment,
    rfm_score,
    monthly_revenue_rub,
    expected_lifetime_months,
    ROUND(monthly_revenue_rub * expected_lifetime_months * 0.28, 2) AS predicted_ltv_rub
FROM ltv_estimate
ORDER BY predicted_ltv_rub DESC;


-- Segment-level business view.
WITH rfm_output AS (
    WITH delivered_orders AS (
        SELECT *
        FROM fact_orders
        WHERE order_status = 'delivered'
    ),
    global_anchor AS (
        SELECT DATE(MAX(order_ts)) AS anchor_date
        FROM delivered_orders
    ),
    user_metrics AS (
        SELECT
            o.user_id,
            DATEDIFF((SELECT anchor_date FROM global_anchor), DATE(MAX(o.order_ts))) AS recency_days,
            COUNT(*) AS frequency_orders,
            ROUND(SUM(o.basket_value_rub - o.discount_rub + o.delivery_fee_rub), 2) AS monetary_rub
        FROM delivered_orders o
        GROUP BY o.user_id
    ),
    scored AS (
        SELECT
            m.*,
            (6 - NTILE(5) OVER (ORDER BY recency_days ASC)) AS r_score,
            NTILE(5) OVER (ORDER BY frequency_orders ASC) AS f_score,
            NTILE(5) OVER (ORDER BY monetary_rub ASC) AS m_score
        FROM user_metrics m
    )
    SELECT
        user_id,
        recency_days,
        frequency_orders,
        monetary_rub,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'Hibernating'
            ELSE 'Other'
        END AS segment
    FROM scored
)
SELECT
    segment,
    COUNT(*) AS users_cnt,
    ROUND(AVG(recency_days), 2) AS avg_recency_days,
    ROUND(AVG(frequency_orders), 2) AS avg_frequency_orders,
    ROUND(AVG(monetary_rub), 2) AS avg_monetary_rub
FROM rfm_output
GROUP BY segment
ORDER BY avg_monetary_rub DESC;
