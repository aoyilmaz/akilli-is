# Copilot / AI agent instructions — Akıllı İş

This file contains concise, actionable guidance for AI coding agents working in this repository.

1. Big picture

- Desktop PyQt6 application (single-process GUI) launched from [main.py](main.py). UI is componentized into "modules" under the `modules/` package (e.g. `modules/inventory`).
- Data layer: SQLAlchemy models live in `database/models/`; connection/session helpers and base models are in [database/base.py](database/base.py). Migrations are in `alembic/`.
- Configuration: runtime configuration and paths are in [config/settings.py](config/settings.py). Environment variables drive DB credentials and AI keys (`.env`).

2. Key workflows (how to run / develop)

- Setup: use the project script `setup.sh` (macOS) which creates `.venv`, installs `requirements.txt`, and copies `.env.example` → `.env`.
- Database: create DB (`createdb akilli_is`) then initialize schema with `python init_db.py` (calls `database.init_database`). Alembic migrations live under `alembic/versions`.
- Run: activate virtualenv then `python main.py` to start the GUI. `main.py` loads UI theme from `ui/themes/*.qss`.

3. Project-specific patterns and conventions

- Module pattern: each feature lives in `modules/<name>/` with `module.py` (QWidget container), `services.py` (data access/business logic), and `views/` (Qt pages/forms). See `modules/inventory/module.py` for a canonical example.
- Services: service classes lazily open DB sessions and expose `close()` — call `close()` after use. Modules call `_get_services()` and `_close_services()` for lifecycle management.
- UI messages: errors are surfaced via `QMessageBox` (Turkish messages throughout). Keep string locale in mind when editing text.
- Database helpers: use `get_session()` from `database/base.py` and model mixins (`BaseModel`, `TimestampMixin`, `SoftDeleteMixin`) — prefer model `to_dict()` when serializing.
- Configuration constants: UI constants (theme, font) are in `config/settings.py` under the `UI` dict; reference these rather than hardcoding values in widgets.

4. Integration points & external dependencies

- Desktop: depends on `PyQt6` (see `requirements.txt`).
- DB: `psycopg2-binary` for PostgreSQL; `get_database_url()` supports `postgresql`, `sqlite`, and `mysql`.
- Secrets: AI integration keys (e.g. `ANTHROPIC_API_KEY`) and `AI_MODEL` live in `.env` / `config/settings.py`.

5. When you edit or add code

- To add a new module: create `modules/<name>/module.py`, `services.py`, and `views/` following the inventory module pattern. Export the module from `modules/__init__.py` to make it discoverable.
- Database model changes: add models under `database/models/` and create an Alembic migration under `alembic/versions/`.
- UI changes: modify `ui/themes/*.qss` for styling; `ui/main_window.py` composes module widgets into the main app frame.

6. Helpful file references (examples)

- App entry: [main.py](main.py)
- Installer script: [setup.sh](setup.sh)
- Config: [config/settings.py](config/settings.py)
- DB base and session: [database/base.py](database/base.py)
- DB models: [database/models/](database/models/)
- Inventory example: [modules/inventory/module.py](modules/inventory/module.py)
- UI: [ui/main_window.py](ui/main_window.py) and `ui/themes/dark.qss`

7. Known inconsistencies to watch for

- README states Python 3.9+ but `setup.sh` enforces Python 3.11+. Prefer `setup.sh` when preparing dev environments.
- Strings are Turkish; PRs that change UI text should preserve or update localization consistently.

8. What the AI should NOT do

- Do not modify `.env` files or commit secrets. Do not change database credentials in `config/settings.py` — use environment overrides.
- Avoid long-running blocking operations on the main thread; UI code must keep the Qt event loop responsive.

9. Suggested first tasks for an agent

- Small: add a missing import or fix linter errors in a module.
- Medium: implement a new `views` page following `StockListPage` / `StockFormPage` patterns.
- Large: add a migration to `alembic/versions` and update `database/models/` + `init_db.py` default data if schema changes.

If any section is unclear or you want more examples (e.g. a concrete service implementation or a template for new modules), tell me which area and I will expand the file.
