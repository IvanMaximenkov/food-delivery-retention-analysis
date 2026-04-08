import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ====================== НАСТРОЙКИ ======================
NUM_USERS = 100_000
NUM_ORDERS = 220_000
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 3, 31)

np.random.seed(42)
random.seed(42)

print(f"Параметры: {NUM_USERS:,} пользователей, {NUM_ORDERS:,} заказов\n")


def generate_users():
    user_ids = np.arange(1, NUM_USERS + 1)

    # Даты регистрации (больше в начале)
    days = (END_DATE - START_DATE).days
    registration_dates = START_DATE + pd.to_timedelta(
        np.random.exponential(scale=days / 3, size=NUM_USERS).astype(int), unit='D'
    )
    registration_dates = np.clip(registration_dates, START_DATE, END_DATE)

    cities = ['Москва', 'Санкт-Петербург', 'Екатеринбург', 'Новосибирск',
              'Казань', 'Краснодар', 'Нижний Новгород', 'Челябинск']

    data = {
        'user_id': user_ids,
        'registration_date': registration_dates,
        'city': np.random.choice(cities, NUM_USERS, p=[0.35, 0.20, 0.10, 0.08, 0.07, 0.08, 0.06, 0.06]),
        'age': np.random.normal(32, 8, NUM_USERS).astype(int).clip(18, 65),
        'gender': np.random.choice(['male', 'female', 'other'], NUM_USERS, p=[0.48, 0.48, 0.04]),
        'device': np.random.choice(['android', 'ios'], NUM_USERS, p=[0.65, 0.35]),
        'acquisition_channel': np.random.choice(
            ['organic', 'google_ads', 'yandex_direct', 'referral', 'app_store', 'vk_ads'],
            NUM_USERS, p=[0.35, 0.25, 0.20, 0.10, 0.07, 0.03]
        ),
        'ab_group': np.random.choice(['A', 'B'], NUM_USERS, p=[0.5, 0.5])
    }

    users = pd.DataFrame(data)
    print(f"Создано пользователей: {len(users):,}")
    return users


def generate_orders(users):

    target_avg_orders = NUM_ORDERS / len(users)

    orders_list = []
    order_id = 1

    for i, user in users.iterrows():
        num_orders = int(np.random.poisson(lam=target_avg_orders))
        num_orders = np.clip(num_orders, 0, 15)

        if num_orders == 0:
            continue

        user_reg = user['registration_date']
        max_days = (END_DATE - user_reg).days
        if max_days <= 0:
            continue

        order_dates = user_reg + pd.to_timedelta(
            np.random.randint(0, max_days + 1, num_orders), unit='D'
        )

        for d in order_dates:
            if user['ab_group'] == 'B':
                amount = round(np.random.lognormal(6.9, 0.55), 2)
            else:
                amount = round(np.random.lognormal(6.4, 0.65), 2)

            orders_list.append({
                'order_id': order_id,
                'user_id': user['user_id'],
                'order_date': d,
                'order_amount': amount,
                'ab_group': user['ab_group'],
                'city': user['city']
            })
            order_id += 1

    orders = pd.DataFrame(orders_list)
    print(f"Создано заказов: {len(orders):,}")
    return orders

if __name__ == "__main__":
    users = generate_users()
    orders = generate_orders(users)

    os.makedirs('data', exist_ok=True)

    users.to_csv('data/users.csv', index=False)
    orders.to_csv('data/orders.csv', index=False)

    print("\n Генерация завершена")