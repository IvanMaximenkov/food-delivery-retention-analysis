-- 02_load_data.sql
-- Load generated CSV files into MySQL tables.
--
-- Important for Windows + MySQL Workbench:
-- Put CSV files into C:/food_delivery_data first. This avoids issues with
-- Cyrillic characters in the Windows user folder path.
--
-- PowerShell command:
-- New-Item -ItemType Directory -Force C:\food_delivery_data
-- Copy-Item .\data\*.csv C:\food_delivery_data\ -Force

USE food_delivery_analytics;

-- If LOCAL INFILE is disabled, enable it in the server/client settings first.
-- Example for an admin session:
-- SET GLOBAL local_infile = 1;
SET SESSION sql_mode = '';

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/dim_users.csv'
INTO TABLE dim_users
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  user_id,
  @registration_ts,
  acquisition_channel,
  city,
  device_os,
  age,
  gender,
  loyalty_tier
)
SET registration_ts = STR_TO_DATE(@registration_ts, '%Y-%m-%d %H:%i:%s');

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/dim_restaurants.csv'
INTO TABLE dim_restaurants
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  restaurant_id,
  restaurant_name,
  cuisine_type,
  city,
  average_prep_minutes,
  rating
);

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/dim_couriers.csv'
INTO TABLE dim_couriers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  courier_id,
  city,
  courier_type,
  shift_type,
  @hire_date,
  avg_speed_kmh,
  on_time_rate
)
SET hire_date = STR_TO_DATE(@hire_date, '%Y-%m-%d');

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/dim_promo_campaigns.csv'
INTO TABLE dim_promo_campaigns
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  campaign_id,
  campaign_name,
  @start_date,
  @end_date,
  discount_pct,
  min_basket_rub,
  campaign_type
)
SET
  start_date = STR_TO_DATE(@start_date, '%Y-%m-%d'),
  end_date = STR_TO_DATE(@end_date, '%Y-%m-%d');

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/fact_orders.csv'
INTO TABLE fact_orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  order_id,
  user_id,
  restaurant_id,
  courier_id,
  @campaign_id,
  @order_ts,
  order_status,
  delivery_minutes,
  basket_value_rub,
  delivery_fee_rub,
  discount_rub,
  payment_method,
  distance_km,
  is_express,
  gross_margin_rub
)
SET
  campaign_id = NULLIF(@campaign_id, ''),
  order_ts = STR_TO_DATE(@order_ts, '%Y-%m-%d %H:%i:%s');

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/fact_order_items.csv'
INTO TABLE fact_order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  order_item_id,
  order_id,
  item_name,
  item_category,
  quantity,
  unit_price_rub,
  cogs_rub
);

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/fact_app_sessions.csv'
INTO TABLE fact_app_sessions
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  session_id,
  user_id,
  @session_start_ts,
  @session_end_ts,
  session_source,
  city,
  device_os,
  is_push_opened,
  did_order
)
SET
  session_start_ts = STR_TO_DATE(@session_start_ts, '%Y-%m-%d %H:%i:%s'),
  session_end_ts = STR_TO_DATE(@session_end_ts, '%Y-%m-%d %H:%i:%s');

LOAD DATA LOCAL INFILE 'C:/food_delivery_data/fact_ab_test_assignments.csv'
INTO TABLE fact_ab_test_assignments
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
  assignment_id,
  user_id,
  test_id,
  variant,
  @assigned_at,
  exposure_channel
)
SET assigned_at = STR_TO_DATE(@assigned_at, '%Y-%m-%d %H:%i:%s');
