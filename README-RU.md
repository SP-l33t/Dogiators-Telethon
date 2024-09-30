[![Static Badge](https://img.shields.io/badge/Telegram-Channel-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/+jJhUfsfFCn4zZDk0)      [![Static Badge](https://img.shields.io/badge/Telegram-Bot%20Link-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/Dogiators_bot/game?startapp=s5XexnShM18Ftejz)



## Recommendation before use

# 🔥🔥 PYTHON version must be 3.10 🔥🔥

> 🇪🇳 README in english available [here](README)

## Функционал  
|               Функционал               | Поддерживается |
|:--------------------------------------:|:--------------:|
|            Многопоточность             |       ✅        | 
|        Привязка прокси к сессии        |       ✅        | 
| Использование вашей реферальной ссылки |       ✅        |
|               Авто фарм                |       ✅        |
|        Авто выполнение заданий         |       ✅        |
|             Авто улучшения             |       ✅        |
|         Авто вращение рулетки          |       ✅        |
|    Автоматичесие ежедневная стрики     |       ✅        |
|      Поддержка telethon .session       |       ✅        |


## [Настройки](https://github.com/SP-l33t/Dogiators-Telethon/tree/main/.env-example)
|           Настройки            |                                                                                                                              Описание                                                                                                                               |
|:------------------------------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|
|     **API_ID / API_HASH**      |                                                                                         Данные платформы, с которой будет запущена сессия Telegram (по умолчанию - android)                                                                                         |
|     **GLOBAL_CONFIG_PATH**     | Определяет глобальный путь для accounts_config, proxies, sessions. <br/>Укажите абсолютный путь или используйте переменную окружения (по умолчанию - переменная окружения: **TG_FARM**)<br/> Если переменной окружения не существует, использует директорию скрипта |
|           **REF_ID**           |                                                                                                Ваш реферальный идентификатор (В реферальной ссылке после startapp= )                                                                                                |
|       **PERFORM_QUESTS**       |                                                                                                       Автоматическое выполнение заданий ( **True** / False )                                                                                                        |
|  **CHANNEL_SUBSCRIBE_TASKS**   |                                                                                                    Выполнение заданий с подпиской на каналы ( **True** / False )                                                                                                    |
|       **UPGRADE_CARDS**        |                                                                                                        Автоматическое улучшение карточек ( **True** / False)                                                                                                        |
|       **SPIN_THE_WHEEL**       |                                                                                                Автоматическое спины рулетки при наличии билетов ( **True** / False )                                                                                                |
|          **AUTO_TAP**          |                                                                                                              Автоматически тапать ( **True** / False )                                                                                                              |
|     **RANDOM_SLEEP_TIME**      |                                                                                                         Случайный интервал времени на сон ( [3600, 10800] )                                                                                                         |
| **RANDOM_SESSION_START_DELAY** |                                                                                           Случайная задержка при запуске. От 1 до указанного значения (например, **30**)                                                                                            |
|     **SESSIONS_PER_PROXY**     |                                                                                            Количество сессий, которые могут использовать один и тот же прокси ( **1** )                                                                                             |
|    **USE_PROXY_FROM_FILE**     |                                                                                             Использовать ли прокси из файла `bot/config/proxies.txt` (**True** / False)                                                                                             |
|       **DEVICE_PARAMS**        |                                                                                 Введите настройки устройства, чтобы телеграмм-сессия выглядела более реалистично (True / **False**)                                                                                 |
|       **DEBUG_LOGGING**        |                                                                                                Включить логирование трейсбэков ошибок в лог файл (True / **False**)                                                                                                 |

## Быстрый старт 📚

Для быстрой установки и последующего запуска - запустите файл run.bat на Windows или run.sh на Линукс

## Предварительные условия
Прежде чем начать, убедитесь, что у вас установлено следующее:
- [Python](https://www.python.org/downloads/) **версии 3.10**

## Получение API ключей
1. Перейдите на сайт [my.telegram.org](https://my.telegram.org) и войдите в систему, используя свой номер телефона.
2. Выберите **"API development tools"** и заполните форму для регистрации нового приложения.
3. Запишите `API_ID` и `API_HASH` в файле `.env`, предоставленные после регистрации вашего приложения.

## Установка
Вы можете скачать [**Репозиторий**](https://github.com/SP-l33t/Dogiators-Telethon) клонированием на вашу систему и установкой необходимых зависимостей:
```shell
git clone https://github.com/SP-l33t/Dogiators-Telethon.git
cd Dogiators-Telethon
```

Затем для автоматической установки введите:

Windows:
```shell
run.bat
```

Linux:
```shell
run.sh
```

# Linux ручная установка
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Здесь вы обязательно должны указать ваши API_ID и API_HASH , остальное берется по умолчанию
python3 main.py
```

Также для быстрого запуска вы можете использовать аргументы, например:
```shell
~/Dogiators-Telethon >>> python3 main.py --action (1/2)
# Or
~/Dogiators-Telethon >>> python3 main.py -a (1/2)

# 1 - Запускает кликер
# 2 - Создает сессию
```


# Windows ручная установка
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Указываете ваши API_ID и API_HASH, остальное берется по умолчанию
python main.py
```

Также для быстрого запуска вы можете использовать аргументы, например:
```shell
~/Dogiators-Telethon >>> python main.py --action (1/2)
# Или
~/Dogiators-Telethon >>> python main.py -a (1/2)

# 1 - Запускает кликер
# 2 - Создает сессию
```
