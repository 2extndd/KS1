# 🚨 Railway Quick Fix для KF Searcher

## Проблема
Бот не запускается на Railway с ошибкой:
```
ValueError: DATABASE_URL not set on Railway. Please set it in Railway environment variables.
```

## ✅ Решение (3 шага)

### 1. Добавить PostgreSQL на Railway
1. Открой [Railway Dashboard](https://railway.app)
2. Перейди в свой проект
3. Нажми **"New Service"**
4. Выбери **"PostgreSQL"**
5. Railway автоматически создаст `DATABASE_URL`

### 2. Настроить переменные окружения
В Railway Variables добавь:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
PROXY_ENABLED=true
PROXY_LIST=proxy1:port,proxy2:port
```

### 3. Перезапустить приложение
1. Railway автоматически перезапустит приложение
2. Или нажми **"Redeploy"** вручную

## 🔍 Проверка
После исправления:
- ✅ Бот запустится без ошибок
- ✅ Веб-интерфейс будет доступен
- ✅ База данных будет работать
- ✅ Поиск и уведомления будут функционировать

## 📞 Если не помогло
1. Проверь логи в Railway Dashboard
2. Убедись что PostgreSQL сервис добавлен
3. Проверь что `DATABASE_URL` создался автоматически

---
**Время исправления: 2-3 минуты** ⚡
