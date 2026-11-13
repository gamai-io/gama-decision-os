# Examples

- `python_decide.py` — call Gate 1, Gate 2 and Gate 3 directly.
- `serve_decision.py` — minimal stdlib HTTP wrapper exposing `POST /decide`.
- `curl_decide.sh` — two curl calls against the wrapper.

```bash
python3 -m pip install -e .
python3 examples/python_decide.py

python3 examples/serve_decision.py &
./examples/curl_decide.sh
```
