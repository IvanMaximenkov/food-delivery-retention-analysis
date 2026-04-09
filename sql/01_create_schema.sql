-- Создание схемы базы данных

CREATE DATABASE IF NOT EXISTS food_delivery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_delivery;

-- Справочник пользователей (Dimension)
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

-- Таблица заказов
CREATE TABLE IF NOT EXISTS orders (
    order_id       INT PRIMARY KEY,
    user_id        INT NOT NULL,
    order_date     DATETIME NOT NULL,
    order_amount   DECIMAL(10,2) NOT NULL,
    ab_group       ENUM('A', 'B') NOT NULL,
    city           VARCHAR(50) NOT NULL,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,

    INDEX idx_order_date (order_date),
    INDEX idx_user_id (user_id),
    INDEX idx_ab_group (ab_group)
) ENGINE=InnoDB;

-- Состав заказов (Bridge / Fact)
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id  INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT NOT NULL,
    item_name      VARCHAR(100) NOT NULL,
    quantity       TINYINT UNSIGNED NOT NULL,
    price          DECIMAL(8,2) NOT NULL,

    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Доставки
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id    INT PRIMARY KEY,
    order_id       INT NOT NULL,
    delivery_date  DATETIME,
    delivery_time_minutes INT,
    status         ENUM('delivered', 'cancelled', 'delayed'),

    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Лог событий в приложении
CREATE TABLE IF NOT EXISTS events (
    event_id       BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    event_date     DATETIME NOT NULL,
    event_type     VARCHAR(50) NOT NULL,
    ab_group       ENUM('A', 'B'),

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    
    INDEX idx_event_date (event_date),
    INDEX idx_event_type (event_type)
) ENGINE=InnoDB;

-- Платежи
CREATE TABLE IF NOT EXISTS payments (
    payment_id     INT PRIMARY KEY,
    order_id       INT NOT NULL,
    payment_date   DATETIME NOT NULL,
    amount         DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(30),

    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Промоакции
CREATE TABLE IF NOT EXISTS promotions (
    promo_id       INT PRIMARY KEY,
    user_id        INT,
    order_id       INT,
    promo_code     VARCHAR(50),
    discount_amount DECIMAL(8,2),
    promo_date     DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE RESTRICT
) ENGINE=InnoDB;