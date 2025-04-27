# main.py
import asyncio
from typing import List, Dict, Any

import sqlalchemy
from databases import Database
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ─── Database & Tables ─────────────────────────────────────────────────────────
DATABASE_URL = "sqlite:///./bistro92.db"
database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("table_name", sqlalchemy.String, index=True),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime,
        server_default=sqlalchemy.func.datetime("now"),
    ),
)

order_items = sqlalchemy.Table(
    "order_items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("order_id", sqlalchemy.ForeignKey("orders.id")),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("quantity", sqlalchemy.Integer),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

# Use a lock to serialize writes
write_lock = asyncio.Lock()


# ─── Pydantic Models ────────────────────────────────────────────────────────────
class OrderItemIn(BaseModel):
    name: str = Field(..., example="Burger")
    quantity: int = Field(..., gt=0, example=3)


class OrderIn(BaseModel):
    table: str = Field(..., example="Table 1")
    items: List[OrderItemIn]


class OrderOut(BaseModel):
    id: int
    table: str
    items: List[OrderItemIn]
    created_at: str


# ─── WebSocket Connection Manager ───────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        print(f"Broadcasting message to {len(self.active_connections)} clients")
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message to a client: {e}")


manager = ConnectionManager()


# ─── App & Lifespan ─────────────────────────────────────────────────────────────
app = FastAPI(title="Bistro92 High-Concurrency API")

# Add CORS middleware to allow WebSocket connections from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await database.connect()
    # Enable WAL mode and set a busy timeout to reduce lock errors
    await database.execute("PRAGMA journal_mode = WAL;")
    await database.execute("PRAGMA busy_timeout = 30000;")
    print("Database connected and configured")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    print("Database disconnected")


# ─── Debug Endpoint ─────────────────────────────────────────────────────────────
@app.get("/api/debug")
async def debug_info(request: Request):
    """Return debug information about the API"""
    return {
        "server": {
            "host": request.client.host,
            "port": request.client.port,
            "headers": dict(request.headers),
        },
        "websocket_connections": len(manager.active_connections),
        "database": {
            "url": DATABASE_URL,
            "connected": database.is_connected
        }
    }


# ─── Endpoints ─────────────────────────────────────────────────────────────────
@app.websocket("/ws/orders")
async def websocket_endpoint(websocket: WebSocket):
    print(f"WebSocket connection attempt from {websocket.client}")
    await manager.connect(websocket)
    try:
        # Send current orders when a client connects
        orders_data = await list_orders()
        await websocket.send_json({"type": "initial", "orders": [order.dict() for order in orders_data]})
        print(f"Sent initial {len(orders_data)} orders to WebSocket client")
        
        # Keep the connection alive
        while True:
            data = await websocket.receive_text()
            print(f"Received message from client: {data}")
            # Echo the message back (optional)
            await websocket.send_json({"type": "echo", "message": data})
    except WebSocketDisconnect:
        print("WebSocket disconnected normally")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.post("/api/order", response_model=OrderOut, status_code=201)
async def create_order(order: OrderIn):
    """
    Place a new order. Under the hood we:
      1) Acquire an asyncio.Lock to avoid concurrent write collisions
      2) Open a transaction, insert into `orders` and `order_items`
      3) Return the created order with timestamp
    """
    async with write_lock:
        # 1) Insert into orders
        query = orders.insert().values(table_name=order.table)
        order_id = await database.execute(query)

        # 2) Insert all items
        for itm in order.items:
            await database.execute(
                order_items.insert().values(
                    order_id=order_id, name=itm.name, quantity=itm.quantity
                )
            )

        # 3) Fetch created_at
        row = await database.fetch_one(
            orders.select().where(orders.c.id == order_id)
        )
        created_at = row["created_at"].isoformat()

    order_out = OrderOut(
        id=order_id, table=order.table, items=order.items, created_at=created_at
    )
    
    # Broadcast new order to all connected clients
    try:
        await manager.broadcast({"type": "new_order", "order": order_out.dict()})
        print(f"Broadcasted new order #{order_id} to all connected clients")
    except Exception as e:
        print(f"Error broadcasting order: {e}")
    
    return order_out


@app.get("/api/orders", response_model=List[OrderOut])
async def list_orders():
    """
    Return all orders. Useful for polling dashboards.
    """
    rows = await database.fetch_all(orders.select().order_by(orders.c.created_at.desc()))
    results = []
    for row in rows:
        items = await database.fetch_all(
            order_items.select().where(order_items.c.order_id == row["id"])
        )
        results.append(
            OrderOut(
                id=row["id"],
                table=row["table_name"],
                items=[OrderItemIn(name=i["name"], quantity=i["quantity"]) for i in items],
                created_at=row["created_at"].isoformat(),
            )
        )
    return results


# ─── Run with: uvicorn main:app --reload ────────────────────────────────────────
