# Каноническая область модели

Эта директория — каноническое место для авторинга онтологии.
Пошаговые инструкции по внесению изменений — см. [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Содержимое

- [`metamodel.yaml`](metamodel.yaml) — **core ontology**: типы сущностей, атрибуты, словари, базовые типы связей и метаданные.
- [`relation_catalog.yaml`](relation_catalog.yaml) — **profile overlay**: обогащённые типы связей с UI-лейблами, traversal-правилами, квалификаторами и параметрами impact analysis.
- [`profiles/`](profiles/README.md) — фильтры профильных проекций (например, `atlas_mvp.yaml`).
- [`templates/`](templates/) — готовые шаблоны для контрибьюторов, добавляющих новые сущности или связи.
- [`schema/`](schema/README.md) — JSON Schema контракты валидации.
- [`glossary/`](glossary/README.md) — термины глоссария, алиасы и артефакты политики именования.

Почему метамодель хранится в двух файлах, а не file-per-kind —
см. [Обоснование структуры авторинга](../docs/architecture/authoring_rationale.md).

## Контракт mm / rc (two-layer)

`metamodel.yaml` и `relation_catalog.yaml` — это два слоя одной модели, а не два независимых источника. Чтобы они не расходились (как было до MACWO-512), действуют три правила, которые проверяет CI через [`tools.wave1.contract_validator`](../tools/wave1/contract_validator.py):

1. **Rule 1 — обязательное наличие в core.** Каждый `relations[*].id` в `relation_catalog.yaml` обязан иметь соответствующий `relation_kinds[*].id` в `metamodel.yaml`. Catalog не может вводить «свои» relation'ы — он только обогащает уже декларированные в ядре.
2. **Rule 2 — согласованные эндпоинты.** Поля `from_kind`, `to_kind`, `category` и `direction` обязаны быть одинаковыми в обоих файлах для одного и того же `id`. Расхождения = error в CI.
3. **Rule 3 — core-only relation_kinds допустимы.** В `metamodel.yaml` могут жить relation_kind'ы без обогащения в catalog (они не входят ни в один профиль ещё). Это warning, не error.

CLI: `python -m tools.wave1.contract_validator` (выведет все нарушения; добавьте `--summary-only` для краткого отчёта).

## Какие поля где живут

| Поле | metamodel.yaml | relation_catalog.yaml |
|---|---|---|
| `id`, `name`, `from_kind`, `to_kind`, `category`, `direction`, `description`, `metamodel_level` | ✅ обязательно | ✅ обязательно (Rule 2) |
| `ui_label_in`, `ui_label_out`, `ui_group` | ❌ | ✅ |
| `path_priority`, `is_traversable_by_default`, `allowed_in_neighbors`, `allowed_in_paths`, `allowed_in_impact`, `impact_mode` | ❌ | ✅ |
| `supports_qualifiers`, `allowed_qualifiers`, `required_qualifiers`, `evidence_required` | ❌ | ✅ |
| `applies_to_profiles`, `default_visibility`, `exportable` | ❌ | ✅ |
| `has_inverse`, `inverse_relation_id`, `source_cardinality`, `target_cardinality` | ❌ | ✅ |

Кратко: ядро говорит **что существует**, catalog — **как это используется в профиле**.

## Валидация

```bash
make validate    # запускает все 5 стадий harness'а
```

Стадии:

| Стадия | Что проверяет | Источник |
|---|---|---|
| `ontology_validation` | Структурные инварианты (id, ссылки, перечисления) | `tools/wave1/validator.py` |
| `ontology_lint` | Семантические warnings (имена, алиасы, глоссарий) | `tools/wave1/lint.py` |
| `relation_catalog_validation` | Внутренние инварианты catalog'а (inverse, qualifier'ы) | `tools/wave1/relation_catalog_validator.py` |
| `schema_validation` | JSON Schema на `metamodel.yaml` | `tools/wave1/schema_validator.py` |
| `contract_validation` | Two-layer контракт mm ↔ rc (Rules 1–3) | `tools/wave1/contract_validator.py` |

Любая стадия с `errors > 0` валит CI.
