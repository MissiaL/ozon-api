# ozon-api — Claude/Agent Skill для Ozon Seller API

Skill-репозиторий: полный официальный OpenAPI 3.0 спек Ozon Seller API
(460 операций, ~55 разделов) + CLI для навигации по нему.

- [SKILL.md](SKILL.md) — точка входа для агента: авторизация, паттерны вызова, грабли.
- [references/ozon-seller-openapi.json](references/ozon-seller-openapi.json) — спек с официального
  `docs.ozon.ru/api/seller/swagger.json`, обогащённый русскими тегами и `x-ozon-section`.
- [references/index.md](references/index.md) — плоский индекс всех эндпоинтов по разделам.
- [scripts/lookup_endpoint.py](scripts/lookup_endpoint.py) — `tags` / `search` / `show` по спеку.

## Обновление спека

Спек пересобирается скриптом из внешней обёртки (`../tools/build_spec.py`).
docs.ozon.ru за антиботом, поэтому swagger.json надо скачать реальным браузером
(см. докстринг скрипта), затем:

```bash
python3 ../tools/build_spec.py --input /path/to/swagger.json
```

Только stdlib, сети не требует при `--input`.
