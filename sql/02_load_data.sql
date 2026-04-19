-- =============================================
-- 02_load_data.sql
-- Полная загрузка всех 7 таблиц
-- =============================================

USE food_delivery;

SET FOREIGN_KEY_CHECKS = 0;

-- Очистка всех таблиц (в безопасном порядке)
TRUNCATE TABLE promotions;
TRUNCATE TABLE payments;
TRUNCATE TABLE deliveries;
TRUNCATE TABLE order_items;
TRUNCATE TABLE events;
TRUNCATE TABLE orders;
TRUNCATE TABLE users;

-- =============================================
-- ЗАГРУЗКА ДАННЫХ (замени путь, если нужно)
-- =============================================
SET @upload_path = 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/';

-- 1. Пользователи
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/users.csv'
INTO TABLE users
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(user_id, registration_date, city, age, gender, device, acquisition_channel, ab_group);

-- 2. Заказы
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/orders.csv'
INTO TABLE orders
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(order_id, user_id, order_date, order_amount, ab_group, city);

-- 3. Позиции заказов
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/order_items.csv'
INTO TABLE order_items
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(order_item_id, order_id, item_name, quantity, price);

-- 4. Доставки
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/deliveries.csv'
INTO TABLE deliveries
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(delivery_id, order_id, delivery_date, delivery_time_minutes, status);

-- 5. События
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/events.csv'
INTO TABLE events
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(event_id, user_id, event_date, event_type, ab_group);

-- 6. Платежи
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/payments.csv'
INTO TABLE payments
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(payment_id, order_id, payment_date, amount, payment_method);

-- 7. Промоакции
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/promotions.csv'
INTO TABLE promotions
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(promo_id, user_id, order_id, promo_code, discount_amount, promo_date);

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================
-- ПРОВЕРКА ЗАГРУЗКИ
-- =============================================
SELECT 'users'          AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'orders'         , COUNT(*) FROM orders
UNION ALL
SELECT 'order_items'    , COUNT(*) FROM order_items
UNION ALL
SELECT 'deliveries'     , COUNT(*) FROM deliveries
UNION ALL
SELECT 'events'         , COUNT(*) FROM events
UNION ALL
SELECT 'payments'       , COUNT(*) FROM payments
UNION ALL
SELECT 'promotions'     , COUNT(*) FROM promotions
ORDER BY table_name;