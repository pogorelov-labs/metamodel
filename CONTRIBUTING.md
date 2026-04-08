# Как вносить изменения в метамодель

Этот репозиторий содержит **каноническое описание метамодели** платформы RBank Atlas.
Изменения здесь влияют на все downstream-системы (API, MCP, UI, ingestion).

---

## Быстрый старт

```bash
git clone <repo-url> && cd metamodel

make validate    # Валидация: loader + validator + lint + relation catalog
make test        # Юнит-тесты
make diff        # Показать разницу бандла с текущим baseline
make help        # Все доступные команды
```

---

## Где что лежит

| Файл | Содержание |
|------|------------|
| [`model/metamodel.yaml`](model/metamodel.yaml) | Типы сущностей (entity kinds), их атрибуты, словари |
| [`model/relation_catalog.yaml`](model/relation_catalog.yaml) | Типы связей (relation kinds), квалификаторы |
| [`model/templates/`](model/templates/) | Готовые шаблоны для копирования |
| [`model/schema/`](model/schema/) | JSON Schema для валидации |

---

## 1. Добавить новый тип сущности (entity kind)

Файл: **[`model/metamodel.yaml`](model/metamodel.yaml)**, секция `entity_kinds`.

### Шаги

1. Открыть [`model/templates/new_entity_kind.yaml`](model/templates/new_entity_kind.yaml) — скопировать блок
2. Вставить в конец секции `entity_kinds` (перед строкой `relation_kinds:`)
3. Заполнить поля:

```yaml
  - id: data_quality_rule              # snake_case, уникальный
    name: "Data Quality Rule"          # английское имя
    name_ru: "Правило качества данных" # русское имя (обязательно!)
    metamodel_level: solution_details  # уровень (см. ниже)
    category: data                     # семантическая категория
    description: "Правило проверки качества данных при загрузке в граф."
```

### Обязательные поля

| Поле | Формат | Пример |
|------|--------|--------|
| `id` | `snake_case`, уникальный | `data_quality_rule` |
| `name` | Английское имя | `"Data Quality Rule"` |
| `name_ru` | Русское имя | `"Правило качества данных"` |
| `metamodel_level` | Один из уровней | `solution_details` |
| `category` | Произвольная строка | `data`, `process`, `infrastructure` |
| `description` | Описание на русском | `"Что это за сущность и зачем она нужна."` |

### Допустимые значения `metamodel_level`

| Уровень | Что описывает | Примеры |
|---------|---------------|---------|
| `strategic_view` | Стратегия, цели, продукты | goal, bank_product |
| `business_details` | Процессы, способности, ценность | business_process, value_stream |
| `solution_details` | ИТ-системы, информационные потоки | it_system, information_flow |
| `component_details` | Компоненты, API, интеграции | component, api, integration |
| `infrastructure_details` | Инфраструктура, ресурсы | logical_resource, infra_resource |

### Проверка перед коммитом

```bash
make validate    # Должно быть 0 errors
make lint        # Проверка именования, алиасов, консистентности связей
make diff        # Покажет "+1 kind"
```

---

## 2. Добавить атрибут к сущности

Файл: **[`model/metamodel.yaml`](model/metamodel.yaml)**, вложенная секция `attributes` внутри entity kind.

### Пример

У сущности `logical_resource` уже есть атрибут. Чтобы добавить свой:

```yaml
  - id: logical_resource
    name: "Logical Resource"
    name_ru: "Логический ресурс"
    metamodel_level: infrastructure_details
    category: infrastructure
    description: "Логический ресурс хранения или обмена."
    attributes:
      - id: logical_resource.resource_kind       # формат: <kind_id>.<field_id>
        name: "Тип ресурса"
        metamodel_level: infrastructure_details
        description: "DB, Namespace, Bucket, Topic или Queue."
        properties:
          allowed_values: ["DB", "Namespace", "Bucket", "Topic", "Queue"]

      - id: logical_resource.connection_string   # <-- новый атрибут
        name: "Строка подключения"
        metamodel_level: infrastructure_details
        description: "URI или DSN для подключения к ресурсу."
```

### Правила для атрибутов

- `id` — формат `<kind_id>.<field_id>`, snake_case
- `name` — отображаемое имя
- `metamodel_level` — обычно совпадает с уровнем родительской сущности
- `description` — что хранит этот атрибут
- `properties.allowed_values` — (опционально) список допустимых значений

Полная спецификация — см. [контракт атрибутов](docs/architecture/attribute_def_contract_v2.md).

---

## 3. Отредактировать существующую сущность

Файл: **[`model/metamodel.yaml`](model/metamodel.yaml)**.

Найти нужный kind по `id` и изменить поля. Что можно менять безопасно:

| Действие | Риск | Нужен ADR? |
|----------|------|------------|
| Изменить `description` | Нет | Нет |
| Изменить `name_ru` | Нет | Нет |
| Добавить атрибут | Низкий | Нет |
| Изменить `id` | **Ломающее** | **Да** |
| Удалить kind | **Ломающее** | **Да** |
| Изменить `metamodel_level` | Средний | Желательно |

Ломающие изменения (переименование `id`, удаление kind, изменение контракта)
требуют ADR в [`docs/decisions/`](docs/decisions/) — опишите причину, альтернативы и план миграции.

---

## 4. Добавить новый тип связи (relation kind)

Связи живут в **двух** слоях, и это намеренно:

| Файл | Слой | Что определяет |
|------|------|----------------|
| [`model/metamodel.yaml`](model/metamodel.yaml) → секция `relation_kinds` | **core ontology** | Краткое определение (id, from/to, category, direction, level, description) |
| [`model/relation_catalog.yaml`](model/relation_catalog.yaml) → секция `relation_catalog.relations` | **profile overlay** | Полное определение (traversal, qualifiers, UI labels, profiles, impact) |

### Two-layer контракт (Rules 1–3)

CI [`tools.wave1.contract_validator`](tools/wave1/contract_validator.py) автоматически проверяет:

- **Rule 1** — каждый `relations[*].id` в catalog обязан иметь соответствующий `relation_kinds[*].id` в `metamodel.yaml`. Catalog не вводит новые relation'ы — только обогащает декларированные.
- **Rule 2** — `from_kind`, `to_kind`, `category`, `direction` обязаны совпадать между mm.yaml и rc.yaml для одного и того же id. Расхождение = error.
- **Rule 3** — relation_kind в `metamodel.yaml` без catalog-overlay допустим (warning, не error). Это «core declaration», ещё не вошедший ни в один профиль.

> **Практическое следствие:** при добавлении новой связи **сначала** добавляйте запись в `metamodel.yaml`, потом обогащение в `relation_catalog.yaml`. Если добавляете только в catalog — контракт не пройдёт CI.

### Шаг 1: Краткая запись в `metamodel.yaml`

Вставить в секцию `relation_kinds`:

```yaml
  - id: rel_rule_validates_entity        # rel_<source>_<verb>_<target>
    name: "Rule validates Entity"
    from_kind: data_quality_rule          # должен существовать в entity_kinds
    to_kind: business_entity             # должен существовать в entity_kinds
    metamodel_level: solution_details
    category: association
    direction: directed
    description: "Правило качества данных проверяет бизнес-сущность."
```

### Шаг 2: Полная запись в `relation_catalog.yaml`

Скопировать шаблон из [`model/templates/new_relation_kind.yaml`](model/templates/new_relation_kind.yaml) и вставить
в секцию `relation_catalog.relations`:

```yaml
    - id: rel_rule_validates_entity
      name: Rule validates Entity
      description: Data quality rule validates a business entity.
      from_kind: data_quality_rule
      to_kind: business_entity
      category: association
      direction: directed
      source_cardinality: many
      target_cardinality: many
      has_inverse: false
      inverse_relation_id: null
      is_traversable_by_default: true
      allowed_in_neighbors: true
      allowed_in_paths: true
      allowed_in_impact: false
      default_visibility: visible
      path_priority: secondary
      impact_mode: exclude
      supports_qualifiers: false
      allowed_qualifiers: []
      required_qualifiers: []
      evidence_required: false
      ui_label_out: validates
      ui_label_in: validated by
      ui_group: structure
      exportable: true
      status: active
      introduced_in: "2.0.0"
      applies_to_profiles: [atlas_mvp]
```

### Ключевые поля связи

| Поле | Что значит |
|------|------------|
| `from_kind` / `to_kind` | Какие сущности связывает (должны существовать) |
| `direction` | `directed` (стрелка) или `undirected` |
| `category` | `composition`, `aggregation`, `association`, `realization`, `dependency`, `flow` |
| `source_cardinality` / `target_cardinality` | `one` или `many` |
| `has_inverse` | Есть ли обратная связь (если `true` — определить её отдельно) |
| `allowed_in_neighbors` / `paths` / `impact` | Где эту связь можно использовать в graph queries |
| `ui_label_out` / `ui_label_in` | Как читается: "A **validates** B" / "B **validated by** A" |
| `applies_to_profiles` | В каких профилях видна (обычно `[atlas_mvp]`) |

---

## 5. Добавить квалификатор на связь

Квалификаторы — это атрибуты на рёбрах графа (например, `order_index`, `criticality`).

Определены в начале [`model/relation_catalog.yaml`](model/relation_catalog.yaml), секция `qualifier_references`:

```yaml
qualifier_references:
  - id: order_index
    note: "Ordering hint for staged or sequential relations"
  - id: criticality
    note: "Business criticality of edge assertion"
  # ...добавить новый:
  - id: sla_class
    note: "SLA classification for the relation"
```

Чтобы связь использовала квалификатор — указать в её определении:

```yaml
    - id: rel_rule_validates_entity
      # ...
      supports_qualifiers: true
      allowed_qualifiers: [criticality, sla_class]
      required_qualifiers: [criticality]    # обязательные
```

Полная спецификация — см. [контракт квалификаторов](docs/architecture/qualifier_def_contract_v2.md).

---

## Общий workflow

```bash
# 1. Ветка
git checkout -b feat/add-<что-добавляем>

# 2. Редактирование
#    model/metamodel.yaml       — сущности, атрибуты, краткие связи
#    model/relation_catalog.yaml — полные связи, квалификаторы

# 3. Проверка
make validate    # 0 errors обязательно
make lint        # именование, консистентность
make diff        # посмотреть дельту бандла

# 4. Коммит + PR
git add model/metamodel.yaml model/relation_catalog.yaml
git commit -m "feat: add <что добавили>"
git push -u origin feat/add-<что-добавляем>
```

CI автоматически прогонит validate + lint + test и опубликует **bundle diff**
в комментарии к PR.

### После открытия PR

1. Дождитесь зелёных чеков CI (validate, lint, test, determinism).
2. Metamodel Architect проведёт ревью — обычно в течение 1–2 рабочих дней.
3. При замечаниях — правьте, пушьте, CI перезапустится автоматически.
4. После апрува мейнтейнер мержит PR. Изменения попадают в следующий релизный бандл.

---

## Роли

| Роль | Ответственность |
|------|-----------------|
| **Metamodel Architect** | Апрувит все структурные изменения kinds/relations |
| **Data Owner** | Подтверждает атрибуты для своего домена |
| **Platform Team** | Поддерживает тулинг, CI, валидацию |

## Правила

- Один PR — одно изменение (атомарность)
- Все `id` — `snake_case`
- `name_ru` обязателен для всех сущностей и связей
- Ломающие изменения требуют ADR в [`docs/decisions/`](docs/decisions/)
- Файлы в [`generated/`](generated/) — иммутабельны, не редактировать

## Ссылки

- [Обоснование структуры авторинга](docs/architecture/authoring_rationale.md)
- [Формат YAML метамодели](docs/metamodel_yaml_format.md)
- [Правила контрибьюшена (расширенные)](docs/metamodel_contribution_rules.md)
- [Правила именования](docs/architecture/glossary_alias_naming_policy.md)
- [Контракт entity kind](docs/architecture/entity_kind_contract_v2.md)
- [Контракт relation kind](docs/architecture/relation_kind_contract_v2.md)
- [Контракт атрибутов](docs/architecture/attribute_def_contract_v2.md)
- [Контракт квалификаторов](docs/architecture/qualifier_def_contract_v2.md)
- [Журнал решений](docs/decisions/)
