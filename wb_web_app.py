#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-версия парсера Wildberries с авторизацией через SMS
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
import json
import time
import random
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)
app.secret_key = 'wb_analytics_secret_key_2025'

@dataclass
class ProductInfo:
    """Класс для хранения информации о товаре"""
    article: str
    name: str
    price: float
    old_price: Optional[float] = None
    discount: Optional[int] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    url: str = ""
    stock: Optional[int] = None
    sales: Optional[int] = None
    brand: Optional[str] = None
    category: Optional[str] = None

class WildberriesWebAuth:
    """Класс для авторизации через веб-интерфейс"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://seller.wildberries.ru"
        
        # Настройка сессии
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://seller.wildberries.ru/',
        })
    
    def normalize_phone(self, phone: str) -> str:
        """Нормализация номера телефона"""
        digits = re.sub(r'\D', '', phone)
        
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        
        if digits.startswith('7'):
            return '+' + digits
        
        return '+7' + digits
    
    def send_sms_code(self, phone: str) -> Dict[str, any]:
        """Отправить SMS код"""
        try:
            phone = self.normalize_phone(phone)
            logger.info(f"Отправка SMS кода на номер: {phone}")
            
            # Различные endpoints для отправки SMS
            sms_endpoints = [
                f"{self.base_url}/ns/sm/supplier-manager/api/v1/auth/sms/send",
                f"{self.base_url}/api/v1/auth/sms/send",
                f"{self.base_url}/auth/sms/send",
                f"{self.base_url}/login/sms/send",
            ]
            
            data = {
                'phone': phone,
                'type': 'login'
            }
            
            for endpoint in sms_endpoints:
                try:
                    response = self.session.post(endpoint, json=data, timeout=15)
                    logger.info(f"SMS endpoint {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        logger.info(f"SMS ответ: {response_data}")
                        return {
                            'success': True,
                            'message': 'SMS код отправлен',
                            'data': response_data
                        }
                    elif response.status_code == 201:
                        return {
                            'success': True,
                            'message': 'SMS код отправлен',
                            'data': response.json() if response.content else {}
                        }
                    else:
                        logger.warning(f"SMS ошибка {response.status_code}: {response.text[:200]}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка SMS endpoint {endpoint}: {e}")
                    continue
            
            # Если все endpoints не сработали, пробуем альтернативный способ
            return self._try_alternative_sms(phone)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке SMS: {e}")
            return {
                'success': False,
                'message': f'Ошибка отправки SMS: {str(e)}'
            }
    
    def _try_alternative_sms(self, phone: str) -> Dict[str, any]:
        """Альтернативный способ отправки SMS"""
        try:
            # Пробуем через главную страницу
            main_url = f"{self.base_url}/"
            response = self.session.get(main_url, timeout=10)
            
            if response.status_code == 200:
                # Ищем формы авторизации в HTML
                html = response.text
                
                # Ищем скрытые поля или токены
                csrf_patterns = [
                    r'name="csrf_token"[^>]*value="([^"]*)"',
                    r'name="_token"[^>]*value="([^"]*)"',
                    r'csrf-token["\']?\s*content=["\']([^"\']*)["\']',
                ]
                
                csrf_token = None
                for pattern in csrf_patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        csrf_token = match.group(1)
                        break
                
                # Пробуем отправить SMS с CSRF токеном
                if csrf_token:
                    sms_data = {
                        'phone': phone,
                        'csrf_token': csrf_token,
                        '_token': csrf_token
                    }
                    
                    sms_response = self.session.post(
                        f"{self.base_url}/auth/sms",
                        data=sms_data,
                        timeout=15
                    )
                    
                    if sms_response.status_code in [200, 201]:
                        return {
                            'success': True,
                            'message': 'SMS код отправлен (альтернативный способ)'
                        }
            
            return {
                'success': False,
                'message': 'Не удалось отправить SMS код'
            }
            
        except Exception as e:
            logger.error(f"Ошибка альтернативного SMS: {e}")
            return {
                'success': False,
                'message': f'Ошибка альтернативного SMS: {str(e)}'
            }
    
    def verify_sms_code(self, phone: str, sms_code: str) -> Dict[str, any]:
        """Проверить SMS код"""
        try:
            phone = self.normalize_phone(phone)
            logger.info(f"Проверка SMS кода для номера: {phone}")
            
            # Различные endpoints для проверки SMS
            verify_endpoints = [
                f"{self.base_url}/ns/sm/supplier-manager/api/v1/auth/sms/verify",
                f"{self.base_url}/api/v1/auth/sms/verify",
                f"{self.base_url}/auth/sms/verify",
                f"{self.base_url}/login/sms/verify",
            ]
            
            data = {
                'phone': phone,
                'code': sms_code
            }
            
            for endpoint in verify_endpoints:
                try:
                    response = self.session.post(endpoint, json=data, timeout=15)
                    logger.info(f"Verify endpoint {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        logger.info(f"Verify ответ: {response_data}")
                        
                        # Ищем токен в ответе
                        token = self._extract_token(response_data)
                        if token:
                            return {
                                'success': True,
                                'message': 'Авторизация успешна',
                                'token': token,
                                'data': response_data
                            }
                        else:
                            return {
                                'success': True,
                                'message': 'Код верный, но токен не найден',
                                'data': response_data
                            }
                    else:
                        logger.warning(f"Verify ошибка {response.status_code}: {response.text[:200]}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка verify endpoint {endpoint}: {e}")
                    continue
            
            return {
                'success': False,
                'message': 'Неверный SMS код'
            }
            
        except Exception as e:
            logger.error(f"Ошибка при проверке SMS: {e}")
            return {
                'success': False,
                'message': f'Ошибка проверки SMS: {str(e)}'
            }
    
    def _extract_token(self, response_data: Dict[str, any]) -> Optional[str]:
        """Извлечь токен из ответа"""
        token_fields = [
            'token', 'jwt', 'access_token', 'accessToken',
            'auth_token', 'authToken', 'bearer_token', 'bearerToken'
        ]
        
        # Поиск в корневом уровне
        for field in token_fields:
            if field in response_data:
                token = response_data[field]
                if isinstance(token, str) and len(token) > 10:
                    return token
        
        # Поиск в data
        if 'data' in response_data:
            for field in token_fields:
                if field in response_data['data']:
                    token = response_data['data'][field]
                    if isinstance(token, str) and len(token) > 10:
                        return token
        
        # Поиск в cookies
        for cookie in self.session.cookies:
            if 'token' in cookie.name.lower():
                if len(cookie.value) > 10:
                    return cookie.value
        
        return None

class WildberriesWebParser:
    """Веб-версия парсера Wildberries"""
    
    def __init__(self, token: str = None):
        self.token = token
        self.session = requests.Session()
        self.base_url = "https://seller.wildberries.ru"
        
        # Настройка сессии
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://seller.wildberries.ru/',
        })
        
        if self.token:
            self.set_token(self.token)
    
    def set_token(self, token: str):
        """Установка токена авторизации"""
        self.token = token
        
        # Пробуем разные способы авторизации
        auth_methods = [
            {'Authorization': f'Bearer {token}'},
            {'X-Auth-Token': token},
            {'Cookie': f'WBToken={token}; wb_token={token}'}
        ]
        
        for method in auth_methods:
            self.session.headers.update(method)
    
    def get_product_info(self, article: str) -> Optional[ProductInfo]:
        """Получить информацию о товаре"""
        try:
            logger.info(f"Получение информации о товаре: {article}")
            
            endpoints = [
                f"/ns/sm/supplier-manager/api/v1/supplier/products/{article}",
                f"/api/v1/supplier/products/{article}",
            ]
            
            for endpoint in endpoints:
                url = self.base_url + endpoint
                
                try:
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        product = self._parse_product_data(data, article)
                        if product:
                            return product
                    
                except Exception as e:
                    logger.warning(f"Ошибка для {endpoint}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка для артикула {article}: {e}")
            return None
    
    def _parse_product_data(self, data: dict, article: str) -> Optional[ProductInfo]:
        """Парсинг данных товара"""
        try:
            product_data = None
            
            if 'data' in data:
                product_data = data['data']
            elif 'product' in data:
                product_data = data['product']
            elif isinstance(data, dict) and 'id' in data:
                product_data = data
            else:
                return None
            
            if not product_data:
                return None
            
            name = product_data.get('name', product_data.get('title', ''))
            price = self._extract_price(product_data)
            old_price = self._extract_old_price(product_data)
            discount = product_data.get('discount', product_data.get('sale', 0))
            rating = product_data.get('rating', product_data.get('reviewRating', 0))
            reviews_count = product_data.get('reviews', product_data.get('feedbacks', 0))
            stock = product_data.get('stock', product_data.get('quantity', 0))
            sales = product_data.get('sales', product_data.get('sold', 0))
            brand = product_data.get('brand', product_data.get('brandName', ''))
            category = product_data.get('category', product_data.get('categoryName', ''))
            
            return ProductInfo(
                article=article,
                name=name,
                price=price,
                old_price=old_price,
                discount=discount,
                rating=rating,
                reviews_count=reviews_count,
                url=f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
                stock=stock,
                sales=sales,
                brand=brand,
                category=category
            )
            
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}")
            return None
    
    def _extract_price(self, product_data: dict) -> float:
        """Извлечь цену"""
        price_fields = ['price', 'priceU', 'currentPrice', 'salePrice']
        
        for field in price_fields:
            if field in product_data:
                price = product_data[field]
                if isinstance(price, (int, float)):
                    if price > 1000:
                        return price / 100
                    return float(price)
        
        return 0.0
    
    def _extract_old_price(self, product_data: dict) -> Optional[float]:
        """Извлечь старую цену"""
        old_price_fields = ['oldPrice', 'originalPrice', 'basePrice']
        
        for field in old_price_fields:
            if field in product_data:
                old_price = product_data[field]
                if isinstance(old_price, (int, float)) and old_price > 0:
                    if old_price > 1000:
                        return old_price / 100
                    return float(old_price)
        
        return None
    
    def get_products_list(self, limit: int = 100) -> List[ProductInfo]:
        """Получить список товаров"""
        try:
            url = f"{self.base_url}/ns/sm/supplier-manager/api/v1/supplier/products"
            
            params = {
                'limit': limit,
                'offset': 0
            }
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                products = []
                if 'data' in data:
                    for product_data in data['data']:
                        article = str(product_data.get('id', ''))
                        product = self._parse_product_data(product_data, article)
                        if product:
                            products.append(product)
                
                return products
            else:
                logger.error(f"Ошибка получения списка: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Ошибка получения списка: {e}")
            return []

# Инициализация классов
auth_manager = WildberriesWebAuth()
parser = WildberriesWebParser()

# Маршруты Flask
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Страница авторизации"""
    return render_template('login.html')

@app.route('/api/send-sms', methods=['POST'])
def send_sms():
    """API для отправки SMS кода"""
    try:
        data = request.get_json()
        phone = data.get('phone', '').strip()
        
        if not phone:
            return jsonify({
                'success': False,
                'message': 'Номер телефона не указан'
            })
        
        # Отправляем SMS код
        result = auth_manager.send_sms_code(phone)
        
        # Сохраняем номер телефона в сессии
        session['phone'] = phone
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка отправки SMS: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

@app.route('/api/verify-sms', methods=['POST'])
def verify_sms():
    """API для проверки SMS кода"""
    try:
        data = request.get_json()
        sms_code = data.get('code', '').strip()
        phone = session.get('phone', '')
        
        if not sms_code:
            return jsonify({
                'success': False,
                'message': 'SMS код не указан'
            })
        
        if not phone:
            return jsonify({
                'success': False,
                'message': 'Номер телефона не найден в сессии'
            })
        
        # Проверяем SMS код
        result = auth_manager.verify_sms_code(phone, sms_code)
        
        if result['success'] and 'token' in result:
            # Сохраняем токен в сессии
            session['token'] = result['token']
            session['authenticated'] = True
            
            # Настраиваем парсер с токеном
            parser.set_token(result['token'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка проверки SMS: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

@app.route('/dashboard')
def dashboard():
    """Панель управления"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/api/products')
def get_products():
    """API для получения списка товаров"""
    if not session.get('authenticated'):
        return jsonify({
            'success': False,
            'message': 'Не авторизован'
        })
    
    try:
        limit = request.args.get('limit', 50, type=int)
        products = parser.get_products_list(limit)
        
        # Преобразуем в словари для JSON
        products_data = [asdict(product) for product in products]
        
        return jsonify({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения товаров: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

@app.route('/api/product/<article>')
def get_product(article):
    """API для получения информации о товаре"""
    if not session.get('authenticated'):
        return jsonify({
            'success': False,
            'message': 'Не авторизован'
        })
    
    try:
        product = parser.get_product_info(article)
        
        if product:
            return jsonify({
                'success': True,
                'product': asdict(product)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Товар не найден'
            })
        
    except Exception as e:
        logger.error(f"Ошибка получения товара: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
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
