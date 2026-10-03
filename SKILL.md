---
name: ozon-api
description: "Use for Ozon Seller API and Ozon Performance API work: товары, цены, остатки, FBS/rFBS/FBO, поставки, возвраты, отчёты, финансы, отзывы, чаты, реклама, кампании, статистика, ставки. Triggers: ozon, озон, Ozon API, озон апи, Seller API, реклама на озоне, api-seller.ozon.ru, api-performance.ozon.ru, docs.ozon.ru/api."
---

# Ozon Seller API + Performance API

This skill helps you call two Ozon APIs, each with its own bundled official OpenAPI 3.0 spec:

- **Seller API** (`https://api-seller.ozon.ru`) — товары, цены, заказы, поставки, отчёты: 481 operations across 56 sections. Everything below describes it unless said otherwise.
- **Performance API** (`https://api-performance.ozon.ru`) — реклама: кампании, статистика, ставки: 48 operations across 6 sections. Different host, different credentials, different auth — see [the dedicated section](#ozon-performance-api--реклама) at the end.

Both official snapshots were fetched on **2026-10-03**. Their `x-source` records the source URL, verification date, and SHA-256 of the downloaded source. These are documentation snapshots; endpoint availability and account permissions still require a live authenticated request. The seller spec is large; use the helpers below to pull only what you need.

## Authentication — Client-Id + Api-Key headers

Every request carries **two headers** (no token endpoint, no OAuth dance needed):

```http
Client-Id: <числовой ID кабинета продавца>
Api-Key: <API-ключ>
Content-Type: application/json
```

The user gets both in the Ozon seller cabinet: **seller.ozon.ru → Настройки → Seller API** (`/app/settings/api-keys`). The Client-Id is shown next to the keys list. Keys are shown **only once at creation** and have an access-level role chosen at creation — a read-only key will get `403` on mutating methods.

New Seller API keys expire after **3 months**. Check `expires_at` in `/v1/roles` and arrange replacement before expiry; see `tag-info Auth` or [official authorization docs](https://docs.ozon.ru/api/seller/#tag/Auth).

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

# 4) Read doc-only tag prose (auth walkthroughs, limits) that has no endpoints
python3 scripts/lookup_endpoint.py tag-info Auth
```

`show` resolves local `$ref` one level for readability but leaves nested refs alone. External or missing refs remain visible as `$ref`; the official Seller snapshot contains external `rpcStatus.yaml` references in two operations, so their error schemas are not fully bundled. For a deeper schema, read `references/ozon-seller-openapi.json` with `jq`:

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

# example: unprocessed FBS postings (v4 — v3 shutdown date has passed)
curl -s -X POST "https://api-seller.ozon.ru/v4/posting/fbs/unfulfilled/list" \
  -H "Client-Id: $OZON_CLIENT_ID" -H "Api-Key: $OZON_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"cutoff_from":"2026-08-01T00:00:00Z","cutoff_to":"2026-08-14T23:59:59Z"},"limit":100,"sort_dir":"asc"}' | jq .
```

For Python, use `requests`/`httpx` with the same two headers. No SDK needed — every endpoint is a plain JSON HTTP call.

## Conventions and gotchas

- **Base URL** is `https://api-seller.ozon.ru` (no trailing slash). Paths from the spec are appended directly.
- **Almost everything is POST.** 475 of 481 operations are `POST` with a JSON body — including pure reads ("получить список", "информация о..."). The few `GET`s are file downloads (labels, PDF). Don't assume REST semantics.
- **Empty body is still a body.** Even when all parameters are optional, send `{}` with `Content-Type: application/json`.
- **Three product identifiers**, not interchangeable:
  - `offer_id` — артикул продавца (string, your own ID);
  - `product_id` — internal numeric Ozon ID (returned at import);
  - `sku` — ID карточки на витрине (used in postings/analytics; the SKU in the product URL).
  Methods differ in which they accept — check the request schema with `show` before composing.
- **Versioning**: `/v1`…`/v5` of the same method coexist. Follow the documented successor and compare its schema and behavior. Deprecated ones are flagged in `search`/`show` and the index; read the description for shutdown dates. A path still present in the snapshot may already have been switched off.
- **Pagination is inconsistent across sections**: products use cursor `last_id` + `limit`; postings use `offset`/`limit` or `cursor`; some reports use `page`/`page_size`. Read the schema, don't assume.
- **Hard caps live in descriptions**, e.g. «не больше 1000 товаров в одном запросе» for `/v3/product/info/list`. Trust the prose description over schema `maxItems`.
- **Schema inconsistencies exist.** If `required`, `properties`, examples, or a shutdown notice disagree, consult the current method documentation before composing the request; report unresolved conflicts instead of silently dropping required fields.
- **Seller rate limits**: unless a method declares its own limit, the default is **50 requests/second per Client ID**. Read `Ratelimit-Remaining` and honor `Retry-After` on `429`; the full rules are in `tag-info Limits` or [official limits docs](https://docs.ozon.ru/api/seller/#tag/Limits). `/v1/analytics/data` allows at most **1 request/minute**, and without Premium Plus/Pro has a **50 requests/day** cap and three-month data window. Retry transient failures with bounded backoff only when the operation can safely be repeated.
- **Premium-методы** (tag `Premium`: extended analytics, daily realisation reports) require an active Premium subscription; `ReviewAPI` (отзывы) requires the «Управление отзывами» or Premium Pro subscription (each method's description names the required plan). Without it the API returns an access error — that's the subscription, not a bad key.
- **Бета-методы** group (FBP, акции продавца, грузоместа) can change without notice — flag this to the user when relying on them.
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

When you report an error to the user, include the HTTP status and relevant error body with secrets and private data redacted.

## Sections at a glance

56 sections in 4 groups. Full per-endpoint list is in [references/index.md](references/index.md).

| Group | # | What's inside |
|---|---:|---|
| Базовые методы | 323 | Товары (`ProductAPI`, `CategoryAPI`, `BarcodeAPI`), цены и остатки (`Prices&StocksAPI`), заказы и отправления FBS/rFBS (`FBS`, `DeliveryFBS`, `DeliveryrFBS`, `FBS&rFBSMarks`), поставки FBO (`FboSupplyRequest`, `FBO`), склады (`WarehouseAPI`, `FBSWarehouseSetup`), возвраты (`ReturnsAPI`, `RFBSReturnsAPI`, `ReturnAPI`), отмены, акции (`Promos`), стратегии цен (`PricingStrategyAPI`), сертификаты, отчёты (`ReportAPI`), финансы (`FinanceAPI`), аналитика, рейтинг, чаты, цифровые товары, отзывы, вопросы и ответы |
| Бета-методы | 133 | FBP-поставки (черновики/поставки direct, drop-off, pick-up), грузоместа FBS/FBO (`CarriageAPI`, `FBOTransport`), акции продавца (`SellerActions`), пуш-уведомления |
| Ozon Доставка | 15 | Интеграция «Ozon Доставка» для внешних магазинов (`OrderAPI`, `DeliveryAPI`) — не то же самое, что доставка маркетплейса |
| Premium-методы | 10 | Расширенная аналитика, ежедневные отчёты о реализации — только с подпиской Premium |

## Ozon Performance API — реклама

A separate API for advertising campaigns. **Don't mix it up with the Seller API**: different host, different credentials, different auth scheme.

**Auth — OAuth2 Client Credentials.** Credentials come from the same cabinet page as seller keys, but a different tab: **seller.ozon.ru → Настройки → API-ключи → вкладка Performance API** — there the user creates a *service account* and gets `client_id` (looks like `XYZ@advertising.performance.ozon.ru`) + `client_secret`. Exchange them for a Bearer token:

```bash
curl -s -X POST "https://api-performance.ozon.ru/api/client/token" \
  -H "Content-Type: application/json" \
  -d "{\"client_id\":\"$OZON_PERF_CLIENT_ID\",\"client_secret\":\"$OZON_PERF_CLIENT_SECRET\",\"grant_type\":\"client_credentials\"}"
# {"access_token":"...","expires_in":1800,"token_type":"Bearer"}
```

Cache the token for the returned **`expires_in`** seconds (the documented example is 1800), then refresh it on expiry/401. Use it as `Authorization: Bearer <token>` on every call to `https://api-performance.ozon.ru`.

**Lookup** works the same way, with `--api performance`:

```bash
python3 scripts/lookup_endpoint.py tags --api performance
python3 scripts/lookup_endpoint.py search статистика --api performance
python3 scripts/lookup_endpoint.py show /api/client/campaign --api performance
```

Index: [references/index-performance.md](references/index-performance.md). Sections: Кампании (`Campaign`), Статистика (`Statistics`, 17 — the biggest), Оплата за клик (`Ad`, `Product`), Оплата за заказ (`Search-Promo`), Аналитика внешнего трафика (`Vendor`).

Performance-specific gotchas:

- **Paths already include `/api/client/...`** — append them to the host as-is, don't add prefixes.
- **Statistics are async**: `POST /api/client/statistics` (or `/statistics/video`, `/statistics/attribution`) returns a `UUID` → poll `GET /api/client/statistics/{UUID}` until ready → download via `GET /api/client/statistics/report?UUID=...`. Response format is CSV for one campaign, ZIP of CSVs for several.
- **Mixed verbs**: unlike the Seller API, this one uses GET extensively (22 of 48). Check with `show`.
- **Limits**: 100 000 requests/day total; statistics exports are capped — max 62 days per export, max 10 campaigns per report, **only 1 concurrent export per account** (5 per organisation), daily export quota = активные кампании × 240, но не больше 2000/сутки. One campaign in a request = one export. Full table: `python3 scripts/lookup_endpoint.py tag-info Limits --api performance`.
- Deprecated methods exist here too (3) — `search`/`show` flag them, but unlike the Seller API their descriptions **don't always name a successor** (e.g. the per-SKU Search-Promo bid methods). Don't guess the replacement — check the section's remaining methods with `search --tag Search-Promo` and confirm the flow with the user.
- **Doc-only tags** (`Token`, `Limits`, `Intro` here; `Auth`, `Environment` in the Seller spec) have no endpoints — they're prose. Read them with `tag-info`: e.g. `lookup_endpoint.py tag-info Token --api performance` prints the full auth walkthrough.

## Working with the user

- Look up the operation and execute within the user's authorized scope. An explicit request for a specific read or update already authorizes it; avoid repeated confirmation. Resolve ambiguous targets or unapproved live changes before sending them.
- If the request is ambiguous (e.g. "выгрузи остатки" — FBS warehouse stocks? FBO? by-warehouse breakdown?), `search` first and ask which they mean before making calls.
- When credentials are missing, ask the user to configure local environment variables `OZON_CLIENT_ID` / `OZON_API_KEY` (Seller) or `OZON_PERF_CLIENT_ID` / `OZON_PERF_CLIENT_SECRET` (Performance), and explain where to get them (seller.ozon.ru → Настройки → API-ключи, для рекламы — вкладка Performance API). Keep secrets out of chat and command output. Without credentials, prepare the call and report that live execution is unverified.
- For mutations (товары, цены, остатки, статусы отправлений, отмены), check the target, body, and existing authorization immediately before sending. There is no sandbox; an accidental `/v2/products/stocks` update changes the live store.

## Recent migrations to check

For the affected workflows, consult the bundled operation descriptions and [official update notices](https://docs.ozon.ru/api/seller/#tag/News):

- `/v1/product/certificate/products/list`: since 2026-09-28 use `last_id`/`limit`; the official snapshot still lists the retired `page`/`page_size` fields as deprecated.
- Promotions: `/v2/actions/...` methods change behavior on **2026-10-13**, when the replaced v1 methods are scheduled to stop. Use the documented v2 schema and recheck the rollout notice when migrating.
- FBS labels: the new `scanit` labels begin on **2026-10-05**. Check `/v3/posting/fbs/package-label/create` and `/v2/posting/fbs/package-label/get` plus the older methods' shutdown notices.
