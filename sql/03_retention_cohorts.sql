-- =============================================
-- 03_retention_cohorts.sql — ИСПРАВЛЕННАЯ ВЕРСИЯ
-- =============================================

USE food_delivery;

WITH user_cohorts AS (
    SELECT
        user_id,
        ab_group,
        device,
        acquisition_channel,
        city,
        DATE(registration_date) AS reg_date,
        DATE_SUB(DATE(registration_date), INTERVAL WEEKDAY(registration_date) DAY) AS cohort_week
    FROM users
),

-- Активность пользователей по дням относительно регистрации
daily_activity AS (
    SELECT
        uc.user_id,
        uc.cohort_week,
        uc.ab_group,
        uc.device,
        uc.acquisition_channel,
        uc.city,
        uc.reg_date,
        DATEDIFF(DATE(o.order_date), uc.reg_date) AS day_since_reg,
        o.order_amount
    FROM user_cohorts uc
    JOIN orders o ON uc.user_id = o.user_id
    WHERE DATEDIFF(DATE(o.order_date), uc.reg_date) >= 0
),

cohort_metrics AS (
    SELECT
        cohort_week,
        ab_group,
        device,
        acquisition_channel,
        city,
        COUNT(DISTINCT user_id) AS cohort_size,

        -- Retention по дням
        COUNT(DISTINCT CASE WHEN day_since_reg = 0 THEN user_id END) / COUNT(DISTINCT user_id) AS ret_d0,
        COUNT(DISTINCT CASE WHEN day_since_reg <= 1 THEN user_id END) / COUNT(DISTINCT user_id) AS ret_d1,
        COUNT(DISTINCT CASE WHEN day_since_reg <= 7 THEN user_id END) / COUNT(DISTINCT user_id) AS ret_d7,
        COUNT(DISTINCT CASE WHEN day_since_reg <= 14 THEN user_id END) / COUNT(DISTINCT user_id) AS ret_d14,
        COUNT(DISTINCT CASE WHEN day_since_reg <= 30 THEN user_id END) / COUNT(DISTINCT user_id) AS ret_d30
    FROM daily_activity
    GROUP BY cohort_week, ab_group, device, acquisition_channel, city
    HAVING cohort_size >= 300
)

SELECT
    cohort_week,
    ab_group,
    device,
    acquisition_channel,
    city,
    cohort_size,
    ROUND(ret_d0 * 100, 2)  AS ret_d0_pct,
    ROUND(ret_d1 * 100, 2)  AS ret_d1_pct,
    ROUND(ret_d7 * 100, 2)  AS ret_d7_pct,
    ROUND(ret_d14 * 100, 2) AS ret_d14_pct,
    ROUND(ret_d30 * 100, 2) AS ret_d30_pct
FROM cohort_metrics
ORDER BY cohort_week, ab_group, device, acquisition_channel, city;