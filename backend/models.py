from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base


class MeetingRoom(Base):
    __tablename__ = "meeting_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    floor = Column(String)
    capacity = Column(Integer)


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("meeting_rooms.id"))
    user_name = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    purpose = Column(String)