# python-dev reference

Configuration files for the rules in [SKILL.md](SKILL.md). The
workflows show tags. Run `pinact` after you copy them, as
`git-conventions` says ("CI workflows").

## .pre-commit-config.yaml

Start from the base file in the `git-conventions` reference.md
("Base pre-commit config"). Add ruff as the first repo:

```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.10
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Add `exclude: ^uv\.lock$` to the `pretty-format-toml` hook, because
uv owns that file.

## test.yaml

```yaml
name: Run tests
on:
  push:
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: "17 3 * * *"
jobs:
  fast:
    if: github.event_name == 'push' || github.event_name == 'pull_request'
    strategy:
      matrix:
        platform: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.11', '3.14']
    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install .[test]
      - run: pytest -m "not slow"
  full:
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - run: pip install .[test]
      - run: pytest
```

## docs.yaml

```yaml
name: docs
on:
  push:
    branches: [main, dev, 'dev-*']
  workflow_dispatch:
permissions:
  contents: write
concurrency:
  group: gh-pages
  cancel-in-progress: false
jobs:
  docs:
    runs-on: ubuntu-latest
    env:
      REF: ${{ github.ref_name }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .[docs]
      - run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          if [ "$REF" = main ]; then
            mike deploy --push --update-aliases main latest
            mike set-default --push latest
          else
            mike deploy --push "$REF"
          fi
```

The site root returns 404 until the first deploy from `main`. Check
and set the Pages source:

```bash
gh api repos/<owner>/<repo>/pages -q .source
gh api -X PUT repos/<owner>/<repo>/pages \
  -f 'source[branch]=gh-pages' -f 'source[path]=/'
```

## mkdocs.yml

```yaml
site_name: <package>
repo_url: https://github.com/<owner>/<repo>
strict: true
theme:
  name: material
plugins:
  - search
  - bibtex: {bib_file: docs/references.bib}
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: numpy
markdown_extensions:
  - pymdownx.snippets
extra:
  version:
    provider: mike
```
