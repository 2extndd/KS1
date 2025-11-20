# 🎨 Branding & Logo Pattern Guide

Руководство по созданию единообразного брендинга для всех ваших marketplace bot проектов.

## 📋 Содержание
1. [Структура логотипа](#структура-логотипа)
2. [HTML разметка](#html-разметка)
3. [CSS стили](#css-стили)
4. [Примеры для разных проектов](#примеры-для-разных-проектов)
5. [Цветовая палитра](#цветовая-палитра)
6. [Адаптация под мобильные](#адаптация-под-мобильные)

---

## Структура логотипа

### Общий паттерн

```
[ProjectName]Searcher
    powered by extndd
```

**Формат:**
- **Первая строка:** Название проекта + "Searcher" (без пробела)
- **Вторая строка:** "powered by" + ваш бренд со ссылкой

**Пример:**
- `MercariSearcher`
- `KufarSearcher`
- `VintedSearcher`
- `WildberriesSearcher`

---

## HTML разметка

### Базовая структура navbar

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm" style="padding: 0.75rem 0;">
    <div class="container-fluid">
        <!-- Logo Section -->
        <div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
            <!-- Main Title -->
            <a href="/" class="text-decoration-none text-white">
                <span class="brand-title" style="font-size: 1.25rem; font-weight: 600;">
                    [Project]Searcher
                </span>
            </a>

            <!-- Subtitle with branding -->
            <span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
                powered by
                <a href="https://t.me/extndd" target="_blank"
                   class="text-decoration-none"
                   style="color: #0dcaf0;">
                    extndd
                </a>
            </span>
        </div>

        <!-- Mobile menu toggle -->
        <button class="navbar-toggler" type="button"
                data-bs-toggle="collapse"
                data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>

        <!-- Navigation links -->
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
                <li class="nav-item">
                    <a class="nav-link" href="/">
                        <i class="bi bi-speedometer2"></i> Dashboard
                    </a>
                </li>
                <!-- More nav items... -->
            </ul>
        </div>
    </div>
</nav>
```

---

## CSS стили

### Базовые стили navbar

```css
/* Navigation */
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
```

### Адаптация для desktop (увеличенный размер)

```css
/* Larger navbar on desktop */
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

### Мобильные устройства

```css
@media (max-width: 768px) {
    .navbar-nav .nav-link {
        margin: 0.125rem 0;
    }
}
```

---

## Примеры для разных проектов

### 1. MercariSearcher (текущий)

```html
<div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
    <a href="/" class="text-decoration-none text-white">
        <span class="brand-title" style="font-size: 1.25rem; font-weight: 600;">
            MercariSearcher
        </span>
    </a>
    <span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
        powered by <a href="https://t.me/extndd" target="_blank"
                       class="text-decoration-none"
                       style="color: #0dcaf0;">extndd</a>
    </span>
</div>
```

**Title tag:**
```html
<title>{% block title %}MercariSearcher{% endblock %}</title>
```

---

### 2. KufarSearcher

```html
<div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
    <a href="/" class="text-decoration-none text-white">
        <span class="brand-title" style="font-size: 1.25rem; font-weight: 600;">
            KufarSearcher
        </span>
    </a>
    <span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
        powered by <a href="https://t.me/extndd" target="_blank"
                       class="text-decoration-none"
                       style="color: #0dcaf0;">extndd</a>
    </span>
</div>
```

**Title tag:**
```html
<title>{% block title %}KufarSearcher{% endblock %}</title>
```

**Favicon:** Замените `favicon.svg` на Kufar-themed SVG

---

### 3. VintedSearcher

```html
<div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
    <a href="/" class="text-decoration-none text-white">
        <span class="brand-title" style="font-size: 1.25rem; font-weight: 600;">
            VintedSearcher
        </span>
    </a>
    <span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
        powered by <a href="https://t.me/extndd" target="_blank"
                       class="text-decoration-none"
                       style="color: #0dcaf0;">extndd</a>
    </span>
</div>
```

**Title tag:**
```html
<title>{% block title %}VintedSearcher{% endblock %}</title>
```

---

### 4. WildberriesSearcher

```html
<div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
    <a href="/" class="text-decoration-none text-white">
        <span class="brand-title" style="font-size: 1.25rem; font-weight: 600;">
            WildberriesSearcher
        </span>
    </a>
    <span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
        powered by <a href="https://t.me/extndd" target="_blank"
                       class="text-decoration-none"
                       style="color: #0dcaf0;">extndd</a>
    </span>
</div>
```

**Title tag:**
```html
<title>{% block title %}WildberriesSearcher{% endblock %}</title>
```

---

## Цветовая палитра

### Navbar colors

| Элемент | Светлая тема | Темная тема |
|---------|-------------|-------------|
| Background | `bg-dark` (#343a40) | `bg-dark` (#343a40) |
| Main title | `#ffffff` | `#ffffff` |
| Subtitle text | `#adb5bd` | `#adb5bd` |
| Brand link | `#0dcaf0` | `#0dcaf0` |
| Nav link | `rgba(255,255,255,0.55)` | `rgba(255,255,255,0.55)` |
| Nav link hover | `rgba(255,255,255,0.75)` | `rgba(255,255,255,0.75)` |

### Accent colors для разных проектов

**MercariSearcher:**
- Accent: `#0dcaf0` (циановый)
- Logo colors: Red (#ff0000), blue (#0dcaf0)

**KufarSearcher:**
- Accent: `#00a859` (зеленый Kufar)
- Logo colors: Green (#00a859)

**VintedSearcher:**
- Accent: `#09b1ba` (бирюзовый Vinted)
- Logo colors: Teal (#09b1ba)

**WildberriesSearcher:**
- Accent: `#cb11ab` (пурпурный Wildberries)
- Logo colors: Purple (#cb11ab)

### Применение accent color

```html
<span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
    powered by <a href="https://t.me/extndd" target="_blank"
                   class="text-decoration-none"
                   style="color: [YOUR-ACCENT-COLOR];">extndd</a>
</span>
```

---

## Адаптация под мобильные

### Responsive font sizes

```css
/* Mobile (< 768px) */
.brand-title {
    font-size: 1.25rem;
}

.brand-subtitle {
    font-size: 0.7rem;
}

/* Desktop (>= 992px) */
@media (min-width: 992px) {
    .brand-title {
        font-size: 1.5rem !important;
    }

    .brand-subtitle {
        font-size: 0.8rem !important;
    }
}
```

### Sticky navbar

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm">
```

Классы:
- `sticky-top` - navbar остается видимым при скролле
- `shadow-sm` - небольшая тень для визуального разделения

---

## 🎯 Чеклист для адаптации

### HTML
- [ ] Заменить название проекта в `brand-title`
- [ ] Обновить `<title>` в base.html
- [ ] Добавить классы `brand-title` и `brand-subtitle`
- [ ] Убедиться в структуре: `d-flex flex-column` для вертикального расположения

### CSS
- [ ] Добавить стили для `.brand-title` и `.brand-subtitle`
- [ ] Добавить медиа-запросы для desktop (>= 992px)
- [ ] Настроить accent color для ссылки "extndd"
- [ ] Проверить responsive поведение на мобильных

### Favicon
- [ ] Создать/заменить `favicon.svg` в папке static
- [ ] Убедиться, что favicon соответствует тематике проекта

### Testing
- [ ] Проверить отображение на мобильных (< 768px)
- [ ] Проверить отображение на планшетах (768px - 992px)
- [ ] Проверить отображение на desktop (>= 992px)
- [ ] Проверить sticky navbar при скролле
- [ ] Проверить ссылку на Telegram extndd

---

## 📝 Шаблон для быстрого копирования

```html
<!-- Copy this to your base.html -->
<nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top shadow-sm" style="padding: 0.75rem 0;">
    <div class="container-fluid">
        <div class="navbar-brand d-flex flex-column" style="line-height: 1.2;">
            <a href="/" class="text-decoration-none text-white">
                <span class="brand-title" style="font-size: 1.25rem; font-weight: 600;">
                    [YourProject]Searcher
                </span>
            </a>
            <span class="brand-subtitle" style="font-size: 0.7rem; color: #adb5bd; margin-top: -3px;">
                powered by <a href="https://t.me/extndd" target="_blank"
                               class="text-decoration-none"
                               style="color: #0dcaf0;">extndd</a>
            </span>
        </div>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav">
                <!-- Your navigation items -->
            </ul>
        </div>
    </div>
</nav>
```

```css
/* Copy this to your style.css */
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

---

## 🎨 Визуальная иерархия

```
┌─────────────────────────────────────┐
│  [Project]Searcher  ← Крупный, bold │
│  powered by extndd  ← Мелкий, muted │
└─────────────────────────────────────┘
```

**Принципы:**
1. **Главное название** - самый крупный, жирный шрифт
2. **Подпись** - мелкий шрифт, приглушенный цвет
3. **Бренд-ссылка** - accent color для привлечения внимания
4. **Вертикальное выравнивание** - две строки друг под другом
5. **Никаких вложенных ссылок** - `<div>` содержит две отдельные ссылки

---

**Создано на основе MercariSearcher v1.0**
*Единообразный брендинг для всех marketplace bot проектов*
