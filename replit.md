# Overview

This is a Telegram bot application built with Python and the python-telegram-bot library. The bot provides a menu-driven interface for users to interact with various features including sending messages with media/text/buttons to a group chat, automatic message forwarding to registered groups, and group registration management. The bot is designed to handle conversation flows with multiple states and provides options for content management and automated message distribution.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Bot Framework
- **Framework**: Built on python-telegram-bot library using the Application and ConversationHandler patterns
- **State Management**: Uses conversation states to track user interactions across multiple message exchanges
- **Modular Design**: Separated into distinct modules (handlers, utils, config) for maintainability

## Conversation Flow Architecture
- **Main Menu System**: Six primary options accessible through inline keyboard buttons
- **State-Based Navigation**: Implements 14 different conversation states to handle complex multi-step interactions
- **Conversation Handlers**: Three main conversation flows - message sending, group registration, and legacy message forwarding
- **Automatic Message Processing**: Any message sent to bot is automatically forwarded to registered destination group
- **Fallback Mechanisms**: Includes cancel commands and error handling to gracefully exit conversations

## Message Processing System
- **Multi-Format Support**: Handles text messages, photos, videos, documents, audio, voice, stickers, animations and inline buttons
- **Content Validation**: Validates button formats, URLs, and message content before processing
- **Media Handling**: Processes all media types with file ID tracking and preserves captions/entities
- **Button Generation**: Creates inline keyboards from user-provided text using pipe-separated format
- **Automatic Forwarding**: Copies messages preserving all original content including text formatting, media, captions, and buttons
- **Group Management**: Allows registration and testing of destination groups for automatic message forwarding

## Error Handling and Logging
- **Comprehensive Logging**: Uses Python's logging module for debugging and monitoring
- **Exception Management**: Try-catch blocks around critical operations with user-friendly error messages
- **Input Validation**: Validates user inputs before processing to prevent errors

## Configuration Management
- **Environment Variables**: Bot token and sensitive configuration stored in environment variables
- **Constants**: Centralized configuration file for conversation states and message limits
- **Persistent Storage**: JSON file storage for destination group configuration and user data
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
- **JSON Storage**: Uses local JSON file (bot_data.json) for persistent data storage including destination group settings
- **Memory State**: Stores conversation state in memory using context.user_data
- **Static Configuration**: Uses Python files for configuration rather than external config files
- **Modular Structure**: Organized into handlers/, utils/ directories for better code organization

# Recent Changes (August 20, 2025)

## Group Registration Flow Fix (August 20, 2025 - Evening)

### Fixed Conversation Stuck Issue
- **Group Confirmation Flow**: Fixed issue where users got stuck after confirming group registration
- **Success Message Enhancement**: After successful group registration, users now see proper success message with navigation options
- **Navigation Options**: Added "➕ Adicionar novo grupo ou canal" and "🔙 Voltar ao menu principal" buttons
- **Workflow Port Configuration**: Added HTTP health check server on port 5000 for web application feedback support
- **Global Callback Handler**: Implemented global callback handler for seamless menu navigation outside conversations

### Technical Implementation
- **Port 5000 Web Server**: Uses Python's built-in HTTPServer for health checks without external dependencies
- **Conversation Flow Fix**: Group registration properly ends with user-friendly navigation options
- **Duplicate Prevention**: Enhanced duplicate group detection during registration
- **Sequential Group Registration**: Users can now register multiple groups in sequence without getting stuck
- **Proper State Management**: Conversations end cleanly while maintaining navigation capabilities

## Major System Refactor - Unified Group Management (August 20, 2025 - Morning)

### Unified Group Management System
- **Option 1 Redesign**: Changed from "Gerenciar grupos de destino" to "Gerenciar grupos" 
- **Removed Option 6**: Eliminated redundant "Cadastrar grupo individual" option
- **New Group Storage**: Replaced file-based storage with `context.user_data["grupos"]` array for better user separation
- **Enhanced Group Registration**: Each group test sends "GRUPO ATIVADO" message before confirmation
- **Real-time Group Testing**: Validates bot access during registration process
- **Multiple Group Support**: Users can register unlimited groups with custom names

### Improved Message Sending Flow
- **Destination Selection Required**: Before sending (Options 4 & 5), users must choose destination group
- **Selected Group Display**: Shows chosen group name in confirmation and success messages
- **Enhanced Error Messages**: Clear feedback when no groups are registered
- **Streamlined Navigation**: Direct flow from group selection to message creation/forwarding

### Privacy and Security Enhancements
- **Private Chat Only**: Bot now ignores all messages in group chats (`update.message.chat.type != "private"`)
- **Secure Group Access**: Uses actual message sending for group validation
- **User Data Isolation**: Each user maintains separate group list in their context data

### Technical Implementation
- **New Handler Functions**: Added `mostrar_menu_gerenciar_grupos`, `cadastrar_novo_grupo`, `processar_cadastro_grupo`, `mostrar_grupos_cadastrados`, `mostrar_selecao_destinos`
- **Updated Conversation Flow**: Modified main.py to handle new group management states
- **Enhanced Callback System**: Extended callback handlers for group management operations
- **Improved Error Handling**: Better exception management with user-friendly messages

### User Experience Improvements
- **Intuitive Menu Structure**: Clear hierarchy from main menu → group management → specific actions
- **Visual Feedback**: Progress indicators and confirmation messages throughout registration process
- **Flexible Group Removal**: Easy group deletion with confirmation prompts
- **Success Tracking**: Detailed feedback showing which group received messages

### Backward Compatibility
- **Legacy Support**: Maintains compatibility with existing bot_data.json storage
- **Smooth Migration**: Automatic detection and conversion of old group storage format
- **State Management**: Preserves existing conversation states while adding new ones

# Previous Changes (August 19, 2025)

## New Features Implemented
- **Option 6 - Group Registration**: Added new menu option "Cadastrar grupo de destino" for setting up destination groups
- **Immediate Message Forwarding**: Option 5 now immediately forwards messages to registered destination group without confirmation
- **Group Testing System**: Sends test message "GRUPO ATIVADO" to verify group access before registration
- **Enhanced Message Copying**: Preserves all message types (text, media, stickers, etc.) with original formatting, captions, and buttons
- **Streamlined Flow**: Eliminated confirmation steps in forwarding process for faster operation
- **Anonymous Message Copying**: Replaced forward_message with copy_message to send messages without preserving original sender identity
- **Advanced Message Editing**: Added comprehensive editing menu for option 5 with text addition, button creation, word removal, and preview functionality

## Technical Updates
- **New Storage System**: Added utils/storage.py for persistent JSON-based data storage
- **Extended Conversation States**: Added CADASTRAR_GRUPO, SELECIONAR_GRUPO, CONFIRMAR_GRUPO states and new editing states (MENU_EDICAO, ADICIONAR_TEXTO, ADICIONAR_BOTAO_TITULO, ADICIONAR_BOTAO_LINK, REMOVER_PALAVRA, CONFIRMAR_EDICAO)
- **Message Handler Reorganization**: Separated group registration flow into dedicated conversation handler
- **Smart Message Routing**: Messages automatically forwarded to destination group if registered, otherwise shows main menu

## User Experience Improvements
- **Clear Error Messages**: Provides specific feedback when group access fails or no destination group is set
- **Confirmation Flow**: Three-step confirmation process (test → confirm/alter → save) for group registration
- **Success Notifications**: Clear feedback when messages are forwarded successfully
- **Flexible Group Input**: Accepts both numeric group IDs (-100xxxxxxxxx) and channel usernames (@channelname)
- **Return to Menu**: "Voltar ao Menu Principal" button appears at end of functions 4 and 5 to prevent users getting stuck
- **Automatic Menu Opening**: Any message automatically opens the main menu except during active function execution

## Flow Control System
- **Universal Menu Access**: Any message sent to bot automatically opens main menu
- **Protected Function Flow**: Functions 4 and 5 execute completely without menu interruptions
- **Graceful Return**: At completion of functions 4 and 5, users get "Voltar ao Menu Principal" button
- **State Management**: Conversation states properly managed to prevent conflicts between functions
- **Immediate Processing**: Option 5 processes and forwards messages instantly without confirmation prompts

## Option 5 Bulk Message Workflow with Entity Preservation (Enhanced Feature)
- **Advanced Message Storage**: Stores complete message data including text, caption, entities, caption_entities, file_id, and media_type
- **Telegram Formatting Preservation**: Maintains all original Telegram text formatting (bold, italic, links, etc.) through entities system
- **Collection Interface**: After each message, shows "Finalizar e editar" or "Continuar enviando" buttons
- **Bulk Editing Menu**: Only appears after user clicks "Finalizar e editar" with options to edit all messages simultaneously
- **Entity-Aware Text Addition**: Appends text to message.text (for text messages) or message.caption (for media) while preserving original entities
- **Universal Button Addition**: Adds same inline button to all messages (title + URL validation)
- **Smart Word Removal**: Uses text.replace() on raw content while maintaining existing entity formatting
- **Complete Visual Preview**: Shows actual message previews exactly as they will appear in the destination group with full formatting
- **Entity-Preserving Sending**: Uses send_message(text, entities=entities) for text and send_photo(caption, caption_entities=caption_entities) for media
- **Format Integrity**: Uses parse_mode=None and passes entities/caption_entities directly to preserve exact Telegram formatting
- **Media Type Support**: Handles photo, video, document, audio, voice, sticker with appropriate file_id and caption preservation
- **Automatic Cleanup**: Clears mensagens_temp[user_id] array and returns to main menu after successful sending
- **URL Validation**: Button links must include http:// or https:// protocol for security

## Multi-Destination Group System (New Feature - August 19, 2025)
- **Multiple Group Storage**: Replaced single destination group with groups dictionary: {"Group Name": group_id}
- **Enhanced Option 1**: Changed from "Grupos e canais" to "Gerenciar grupos de destino" with full group management interface
- **Group Management Menu**: Add new groups, remove existing groups, test group access, view all registered groups
- **Destination Selection**: Before sending (Options 4 & 5), users select which groups to target from registered list
- **Multi-Target Sending**: Single message action sends to multiple selected destination groups simultaneously
- **Entity-Preserved Broadcasting**: Each destination receives identical message with preserved Telegram formatting
- **Legacy Compatibility**: Maintains backward compatibility with existing single-group storage system
- **Storage Migration**: Automatic conversion from single destination_group to multiple destination_groups structure