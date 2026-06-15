import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    print("\n1. Проверка здоровья")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"   Статус: {resp.status_code}")
        print(f"   Ответ: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"   Ошибка: {e}")

def test_home():
    print("\n2. Главная страница")
    try:
        resp = requests.get(f"{BASE_URL}/")
        print(f"   Статус: {resp.status_code}")
        print(f"   Ответ: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   Ошибка: {e}")

def test_secrets_no_auth():
    print("\n3. Попытка получить секреты без авторизации")
    try:
        resp = requests.get(f"{BASE_URL}/secrets")
        print(f"   Статус: {resp.status_code}")
        print(f"   Ответ: {resp.json()}")
    except Exception as e:
        print(f"   Ошибка: {e}")

def test_vault():
    print("\n4. Прямая проверка Vault")
    try:
        resp = requests.get("http://localhost:8200/v1/sys/health")
        print(f"   Vault статус: {resp.status_code}")
        
        headers = {"X-Vault-Token": "root"}
        resp = requests.get("http://localhost:8200/v1/secret/data/database", headers=headers)
        if resp.status_code == 200:
            data = resp.json()['data']['data']
            print(f"   Секрет database: {list(data.keys())}")
    except Exception as e:
        print(f"   Ошибка: {e}")

def test_keycloak():
    print("\n5. Прямая проверка Keycloak")
    try:
        resp = requests.get("http://localhost:8080/health")
        print(f"   Keycloak статус: {resp.status_code}")
    except Exception as e:
        print(f"   Ошибка: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ API")
    print("=" * 60)
    
    test_health()
    test_home()
    test_secrets_no_auth()
    test_vault()
    test_keycloak()
    
    print("\n" + "=" * 60)
    print("ДЛЯ ТЕСТА SSO ОТКРОЙТЕ В БРАУЗЕРЕ:")
    print(f"  {BASE_URL}/login")
    print("  Логин: testuser, Пароль: testpass")
    print("=" * 60)