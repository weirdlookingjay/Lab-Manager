from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import json

from . import models, database
from .database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active websocket connections
active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - we'll enhance this later
            await websocket.send_text(f"Message received: {data}")
    except:
        active_connections.remove(websocket)

@app.post("/notifications/")
async def create_notification(
    title: str,
    message: str,
    notification_type: str,
    priority: str,
    user_id: int,
    db: Session = Depends(get_db)
):
    notification = models.Notification(
        title=title,
        message=message,
        type=notification_type,
        priority=priority,
        user_id=user_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Notify all connected clients
    for connection in active_connections:
        await connection.send_json({
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "priority": notification.priority
        })
    
    return notification

@app.get("/notifications/{user_id}")
def get_user_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(models.Notification)\
        .filter(models.Notification.user_id == user_id)\
        .order_by(models.Notification.created_at.desc())\
        .all()
    return notifications
