# v2forge
<a href="https://github.com/NakuTenshi/v2ray_config_collector/">English</a> · <a href="https://github.com/NakuTenshi/v2ray_config_collector/blob/main/README_FA.md">فارسی</a>

Скрипт `v2forge.py` собирает конфиги v2ray (vmess/vless/trojan/ss/hysteria и др.) из проверенных источников подписок на `raw.githubusercontent.com`, парсит их с помощью `python_v2ray` и фильтрует доступные серверы через TCP handshake. Сохранённые конфиги записываются в `./configs/configs.txt`.

## Как использовать

Клонируйте репозиторий:

```bash
git clone https://github.com/NakuTenshi/v2ray_config_collector
cd v2ray_config_collector
```

Установите зависимости:

```bash
pip3 install -r requirements.txt
```

Запустите скрипт:

```bash
python3 v2forge.py
```

## Как это работает

1. Читает URL-ы источников из `sources.txt` (87 проверенных источников)
2. Создаёт один поток на каждый источник для параллельной загрузки конфигов
3. Парсит каждую строку через `python_v2ray.config_parser.parse_uri()`
4. Проверяет доступность через TCP handshake (тайм-аут 2 сек)
5. Добавляет доступные конфиги в `./configs/configs.txt`

### Поддерживаемые протоколы

`vmess` · `vless` · `trojan` · `shadowsocks` · `socks` · `wireguard` · `hysteria` · `hysteria2` · `hy2`

## Примечание

> Файл `sources.txt` должен находиться в той же директории, что и `v2forge.py`

> Чтобы добавить свои источники, просто допишите URL в `sources.txt` (по одному URL на строку, должен указывать на текстовый список конфигов на `raw.githubusercontent.com`)

> Необработанные исключения из потоков записываются в `errors.log`

## Советы

После сборки, если конфигов больше 1000 (неудобно импортировать на телефон), разделите вывод:

```bash
split -l 1000 -d --additional-suffix=.txt configs/configs.txt config_
```

Результат:

```text
config_00.txt  config_01.txt  config_02.txt  config_03.txt
```
