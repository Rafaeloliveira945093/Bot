# Overview

This is a Telegram bot application built with Python and the python-telegram-bot library. The bot provides a menu-driven interface for users to interact with various features including sending messages with media/text/buttons to a group chat, and forwarding messages. The bot is designed to handle conversation flows with multiple states and provides options for content management and message distribution.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Bot Framework
- **Framework**: Built on python-telegram-bot library using the Application and ConversationHandler patterns
- **State Management**: Uses conversation states to track user interactions across multiple message exchanges
- **Modular Design**: Separated into distinct modules (handlers, utils, config) for maintainability

## Conversation Flow Architecture
- **Main Menu System**: Five primary options accessible through inline keyboard buttons
- **State-Based Navigation**: Implements 11 different conversation states to handle complex multi-step interactions
- **Conversation Handlers**: Two main conversation flows - message sending and message forwarding
- **Fallback Mechanisms**: Includes cancel commands and error handling to gracefully exit conversations

## Message Processing System
- **Multi-Format Support**: Handles text messages, photos, videos, and inline buttons
- **Content Validation**: Validates button formats, URLs, and message content before processing
- **Media Handling**: Processes photo and video uploads with file ID tracking
- **Button Generation**: Creates inline keyboards from user-provided text using pipe-separated format

## Error Handling and Logging
- **Comprehensive Logging**: Uses Python's logging module for debugging and monitoring
- **Exception Management**: Try-catch blocks around critical operations with user-friendly error messages
- **Input Validation**: Validates user inputs before processing to prevent errors

## Configuration Management
- **Environment Variables**: Bot token and sensitive configuration stored in environment variables
- **Constants**: Centralized configuration file for conversation states and message limits
- **Type Safety**: Uses type hints throughout the codebase for better maintainability

# External Dependencies

## Telegram Bot API
- **python-telegram-bot**: Primary library for Telegram bot functionality
- **Bot Token**: Requires BOT_TOKEN environment variable for authentication
- **Group Integration**: Configured to send messages to a specific group chat (GROUP_CHAT_ID)

## Python Standard Library
- **os**: Environment variable access
- **logging**: Application logging and debugging
- **re**: Regular expression validation for URLs and text patterns
- **typing**: Type hints for better code quality

## Message Limits
- **Telegram API Constraints**: Respects Telegram's message length limits (4096 chars for messages, 1024 for captions)
- **Content Validation**: Validates URLs and button formats before sending

## File System
- **No Database**: Currently stores conversation state in memory using context.user_data
- **Static Configuration**: Uses Python files for configuration rather than external config files