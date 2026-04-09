-- =============================================
-- 01_create_schema.sql
-- Создание схемы базы данных для проекта Food Delivery
-- =============================================

-- Удаляем базу, если она уже существует (для удобства разработки)
-- DROP DATABASE IF EXISTS food_delivery;
-- CREATE DATABASE food_delivery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE food_delivery;

-- =============================================
-- 1. Таблица пользователей (Dimension)
-- =============================================
CREATE TABLE IF NOT EXISTS users (
    user_id              INT PRIMARY KEY,
    registration_date    DATETIME NOT NULL,
    city                 VARCHAR(50) NOT NULL,
    age                  TINYINT UNSIGNED,
    gender               ENUM('male', 'female', 'other'),
    device               ENUM('android', 'ios'),
    acquisition_channel  VARCHAR(50),
    ab_group             ENUM('A', 'B') NOT NULL,

    INDEX idx_registration_date (registration_date),
    INDEX idx_city (city),
    INDEX idx_ab_group (ab_group)
) ENGINE=InnoDB;

-- =============================================
-- 2. Таблица заказов (Fact)
-- =============================================
CREATE TABLE IF NOT EXISTS orders (
    order_id       INT PRIMARY KEY,
    user_id        INT NOT NULL,
    order_date     DATETIME NOT NULL,
    order_amount   DECIMAL(10,2) NOT NULL,
    ab_group       ENUM('A', 'B') NOT NULL,
    city           VARCHAR(50) NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,

    INDEX idx_order_date (order_date),
    INDEX idx_user_id (user_id),
    INDEX idx_ab_group (ab_group)
) ENGINE=InnoDB;

-- =============================================
-- 3. Таблица составов заказов (order_items)
-- =============================================
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id  INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT NOT NULL,
    item_name      VARCHAR(100),
    quantity       TINYINT UNSIGNED NOT NULL,
    price          DECIMAL(8,2) NOT NULL,

    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =============================================
-- 4. Таблица доставок
-- =============================================
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id    INT PRIMARY KEY,
    order_id       INT NOT NULL,
    delivery_date  DATETIME,
    delivery_time_minutes INT,
    status         ENUM('delivered', 'cancelled', 'delayed'),

    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =============================================
-- 5. Таблица событий в приложении (events)
-- =============================================
CREATE TABLE IF NOT EXISTS events (
    event_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    event_date     DATETIME NOT NULL,
    event_type     VARCHAR(50) NOT NULL,   -- open_app, add_to_cart, checkout и т.д.
    ab_group       ENUM('A', 'B'),

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_event_date (event_date),
    INDEX idx_event_type (event_type)
) ENGINE=InnoDB;

-- =============================================
-- 6. Таблица A/B групп (справочник)
-- =============================================
CREATE TABLE IF NOT EXISTS ab_groups (
    ab_group       ENUM('A', 'B') PRIMARY KEY,
    description    VARCHAR(200)
) ENGINE=InnoDB;

-- =============================================
-- 7. Таблица платежей
-- =============================================
CREATE TABLE IF NOT EXISTS payments (
    payment_id     INT PRIMARY KEY,
    order_id       INT NOT NULL,
    payment_date   DATETIME NOT NULL,
    amount         DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(30),

    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- =============================================
-- 8. Таблица промоакций (опционально, но полезно)
-- =============================================
CREATE TABLE IF NOT EXISTS promotions (
    promo_id       INT PRIMARY KEY,
    user_id        INT,
    order_id       INT,
    promo_code     VARCHAR(50),
    discount_amount DECIMAL(8,2),
    promo_date     DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
) ENGINE=InnoDB;

-- =============================================
-- Комментарии к таблицам
-- =============================================
ALTER TABLE users COMMENT = 'Пользователи приложения';
ALTER TABLE orders COMMENT = 'Основные заказы (Fact table)';
ALTER TABLE order_items COMMENT = 'Состав каждого заказа';
ALTER TABLE deliveries COMMENT = 'Информация о доставках';
ALTER TABLE events COMMENT = 'События в приложении (открытия, корзина и т.д.)';