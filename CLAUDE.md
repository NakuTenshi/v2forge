# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

v2forge is a v2ray config collector. It fetches proxy configs (vmess/vless/trojan/shadowsocks/hysteria/etc.) from 87+ sources on `raw.githubusercontent.com`, parses them, tests reachability via TCP handshake, and saves working configs to `./configs/configs.txt`.

## Commands

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the collector
python3 v2forge.py

# Split large output (1000+ configs) for mobile import
split -l 1000 -d --additional-suffix=.txt configs/configs.txt config_
```

## Architecture

Everything is in a single file: `v2forge.py` (~155 lines).

- **Config parsing**: Uses `python_v2ray.config_parser.parse_uri()` to extract protocol, address, and port from each config URI.
- **Reachability test**: Opens a raw TCP socket to each parsed `(address, port)` with a 2-second timeout. Only configs that connect are saved.
- **Deduplication**: SHA-256 hash on `protocol://address:port` before writing. Existing entries in `./configs/configs.txt` are preloaded on startup so previous runs aren't re-added.
- **Rebranding**: Before saving, each config's remark/fragment is replaced with a random emoji + `Telegram: @nakutenshii`. Vmess configs have their `ps` field inside the base64-encoded body rewritten; all other protocols use the `#fragment`.
- **Concurrency**: One thread per source URL with a global dedup set protected by `threading.Lock()`. There are no thread pools or worker limits — all threads fire immediately.
- **Error handling**: Individual socket failures (timeout, DNS resolution, connection refused, no-route) silently skip the config. Chunked encoding errors from a source preserve whatever configs were already collected from it. Unhandled exceptions in threads go to the default stderr (not captured by the global logger, which is disabled).

## Key files

| File | Purpose |
|---|---|
| `v2forge.py` | Entire application |
| `sources.txt` | 87 GitHub raw URLs (one per line), feeds the collector |
| `configs/configs.txt` | Output file (appended in-place, auto-created on first run) |
| `requirements.txt` | Python dependencies |
| `errors.log` | Runtime error log (mentioned in README, not actually written by the code) |

## Notable details

- The global logger is disabled (`logging.disable(logging.WARNING)`); output goes to `print()` only.
- Vmess configs are decoded, edited, and re-encoded with `separators=(",", ":")` (compact JSON, no spaces) — this differs from the standard padded base64, so be careful if modifying that path.
- The `.gitignore` lists `configs.txt` but the actual output path is `./configs/configs.txt` (inside the directory).