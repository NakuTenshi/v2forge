import os
import sys
import json
import ctypes
import base64
import socket
import logging
import requests
import threading
from python_v2ray.config_parser import parse_uri

logging.disable(logging.WARNING)

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
                                with open("./configs/configs.txt", "a") as f:
                                    f.write(f"{config}\n")

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
