# KF Searcher (KS1)

**KF Searcher** - автоматический мониторинг новых объявлений на Kufar.by с уведомлениями в Telegram и современным веб-интерфейсом.

Создан на основе архитектуры [VS5](https://github.com/2extndd/VS5), адаптирован для работы с Kufar.by.

## 🌟 Особенности

- **Автоматический мониторинг** - проверка новых объявлений по заданным поисковым запросам
- **Telegram уведомления** - мгновенные уведомления о новых товарах в супергруппах с поддержкой тредов
- **Современный веб-интерфейс** - удобное управление поисками, просмотр товаров и логов
- **Поддержка прокси** - защита от блокировок со стороны Kufar.by
- **Auto-redeploy** - автоматический перезапуск при накоплении ошибок
- **PostgreSQL** - надежное хранение данных
- **Railway готов** - легкое развертывание в облаке

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/2extndd/KS1.git
cd KS1
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка окружения

```bash
cp env.example .env
# Отредактируйте .env файл, добавив ваши настройки
```

### 4. Запуск

```bash
# Запуск основного сервиса
python kufar_notifications.py

# Или запуск только веб-интерфейса
python kufar_notifications.py web
```

## 📋 Конфигурация

### Обязательные переменные окружения

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here    # Токен от @BotFather
```

### Рекомендуемые переменные

```env
TELEGRAM_CHAT_ID=your_chat_id             # ID чата для уведомлений
PROXY_ENABLED=true                        # Включить прокси
PROXY_LIST=proxy1:port,proxy2:port        # Список прокси
```

### Дополнительные настройки

```env
SEARCH_INTERVAL=300                       # Интервал поиска (секунды)
MAX_ITEMS_PER_SEARCH=50                   # Макс. товаров за поиск
MAX_ERRORS_BEFORE_REDEPLOY=5             # Порог ошибок для redeploy
```

## 🔧 Настройка Telegram бота

1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Получите токен бота
3. Добавьте бота в вашу супергруппу
4. Получите ID чата (можно через [@userinfobot](https://t.me/userinfobot))
5. Для тредов: получите ID треда (message_thread_id)

## 🌐 Веб-интерфейс

Веб-интерфейс доступен по адресу `http://localhost:5000` и включает:

- **Dashboard** - общая статистика и последние товары
- **Items** - просмотр всех найденных товаров с фильтрацией
- **Searches** - управление поисковыми запросами
- **Configuration** - настройки системы
- **Logs** - просмотр логов работы системы

## 📱 Добавление поисков

1. Перейдите на [kufar.by](https://www.kufar.by)
2. Настройте поиск (категория, регион, цена и т.д.)
3. Скопируйте URL из адресной строки
4. В веб-интерфейсе: Searches → Add Search
5. Вставьте URL и настройте уведомления

## 🚀 Развертывание на Railway

### 1. Подготовка

1. Зарегистрируйтесь на [Railway](https://railway.app)
2. Создайте новый проект
3. Подключите PostgreSQL database

### 2. Переменные окружения на Railway

Установите следующие переменные в Railway:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
PROXY_ENABLED=true
PROXY_LIST=your_proxy_list
RAILWAY_TOKEN=your_railway_token
RAILWAY_PROJECT_ID=your_project_id
RAILWAY_SERVICE_ID=your_service_id
```

### 3. Деплой

```bash
# Подключите Railway CLI
railway login

# Деплой
railway up
```

## 🛡️ Настройка прокси

Для избежания блокировок рекомендуется использовать прокси:

1. Получите список прокси (резидентные или мобильные)
2. Установите `PROXY_ENABLED=true`
3. Добавьте прокси в `PROXY_LIST` через запятую
4. Система автоматически будет ротировать прокси

Формат прокси:
```
ip:port
ip:port:username:password
http://ip:port
socks5://ip:port
```

## 📊 Auto-Redeploy

Система автоматически перезапускается при накоплении ошибок:

- Отслеживаются коды ошибок: 403, 404, 429, 500, 502, 503
- По умолчанию redeploy после 5 ошибок
- Настраивается через `MAX_ERRORS_BEFORE_REDEPLOY`
- Требует настройки Railway API токена

## 🔍 Мониторинг

### Логи

- Веб-интерфейс: `/logs`
- Фильтрация по уровню (ERROR, WARNING, INFO, DEBUG)
- Автообновление каждую минуту
- Экспорт логов

### Статистика

- Общее количество товаров
- Товары за сегодня
- Неотправленные уведомления
- Активные поиски
- Статус прокси

## 🛠️ API

Система предоставляет REST API:

```bash
# Запуск поиска
POST /api/search/run

# Отправка уведомлений
POST /api/notifications/send

# Статистика
GET /api/stats

# Ручной redeploy
POST /api/redeploy

# Проверка URL
POST /api/search/test
```

## 📁 Структура проекта

```
KS1/
├── pyKufarVN/              # API клиент для Kufar.by
│   ├── kufar.py           # Основной класс
│   ├── items.py           # Работа с товарами
│   └── exceptions.py      # Исключения
├── web_ui_plugin/         # Веб-интерфейс
│   ├── templates/         # HTML шаблоны
│   ├── static/           # CSS/JS файлы
│   └── app.py            # Flask приложение
├── kufar_notifications.py # Главный файл
├── core.py               # Основная логика
├── db.py                # Работа с БД
├── simple_telegram_worker.py # Telegram уведомления
├── railway_redeploy.py   # Auto-redeploy
├── proxies.py           # Управление прокси
└── configuration_values.py # Конфигурация
```

## 🐛 Устранение неполадок

### Частые проблемы

1. **Telegram уведомления не работают**
   - Проверьте `TELEGRAM_BOT_TOKEN`
   - Убедитесь, что бот добавлен в группу
   - Проверьте `TELEGRAM_CHAT_ID`

2. **Блокировки от Kufar.by**
   - Включите прокси (`PROXY_ENABLED=true`)
   - Увеличьте задержки между запросами
   - Проверьте качество прокси

3. **Ошибки базы данных**
   - Проверьте `DATABASE_URL`
   - На Railway БД настраивается автоматически

4. **Auto-redeploy не работает**
   - Проверьте Railway токены
   - Убедитесь в правильности PROJECT_ID и SERVICE_ID

### Логи и отладка

```bash
# Увеличить уровень логирования
export LOG_LEVEL=DEBUG

# Проверить конфигурацию
python railway_config.py

# Тест соединения с БД
python -c "from db import db; print('DB OK' if db.get_items_stats() else 'DB Error')"
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🔗 Ссылки

- [VS5 (оригинальный проект для Vinted)](https://github.com/2extndd/VS5)
- [Railway (хостинг)](https://railway.app)
- [Kufar.by (мониторируемый сайт)](https://www.kufar.by)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 📞 Поддержка

При возникновении проблем:

1. Проверьте [Issues](https://github.com/2extndd/KS1/issues)
2. Создайте новый Issue с подробным описанием
3. Приложите логи и конфигурацию (без токенов!)

---

**KF Searcher** - мониторинг Kufar.by стал проще! 🔍📱
