import discord
from discord.ext import commands
import asyncio
import logging
import os
from aiohttp import web
from db_manager import DatabaseManager
from leveling import LevelingSystem
from commands import setup_commands
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurrencyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            case_insensitive=True
        )
        
        self.db = DatabaseManager()
        self.leveling = LevelingSystem(self.db)
        self.web_app = None
        
    async def setup_hook(self):
        """Setup the bot when it starts"""
        # Setup web server first for faster port binding
        await self.setup_web_server()
        
        # Setup commands after web server is running
        try:
            await setup_commands(self)
        except Exception as e:
            logger.warning(f"Command sync failed (continuing anyway): {e}")
        
        logger.info("Bot setup completed")
        
    async def setup_web_server(self):
        """Setup web server for UptimeRobot health checks"""
        app = web.Application()
        
        async def health_check(request):
            """Health check endpoint for UptimeRobot"""
            try:
                # Check if bot is ready
                if not self.is_ready():
                    return web.Response(
                        text="Starting...", 
                        status=503,
                        headers={'Content-Type': 'text/plain'}
                    )
                
                # Simple text response that UptimeRobot expects
                return web.Response(
                    text="OK", 
                    status=200,
                    headers={'Content-Type': 'text/plain'}
                )
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return web.Response(
                    text="ERROR", 
                    status=503,
                    headers={'Content-Type': 'text/plain'}
                )
            
        async def ping(request):
            """Simple ping endpoint"""
            return web.Response(text="pong")
            
        async def status(request):
            """Detailed status endpoint for debugging"""
            try:
                if not self.is_ready():
                    return web.json_response({
                        "status": "starting",
                        "message": "Bot is connecting to Discord..."
                    }, status=503)
                
                bot_status = {
                    "status": "online",
                    "bot_name": str(self.user) if self.user else "Bot starting...",
                    "guilds": len(self.guilds),
                    "latency": round(self.latency * 1000, 2),
                    "users_in_db": self.db.get_user_count()
                }
                return web.json_response(bot_status)
            except Exception as e:
                return web.json_response({"status": "error", "message": str(e)}, status=500)
            
        # Add a simple always-available endpoint for UptimeRobot
        async def simple_check(request):
            """Always returns OK for UptimeRobot"""
            return web.Response(text="OK", status=200, headers={'Content-Type': 'text/plain'})
        
        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)
        app.router.add_get('/ping', ping)
        app.router.add_get('/status', status)
        app.router.add_get('/uptime', simple_check)  # Always available endpoint
        
        self.web_app = app
        
        # Start the web server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        await site.start()
        logger.info("Web server started on port 5000 for UptimeRobot")
        
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for messages and level ups!"
        )
        await self.change_presence(activity=activity)
        
    async def on_message(self, message):
        """Handle incoming messages for XP tracking"""
        # Ignore bot messages
        if message.author.bot:
            return
            
        # Process XP gain
        await self.leveling.process_message(message)
        
        # Process commands
        await self.process_commands(message)
        
    async def on_member_update(self, before, after):
        """Handle role updates for coin rewards"""
        # Check if roles changed
        before_roles = set(before.roles)
        after_roles = set(after.roles)
        
        # New roles gained
        new_roles = after_roles - before_roles
        
        if new_roles:
            total_reward = 0
            role_names = []
            
            for role in new_roles:
                reward = Config.ROLE_REWARDS.get(role.name, Config.DEFAULT_ROLE_REWARD)
                if reward > 0:
                    self.db.add_coins(after.id, reward, "role_reward", f"Role reward for {role.name}")
                    total_reward += reward
                    role_names.append(role.name)
                    
            if total_reward > 0:
                try:
                    embed = discord.Embed(
                        title="🎉 Role Reward!",
                        description=f"You received **{total_reward}** coins for gaining the role(s): {', '.join(role_names)}!",
                        color=Config.SUCCESS_COLOR
                    )
                    await after.send(embed=embed)
                except discord.Forbidden:
                    # User has DMs disabled, try to send in a channel
                    pass
                    
                logger.info(f"Awarded {total_reward} coins to {after.name} for roles: {', '.join(role_names)}")

async def main():
    """Main function to run the bot"""
    bot = CurrencyBot()
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN', 'your_discord_token_here')
    
    if token == 'your_discord_token_here':
        logger.error("Please set your Discord token in the DISCORD_TOKEN environment variable")
        return
        
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
