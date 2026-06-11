# Ozon Performance API (реклама) — индекс категорий

Источник: официальный `docs.ozon.ru/api/performance/swagger.json`. Полный спек: [ozon-performance-openapi.json](./ozon-performance-openapi.json) (~0.3 МБ, 47 путей / 48 операций).

**Не читай OpenAPI целиком.** Используй `scripts/lookup_endpoint.py` (`tags`/`search`/`show`).

Категории отсортированы по числу эндпоинтов.

## Статистика (`Statistics`, 17) — группа «Методы Performance API»

- `POST   /api/client/statistic/orders/generate` — Получить отчёт по заказам в оплате за заказ — выбранные товары
- `POST   /api/client/statistic/products/generate` — Получить отчёт по товарам в оплате за заказ — выбранные товары
- `POST   /api/client/statistics` — Статистика по кампании
- `GET    /api/client/statistics/all_sku_promo/orders/generate` — Получить отчёт по заказам в оплате за заказ — все товары
- `GET    /api/client/statistics/all_sku_promo/products/generate` — Получить отчёт по товарам в оплате за заказ — все товары
- `POST   /api/client/statistics/attribution` — Отчёт по заказам
- `GET    /api/client/statistics/campaign/media` — Статистика по медийным кампаниям
- `GET    /api/client/statistics/campaign/product` — Статистика по кампании Оплата за клик
- `GET    /api/client/statistics/daily` — Дневная статистика по кампаниям
- `GET    /api/client/statistics/expense` — Статистика по расходу кампаний
- `GET    /api/client/statistics/externallist` — Список отчётов, сгенерированных через API
- `GET    /api/client/statistics/list` — Список отчётов, сгенерированных через интерфейс
- `POST   /api/client/statistics/phrases` — Отчёт по поисковым запросам
- `POST   /api/client/statistics/products/sku` — Получить статистику по товарам в оплате за клик
- `GET    /api/client/statistics/report` — Получить отчёты
- `POST   /api/client/statistics/video` — Статистика по показам видеобаннера
- `GET    /api/client/statistics/{UUID}` — Cтатус отчёта

## Оплата за заказ (`Search-Promo`, 12) — группа «Методы Performance API»

- `GET    /api/client/campaign/all_sku_promo/activate` — Включить продвижение в оплате за заказ — все товары
- `GET    /api/client/campaign/all_sku_promo/deactivate` — Выключить продвижение в оплате за заказ — все товары
- `GET    /api/client/campaign/all_sku_promo/set_bid` — Установить ставку для продвижения в Оплате за заказ — все товары
- `POST   /api/client/campaign/search_promo/carrots/disable` — Отключить продвижение товаров в акции «Морковск»
- `POST   /api/client/campaign/search_promo/carrots/enable` — Включить продвижение товаров в акции «Морковск»
- `POST   /api/client/campaign/search_promo/v2/bids/delete` — Удалить товар из продвижения в оплате за заказ
- `POST   /api/client/campaign/search_promo/v2/bids/set` — Установить ставку на товар ⚠️ deprecated
- `POST   /api/client/campaign/search_promo/v2/products` — Список товаров в продвижении в оплате за заказ
- `POST   /api/client/search_promo/bids/recommendation` — Рекомендованные ставки для товаров ⚠️ deprecated
- `POST   /api/client/search_promo/get_cpo_min_bids` — Получить фиксированные ставки для товаров
- `POST   /api/client/search_promo/product/disable` — Отключить продвижение товара в оплате за заказ
- `POST   /api/client/search_promo/product/enable` — Включить продвижение товара в оплате за заказ

## Кампании и рекламируемые объекты (`Campaign`, 5) — группа «Методы Performance API»

- `GET    /api/client/campaign` — Список кампаний
- `GET    /api/client/campaign/{campaignId}/objects` — Список продвигаемых объектов в кампании
- `GET    /api/client/limits/list` — Лимиты ставок для инструментов продвижения
- `POST   /api/client/min/sku` — Минимальная ставка для товаров по SKU
- `GET    /api/client/products_with_bonuses` — Список товаров с бонусами

## Оплата за клик (`Ad`, 5) — группа «Методы Performance API»

- `POST   /api/client/campaign/cpc/v2/product` — Создать кампанию с оплатой за клики
- `PATCH  /api/client/campaign/{campaignId}` — Параметры кампании
- `POST   /api/client/campaign/{campaignId}/activate` — Активировать кампанию
- `POST   /api/client/campaign/{campaignId}/deactivate` — Выключить кампанию
- `POST   /external/api/dynamic_budget` — Рассчитать минимальный бюджет кампании ⚠️ deprecated

## Товары в Оплате за клик (`Product`, 5) — группа «Методы Performance API»

- `POST   /api/client/campaign/{campaignId}/products` — Добавить товары в кампанию
- `PUT    /api/client/campaign/{campaignId}/products` — Обновить ставки товаров
- `GET    /api/client/campaign/{campaignId}/products/bids/competitive` — Конкурентные ставки для товара
- `POST   /api/client/campaign/{campaignId}/products/delete` — Удалить товары из кампании
- `GET    /api/client/campaign/{campaignId}/v2/products` — Список товаров кампании

## Аналитика внешнего трафика (`Vendor`, 4) — группа «Методы Performance API»

- `GET    /api/client/organisation/vendor_tag` — Метка организации для внешних рекламных кампаний
- `POST   /api/client/vendors/statistics` — Отчёт с аналитикой внешнего трафика
- `GET    /api/client/vendors/statistics/list` — Список запрошенных отчётов с аналитикой внешнего трафика
- `GET    /api/client/vendors/statistics/{UUID}` — Информация об отчёте по UUID
