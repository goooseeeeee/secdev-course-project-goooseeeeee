# DFD — Data Flow Diagram (Wishlist Service)

## Диаграмма (Mermaid)
```mermaid
flowchart LR
  U[User / Browser or Mobile App]

  subgraph Edge [Trust Boundary: Edge]
    BFF[FastAPI Backend / API Endpoint]
  end

  subgraph Core [Trust Boundary: Core]
    WISH[Wishlist Service (CRUD logic)]
  end

  subgraph Data [Trust Boundary: Data]
    DB[(PostgreSQL / SQLite)]
    EXPORT[(Export Storage: CSV/JSON)]
  end

  U -->|F1: HTTPS (AuthN, CRUD /wishes)| BFF
  BFF -->|F2: Internal API call| WISH
  WISH -->|F3: SQL over TCP| DB
  WISH -->|F4: Export File Write| EXPORT
  U -->|F5: HTTPS GET /export| BFF
  BFF -->|F6: Read file| EXPORT
```

## Список потоков

| ID | Откуда → Куда                    | Канал / Протокол         | Данные / PII                                      | Комментарий                                      |
|----|-----------------------------------|----------------------------|---------------------------------------------------|--------------------------------------------------|
| F1 | User → FastAPI Backend           | HTTPS                     | credentials, session token, wish data            | Аутентификация и CRUD операций по желаниям       |
| F2 | FastAPI Backend → Wishlist Logic | internal call (Python)    | session context, wish data                       | Передача данных в бизнес-логику                  |
| F3 | Wishlist Logic → DB              | SQL over TCP              | user_id, title, link, price_estimate, notes       | Хранение списка желаний                          |
| F4 | Wishlist Logic → Export Storage  | Local FS / S3 / GCS       | wish list (CSV/JSON)                             | Формирование и запись файла экспорта             |
| F5 | User → FastAPI Backend           | HTTPS                     | session token                                    | Запрос на скачивание файла экспорта             |
| F6 | FastAPI Backend → Export Storage | Local FS / S3 / GCS       | export file                                     | Чтение и выдача файла экспорта пользователю     |
