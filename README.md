# ozon-api — Claude/Agent Skill для Ozon Seller API + Performance API

Skill-репозиторий: полные официальные OpenAPI 3.0 спеки Ozon Seller API
(460 операций, ~55 разделов) и Ozon Performance API — рекламы (48 операций,
6 разделов) + CLI для навигации по ним.

- [SKILL.md](SKILL.md) — точка входа для агента: авторизация, паттерны вызова, грабли.
- [references/ozon-seller-openapi.json](references/ozon-seller-openapi.json) — спек с официального
  `docs.ozon.ru/api/seller/swagger.json`, обогащённый русскими тегами и `x-ozon-section`.
- [references/ozon-performance-openapi.json](references/ozon-performance-openapi.json) — спек рекламы
  с `docs.ozon.ru/api/performance/swagger.json`, та же обработка.
- [references/index.md](references/index.md), [references/index-performance.md](references/index-performance.md) —
  плоские индексы всех эндпоинтов по разделам.
- [scripts/lookup_endpoint.py](scripts/lookup_endpoint.py) — `tags` / `search` / `show`
  (`--api seller|performance`).

## Обновление спеков

Спеки пересобираются скриптом из внешней обёртки (`../tools/build_spec.py`).
docs.ozon.ru за антиботом, поэтому swagger.json надо скачать реальным браузером
(см. докстринг скрипта), затем:

```bash
python3 ../tools/build_spec.py --seller-input seller.json --performance-input perf.json
python3 ../tools/build_spec.py --only performance --performance-input perf.json
```

Только stdlib, сети не требует при переданных входных файлах.
