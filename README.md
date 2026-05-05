# Food Delivery Retention & Churn Analysis

Проект по продуктовой аналитике, retention, A/B testing и прогнозированию churn для сервиса доставки еды. Полный цикл работы продуктового аналитика / junior data scientist: от генерации данных и SQL-модели до EDA, когортного анализа, RFM-сегментации, ML-модели оттока и продуктовых рекомендаций.

Все данные в проекте синтетические

## Цель проекта

Главная задача: понять, как пользователи возвращаются после первого заказа, какие сегменты требуют разной коммуникации, какие продуктовые гипотезы помогают удержанию и как заранее находить пользователей с высоким риском оттока.

В проекте решены следующие задачи:

- построена синтетическая star schema для food delivery-аналитики;
- подготовлены SQL-скрипты для MySQL 8.0+;
- проведен EDA по пользователям, заказам и сессиям;
- рассчитан repeat order retention по окнам 7/14/30 дней;
- выполнена RFM-сегментация клиентской базы;
- проанализирован A/B-тест `free_delivery_banner_v1`;
- построена ML-модель churn prediction;
- сохранены модель и feature importance;
- сформулированы итоговые бизнес-выводы и рекомендации.

## Итоговые результаты

### Данные

| Сущность | Объем |
|---|---:|
| Пользователи | 14 000 |
| Заказы всего | 21 976 |
| Доставленные заказы | 20 848 |
| Доля доставленных заказов | 94.9% |
| Сессии приложения | 94 745 |
| Рестораны | 260 |
| Курьеры | 1 100 |
| Промокампании | 15 |
| Период заказов | 2025-01-02 - 2026-03-31 |

### Product KPI

| Метрика | Значение |
|---|---:|
| GMV | 16.8 млн RUB |
| Gross margin | 5.1 млн RUB |
| Средний DAU | 204 пользователя |
| Пользователи без заказа 28+ дней | 10 098 |
| Repeat order rate 30D | 57.3% |

### Retention

Основная метрика удержания для проекта - доля пользователей, сделавших хотя бы один повторный доставленный заказ после первого заказа.

| Окно после первого заказа | База пользователей | Повторили заказ | Repeat rate |
|---|---:|---:|---:|
| 7 дней | 10 193 | 3 503 | 34.4% |
| 14 дней | 10 193 | 5 285 | 51.8% |
| 30 дней | 10 192 | 5 840 | 57.3% |

Вывод: ключевое окно влияния на удержание - первые 7-14 дней. За 30 дней повторный заказ делает больше половины eligible-пользователей, но заметная часть аудитории все еще не формирует привычку ко второму заказу.

### RFM-сегментация

| Сегмент | Пользователи | Средний monetary, RUB |
|---|---:|---:|
| Core Users | 1 534 | 2 603 |
| High Value at Risk | 1 483 | 2 251 |
| Active Loyal | 1 052 | 1 354 |
| Growth Potential | 4 387 | 1 182 |
| Dormant | 1 737 | 710 |

Вывод: наиболее ценный сегмент для CRM-активации - `High Value at Risk`: пользователи с высокой исторической ценностью, но ухудшившейся свежестью активности. Для `Growth Potential` логичнее развивать повторные сценарии и персональные предложения, а не давать одинаковые скидки всей базе.

### A/B-тест

Тест: `free_delivery_banner_v1`  
Основная метрика: 7-day conversion to delivered order.

| Вариант | Пользователи | Конверсии | Conversion |
|---|---:|---:|---:|
| control | 2 857 | 1 697 | 59.4% |
| treatment | 2 792 | 1 626 | 58.2% |

| Метрика | Значение |
|---|---:|
| Uplift | -1.16 pp |
| z-stat | -0.89 |
| p-value | 0.376 |
| Оценка эффекта gross margin за 30 дней | -14.4 тыс. RUB |

Вывод: treatment не показал статистически значимого улучшения. На текущих данных баннер бесплатной доставки не стоит раскатывать на всю базу. Следующий шаг - переупаковать механику: тестировать не общий баннер, а таргетированное предложение для новых пользователей без второго заказа или для сегмента `High Value at Risk`.

### Churn prediction

Модель прогнозирует вероятность отсутствия заказа в следующие 30 дней. Для обучения используется user-level dataset с признаками заказов, сессий, скидок, давности активности, acquisition channel, города, loyalty tier и участия в A/B-тесте.

| Метрика | Значение |
|---|---:|
| Modeling cohort | 677 пользователей |
| Churn label share | 83.3% |
| ROC-AUC | 0.723 |
| PR-AUC | 0.922 |
| F1 | 0.744 |
| Precision | 0.946 |
| Recall | 0.613 |
| Рабочий threshold | 0.968 |

Топ факторов модели:

1. `days_since_last_order`
2. `city_Yekaterinburg`
3. `is_treatment`
4. `avg_discount_rub`
5. `acquisition_channel_social_ads`
6. `city_Kazan`
7. `engagement_ratio`
8. `acquisition_channel_affiliate`
9. `days_since_last_session`
10. `acquisition_channel_paid_search`

Вывод: главный сигнал churn - давность последнего заказа и последней сессии. Модель уже можно использовать как основу для CRM-скоринга, но перед production-применением нужно валидировать ее на новых периодах и доработать стратегию под разные сегменты.

## Рекомендации

1. Сфокусировать retention-механику на первых 7-14 днях после первого заказа: onboarding, push/email-триггеры, персональный повод ко второму заказу.
2. Не масштабировать `free_delivery_banner_v1` в текущем виде: эффект отрицательный и статистически не подтвержден.
3. Разделить CRM по сегментам RFM:
   - `Core Users`: удерживать качеством сервиса и loyalty benefits;
   - `High Value at Risk`: запускать реактивационные офферы и персональные промо;
   - `Growth Potential`: стимулировать второй и третий заказ;
   - `Dormant`: ограничивать дорогие скидки и тестировать дешевые каналы возврата.
4. Использовать churn score для приоритизации кампаний: таргетировать пользователей с высоким риском и достаточной исторической маржинальностью.
5. Отслеживать не только conversion uplift, но и gross margin uplift, чтобы скидки не улучшали метрики активности за счет экономики.

## Структура проекта

```text
food-delivery-retention-analysis-main/
├── data/
│   ├── dim_users.csv
│   ├── dim_restaurants.csv
│   ├── dim_couriers.csv
│   ├── dim_promo_campaigns.csv
│   ├── fact_orders.csv
│   ├── fact_order_items.csv
│   ├── fact_app_sessions.csv
│   └── fact_ab_test_assignments.csv
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_cohort_retention.ipynb
│   ├── 03_rfm_segmentation.ipynb
│   ├── 04_ab_test_analysis.ipynb
│   ├── 05_final_dashboard.ipynb
│   └── 06_churn_prediction_ml.ipynb
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_load_data.sql
│   ├── 03_retention_cohorts.sql
│   ├── 04_rfm_analysis.sql
│   ├── 05_ab_test_queries.sql
│   └── 06_business_metrics.sql
├── src/
│   ├── features.py
│   ├── modeling.py
│   ├── model_utils.py
│   ├── utils.py
│   └── visualizations.py
├── models/
│   ├── churn_model.joblib
│   └── feature_importance.joblib
├── data_generator.py
├── requirements.txt
└── README.md
```

## Технологии

- Python: `pandas`, `numpy`, `scipy`, `scikit-learn`, `xgboost`, `imbalanced-learn`, `shap`, `joblib`
- Визуализация: `matplotlib`, `seaborn`, `plotly`
- SQL: MySQL 8.0+
- Среда анализа: Jupyter Notebook

## Как запустить проект

### 1. Создать окружение

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Использовать готовые данные или сгенерировать их заново

CSV-файлы уже лежат в папке `data/`. Если нужно пересобрать датасет:

```powershell
python data_generator.py
```

Параметры генератора можно менять:

```powershell
python data_generator.py --n-users 14000 --n-restaurants 260 --n-couriers 1100 --seed 42
```

### 3. Запустить ноутбуки

```powershell
jupyter notebook
```

Рекомендуемый порядок:

1. `notebooks/01_data_exploration.ipynb`
2. `notebooks/02_cohort_retention.ipynb`
3. `notebooks/03_rfm_segmentation.ipynb`
4. `notebooks/04_ab_test_analysis.ipynb`
5. `notebooks/05_final_dashboard.ipynb`
6. `notebooks/06_churn_prediction_ml.ipynb`

### 4. Загрузить данные в MySQL

Создать схему:

```sql
SOURCE sql/01_create_schema.sql;
```

Для Windows + MySQL Workbench удобнее сначала скопировать CSV в путь без кириллицы:

```powershell
New-Item -ItemType Directory -Force C:\food_delivery_data
Copy-Item .\data\*.csv C:\food_delivery_data\ -Force
```

Затем выполнить:

```sql
SOURCE sql/02_load_data.sql;
```

После загрузки можно запускать аналитические SQL-скрипты из папки `sql/`.

## Финальный вывод

Основная зона роста для food delivery-сервиса находится в раннем удержании и точечной реактивации. Повторный заказ в течение 30 дней делают 57.3% eligible-пользователей, но уже к 7-му дню видно, кто с высокой вероятностью не закрепится в продукте. Универсальный баннер бесплатной доставки не дал значимого uplift, поэтому дальнейшие эксперименты должны быть сегментированными. Churn-модель и RFM-сегментация дают основу для более точного CRM: удерживать ценных активных пользователей, отдельно возвращать high-value at-risk аудиторию и не тратить промобюджет одинаково на всю базу.
