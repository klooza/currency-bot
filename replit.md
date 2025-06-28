# Discord Currency & Leveling Bot

## Overview

This is a Discord bot built with discord.py that implements a currency and leveling system. The bot tracks user messages, awards XP and coins based on activity, and provides commands to check user statistics. It uses a JSON-based database for data persistence and features a role-based reward system.

## System Architecture

The bot follows a modular architecture with clear separation of concerns:

- **Main Bot Logic** (`main.py`): Core bot initialization and event handling
- **Command System** (`commands.py`): Slash command implementations
- **Leveling System** (`leveling.py`): XP calculation and level progression logic
- **Database Layer** (`database.py`): JSON-based data persistence
- **Configuration** (`config.py`): Centralized settings and constants

## Key Components

### Bot Core (`main.py`)
- **CurrencyBot Class**: Extends discord.py's commands.Bot
- **Event Handlers**: Processes message events for XP tracking
- **Initialization**: Sets up database, leveling system, and commands
- **Status Management**: Configures bot presence and activity

### Command System (`commands.py`)
- **Slash Commands**: Modern Discord interaction-based commands
- **Balance Command**: Displays user statistics including coins, level, XP, and progress
- **Profile Embeds**: Rich Discord embeds with formatted user data

### Leveling System (`leveling.py`)
- **XP Calculation**: Exponential level progression formula
- **Message Processing**: Analyzes messages for XP rewards
- **Level Detection**: Automatic level-up detection and notifications
- **Cooldown Management**: Prevents XP farming with time-based restrictions

### Database (`database.py`)
- **JSON Storage**: File-based persistence using structured JSON
- **User Management**: CRUD operations for user data
- **Data Structure**: Organized storage for users, messages, and settings
- **Error Handling**: Graceful handling of file I/O operations

### Configuration (`config.py`)
- **XP Settings**: Configurable XP rates, bonuses, and cooldowns
- **Role Rewards**: Customizable coin rewards based on Discord roles
- **Visual Settings**: Color schemes and embed configurations
- **Permission System**: Admin permission checking utilities

## Data Flow

1. **Message Reception**: Bot receives Discord messages via event handlers
2. **XP Processing**: Leveling system calculates XP based on message content and timing
3. **Database Update**: User statistics are updated and persisted to JSON
4. **Level Checking**: System determines if user leveled up
5. **Reward Distribution**: Coins and role-based bonuses are awarded
6. **Command Response**: Slash commands query database and return formatted results

## External Dependencies

- **discord.py**: Primary Discord API wrapper
- **Python Standard Library**: JSON, logging, math, datetime, os
- **Discord API**: Real-time message events and slash command interactions

## Deployment Strategy

The bot is designed for simple deployment:
- **File-based Database**: No external database server required
- **JSON Configuration**: Easy configuration management
- **Logging System**: Comprehensive logging for monitoring and debugging
- **Environment Variables**: Bot token management through environment variables
- **Modular Structure**: Easy to extend with additional features

The architecture supports both development and production environments with minimal configuration changes.

## Changelog
- June 28, 2025: Initial Discord bot with currency and leveling system
- June 28, 2025: Added UptimeRobot support with HTTP health check endpoints
- June 28, 2025: Upgraded from JSON file storage to PostgreSQL database with transaction logging

## User Preferences

Preferred communication style: Simple, everyday language.
UptimeRobot monitoring: Uses /ping endpoint at https://34afbf78-17b5-4402-a4a3-2661aff35a25-00-34ai7v2haxokz.kirk.replit.dev/ping