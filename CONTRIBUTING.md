# Contributing

Thanks for taking a look at AffixIO NeMo Plugin.

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests -q
python -m ruff check affixio_nemo tests
```

## Pull Requests

Keep changes focused. Include tests for behaviour changes. Do not commit API keys, credentials, customer data, generated virtual environments or local build caches.
