import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymilvus import connections, Collection

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DB_URL = os.getenv("DB_URL")
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")

def init_milvus():
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    return Collection("drugs_vectors")  # 需先创建

engine = create_engine(DB_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)