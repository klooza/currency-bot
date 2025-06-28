import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import Config

logger = logging.getLogger(__name__)

async def setup_commands(bot):
    """Setup all slash commands"""
    
    @bot.tree.command(name="balance", description="Check your coin balance and level")
    async def balance(interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        # Get user stats
        stats = bot.leveling.get_user_stats(target_user.id)
        
        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Profile",
            color=Config.INFO_COLOR
        )
        
        embed.add_field(
            name="🪙 Coins",
            value=f"**{stats['coins']:,}**",
            inline=True
        )
        
        embed.add_field(
            name="📊 Level",
            value=f"**{stats['level']}**",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Total XP",
            value=f"**{stats['xp']:,}**",
            inline=True
        )
        
        embed.add_field(
            name="📈 Progress to Next Level",
            value=f"**{stats['xp_progress']}/{stats['xp_for_next_level']}** XP ({stats['progress_percentage']:.1f}%)",
            inline=False
        )
        
        embed.add_field(
            name="💬 Messages Sent",
            value=f"**{stats['total_messages']:,}**",
            inline=True
        )
        
        embed.add_field(
            name="🎯 XP Needed",
            value=f"**{stats['xp_needed']}** XP",
            inline=True
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text="Keep chatting to earn more XP and level up!")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="leaderboard", description="View the server leaderboard")
    async def leaderboard(interaction: discord.Interaction, sort_by: str = "coins"):
        if sort_by not in ["coins", "level"]:
            sort_by = "coins"
            
        leaders = bot.db.get_leaderboard(limit=Config.MAX_LEADERBOARD_ENTRIES, sort_by=sort_by)
        
        if not leaders:
            embed = discord.Embed(
                title="📊 Leaderboard",
                description="No users found in the database yet!",
                color=Config.INFO_COLOR
            )
            await interaction.response.send_message(embed=embed)
            return
            
        embed = discord.Embed(
            title=f"📊 Leaderboard - Top {sort_by.title()}",
            color=Config.INFO_COLOR
        )
        
        description = ""
        for i, user_data in enumerate(leaders, 1):
            try:
                user = bot.get_user(user_data['user_id']) or await bot.fetch_user(user_data['user_id'])
                username = user.display_name if user else f"Unknown User"
            except:
                username = "Unknown User"
                
            if sort_by == "coins":
                value = f"{user_data['coins']:,} coins"
            else:
                value = f"Level {user_data['level']} ({user_data['xp']:,} XP)"
                
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"
            description += f"{medal} **{username}** - {value}\n"
            
        embed.description = description
        embed.set_footer(text=f"Total users: {bot.db.get_user_count()}")
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="pay", description="Send coins to another user")
    async def pay(interaction: discord.Interaction, user: discord.Member, amount: int):
        sender_id = interaction.user.id
        receiver_id = user.id
        
        # Validation
        if sender_id == receiver_id:
            embed = discord.Embed(
                title="❌ Error",
                description="You cannot send coins to yourself!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if user.bot:
            embed = discord.Embed(
                title="❌ Error",
                description="You cannot send coins to bots!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if amount < Config.MIN_TRANSACTION:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Minimum transaction amount is {Config.MIN_TRANSACTION} coins!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Check sender balance
        sender_balance = bot.db.get_coins(sender_id)
        if sender_balance < amount:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"You only have **{sender_balance:,}** coins, but tried to send **{amount:,}** coins!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Process transaction
        success = bot.db.transfer_coins(sender_id, receiver_id, amount, f"Payment from user {sender_id} to user {receiver_id}")
        if not success:
            embed = discord.Embed(
                title="❌ Transaction Failed",
                description="Failed to process the payment. Please try again.",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💸 Payment Successful",
            description=f"**{interaction.user.display_name}** sent **{amount:,}** coins to **{user.display_name}**!",
            color=Config.SUCCESS_COLOR
        )
        
        new_sender_balance = bot.db.get_coins(sender_id)
        new_receiver_balance = bot.db.get_coins(receiver_id)
        
        embed.add_field(
            name="💰 Your New Balance",
            value=f"**{new_sender_balance:,}** coins",
            inline=True
        )
        
        embed.add_field(
            name="💰 Recipient's New Balance",
            value=f"**{new_receiver_balance:,}** coins",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Try to notify recipient
        try:
            dm_embed = discord.Embed(
                title="💰 You Received Coins!",
                description=f"**{interaction.user.display_name}** sent you **{amount:,}** coins!",
                color=Config.SUCCESS_COLOR
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
    
    @bot.tree.command(name="give", description="[ADMIN] Give coins to a user")
    async def give_coins(interaction: discord.Interaction, user: discord.Member, amount: int):
        if not Config.has_admin_permissions(interaction.user):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You need administrator permissions to use this command!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if amount <= 0:
            embed = discord.Embed(
                title="❌ Error",
                description="Amount must be positive!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        old_balance = bot.db.get_coins(user.id)
        new_balance = bot.db.add_coins(user.id, amount, "admin_give", f"Admin {interaction.user.name} gave {amount} coins")
        
        embed = discord.Embed(
            title="✅ Coins Added",
            description=f"Added **{amount:,}** coins to **{user.display_name}**",
            color=Config.SUCCESS_COLOR
        )
        
        embed.add_field(
            name="Previous Balance",
            value=f"{old_balance:,} coins",
            inline=True
        )
        
        embed.add_field(
            name="New Balance",
            value=f"{new_balance:,} coins",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
        
        logger.info(f"Admin {interaction.user.name} gave {amount} coins to {user.name}")
    
    @bot.tree.command(name="take", description="[ADMIN] Remove coins from a user")
    async def take_coins(interaction: discord.Interaction, user: discord.Member, amount: int):
        if not Config.has_admin_permissions(interaction.user):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You need administrator permissions to use this command!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if amount <= 0:
            embed = discord.Embed(
                title="❌ Error",
                description="Amount must be positive!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        old_balance = bot.db.get_coins(user.id)
        
        if bot.db.remove_coins(user.id, amount, "admin_take", f"Admin {interaction.user.name} removed {amount} coins"):
            new_balance = bot.db.get_coins(user.id)
            
            embed = discord.Embed(
                title="✅ Coins Removed",
                description=f"Removed **{amount:,}** coins from **{user.display_name}**",
                color=Config.SUCCESS_COLOR
            )
            
            embed.add_field(
                name="Previous Balance",
                value=f"{old_balance:,} coins",
                inline=True
            )
            
            embed.add_field(
                name="New Balance",
                value=f"{new_balance:,} coins",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)
            
            logger.info(f"Admin {interaction.user.name} took {amount} coins from {user.name}")
        else:
            embed = discord.Embed(
                title="❌ Insufficient Funds",
                description=f"**{user.display_name}** only has **{old_balance:,}** coins, cannot remove **{amount:,}** coins!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.command(name="setlevel", description="[ADMIN] Set a user's level")
    async def set_level(interaction: discord.Interaction, user: discord.Member, level: int):
        if not Config.has_admin_permissions(interaction.user):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You need administrator permissions to use this command!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if level < 1:
            embed = discord.Embed(
                title="❌ Error",
                description="Level must be at least 1!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        old_level = bot.db.get_level(user.id)
        required_xp = bot.leveling.calculate_xp_for_level(level)
        
        # Set level and XP
        bot.db.set_level(user.id, level)
        bot.db.get_user_data(user.id)["xp"] = required_xp
        bot.db.save_data()
        
        embed = discord.Embed(
            title="✅ Level Set",
            description=f"Set **{user.display_name}**'s level to **{level}**",
            color=Config.SUCCESS_COLOR
        )
        
        embed.add_field(
            name="Previous Level",
            value=f"Level {old_level}",
            inline=True
        )
        
        embed.add_field(
            name="New Level",
            value=f"Level {level}",
            inline=True
        )
        
        embed.add_field(
            name="XP Set",
            value=f"{required_xp:,} XP",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
        
        logger.info(f"Admin {interaction.user.name} set {user.name}'s level to {level}")
    
    @bot.tree.command(name="backup", description="[ADMIN] Create a backup of bot data")
    async def backup_data(interaction: discord.Interaction):
        if not Config.has_admin_permissions(interaction.user):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You need administrator permissions to use this command!",
                color=Config.ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        backup_file = bot.db.backup_data()
        
        if backup_file:
            embed = discord.Embed(
                title="✅ Backup Created",
                description=f"Database backup created: `{backup_file}`",
                color=Config.SUCCESS_COLOR
            )
            embed.add_field(
                name="📊 Stats",
                value=f"Users: {bot.db.get_user_count()}",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="❌ Backup Failed",
                description="Failed to create database backup!",
                color=Config.ERROR_COLOR
            )
            
        await interaction.response.send_message(embed=embed)
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
