# 🎨 Dark Theme Implementation Guide

Полное руководство по реализации темной темы для ваших проектов на основе MercariSearcher.

## 📋 Содержание
1. [CSS Variables](#css-variables)
2. [Основные стили](#основные-стили)
3. [Темная тема компонентов](#темная-тема-компонентов)
4. [JavaScript для переключения](#javascript-для-переключения)
5. [Предотвращение белого "мелька"](#предотвращение-белого-мелька)
6. [Мобильная адаптация](#мобильная-адаптация)

---

## CSS Variables

### 1. Определение переменных в `:root` (светлая тема по умолчанию)

```css
:root {
    /* Light Theme (default) */
    --bg-primary: #f8f9fa;           /* Основной фон страницы */
    --bg-secondary: #ffffff;         /* Вторичный фон */
    --bg-card: #ffffff;              /* Фон карточек */
    --bg-header: #ffffff;            /* Фон заголовков */
    --text-primary: #212529;         /* Основной текст */
    --text-secondary: #6c757d;       /* Вторичный текст */
    --text-muted: #adb5bd;           /* Приглушенный текст */
    --border-color: #dee2e6;         /* Цвет границ */
    --shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);  /* Малая тень */
    --shadow-md: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);        /* Средняя тень */
    --table-hover: rgba(0, 0, 0, 0.02);  /* Ховер таблицы */
    --log-hover: rgba(0, 0, 0, 0.02);    /* Ховер логов */
    --input-bg: #ffffff;             /* Фон инпутов */
    --input-border: #ced4da;         /* Границы инпутов */
    --card-header-bg: #ffffff;       /* Фон заголовков карточек */
}
```

### 2. Темная тема с высоким контрастом

```css
[data-theme="dark"] {
    /* Dark Theme - High Contrast (GitHub-inspired) */
    --bg-primary: #0d1117;           /* Самый темный фон */
    --bg-secondary: #161b22;         /* Темный фон */
    --bg-card: #21262d;              /* Фон карточек (светлее) */
    --bg-header: #161b22;            /* Фон заголовков */
    --text-primary: #f0f6fc;         /* Яркий белый текст */
    --text-secondary: #c9d1d9;       /* Светло-серый текст */
    --text-muted: #8b949e;           /* Приглушенный серый */
    --border-color: #30363d;         /* Темно-серые границы */
    --shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.5);   /* Усиленная тень */
    --shadow-md: 0 0.5rem 1rem rgba(0, 0, 0, 0.6);        /* Усиленная тень */
    --table-hover: rgba(255, 255, 255, 0.08);  /* Ховер таблицы */
    --log-hover: rgba(255, 255, 255, 0.08);    /* Ховер логов */
    --input-bg: #161b22;             /* Темный фон инпутов */
    --input-border: #30363d;         /* Темные границы */
    --card-header-bg: #161b22;       /* Темный заголовок карточек */
}
```

---

## Основные стили

### Body и общие элементы

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    transition: background-color 0.3s ease, color 0.3s ease;
}
```

### Карточки

```css
.card {
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.15s ease-in-out;
    background-color: var(--bg-card);
    color: var(--text-primary);
}

.card:hover {
    box-shadow: var(--shadow-md);
}

.card-header {
    background-color: var(--card-header-bg);
    border-bottom: 1px solid var(--border-color);
    font-weight: 600;
    color: var(--text-primary);
}
```

### Таблицы

```css
.table {
    font-size: 0.9rem;
    color: var(--text-primary);
}

.table th {
    font-weight: 600;
    border-top: none;
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.table-hover tbody tr:hover {
    background-color: var(--table-hover);
}

.table-light {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}
```

### Формы

```css
.form-control,
.form-select {
    border-radius: 0.375rem;
    border: 1px solid var(--input-border);
    background-color: var(--input-bg);
    color: var(--text-primary);
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus,
.form-select:focus {
    border-color: #86b7fe;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
    background-color: var(--input-bg);
    color: var(--text-primary);
}

.form-label {
    font-weight: 500;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.text-muted {
    color: var(--text-muted) !important;
}
```

---

## Темная тема компонентов

### Цены товаров

```css
/* Исправление видимости цен в темной теме */
[data-theme="dark"] .text-dark,
[data-theme="dark"] .item-price {
    color: #f0f6fc !important;
}

/* Фон контейнеров изображений */
[data-theme="dark"] .bg-light,
[data-theme="dark"] .item-image-container {
    background-color: var(--bg-card) !important;
}
```

### Таблица Queries

```css
[data-theme="dark"] .queries-table tbody tr {
    background-color: var(--bg-card);
    border-color: var(--border-color);
}

[data-theme="dark"] .queries-table tbody tr:hover {
    background-color: var(--table-hover);
}

[data-theme="dark"] .query-code {
    background-color: var(--bg-primary);
    color: #58a6ff;  /* Синий текст для кода */
    border: 1px solid var(--border-color);
}

[data-theme="dark"] .table-striped > tbody > tr:nth-of-type(odd) > * {
    background-color: rgba(255, 255, 255, 0.02);
}
```

### Логи (мобильная версия)

```css
@media (max-width: 768px) {
    .log-table tr {
        border: 1px solid var(--border-color);
        border-radius: 0.25rem;
        margin-bottom: 0.75rem;
        display: block;
        background: var(--bg-card);
    }

    .log-table .timestamp {
        font-size: 0.7rem;
        color: var(--text-muted);
    }

    .log-table .message {
        font-size: 0.85rem;
        line-height: 1.4;
        word-break: break-word;
        color: var(--text-primary);
    }
}
```

### Кнопка переключения темы

```css
.theme-toggle-btn {
    position: relative;
    padding: 0.5rem 1rem;
    border: 2px solid var(--border-color);
    background-color: var(--bg-card);
    color: var(--text-primary);
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.theme-toggle-btn:hover {
    background-color: var(--bg-primary);
    border-color: #0d6efd;
}

.theme-toggle-btn i {
    font-size: 1.2rem;
}
```

---

## JavaScript для переключения

### 1. Предотвращение белого "мелька" (в `<head>`)

**ВАЖНО:** Этот скрипт должен быть в `<head>` ПЕРЕД всеми CSS!

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your App</title>

    <!-- Prevent white flash on dark theme -->
    <script>
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            if (savedTheme === 'dark') {
                document.documentElement.style.backgroundColor = '#0d1117';
                document.documentElement.style.color = '#f0f6fc';
            }
        })();
    </script>

    <!-- CSS files here -->
    <link rel="stylesheet" href="style.css">
</head>
```

### 2. Загрузка темы при загрузке страницы

```html
<script>
// Load theme from localStorage on page load (MUST be synchronous!)
(function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();
</script>
```

### 3. Функция переключения темы

```html
<script>
// Global theme toggle function
window.toggleTheme = function() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update toggle button icon if it exists
    const icon = document.querySelector('.theme-toggle-btn i');
    if (icon) {
        icon.className = newTheme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }

    // Update button text if it exists
    const text = document.querySelector('.theme-toggle-btn .theme-text');
    if (text) {
        text.textContent = newTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
};

// Get current theme
window.getCurrentTheme = function() {
    return document.documentElement.getAttribute('data-theme') || 'light';
};
</script>
```

### 4. Инициализация кнопки переключения (на странице Config)

```html
<script>
// Initialize theme toggle button state
function initThemeToggle() {
    const currentTheme = window.getCurrentTheme();
    const icon = document.querySelector('.theme-toggle-btn i');
    const text = document.querySelector('.theme-toggle-btn .theme-text');

    if (icon) {
        icon.className = currentTheme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
    }
    if (text) {
        text.textContent = currentTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
    }
}

// Initialize on page load
initThemeToggle();
</script>
```

---

## Предотвращение белого "мелька"

### Проблема
При перезагрузке страницы на темной теме происходит кратковременный "мелёк" белым фоном.

### Решение
**1. Inline скрипт в `<head>` перед CSS:**

```html
<head>
    <!-- Prevent white flash - MUST BE FIRST! -->
    <script>
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            if (savedTheme === 'dark') {
                document.documentElement.style.backgroundColor = '#0d1117';
                document.documentElement.style.color = '#f0f6fc';
            }
        })();
    </script>

    <!-- CSS after the script -->
    <link rel="stylesheet" href="style.css">
</head>
```

**2. Синхронный скрипт сразу после открытия `<body>`:**

```html
<body>
    <script>
        (function() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
        })();
    </script>

    <!-- Rest of content -->
</body>
```

---

## Мобильная адаптация

### Увеличение размера карточек товаров на мобильных

```css
/* Larger images on mobile */
@media (max-width: 576px) {
    .col-6 {
        flex: 0 0 50%;
        max-width: 50%;
    }
}
```

### HTML структура карточки товара

```html
<div class="col-6 col-sm-4 col-md-3 col-lg-3 col-xl-2 mb-3">
    <div class="card h-100 shadow-sm">
        <a href="${item.url}" target="_blank" class="text-decoration-none">
            <div class="item-image-container" style="aspect-ratio: 4/5; overflow: hidden; background: var(--bg-card); border-radius: 0.25rem 0.25rem 0 0;">
                <img src="${item.image}" class="d-block w-100 h-100" style="object-fit: cover;" loading="lazy">
            </div>
        </a>
        <div class="card-body p-2">
            <h6 class="card-title mb-1 fw-bold" style="font-size: 0.8rem;">
                ${item.title}
            </h6>
            <div class="mb-1">
                <div class="fw-bold item-price" style="font-size: 1.1rem;">$${item.price}</div>
            </div>
        </div>
    </div>
</div>
```

---

## 🎯 Чеклист для внедрения темной темы

### CSS
- [ ] Скопировать CSS variables для `:root` и `[data-theme="dark"]`
- [ ] Заменить все hardcoded цвета на CSS variables
- [ ] Добавить стили для карточек, таблиц, форм
- [ ] Добавить специфичные стили для темной темы (цены, таблицы, логи)
- [ ] Добавить стили для кнопки переключения темы

### HTML
- [ ] Добавить inline скрипт в `<head>` для предотвращения "мелька"
- [ ] Добавить скрипт загрузки темы сразу после `<body>`
- [ ] Добавить функции `toggleTheme()` и `getCurrentTheme()`
- [ ] Создать кнопку переключения темы на странице Config
- [ ] Добавить классы `.item-price`, `.item-image-container` к элементам

### JavaScript
- [ ] Инициализация темы при загрузке страницы
- [ ] Функция переключения с сохранением в localStorage
- [ ] Обновление иконки и текста кнопки при переключении
- [ ] Инициализация состояния кнопки на странице Config

### Тестирование
- [ ] Проверить переключение темы на всех страницах
- [ ] Проверить отсутствие "белого мелька" при перезагрузке
- [ ] Проверить видимость цен, текста, таблиц в темной теме
- [ ] Проверить мобильную версию (размер карточек, таблицы)
- [ ] Проверить сохранение темы в localStorage

---

## 🔧 Адаптация для других проектов

### KufarSearcher / VintedSearcher

1. Замените `MercariSearcher` на `KufarSearcher` / `VintedSearcher`
2. Используйте те же CSS переменные
3. Добавьте специфичные классы для ваших компонентов
4. Скопируйте JavaScript без изменений

### Цветовая схема

Можете настроить цвета под ваш бренд, изменив значения в `[data-theme="dark"]`:

```css
[data-theme="dark"] {
    --bg-primary: #ваш-цвет;
    --text-primary: #ваш-цвет;
    /* и т.д. */
}
```

---

**Создано на основе MercariSearcher v1.0**
*Высокий контраст, плавные переходы, без "белого мелька"*
