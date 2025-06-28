import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, Transaction
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(
            self.database_url, 
            pool_pre_ping=True,
            pool_recycle=300,
            pool_reset_on_return='commit',
            echo=False
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
        # Create tables if they don't exist
        self.create_tables()
        logger.info("Database connection established")
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def get_session(self):
        """Get a database session"""
        return self.Session()
    
    def get_user_data(self, user_id: int) -> Dict:
        """Get user data, create if doesn't exist"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            
            if not user:
                user = User(
                    user_id=user_id,
                    coins=0,
                    xp=0,
                    level=1,
                    total_messages=0
                )
                session.add(user)
                session.commit()
                logger.debug(f"Created new user: {user_id}")
            
            return {
                "coins": user.coins,
                "xp": user.xp,
                "level": user.level,
                "total_messages": user.total_messages,
                "last_xp_gain": user.last_xp_gain.isoformat() if user.last_xp_gain else None
            }
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error getting user data: {e}")
            raise
        finally:
            session.close()
    
    def get_coins(self, user_id: int) -> int:
        """Get user's coin balance"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                # Create user if doesn't exist
                self.get_user_data(user_id)
                return 0
            return user.coins
        except SQLAlchemyError as e:
            logger.error(f"Error getting coins: {e}")
            return 0
        finally:
            session.close()
    
    def add_coins(self, user_id: int, amount: int, transaction_type: str = "system", description: str = None) -> int:
        """Add coins to user's balance"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.get_user_data(user_id)
                user = session.query(User).filter_by(user_id=user_id).first()
            
            user.coins += amount
            user.updated_at = datetime.now()
            
            # Record transaction
            transaction = Transaction(
                from_user_id=None,
                to_user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description
            )
            session.add(transaction)
            session.commit()
            
            return user.coins
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding coins: {e}")
            raise
        finally:
            session.close()
    
    def remove_coins(self, user_id: int, amount: int, transaction_type: str = "system", description: str = None) -> bool:
        """Remove coins from user's balance, returns True if successful"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user or user.coins < amount:
                return False
            
            user.coins -= amount
            user.updated_at = datetime.now()
            
            # Record transaction
            transaction = Transaction(
                from_user_id=user_id,
                to_user_id=None,
                amount=-amount,
                transaction_type=transaction_type,
                description=description
            )
            session.add(transaction)
            session.commit()
            
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error removing coins: {e}")
            return False
        finally:
            session.close()
    
    def set_coins(self, user_id: int, amount: int):
        """Set user's coin balance"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.get_user_data(user_id)
                user = session.query(User).filter_by(user_id=user_id).first()
            
            old_amount = user.coins
            user.coins = amount
            user.updated_at = datetime.now()
            
            # Record transaction
            diff = amount - old_amount
            transaction = Transaction(
                from_user_id=None if diff > 0 else user_id,
                to_user_id=user_id if diff > 0 else None,
                amount=diff,
                transaction_type="admin_set",
                description=f"Balance set from {old_amount} to {amount}"
            )
            session.add(transaction)
            session.commit()
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error setting coins: {e}")
            raise
        finally:
            session.close()
    
    def get_xp(self, user_id: int) -> int:
        """Get user's XP"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.get_user_data(user_id)
                return 0
            return user.xp
        except SQLAlchemyError as e:
            logger.error(f"Error getting XP: {e}")
            return 0
        finally:
            session.close()
    
    def add_xp(self, user_id: int, amount: int) -> int:
        """Add XP to user"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.get_user_data(user_id)
                user = session.query(User).filter_by(user_id=user_id).first()
            
            user.xp += amount
            user.total_messages += 1
            user.last_xp_gain = datetime.now()
            user.updated_at = datetime.now()
            session.commit()
            
            return user.xp
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error adding XP: {e}")
            raise
        finally:
            session.close()
    
    def get_level(self, user_id: int) -> int:
        """Get user's level"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.get_user_data(user_id)
                return 1
            return user.level
        except SQLAlchemyError as e:
            logger.error(f"Error getting level: {e}")
            return 1
        finally:
            session.close()
    
    def set_level(self, user_id: int, level: int):
        """Set user's level"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                self.get_user_data(user_id)
                user = session.query(User).filter_by(user_id=user_id).first()
            
            user.level = level
            user.updated_at = datetime.now()
            session.commit()
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error setting level: {e}")
            raise
        finally:
            session.close()
    
    def can_gain_xp(self, user_id: int, cooldown_seconds: int = 60) -> bool:
        """Check if user can gain XP (anti-spam)"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user or not user.last_xp_gain:
                return True
            
            time_diff = datetime.now() - user.last_xp_gain
            return time_diff.total_seconds() >= cooldown_seconds
        except SQLAlchemyError as e:
            logger.error(f"Error checking XP cooldown: {e}")
            return True
        finally:
            session.close()
    
    def get_leaderboard(self, limit: int = 10, sort_by: str = "coins") -> List[Dict]:
        """Get leaderboard sorted by coins or level"""
        for attempt in range(3):  # Retry up to 3 times
            session = self.get_session()
            try:
                if sort_by == "level":
                    users = session.query(User).order_by(User.level.desc(), User.xp.desc()).limit(limit).all()
                else:
                    users = session.query(User).order_by(User.coins.desc()).limit(limit).all()
                
                return [
                    {
                        "user_id": user.user_id,
                        "coins": user.coins,
                        "level": user.level,
                        "xp": user.xp,
                        "total_messages": user.total_messages
                    }
                    for user in users
                ]
            except SQLAlchemyError as e:
                logger.error(f"Error getting leaderboard (attempt {attempt + 1}): {e}")
                if attempt == 2:  # Last attempt
                    return []
                # Recreate engine and session for retry
                self.engine.dispose()
                self.engine = create_engine(
                    os.environ.get('DATABASE_URL'),
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False
                )
                self.Session = sessionmaker(bind=self.engine)
            finally:
                session.close()
    
    def get_user_count(self) -> int:
        """Get total number of users in database"""
        session = self.get_session()
        try:
            return session.query(User).count()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user count: {e}")
            return 0
        finally:
            session.close()
    
    def transfer_coins(self, from_user_id: int, to_user_id: int, amount: int, description: str = None) -> bool:
        """Transfer coins between users"""
        session = self.get_session()
        try:
            from_user = session.query(User).filter_by(user_id=from_user_id).first()
            to_user = session.query(User).filter_by(user_id=to_user_id).first()
            
            if not from_user or from_user.coins < amount:
                return False
            
            if not to_user:
                self.get_user_data(to_user_id)
                to_user = session.query(User).filter_by(user_id=to_user_id).first()
            
            from_user.coins -= amount
            to_user.coins += amount
            from_user.updated_at = datetime.now()
            to_user.updated_at = datetime.now()
            
            # Record transaction
            transaction = Transaction(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                amount=amount,
                transaction_type="user_pay",
                description=description
            )
            session.add(transaction)
            session.commit()
            
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error transferring coins: {e}")
            return False
        finally:
            session.close()
    
    def backup_data(self) -> str:
        """Create a backup of current data"""
        session = self.get_session()
        try:
            users = session.query(User).all()
            transactions = session.query(Transaction).all()
            
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "users": [
                    {
                        "user_id": user.user_id,
                        "coins": user.coins,
                        "xp": user.xp,
                        "level": user.level,
                        "total_messages": user.total_messages,
                        "last_xp_gain": user.last_xp_gain.isoformat() if user.last_xp_gain else None,
                        "created_at": user.created_at.isoformat(),
                        "updated_at": user.updated_at.isoformat()
                    }
                    for user in users
                ],
                "transactions": [
                    {
                        "from_user_id": t.from_user_id,
                        "to_user_id": t.to_user_id,
                        "amount": t.amount,
                        "transaction_type": t.transaction_type,
                        "description": t.description,
                        "created_at": t.created_at.isoformat()
                    }
                    for t in transactions
                ]
            }
            
            import json
            backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return backup_file
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
        finally:
            session.close()
    
    def close(self):
        """Close database connections"""
        try:
            self.Session.remove()
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")