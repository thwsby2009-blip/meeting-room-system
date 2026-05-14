from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 支援環境變數 DATABASE_PATH（PythonAnywhere 需要絕對路徑）
db_path = os.environ.get('DATABASE_PATH', './meeting_room.db')
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()