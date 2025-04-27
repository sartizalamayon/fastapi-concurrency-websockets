# Bistro92 High-Concurrency API

A high-performance restaurant ordering system built with FastAPI that handles extreme concurrency without data loss or errors.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-teal.svg)

## 🔍 Overview

This implementation provides a highly reliable, concurrent restaurant order management system that enables multiple simultaneous orders without data loss, leveraging both RESTful API endpoints and WebSocket support for real-time updates.

Key features:
- **High-Concurrency Design**: Handles many simultaneous requests without conflicts
- **Real-Time Updates**: Supports both WebSockets and polling for real-time order tracking
- **Robust Transaction Handling**: Prevents data loss during concurrent write operations
- **Comprehensive Testing**: Includes test suites for all API endpoints and concurrency

## 📋 API Endpoints

### 1. Create Order
- **URL**: `/api/order`
- **Method**: `POST`
- **Status**: 201 Created
- **Request Body**:
  ```json
  {
    "table": "Table 1",
    "items": [
      { "name": "Burger", "quantity": 3 },
      { "name": "Ice Cream", "quantity": 1 }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "id": 12,
    "table": "Table 1",
    "items": [
      { "name": "Burger", "quantity": 3 },
      { "name": "Ice Cream", "quantity": 1 }
    ],
    "created_at": "2025-04-27T07:30:20"
  }
  ```
- **Description**: Creates a new order with table information and food items

### 2. List Orders
- **URL**: `/api/orders`
- **Method**: `GET`
- **Status**: 200 OK
- **Response**: Array of order objects in reverse chronological order
- **Description**: Returns all orders with complete details and line items

### 3. WebSocket for Real-time Updates
- **URL**: `/ws/orders`
- **Events**:
  - **Initial Connection**: Receives all current orders
    ```json
    {
      "type": "initial",
      "orders": [...]
    }
    ```
  - **New Order**: Receives updates when new orders are created
    ```json
    {
      "type": "new_order",
      "order": { ... }
    }
    ```
- **Description**: Provides instant updates when orders are created

## ⚙️ High Concurrency Implementation

The API achieves exceptional concurrency through several key mechanisms:

### 1. Asyncio Lock for Write Operations
```python
write_lock = asyncio.Lock()

async with write_lock:
    # Database write operations
```
- Serializes write operations to prevent race conditions
- Ensures transactional integrity during concurrent writes

### 2. SQLite WAL Mode
```python
await database.execute("PRAGMA journal_mode = WAL;")
```
- Enables Write-Ahead Logging for better concurrent access
- Allows multiple readers while writing
- Prevents database corruption during concurrent access

### 3. Busy Timeout Setting
```python
await database.execute("PRAGMA busy_timeout = 30000;")
```
- Sets a 30-second timeout for busy database connections
- Prevents immediate failures when database is locked
- Improves reliability during high traffic periods

### 4. Asynchronous Database Operations
- Uses non-blocking database calls with `databases` library
- Prevents thread blocking during I/O operations
- Efficiently utilizes server resources

### 5. WebSocket Connection Manager
- Efficiently tracks active WebSocket connections
- Manages connection lifecycle (connect/disconnect)
- Provides optimized broadcasting to all connected clients

## 🚀 Concurrency Visualization

```
Client 1 ─┐
Client 2 ─┤
Client 3 ─┤     ┌───────┐     ┌─────────┐
    ...   ├────►│FastAPI├────►│asyncio  │
Client n ─┘     └───────┘     │  Lock   │
                              └─────────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │SQLite (WAL) │
                            └─────────────┘
```

## 🛠️ Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   ```
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the server:
   ```
   # Default port (8000)
   uvicorn app:app --reload
   
   # Alternative port (8001)
   uvicorn app:app --reload --port 8001
   ```

## 🧪 Testing

### Running All Tests
```
python test_all_apis.py
```
This comprehensive test suite:
- Tests all API endpoints (POST/GET)
- Verifies concurrent request handling 
- Validates WebSocket functionality
- Provides a detailed test report

### WebSocket Testing
```
python simple_ws_client.py
```
- Tests WebSocket connection
- Verifies real-time order updates

### Manual Testing with curl

Test GET endpoint:
```
curl http://localhost:8001/api/orders
```

Test POST endpoint:
```
curl -X POST http://localhost:8001/api/order \
  -H "Content-Type: application/json" \
  -d '{
    "table": "Table 1",
    "items": [
      { "name": "Burger", "quantity": 3 },
      { "name": "Ice Cream", "quantity": 1 }
    ]
  }'
```

## 🔧 Troubleshooting

### Port Already in Use

If you see the error `[Errno 48] Address already in use`, it means the port is already being used by another process. Try:

1. Use a different port:
   ```
   uvicorn app:app --reload --port 8002
   ```

2. Find and terminate the process using the port:
   ```
   # On macOS/Linux
   lsof -i :8001
   kill <PID>
   
   # On Windows
   netstat -ano | findstr :8001
   taskkill /F /PID <PID>
   ```

## 📊 Load Testing Considerations

For production deployment, consider these additional load testing strategies:

1. **Horizontal Scaling**: Deploy multiple instances behind a load balancer
2. **Database Optimization**: Consider moving to PostgreSQL for higher concurrency
3. **Connection Pooling**: Implement connection pooling for database access
4. **Rate Limiting**: Add rate limiting for public-facing endpoints
5. **Caching**: Implement Redis caching for frequently accessed orders

## 📚 Documentation

Interactive API documentation is available at:
- http://localhost:8001/docs (Swagger UI)
- http://localhost:8001/redoc (ReDoc UI)

## 📁 Project Structure

```
.
├── app.py              # Main application file with API implementation
├── bistro92.db         # SQLite database 
├── bistro92.db-shm     # SQLite shared memory file
├── bistro92.db-wal     # SQLite write-ahead log
├── requirements.txt    # Project dependencies
├── simple_ws_client.py # WebSocket client for testing
└── test_all_apis.py    # Comprehensive test suite
```

