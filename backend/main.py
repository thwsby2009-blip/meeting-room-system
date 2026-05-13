from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ==================== CORS（允許前端不同 port 存取）====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Pydantic 請求模型 ====================

class RoomCreate(BaseModel):
    name: str
    floor: str
    capacity: int


class RoomUpdate(BaseModel):
    name: str
    floor: str
    capacity: int


class BookingCreate(BaseModel):
    room_id: int
    user_name: str
    start_time: datetime
    end_time: datetime
    purpose: str


class BookingUpdate(BaseModel):
    room_id: int
    user_name: str
    start_time: datetime
    end_time: datetime
    purpose: str


# ==================== 會議室 API ====================

@app.get("/")
def home():
    return {"message": "API running"}


@app.get("/rooms")
def get_all_rooms(db: Session = Depends(get_db)):
    return db.query(models.MeetingRoom).all()


@app.get("/rooms/{room_id}")
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="找不到該會議室")
    return room


@app.post("/rooms")
def create_room(body: RoomCreate, db: Session = Depends(get_db)):
    exist_room = db.query(models.MeetingRoom).filter(
        models.MeetingRoom.name == body.name,
        models.MeetingRoom.floor == body.floor
    ).first()

    if exist_room:
        return {"error": "這個會議室已存在"}

    room = models.MeetingRoom(
        name=body.name,
        floor=body.floor,
        capacity=body.capacity
    )

    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@app.put("/rooms/{room_id}")
def update_room(room_id: int, body: RoomUpdate, db: Session = Depends(get_db)):
    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == room_id).first()
    if not room:
        return {"error": "找不到該會議室"}

    # 檢查同名同樓層衝突（排除自己）
    exist = db.query(models.MeetingRoom).filter(
        models.MeetingRoom.name == body.name,
        models.MeetingRoom.floor == body.floor,
        models.MeetingRoom.id != room_id
    ).first()
    if exist:
        return {"error": "這個會議室已存在"}

    room.name = body.name
    room.floor = body.floor
    room.capacity = body.capacity
    db.commit()
    db.refresh(room)
    return room


@app.delete("/rooms/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == room_id).first()
    if not room:
        return {"error": "找不到該會議室"}

    # 檢查是否有未結束的預約
    active_bookings = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.end_time > datetime.now()
    ).first()
    if active_bookings:
        return {"error": "該會議室尚有進行中或未來的預約，無法刪除"}

    # 一併刪除該會議室的所有預約
    db.query(models.Booking).filter(models.Booking.room_id == room_id).delete()
    db.delete(room)
    db.commit()
    return {"message": "會議室已刪除"}


# ==================== 預約 API ====================

@app.post("/bookings")
def create_booking(body: BookingCreate, db: Session = Depends(get_db)):
    # 檢查會議室是否存在
    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == body.room_id).first()
    if not room:
        return {"error": "找不到該會議室"}

    # 檢查時間是否衝突
    bookings = db.query(models.Booking).filter(
        models.Booking.room_id == body.room_id
    ).all()

    for b in bookings:
        if not (body.end_time <= b.start_time or body.start_time >= b.end_time):
            return {"error": "時間衝突，已被預約"}

    booking = models.Booking(
        room_id=body.room_id,
        user_name=body.user_name,
        start_time=body.start_time,
        end_time=body.end_time,
        purpose=body.purpose
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return booking


@app.get("/bookings")
def get_all_bookings(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()


@app.get("/bookings/room/{room_id}")
def get_room_bookings(room_id: int, db: Session = Depends(get_db)):
    return db.query(models.Booking).filter(
        models.Booking.room_id == room_id
    ).all()


@app.put("/bookings/{booking_id}")
def update_booking(booking_id: int, body: BookingUpdate, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id
    ).first()

    if not booking:
        return {"error": "找不到該預約"}

    # 檢查時間衝突（排除自己）
    bookings = db.query(models.Booking).filter(
        models.Booking.room_id == body.room_id,
        models.Booking.id != booking_id
    ).all()

    for b in bookings:
        if not (body.end_time <= b.start_time or body.start_time >= b.end_time):
            return {"error": "時間衝突，無法修改"}

    # 更新資料
    booking.room_id = body.room_id
    booking.user_name = body.user_name
    booking.start_time = body.start_time
    booking.end_time = body.end_time
    booking.purpose = body.purpose

    db.commit()
    db.refresh(booking)

    return booking


@app.delete("/bookings/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.id == booking_id
    ).first()

    if not booking:
        return {"error": "找不到該預約"}

    db.delete(booking)
    db.commit()

    return {"message": "刪除成功"}
