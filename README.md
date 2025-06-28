# Discord Currency & Leveling Bot

A Discord bot with currency system, automatic leveling, and role-based rewards.

## Features
- Currency system with coins
- Automatic XP tracking and leveling
- Role-based coin rewards
- PostgreSQL database storage
- Slash commands (/balance, /pay, /leaderboard)
- Admin commands for coin management

## Environment Variables
Required for deployment:
- `DISCORD_TOKEN` - Your Discord bot token
- `DATABASE_URL` - PostgreSQL connection string

## Commands
- `/balance` - Check your coins and level
- `/pay` - Send coins to another user
- `/leaderboard` - View top users
- `/give` (admin) - Give coins to users
- `/take` (admin) - Remove coins from users
- `/setlevel` (admin) - Set user level

## Deployment
This bot is ready for Railway deployment with the included configuration files.