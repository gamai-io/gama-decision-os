# Contributing

Thanks for your interest in GAMA Decision OS.

## Development setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[test]"
python3 -m pytest tests/ -q
```

## Ground rules

- The core must stay dependency-free at runtime (standard library only).
- Every behavioral change needs a test. Prefer small, focused tests.
- Do not commit secrets, credentials, private endpoints or customer data.
- Keep the public core and the enterprise layer separate.

## Pull requests

1. Open an issue describing the problem or proposal.
2. Keep changes scoped; avoid unrelated reformatting.
3. Run `python3 -m pytest tests/ -q` before opening a PR.
4. Describe the risk tier of the change (especially anything touching `decide_tool` or `verify_evidence`).

## Security issues

Do **not** open a public issue. Follow [`SECURITY.md`](SECURITY.md).
