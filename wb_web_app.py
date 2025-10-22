from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import json
import os
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = 'wb_analytics_secret_key_2024'

# Глобальные переменные для сессии
user_session = {
    'authenticated': False,
    'phone': None,
    'token': None,
    'products': []
}

class WBWebParser:
    def __init__(self):
        self.session = requests.Session()
    
    def get_product_info(self, article):
        """Получает информацию о товаре по артикулу"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        }
        api_url = f"https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}"
        
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get('data', {}).get('products'):
                product = data['data']['products'][0]
                return {
                    'article': product.get('id'),
                    'name': product.get('name'),
                    'price': product.get('priceU') / 100 if product.get('priceU') else None,
                    'old_price': product.get('salePriceU') / 100 if product.get('salePriceU') else None,
                    'discount': product.get('discount'),
                    'rating': product.get('rating'),
                    'reviews': product.get('feedbacks'),
                    'url': f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return None
        except Exception as e:
            logging.error(f"Ошибка при получении данных для артикула {article}: {e}")
            return None
    
    def parse_multiple_articles(self, articles):
        """Парсит несколько артикулов"""
        results = []
        failed_articles = []
        
        for i, article in enumerate(articles):
            logging.info(f"Обработка артикула {i+1}/{len(articles)}: {article}")
            product_info = self.get_product_info(article)
            
            if product_info:
                results.append(product_info)
            else:
                failed_articles.append(article)
            
            # Небольшая задержка между запросами
            time.sleep(1)
        
        return results, failed_articles

# Инициализация парсера
parser = WBWebParser()

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница авторизации"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        sms_code = request.form.get('sms_code')
        
        if phone and sms_code:
            # Простая проверка (в реальной версии здесь была бы SMS авторизация)
            if sms_code == '1234':  # Тестовый код
                user_session['authenticated'] = True
                user_session['phone'] = phone
                user_session['token'] = 'test_token_12345'
                flash('Авторизация успешна!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Неверный SMS код', 'error')
        else:
            flash('Заполните все поля', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Панель управления"""
    if not user_session['authenticated']:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', products=user_session['products'])

@app.route('/parse', methods=['POST'])
def parse_products():
    """API для парсинга товаров"""
    if not user_session['authenticated']:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.get_json()
    articles = data.get('articles', [])
    
    if not articles:
        return jsonify({'error': 'Не указаны артикулы'}), 400
    
    try:
        results, failed = parser.parse_multiple_articles(articles)
        user_session['products'] = results
        
        return jsonify({
            'success': True,
            'products': results,
            'failed_articles': failed,
            'total_parsed': len(results),
            'total_failed': len(failed)
        })
    except Exception as e:
        logging.error(f"Ошибка при парсинге: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/export/<format>')
def export_data(format):
    """Экспорт данных"""
    if not user_session['authenticated']:
        return redirect(url_for('login'))
    
    products = user_session['products']
    if not products:
        flash('Нет данных для экспорта', 'error')
        return redirect(url_for('dashboard'))
    
    if format == 'json':
        return jsonify(products)
    elif format == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        writer.writerow(['Артикул', 'Название', 'Цена', 'Старая цена', 'Скидка', 'Рейтинг', 'Отзывы', 'URL', 'Время'])
        
        # Данные
        for product in products:
            writer.writerow([
                product['article'],
                product['name'],
                product['price'],
                product['old_price'],
                product['discount'],
                product['rating'],
                product['reviews'],
                product['url'],
                product['timestamp']
            ])
        
        output.seek(0)
        return output.getvalue(), 200, {'Content-Type': 'text/csv; charset=utf-8'}
    else:
        flash('Неподдерживаемый формат', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Выход из системы"""
    user_session['authenticated'] = False
    user_session['phone'] = None
    user_session['token'] = None
    user_session['products'] = []
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    import os
    
    # Настройки для продакшена
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("Запуск веб-версии парсера Wildberries")
    print("=" * 50)
    print(f"Сервер запущен на порту: {port}")
    print(f"Debug режим: {debug}")
    print("=" * 50)
    
    app.run(debug=debug, host='0.0.0.0', port=port)