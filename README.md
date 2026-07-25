# v2forge
<a href="https://github.com/NakuTenshi/v2ray_config_collector/blob/main/README_FA.md">فارسی</a> · <a href="https://github.com/NakuTenshi/v2ray_config_collector/blob/main/README_RU.md">Русский</a>

The `v2forge.py` script collects v2ray configs (vmess/vless/trojan/ss/hysteria/etc.) from verified `raw.githubusercontent.com` subscription sources, parses them with `python_v2ray`, and filters down to reachable servers via TCP handshake. Surviving configs are saved to `./configs/configs.txt`.

## How to use

Clone this repository:

```bash
git clone https://github.com/NakuTenshi/v2ray_config_collector
cd v2ray_config_collector
```

Install requirements:

```bash
pip3 install -r requirements.txt
```

Run the script:

```bash
python3 v2forge.py
```

## How it works

1. Reads source URLs from `sources.txt` (87 verified sources)
2. Spawns one thread per source to fetch configs concurrently
3. Parses each line with `python_v2ray.config_parser.parse_uri()`
4. Tests reachability with a TCP handshake (2s timeout)
5. Appends reachable configs to `./configs/configs.txt`

### Supported protocols

`vmess` · `vless` · `trojan` · `shadowsocks` · `socks` · `wireguard` · `hysteria` · `hysteria2` · `hy2`

## Note

> `sources.txt` must be in the same directory as `v2forge.py`

> To add your own sources, simply append a URL to `sources.txt` (one URL per line, must point to a plain-text config list on `raw.githubusercontent.com`)

> Unhandled exceptions from worker threads are logged to `errors.log`

## Tips

After collecting, if you have more than 1000 configs (awkward to import on mobile), split the output:

```bash
split -l 1000 -d --additional-suffix=.txt configs/configs.txt config_
```

Output:

```text
config_00.txt  config_01.txt  config_02.txt  config_03.txt
```
