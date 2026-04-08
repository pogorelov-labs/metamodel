# Agents — Metamodel Repository

Instructions for AI coding agents (Claude Code, Codex, Cursor, Windsurf, etc.) working with this repository.

## Project Overview

Upstream ontology repository for RBank Atlas. Contains canonical YAML definitions of entity kinds, relation kinds, qualifiers, and attribute definitions. Changes here propagate to all downstream systems (API, MCP, UI, ingestion).

## Key Paths

| Path | Purpose |
|------|---------|
| `model/metamodel.yaml` | **core ontology**: entity kinds, dictionaries, attribute_defs, base relation_kinds |
| `model/relation_catalog.yaml` | **profile overlay**: enriched relations with UI, traversal, qualifiers, impact |
| `model/schema/` | JSON Schema validation contracts |
| `model/templates/` | Templates for new entity/relation kinds |
| `model/profiles/` | Projection profiles (e.g. `atlas_mvp`) |
| `tools/wave1/` | Validation harness, loader, validators, generators |
| `tools/migrations/` | One-shot data migration scripts (e.g. MACWO-512 cleanup) |
| `docs/architecture/` | v2 contracts (entity_kind, relation, qualifier, attribute_def) |
| `docs/decisions/` | Architecture Decision Records |
| `generated/` | Immutable release bundles — **do not edit** |

## Commands

```bash
make validate    # Full validation harness — 5 stages, all must be 0 errors
make test        # Unit tests (pytest)
make bundle      # Generate Atlas bundle into generated/
make diff        # Show bundle diff vs current baseline
make help        # All available commands
```

Or directly:

```bash
python -m tools.wave1.harness model/metamodel.yaml \
  --relation-catalog-path model/relation_catalog.yaml

# Inspect individual stages:
python -m tools.wave1.schema_validator      # JSON Schema on metamodel.yaml
python -m tools.wave1.contract_validator    # mm/rc two-layer contract

pytest tests/
```

## Two-layer mm/rc contract

`metamodel.yaml` and `relation_catalog.yaml` are not independent sources — they form a layered contract that the harness enforces:

1. **Rule 1** — every relation in catalog must have a relation_kind in mm (lookup by id).
2. **Rule 2** — `from_kind`, `to_kind`, `category`, `direction` must agree across both files.
3. **Rule 3** — relation_kinds in mm without a catalog overlay are allowed (warning only).

Practical implication: when adding a new relation, **start with metamodel.yaml** (the core declaration), then enrich it in `relation_catalog.yaml`. CI will reject catalog-only relations.

See [`model/README.md`](model/README.md) for the full contract description and field-level split.

## Conventions

- Model language: Russian field labels, English identifiers (`id`, `from_kind`, etc.)
- Two canonical YAML files (`metamodel.yaml` + `relation_catalog.yaml`) — see contract above
- All changes must pass `make validate` (5 stages, 0 errors) before merge
- Lifecycle status values: `active`, `draft`, `experimental`, `deprecated`, `stub` (`stub` = declared but unfinished, e.g. zero attributes)
- Migrations live in `tools/migrations/` as idempotent Python scripts referencing the MACWO id
- Contribution guide: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- `generated/` is immutable output — never hand-edit

---

## Local RAG — Semantic Search over Documentation

This repo includes a local vector search index powered by [mcp-local-rag](https://github.com/shinpr/mcp-local-rag). It enables semantic search over architecture contracts, decision records, and contribution rules without sending data to external services.

### What is indexed

| Content | Why |
|---------|-----|
| `docs/` (architecture contracts, ADRs, audits) | Core knowledge base |
| `README.md` | Project overview and quick start |
| `CONTRIBUTING.md` | Step-by-step guides for model changes |

**Not indexed** (format limitations): YAML model files, Python code. Use standard file search / grep for those.

### Installation

#### 1. MCP server (Claude Code)

Create `.claude/settings.local.json` (this file is gitignored):

```json
{
  "mcpServers": {
    "local-rag": {
      "command": "npx",
      "args": ["-y", "mcp-local-rag"],
      "env": {
        "BASE_DIR": "<absolute-path-to-metamodel>",
        "DB_PATH": "<absolute-path-to-metamodel>/.claude/lancedb",
        "CACHE_DIR": "~/.cache/mcp-local-rag/models"
      }
    }
  }
}
```

Replace `<absolute-path-to-metamodel>` with your actual path.

#### 2. Build the index (first time only)

```bash
cd /path/to/metamodel

npx -y mcp-local-rag --db-path .claude/lancedb ingest ./docs/
npx -y mcp-local-rag --db-path .claude/lancedb ingest ./README.md
npx -y mcp-local-rag --db-path .claude/lancedb ingest ./CONTRIBUTING.md
```

First run downloads the embedding model (~90 MB, cached in `~/.cache/mcp-local-rag/models/`).

#### 3. Verify

```bash
npx -y mcp-local-rag --db-path .claude/lancedb status
# Expected: ~1200 chunks, 21 documents

npx -y mcp-local-rag --db-path .claude/lancedb query "business layer architecture"
# Should return results from business_layer_semantic_alignment.md
```

#### 4. Skills (Claude Code only)

Skills are pre-installed in `.claude/skills/mcp-local-rag/`. They teach the agent how to formulate queries, interpret scores, and pick the right tool. No action needed — they load automatically.

To reinstall or update:

```bash
npx -y mcp-local-rag skills install --claude-code
```

### Re-indexing

Re-run `ingest` after adding or editing documentation:

```bash
npx -y mcp-local-rag --db-path .claude/lancedb ingest ./docs/architecture/new_contract.md
```

Re-ingesting an already indexed file replaces the old chunks automatically.

### MCP Tools

When the MCP server is running, these tools are available to the agent:

| Tool | Purpose |
|------|---------|
| `query_documents` | Semantic + keyword hybrid search |
| `ingest_file` | Add a local file to the index |
| `ingest_data` | Index raw HTML/text/markdown content with source URL |
| `list_files` | Show all indexed documents and their chunk counts |
| `delete_file` | Remove a file from the index |
| `status` | Database statistics (document count, chunk count) |

### CLI fallback

All tools work via CLI without a running MCP server:

```bash
npx -y mcp-local-rag --db-path .claude/lancedb query "qualifier definition rules"
npx -y mcp-local-rag --db-path .claude/lancedb list
npx -y mcp-local-rag --db-path .claude/lancedb status
npx -y mcp-local-rag --db-path .claude/lancedb delete ./docs/old_file.md
```

### When to use RAG vs file search

| Need | Use |
|------|-----|
| "What are the rules for qualifier definitions?" | RAG (`query_documents`) |
| "Find the file that defines `business_operation`" | grep / glob |
| "How does the business layer relate to data layer?" | RAG |
| "What's the schema for `entity_kind`?" | Read `model/schema/` directly |
| "Show me the YAML for `application_system`" | Read `model/metamodel.yaml` directly |

### Score interpretation

RAG returns distance scores (lower = better match):

| Score | Quality |
|-------|---------|
| < 0.3 | High confidence — use directly |
| 0.3 — 0.5 | Good — include if topic matches |
| 0.5 — 0.7 | Marginal — include only if directly relevant |
| > 0.7 | Noise — skip |

### Storage (gitignored)

| Path | Contents | In git? |
|------|----------|---------|
| `.claude/lancedb/` | Vector database | No |
| `.claude/settings.local.json` | MCP server config (user-specific paths) | No |
| `.claude/skills/mcp-local-rag/` | Agent skills | Yes |
