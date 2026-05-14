from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
from datetime import datetime
import os

from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 會議室 API ====================

@app.route("/")
def home():
    return jsonify({"message": "API running"})


@app.route("/rooms", methods=["GET"])
def get_all_rooms():
    db = next(get_db())
    rooms = db.query(models.MeetingRoom).all()
    db.close()
    return jsonify([{
        "id": r.id,
        "name": r.name,
        "floor": r.floor,
        "capacity": r.capacity
    } for r in rooms])


@app.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    db = next(get_db())
    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == room_id).first()
    db.close()
    if not room:
        return jsonify({"error": "找不到該會議室"}), 404
    return jsonify({
        "id": room.id,
        "name": room.name,
        "floor": room.floor,
        "capacity": room.capacity
    })


@app.route("/rooms", methods=["POST"])
def create_room():
    data = request.get_json()
    if not data:
        return jsonify({"error": "請提供 JSON 資料"}), 400

    db = next(get_db())
    exist = db.query(models.MeetingRoom).filter(
        models.MeetingRoom.name == data["name"],
        models.MeetingRoom.floor == data["floor"]
    ).first()
    if exist:
        db.close()
        return jsonify({"error": "這個會議室已存在"})

    room = models.MeetingRoom(
        name=data["name"],
        floor=data["floor"],
        capacity=data["capacity"]
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    db.close()
    return jsonify({
        "id": room.id,
        "name": room.name,
        "floor": room.floor,
        "capacity": room.capacity
    })


@app.route("/rooms/<int:room_id>", methods=["PUT"])
def update_room(room_id):
    data = request.get_json()
    db = next(get_db())

    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == room_id).first()
    if not room:
        db.close()
        return jsonify({"error": "找不到該會議室"})

    exist = db.query(models.MeetingRoom).filter(
        models.MeetingRoom.name == data["name"],
        models.MeetingRoom.floor == data["floor"],
        models.MeetingRoom.id != room_id
    ).first()
    if exist:
        db.close()
        return jsonify({"error": "這個會議室已存在"})

    room.name = data["name"]
    room.floor = data["floor"]
    room.capacity = data["capacity"]
    db.commit()
    db.refresh(room)
    db.close()
    return jsonify({
        "id": room.id,
        "name": room.name,
        "floor": room.floor,
        "capacity": room.capacity
    })


@app.route("/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    db = next(get_db())
    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == room_id).first()
    if not room:
        db.close()
        return jsonify({"error": "找不到該會議室"})

    active = db.query(models.Booking).filter(
        models.Booking.room_id == room_id,
        models.Booking.end_time > datetime.now()
    ).first()
    if active:
        db.close()
        return jsonify({"error": "該會議室尚有進行中或未來的預約，無法刪除"})

    db.query(models.Booking).filter(models.Booking.room_id == room_id).delete()
    db.delete(room)
    db.commit()
    db.close()
    return jsonify({"message": "會議室已刪除"})


# ==================== 預約 API ====================

@app.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json()
    db = next(get_db())

    room = db.query(models.MeetingRoom).filter(models.MeetingRoom.id == data["room_id"]).first()
    if not room:
        db.close()
        return jsonify({"error": "找不到該會議室"})

    bookings = db.query(models.Booking).filter(
        models.Booking.room_id == data["room_id"]
    ).all()

    start_time = datetime.fromisoformat(data["start_time"])
    end_time = datetime.fromisoformat(data["end_time"])

    for b in bookings:
        if not (end_time <= b.start_time or start_time >= b.end_time):
            db.close()
            return jsonify({"error": "時間衝突，已被預約"})

    booking = models.Booking(
        room_id=data["room_id"],
        user_name=data["user_name"],
        start_time=start_time,
        end_time=end_time,
        purpose=data["purpose"]
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    db.close()
    return jsonify({
        "id": booking.id,
        "room_id": booking.room_id,
        "user_name": booking.user_name,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "purpose": booking.purpose
    })


@app.route("/bookings", methods=["GET"])
def get_all_bookings():
    db = next(get_db())
    bookings = db.query(models.Booking).all()
    db.close()
    return jsonify([{
        "id": b.id,
        "room_id": b.room_id,
        "user_name": b.user_name,
        "start_time": b.start_time.isoformat(),
        "end_time": b.end_time.isoformat(),
        "purpose": b.purpose
    } for b in bookings])


@app.route("/bookings/room/<int:room_id>", methods=["GET"])
def get_room_bookings(room_id):
    db = next(get_db())
    bookings = db.query(models.Booking).filter(models.Booking.room_id == room_id).all()
    db.close()
    return jsonify([{
        "id": b.id,
        "room_id": b.room_id,
        "user_name": b.user_name,
        "start_time": b.start_time.isoformat(),
        "end_time": b.end_time.isoformat(),
        "purpose": b.purpose
    } for b in bookings])


@app.route("/bookings/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    data = request.get_json()
    db = next(get_db())

    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        db.close()
        return jsonify({"error": "找不到該預約"})

    bookings = db.query(models.Booking).filter(
        models.Booking.room_id == data["room_id"],
        models.Booking.id != booking_id
    ).all()

    start_time = datetime.fromisoformat(data["start_time"])
    end_time = datetime.fromisoformat(data["end_time"])

    for b in bookings:
        if not (end_time <= b.start_time or start_time >= b.end_time):
            db.close()
            return jsonify({"error": "時間衝突，無法修改"})

    booking.room_id = data["room_id"]
    booking.user_name = data["user_name"]
    booking.start_time = start_time
    booking.end_time = end_time
    booking.purpose = data["purpose"]
    db.commit()
    db.refresh(booking)
    db.close()
    return jsonify({
        "id": booking.id,
        "room_id": booking.room_id,
        "user_name": booking.user_name,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "purpose": booking.purpose
    })


@app.route("/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    db = next(get_db())
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        db.close()
        return jsonify({"error": "找不到該預約"})

    db.delete(booking)
    db.commit()
    db.close()
    return jsonify({"message": "刪除成功"})
