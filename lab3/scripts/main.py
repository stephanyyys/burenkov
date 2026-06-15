import hvac
import requests
from flask import Flask, jsonify, session, redirect, url_for, request
import os
import time
import json

app = Flask(__name__)
app.secret_key = 'lab3_secret_key_2024'

VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://vault:8200')
VAULT_TOKEN = os.getenv('VAULT_TOKEN', 'root')
KEYCLOAK_URL_INTERNAL = os.getenv('KEYCLOAK_URL_INTERNAL', 'http://keycloak:8080')
KEYCLOAK_URL_EXTERNAL = os.getenv('KEYCLOAK_URL_EXTERNAL', 'http://localhost:8080')

vault_client = None
keycloak_openid = None

def wait_for_vault(max_retries=15):
    print("Ожидание запуска Vault...")
    for i in range(max_retries):
        try:
            client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
            if client.is_authenticated():
                print("Vault готов")
                return client
        except Exception as e:
            print(f"Попытка {i+1}/{max_retries}: {e}")
        time.sleep(2)
    raise Exception("Vault не запустился")

def setup_vault():
    print("\n=== НАСТРОЙКА VAULT ===")
    client = wait_for_vault()
    
    try:
        client.sys.enable_secrets_engine(
            path='secret',
            backend_type='kv-v2'
        )
        print("Движок secret включён")
    except Exception as e:
        if "path is already in use" in str(e):
            print("Движок secret уже существует")
        else:
            print(f"Ошибка: {e}")
    
    secrets = {
        'database': {
            'host': 'postgres',
            'port': '5432',
            'username': 'app_user',
            'password': 'db_secret_789',
            'dbname': 'myapp'
        },
        'api_keys': {
            'openai': 'sk-1234567890',
            'stripe': 'sk_test_abc123',
            'github': 'ghp_xyz789'
        },
        'app_config': {
            'debug': 'false',
            'secret_key': 'vault_managed_key_123',
            'rate_limit': '100'
        }
    }
    
    for path, data in secrets.items():
        client.secrets.kv.v2.create_or_update_secret(
            path=f'secret/data/{path}',
            secret=data
        )
        print(f"Секрет сохранён: {path}")
    
    print("\nПрочитанные секреты:")
    for path in secrets.keys():
        response = client.secrets.kv.v2.read_secret_version(
            path=f'secret/data/{path}'
        )
        data = response['data']['data']
        print(f"  {path}: {list(data.keys())}")
    
    return client

def init_keycloak():
    global keycloak_openid
    
    print("\n=== НАСТРОЙКА KEYCLOAK ===")
    
    for i in range(15):
        try:
            resp = requests.get(f'{KEYCLOAK_URL_INTERNAL}/health')
            if resp.status_code == 200:
                print("Keycloak готов")
                break
        except:
            pass
        print(f"Ожидание Keycloak ({i+1}/15)...")
        time.sleep(3)
    
    try:
        admin_url = f'{KEYCLOAK_URL_INTERNAL}/admin/realms'
        token_url = f'{KEYCLOAK_URL_INTERNAL}/realms/master/protocol/openid-connect/token'
        
        token_data = {
            'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin',
            'grant_type': 'password'
        }
        token_resp = requests.post(token_url, data=token_data)
        
        if token_resp.status_code == 200:
            admin_token = token_resp.json()['access_token']
            headers = {'Authorization': f'Bearer {admin_token}'}
            
            realms_resp = requests.get(admin_url, headers=headers)
            realms = [r['realm'] for r in realms_resp.json() if 'realm' in r]
            
            if 'myrealm' not in realms:
                realm_config = {
                    'realm': 'myrealm',
                    'enabled': True,
                    'displayName': 'My App Realm'
                }
                requests.post(admin_url, json=realm_config, headers=headers)
                print("Realm 'myrealm' создан")
                
                client_config = {
                    'clientId': 'myapp',
                    'enabled': True,
                    'publicClient': True,
                    'directAccessGrantsEnabled': True,
                    'redirectUris': ['http://localhost:5000/callback', 'http://localhost:5000/*'],
                    'webOrigins': ['http://localhost:5000', '*']
                }
                clients_url = f'{admin_url}/myrealm/clients'
                requests.post(clients_url, json=client_config, headers=headers)
                print("Клиент 'myapp' создан")
                
                user_config = {
                    'username': 'testuser',
                    'enabled': True,
                    'email': 'test@example.com',
                    'firstName': 'Test',
                    'lastName': 'User',
                    'credentials': [{
                        'type': 'password',
                        'value': 'testpass',
                        'temporary': False
                    }]
                }
                users_url = f'{admin_url}/myrealm/users'
                response = requests.post(users_url, json=user_config, headers=headers)
                if response.status_code == 201:
                    print("Пользователь 'testuser' создан (пароль: testpass)")
                else:
                    print(f"Ошибка создания пользователя: {response.text}")
                    
                    get_users_url = f'{admin_url}/myrealm/users?username=testuser'
                    user_resp = requests.get(get_users_url, headers=headers)
                    if user_resp.status_code == 200 and user_resp.json():
                        user_id = user_resp.json()[0]['id']
                        password_url = f'{admin_url}/myrealm/users/{user_id}/reset-password'
                        password_data = {
                            'type': 'password',
                            'value': 'testpass',
                            'temporary': False
                        }
                        requests.put(password_url, json=password_data, headers=headers)
                        print("Пароль для testuser принудительно установлен")
    except Exception as e:
        print(f"Ошибка настройки Keycloak: {e}")
    
    try:
        from keycloak import KeycloakOpenID
        keycloak_openid = KeycloakOpenID(
            server_url=f'{KEYCLOAK_URL_INTERNAL}/',
            client_id='myapp',
            realm_name='myrealm',
            client_secret_key=''
        )
        print("Keycloak клиент инициализирован")
    except Exception as e:
        print(f"Ошибка инициализации Keycloak: {e}")

@app.route('/')
def home():
    if 'user' in session:
        return jsonify({
            'status': 'authenticated',
            'user': session['user'],
            'message': f'Привет, {session["user"]}!',
            'links': {
                'secrets': '/secrets',
                'logout': '/logout'
            }
        })
    return jsonify({
        'status': 'anonymous',
        'message': 'Добро пожаловать!',
        'links': {
            'login': '/login'
        }
    })

@app.route('/login')
def login():
    external_url = f'{KEYCLOAK_URL_EXTERNAL}/realms/myrealm/protocol/openid-connect/auth?client_id=myapp&response_type=code&redirect_uri=http://localhost:5000/callback&scope=openid'
    return redirect(external_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    try:
        token_response = keycloak_openid.token(
            grant_type='authorization_code',
            code=code,
            redirect_uri='http://localhost:5000/callback'
        )
        userinfo = keycloak_openid.userinfo(token_response['access_token'])
        session['user'] = userinfo.get('preferred_username', 'User')
        return redirect(url_for('home'))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/secrets')
def get_secrets():
    if 'user' not in session:
        return jsonify({'error': 'Требуется аутентификация'}), 401
    
    if vault_client is None:
        return jsonify({'error': 'Vault не настроен'}), 500
    
    try:
        secrets = {}
        paths = ['database', 'api_keys', 'app_config']
        
        for path in paths:
            response = vault_client.secrets.kv.v2.read_secret_version(
                path=f'secret/data/{path}'
            )
            secrets[path] = response['data']['data']
        
        if 'api_keys' in secrets:
            for key in secrets['api_keys']:
                if 'secret' in key or 'key' in key:
                    secrets['api_keys'][key] = '***HIDDEN***'
        
        return jsonify({
            'user': session['user'],
            'secrets': secrets,
            'message': 'Секреты получены из Vault'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    status = {
        'service': 'python-backend',
        'status': 'healthy',
        'vault': vault_client is not None,
        'keycloak': keycloak_openid is not None
    }
    return jsonify(status)

def main():
    global vault_client
    
    print("=" * 60)
    print("ЛАБОРАТОРНЫЕ РАБОТЫ №3 И №4: VAULT + KEYCLOAK + PYTHON")
    print("=" * 60)
    
    vault_client = setup_vault()
    init_keycloak()
    
    print("\n" + "=" * 60)
    print("СЕРВИС ЗАПУЩЕН")
    print("=" * 60)
    print("Доступные эндпоинты:")
    print("  GET  /           - Главная страница")
    print("  GET  /login      - Вход через Keycloak (SSO)")
    print("  GET  /secrets    - Получение секретов из Vault")
    print("  GET  /health     - Проверка здоровья")
    print("\nТестовый пользователь Keycloak:")
    print("  Логин: testuser")
    print("  Пароль: testpass")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    main()