-- Загрузка синтетических данных из CSV

USE food_delivery;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE payments;
TRUNCATE TABLE promotions;
TRUNCATE TABLE deliveries;
TRUNCATE TABLE order_items;
TRUNCATE TABLE events;
TRUNCATE TABLE orders;
TRUNCATE TABLE users;

-- Загрузка пользователей
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/users.csv'
INTO TABLE users
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(user_id, registration_date, city, age, gender, device, acquisition_channel, ab_group);

-- Загрузка заказов
LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 9.5/Uploads/orders.csv'
INTO TABLE orders
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(order_id, user_id, order_date, order_amount, ab_group, city);

SET FOREIGN_KEY_CHECKS = 1;

-- проверка данных
SELECT 'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'orders' as table_name, COUNT(*) FROM orders;