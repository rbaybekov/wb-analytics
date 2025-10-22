#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Альтернативная система авторизации для Wildberries Seller API
"""

import requests
import json
import time
import re
from typing import Optional, Dict, Any
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WildberriesAuthV2:
    """Альтернативный класс для авторизации в Wildberries Seller API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://seller.wildberries.ru"
        self.jwt_token = None
        
        # Настройка сессии
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://seller.wildberries.ru/',
        })
    
    def try_direct_auth(self, phone: str) -> Optional[str]:
        """
        Попытка прямой авторизации через Seller API
        
        Args:
            phone: Номер телефона
            
        Returns:
            JWT токен или None
        """
        try:
            phone = self._normalize_phone(phone)
            logger.info(f"Попытка прямой авторизации для номера: {phone}")
            
            # Различные endpoints для авторизации
            auth_endpoints = [
                f"{self.base_url}/ns/sm/supplier-manager/api/v1/auth/login",
                f"{self.base_url}/api/v1/auth/login",
                f"{self.base_url}/auth/login",
                f"{self.base_url}/login",
            ]
            
            for endpoint in auth_endpoints:
                logger.info(f"Пробуем endpoint: {endpoint}")
                
                # Данные для запроса
                data = {
                    'phone': phone,
                    'type': 'phone'
                }
                
                try:
                    response = self.session.post(endpoint, json=data, timeout=10)
                    logger.info(f"Статус: {response.status_code}")
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        logger.info(f"Ответ: {response_data}")
                        
                        token = self._extract_token(response_data)
                        if token:
                            self.jwt_token = token
                            return token
                    elif response.status_code == 401:
                        logger.info("Требуется SMS код")
                        return self._request_sms_code(phone, endpoint)
                    else:
                        logger.warning(f"Неожиданный статус: {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Ошибка для {endpoint}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при прямой авторизации: {e}")
            return None
    
    def _request_sms_code(self, phone: str, base_endpoint: str) -> Optional[str]:
        """Запросить SMS код"""
        try:
            logger.info("Запрос SMS кода...")
            
            # Endpoint для отправки SMS
            sms_endpoint = base_endpoint.replace('/login', '/sms/send')
            if sms_endpoint == base_endpoint:
                sms_endpoint = base_endpoint + '/sms'
            
            data = {
                'phone': phone,
                'action': 'login'
            }
            
            response = self.session.post(sms_endpoint, json=data, timeout=10)
            logger.info(f"SMS статус: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("SMS код отправлен")
                return "SMS_SENT"  # Специальный маркер
            else:
                logger.error(f"Ошибка отправки SMS: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при запросе SMS: {e}")
            return None
    
    def verify_with_sms(self, phone: str, sms_code: str, base_endpoint: str) -> Optional[str]:
        """Проверить SMS код"""
        try:
            logger.info("Проверка SMS кода...")
            
            # Endpoint для проверки SMS
            verify_endpoint = base_endpoint.replace('/login', '/sms/verify')
            if verify_endpoint == base_endpoint:
                verify_endpoint = base_endpoint + '/verify'
            
            data = {
                'phone': phone,
                'code': sms_code
            }
            
            response = self.session.post(verify_endpoint, json=data, timeout=10)
            logger.info(f"Проверка статус: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                token = self._extract_token(response_data)
                if token:
                    self.jwt_token = token
                    return token
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при проверке SMS: {e}")
            return None
    
    def try_web_auth(self, phone: str) -> Optional[str]:
        """
        Попытка авторизации через веб-интерфейс
        
        Args:
            phone: Номер телефона
            
        Returns:
            JWT токен или None
        """
        try:
            logger.info("Попытка авторизации через веб-интерфейс...")
            
            # Получаем главную страницу Seller
            main_url = f"{self.base_url}/"
            
            response = self.session.get(main_url, timeout=10)
            logger.info(f"Главная страница: {response.status_code}")
            
            if response.status_code == 200:
                html = response.text
                logger.info(f"HTML получен, размер: {len(html)} символов")
                
                # Ищем формы авторизации или API endpoints
                auth_patterns = [
                    r'api/v\d+/auth',
                    r'/auth/login',
                    r'/login',
                    r'passport',
                    r'auth'
                ]
                
                found_endpoints = []
                for pattern in auth_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    if matches:
                        found_endpoints.extend(matches)
                
                if found_endpoints:
                    logger.info(f"Найдены endpoints: {found_endpoints}")
                    
                    # Пробуем найденные endpoints
                    for endpoint in found_endpoints:
                        if not endpoint.startswith('/'):
                            endpoint = '/' + endpoint
                        
                        auth_url = self.base_url + endpoint
                        logger.info(f"Пробуем найденный endpoint: {auth_url}")
                        
                        data = {'phone': self._normalize_phone(phone)}
                        
                        try:
                            response = self.session.post(auth_url, json=data, timeout=10)
                            logger.info(f"Статус: {response.status_code}")
                            
                            if response.status_code == 200:
                                response_data = response.json()
                                token = self._extract_token(response_data)
                                if token:
                                    return token
                        except Exception as e:
                            logger.warning(f"Ошибка для {auth_url}: {e}")
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при веб-авторизации: {e}")
            return None
    
    def _normalize_phone(self, phone: str) -> str:
        """Нормализация номера телефона"""
        digits = re.sub(r'\D', '', phone)
        
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        
        if digits.startswith('7'):
            return '+' + digits
        
        return '+7' + digits
    
    def _extract_token(self, response_data: Dict[str, Any]) -> Optional[str]:
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
    
    def interactive_auth(self, phone: str) -> Optional[str]:
        """Интерактивная авторизация"""
        print(f"Авторизация в Wildberries Seller API")
        print(f"Номер телефона: {phone}")
        print("=" * 50)
        
        # Пробуем разные методы авторизации
        methods = [
            ("Прямая авторизация", self.try_direct_auth),
            ("Веб-авторизация", self.try_web_auth),
        ]
        
        for method_name, method_func in methods:
            print(f"\n{method_name}...")
            result = method_func(phone)
            
            if result == "SMS_SENT":
                print("SMS код отправлен!")
                
                # Запрашиваем код у пользователя
                while True:
                    sms_code = input("Введите SMS код: ").strip()
                    
                    if not sms_code.isdigit() or len(sms_code) < 4:
                        print("Введите корректный код")
                        continue
                    
                    # Пробуем проверить код
                    token = self.verify_with_sms(phone, sms_code, f"{self.base_url}/api/v1/auth/login")
                    
                    if token:
                        print("Авторизация успешна!")
                        return token
                    else:
                        print("Неверный код. Попробуйте еще раз.")
                        
                        retry = input("Попробовать еще раз? (y/n): ").strip().lower()
                        if retry not in ['y', 'yes', 'да', 'д']:
                            break
                        
            elif result:
                print(f"Авторизация успешна через {method_name}!")
                return result
            else:
                print(f"{method_name} не удалась")
        
        print("Все методы авторизации не удались")
        return None

def main():
    """Тестирование альтернативной авторизации"""
    auth = WildberriesAuthV2()
    
    phone = "+79264845850"
    
    print("Тест альтернативной авторизации")
    print("=" * 40)
    
    token = auth.interactive_auth(phone)
    
    if token:
        print(f"\nТокен получен: {token[:50]}...")
    else:
        print("\nАвторизация не удалась")

if __name__ == "__main__":
    main()
