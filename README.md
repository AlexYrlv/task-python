# Service API

Этот проект предоставляет API для управления и мониторинга состояния различных сервисов. API позволяет:

- Получать и сохранять данные о сервисах (имя, состояние, описание).
- Выводить список сервисов с их актуальным состоянием.
- Выдавать историю изменения состояния сервиса по его имени.
- Выдавать информацию о времени простоя сервиса и рассчитывать SLA (Service Level Agreement) в процентах за указанный
  интервал времени.

## Установка и запуск

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/AlexYrlv/service-api.git
   cd service-api

2. Запустите контейнеры

   ```bash
   docker-compose up --build
    ```

## Документация API

3. После запуска можно проверить запросы по ссылке

   ```bash
   http://localhost:8000/docs/swagger.
   ```

## Примеры запросов

- Добавить новый сервис
   ```bash
   POST http://localhost:8000/service
  
  BODY(JSON):
    {
        "name": "Service1",
        "state": "работает",
        "description": "Описание сервиса 1"
    }

  
  RESPONSE(201):

    {
        "_id": "66854af23c98e7c594465936",
        "name": "Service3",
        "state": "работает",
        "description": "Описание сервиса 1",
        "timestamp": "2024-07-03T12:58:26.365389",
        "timestamp_end": null
    }

  ```
- Обновить состояние сервиса
    ```bash
  PUT http://localhost:8000/service/Service1
  
  REQUEST(JSON):
    {
        "state": "не работает"
    }

  RESPONSE(200)
    {
        "_id": "66854af73c98e7c594465937",
        "name": "Service1",
        "state": "не работает",
        "description": null,
        "timestamp": "2024-07-03T12:58:31.205178",
        "timestamp_end": null
    }

- Получить историю сервиса
    ```bash
  GET http://localhost:8000/service/Service1

  RESPONSE:
    {
        "history": [
            {
                "_id": "66854af23c98e7c594465936",
                "name": "Service1",
                "state": "работает",
                "description": "Описание сервиса 1",
                "timestamp": "2024-07-03T12:58:26.365389",
                "timestamp_end": "2024-07-03T12:58:31.201000"
            },
            {
                "_id": "66854af73c98e7c594465937",
                "name": "Service1",
                "state": "не работает",
                "description": null,
                "timestamp": "2024-07-03T12:58:31.205178",
                "timestamp_end": null
            }
        ]
    }
- Получить все сервисы
   ```bash
  GET http://localhost:8000/services
  
  RESPONSE:
    {
        "services": [
            {
                "_id": "668503f8225d7a5645a5dd1a",
                "name": "Service1",
                "state": "работает",
                "description": "Описание сервиса 1",
                "timestamp": "2024-07-03T07:55:36.801593",
                "timestamp_end": "2024-07-03T07:57:00.052000"
            },
            {
                "_id": "6685044c225d7a5645a5dd1b",
                "name": "Service1",
                "state": "не работает",
                "description": null,
                "timestamp": "2024-07-03T07:57:00.056868",
                "timestamp_end": "2024-07-03T07:58:47.221000"
            },
            {
                "_id": "668504b7225d7a5645a5dd1c",
                "name": "Service1",
                "state": "работает",
                "description": null,
                "timestamp": "2024-07-03T07:58:47.225278",
                "timestamp_end": "2024-07-03T12:56:53.155000"
            },
        ]
    }
- Получить SLA для сервиса

    ```bash
  ОБРАТИТЕ ВНИМАНИЕ!!! 
  ----  ----  ----  ----  ----  ----  ----  ----  ----  
  SLA МОЖНО РАССЧИТАТЬ ТОЛЬКО КОГДА СЕРВИС В ДАННЫЙ 
  МОМЕНТ РАБОТАЕТ,ЕСЛИ В ПОСЛЕДНЕЙ ЗАПИСИ "state" "не работает",
  ТО ОБНОВИТЕ ЕГО 
  ----  ----  ----  ----  ----  ----  ----  ----  ----
  
  GET http://localhost:8000/sla/Service1?interval=24h

  RESPONSE:
    {
        "sla": 100.0,
        "downtime": 0.0
    }