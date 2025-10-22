# WB Analytics - Веб-версия парсера Wildberries

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Описание

Веб-версия парсера Wildberries для анализа товаров, отслеживания цен и получения уведомлений о изменениях.

## ✨ Возможности

- **Парсинг товаров** по артикулам
- **Анализ цен** и трендов
- **Экспорт данных** в различных форматах (CSV, JSON)
- **Веб-интерфейс** с современным дизайном
- **Авторизация** пользователей
- **Отслеживание истории** цен

## 🛠 Технологии

- **Backend**: Flask, Python 3.11+
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Парсинг**: requests
- **Анализ данных**: pandas, openpyxl

## 📦 Установка

### Локальная установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/YOUR_USERNAME/wb-analytics.git
cd wb-analytics
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Запустите приложение:**
```bash
python wb_web_app.py
```

4. **Откройте браузер:**
```
http://localhost:5000
```

### Деплой на облачных платформах

#### Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy)

#### Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

#### Heroku
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 🎯 Использование

### 1. Авторизация
- Введите номер телефона
- Для тестирования используйте SMS код: `1234`

### 2. Парсинг товаров
- Введите артикулы товаров (по одному на строку)
- Нажмите "Начать парсинг"
- Дождитесь результатов

### 3. Экспорт данных
- Нажмите "Экспорт CSV" для сохранения в CSV
- Нажмите "Экспорт JSON" для сохранения в JSON

## 📁 Структура проекта

```
wb-analytics/
├── wb_web_app.py          # Основное Flask приложение
├── requirements.txt        # Зависимости Python
├── Procfile              # Конфигурация для Heroku
├── runtime.txt           # Версия Python
├── railway.toml          # Конфигурация для Railway
├── .gitignore           # Игнорируемые файлы
├── templates/           # HTML шаблоны
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   └── dashboard.html
└── README.md            # Документация
```

## 🔧 API Endpoints

- `GET /` - Главная страница
- `GET /login` - Страница авторизации
- `POST /login` - Авторизация пользователя
- `GET /dashboard` - Панель управления
- `POST /parse` - Парсинг товаров
- `GET /export/<format>` - Экспорт данных
- `GET /logout` - Выход из системы

## 📊 Примеры использования

### Парсинг товаров
```javascript
fetch('/parse', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        articles: ['182168410', '275545719', '159808254']
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

### Экспорт данных
```javascript
// CSV экспорт
window.open('/export/csv');

// JSON экспорт
fetch('/export/json')
.then(response => response.json())
.then(data => console.log(data));
```

## 🚀 Деплой

### Railway
1. Подключите GitHub репозиторий
2. Railway автоматически определит настройки
3. Приложение будет доступно по URL

### Render
1. Создайте новый Web Service
2. Подключите GitHub репозиторий
3. Настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python wb_web_app.py`

### Heroku
1. Создайте приложение на Heroku
2. Подключите GitHub репозиторий
3. Включите автоматический деплой

## 🔒 Безопасность

- Авторизация пользователей
- Защита от CSRF атак
- Валидация входных данных
- Безопасное хранение сессий

## 📈 Мониторинг

- Логирование всех операций
- Отслеживание ошибок
- Статистика использования

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 📞 Поддержка

Если у вас есть вопросы или проблемы:

1. Создайте Issue в GitHub
2. Опишите проблему подробно
3. Приложите логи ошибок

## 🎉 Благодарности

- Wildberries за предоставление API
- Flask сообществу за отличный фреймворк
- Bootstrap за красивые компоненты

---

**Сделано с ❤️ для анализа товаров Wildberries**
