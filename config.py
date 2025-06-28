import discord

class Config:
    # Bot Settings
    COMMAND_PREFIX = "!"
    
    # XP System Settings
    BASE_XP_PER_MESSAGE = 15
    MAX_LENGTH_BONUS = 10
    RANDOM_XP_BONUS = 5
    XP_COOLDOWN = 60  # seconds between XP gains
    XP_PER_LEVEL_BASE = 100  # Base XP calculation for levels
    
    # Currency Settings
    BASE_COINS_PER_LEVEL = 50
    DEFAULT_ROLE_REWARD = 25
    
    # Role-specific coin rewards (customize these for your server)
    ROLE_REWARDS = {
        "VIP": 100,
        "Supporter": 75,
        "Active Member": 50,
        "Member": 25,
        "Verified": 10,
        # Add more roles and their rewards here
    }
    
    # Colors for embeds
    SUCCESS_COLOR = discord.Color.green()
    ERROR_COLOR = discord.Color.red()
    INFO_COLOR = discord.Color.blue()
    LEVEL_UP_COLOR = discord.Color.gold()
    WARNING_COLOR = discord.Color.orange()
    
    # Embed Settings
    MAX_LEADERBOARD_ENTRIES = 10
    
    # Admin Settings
    ADMIN_PERMISSIONS = [
        "administrator",
        "manage_guild"
    ]
    
    # Economy Settings
    MAX_COINS_PER_USER = 1000000  # Maximum coins a user can have
    MIN_TRANSACTION = 1  # Minimum coins for transactions
    
    @staticmethod
    def has_admin_permissions(member):
        """Check if a member has admin permissions"""
        return (
            member.guild_permissions.administrator or
            member.guild_permissions.manage_guild or
            member.id == member.guild.owner_id
        )
