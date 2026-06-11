---
name: ozon-api
description: Use whenever the user wants to interact with Ozon as a seller — managing product cards (загрузка товаров, атрибуты, категории), prices and stocks (цены и остатки), FBS/rFBS/FBO orders and postings (отправления, сборка, маркировка), supply requests (заявки на поставку FBO), returns (возвраты), promotions (акции), pricing strategies, reports, finance, analytics, seller rating, chats, reviews (отзывы), questions, warehouses, or any other Ozon Seller API endpoint. Trigger on phrases like "Ozon API", "озон апи", "Seller API", "товары на озоне", "отправления озон", "поставка FBO", "остатки на озоне", "акции озон", or any URL under api-seller.ozon.ru or docs.ozon.ru/api/seller. The skill bundles the full official OpenAPI 3.0 spec (460 endpoints, ~55 sections) and a lookup tool — use it instead of guessing paths or schemas, even for endpoints that look obvious.
---

# Ozon Seller API

This skill helps you call the Ozon Seller API (`https://api-seller.ozon.ru`). It bundles the full OpenAPI 3.0 spec from the **official documentation** (`docs.ozon.ru/api/seller/swagger.json`) — 460 operations across ~55 sections.

The spec is large (~3.7 MB). Don't read it whole — use the helpers described below to pull only what you need.

## Authentication — Client-Id + Api-Key headers

Every request carries **two headers** (no token endpoint, no OAuth dance needed):

```http
Client-Id: <числовой ID кабинета продавца>
Api-Key: <API-ключ>
Content-Type: application/json
```

The user gets both in the Ozon seller cabinet: **seller.ozon.ru → Настройки → Seller API** (`/app/settings/api-keys`). The Client-Id is shown next to the keys list. Keys are shown **only once at creation** and have an access-level role chosen at creation — a read-only key will get `403` on mutating methods.

An alternative **OAuth-token** flow exists (`Authorization: Bearer <token>` instead of the two headers) for Ozon "applications" acting on behalf of sellers — only relevant if the user explicitly works with Ozon apps; see the `OAuth-token` tag description in the spec.

There is no sandbox — `api-seller.ozon.ru` is the live store. Mutating calls change real listings and orders.

## How to find the right endpoint — DO THIS FIRST

The OpenAPI spec is too big to read whole. The skill ships a CLI to navigate it:

```bash
# 1) See all sections with endpoint counts
python3 scripts/lookup_endpoint.py tags

# 2) Find endpoints by keyword (matches path, summary, tag — case-insensitive,
#    auto-falls-back to a shorter stem so Russian inflections work)
python3 scripts/lookup_endpoint.py search остатки
python3 scripts/lookup_endpoint.py search /product/info
python3 scripts/lookup_endpoint.py search --tag FBS

# 3) Get full operation details (headers, request/response schemas, deprecation)
python3 scripts/lookup_endpoint.py show /v3/product/info/list
python3 scripts/lookup_endpoint.py show /v2/posting/fbs/get --method post
```

`show` resolves top-level `$ref` for readability but leaves nested refs alone — for a deeper schema, read `references/ozon-seller-openapi.json` directly with `jq`:

```bash
jq '.components.schemas | keys[:50]' references/ozon-seller-openapi.json
```

For a category overview, browse [references/index.md](references/index.md) — a flat per-section list of all paths and summaries with deprecated markers.

**Why this matters:** the same logical method often exists in several versions (`/v1/product/info/stocks-by-warehouse/fbs` **and** `/v2/...`, postings have `/v2` and `/v3` lists) and the older ones are deprecated. Field names and limits differ between versions. Guessing leads to 404s, wrong schemas, or deprecated paths. Always look up before composing a request.

## Calling pattern

```bash
# example: get product info by offer_id
curl -s -X POST "https://api-seller.ozon.ru/v3/product/info/list" \
  -H "Client-Id: $OZON_CLIENT_ID" \
  -H "Api-Key: $OZON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"offer_id": ["АРТИКУЛ-123"]}' | jq .

# example: unprocessed FBS postings (v4 — v3 is deprecated, dies 2026-06-01)
curl -s -X POST "https://api-seller.ozon.ru/v4/posting/fbs/unfulfilled/list" \
  -H "Client-Id: $OZON_CLIENT_ID" -H "Api-Key: $OZON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"cutoff_from":"2026-06-01T00:00:00Z","cutoff_to":"2026-06-14T23:59:59Z"},"limit":100,"sort_dir":"ASC"}' | jq .
```

For Python, use `requests`/`httpx` with the same two headers. No SDK needed — every endpoint is a plain JSON HTTP call.

## Conventions and gotchas

- **Base URL** is `https://api-seller.ozon.ru` (no trailing slash). Paths from the spec are appended directly.
- **Almost everything is POST.** 454 of 460 operations are `POST` with a JSON body — including pure reads ("получить список", "информация о..."). The few `GET`s are file downloads (labels, PDF). Don't assume REST semantics.
- **Empty body is still a body.** Even when all parameters are optional, send `{}` with `Content-Type: application/json`.
- **Three product identifiers**, not interchangeable:
  - `offer_id` — артикул продавца (string, your own ID);
  - `product_id` — internal numeric Ozon ID (returned at import);
  - `sku` — ID карточки на витрине (used in postings/analytics; the SKU in the product URL).
  Methods differ in which they accept — check the request schema with `show` before composing.
- **Versioning**: `/v1`…`/v5` of the same method coexist. Prefer the highest non-deprecated version; deprecated ones are flagged in `search`/`show` output and in `index.md`, and their `description` names the successor (e.g. `/v3/posting/fbs/list` → «переключитесь на `/v4/posting/fbs/list`») — read it with `show` before picking a replacement.
- **Pagination is inconsistent across sections**: products use cursor `last_id` + `limit`; postings use `offset`/`limit` or `cursor`; some reports use `page`/`page_size`. Read the schema, don't assume.
- **Hard caps live in descriptions**, e.g. «не больше 1000 товаров в одном запросе» for `/v3/product/info/list`. Trust the prose description over schema `maxItems`.
- **`required` arrays in schemas sometimes lie** — they can list properties that don't exist in `properties` at all (e.g. `quant_size` in the `/v2/products/stocks` request schema). When `required` and `properties`/`example` disagree, trust `properties` and the example.
- **Rate limits are not in the spec.** Ozon throttles per-method and per-account; `429` means back off with exponential retry. Mass operations (price/stock updates) have documented per-minute caps in method descriptions.
- **Premium-методы** (tag `Premium`: extended analytics, daily realisation reports) require an active Premium subscription; `ReviewAPI` (отзывы) requires the «Управление отзывами» or Premium Pro subscription (each method's description names the required plan). Without it the API returns an access error — that's the subscription, not a bad key.
- **Бета-методы** group (FBP, отзывы, акции продавца, грузоместа) can change without notice — flag this to the user when relying on them.
- **Dates** are RFC3339 with `Z` (`2026-06-11T00:00:00Z`). Don't pass local time without an offset.
- **Field naming is snake_case** throughout (`offer_id`, `posting_number`, `cutoff_from`).

## Errors

Error bodies follow the google.rpc style:

```json
{"code": 5, "message": "PRODUCT_NOT_FOUND", "details": []}
```

`code` here is a **gRPC code, not the HTTP status** (3 = InvalidArgument, 5 = NotFound, 7 = PermissionDenied, 8 = ResourceExhausted, 16 = Unauthenticated). Map the HTTP status first, then read `message`:

- `400` — validation: re-read the request schema with `show`.
- `403` — wrong/insufficient Api-Key role, missing Premium subscription, or the method needs a different access level. Tell the user which permission to add when generating a key.
- `404` — wrong path or the entity doesn't belong to this Client-Id.
- `429` — rate limit: back off, retry with exponential backoff.
- `5xx` — Ozon's side: retry with backoff.

When you report an error to the user, include the HTTP status and the full body.

## Sections at a glance

~55 sections in 4 groups. Full per-endpoint list is in [references/index.md](references/index.md).

| Group | # | What's inside |
|---|---:|---|
| Базовые методы | 298 | Товары (`ProductAPI`, `CategoryAPI`, `BarcodeAPI`), цены и остатки (`Prices&StocksAPI`), заказы и отправления FBS/rFBS (`FBS`, `DeliveryFBS`, `DeliveryrFBS`, `FBS&rFBSMarks`), поставки FBO (`FboSupplyRequest`, `FBO`), склады (`WarehouseAPI`, `FBSWarehouseSetup`), возвраты (`ReturnsAPI`, `RFBSReturnsAPI`, `ReturnAPI`), отмены, акции (`Promos`), стратегии цен (`PricingStrategyAPI`), сертификаты, отчёты (`ReportAPI`), финансы (`FinanceAPI`), аналитика, рейтинг, чаты, цифровые товары |
| Бета-методы | 137 | FBP-поставки (черновики/поставки direct, drop-off, pick-up), грузоместа FBS/FBO (`CarriageAPI`, `FBOTransport`), отзывы (`ReviewAPI`), вопросы и ответы, акции продавца (`SellerActions`), пуш-уведомления, кванты |
| Ozon Доставка | 15 | Интеграция «Ozon Доставка» для внешних магазинов (`OrderAPI`, `DeliveryAPI`) — не то же самое, что доставка маркетплейса |
| Premium-методы | 10 | Расширенная аналитика, ежедневные отчёты о реализации — только с подпиской Premium |

## Working with the user

- If the user's request maps to one obvious endpoint, look it up, show them the call you're about to make (URL, headers minus secrets, body), and execute when they confirm.
- If the request is ambiguous (e.g. "выгрузи остатки" — FBS warehouse stocks? FBO? by-warehouse breakdown?), `search` first and ask which they mean before making calls.
- When credentials are missing, ask for `OZON_CLIENT_ID` / `OZON_API_KEY` and explain where to get them (seller.ozon.ru → Настройки → Seller API). Don't fabricate test calls without credentials — prepare the curl/python command and let the user run it.
- Watch out for endpoints that mutate state (товары, цены, остатки, статусы отправлений, отмены). There is no sandbox — confirm with the user before sending; an accidental `/v2/products/stocks` update changes the live store.
