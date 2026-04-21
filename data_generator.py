from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


CITIES = ["Moscow", "Saint-Petersburg", "Kazan", "Novosibirsk", "Yekaterinburg"]
CITY_WEIGHTS = np.array([0.48, 0.2, 0.12, 0.1, 0.1])
ACQUISITION_CHANNELS = ["organic", "paid_search", "social_ads", "referral", "affiliate"]
CHANNEL_WEIGHTS = np.array([0.33, 0.22, 0.2, 0.18, 0.07])
DEVICE_OS = ["iOS", "Android"]
CUISINES = [
    "Burgers",
    "Sushi",
    "Pizza",
    "Healthy",
    "Georgian",
    "Asian",
    "Desserts",
    "Coffee",
    "Russian",
]
LOYALTY_TIERS = ["new", "silver", "gold", "platinum"]
LOYALTY_WEIGHTS = np.array([0.57, 0.26, 0.13, 0.04])
PAYMENT_METHODS = ["card", "sbp", "apple_pay", "google_pay"]
SESSION_SOURCES = ["push", "organic", "paid", "email", "direct"]
COURIER_TYPES = ["bike", "car", "foot"]
SHIFT_TYPES = ["day", "evening", "night"]
ITEM_CATEGORIES = ["main", "snack", "drink", "dessert"]


@dataclass
class GeneratorConfig:
    n_users: int = 14_000
    n_restaurants: int = 260
    n_couriers: int = 1_100
    start_date: str = "2025-01-01"
    end_date: str = "2026-03-31"
    seed: int = 42
    output_dir: Path = Path("data")


def _random_timestamps(
    rng: np.random.Generator, n: int, start: pd.Timestamp, end: pd.Timestamp
) -> pd.Series:
    start_ns = start.value
    end_ns = end.value
    random_ns = rng.integers(start_ns, end_ns, size=n)
    return pd.to_datetime(random_ns)


def generate_users(cfg: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    start = pd.Timestamp(cfg.start_date)
    end = pd.Timestamp(cfg.end_date) - pd.Timedelta(days=45)
    reg_ts = _random_timestamps(rng, cfg.n_users, start, end)

    users = pd.DataFrame(
        {
            "user_id": np.arange(1, cfg.n_users + 1, dtype=int),
            "registration_ts": reg_ts,
            "acquisition_channel": rng.choice(
                ACQUISITION_CHANNELS, size=cfg.n_users, p=CHANNEL_WEIGHTS
            ),
            "city": rng.choice(CITIES, size=cfg.n_users, p=CITY_WEIGHTS),
            "device_os": rng.choice(DEVICE_OS, size=cfg.n_users, p=[0.46, 0.54]),
            "age": np.clip(rng.normal(loc=31, scale=8, size=cfg.n_users).round(), 18, 60).astype(
                int
            ),
            "gender": rng.choice(["female", "male"], size=cfg.n_users, p=[0.52, 0.48]),
            "loyalty_tier": rng.choice(LOYALTY_TIERS, size=cfg.n_users, p=LOYALTY_WEIGHTS),
        }
    )

    return users.sort_values("registration_ts").reset_index(drop=True)


def generate_restaurants(cfg: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    cities = rng.choice(CITIES, size=cfg.n_restaurants, p=CITY_WEIGHTS)
    cuisines = rng.choice(CUISINES, size=cfg.n_restaurants)
    ratings = np.clip(rng.normal(loc=4.35, scale=0.28, size=cfg.n_restaurants), 3.2, 5.0)

    restaurants = pd.DataFrame(
        {
            "restaurant_id": np.arange(1, cfg.n_restaurants + 1, dtype=int),
            "restaurant_name": [f"{cuisine} Place {idx:03d}" for idx, cuisine in enumerate(cuisines, 1)],
            "cuisine_type": cuisines,
            "city": cities,
            "average_prep_minutes": np.clip(
                rng.normal(loc=24, scale=5, size=cfg.n_restaurants).round(), 12, 45
            ).astype(int),
            "rating": ratings.round(2),
        }
    )

    return restaurants


def generate_couriers(cfg: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    hire_start = pd.Timestamp(cfg.start_date) - pd.Timedelta(days=365)
    hire_end = pd.Timestamp(cfg.end_date)
    hire_dates = _random_timestamps(rng, cfg.n_couriers, hire_start, hire_end).date

    couriers = pd.DataFrame(
        {
            "courier_id": np.arange(1, cfg.n_couriers + 1, dtype=int),
            "city": rng.choice(CITIES, size=cfg.n_couriers, p=CITY_WEIGHTS),
            "courier_type": rng.choice(COURIER_TYPES, size=cfg.n_couriers, p=[0.62, 0.28, 0.1]),
            "shift_type": rng.choice(SHIFT_TYPES, size=cfg.n_couriers, p=[0.53, 0.34, 0.13]),
            "hire_date": hire_dates,
            "avg_speed_kmh": np.clip(rng.normal(loc=17, scale=3.2, size=cfg.n_couriers), 8, 30).round(1),
            "on_time_rate": np.clip(rng.normal(loc=0.91, scale=0.05, size=cfg.n_couriers), 0.65, 0.99).round(
                3
            ),
        }
    )

    return couriers


def generate_campaigns(cfg: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    start = pd.Timestamp(cfg.start_date)
    end = pd.Timestamp(cfg.end_date)
    month_starts = pd.date_range(start=start, end=end, freq="MS")

    rows = []
    campaign_types = ["free_delivery", "percent_discount", "combo_offer", "reactivation"]
    for campaign_id, month_start in enumerate(month_starts, start=1):
        launch = month_start + pd.Timedelta(days=int(rng.integers(1, 12)))
        duration = int(rng.integers(6, 14))
        campaign_end = min(launch + pd.Timedelta(days=duration), end)
        campaign_type = rng.choice(campaign_types, p=[0.3, 0.4, 0.2, 0.1])
        rows.append(
            {
                "campaign_id": campaign_id,
                "campaign_name": f"{campaign_type}_{launch.strftime('%Y_%m')}",
                "start_date": launch.date(),
                "end_date": campaign_end.date(),
                "discount_pct": int(rng.integers(8, 30)),
                "min_basket_rub": int(rng.integers(500, 1500)),
                "campaign_type": campaign_type,
            }
        )

    return pd.DataFrame(rows)


def generate_ab_assignments(users: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    test_start = pd.Timestamp("2025-09-01")
    eligible = users.loc[users["registration_ts"] >= test_start].copy()
    eligible["variant"] = rng.choice(["control", "treatment"], size=len(eligible), p=[0.5, 0.5])
    eligible["assigned_at"] = eligible["registration_ts"] + pd.to_timedelta(
        rng.integers(0, 3, size=len(eligible)), unit="D"
    )
    eligible["test_id"] = "free_delivery_banner_v1"
    eligible["exposure_channel"] = rng.choice(["home_feed", "push", "search"], size=len(eligible), p=[0.6, 0.2, 0.2])
    eligible = eligible.sort_values("user_id")
    eligible["assignment_id"] = np.arange(1, len(eligible) + 1, dtype=int)

    return eligible[
        ["assignment_id", "user_id", "test_id", "variant", "assigned_at", "exposure_channel"]
    ].reset_index(drop=True)


def generate_orders(
    users: pd.DataFrame,
    restaurants: pd.DataFrame,
    couriers: pd.DataFrame,
    campaigns: pd.DataFrame,
    ab_assignments: pd.DataFrame,
    cfg: GeneratorConfig,
    rng: np.random.Generator,
) -> pd.DataFrame:
    end_ts = pd.Timestamp(cfg.end_date) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    restaurants_by_city: Dict[str, np.ndarray] = {
        city: restaurants.loc[restaurants["city"] == city, "restaurant_id"].to_numpy()
        for city in CITIES
    }
    couriers_by_city: Dict[str, np.ndarray] = {
        city: couriers.loc[couriers["city"] == city, "courier_id"].to_numpy() for city in CITIES
    }

    assignment_map = ab_assignments.set_index("user_id")[["variant", "assigned_at"]].to_dict("index")
    campaign_frame = campaigns.copy()
    campaign_frame["start_date"] = pd.to_datetime(campaign_frame["start_date"])
    campaign_frame["end_date"] = pd.to_datetime(campaign_frame["end_date"])
    restaurant_prep_map = restaurants.set_index("restaurant_id")["average_prep_minutes"].to_dict()

    orders_rows = []
    order_id = 1

    for user in users.itertuples(index=False):
        reg_ts = pd.Timestamp(user.registration_ts)
        city = user.city
        loyalty_tier = user.loyalty_tier
        acquisition_channel = user.acquisition_channel
        loyalty_bonus = {"new": 0.0, "silver": 0.05, "gold": 0.12, "platinum": 0.19}[loyalty_tier]
        channel_bonus = {
            "organic": 0.08,
            "referral": 0.06,
            "paid_search": 0.03,
            "social_ads": -0.01,
            "affiliate": -0.04,
        }[acquisition_channel]

        p_first_order = np.clip(0.67 + loyalty_bonus + channel_bonus, 0.25, 0.93)
        if rng.random() > p_first_order:
            continue

        first_gap_days = int(rng.integers(0, 9))
        current_ts = reg_ts + pd.Timedelta(days=first_gap_days) + pd.Timedelta(
            minutes=int(rng.integers(600, 1320))
        )
        if current_ts > end_ts:
            continue

        user_assignment = assignment_map.get(user.user_id)
        variant = user_assignment["variant"] if user_assignment else "na"
        assigned_at = pd.Timestamp(user_assignment["assigned_at"]) if user_assignment else pd.Timestamp.max
        user_order_number = 0
        max_orders_per_user = int(np.clip(rng.poisson(3.8) + 1, 1, 12))

        while current_ts <= end_ts and user_order_number < max_orders_per_user:
            user_order_number += 1
            city_restaurants = restaurants_by_city.get(city)
            city_couriers = couriers_by_city.get(city)
            if city_restaurants is None or len(city_restaurants) == 0:
                break
            if city_couriers is None or len(city_couriers) == 0:
                break

            restaurant_id = int(rng.choice(city_restaurants))
            courier_id = int(rng.choice(city_couriers))
            is_express = int(rng.random() < 0.18)
            distance_km = float(np.clip(rng.gamma(shape=2.8, scale=1.4), 0.4, 16.0))

            basket_base = 700 + 180 * loyalty_bonus + 40 * (user_order_number > 1)
            basket_value = float(np.clip(rng.normal(loc=basket_base, scale=185), 220, 3800))
            delivery_fee = float(np.clip(49 + distance_km * 10 + is_express * 85, 0, 290))
            discount = 0.0
            campaign_id = pd.NA

            current_date = current_ts.normalize()
            active_campaigns = campaign_frame.loc[
                (campaign_frame["start_date"] <= current_date) & (campaign_frame["end_date"] >= current_date)
            ]
            if len(active_campaigns) > 0 and rng.random() < 0.34:
                selected_campaign = active_campaigns.sample(n=1, random_state=int(rng.integers(1, 1_000_000))).iloc[0]
                campaign_id = int(selected_campaign["campaign_id"])
                if basket_value >= float(selected_campaign["min_basket_rub"]):
                    discount = basket_value * (float(selected_campaign["discount_pct"]) / 100.0)

            if variant == "treatment" and current_ts >= assigned_at and user_order_number <= 3:
                delivery_fee = 0.0

            prep_minutes = restaurant_prep_map[restaurant_id]
            status = "delivered" if rng.random() < 0.95 else "cancelled"
            if status == "delivered":
                delivery_minutes = int(
                    np.clip(rng.normal(loc=prep_minutes + 7 + distance_km * 3.2, scale=8), 12, 95)
                )
                gross_margin = float(
                    np.clip(basket_value * 0.28 + delivery_fee - discount - distance_km * 9.0, -200, 1500)
                )
            else:
                delivery_minutes = int(np.clip(rng.normal(loc=max(prep_minutes * 0.55, 7), scale=5), 5, 45))
                sunk_cost = basket_value * rng.uniform(0.04, 0.11) + distance_km * rng.uniform(2.0, 5.0)
                gross_margin = -float(np.clip(sunk_cost, 20, 260))

            orders_rows.append(
                {
                    "order_id": order_id,
                    "user_id": int(user.user_id),
                    "restaurant_id": restaurant_id,
                    "courier_id": courier_id,
                    "campaign_id": campaign_id,
                    "order_ts": current_ts,
                    "order_status": status,
                    "delivery_minutes": delivery_minutes,
                    "basket_value_rub": round(basket_value, 2),
                    "delivery_fee_rub": round(delivery_fee, 2),
                    "discount_rub": round(discount, 2),
                    "payment_method": rng.choice(PAYMENT_METHODS, p=[0.65, 0.17, 0.09, 0.09]),
                    "distance_km": round(distance_km, 2),
                    "is_express": is_express,
                    "gross_margin_rub": round(gross_margin, 2),
                }
            )

            order_id += 1

            churn_pressure = 0.22 + 0.04 * user_order_number - loyalty_bonus - max(channel_bonus, -0.02)
            variant_bonus = 0.05 if variant == "treatment" and current_ts >= assigned_at else 0.0
            continue_probability = float(np.clip(0.77 - churn_pressure + variant_bonus, 0.06, 0.88))
            if rng.random() > continue_probability:
                break

            gap_days = int(np.clip(rng.gamma(shape=2.2, scale=3.4), 1, 35))
            if user_order_number > 1:
                gap_days += int(rng.integers(0, 7))
            current_ts = current_ts + pd.Timedelta(days=gap_days) + pd.Timedelta(
                minutes=int(rng.integers(-120, 210))
            )

    orders = pd.DataFrame(orders_rows)
    if not orders.empty:
        orders["campaign_id"] = orders["campaign_id"].astype("Int64")
        orders = orders.sort_values("order_ts").reset_index(drop=True)

    return orders


def _split_amount_in_cents(total_cents: int, n_parts: int, rng: np.random.Generator) -> np.ndarray:
    if n_parts == 1:
        return np.array([total_cents], dtype=int)

    weights = rng.dirichlet(np.full(n_parts, 1.6))
    cents = np.floor(total_cents * weights).astype(int)
    remainder = total_cents - int(cents.sum())
    if remainder > 0:
        top_up_idx = rng.choice(n_parts, size=remainder, replace=True)
        np.add.at(cents, top_up_idx, 1)
    return cents


def generate_order_items(orders: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    items_catalog = {
        "main": ["Burger", "Ramen", "Pizza slice", "Wok", "Khachapuri"],
        "snack": ["Fries", "Nuggets", "Salad", "Rolls"],
        "drink": ["Cola", "Lemonade", "Coffee", "Mineral water"],
        "dessert": ["Cheesecake", "Brownie", "Ice cream", "Donut"],
    }
    line_floor_cents = 4_500
    cogs_ratio_ranges = {
        "main": (0.42, 0.6),
        "snack": (0.35, 0.54),
        "drink": (0.22, 0.42),
        "dessert": (0.28, 0.48),
    }

    rows = []
    order_item_id = 1
    for order in orders.itertuples(index=False):
        if order.order_status != "delivered":
            continue

        basket_cents = int(round(float(order.basket_value_rub) * 100))
        max_items = int(np.clip(basket_cents // line_floor_cents, 1, 8))
        n_items = int(np.clip(rng.poisson(2.6) + 1, 1, max_items))
        base_cents = np.full(n_items, line_floor_cents, dtype=int)
        residual_cents = basket_cents - int(base_cents.sum())
        allocated_cents = base_cents + _split_amount_in_cents(residual_cents, n_items, rng)

        for line_cents in allocated_cents:
            category = rng.choice(ITEM_CATEGORIES, p=[0.43, 0.2, 0.22, 0.15])
            item_name = rng.choice(items_catalog[category])
            quantity = 1
            unit_price = line_cents / 100.0
            cogs_low, cogs_high = cogs_ratio_ranges[category]
            cogs = unit_price * rng.uniform(cogs_low, cogs_high)
            rows.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": int(order.order_id),
                    "item_name": item_name,
                    "item_category": category,
                    "quantity": quantity,
                    "unit_price_rub": round(unit_price, 2),
                    "cogs_rub": round(cogs, 2),
                }
            )
            order_item_id += 1

    return pd.DataFrame(rows)


def generate_sessions(users: pd.DataFrame, orders: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    if orders.empty:
        return pd.DataFrame(
            columns=[
                "session_id",
                "user_id",
                "session_start_ts",
                "session_end_ts",
                "session_source",
                "city",
                "device_os",
                "is_push_opened",
                "did_order",
            ]
        )

    user_lookup = users.set_index("user_id")[["city", "device_os", "registration_ts"]]
    order_counts = orders.groupby("user_id")["order_id"].count().rename("orders_cnt")

    rows = []
    session_id = 1

    for order in orders.itertuples(index=False):
        if order.order_status != "delivered":
            continue
        user_info = user_lookup.loc[order.user_id]
        duration_min = int(np.clip(rng.normal(loc=16, scale=7), 3, 65))
        start_ts = pd.Timestamp(order.order_ts) - pd.Timedelta(minutes=duration_min)
        end_ts = pd.Timestamp(order.order_ts)
        rows.append(
            {
                "session_id": session_id,
                "user_id": int(order.user_id),
                "session_start_ts": start_ts,
                "session_end_ts": end_ts,
                "session_source": rng.choice(SESSION_SOURCES, p=[0.28, 0.31, 0.2, 0.09, 0.12]),
                "city": user_info["city"],
                "device_os": user_info["device_os"],
                "is_push_opened": int(rng.random() < 0.37),
                "did_order": 1,
            }
        )
        session_id += 1

    for user in users.itertuples(index=False):
        user_orders = int(order_counts.get(user.user_id, 0))
        extra_sessions = int(np.clip(rng.poisson(4 + user_orders * 0.8), 1, 28))
        first_ts = pd.Timestamp(user.registration_ts)
        last_ts = pd.Timestamp(orders["order_ts"].max()) + pd.Timedelta(days=1)
        if first_ts >= last_ts:
            continue
        for _ in range(extra_sessions):
            start_ts = _random_timestamps(rng, 1, first_ts, last_ts)[0]
            duration_min = int(np.clip(rng.normal(loc=8, scale=4), 1, 40))
            rows.append(
                {
                    "session_id": session_id,
                    "user_id": int(user.user_id),
                    "session_start_ts": start_ts,
                    "session_end_ts": start_ts + pd.Timedelta(minutes=duration_min),
                    "session_source": rng.choice(SESSION_SOURCES, p=[0.22, 0.34, 0.2, 0.09, 0.15]),
                    "city": user.city,
                    "device_os": user.device_os,
                    "is_push_opened": int(rng.random() < 0.32),
                    "did_order": 0,
                }
            )
            session_id += 1

    sessions = pd.DataFrame(rows).sort_values("session_start_ts").reset_index(drop=True)
    return sessions


def save_tables(tables: Dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        path = output_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        print(f"Saved {name:<26} -> {path} ({len(frame):>7} rows)")


def build_star_schema(cfg: GeneratorConfig) -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(cfg.seed)

    users = generate_users(cfg, rng)
    restaurants = generate_restaurants(cfg, rng)
    couriers = generate_couriers(cfg, rng)
    campaigns = generate_campaigns(cfg, rng)
    ab_assignments = generate_ab_assignments(users, rng)
    orders = generate_orders(users, restaurants, couriers, campaigns, ab_assignments, cfg, rng)
    order_items = generate_order_items(orders, rng)
    sessions = generate_sessions(users, orders, rng)

    tables = {
        "dim_users": users,
        "dim_restaurants": restaurants,
        "dim_couriers": couriers,
        "dim_promo_campaigns": campaigns,
        "fact_orders": orders,
        "fact_order_items": order_items,
        "fact_app_sessions": sessions,
        "fact_ab_test_assignments": ab_assignments,
    }
    return tables


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic food-delivery analytics dataset.")
    parser.add_argument("--n-users", type=int, default=GeneratorConfig.n_users)
    parser.add_argument("--n-restaurants", type=int, default=GeneratorConfig.n_restaurants)
    parser.add_argument("--n-couriers", type=int, default=GeneratorConfig.n_couriers)
    parser.add_argument("--start-date", type=str, default=GeneratorConfig.start_date)
    parser.add_argument("--end-date", type=str, default=GeneratorConfig.end_date)
    parser.add_argument("--seed", type=int, default=GeneratorConfig.seed)
    parser.add_argument("--output-dir", type=Path, default=GeneratorConfig.output_dir)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = GeneratorConfig(
        n_users=args.n_users,
        n_restaurants=args.n_restaurants,
        n_couriers=args.n_couriers,
        start_date=args.start_date,
        end_date=args.end_date,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    print("Generating synthetic star schema tables...")
    tables = build_star_schema(cfg)
    save_tables(tables, cfg.output_dir)
    print("Done.")


if __name__ == "__main__":
    main()
