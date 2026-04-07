# CI/CD Standard

## Purpose

This document defines the CI/CD pipeline standard for AIBooster+ GenAI repositories. It is based on the pipeline implemented in `aib-genai-agent-core-session-manager` and `aib-genai-ml-context`, and serves as the reference implementation for all new repositories.

---

## 1. Pipeline Structure

Every repository must have a `.gitlab-ci.yml` at the repo root. Pipelines must define three stages in the following order:

```yaml
stages:
  - build
  - verify
  - security
```

| Stage | Purpose |
| --- | --- |
| `build` | Dependency resolution and graph generation |
| `verify` | Lint and test — runs in parallel |
| `security` | Vulnerability scanning of dependencies |

### 1.1 Required Jobs

| Job | Stage | Required |
| --- | --- | --- |
| `dependency-graph` | `build` | Yes |
| `lint` | `verify` | Yes |
| `test` | `verify` | Yes |
| `pip-audit` | `security` | Yes |

---

## 2. Runner Image

All jobs must use the official `python:3.12-slim` image unless a specific job requires otherwise. Declare it as the pipeline-level default:

```yaml
default:
  image: python:3.12-slim
```

---

## 3. Private Dependency Authentication

Repositories with private GitLab dependencies in `requirements.txt` (installed via `git+https://gitlab.com/...`) must authenticate using `CI_JOB_TOKEN` via git URL rewriting. Declare the following at the top-level `variables` block:

```yaml
variables:
  PIP_ROOT_USER_ACTION: ignore
  GIT_CONFIG_COUNT: "1"
  GIT_CONFIG_KEY_0: "url.https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.com/.insteadOf"
  GIT_CONFIG_VALUE_0: "https://gitlab.com/"
```

`PIP_ROOT_USER_ACTION: ignore` suppresses pip's root-user warning (pipeline containers run as root).

`CI_JOB_TOKEN` is injected automatically by GitLab — do not define it manually or store it as a CI/CD variable.

---

## 4. Job Definitions

### 4.1 Shared Install Anchor

Define a YAML anchor for the common `before_script` used by `lint` and `test`:

```yaml
.install: &install
  before_script:
    - apt-get update -qq && apt-get install -y --no-install-recommends make git
    - pip install --quiet --upgrade pip
    - pip install --quiet -r requirements_dev.txt -e .
```

### 4.2 `dependency-graph`

Produces a full JSON dependency tree of production dependencies.

```yaml
dependency-graph:
  stage: build
  before_script:
    - apt-get update -qq && apt-get install -y --no-install-recommends git
  script:
    - pip install --quiet --upgrade pip pipdeptree -r requirements.txt -e .
    - pipdeptree -e pipdeptree --json > pipdeptree.json
  artifacts:
    when: on_success
    access: developer
    paths: ["**/pipdeptree.json"]
```

The `access: developer` restriction limits artifact downloads to Developer role and above in the GitLab UI.

### 4.3 `lint`

```yaml
lint:
  stage: verify
  <<: *install
  script:
    - make lint
```

`make lint` must invoke `ruff check src tests`. See §6 for ruff configuration.

### 4.4 `test`

```yaml
test:
  stage: verify
  <<: *install
  script:
    - make test
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

The `coverage` regex parses the coverage percentage from pytest-cov's terminal output and reports it in the GitLab pipeline UI.

The JUnit (`report.xml`) and Cobertura (`coverage.xml`) artifacts enable test results and diff coverage to be displayed in GitLab MR views.

### 4.5 `pip-audit`

```yaml
pip-audit:
  stage: security
  before_script:
    - apt-get update -qq && apt-get install -y --no-install-recommends git
    - pip install --quiet --upgrade pip pip-audit
    - pip install --quiet -r requirements.txt -e .
  script:
    - pip-audit --desc -r requirements.txt
```

`pip-audit` installs its own `before_script` rather than using the `.install` anchor — it only needs production dependencies, not dev tooling.

---

## 5. Makefile

Every repository must provide a `Makefile` with at minimum these targets:

```makefile
.PHONY: setup test lint format

setup:
	conda env create -f environment.yml || conda env update -f environment.yml --prune

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests
```

`format` is for local developer use only — it is not run in CI. CI only checks (via `lint`); it never auto-fixes.

---

## 6. Tool Configuration

All tool configuration must live in `pyproject.toml`. Do not create separate `ruff.toml`, `.flake8`, `setup.cfg`, or `mypy.ini` files.

### 6.1 pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--tb=short --cov=<package_name> --cov-report=term-missing --cov-report=xml --junitxml=report.xml"
markers = [
    "regression: marks tests that cover previously found bugs (deselect with '-m \"not regression\"')",
]

[tool.coverage.run]
source = ["src/<package_name>"]
branch = true

[tool.coverage.report]
fail_under = 90
show_missing = true
```

Replace `<package_name>` with the importable package name (e.g. `aib_genai_agent_core_session_manager`).

Key requirements:
- **Branch coverage** must be enabled (`branch = true`).
- **Coverage gate** must be set to a minimum of 90% (`fail_under = 90`). The pipeline fails if this threshold is not met.
- `--junitxml=report.xml` and `--cov-report=xml` are required to populate GitLab's MR test and coverage views.

### 6.2 ruff

```toml
[tool.ruff]
src = ["src"]
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "S"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]
```

| Rule set | Source | What it checks |
| --- | --- | --- |
| `E`, `W` | pycodestyle | PEP 8 style |
| `F` | pyflakes | Undefined names, unused imports |
| `I` | isort | Import ordering |
| `UP` | pyupgrade | Modernise syntax for target Python version |
| `S` | bandit | Common security issues |

`S101` (use of `assert`) is suppressed for `tests/**` because `assert` is idiomatic in pytest.

---

## 7. Dependency Management

### 7.1 File Responsibilities

| File | Purpose |
| --- | --- |
| `requirements.txt` | **Canonical runtime dependencies.** The only place to add or change runtime deps. |
| `requirements_dev.txt` | Dev and test tooling. Must start with `-r requirements.txt`. |
| `environment.yml` | Local conda environment. Must not list runtime deps directly — gets them via `-r requirements_dev.txt`. |
| `pyproject.toml` | Package metadata. Reads runtime deps dynamically from `requirements.txt` via `hatch-requirements-txt`. |

### 7.2 `pyproject.toml` — Making `requirements.txt` the Canonical Source

`pyproject.toml` must delegate runtime dependencies to `requirements.txt` using the `hatch-requirements-txt` plugin. This ensures there is exactly one place to declare runtime deps — adding `hatch-requirements-txt` to the `[build-system]` requires list and marking `dependencies` as `dynamic` is what wires this up:

```toml
[build-system]
requires = ["hatchling", "hatch-requirements-txt"]
build-backend = "hatchling.build"

[project]
name = "aib-genai-<your-package-name>"
version = "1.0.0"
description = "..."
readme = "README.md"
license = { text = "Proprietary" }
authors = [{ name = "Vodacom AI Booster Plus" }]
requires-python = ">=3.12"
dynamic = ["dependencies"]          # <-- deps come from requirements.txt, not here

[tool.hatch.metadata.hooks.requirements_txt]
files = ["requirements.txt"]        # <-- hatch-requirements-txt reads this file

[tool.hatch.metadata]
allow-direct-references = true      # <-- required for git+https:// dependencies

[project.urls]
Repository = "https://gitlab.com/vodacomsa/ai-booster-plus/..."

[tool.hatch.build.targets.wheel]
packages = ["src/<your_package_name>"]
```

The key lines:

- `dynamic = ["dependencies"]` — tells hatch not to look for a static `dependencies` list in `[project]`
- `[tool.hatch.metadata.hooks.requirements_txt]` with `files = ["requirements.txt"]` — instructs the plugin to populate `dependencies` from `requirements.txt` at build time
- `allow-direct-references = true` — required whenever `requirements.txt` contains a `git+https://` reference; without this, hatch rejects the dependency as a non-standard specifier

### 7.3 `requirements_dev.txt` — Extending Runtime Deps for Development

`requirements_dev.txt` must include runtime deps via `-r requirements.txt` so that installing dev tooling also installs the package's own runtime dependencies:

```text
-r requirements.txt
pytest>=8
pytest-cov>=5.0.0
ruff>=0.4
pip-audit>=2.7
```

Never duplicate runtime dependency entries in `requirements_dev.txt` — the `-r requirements.txt` line is the single source. Do not add `hatch-requirements-txt` here — it is a build-system plugin declared in `pyproject.toml`'s `[build-system].requires` (see §7.2) and is not needed at install time.

### 7.4 `environment.yml` — Local Conda Environment

The conda environment for local development must install all dependencies through `requirements_dev.txt`, not by listing them directly. This keeps the conda environment in sync with the pip dependency chain automatically:

```yaml
name: aib-genai-<your-package-name>
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - pip
  - pip:
    - -r requirements_dev.txt   # pulls in requirements.txt transitively
    - -e .                      # installs the package itself in editable mode
```

The full dependency chain is therefore:

```
environment.yml
  └─ requirements_dev.txt    (via -r)
       └─ requirements.txt   (via -r)
            └─ runtime deps
```

Never add runtime or dev packages directly to `environment.yml` — always add them to the appropriate `requirements*.txt` file and let `environment.yml` pick them up transitively.

### 7.5 Pinning

Always pin with `>=` (lower-bound). Never use bare names or `==` (exact pins):

```
# Good
pytest>=8
ruff>=0.4

# Bad
pytest
ruff==0.4.1
```

### 7.6 Private Dependencies

Private GitLab packages are installed via git references in `requirements.txt`:

```
aib-genai-ml-context @ git+https://gitlab.com/vodacomsa/ai-booster-plus/aib-genai/aib-genai-ml-context.git@master
```

Always pin to `@master` (or a specific tag for released dependencies). Never pin to a feature branch.

---

## 8. What Is Not in the Pipeline

The following are intentionally absent from the standard pipeline:

- **Caching** — pip installs run from scratch on each job. Acceptable for repos with few dependencies; add caching only if pipeline times become a problem.
- **Deployment** — GenAI libraries are consumed via git references, not a package registry. No publish or deploy step is required for library repos. Services with a deployment target define their own deploy stage.
- **Conditional job execution** — All jobs run on every push. No `rules:`, `only:`, or `except:` restrictions are applied by default.
- **Auto-formatting** — CI checks only. Auto-fix is a local developer action via `make format`.

---

## 9. `.gitignore` Requirements

The following generated CI artefacts must be in `.gitignore`:

```
.pytest_cache/
.coverage
coverage.xml
report.xml
```

---

## References

- [GitLab CI/CD — `.gitlab-ci.yml` reference](https://docs.gitlab.com/ci/yaml/)
- [GitLab CI/CD — Predefined variables (`CI_JOB_TOKEN`)](https://docs.gitlab.com/ci/variables/predefined_variables/)
- [GitLab CI/CD — Test reports](https://docs.gitlab.com/ci/testing/unit_test_reports/)
- [GitLab CI/CD — Coverage reports](https://docs.gitlab.com/ci/testing/code_coverage/)
- [pytest — Configuration](https://docs.pytest.org/en/stable/reference/customize.html)
- [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)
- [Ruff — Configuration](https://docs.astral.sh/ruff/configuration/)
- [pip-audit](https://pypi.org/project/pip-audit/)
- [pipdeptree](https://pypi.org/project/pipdeptree/)
- [Hatch — hatch-requirements-txt plugin](https://github.com/repo-helper/hatch-requirements-txt)
