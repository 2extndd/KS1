# ✅ Быстрая проверка после деплоя на Railway

## Перед деплоем
```bash
# Убедитесь что все закоммичено
git status

# Проверьте последние коммиты
git log --oneline -3
# Должны быть:
# f3ec4bb Fix: Add {% block scripts %} to base.html
# 0188238 Fix: Query delete and update operations now work correctly

# Деплой
git push origin main
```

## После деплоя на Railway

### 1. Откройте Web UI
```
https://your-app.railway.app/queries
```

### 2. Проверьте ADD Query
- [ ] Заполните форму добавления query
- [ ] Нажмите "Add Query"
- [ ] **Ожидается**: ✅ Зеленый алерт "Query added successfully!" вверху справа
- [ ] Query появился в списке

### 3. Проверьте EDIT Query
- [ ] Нажмите кнопку "Edit Link" на любом query
- [ ] Измените URL или имя
- [ ] Нажмите "Update Query"
- [ ] **Ожидается**: ✅ Зеленый алерт "Query updated successfully!"
- [ ] Модальное окно закрылось
- [ ] Изменения видны в списке

### 4. Проверьте Thread ID
- [ ] Кликните checkbox рядом с Thread ID
- [ ] Введите новый ID (например, 888)
- [ ] **Ожидается**: ✅ Зеленый алерт "Thread ID updated successfully!"
- [ ] Новый ID отображается

### 5. Проверьте DELETE Query
- [ ] Нажмите кнопку "Remove" на любом query
- [ ] Подтвердите удаление в модальном окне
- [ ] **Ожидается**: ✅ Зеленый алерт "Query removed successfully!"
- [ ] Query исчез из списка

### 6. Проверьте DELETE ALL
- [ ] Нажмите "Remove All Queries" вверху страницы
- [ ] Подтвердите удаление
- [ ] **Ожидается**: ✅ Зеленый алерт "All queries removed successfully!"
- [ ] Список пустой

### 7. Проверьте обработку ошибок
- [ ] Попробуйте добавить query с пустым URL
- [ ] **Ожидается**: ⚠️ Красный алерт с описанием ошибки

## Особенности алертов

✅ **Правильное поведение**:
- Алерты появляются в правом верхнем углу
- Автоматически исчезают через 5 секунд
- Можно закрыть вручную кнопкой X
- Зеленые (success) для успешных операций
- Красные (danger) для ошибок

❌ **Если алерты НЕ показываются**:
```bash
# Проверьте в браузере консоль (F12)
# Должны быть видны:
# - window.showAlert = function...
# - function editQuery(queryId) {...}
# - function removeQuery(queryId, queryName) {...}

# Если функций нет - проблема с {% block scripts %}
```

## Проверка PostgreSQL

### В Railway логах должно быть:
```
✅ PostgreSQL база данных инициализирована успешно
✅ Added new search: ... (ID: X)
INFO:db:Updated search query X, affected rows: 1
INFO:db:Deleted search query X, affected rows: 1
```

### НЕ должно быть:
```
❌ Error updating search query
❌ Error deleting search query
❌ Failed to update query (API response 500)
❌ Failed to delete query (API response 500)
```

## Быстрая диагностика

### Проблема: Алерты не показываются
**Причина**: JavaScript не загрузился
**Решение**: Проверьте console.log, должна быть функция showAlert

### Проблема: API возвращает 500
**Причина**: Ошибка в db.py
**Решение**: Проверьте Railway логи, должны быть rowcount > 0

### Проблема: Query не удаляется
**Причина**: cursor.rowcount теряется
**Решение**: Убедитесь что используется новая версия db.py (commit 0188238)

## Контакты для отладки

Если что-то не работает:
1. Проверьте Railway логи
2. Откройте browser console (F12)
3. Проверьте Network tab для API запросов
4. Все должны возвращать 200 + success:true

---

✨ **Если все галочки проставлены - деплой успешен!** ✨
