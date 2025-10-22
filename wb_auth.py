#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Система авторизации для Wildberries Seller API
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

class WildberriesAuth:
    """Класс для авторизации в Wildberries Seller API"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://seller.wildberries.ru"
        self.auth_url = "https://passport.wildberries.ru"
        self.jwt_token = None
        
        # Настройка сессии
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def send_sms_code(self, phone: str) -> bool:
        """
        Отправить SMS код на номер телефона
        
        Args:
            phone: Номер телефона в формате +7XXXXXXXXXX
            
        Returns:
            True если код отправлен успешно
        """
        try:
            # Нормализуем номер телефона
            phone = self._normalize_phone(phone)
            logger.info(f"Отправка SMS кода на номер: {phone}")
            
            # URL для отправки SMS
            sms_url = f"{self.auth_url}/passport/api/v2/auth/login"
            
            # Данные для запроса
            data = {
                'phone': phone,
                'isNewAccount': False
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Referer': f'{self.auth_url}/passport/',
                'Origin': self.auth_url
            }
            
            response = self.session.post(sms_url, json=data, headers=headers, timeout=15)
            
            logger.info(f"Статус отправки SMS: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Ответ SMS: {response_data}")
                
                if response_data.get('success') or 'code' in response_data:
                    logger.info("SMS код отправлен успешно")
                    return True
                else:
                    logger.error(f"Ошибка отправки SMS: {response_data}")
                    return False
            else:
                logger.error(f"Ошибка HTTP при отправке SMS: {response.status_code}")
                logger.error(f"Ответ: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при отправке SMS: {e}")
            return False
    
    def verify_sms_code(self, phone: str, sms_code: str) -> Optional[str]:
        """
        Проверить SMS код и получить токен
        
        Args:
            phone: Номер телефона
            sms_code: SMS код
            
        Returns:
            JWT токен или None если ошибка
        """
        try:
            phone = self._normalize_phone(phone)
            logger.info(f"Проверка SMS кода для номера: {phone}")
            
            # URL для проверки SMS кода
            verify_url = f"{self.auth_url}/passport/api/v2/auth/login"
            
            # Данные для запроса
            data = {
                'phone': phone,
                'code': sms_code,
                'isNewAccount': False
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Referer': f'{self.auth_url}/passport/',
                'Origin': self.auth_url
            }
            
            response = self.session.post(verify_url, json=data, headers=headers, timeout=15)
            
            logger.info(f"Статус проверки SMS: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Ответ проверки: {response_data}")
                
                # Ищем токен в ответе
                token = self._extract_token(response_data)
                if token:
                    self.jwt_token = token
                    logger.info("Токен получен успешно")
                    return token
                else:
                    logger.error("Токен не найден в ответе")
                    return None
            else:
                logger.error(f"Ошибка HTTP при проверке SMS: {response.status_code}")
                logger.error(f"Ответ: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при проверке SMS: {e}")
            return None
    
    def _normalize_phone(self, phone: str) -> str:
        """Нормализация номера телефона"""
        # Убираем все кроме цифр
        digits = re.sub(r'\D', '', phone)
        
        # Если номер начинается с 8, заменяем на 7
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        
        # Если номер начинается с 7, добавляем +
        if digits.startswith('7'):
            return '+' + digits
        
        # Если номер не начинается с 7, добавляем +7
        return '+7' + digits
    
    def _extract_token(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Извлечь токен из ответа API"""
        # Различные возможные поля с токеном
        token_fields = [
            'token',
            'jwt',
            'access_token',
            'accessToken',
            'auth_token',
            'authToken',
            'bearer_token',
            'bearerToken'
        ]
        
        # Ищем токен в корневом уровне
        for field in token_fields:
            if field in response_data:
                token = response_data[field]
                if isinstance(token, str) and len(token) > 10:
                    return token
        
        # Ищем токен в вложенных объектах
        if 'data' in response_data:
            for field in token_fields:
                if field in response_data['data']:
                    token = response_data['data'][field]
                    if isinstance(token, str) and len(token) > 10:
                        return token
        
        # Ищем в cookies
        for cookie in self.session.cookies:
            if 'token' in cookie.name.lower() or 'jwt' in cookie.name.lower():
                if len(cookie.value) > 10:
                    return cookie.value
        
        return None
    
    def get_token_from_cookies(self) -> Optional[str]:
        """Получить токен из cookies"""
        try:
            # Проверяем cookies на наличие токена
            for cookie in self.session.cookies:
                cookie_name = cookie.name.lower()
                if any(keyword in cookie_name for keyword in ['token', 'jwt', 'auth', 'session']):
                    logger.info(f"Найден cookie: {cookie.name}")
                    if len(cookie.value) > 10:
                        return cookie.value
            
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении токена из cookies: {e}")
            return None
    
    def is_token_valid(self, token: str) -> bool:
        """Проверить валидность токена"""
        try:
            import base64
            
            # Декодируем JWT токен
            parts = token.split('.')
            if len(parts) != 3:
                return False
            
            # Декодируем payload
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            decoded = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded)
            
            # Проверяем срок действия
            exp = payload_data.get('exp', 0)
            current_time = int(time.time())
            
            if exp > current_time:
                logger.info(f"Токен действителен до: {time.ctime(exp)}")
                return True
            else:
                logger.warning(f"Токен истек: {time.ctime(exp)}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при проверке токена: {e}")
            return False
    
    def interactive_auth(self, phone: str) -> Optional[str]:
        """
        Интерактивная авторизация
        
        Args:
            phone: Номер телефона
            
        Returns:
            JWT токен или None
        """
        print(f"Авторизация в Wildberries Seller API")
        print(f"Номер телефона: {phone}")
        print("=" * 50)
        
        # Отправляем SMS код
        print("Отправка SMS кода...")
        if not self.send_sms_code(phone):
            print("Ошибка при отправке SMS кода")
            return None
        
        print("SMS код отправлен!")
        
        # Запрашиваем код у пользователя
        while True:
            sms_code = input("Введите SMS код: ").strip()
            
            if not sms_code:
                print("Код не может быть пустым")
                continue
            
            if not sms_code.isdigit():
                print("Код должен содержать только цифры")
                continue
            
            if len(sms_code) < 4:
                print("Код слишком короткий")
                continue
            
            # Проверяем код
            print("Проверка SMS кода...")
            token = self.verify_sms_code(phone, sms_code)
            
            if token:
                print("Авторизация успешна!")
                print(f"Токен получен: {token[:50]}...")
                return token
            else:
                print("Неверный SMS код. Попробуйте еще раз.")
                
                retry = input("Попробовать еще раз? (y/n): ").strip().lower()
                if retry not in ['y', 'yes', 'да', 'д']:
                    break
        
        return None

def main():
    """Тестирование авторизации"""
    auth = WildberriesAuth()
    
    # Номер телефона для авторизации
    phone = "+79264845850"
    
    print("Тест авторизации Wildberries Seller API")
    print("=" * 50)
    
    # Интерактивная авторизация
    token = auth.interactive_auth(phone)
    
    if token:
        print(f"\nТокен получен: {token}")
        
        # Проверяем валидность токена
        if auth.is_token_valid(token):
            print("Токен валиден!")
        else:
            print("Токен невалиден!")
    else:
        print("Авторизация не удалась")

if __name__ == "__main__":
    main()
