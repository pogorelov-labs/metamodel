# Attribute Definition Contract

> Контракт определения атрибута сущности в онтологии.

## 1. Назначение

`attribute_def` — это **authoring-level контракт поля**, который определяет, как конкретный атрибут сущности описывается в онтологии, валидируется, сериализуется в runtime и используется в UI/search/export.

Задача контракта:
- превратить атрибуты из свободных текстовых описаний в строгую и машиночитаемую модель;
- сделать возможной автоматическую генерацию `type_catalog.json` и runtime field metadata;
- зафиксировать достаточную семантику для entity card, filters, search, evidence и export.

`attribute_def` принадлежит **upstream authoring schema** в репозитории `metamodel`.
`rbank-atlas` не должен читать authoring-форму напрямую; он получает только нормализованную runtime-проекцию через release bundle.

---

## 2. Принципы

1. **Attribute-as-contract, not prose**  
   Атрибут должен иметь строгую типизацию, cardinality и поведение в runtime.

2. **Single semantic meaning**  
   Один `attribute_def` описывает одно семантическое поле. Не допускается смешивать несколько смыслов в одном атрибуте.

3. **Authoring richness, runtime discipline**  
   В authoring-слое допускаются расширенные metadata/hints; в runtime попадает только нормализованная и полезная часть.

4. **Kind-scoped identity**  
   Идентификатор атрибута должен быть уникален в рамках модели и обычно иметь вид `<kind_id>.<field_id>`.

5. **UI/search/filter behavior is explicit**  
   Нельзя оставлять поведение поля на догадку frontend/backend. Searchability, filterability, sortability, link semantics и display semantics задаются явно.

6. **Reference vs scalar must be explicit**  
   Поле-ссылка на другой объект должно отличаться от текстового поля не по значению, а по контракту.

---

## 3. Область применения

`attribute_def` используется для:
- `entity_kind.attributes[]`;
- генерации `type_catalog.json`;
- генерации runtime field metadata в `metamodel_snapshot.json` / `type_catalog`;
- настройки entity card (key attributes, inline links, JSON view, display hints);
- настройки search/filter/index behavior;
- export hints;
- compatibility checks.

`attribute_def` **не** определяет:
- relation semantics между сущностями;
- qualified edge contract;
- source mapping конкретных внешних систем;
- merge/conflict resolution runtime-данных.

---

## 4. Обязательный контракт `attribute_def`

### 4.1. Identity and naming

#### Required
- `id: string`  
  Канонический ID атрибута. Формат по умолчанию: `<kind_id>.<field_id>`.
- `name: string`  
  Каноническое human-readable имя.
- `name_ru: string`  
  Человеко-читаемое имя на русском для UI/catalog.
- `description: string`  
  Краткое, точное определение смысла поля.

#### Optional but strongly recommended
- `aliases: string[]`  
  Синонимы/исторические имена поля.
- `example_values: array`  
  Примеры допустимых значений.

### 4.2. Ownership and scope

#### Required
- `kind_id: string`  
  Kind, которому принадлежит атрибут.
- `category: enum`  
  Один из:
  - `identity`
  - `business`
  - `organizational`
  - `lifecycle`
  - `technical`
  - `data`
  - `security`
  - `integration`
  - `evidence`
  - `display`
  - `custom`

#### Optional
- `metamodel_level: enum`  
  Например: `core`, `business_details`, `solution_details`, `data_details`, `operational_details`.
- `namespace: string`  
  Для логической группировки полей в authoring/runtime catalog.

### 4.3. Type system

#### Required
- `data_type: enum`  
  **Enforced** — whitelist в `tools/wave1/validator.py` (`_ALLOWED_VALUE_TYPES`), нормативный источник истины. Любое значение вне этого набора роняет `make validate`:
  - `string`
  - `text`
  - `integer`
  - `number`
  - `boolean`
  - `enum`
  - `id` — ссылка на другую сущность по id (**текущий** механизм ссылок; 21 использование в модели)
  - `uri`

  **Planned / reserved** — задокументированы как намерение, но **пока не принимаются валидатором**. Не использовать в authoring, пока не добавлены в whitelist (см. roadmap):
  - `date`, `datetime` — сегодня моделируются как `string` + `format_hint`
  - `url` — сегодня как `string` + `display_mode=link`
  - `urn_ref` (+ `ref_kind`, `display_mode=entity_ref`) — планируемый типизированный upgrade над `id`; см. миграцию `id` → typed-ref в roadmap (MACWO-532)
  - `external_key`, `json` (+ `json_schema_ref`)

- `cardinality: enum`  
  Один из:
  - `one`
  - `many`

- `required: boolean`

#### Conditional
- `enum_values: array` — обязательно, если `data_type=enum` и используется inline enum.
- `enum_ref: string` — альтернатива `enum_values`, если используется внешний enum dictionary.
- `ref_kind: string | string[]` — обязательно, если `data_type=urn_ref`.
- `json_schema_ref: string` — допустимо, если `data_type=json` и нужна строгая структура.
- `format_hint: string` — допустимо для `string`/`text`, если есть regex/format semantics, например `email`, `semver`, `cron`, `country_code`.

### 4.4. Runtime behavior hints

#### Required
- `is_searchable: boolean`
- `is_filterable: boolean`
- `is_sortable: boolean`
- `is_facetable: boolean`
- `is_exported_by_default: boolean`

#### Optional
- `filter_operators: string[]`  
  Например: `eq`, `in`, `contains`, `prefix`, `range`, `exists`.
- `sort_nulls_policy: enum`  
  `first | last`
- `indexing_strategy: enum`  
  `keyword | fulltext | exact | none`

### 4.5. UI/display semantics

#### Required
- `display_mode: enum`  
  Один из:
  - `plain`
  - `long_text`
  - `badge`
  - `chip_list`
  - `json`
  - `link`
  - `entity_ref`
  - `date`
  - `datetime`

#### Optional
- `display_group: string`  
  Для логического grouping на карточке/registry.
- `display_order: integer`
- `collapse_by_default: boolean`
- `copyable: boolean`
- `masking_policy: enum`  
  `none | partial | full`
- `empty_state_label: string`

### 4.6. Evidence / external semantics

#### Required
- `is_evidence_field: boolean`
- `is_external_link: boolean`

#### Conditional
- Если `is_external_link=true`, то `data_type` должен быть `url` или `string` с `display_mode=link`.
- Если `is_evidence_field=true`, поле должно иметь понятный provenance policy на runtime-уровне.

### 4.7. Lifecycle / compatibility metadata

#### Required
- `status: enum`  
  `active | deprecated | experimental`
- `introduced_in: string`  
  Версия модели, где поле появилось.

#### Optional
- `deprecated_in: string`
- `replaced_by: string`
- `removal_after: string`
- `compatibility_notes: string`

---

## 5. Рекомендуемые дополнительные поля

Не обязательны для MVP, но полезны для зрелой модели:
- `validation_regex: string`
- `min_value: number`
- `max_value: number`
- `max_length: integer`
- `default_value: any`
- `unit: string`
- `sensitivity: enum` (`public | internal | restricted | confidential`)
- `quality_expectation: enum` (`required_for_mvp | recommended | optional`)
- `source_expectation: string[]` — только как hint, не как runtime source mapping
- `field_provenance_mode: enum` (`none | entity_level | field_level`)

---

## 6. Инварианты

1. `id` уникален в рамках модели.
2. `kind_id` обязан ссылаться на существующий `entity_kind`.
3. Для одного kind не допускаются два атрибута с одинаковым `field_id` или одинаковым runtime-назначением.
4. Если `data_type=enum`, должен быть задан либо `enum_values`, либо `enum_ref`, но не оба одновременно без явной policy.
5. Если `data_type=urn_ref`, должен быть задан `ref_kind`.
6. `display_mode=entity_ref` допустим только при `data_type=urn_ref`.
7. `display_mode=link` допустим только для `url` или явно link-like string fields.
8. Multi-valued field (`cardinality=many`) не может быть помечен как `is_sortable=true`, если явно не описано derived sort behavior.
9. `required=true` не означает, что источник всегда может его дать на MVP; это означает требование модели к каноническому объекту и должно проходить через compatibility/source coverage review.
10. Deprecated field должен иметь либо `replaced_by`, либо `compatibility_notes`.
11. Поле, помеченное как `is_external_link=true`, не должно одновременно использоваться как primary display/title field.
12. Поле, входящее в `key_attributes` kind-а, должно быть `is_exported_by_default=true`, если нет отдельного исключения.

---

## 7. Минимальная нормализованная runtime-проекция

В runtime bundle (`type_catalog.json` / metamodel snapshot) должен попадать не весь authoring payload, а нормализованный поднабор:

```json
{
  "id": "business_process.owner",
  "kind_id": "business_process",
  "name": "Owner",
  "name_ru": "Владелец",
  "description": "Ответственный владелец процесса.",
  "data_type": "urn_ref",
  "cardinality": "one",
  "required": false,
  "ref_kind": ["team", "organizational_unit"],
  "is_searchable": false,
  "is_filterable": true,
  "is_sortable": false,
  "is_facetable": true,
  "display_mode": "entity_ref",
  "is_external_link": false,
  "is_evidence_field": false,
  "status": "active"
}
```

Runtime-проекция должна быть:
- детерминированной;
- достаточной для `/v1/meta/model`, metamodel registry UI, entity card config и search/filter builder;
- независимой от внутренней структуры authoring schema.

---

## 8. Базовые паттерны атрибутов

### 8.1. Scalar attribute
Примеры:
- `it_system.status`
- `business_process.tier`
- `data_product.freshness_sla`

Признаки:
- `data_type=string|enum|integer|number|boolean|date|datetime`
- обычно `display_mode=plain|badge|date|datetime`

### 8.2. Multi-valued scalar attribute
Примеры:
- `aliases`
- `tags`
- `supported_channels`

Признаки:
- `cardinality=many`
- `display_mode=chip_list`

### 8.3. Reference attribute
Примеры:
- `data_table.business_entity_id`
- `topic.source_system_id`
- `business_process.owner`

Признаки:
- `data_type=urn_ref`
- `display_mode=entity_ref`
- clickable from entity card

### 8.4. External link attribute
Примеры:
- `confluence_url`
- `repo_url`
- `runbook_url`

Признаки:
- `is_external_link=true`
- `display_mode=link`
- открывается как external source or supporting doc

### 8.5. Structured attribute
Примеры:
- `schema_definition`
- `config_snapshot`

Признаки:
- `data_type=json`
- `display_mode=json`
- P0 использовать экономно

---

## 9. Как `attribute_def` влияет на UI и search

### Entity Card
Контракт должен позволять frontend/backend без догадок определить:
- какие поля являются ключевыми атрибутами kind-а;
- какие значения многоэлементные;
- какие поля рендерить как inline links;
- какие поля допустимо collapse/expand;
- какие поля можно показать как chips/badges.

### Search / filters
Контракт должен позволять определить:
- какие поля участвуют в search indexing;
- какие поля доступны как kind-aware filters;
- какие значения facet-friendly;
- где допустим exact search, а где full-text.

### Export
Контракт должен определять:
- какие поля экспортируются по умолчанию;
- какие поля могут требовать special serialization;
- какие поля лучше не тащить в CSV default view.

---

## 10. Примеры

### Пример 1. Reference field
```yaml
id: business_process.owner
name: Owner
name_ru: Владелец
kind_id: business_process
description: Ответственный владелец процесса.
category: organizational
data_type: urn_ref
cardinality: one
required: false
ref_kind:
  - team
  - organizational_unit
is_searchable: false
is_filterable: true
is_sortable: false
is_facetable: true
is_exported_by_default: true
display_mode: entity_ref
display_group: ownership
is_evidence_field: false
is_external_link: false
status: active
introduced_in: 2.0.0
```

### Пример 2. Enum field
```yaml
id: it_system.lifecycle_status
name: Lifecycle status
name_ru: Статус жизненного цикла
kind_id: it_system
description: Статус жизненного цикла ИТ-системы.
category: lifecycle
data_type: enum
cardinality: one
required: false
enum_values:
  - planned
  - active
  - deprecated
  - retired
is_searchable: false
is_filterable: true
is_sortable: true
is_facetable: true
is_exported_by_default: true
display_mode: badge
is_evidence_field: false
is_external_link: false
status: active
introduced_in: 2.0.0
```

### Пример 3. External link field
```yaml
id: it_system.runbook_url
name: Runbook URL
name_ru: Ссылка на runbook
kind_id: it_system
description: Ссылка на внешний runbook или operational guide.
category: evidence
data_type: url
cardinality: one
required: false
is_searchable: false
is_filterable: false
is_sortable: false
is_facetable: false
is_exported_by_default: true
display_mode: link
is_evidence_field: true
is_external_link: true
status: active
introduced_in: 2.0.0
```

---

## 11. Связанные контракты

- [Entity Kind Contract](entity_kind_contract_v2.md)
- [Relation Kind Contract](relation_kind_contract_v2.md)
- [Qualifier Definition Contract](qualifier_def_contract_v2.md)
- [Glossary и Naming Policy](glossary_alias_naming_policy.md)

