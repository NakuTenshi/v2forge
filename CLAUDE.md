# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

A single Python script (`collect.py`) that harvests v2ray proxy configs (vmess/vless/trojan/ss/hysteria/etc.) from a list of `raw.githubusercontent.com` subscription URLs, then filters them down to reachable servers by opening a TCP connection to each parsed `address:port`. Surviving configs are appended to `./configs/configs.txt`.

It is not a library, framework, or app — it is one script plus data files. There is no test suite, no lint config, and no build step.

## Commands

```bash
pip3 install -r requirements.txt   # dependencies (python_v2ray, requests, PySocks)
python3 collect.py                # run the collector
```

After a run, split the output for the mobile v2ray client (configs > 1000 are awkward to import):

```bash
split -l 1000 -d --additional-suffix=.txt configs/configs.txt config_
```

There are no tests and no linter configured. To validate changes, run `python3 collect.py` and confirm `./configs/configs.txt` grows; `errors.log` captures unhandled exceptions from worker threads.

## Architecture / how the script works

`collect.py` is ~75 lines with one worker function and an `__main__` block. The flow:

1. **Load+dedupe sources**: `sources.txt` is read line-by-line, deduped with `set()`. One URL per line, must be a `raw.githubusercontent.com` plain-text subscription (each line = one config URI). `raw_sources.txt` is a separate, larger backlog of not-yet-validated URLs and is **not** read by the script — it's only a holding pen for candidates to promote into `sources.txt`.
2. **Per-source threads**: one `threading.Thread` is spawned **per URL** (no thread pool, no cap — all launch concurrently). Each thread runs `testSubscriptionConfigs(sub_url)`.
3. **Fetch**: `requests.get(sub_url, stream=True)`; on `status_code == 200`, iterate `response.iter_lines()` and decode each line. Lines starting with `#` are skipped (subscription metadata/comments).
4. **Parse**: `python_v2ray.config_parser.parse_uri(config_uri)` returns a `ConfigParams` (has `.address`, `.port`) or `None` for unsupported protocols / malformed URIs. Supported protocol schemes: `vless, mvless, vmess, trojan, ss, socks, wireguard, hysteria, hysteria2, hy2`. `None` results are silently dropped — that is the skip path, not an error.
5. **Liveness probe**: open a plain TCP socket to `(address, port)` with a **2.0s timeout**. On successful `connect()`, the raw config line is appended to `./configs/configs.txt`. The socket is closed via the `with` block. Note this only verifies the TCP port answers — it does not validate TLS, the protocol handshake, or that the server actually proxies; many false positives survive.
6. **Skip handling**: `TimeoutError`, `socket.gaierror` (DNS fail), `ConnectionRefusedError`, and `OSError` (no route / parse-derived address) are each swallowed with `continue`. The commented-out `ChunkedEncodingError` handler is the current uncommitted edit — that exception currently kills the worker thread for that source (see `errors.log`), so be aware that a truncated download aborts collection from that URL mid-stream.

Shared mutable state uses module-level `globals` (`x`, `sources_done_length`, `sources_length`) rather than arguments or a queue:
- `sources_length` / `sources_done_length` are incremented/printed from worker threads to report `(done/total)` progress — **not thread-safe** (Python GIL makes the individual ops atomic, but the increment-then-print is a read-modify-write race). Preserve this shape if editing rather than "fixing" unless asked.
- `sources_done_length += 1` happens only on the HTTP 200 path; sources that return non-200 silently never report done and skew the progress counter.

The `project_id` display label is derived by splitting the URL on `/` and taking indices `[3]`/`[4]` — this assumes the `raw.githubusercontent.com/{owner}/{repo}/...` shape. URLs not matching this shape produce a broken `project_id` (and index `[3]/[4]` may raise).

### File roles (root-relative paths matter)

The script uses relative paths (`sources.txt`, `./configs/configs.txt`) — it **must be run from the repo root** or it will either fail to find sources or write configs to the wrong tree.

- `sources.txt` — validated subscription URLs the script reads (required; missing → exit).
- `raw_sources.txt` — backlog of unvalidated URLs; **not** consumed by code.
- `./configs/` — created if missing; `configs.txt` is the script's append-only output (gitignored).
- `errors.log` — unhandled worker-thread exceptions (gitignored).
- `requirements.txt` — pins `python_v2ray==0.1.8`; this is the parser the whole script depends on. Other pins (`grpcio`, `protobuf`) are transitive deps of `python_v2ray`.

## Conventions to follow

- `sources.txt` entries must be `raw.githubusercontent.com` URLs pointing at *plain-text* config lists (one URI per line), not HTML blob pages. `raw_sources.txt` contains both `github.com/.../blob/...` links and raw URLs mixed together — that's why it's unvalidated.
- Keep the external behavior (one-thread-per-source, append-only output to `./configs/configs.txt`, 2s TCP probe) intact unless an edit explicitly targets it.
- README.md is English; README_FA.md is the Persian translation. Keep them in sync when documenting user-facing changes.
