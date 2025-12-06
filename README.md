# py-zontium

Python библиотека и CLI для управления устройствами ZONT через официальное API. Вдохновлено интерфейсом [`ya-whatsminer-cli`](https://github.com/iaon/ya-whatsminer-cli).

## Содержание / Table of Contents
- [Установка / Installation](#установка--installation)
- [Конфигурация / Configuration](#конфигурация--configuration)
- [Использование CLI / CLI Usage](#использование-cli--cli-usage)
- [Python API](#python-api)
- [Тесты / Tests](#тесты--tests)

## Установка / Installation
```bash
python -m pip install .
# или / or
python -m pip install .[dev]
```

## Конфигурация / Configuration
Сначала возьмите один из примеров конфигурации и подставьте свой токен:

- `examples/config.example.yaml`
- `examples/config.example.json`

Затем сохраните итоговый файл как `~/.config/zontium/config.yaml` (или укажите свой путь через `--config`). Файл может быть в YAML или JSON формате. CLI проверяет наличие токена и использует его в заголовке `Authorization: Bearer <token>`. Опциональное поле `verbose: true` включает вывод исходящих запросов. Получить токен можно через API:

```bash
# Вернет свежий токен без необходимости существующего конфига
zontium get-authtoken <login> <password>
```

## Использование CLI / CLI Usage

```bash
# Показать информацию о конфигурации / Show configuration
zontium show-config

# Включить вывод запросов / Enable request logging
zontium --verbose user

# Получить данные учетной записи / Get account data
zontium user

# Список устройств / List devices
zontium devices

# Информация об устройстве / Device details
zontium device <device_id>

# История устройства / Device history
zontium history <device_id> --from 1710000000 --to 1710003600

# Выполнение действия над устройством / Perform device action
zontium action <device_id> set_relay --payload '{"relay":1,"state":"on"}'

# Произвольный запрос к API / Arbitrary API call
zontium request POST devices/123/custom --payload '{"value": 1}'

# Запросить новый токен / Request new token
zontium get-authtoken login password
```

## Python API

```python
from zontium import ZontClient, load_settings

settings = load_settings()  # берет настройки из ~/.config/zontium/config.yaml
with ZontClient(settings) as client:
    me = client.get_user()
    devices = client.list_devices()
    history = client.get_device_history(devices["items"][0]["id"], from_ts=1710000000)
```

Основные методы:
- `get_user()` — информация о текущем аккаунте
- `list_devices()` — список устройств
- `get_device(device_id)` — описание устройства
- `get_device_history(device_id, from_ts=None, to_ts=None)` — исторические данные
- `execute_action(device_id, action, payload)` — выполнить действие
- `call_raw(method, path, params=None, payload=None)` — произвольный HTTP-запрос

## Тесты / Tests

```bash
python -m pip install .[dev]
pytest
```

CI запускает тесты автоматически через GitHub Actions.
