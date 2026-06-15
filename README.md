Vault + Keycloak Integration Lab
Overview

Проект демонстрирует интеграцию системы управления секретами и централизованной аутентификации в backend-приложении.

В рамках работы реализованы:

SSH доступ к виртуальной машине
RSA-аутентификация
интеграция приложения с HashiCorp Vault для безопасного хранения секретов
интеграция с Keycloak для реализации SSO
Architecture

Система состоит из трех сервисов:

Service	Purpose	Port
Vault	Хранение секретов	8200
Keycloak	SSO authentication	8080
Flask Backend	API приложение	5000
Running the Project

Запуск контейнеров:

docker compose up -d --build

Проверка статуса:

docker compose ps
Verification

Проверка backend:

curl http://localhost:5000/health

Проверка Vault:

curl http://localhost:8200/v1/sys/health

Проверка Keycloak:

curl http://localhost:8080/
Authentication Flow
Пользователь переходит на /login
Backend перенаправляет в Keycloak
Пользователь проходит аутентификацию
Backend получает token
Пользователь получает доступ к защищенным ресурсам
Secrets Management

После успешной аутентификации доступен endpoint:

GET /secrets

Backend получает секреты из Vault:

database credentials
API keys
application configuration
Implemented Requirements

Реализовано:

RSA authentication
работа с секретами через Vault
SSO authentication через Keycloak
защищенный API backend
Docker Compose deployment
Result

Backend успешно интегрирован с Vault и Keycloak.

Приложение поддерживает:

безопасное хранение секретов
централизованную аутентификацию
доступ к защищенным данным только после login
