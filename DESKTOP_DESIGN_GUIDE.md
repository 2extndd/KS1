# 🖥️ Desktop Design Guide

Полное руководство по дизайну и адаптации десктопной версии для marketplace bot проектов.

## 📋 Содержание
1. [Навигационная панель](#навигационная-панель)
2. [Сетка и колонки](#сетка-и-колонки)
3. [Карточки товаров](#карточки-товаров)
4. [Таблицы](#таблицы)
5. [Формы и инпуты](#формы-и-инпуты)
6. [Типографика](#типографика)
7. [Адаптивные брейкпоинты](#адаптивные-брейкпоинты)

---

## Навигационная панель

### Структура

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm" style="padding: 0.75rem 0;">
    <div class="container-fluid">
        <!-- Logo Section -->
        <div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
            <a href="/" class="text-decoration-none text-white">
                <span class="brand-title" style="font-size: 1.25rem; font-weight: 600;">
                    [Project]Searcher
                </span>
            </a>
            <span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
                powered by <a href="https://t.me/extndd" target="_blank"
                               class="text-decoration-none"
                               style="color: #0dcaf0;">extndd</a>
            </span>
        </div>

        <!-- Navigation Links -->
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
                <li class="nav-item">
                    <a class="nav-link" href="/">
                        <i class="bi bi-speedometer2"></i> Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/queries">
                        <i class="bi bi-search"></i> Queries
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/items">
                        <i class="bi bi-bag"></i> Items
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/config">
                        <i class="bi bi-gear"></i> Config
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="/logs">
                        <i class="bi bi-file-text"></i> Logs
                    </a>
                </li>
            </ul>
        </div>
    </div>
</nav>
```

### Размеры навигации на разных экранах

| Экран | Padding | Brand Title | Brand Subtitle | Nav Link |
|-------|---------|-------------|----------------|----------|
| Mobile (< 992px) | `0.75rem 0` | `1.25rem` | `0.7rem` | `default` |
| Desktop (≥ 992px) | `1rem 0` | `1.5rem` | `0.8rem` | `1.05rem` |

### CSS стили

```css
/* Base navbar styles */
.navbar-brand {
    font-weight: 600;
    font-size: 1.25rem;
}

.navbar-nav .nav-link {
    font-weight: 500;
    border-radius: 0.375rem;
    margin: 0 0.25rem;
    transition: all 0.2s ease;
}

.navbar-nav .nav-link:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

.navbar-nav .nav-link.active {
    background-color: rgba(255, 255, 255, 0.2);
    font-weight: 600;
}

/* Desktop enhancement (>= 992px) */
@media (min-width: 992px) {
    .navbar {
        padding: 1rem 0 !important;
    }

    .brand-title {
        font-size: 1.5rem !important;
    }

    .brand-subtitle {
        font-size: 0.8rem !important;
    }

    .navbar-nav .nav-link {
        font-size: 1.05rem;
        padding: 0.6rem 1rem;
    }
}
```

### Особенности

- **Sticky positioning:** navbar остается видимым при прокрутке
- **Shadow:** `shadow-sm` для визуального отделения от контента
- **Dark theme:** `navbar-dark bg-dark` для темного фона
- **Icons:** Bootstrap Icons для визуального усиления
- **Двухстрочный логотип:** вертикальное расположение с `d-flex flex-column`

---

## Сетка и колонки

### Bootstrap 5 Grid System

MercariSearcher использует 12-колоночную сетку Bootstrap 5 с адаптивными брейкпоинтами.

### Брейкпоинты

| Размер | Брейкпоинт | Класс | Контейнер |
|--------|------------|-------|-----------|
| Extra small | < 576px | `.col-*` | 100% |
| Small | ≥ 576px | `.col-sm-*` | 540px |
| Medium | ≥ 768px | `.col-md-*` | 720px |
| Large | ≥ 992px | `.col-lg-*` | 960px |
| Extra large | ≥ 1200px | `.col-xl-*` | 1140px |
| Extra extra large | ≥ 1400px | `.col-xxl-*` | 1320px |

### Основной контейнер

```html
<div class="container-fluid mt-4">
    {% block content %}{% endblock %}
</div>
```

- `container-fluid` - 100% ширина на всех экранах
- `mt-4` - отступ сверху для отделения от navbar

---

## Карточки товаров

### Responsive колонки для товаров

```html
<div class="col-6 col-md-4 col-lg-3 col-xl-2 mb-3">
    <div class="card h-100 shadow-sm">
        <!-- Card content -->
    </div>
</div>
```

### Количество карточек в ряд на разных экранах

| Экран | Класс | Карточек в ряд | Ширина карточки |
|-------|-------|----------------|-----------------|
| Mobile (< 576px) | `col-6` | 2 | 50% |
| Mobile (≥ 576px) | `col-6` | 2 | 50% |
| Tablet (≥ 768px) | `col-md-4` | 3 | 33.33% |
| Desktop (≥ 992px) | `col-lg-3` | 4 | 25% |
| Large (≥ 1200px) | `col-xl-2` | 6 | 16.66% |

### Структура карточки товара

```html
<div class="col-6 col-md-4 col-lg-3 col-xl-2 mb-3">
    <div class="card h-100 shadow-sm">
        <!-- Image container with 4:5 aspect ratio -->
        <a href="${item.url}" target="_blank" class="text-decoration-none">
            <div class="item-image-container"
                 style="aspect-ratio: 4/5; overflow: hidden; background: var(--bg-card); border-radius: 0.25rem 0.25rem 0 0;">
                <img src="${item.image}"
                     class="d-block w-100 h-100"
                     style="object-fit: cover;"
                     loading="lazy"
                     referrerpolicy="no-referrer"
                     crossorigin="anonymous">
            </div>
        </a>

        <!-- Card body -->
        <div class="card-body p-2">
            <!-- Title (2 lines max) -->
            <h6 class="card-title mb-1 fw-bold"
                style="font-size: 0.8rem; line-height: 1.2; height: 2.4rem; overflow: hidden;">
                ${item.title}
            </h6>

            <!-- Price -->
            <div class="mb-1">
                <div class="fw-bold item-price" style="font-size: 1.1rem;">
                    $${item.price}
                </div>
                <div class="text-muted" style="font-size: 0.7rem;">
                    ¥${item.price_jpy}
                </div>
            </div>

            <!-- Badge (optional) -->
            <span class="badge bg-primary" style="font-size: 0.6rem;">
                ${item.keyword}
            </span>
        </div>
    </div>
</div>
```

### CSS стили для карточек

```css
/* Card styles */
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

/* Item card hover effect */
.item-card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.item-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

/* Image container */
.card-img-top {
    transition: transform 0.2s ease;
}

.card:hover .card-img-top {
    transform: scale(1.02);
}
```

---

## Таблицы

### Dashboard Stats (4 колонки в ряд)

```html
<div class="row g-2 mb-3">
    <div class="col-3">
        <div class="card h-100">
            <div class="card-body p-2 text-center">
                <div class="small text-muted mb-1" style="font-size: 0.7rem;">Searches</div>
                <div class="fw-bold" style="font-size: 1.2rem;">5</div>
                <div class="small text-success" style="font-size: 0.65rem;">5 active</div>
            </div>
        </div>
    </div>
    <!-- 3 more columns -->
</div>
```

### Queries Table (Desktop)

```html
<div class="table-responsive">
    <table class="table table-striped table-hover queries-table">
        <thead class="table-light">
            <tr>
                <th>#</th>
                <th>Query</th>
                <th>Thread ID</th>
                <th>Last Found Item</th>
                <th>Items</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>1</td>
                <td>
                    <a href="..." target="_blank" class="text-decoration-none">
                        Query Name
                    </a>
                </td>
                <td>
                    <code class="small query-code">31</code>
                </td>
                <td>
                    <small class="text-muted">2024-01-15 10:30</small>
                </td>
                <td>
                    <span class="badge bg-info">42</span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="..." class="btn btn-sm btn-outline-primary">
                            <i class="bi bi-grid"></i>
                        </a>
                        <button class="btn btn-sm btn-outline-warning">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

### CSS стили для таблиц

```css
/* Table styles */
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

/* Queries table dark theme */
[data-theme="dark"] .queries-table tbody tr {
    background-color: var(--bg-card);
    border-color: var(--border-color);
}

[data-theme="dark"] .queries-table tbody tr:hover {
    background-color: var(--table-hover);
}

[data-theme="dark"] .query-code {
    background-color: var(--bg-primary);
    color: #58a6ff;
    border: 1px solid var(--border-color);
}

[data-theme="dark"] .table-striped > tbody > tr:nth-of-type(odd) > * {
    background-color: rgba(255, 255, 255, 0.02);
}
```

---

## Формы и инпуты

### Структура формы

```html
<div class="card mb-4">
    <div class="card-header">
        <h5><i class="bi bi-gear"></i> System Settings</h5>
    </div>
    <div class="card-body">
        <form id="systemSettingsForm">
            <div class="row">
                <div class="col-md-4 mb-3">
                    <label class="form-label">Items Per Query</label>
                    <input type="number"
                           class="form-control"
                           name="max_items"
                           value="30"
                           min="1"
                           max="120">
                    <small class="text-muted">How many items to scan per query</small>
                </div>

                <div class="col-md-4 mb-3">
                    <label class="form-label">Query Delay (seconds)</label>
                    <input type="number"
                           class="form-control"
                           name="interval"
                           value="300"
                           min="60"
                           max="3600">
                    <small class="text-muted">Delay between queries</small>
                </div>

                <div class="col-md-4 mb-3">
                    <label class="form-label">Currency Rate</label>
                    <input type="number"
                           step="0.0001"
                           class="form-control"
                           name="rate"
                           value="0.0063">
                    <small class="text-muted">JPY to USD conversion</small>
                </div>
            </div>

            <button type="button" class="btn btn-primary">
                <i class="bi bi-save"></i> Save Settings
            </button>
        </form>
    </div>
</div>
```

### CSS стили для форм

```css
/* Forms */
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

### Кнопки

```css
/* Buttons */
.btn {
    font-weight: 500;
    border-radius: 0.375rem;
    transition: all 0.2s ease;
}

.btn-sm {
    font-size: 0.875rem;
    padding: 0.375rem 0.75rem;
}
```

---

## Типографика

### Заголовки страниц

```html
<h1 class="mb-3 d-none d-md-block">Dashboard</h1>
```

- `mb-3` - отступ снизу
- `d-none d-md-block` - скрыт на мобильных, виден на desktop

### Размеры шрифтов

| Элемент | Mobile | Desktop | CSS |
|---------|--------|---------|-----|
| Page title (h1) | hidden | `2.5rem` | `.h1` |
| Card title (h6) | `0.8rem` | `0.8rem` | custom |
| Body text | `1rem` | `1rem` | default |
| Small text | `0.875rem` | `0.875rem` | `.small` |
| Muted text | `0.7rem` | `0.7rem` | `.text-muted` |

### Font family

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 'Helvetica Neue', Arial, sans-serif;
}
```

### Monospace для кода

```css
.log-message,
.query-code {
    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono',
                 Consolas, 'Courier New', monospace;
}
```

---

## Адаптивные брейкпоинты

### Media Queries Structure

```css
/* Mobile First Approach */

/* Base styles (mobile) */
.element {
    /* Mobile styles */
}

/* Small devices (landscape phones, 576px and up) */
@media (min-width: 576px) {
    .element {
        /* Small device overrides */
    }
}

/* Medium devices (tablets, 768px and up) */
@media (min-width: 768px) {
    .element {
        /* Tablet overrides */
    }
}

/* Large devices (desktops, 992px and up) */
@media (min-width: 992px) {
    .element {
        /* Desktop overrides */
    }
}

/* Extra large devices (large desktops, 1200px and up) */
@media (min-width: 1200px) {
    .element {
        /* Large desktop overrides */
    }
}
```

### Примеры адаптации

#### Navbar

```css
/* Mobile (default) */
.navbar {
    padding: 0.75rem 0;
}

.brand-title {
    font-size: 1.25rem;
}

/* Desktop (>= 992px) */
@media (min-width: 992px) {
    .navbar {
        padding: 1rem 0 !important;
    }

    .brand-title {
        font-size: 1.5rem !important;
    }

    .navbar-nav .nav-link {
        font-size: 1.05rem;
        padding: 0.6rem 1rem;
    }
}
```

#### Stats Cards

```css
/* Mobile */
@media (max-width: 768px) {
    .card.bg-primary .card-title {
        font-size: 1.5rem;
    }
}

/* Desktop (default) */
.card.bg-primary .card-title {
    font-size: 2rem;
}
```

---

## 🎨 Цветовая схема (Desktop)

### Светлая тема

```css
:root {
    --bg-primary: #f8f9fa;      /* Основной фон */
    --bg-card: #ffffff;          /* Фон карточек */
    --text-primary: #212529;     /* Основной текст */
    --text-muted: #adb5bd;       /* Приглушенный текст */
    --border-color: #dee2e6;     /* Границы */
    --shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    --shadow-md: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}
```

### Темная тема (High Contrast)

```css
[data-theme="dark"] {
    --bg-primary: #0d1117;       /* Самый темный фон */
    --bg-card: #21262d;          /* Фон карточек */
    --text-primary: #f0f6fc;     /* Яркий белый текст */
    --text-muted: #8b949e;       /* Приглушенный серый */
    --border-color: #30363d;     /* Темно-серые границы */
    --shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.5);
    --shadow-md: 0 0.5rem 1rem rgba(0, 0, 0, 0.6);
}
```

---

## 🎯 Desktop Checklist

### Layout
- [ ] `container-fluid` для полной ширины
- [ ] Правильные брейкпоинты (col-md, col-lg, col-xl)
- [ ] Sticky navbar с shadow
- [ ] Увеличенные размеры на desktop (>= 992px)

### Cards
- [ ] 6 карточек в ряд на XL экранах (col-xl-2)
- [ ] 4 карточки в ряд на desktop (col-lg-3)
- [ ] 3 карточки на tablet (col-md-4)
- [ ] Shadow и hover эффекты

### Tables
- [ ] `.table-responsive` обертка
- [ ] Правильная ширина колонок
- [ ] Hover состояния
- [ ] Dark theme стили

### Forms
- [ ] 3 колонки на desktop (col-md-4)
- [ ] Labels с `form-label`
- [ ] Small text для подсказок
- [ ] Focus состояния с синей обводкой

### Typography
- [ ] Заголовки скрыты на мобильных (d-none d-md-block)
- [ ] Правильная иерархия размеров
- [ ] System font stack
- [ ] Monospace для кода

### Performance
- [ ] `loading="lazy"` для изображений
- [ ] `aspect-ratio` для контейнеров
- [ ] Transition для анимаций
- [ ] Минимальное количество custom CSS

---

**Создано на основе MercariSearcher v1.0**
*Responsive desktop design for marketplace bot projects*
