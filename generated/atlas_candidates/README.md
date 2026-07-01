# Бандлы-кандидаты Atlas

Эта директория содержит версионированные детерминированные бандлы-кандидаты Atlas, сгенерированные из канонических входных данных онтологии и профиля.

Идентификаторы бандлов иммутабельны: однажды опубликованный путь бандла не должен повторно использоваться для других артефактов.

**Это единственное отслеживаемое (committed) расположение релизных бандлов.** `make bundle` пишет черновой бандл в корень `generated/<name>/` — эти пути gitignore-нуты (скретч) и не промотируются. Для релиза бандл должен быть перемещён сюда под иммутабельным `__vN`-идентификатором и закоммичен.

## Текущий кандидат

- Версия модели: `2`
- Профиль: `atlas_mvp`
- Путь бандла: `generated/atlas_candidates/bank_metamodel_horizontal__2__atlas_mvp__v7/`
- Счётчик `__vN` — ручной релиз-инкремент; предыдущие кандидаты остаются иммутабельными историческими артефактами.

## Как нарезать новый кандидат

```bash
# 1. Убедиться, что модель зелёная
make validate            # 0 errors
make determinism         # детерминированная сборка

# 2. Нарезать бандл (пишет в корень generated/, скретч)
make bundle              # → generated/bank_metamodel_horizontal__2__atlas_mvp/

# 3. Переместить под иммутабельным __vN (инкремент от последнего в atlas_candidates/)
mv generated/bank_metamodel_horizontal__2__atlas_mvp \
   generated/atlas_candidates/bank_metamodel_horizontal__2__atlas_mvp__v8

# 4. Добавить BUNDLE_RELEASE_NOTES.md (дельта над предыдущим vN) и закоммитить
```

## Промоушен в rbank-atlas

Промоушен переносит закоммиченный кандидат в downstream-реестр
(`rbank-atlas/specs/metamodel/versions/`) и пинит `active_version.json`.

- **Автоматически:** workflow [`.github/workflows/promote-bundle.yaml`](../../.github/workflows/promote-bundle.yaml)
  срабатывает на push в `main`, затрагивающий `generated/atlas_candidates/**`,
  берёт последний бандл (`sort -V`) и открывает PR в `rbank-atlas`. Шаг
  «Skip if already promoted» — идемпотентный страж: если версия уже есть в
  downstream, промоушен пропускается (без дубль-PR).
- **Вручную / повторно:** `workflow_dispatch` с явным `bundle_version`.

Оба пути пинят `active_version` и валидируют бандл штатным импортёром Atlas
(`load_active_metamodel_bundle`).

> **Раскладка в Atlas:** контракт-валидатор Atlas
> (`scripts/validate_metamodel_bundle.py`) ждёт артефакты в **корне**
> version-каталога (`versions/<id>/type_catalog.json`, …), а не только во
> вложенной `artifacts/`. Workflow уплощает их автоматически; при ручном
> промоушене нужно скопировать `artifacts/*` в корень версии (как в v1..v6).
