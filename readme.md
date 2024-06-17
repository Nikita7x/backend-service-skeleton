# Требования к запуску
- Docker
- Docker compose

# Запуск
```bash
docker compose up
```
Не забыть применить миграции внутри контейнера 
```bash
alembic upgrade head
```

# Тестирование
```bash
pytest
```

# Дополнительно
## 1. Учесть, что сервис будет запускаться в k8s
### Dockerization
Приложение упаковано в Docker-контейнер. Dockerfile настроен для создания образа сервиса:

## 2. Гарантировать обработку транзакции ровно 1 раз
### Идемпотентность и дедупликация

Каждая транзакция имеет уникальный идентификатор (UUID):
```python3
result = await db.execute(
            select(models.Transaction).filter(models.Transaction.uid == transaction.uid)
        )
existing_transaction = result.scalar_one_or_none()
if existing_transaction:
    ...
```
## 3. Уведомление других сервисов о транзакциях
### Брокеры сообщений

Использование брокера сообщений для уведомления других сервисов:
```python
# Пример кода для публикации события в Kafka
from kafka import KafkaProducer
import json

producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

@router.post("/transaction", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionCreate, db: AsyncSession = Depends(get_async_db)):
    async with db.begin():
        new_transaction = models.Transaction(...)
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)

        # Публикация события
        producer.send('transactions', {'uid': new_transaction.uid, 'type': new_transaction.type, 'amount': new_transaction.amount})

```
### Webhooks

Реализация Webhooks для уведомления внешних сервисов:

```python
import requests

@router.post("/transaction", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionCreate, db: AsyncSession = Depends(get_async_db)):
    async with db.begin():
        new_transaction = models.Transaction(...)
        db.add(new_transaction)
        await db.commit()
        await db.refresh(new_transaction)

        # Отправка webhook
        requests.post('http://webhook-url', json={'uid': new_transaction.uid, 'type': new_transaction.type, 'amount': new_transaction.amount})
```
## 4. Инструменты для контроля качества работы сервиса
### Логирование

Централизованное логирование:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/transaction", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionCreate, db: AsyncSession = Depends(get_async_db)):
    logger.info("Processing transaction %s", transaction.uid)
    # остальной код
```
### Мониторинг и алертинг

Использование Prometheus и Grafana:

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend-service'
    static_configs:
      - targets: ['backend-service:80']
```

### CI/CD

Настройка CI/CD пайплайна:

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        pytest
```
### Линтеры
Использование линтеров, таких как **Black**

## 5. Гарантировать, что баланс пользователя не может быть отрицательным
Проверка баланса перед транзакцией
```python
if transaction.type == "WITHDRAW" and user.balance < transaction.amount:
    raise HTTPException(status_code=402, detail="Insufficient funds")
```

