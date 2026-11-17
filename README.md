# ShopEase - Order Management Microservice

## 1. Project Overview

ShopEase Order Management Service is a REST API microservice developed using Python and FastAPI.

It manages customer orders and communicates with other ShopEase microservices to retrieve customer information, product details, and manage product inventory.

The service supports order creation, order retrieval, order status management, inventory reservation, and order cancellation with stock restoration.

## 2. Technologies Used

- Python 3.11+
- FastAPI
- SQLAlchemy ORM
- MySQL 8.0
- Alembic
- Pydantic
- Docker
- Docker Compose
- JWT Authentication
- REST API
- Git and GitHub
- Swagger UI
- PowerShell

## 3. Project Features

### Order Management
- Create customer orders.
- Retrieve order details.
- Retrieve customer orders.
- Manage order items.
- Update order status.
- Cancel orders.
- Generate unique order numbers.

### Inventory Integration
- Retrieve product information from Product Catalog Service.
- Check available product stock.
- Reserve stock when an order is created.
- Restore stock when an order is cancelled.
- Prevent duplicate inventory transactions using order references.
- Aggregate duplicate product items when reserving or restoring stock.

### Security
- JWT-based authentication.
- Validate customer access.
- Use an internal service token for service-to-service inventory communication.
- Protect internal inventory endpoints.

### Database
- MySQL database.
- SQLAlchemy models.
- Alembic database migrations.
- Order and order-item relationships.

### Reliability
- Database transactions.
- Inventory reservation rollback and compensation.
- Idempotent inventory reservation and restoration.
- HTTP error handling for service communication.

## 4. Project Structure

```text
shopease-order-service/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   └── connection.py
│   │
│   ├── models/
│   │   ├── order_model.py
│   │   └── order_item_model.py
│   │
│   ├── routers/
│   │   ├── order_routes.py
│   │   └── order_item_routes.py
│   │
│   ├── schemas/
│   │   ├── order_schema.py
│   │   ├── order_item_schema.py
│   │   └── order_status_schema.py
│   │
│   ├── services/
│   │   ├── order_service.py
│   │   ├── product_client.py
│   │   └── user_client.py
│   │
│   └── main.py
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md

```

## 5. Microservice Communication

The Order Service communicates with:

| Microservice | Purpose |
|---|---|
| Authentication Service | JWT authentication |
| User Service | Retrieve customer shipping address |
| Product Catalog Service | Retrieve product details and manage stock |
| Order Service | Manage customer orders |

### Service URLs

| Service | Local URL |
|---|---|
| Order Service | http://localhost:8014 |
| Product Catalog Service | http://localhost:8013 |
| Authentication Service | http://localhost:8011 |
| User Service | http://localhost:8012 |

## 6. Environment Configuration

Create a `.env` file in the project root.

Configure the following environment variables according to your local setup:

```env
DATABASE_URL=your_mysql_connection_string
PRODUCT_SERVICE_URL=http://host.docker.internal:8013
AUTH_SERVICE_URL=http://host.docker.internal:8011
USER_SERVICE_URL=http://host.docker.internal:8012
INTERNAL_SERVICE_TOKEN=your_shared_internal_service_token
APP_PORT=8000
APP_HOST=0.0.0.0
```

Important:
- Do not upload `.env` to GitHub.
- Use the same internal service token in the Order Service and Product Catalog Service.
- Never publish database passwords, JWT secrets, or service tokens.

## 7. Installation and Setup

### Step 1: Clone the repository

```powershell
git clone YOUR_GITHUB_REPOSITORY_URL
cd shopease-order-service
```

### Step 2: Create a virtual environment

```powershell
python -m venv venv
```

### Step 3: Activate the environment

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install dependencies

```powershell
pip install -r requirements.txt
```

### Step 5: Configure environment variables

Create and configure the `.env` file using the environment variables described above.

### Step 6: Start the services

```powershell
docker compose up -d --build
```

### Step 7: Check running containers

```powershell
docker compose ps
```

## 8. Database Migrations

Apply database migrations:

```powershell
alembic upgrade head
```

Check the current migration:

```powershell
alembic current
```

Create a new migration when database models change:

```powershell
alembic revision --autogenerate -m "describe database change"
```

Apply the new migration:

```powershell
alembic upgrade head
```

## 9. API Documentation

After starting the Order Service, open:

- Swagger UI: http://localhost:8014/docs
- ReDoc: http://localhost:8014/redoc
- OpenAPI JSON: http://localhost:8014/openapi.json
- Health Check: http://localhost:8014/health

Use Swagger UI or Postman to test the APIs.

## 10. Main Order Workflow

### Create Order

1. Customer sends an order request with product IDs, quantities, and shipping address ID.
2. Order Service validates the customer using JWT authentication.
3. Product details are retrieved from Product Catalog Service.
4. Available stock is checked.
5. Customer shipping address is retrieved from User Service.
6. Order is created in the Order database.
7. Product stock is reserved through the internal inventory API.
8. The order is returned with its details and status.

### Cancel Order

1. Customer requests order cancellation.
2. Order Service validates the order.
3. The service restores the reserved product stock.
4. The order status is updated to CANCELLED.
5. Repeated cancellation requests do not restore stock multiple times.

## 11. Inventory Transaction Safety

The Product Catalog Service uses an order reference to identify inventory transactions.

This helps prevent duplicate stock operations.

- STOCK_OUT: Reserve product stock.
- STOCK_IN: Restore product stock.
- Duplicate requests with the same reference and quantity do not repeat the stock operation.
- A conflicting quantity for the same reference is rejected.

## 12. Health Check

Endpoint:

```http
GET /health
```

Example response:

```json
{
  "service": "order-service",
  "status": "healthy"
}
```

## 13. Useful Docker Commands

Start containers:

```powershell
docker compose up -d
```

Rebuild containers:

```powershell
docker compose up -d --build
```

View running containers:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs -f order_api
```

Stop containers:

```powershell
docker compose down
```

## 14. Testing Checklist

- [x] Order Service starts successfully.
- [x] Docker container runs successfully.
- [x] MySQL database connection works.
- [x] Order API health check works.
- [x] Swagger UI is accessible.
- [x] JWT authentication is integrated.
- [x] Product information retrieval is integrated.
- [x] Customer address retrieval is integrated.
- [x] Order creation is implemented.
- [x] Product stock reservation is implemented.
- [x] Order cancellation is implemented.
- [x] Product stock restoration is implemented.
- [x] Duplicate inventory operations are protected.
- [ ] Final failure and timeout recovery testing.
- [ ] Final end-to-end testing.

## 15. Git Commands

Initialize Git:

```powershell
git init
```

Check changes:

```powershell
git status
```

Stage files:

```powershell
git add .
```

Commit changes:

```powershell
git commit -m "Complete order inventory integration"
```

View commits:

```powershell
git log --oneline
```

## 16. Future Improvements

- Durable saga and recovery tracking.
- Retry and timeout handling.
- Circuit breaker implementation.
- Automated unit and integration tests.
- Centralized logging and monitoring.
- CI/CD pipeline integration.

## 17. Project Status

The Order Management Microservice includes order CRUD workflows, JWT authentication integration, customer and product service communication, inventory reservation, and cancellation with stock restoration.

The core inventory integration has been implemented and manually tested.

Final failure-recovery testing and end-to-end verification remain part of the final validation process.

---

**Project:** ShopEase - Order Management Microservice  
**Backend:** Python and FastAPI  
**Database:** MySQL  
**Containerization:** Docker and Docker Compose
