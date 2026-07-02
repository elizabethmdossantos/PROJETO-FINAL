import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# String de conexão configurada para usuário root SEM senha
DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/erp_enxuto"

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True  # Ajuda a testar e manter a conexão ativa
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()