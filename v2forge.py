import os
import sys
import json
import random
import ctypes
import base64
import hashlib
import socket
import logging
import requests
import threading
from python_v2ray.config_parser import parse_uri

_REMARK_EMOJIS = ["🧩", "✂️", "🔀", "🛡️", "🕵️", "🎭", "🚀", "⚡", "📡", "🌐", "🔒", "🔐", "🌊", "🔥", "🛸", "🐉", "🧬", "🌀", "☁️", "🦄"]
_REMARK_NAME = "Telegram: @nakutenshii"

def _rebrand_config(config: str) -> str:
    """Replace fragment/remark with random emoji + @nakutenshii.
    Uses parse_uri to identify protocol, then handles vmess (ps inside base64)
    and other protocols (#fragment) separately."""
    parsed = parse_uri(config_uri=config)
    if not parsed:
        return config

    emoji = random.choice(_REMARK_EMOJIS)
    new_remark = f"{emoji}{_REMARK_NAME}"

    if parsed.protocol == "vmess":
        try:
            encoded_part = config.replace("vmess://", "").split("#")[0]
            decoded = json.loads(base64.b64decode(encoded_part + "==").decode("utf-8"))
            decoded["ps"] = new_remark
            new_encoded = base64.b64encode(json.dumps(decoded, separators=(",", ":")).encode()).decode().rstrip("=")
            return f"vmess://{new_encoded}#{new_remark}"
        except Exception:
            return config.split("#")[0] + f"#{new_remark}"
    else:
        return config.split("#")[0] + f"#{new_remark}"

logging.disable(logging.WARNING)

# --- Dedup state (hash-based for low memory) ---
_configs_lock = threading.Lock()
_configs_hashes = set()

def _hash_config(config: str, parsed=None) -> str:
    """Hash config using parsed address+port+protocol for dedup.
    Accepts pre-parsed result to avoid double-parsing.
    Ignores remark/fragment and handles base64-encoded configs."""
    if parsed:
        canonical = f"{parsed.protocol}://{parsed.address}:{parsed.port}"
    else:
        parsed = parse_uri(config_uri=config)
        if parsed:
            canonical = f"{parsed.protocol}://{parsed.address}:{parsed.port}"
        else:
            canonical = config.split("#")[0]
    return hashlib.sha256(canonical.encode()).hexdigest()

def _load_existing_configs():
    """Preload configs already in the file so previous runs aren't re-added."""
    path = "./configs/configs.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    _configs_hashes.add(_hash_config(line))

def _add_config_if_new(config: str, parsed=None) -> bool:
    """Add config to file only if not already seen. Returns True if added.
    Saves the rebranded version (random emoji + @nakutenshii as fragment).
    Dedup is based on the original config before rebranding.
    Accepts pre-parsed result to avoid double-parsing."""
    h = _hash_config(config, parsed)
    with _configs_lock:
        if h in _configs_hashes:
            return False
        _configs_hashes.add(h)
        saved = _rebrand_config(config)
        with open("./configs/configs.txt", "a") as f:
            f.write(f"{saved}\n")
        return True

def testSubscriptionConfigs(sub_url):
    global x , sources_done_length, sources_length
    
    project_id = f'{sub_url.split("/")[3]}/{sub_url.split("/")[4]}'

    try:
        response = requests.get(sub_url, stream=True)
    except requests.exceptions.RequestException:
        return

    if response.status_code == 200:
        try:
            lines = response.iter_lines()
            for config in lines:
                config = config.decode()

                if not config.startswith("#"):
                    parsed_config = parse_uri(config_uri=config)

                    if parsed_config:
                        addr_port = (parsed_config.address, parsed_config.port)
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                            client.settimeout(2.0)
                            try:
                                client.connect(addr_port)
                                _add_config_if_new(config, parsed_config)

                            except TimeoutError: # timeout
                                continue
                            except socket.gaierror: # could not resolve the domain
                                continue
                            except ConnectionRefusedError: # connection refuss
                                continue
                            except OSError: # No route to host (parsing problem)
                                continue

                            # except requests.exceptions.ChunkedEncodingError:
                            #     continue
        except requests.exceptions.ChunkedEncodingError:
            # the source server dropped the chunked transfer mid-stream;
            # keep whatever configs we already collected from this source.
            pass

        sources_done_length += 1
        print(f"[INFO] ({sources_done_length}/{sources_length}) {project_id} is done.")                       


if __name__ == "__main__":
    try:
        if not os.path.exists("sources.txt"):
            print("sources.txt doesn't find")
            exit()
        
        if not os.path.exists("./configs"):
            os.mkdir("./configs")

        _load_existing_configs()


        with open("sources.txt" , "r") as f:
            source_urls = f.readlines()
            source_urls = list(set(source_urls))

        sources_length = len(source_urls)
        sources_done_length = 0

        print(f"[INFO] Colecting from {sources_length} sourcess")
        for url in source_urls:
            url = url.strip()
            threading.Thread(target=testSubscriptionConfigs, args=[url]).start()
    except KeyboardInterrupt:
        print("bye")
