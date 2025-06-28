import math
import logging
from typing import Optional
from db_manager import DatabaseManager
from config import Config
import discord

logger = logging.getLogger(__name__)

class LevelingSystem:
    def __init__(self, database: DatabaseManager):
        self.db = database
        
    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level based on XP using exponential formula"""
        if xp < 0:
            return 1
        return max(1, int(math.sqrt(xp / Config.XP_PER_LEVEL_BASE)) + 1)
        
    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for a specific level"""
        if level <= 1:
            return 0
        return int(((level - 1) ** 2) * Config.XP_PER_LEVEL_BASE)
        
    def get_xp_for_next_level(self, current_xp: int) -> int:
        """Get XP needed for next level"""
        current_level = self.calculate_level_from_xp(current_xp)
        next_level_xp = self.calculate_xp_for_level(current_level + 1)
        return next_level_xp - current_xp
        
    async def process_message(self, message):
        """Process a message for XP gain and level up"""
        user_id = message.author.id
        
        # Check cooldown
        if not self.db.can_gain_xp(user_id, Config.XP_COOLDOWN):
            return
            
        # Calculate XP gain
        xp_gain = self.calculate_xp_gain(message)
        if xp_gain <= 0:
            return
            
        # Get current stats
        old_xp = self.db.get_xp(user_id)
        old_level = self.calculate_level_from_xp(old_xp)
        
        # Add XP
        new_xp = self.db.add_xp(user_id, xp_gain)
        new_level = self.calculate_level_from_xp(new_xp)
        
        # Update level in database
        self.db.set_level(user_id, new_level)
        
        # Check for level up
        if new_level > old_level:
            await self.handle_level_up(message, user_id, old_level, new_level)
            
    def calculate_xp_gain(self, message) -> int:
        """Calculate XP gain based on message content"""
        base_xp = Config.BASE_XP_PER_MESSAGE
        
        # Bonus for longer messages
        message_length = len(message.content)
        length_bonus = min(message_length // 10, Config.MAX_LENGTH_BONUS)
        
        # Random factor
        import random
        random_bonus = random.randint(0, Config.RANDOM_XP_BONUS)
        
        total_xp = base_xp + length_bonus + random_bonus
        return max(1, total_xp)
        
    async def handle_level_up(self, message, user_id: int, old_level: int, new_level: int):
        """Handle level up rewards and notifications"""
        levels_gained = new_level - old_level
        
        # Calculate coin reward
        coin_reward = 0
        for level in range(old_level + 1, new_level + 1):
            coin_reward += self.calculate_level_reward(level)
            
        # Add coins
        if coin_reward > 0:
            new_balance = self.db.add_coins(user_id, coin_reward, "level_up", f"Level up reward for reaching level {new_level}")
            
        # Send level up message
        await self.send_level_up_message(message, new_level, coin_reward, levels_gained)
        
        logger.info(f"User {message.author.name} leveled up to {new_level}, earned {coin_reward} coins")
        
    def calculate_level_reward(self, level: int) -> int:
        """Calculate coin reward for reaching a specific level"""
        base_reward = Config.BASE_COINS_PER_LEVEL
        
        # Bonus for milestone levels
        if level % 10 == 0:  # Every 10th level
            return base_reward * 3
        elif level % 5 == 0:  # Every 5th level
            return base_reward * 2
        else:
            return base_reward
            
    async def send_level_up_message(self, message, new_level: int, coin_reward: int, levels_gained: int):
        """Send level up notification"""
        try:
            if levels_gained == 1:
                title = f"🎉 Level Up!"
                description = f"Congratulations {message.author.mention}! You reached **Level {new_level}**!"
            else:
                title = f"🚀 Multiple Level Up!"
                description = f"Amazing {message.author.mention}! You jumped **{levels_gained} levels** to **Level {new_level}**!"
                
            embed = discord.Embed(
                title=title,
                description=description,
                color=Config.LEVEL_UP_COLOR
            )
            
            if coin_reward > 0:
                embed.add_field(
                    name="💰 Reward",
                    value=f"**{coin_reward}** coins",
                    inline=True
                )
                
            # Add XP progress to next level
            current_xp = self.db.get_xp(message.author.id)
            xp_for_current = self.calculate_xp_for_level(new_level)
            xp_for_next = self.calculate_xp_for_level(new_level + 1)
            xp_progress = current_xp - xp_for_current
            xp_needed = xp_for_next - xp_for_current
            
            embed.add_field(
                name="📊 Progress",
                value=f"{xp_progress}/{xp_needed} XP to level {new_level + 1}",
                inline=True
            )
            
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_footer(text="Keep chatting to earn more XP and coins!")
            
            await message.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending level up message: {e}")
            # Fallback to simple message
            try:
                await message.channel.send(
                    f"🎉 {message.author.mention} reached Level {new_level} and earned {coin_reward} coins!"
                )
            except:
                pass
                
    def get_user_stats(self, user_id: int) -> dict:
        """Get comprehensive user statistics"""
        user_data = self.db.get_user_data(user_id)
        current_xp = user_data["xp"]
        current_level = user_data["level"]
        
        xp_for_current = self.calculate_xp_for_level(current_level)
        xp_for_next = self.calculate_xp_for_level(current_level + 1)
        xp_progress = current_xp - xp_for_current
        xp_needed = xp_for_next - current_xp
        
        return {
            "coins": user_data["coins"],
            "xp": current_xp,
            "level": current_level,
            "xp_progress": xp_progress,
            "xp_needed": xp_needed,
            "xp_for_next_level": xp_for_next - xp_for_current,
            "total_messages": user_data["total_messages"],
            "progress_percentage": (xp_progress / (xp_for_next - xp_for_current)) * 100
        }
