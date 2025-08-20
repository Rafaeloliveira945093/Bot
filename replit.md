# Overview
This project is a Python-based Telegram bot designed to streamline communication and content distribution. It provides a menu-driven interface for users to send messages (text, media, buttons) to group chats, manage automatic message forwarding to registered groups, and handle group registrations. The bot aims to simplify content management and automate message distribution, offering a robust solution for diverse communication needs.

# User Preferences
Preferred communication style: Simple, everyday language.

# System Architecture
## Core Bot Framework
- **Framework**: Built on `python-telegram-bot` using `Application` and `ConversationHandler` patterns.
- **State Management**: Utilizes conversation states for tracking multi-exchange user interactions.
- **Modular Design**: Structured into distinct modules (handlers, utils, config) for maintainability.

## Conversation Flow Architecture
- **Main Menu System**: Six primary options via inline keyboard buttons.
- **State-Based Navigation**: Implements 14 conversation states for complex multi-step interactions.
- **Conversation Handlers**: Three main flows: message sending, group registration, and message forwarding.
- **Automatic Message Processing**: Messages sent to the bot are automatically forwarded to registered destination groups.
- **Fallback Mechanisms**: Includes cancel commands and error handling.

## Message Processing System
- **Multi-Format Support**: Handles text, photos, videos, documents, audio, voice, stickers, animations, and inline buttons.
- **Content Validation**: Validates button formats, URLs, and message content.
- **Media Handling**: Processes all media types with file ID tracking, preserving captions and entities.
- **Button Generation**: Creates inline keyboards from user-provided text.
- **Automatic Forwarding**: Copies messages preserving all original content (formatting, media, captions, buttons).
- **Group Management**: Allows registration, testing, and management of multiple destination groups.
- **Bulk Message Workflow**: Supports collecting multiple messages for bulk editing and sending, preserving Telegram formatting and entities.

## Error Handling and Logging
- **Logging**: Uses Python's logging module for debugging and monitoring.
- **Exception Management**: Try-catch blocks with user-friendly error messages.
- **Input Validation**: Validates user inputs to prevent errors.

## Configuration Management
- **Environment Variables**: Bot token and sensitive configuration stored as environment variables.
- **Constants**: Centralized configuration for conversation states and message limits.
- **Persistent Storage**: JSON file storage for destination group configuration and user data.
- **Type Safety**: Uses type hints throughout the codebase.

## UI/UX Decisions
- **Intuitive Menu Structure**: Clear hierarchy from main menu to specific actions.
- **Visual Feedback**: Progress indicators and confirmation messages.
- **Flexible Group Removal**: Easy group deletion with confirmation prompts.
- **Success Tracking**: Detailed feedback on message delivery.
- **Return to Menu**: "Voltar ao Menu Principal" button at the end of functions.

## System Design Choices
- **Private Chat Only**: Bot ignores messages in group chats, operating only in private chats.
- **Secure Group Access**: Validates bot access to groups during registration.
- **User Data Isolation**: Each user maintains a separate group list.
- **Multi-Destination Group System**: Supports sending messages to multiple selected groups simultaneously.

# External Dependencies
- **Telegram Bot API**:
    - `python-telegram-bot`: Primary library for bot functionality.
    - `BOT_TOKEN`: Environment variable for authentication.
    - `GROUP_CHAT_ID`: Configured for sending messages to a specific group chat.
- **Python Standard Library**:
    - `os`: For environment variable access.
    - `logging`: For application logging and debugging.
    - `re`: For regular expression validation.
    - `typing`: For type hints.
- **File System**:
    - `bot_data.json`: Local JSON file for persistent data storage (e.g., destination group settings).
- **Web Server**:
    - Python's built-in `HTTPServer`: For HTTP health checks on port 5000.