# Repository Guidelines

## Project Structure & Module Organization
- `gaiya/core`, `gaiya/ui`, and `gaiya/utils` hold desktop logic, Qt flows, and shared helpers; add modules here and expose via `__init__.py` only for shared APIs.
- `api/` hosts Supabase serverless functions and managers; match existing `auth-*` or `payment-*` prefixes when extending endpoints.
- `scripts/diagnostics` and `scripts/generators` store developer tooling; follow the existing `check_*`, `diagnose_*`, and `create_*` patterns.
- `tests/` splits coverage into `unit/`, `integration/`, and `fixtures/`; migrate legacy scripts per `tests/README.md` before promotion.
- Built artifacts land in `dist/` and `build/`; keep them out of version control.

## Build, Test, and Development Commands
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
pip install -r api/requirements.txt
pytest tests
pyinstaller --clean --noconfirm Gaiya.spec
.\build.bat | .\build_onefile.bat
```

## Coding Style & Naming Conventions
- Target Python 3.8+, four-space indentation, and the line widths used in `gaiya/`; keep type hints and docstrings consistent with current modules.
- Use snake_case for modules (`membership_ui.py`), CamelCase for Qt widgets, and prefix async helpers with their service tag (for example, `quota_*`).
- Run `python -m black gaiya api scripts` and resolve lint warnings before opening a PR.

## Testing Guidelines
- Prefer `pytest` and place new unit cases in `tests/unit` with `TestClass` wrappers; reuse or extend fixtures under `tests/fixtures`.
- Aim for >60% coverage across `gaiya/core` and >90% for tooling modules; record regression repro steps alongside new tests.
- Add `tests/integration` scenarios for Supabase flows and document required environment variables in the test docstring.

## Commit & Pull Request Guidelines
- Follow the Conventional Commits pattern (`feat(ui): ...`, `fix(api): ...`, `docs:`); keep subjects <=72 characters and explain the "why" for non-trivial changes.
- Each PR needs a summary, linked issue, validation notes (`pytest`, `build_onefile.bat`), and screenshots for UI-visible updates.
- Request at least one review when touching `gaiya/core` or release assets and update `CHANGELOG.md` for user-facing changes.

## Agent Communication
- 所有与贡献者或用户的互动必须使用中文回复，保持专业、简洁且面向行动的语气。
- 自动化提示或脚本输出同样优先提供中文注释与说明，除非第三方工具强制要求英文。

## Security & Configuration Tips
- Store secrets in `.env` files excluded from git; never hard-code credentials in `api/` scripts.
- Keep `config.json`, `tasks.json`, and `statistics.json` outside `dist/` before running the build scripts—`build.bat` and `build_onefile.bat` wipe that directory.