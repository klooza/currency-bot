from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)  # Discord user ID
    coins = Column(Integer, default=0, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    last_xp_gain = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, level={self.level}, coins={self.coins})>"

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_user_id = Column(BigInteger, nullable=True)  # None for system transactions
    to_user_id = Column(BigInteger, nullable=False)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # 'level_up', 'role_reward', 'user_pay', 'admin_give', 'admin_take'
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Transaction(from={self.from_user_id}, to={self.to_user_id}, amount={self.amount}, type={self.transaction_type})>"