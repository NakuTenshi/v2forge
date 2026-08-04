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

def rebrand_config(config: str) -> str:
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
configs_hashes = set()

def hash_config(config: str, parsed=None) -> str:
    if parsed:
        canonical = f"{parsed.protocol}://{parsed.address}:{parsed.port}/{parsed.path or ''}"
    else:
        parsed = parse_uri(config_uri=config)
        if parsed:
            canonical = f"{parsed.protocol}://{parsed.address}:{parsed.port}/{parsed.path or ''}"
        else:
            canonical = config.split("#")[0]
    return hashlib.md5(canonical.encode()).hexdigest()

def load_existing_configs():
    """Preload configs already in the file so previous runs aren't re-added."""
    path = "./configs/configs.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    configs_hashes.add(hash_config(line))


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
                                config_hash = hash_config(config, parsed_config)
                                if config_hash not in configs_hashes:
                                    configs_hashes.add(config_hash)
                                    saved = rebrand_config(config)
                                    with open("./configs/configs.txt", "a") as f:
                                        f.write(f"{saved}\n")

                            except TimeoutError: # timeout
                                continue
                            except socket.gaierror: # could not resolve the domain
                                continue
                            except ConnectionRefusedError: # connection refuss
                                continue
                            except OSError: # No route to host (parsing problem)
                                continue

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


        load_existing_configs()
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
