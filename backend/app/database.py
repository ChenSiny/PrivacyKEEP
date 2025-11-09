from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite数据库连接URL，使用文件数据库便于演示
SQLITE_DATABASE_URL = "sqlite:///./sports_privacy.db"

# 创建数据库引擎，check_same_thread=False用于SQLite多线程支持
engine = create_engine(
    SQLITE_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 创建数据库会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 declarative base class，所有数据模型将继承这个类
Base = declarative_base()

def get_db():
    """
    数据库会话依赖注入函数
    为每个请求创建独立的数据库会话，请求完成后自动关闭
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()