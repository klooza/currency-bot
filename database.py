import json
import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file: str = "bot_data.json"):
        self.db_file = db_file
        self.data = {
            "users": {},
            "last_message": {},
            "settings": {}
        }
        self.load_data()
        
    def load_data(self):
        """Load data from JSON file"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    loaded_data = json.load(f)
                    self.data.update(loaded_data)
                logger.info(f"Loaded data from {self.db_file}")
            else:
                logger.info("No existing database file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
            logger.debug("Data saved to database")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            
    def get_user_data(self, user_id: int) -> Dict:
        """Get user data, create if doesn't exist"""
        user_id_str = str(user_id)
        if user_id_str not in self.data["users"]:
            self.data["users"][user_id_str] = {
                "coins": 0,
                "xp": 0,
                "level": 1,
                "total_messages": 0,
                "last_xp_gain": None
            }
            self.save_data()
        return self.data["users"][user_id_str]
        
    def get_coins(self, user_id: int) -> int:
        """Get user's coin balance"""
        user_data = self.get_user_data(user_id)
        return user_data["coins"]
        
    def add_coins(self, user_id: int, amount: int) -> int:
        """Add coins to user's balance"""
        user_data = self.get_user_data(user_id)
        user_data["coins"] += amount
        self.save_data()
        return user_data["coins"]
        
    def remove_coins(self, user_id: int, amount: int) -> bool:
        """Remove coins from user's balance, returns True if successful"""
        user_data = self.get_user_data(user_id)
        if user_data["coins"] >= amount:
            user_data["coins"] -= amount
            self.save_data()
            return True
        return False
        
    def set_coins(self, user_id: int, amount: int):
        """Set user's coin balance"""
        user_data = self.get_user_data(user_id)
        user_data["coins"] = amount
        self.save_data()
        
    def get_xp(self, user_id: int) -> int:
        """Get user's XP"""
        user_data = self.get_user_data(user_id)
        return user_data["xp"]
        
    def add_xp(self, user_id: int, amount: int) -> int:
        """Add XP to user"""
        user_data = self.get_user_data(user_id)
        user_data["xp"] += amount
        user_data["total_messages"] += 1
        user_data["last_xp_gain"] = datetime.now().isoformat()
        self.save_data()
        return user_data["xp"]
        
    def get_level(self, user_id: int) -> int:
        """Get user's level"""
        user_data = self.get_user_data(user_id)
        return user_data["level"]
        
    def set_level(self, user_id: int, level: int):
        """Set user's level"""
        user_data = self.get_user_data(user_id)
        user_data["level"] = level
        self.save_data()
        
    def can_gain_xp(self, user_id: int, cooldown_seconds: int = 60) -> bool:
        """Check if user can gain XP (anti-spam)"""
        user_data = self.get_user_data(user_id)
        last_gain = user_data.get("last_xp_gain")
        
        if not last_gain:
            return True
            
        try:
            last_gain_time = datetime.fromisoformat(last_gain)
            return datetime.now() - last_gain_time >= timedelta(seconds=cooldown_seconds)
        except:
            return True
            
    def get_leaderboard(self, limit: int = 10, sort_by: str = "coins") -> list:
        """Get leaderboard sorted by coins or level"""
        users = []
        for user_id, user_data in self.data["users"].items():
            users.append({
                "user_id": int(user_id),
                "coins": user_data["coins"],
                "level": user_data["level"],
                "xp": user_data["xp"],
                "total_messages": user_data["total_messages"]
            })
            
        if sort_by == "level":
            users.sort(key=lambda x: (x["level"], x["xp"]), reverse=True)
        else:
            users.sort(key=lambda x: x["coins"], reverse=True)
            
        return users[:limit]
        
    def get_user_count(self) -> int:
        """Get total number of users in database"""
        return len(self.data["users"])
        
    def backup_data(self) -> str:
        """Create a backup of current data"""
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(backup_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
            return backup_file
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
