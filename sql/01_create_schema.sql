-- 01_create_schema.sql
-- Food Delivery Retention & Churn Analytics
-- MySQL 8.0+

DROP DATABASE IF EXISTS food_delivery_analytics;
CREATE DATABASE food_delivery_analytics
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE food_delivery_analytics;

-- ========== Dimension tables ==========

CREATE TABLE dim_users (
    user_id BIGINT PRIMARY KEY,
    registration_ts DATETIME NOT NULL,
    acquisition_channel VARCHAR(32) NOT NULL,
    city VARCHAR(64) NOT NULL,
    device_os VARCHAR(16) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(16) NOT NULL,
    loyalty_tier VARCHAR(16) NOT NULL
);

CREATE TABLE dim_restaurants (
    restaurant_id BIGINT PRIMARY KEY,
    restaurant_name VARCHAR(128) NOT NULL,
    cuisine_type VARCHAR(64) NOT NULL,
    city VARCHAR(64) NOT NULL,
    average_prep_minutes INT NOT NULL,
    rating DECIMAL(3, 2) NOT NULL
);

CREATE TABLE dim_couriers (
    courier_id BIGINT PRIMARY KEY,
    city VARCHAR(64) NOT NULL,
    courier_type VARCHAR(16) NOT NULL,
    shift_type VARCHAR(16) NOT NULL,
    hire_date DATE NOT NULL,
    avg_speed_kmh DECIMAL(5, 2) NOT NULL,
    on_time_rate DECIMAL(5, 4) NOT NULL
);

CREATE TABLE dim_promo_campaigns (
    campaign_id BIGINT PRIMARY KEY,
    campaign_name VARCHAR(128) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    discount_pct DECIMAL(5, 2) NOT NULL,
    min_basket_rub DECIMAL(12, 2) NOT NULL,
    campaign_type VARCHAR(32) NOT NULL
);

-- ========== Fact tables ==========

CREATE TABLE fact_orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    restaurant_id BIGINT NOT NULL,
    courier_id BIGINT NOT NULL,
    campaign_id BIGINT NULL,
    order_ts DATETIME NOT NULL,
    order_status VARCHAR(16) NOT NULL,
    delivery_minutes INT NOT NULL,
    basket_value_rub DECIMAL(12, 2) NOT NULL,
    delivery_fee_rub DECIMAL(12, 2) NOT NULL,
    discount_rub DECIMAL(12, 2) NOT NULL,
    payment_method VARCHAR(32) NOT NULL,
    distance_km DECIMAL(8, 2) NOT NULL,
    is_express TINYINT NOT NULL,
    gross_margin_rub DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES dim_users (user_id),
    CONSTRAINT fk_orders_restaurant FOREIGN KEY (restaurant_id) REFERENCES dim_restaurants (restaurant_id),
    CONSTRAINT fk_orders_courier FOREIGN KEY (courier_id) REFERENCES dim_couriers (courier_id),
    CONSTRAINT fk_orders_campaign FOREIGN KEY (campaign_id) REFERENCES dim_promo_campaigns (campaign_id)
);

CREATE TABLE fact_order_items (
    order_item_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    item_name VARCHAR(128) NOT NULL,
    item_category VARCHAR(32) NOT NULL,
    quantity INT NOT NULL,
    unit_price_rub DECIMAL(12, 2) NOT NULL,
    cogs_rub DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES fact_orders (order_id)
);

CREATE TABLE fact_app_sessions (
    session_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    session_start_ts DATETIME NOT NULL,
    session_end_ts DATETIME NOT NULL,
    session_source VARCHAR(32) NOT NULL,
    city VARCHAR(64) NOT NULL,
    device_os VARCHAR(16) NOT NULL,
    is_push_opened TINYINT NOT NULL,
    did_order TINYINT NOT NULL,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES dim_users (user_id)
);

CREATE TABLE fact_ab_test_assignments (
    assignment_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    test_id VARCHAR(64) NOT NULL,
    variant VARCHAR(32) NOT NULL,
    assigned_at DATETIME NOT NULL,
    exposure_channel VARCHAR(32) NOT NULL,
    CONSTRAINT uk_ab_user_test UNIQUE (user_id, test_id),
    CONSTRAINT fk_ab_user FOREIGN KEY (user_id) REFERENCES dim_users (user_id)
);

-- ========== Performance indexes ==========

CREATE INDEX idx_users_registration_ts ON dim_users (registration_ts);
CREATE INDEX idx_users_city_channel ON dim_users (city, acquisition_channel);

CREATE INDEX idx_orders_user_ts ON fact_orders (user_id, order_ts);
CREATE INDEX idx_orders_ts_status ON fact_orders (order_ts, order_status);
CREATE INDEX idx_orders_restaurant_ts ON fact_orders (restaurant_id, order_ts);
CREATE INDEX idx_orders_campaign ON fact_orders (campaign_id);

CREATE INDEX idx_order_items_order_id ON fact_order_items (order_id);

CREATE INDEX idx_sessions_user_start ON fact_app_sessions (user_id, session_start_ts);
CREATE INDEX idx_sessions_start_source ON fact_app_sessions (session_start_ts, session_source);

CREATE INDEX idx_ab_test_variant ON fact_ab_test_assignments (test_id, variant);
CREATE INDEX idx_ab_assigned_at ON fact_ab_test_assignments (assigned_at);
