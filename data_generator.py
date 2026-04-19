import pandas as pd
import numpy as np
import os
from datetime import timedelta

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================
np.random.seed(42)
NUM_USERS = 100_000
START_DATE = pd.to_datetime('2025-01-01')
END_DATE = pd.to_datetime('2025-03-31')

CITIES = ['Moscow', 'St. Petersburg', 'Kazan', 'Yekaterinburg', 'Novosibirsk']
MENU_ITEMS = [('Milk 1L', 90, 120), ('Bread', 50, 80), ('Eggs 10pcs', 100, 140), ('Bananas 1kg', 110, 150),
              ('Apples 1kg', 120, 180), ('Cheese 200g', 200, 350), ('Chicken 1kg', 350, 450),
              ('Water 1.5L', 40, 60), ('Coffee', 400, 700), ('Pizza', 250, 400)]

# Матрицы вероятностей (D1, D7, D14, D30, фоновые)
RETENTION_MATRIX = {
    1: {0: 0.15, 1: 0.60, 2: 0.70, 3: 0.80, 4: 0.90},
    7: {1: 0.30, 2: 0.25, 3: 0.30, 4: 0.50},
    14: {2: 0.40, 3: 0.40, 4: 0.50},
    30: {3: 0.45, 4: 0.50}
}
BG_PROBS = {1: 0.15, 2: 0.20, 3: 0.25, 4: 0.35}
MAX_LIFESPAN = {0: 1, 1: 7, 2: 14, 3: 30, 4: 90}


# ==========================================
# 2. ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ВОРОНКИ
# ==========================================
def generate_funnel(user_id, order_id, order_time, group, is_conv):
    """Сжатая версия генерации событий"""
    ts = order_time - timedelta(minutes=np.random.randint(5, 30))
    events = [(user_id, ts, 'app_open', group)]

    for _ in range(np.random.randint(1, 4)):
        ts += timedelta(seconds=np.random.randint(30, 120))
        events.append((user_id, ts, 'product_view', group))

    if not is_conv and np.random.rand() < 0.7: return events
    ts += timedelta(seconds=np.random.randint(20, 90))
    events.append((user_id, ts, 'add_to_cart', group))

    if not is_conv: return events
    events.extend([(user_id, ts + timedelta(seconds=30), 'checkout', group),
                   (user_id, order_time, 'order_placed', group)])
    return events


# ==========================================
# 3. ОСНОВНОЙ ГЕНЕРАТОР
# ==========================================
print("Начинаем быструю генерацию данных...")
data = {k: [] for k in ['users', 'orders', 'items', 'deliveries', 'payments', 'promos', 'events']}
counters = {'order': 1, 'payment': 1, 'delivery': 1, 'promo': 1}

for uid in range(1, NUM_USERS + 1):
    # 1. Профиль юзера
    reg_date = START_DATE + timedelta(days=np.random.randint(0, (END_DATE - START_DATE).days))
    city = np.random.choice(CITIES, p=[0.4, 0.25, 0.15, 0.1, 0.1])
    ab = np.random.choice(['A', 'B'])

    data['users'].append((uid, reg_date, city, np.random.randint(18, 65), np.random.choice(['M', 'F']),
                          np.random.choice(['iOS', 'Android', 'Web'], p=[0.45, 0.5, 0.05]),
                          np.random.choice(['Organic', 'Paid_Ads', 'Referral', 'Influencer'], p=[0.3, 0.45, 0.15, 0.1]),
                          ab))
    data['events'].append((uid, reg_date, 'registration', ab))

    # 2. Жизненный цикл (Определяем активные дни сразу!)
    seg = np.random.choice([0, 1, 2, 3, 4], p=[0.40, 0.15, 0.10, 0.15, 0.20])
    max_d = min(MAX_LIFESPAN[seg], (END_DATE - reg_date).days)

    active_days = [0]  # В день регистрации заходят все
    for day in range(1, max_d + 1):
        prob = RETENTION_MATRIX.get(day, {}).get(seg, BG_PROBS.get(seg, 0))
        if ab == 'B': prob = min(1.0, prob + 0.05)  # Лифт группы B
        if np.random.rand() < prob:
            active_days.append(day)

    # 3. Сессии и заказы
    for d_offset in active_days:
        session_ts = reg_date + timedelta(days=d_offset, hours=np.random.randint(7, 22))

        # Конверсия: D0 = 70%, остальные = 28% (повысил для честных 2.5-3 заказов)
        order_prob = 0.70 if d_offset == 0 else 0.28
        if ab == 'B': order_prob *= 1.1

        is_conv = np.random.rand() < order_prob
        data['events'].extend(generate_funnel(uid, counters['order'] if is_conv else None, session_ts, ab, is_conv))

        if is_conv:
            order_total = 0
            # Корзина
            for _ in range(np.random.choice([1, 2, 3, 4, 5], p=[0.25, 0.3, 0.25, 0.15, 0.05])):
                item = MENU_ITEMS[np.random.randint(0, len(MENU_ITEMS))]
                qty, price = np.random.choice([1, 2, 3], p=[0.75, 0.2, 0.05]), np.random.randint(item[1], item[2])
                order_total += price * qty
                data['items'].append((counters['order'], item[0], qty, price))

            data['orders'].append((counters['order'], uid, session_ts, order_total, ab, city))
            data['payments'].append(
                (counters['payment'], counters['order'], session_ts + timedelta(seconds=15), order_total,
                 np.random.choice(['Card', 'SBP'])))

            # Доставка
            status = np.random.choice(['delivered', 'delayed', 'cancelled'], p=[0.92, 0.05, 0.03])
            data['deliveries'].append(
                (counters['delivery'], counters['order'], session_ts + timedelta(minutes=30), 30, status))

            # Промокод (20%)
            if np.random.rand() < 0.20:
                data['promos'].append(
                    (counters['promo'], uid, counters['order'], 'PROMO20', order_total * 0.2, session_ts))
                counters['promo'] += 1

            counters['order'] += 1;
            counters['payment'] += 1;
            counters['delivery'] += 1

    if uid % 25_000 == 0: print(f"Обработано {uid} / {NUM_USERS}...")

# ==========================================
# 4. СОХРАНЕНИЕ И ОТЧЕТ
# ==========================================
os.makedirs('data', exist_ok=True)
dfs = {
    'users': pd.DataFrame(data['users'], columns=['user_id', 'registration_date', 'city', 'age', 'gender', 'device',
                                                  'acquisition_channel', 'ab_group']),
    'orders': pd.DataFrame(data['orders'],
                           columns=['order_id', 'user_id', 'order_time', 'order_amount', 'ab_group', 'city']),
    'order_items': pd.DataFrame(data['items'], columns=['order_id', 'item_name', 'quantity', 'price']),
    'deliveries': pd.DataFrame(data['deliveries'],
                               columns=['delivery_id', 'order_id', 'delivery_time', 'delivery_time_minutes', 'status']),
    'payments': pd.DataFrame(data['payments'],
                             columns=['payment_id', 'order_id', 'payment_date', 'amount', 'payment_method']),
    'promotions': pd.DataFrame(data['promos'],
                               columns=['promo_id', 'user_id', 'order_id', 'promo_code', 'discount_amount',
                                        'promo_date']),
    'events': pd.DataFrame(data['events'], columns=['user_id', 'event_time', 'event_type', 'ab_group'])
}
dfs['events'].insert(0, 'event_id', range(1, len(dfs['events']) + 1))

for name, df in dfs.items():
    df.to_csv(f'data/{name}.csv', index=False)

print("\n=== Итоговые метрики ===")
print(f"Пользователей: {len(dfs['users'])} | Заказов: {len(dfs['orders'])}")
print(f"Ср. заказов на юзера: {len(dfs['orders']) / NUM_USERS:.2f}")

events_df, users_df = dfs['events'], dfs['users']
opens = events_df[events_df['event_type'] == 'app_open'].merge(users_df[['user_id', 'registration_date']], on='user_id')
opens['day'] = (opens['event_time'] - opens['registration_date']).dt.days

for d in [1, 7, 14, 30]:
    alive = len(users_df[(END_DATE - users_df['registration_date']).dt.days >= d])
    active = opens[opens['day'] == d]['user_id'].nunique()
    print(f"D{d} Retention: ~{(active / alive * 100) if alive else 0:.1f}%")