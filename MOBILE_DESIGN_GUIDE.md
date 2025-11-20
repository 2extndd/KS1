# Mobile Design Guide - MercariSearcher Style
**Эталонный проект для VS5 и KFS**

Этот документ описывает полный дизайн-система и UX паттерны, использованные в MercariSearcher для идеальной мобильной версии.

---

## 🎯 Общие Принципы

### 1. Mobile-First Подход
- Все элементы спроектированы сначала для мобильных (320px+)
- Desktop версия расширяет функциональность, но не меняет логику
- Никаких горизонтальных скроллов
- Все тапабельные элементы минимум 44x44px

### 2. Sticky Navigation
- Navbar всегда видна при прокрутке (`sticky-top`)
- Компактная на мобильных, полная на desktop
- Тень для визуального отделения (`shadow-sm`)

### 3. Infinite Scroll
- Загрузка по 30 элементов за раз
- Автозагрузка за 300px до конца страницы
- Индикатор загрузки при подгрузке
- Без пагинации - только бесконечная прокрутка

### 4. Responsive Grid System
- Mobile: 2 карточки в ряд (`col-6`)
- Tablet: 3-4 карточки (`col-md-4`, `col-lg-3`)
- Desktop: 4-6 карточек (`col-xl-2`)

---

## 📱 Компоненты

### Header (Navbar)

**HTML структура:**
```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm">
    <div class="container-fluid">
        <!-- Брендинг с двумя строками -->
        <div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
            <a href="/" class="text-decoration-none text-white">
                <span style="font-size: 1.25rem; font-weight: 600;">ProjectName</span>
            </a>
            <span style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
                powered by <a href="https://t.me/extndd" target="_blank"
                              class="text-decoration-none" style="color: #0dcaf0;">extndd</a>
            </span>
        </div>

        <!-- Меню (сворачивается на мобильных) -->
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
                data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
                <li class="nav-item">
                    <a class="nav-link" href="/">
                        <i class="bi bi-speedometer2"></i> Dashboard
                    </a>
                </li>
                <!-- Другие пункты меню -->
            </ul>
        </div>
    </div>
</nav>
```

**Ключевые особенности:**
- `sticky-top` - навбар всегда видна
- Двухстрочный брендинг (название + powered by)
- Ссылка на Telegram в брендинге
- Иконки Bootstrap Icons для визуала
- Гамбургер-меню на мобильных

---

### Dashboard Page

#### 1. Статистика (4 колонки в одну строку)

**HTML:**
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
    <!-- Еще 3 колонки: Items, API, Uptime -->
</div>
```

**Стиль:**
- **Мобильные:** 4 колонки (`col-3`) в один ряд
- **Padding:** Минимальный (`p-2`)
- **Шрифты:**
  - Заголовок: `0.7rem`
  - Цифра: `1.2rem`, жирная
  - Подпись: `0.65rem`
- **Цвета:**
  - Active: `text-success`
  - New: `text-warning`
  - Мутед: `text-muted`

#### 2. Кнопки действий (3 в ряд)

**HTML:**
```html
<div class="row g-2 mb-3">
    <div class="col-4">
        <button class="btn btn-success btn-sm w-100"
                style="font-size: 0.75rem; padding: 0.4rem;">
            <i class="bi bi-arrow-clockwise"></i>
            <span class="d-none d-sm-inline ms-1">Scan</span>
        </button>
    </div>
    <div class="col-4">
        <button class="btn btn-danger btn-sm w-100"
                style="font-size: 0.75rem; padding: 0.4rem;">
            <i class="bi bi-trash"></i>
            <span class="d-none d-sm-inline ms-1">Clear</span>
        </button>
    </div>
    <div class="col-4">
        <a href="/items" class="btn btn-outline-primary btn-sm w-100"
           style="font-size: 0.75rem; padding: 0.4rem;">
            <i class="bi bi-grid-3x3"></i>
            <span class="d-none d-sm-inline ms-1">All</span>
        </a>
    </div>
</div>
```

**Стиль:**
- **Мобильные:** Только иконки (`d-none d-sm-inline`)
- **Desktop:** Иконки + текст
- **Размер:** `btn-sm`, `font-size: 0.75rem`
- **Padding:** `0.4rem` для компактности
- **Ширина:** `w-100` на всю колонку

#### 3. Карточки товаров (2 в ряд на мобильных)

**HTML:**
```html
<div class="col-6 col-md-4 col-lg-3 col-xl-2 mb-3">
    <div class="card h-100 shadow-sm">
        <!-- Изображение с aspect ratio 4:5 -->
        <a href="${item_url}" target="_blank" class="text-decoration-none">
            <div style="aspect-ratio: 4/5; overflow: hidden; background: #f8f9fa;
                        border-radius: 0.25rem 0.25rem 0 0;">
                <img src="${image_url}"
                     class="d-block w-100 h-100"
                     style="object-fit: cover;"
                     loading="lazy"
                     referrerpolicy="no-referrer"
                     crossorigin="anonymous">
            </div>
        </a>

        <!-- Информация о товаре -->
        <div class="card-body p-2">
            <!-- Название (2 строки, обрезка) -->
            <h6 class="card-title mb-1 fw-bold"
                style="font-size: 0.8rem; line-height: 1.2;
                       height: 2.4rem; overflow: hidden;">
                ${item_title}
            </h6>

            <!-- Цена -->
            <div class="mb-1">
                <div class="fw-bold text-dark" style="font-size: 1.1rem;">
                    $${usd_price}
                </div>
                <div class="text-muted" style="font-size: 0.7rem;">
                    ¥${jpy_price}
                </div>
            </div>

            <!-- Тег категории -->
            <span class="badge bg-primary" style="font-size: 0.6rem;">
                ${category}
            </span>
        </div>
    </div>
</div>
```

**Grid breakpoints:**
- Mobile (`<576px`): `col-6` (2 карточки)
- Tablet (`≥768px`): `col-md-4` (3 карточки)
- Desktop (`≥992px`): `col-lg-3` (4 карточки)
- Large (`≥1200px`): `col-xl-2` (6 карточек)

**Стиль карточки:**
- **Aspect ratio:** 4:5 для изображения (вертикальное)
- **Shadow:** `shadow-sm` для объема
- **Padding:** `p-2` (компактно)
- **Border radius:** Скругленные углы изображения
- **Loading:** `loading="lazy"` для ленивой загрузки

**Изображения:**
- **Fallback:** Иконка если ошибка загрузки
- **CORS:** `referrerpolicy="no-referrer"` + `crossorigin="anonymous"`
- **Object-fit:** `cover` для заполнения

**Текст:**
- **Название:** 2 строки макс (`height: 2.4rem` + `overflow: hidden`)
- **Цена USD:** Крупная (`1.1rem`), жирная
- **Цена JPY:** Мелкая (`0.7rem`), серая
- **Badge:** Маленький (`0.6rem`)

---

### Items Page (Full Catalog)

**Отличия от Dashboard:**
- Показывает все товары (не только последние 24ч)
- Infinite scroll по 30 товаров
- Loading indicator при подгрузке
- Без auto-refresh (статичные данные)

**HTML структура:**
```html
<!-- Grid контейнер -->
<div class="row" id="items-grid-container">
    <!-- Карточки товаров (такие же как на Dashboard) -->
</div>

<!-- Loading indicator -->
<div class="row mt-4" id="loading-indicator" style="display: none;">
    <div class="col-12 text-center py-3">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading more...</span>
        </div>
        <p class="text-muted mt-2 small">Loading more items...</p>
    </div>
</div>
```

**JavaScript (Infinite Scroll):**
```javascript
let currentOffset = 0;
let isLoading = false;
let hasMore = true;
const itemsPerPage = 30;

function loadMoreItems() {
    if (isLoading || !hasMore) return;

    isLoading = true;
    document.getElementById('loading-indicator').style.display = 'block';

    fetch(`/api/items?limit=${itemsPerPage}&offset=${currentOffset}`)
        .then(r => r.json())
        .then(data => {
            if (!data.success || !data.items || data.items.length === 0) {
                hasMore = false;
                document.getElementById('loading-indicator').style.display = 'none';
                return;
            }

            // Check if there are more items
            if (data.items.length < itemsPerPage) {
                hasMore = false;
            }

            // Render items
            const container = document.getElementById('items-grid-container');
            data.items.forEach(item => {
                const html = `<!-- Card HTML here -->`;
                container.insertAdjacentHTML('beforeend', html);
            });

            currentOffset += data.items.length;
            isLoading = false;
            document.getElementById('loading-indicator').style.display = 'none';
        })
        .catch(err => {
            console.error('Error loading more items:', err);
            isLoading = false;
            document.getElementById('loading-indicator').style.display = 'none';
        });
}

// Infinite scroll detector
function setupInfiniteScroll() {
    window.addEventListener('scroll', () => {
        if (isLoading || !hasMore) return;

        const scrollPosition = window.innerHeight + window.scrollY;
        const pageHeight = document.documentElement.scrollHeight;

        // Load more when user is 300px from bottom
        if (scrollPosition >= pageHeight - 300) {
            loadMoreItems();
        }
    });
}

// Initial setup
document.addEventListener('DOMContentLoaded', function() {
    setupInfiniteScroll();
});
```

**Ключевые моменты:**
- **Offset-based пагинация:** `currentOffset` увеличивается на кол-во загруженных
- **Trigger distance:** 300px от конца страницы
- **Loading guard:** `isLoading` предотвращает дубли
- **End detection:** `hasMore` останавливает загрузку

---

### Logs Page

#### Фильтры (горизонтально)

**HTML:**
```html
<div class="mb-3">
    <div class="d-flex gap-2 flex-wrap">
        <a href="/logs"
           class="btn btn-sm btn-secondary flex-fill"
           style="font-size: 0.75rem;">
            All
        </a>
        <a href="/logs?level=INFO"
           class="btn btn-sm btn-info text-white flex-fill"
           style="font-size: 0.75rem;">
            INFO
        </a>
        <a href="/logs?level=WARNING"
           class="btn btn-sm btn-warning flex-fill"
           style="font-size: 0.75rem;">
            WARNING
        </a>
        <a href="/logs?level=ERROR"
           class="btn btn-sm btn-danger flex-fill"
           style="font-size: 0.75rem;">
            ERROR
        </a>
    </div>
</div>
```

**Стиль:**
- **Layout:** `d-flex gap-2 flex-wrap`
- **Ширина:** `flex-fill` для равномерного распределения
- **Размер:** `btn-sm`, `0.75rem`
- **Адаптивность:** Переносятся на новую строку если не влезают

#### Таблица логов (карточный стиль на мобильных)

**CSS:**
```css
/* Mobile-responsive log table */
@media (max-width: 768px) {
    .log-table td {
        display: block;
        width: 100% !important;
        border: none !important;
        padding: 0.3rem 0.5rem !important;
    }
    .log-table tr {
        border: 1px solid #dee2e6;
        border-radius: 0.25rem;
        margin-bottom: 0.75rem;
        display: block;
        background: white;
    }
    .log-table thead {
        display: none;
    }
    .log-table .timestamp {
        font-size: 0.7rem;
        color: #6c757d;
    }
    .log-table .level-badge {
        margin: 0.3rem 0;
    }
    .log-table .message {
        font-size: 0.85rem;
        line-height: 1.4;
        word-break: break-word;
    }
}

/* Desktop table */
@media (min-width: 769px) {
    .log-table tbody tr {
        line-height: 1.2;
    }
    .log-table tbody td {
        padding: 0.4rem 0.6rem !important;
        vertical-align: middle;
    }
    .log-table thead th {
        padding: 0.5rem 0.6rem !important;
    }
}
```

**HTML:**
```html
<table class="table table-sm table-hover log-table">
    <thead class="table-light">
        <tr>
            <th style="width: 200px;">Timestamp</th>
            <th style="width: 100px;">Level</th>
            <th>Message</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td class="timestamp">
                <small class="text-muted">2025-11-20 15:30:45</small>
            </td>
            <td class="level-badge">
                <span class="badge bg-info">INFO</span>
            </td>
            <td class="message">Search completed: 10 items found</td>
        </tr>
    </tbody>
</table>
```

**Поведение:**
- **Mobile:** Каждый лог - отдельная карточка (вертикальное расположение)
- **Desktop:** Классическая таблица (горизонтальное)
- **Auto-refresh:** Каждые 5 секунд без перезагрузки страницы

---

## 🎨 Design Tokens

### Цвета

```css
/* Primary Actions */
--color-success: #198754;      /* Scan, Active states */
--color-danger: #dc3545;       /* Delete, Error */
--color-primary: #0d6efd;      /* Links, Info */
--color-warning: #ffc107;      /* Warnings, New items */

/* Text */
--color-text-dark: #212529;    /* Основной текст */
--color-text-muted: #6c757d;   /* Вторичный текст */
--color-text-light: #adb5bd;   /* Подписи */

/* Background */
--color-bg-light: #f8f9fa;     /* Card backgrounds */
--color-bg-dark: #212529;      /* Navbar */

/* Borders */
--color-border: #dee2e6;       /* Карточки, таблицы */
```

### Типографика

```css
/* Размеры шрифтов (мобильные) */
--font-tiny: 0.6rem;      /* Badges */
--font-small: 0.7rem;     /* Подписи, метаданные */
--font-normal: 0.8rem;    /* Заголовки карточек */
--font-medium: 1.1rem;    /* Цены, важные цифры */
--font-large: 1.2rem;     /* Статистика */
--font-xlarge: 1.25rem;   /* Название проекта */

/* Веса */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-bold: 600;
```

### Spacing

```css
/* Gaps */
--gap-xs: 0.25rem;   /* 4px */
--gap-sm: 0.5rem;    /* 8px */
--gap-md: 1rem;      /* 16px */
--gap-lg: 1.5rem;    /* 24px */

/* Padding (карточки) */
--card-padding-mobile: 0.5rem;   /* p-2 */
--card-padding-desktop: 0.75rem; /* p-3 */

/* Margins */
--margin-between-sections: 1rem; /* mb-3 */
```

### Border Radius

```css
--border-radius-sm: 0.25rem;    /* Cards, badges */
--border-radius-md: 0.375rem;   /* Buttons */
--border-radius-lg: 0.5rem;     /* Modal */
```

### Shadows

```css
--shadow-sm: 0 .125rem .25rem rgba(0,0,0,.075);     /* Cards */
--shadow-md: 0 .5rem 1rem rgba(0,0,0,.15);          /* Modals */
--shadow-navbar: 0 2px 4px rgba(0,0,0,.08);         /* Sticky navbar */
```

---

## 📐 Layout Patterns

### Grid System

**Breakpoints:**
```css
/* Bootstrap 5 breakpoints */
xs: 0px      /* Mobile portrait */
sm: 576px    /* Mobile landscape */
md: 768px    /* Tablet */
lg: 992px    /* Desktop */
xl: 1200px   /* Large desktop */
xxl: 1400px  /* Extra large */
```

**Common patterns:**
```html
<!-- Stats (4 columns, always horizontal) -->
<div class="row g-2">
    <div class="col-3">...</div>
    <div class="col-3">...</div>
    <div class="col-3">...</div>
    <div class="col-3">...</div>
</div>

<!-- Buttons (3 columns, always horizontal) -->
<div class="row g-2">
    <div class="col-4">...</div>
    <div class="col-4">...</div>
    <div class="col-4">...</div>
</div>

<!-- Items (responsive grid) -->
<div class="row">
    <div class="col-6 col-md-4 col-lg-3 col-xl-2">...</div>
</div>
```

### Spacing System

```html
<!-- Gap между элементами в ряду -->
<div class="row g-2">  <!-- 0.5rem gap -->
<div class="row g-3">  <!-- 1rem gap -->

<!-- Margin bottom между секциями -->
<div class="mb-2">  <!-- 0.5rem -->
<div class="mb-3">  <!-- 1rem -->
<div class="mb-4">  <!-- 1.5rem -->

<!-- Padding внутри карточек -->
<div class="card-body p-2">  <!-- Mobile: compact -->
<div class="card-body p-3">  <!-- Desktop: comfortable -->
```

---

## 🔄 Interactive Patterns

### Infinite Scroll Algorithm

**Псевдокод:**
```
1. Initialize:
   - currentOffset = 0
   - isLoading = false
   - hasMore = true
   - itemsPerPage = 30

2. On scroll:
   IF (not loading AND hasMore AND near bottom):
       loadMore()

3. loadMore():
   - Set isLoading = true
   - Show loading indicator
   - Fetch API: /api/items?limit=30&offset=currentOffset
   - IF response empty OR error:
       Set hasMore = false
   - ELSE:
       Append items to container
       currentOffset += items.length
       IF items.length < 30:
           Set hasMore = false
   - Hide loading indicator
   - Set isLoading = false

4. "Near bottom" check:
   scrollPosition = window.innerHeight + window.scrollY
   pageHeight = document.scrollHeight
   RETURN scrollPosition >= (pageHeight - 300)
```

### Auto-refresh Pattern

**Dashboard только:**
```javascript
// Refresh every 30 seconds (only if on first page)
setInterval(() => {
    // Don't refresh if user scrolled down
    if (currentOffset === 0 || currentOffset === itemsPerPage) {
        loadRecentItems(false);  // Replace content
    }
    refreshStats();  // Always refresh stats
}, 30000);
```

**Logs page:**
```javascript
// Refresh every 5 seconds
setInterval(() => {
    // Save scroll position
    const scrollPos = window.scrollY;

    fetch('/api/logs?level=' + currentLevel)
        .then(r => r.json())
        .then(data => {
            updateLogsTable(data.logs);
            window.scrollTo(0, scrollPos);  // Restore scroll
        });
}, 5000);
```

---

## 🎯 UX Принципы

### 1. Предотвращение раздражения

**Проблема:** Auto-refresh сбрасывает позицию скролла
**Решение:**
```javascript
const scrollPos = window.scrollY;
// ... update content ...
window.scrollTo(0, scrollPos);
```

**Проблема:** Бесконечная загрузка пока юзер скроллит
**Решение:**
```javascript
let isLoading = false;

function loadMore() {
    if (isLoading) return;  // Guard
    isLoading = true;
    // ... load ...
    isLoading = false;
}
```

### 2. Визуальный фидбек

**Loading states:**
```html
<!-- Button loading -->
<button onclick="scan()">
    <span class="spinner-border spinner-border-sm"></span>
    Scanning...
</button>

<!-- Page loading -->
<div class="spinner-border text-primary">
    <span class="visually-hidden">Loading...</span>
</div>
```

**Empty states:**
```html
<div class="col-12 text-center py-5">
    <i class="bi bi-inbox" style="font-size: 3rem; color: #ccc;"></i>
    <p class="text-muted mt-2">No items found yet</p>
    <small>Items will appear here after first scan</small>
</div>
```

**Error states:**
```html
<div class="alert alert-danger">
    <i class="bi bi-exclamation-triangle me-2"></i>
    Failed to load items. Please try again.
</div>
```

### 3. Touch-friendly

**Minimum touch target:** 44x44px
```css
/* Good */
.btn {
    padding: 0.4rem 0.75rem;  /* At least 44px height */
}

/* Bad */
.btn-tiny {
    padding: 0.1rem 0.3rem;   /* Too small to tap */
}
```

**Tap area expansion:**
```html
<!-- Entire card is clickable, not just title -->
<div class="card">
    <a href="/item/123" class="stretched-link">
        <img src="...">
        <h6>Item title</h6>
    </a>
</div>
```

---

## 🚀 Performance Optimization

### Lazy Loading Images

```html
<img src="image.jpg"
     loading="lazy"              <!-- Native lazy load -->
     decoding="async"            <!-- Async decode -->
     referrerpolicy="no-referrer"
     crossorigin="anonymous">
```

### Debounce Scroll Events

```javascript
let scrollTimeout;
window.addEventListener('scroll', () => {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
        checkInfiniteScroll();
    }, 100);  // Wait 100ms after scroll stops
});
```

### Batch DOM Updates

```javascript
// Bad: Multiple DOM writes
items.forEach(item => {
    container.innerHTML += renderCard(item);  // SLOW!
});

// Good: Single DOM write
let html = '';
items.forEach(item => {
    html += renderCard(item);
});
container.insertAdjacentHTML('beforeend', html);
```

### Image Optimization

```javascript
// Use appropriate image sizes
const imageUrl = item.photos[0]
    .replace('/orig/', '/c!/w=400/')  // Mobile: 400px width
    .replace('.jpg', '.webp');         // WebP format
```

---

## 📋 Checklist для внедрения

### Обязательные элементы:

- [ ] **Navbar:** Sticky с брендингом "powered by extndd"
- [ ] **Dashboard stats:** 4 колонки (`col-3`) в один ряд
- [ ] **Action buttons:** 3 кнопки (`col-4`) горизонтально, иконки на мобильных
- [ ] **Cards grid:** Responsive (`col-6` → `col-md-4` → `col-lg-3` → `col-xl-2`)
- [ ] **Card style:** Aspect ratio 4:5, shadow, компактный padding
- [ ] **Infinite scroll:** 30 items per load, offset-based
- [ ] **Loading indicator:** Показывать при подгрузке
- [ ] **Empty state:** Иконка + текст когда нет данных
- [ ] **Error handling:** Показывать ошибки пользователю
- [ ] **Logs page:** Карточный стиль на мобильных, фильтры горизонтально
- [ ] **Auto-refresh:** Без сброса позиции скролла
- [ ] **Touch targets:** Минимум 44x44px
- [ ] **Lazy loading:** Для всех изображений

### Опциональные улучшения:

- [ ] Pull-to-refresh на мобильных
- [ ] Swipe gestures для навигации
- [ ] Progressive Web App (PWA)
- [ ] Offline support
- [ ] Dark mode toggle
- [ ] Skeleton screens вместо spinners

---

## 💡 Примеры адаптации для других проектов

### VS5 (VintedSearcher)

**Специфика:**
- Товары с Vinted (другой маркетплейс)
- Больше фильтров (размер, бренд, состояние)
- Цены в EUR вместо JPY

**Адаптация:**
```html
<!-- Stats: добавить колонку Filters -->
<div class="col-3">
    <div class="card-body p-2 text-center">
        <div class="small text-muted mb-1" style="font-size: 0.7rem;">Filters</div>
        <div class="fw-bold" style="font-size: 1.2rem;">12</div>
        <div class="small text-info" style="font-size: 0.65rem;">active</div>
    </div>
</div>

<!-- Price: EUR вместо JPY -->
<div class="mb-1">
    <div class="fw-bold text-dark" style="font-size: 1.1rem;">€${eur_price}</div>
</div>

<!-- Extra badges: Brand + Size -->
<div class="d-flex gap-1 flex-wrap">
    <span class="badge bg-secondary" style="font-size: 0.6rem;">Nike</span>
    <span class="badge bg-info" style="font-size: 0.6rem;">M</span>
</div>
```

### KFS (KufarSearcher)

**Специфика:**
- Товары с Kufar (белорусский маркетплейс)
- Цены в BYN
- Локация важна (город)

**Адаптация:**
```html
<!-- Price: BYN -->
<div class="mb-1">
    <div class="fw-bold text-dark" style="font-size: 1.1rem;">Br${byn_price}</div>
    <div class="text-muted" style="font-size: 0.7rem;">≈ $${usd_price}</div>
</div>

<!-- Location badge -->
<span class="badge bg-warning text-dark" style="font-size: 0.6rem;">
    <i class="bi bi-geo-alt"></i> Minsk
</span>
```

---

## 📚 Технологии

### Required:
- **Bootstrap 5.3+** для grid и компонентов
- **Bootstrap Icons** для иконок
- **Vanilla JavaScript** для infinite scroll (без jQuery!)
- **Fetch API** для AJAX запросов

### Optional:
- **Swiper.js** для галерей изображений
- **Intersection Observer API** для lazy loading
- **Service Workers** для offline support

---

## 🔗 Ссылки

### Референсы:
- **MercariSearcher:** https://web-production-fe38.up.railway.app/
- **Bootstrap Docs:** https://getbootstrap.com/docs/5.3/
- **Bootstrap Icons:** https://icons.getbootstrap.com/

### Тестирование:
- **Mobile simulator:** Chrome DevTools (Cmd+Opt+I → Toggle device)
- **Real devices:** iPhone SE (минимальная ширина 375px)
- **Lighthouse:** Проверка performance и accessibility

---

## ✅ Финальный чеклист перед деплоем

### Мобильная версия:
- [ ] Тестирование на iPhone SE (375px)
- [ ] Тестирование на Android (360px)
- [ ] Navbar не перекрывает контент
- [ ] Все кнопки тапабельные (44x44px min)
- [ ] Нет горизонтального скролла
- [ ] Infinite scroll работает плавно
- [ ] Изображения загружаются lazy
- [ ] Шрифты читабельные (min 0.7rem)

### Desktop версия:
- [ ] Grid адаптируется (2→3→4→6 колонок)
- [ ] Navbar полная (с текстом)
- [ ] Hover эффекты работают
- [ ] Клики не конфликтуют с тапами

### Performance:
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Lighthouse score > 90
- [ ] No console errors

---

**Дата создания:** 2025-11-20
**Версия:** 1.0
**Автор:** Claude (based on MercariSearcher implementation)
**Проект-эталон:** MercariSearcher v1.0
