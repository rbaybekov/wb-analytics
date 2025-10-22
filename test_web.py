#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простое тестовое веб-приложение для проверки
"""

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WB Analytics - Тест</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body text-center">
                        <h1 class="text-danger">WB Analytics</h1>
                        <p class="lead">Веб-версия парсера Wildberries</p>
                        <div class="alert alert-success">
                            <strong>Сервер работает!</strong><br>
                            Flask приложение успешно запущено.
                        </div>
                        <p>Номер телефона для авторизации: <strong>+79264845850</strong></p>
                        <a href="/login" class="btn btn-primary">Перейти к авторизации</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

@app.route('/login')
def login():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WB Analytics - Авторизация</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h3 class="text-center text-danger">SMS Авторизация</h3>
                        <form>
                            <div class="mb-3">
                                <label for="phone" class="form-label">Номер телефона</label>
                                <input type="tel" class="form-control" id="phone" value="+79264845850" readonly>
                            </div>
                            <div class="mb-3">
                                <label for="smsCode" class="form-label">SMS код</label>
                                <input type="text" class="form-control" id="smsCode" placeholder="Введите код из SMS">
                            </div>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">Подтвердить</button>
                            </div>
                        </form>
                        <div class="alert alert-info mt-3">
                            <strong>Тестовая версия</strong><br>
                            Введите любой код для продолжения.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    ''')

if __name__ == '__main__':
    print("Запуск тестового веб-приложения")
    print("=" * 40)
    print("Откройте браузер: http://localhost:5000")
    print("=" * 40)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
