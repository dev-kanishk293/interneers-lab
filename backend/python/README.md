# Backend (Python) — Django + MongoDB API

This backend is a Django-based REST API that manages products and product categories using MongoDB as the primary database via MongoEngine. It follows a layered architecture to keep concerns separated and the codebase maintainable.

---

## 🧱 Tech Stack

* **Django** — Web framework
* **Django REST Framework (DRF)** — API layer
* **MongoDB** — Database
* **MongoEngine** — ODM (Object Document Mapper)
* **Docker (optional)** — MongoDB container

---

## 📁 Project Structure

```
backend/python/
│
├── django_app/          # Django project configuration
│   ├── settings.py      # App + MongoDB configuration
│   ├── urls.py          # Root URL routing
│
├── products/            # Core application (products + categories)
│   ├── models.py        # MongoEngine documents
│   ├── serializers.py   # Request/response validation
│   ├── repositories.py  # Database interaction layer
│   ├── services.py      # Business logic layer
│   ├── views.py         # API endpoints
│   ├── urls.py          # App-level routes
│   ├── apps.py          # MongoDB connection setup
│
├── manage.py            # Django entry point
├── requirements.txt     # Python dependencies
├── docker-compose.yaml  # MongoDB service
└── Dockerfile.dev       # Dev container setup
```

---

## ⚙️ Architecture Overview

The backend follows a layered design:

```
Views → Services → Repositories → Models (MongoDB)
```

* **Views**: Handle HTTP requests and responses
* **Services**: Contain business logic
* **Repositories**: Interact with MongoDB
* **Models**: Define database schema (MongoEngine)

This separation keeps logic clean and testable.

---

## 🗄️ Database

* MongoDB is used for storing application data
* Connection is configured in `settings.py`
* Established automatically in `apps.py` using MongoEngine

Example config:

```python
MONGODB_SETTINGS = {
    "db": "interneers_lab",
    "host": "localhost",
    "port": 27019,
}
```

---

## 🚀 Running the Backend

### 1. Start MongoDB (Docker)

```bash
docker-compose up -d
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
python manage.py runserver 8001
```

Base URL:

```
http://127.0.0.1:8001
```

---

## 📦 API Endpoints

### 🔹 Products

| Method | Endpoint          | Description               |
| ------ | ----------------- | ------------------------- |
| GET    | `/products/`      | List products (paginated) |
| POST   | `/products/`      | Create product            |
| GET    | `/products/{id}/` | Get product               |
| PUT    | `/products/{id}/` | Replace product           |
| PATCH  | `/products/{id}/` | Update product            |
| DELETE | `/products/{id}/` | Delete product            |

---

### 🔹 Categories

| Method | Endpoint                     | Description      |
| ------ | ---------------------------- | ---------------- |
| GET    | `/products/categories/`      | List categories  |
| POST   | `/products/categories/`      | Create category  |
| GET    | `/products/categories/{id}/` | Get category     |
| PUT    | `/products/categories/{id}/` | Replace category |
| PATCH  | `/products/categories/{id}/` | Update category  |
| DELETE | `/products/categories/{id}/` | Delete category  |

---

## 🧪 Testing

Run tests using:

```bash
python manage.py test
```

Tests cover:

* Product CRUD operations
* Validation logic
* Pagination
* API responses

---

## ⚠️ Notes

* Django’s default SQL database exists but is not used for product data
* All core data is stored in MongoDB via MongoEngine
* Pagination is enabled for product listing
* ID fields are sequential integers (not ObjectIds)

---

## 🧠 Summary

This backend provides a structured, scalable REST API with clear separation of concerns. It supports full CRUD operations for products and categories, uses MongoDB for flexible data storage, and is designed to be extended easily.

---
