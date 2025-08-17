import os
import logging
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers.message_handlers import (
    start, receber_midia, receber_texto, receber_botoes, receber_encaminhadas,
    receber_link, comando_pronto, handle_any_message, selecionar_grupo, processar_repassar_mensagem
)
from handlers.callback_handlers import (
    button_handler, menu_envio_handler, confirmar_previa_handler,
    editar_escolha_handler, encaminhamento_callback_handler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(MENU_ENVIO, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, 
 CONFIRMAR_PREVIA, EDITAR_ESCOLHA, MENU_REPASSAR, RECEBER_ENCAMINHADAS, 
 RECEBER_LINK, CONFIRMAR_REPASSAR, EDITAR_REPASSAR, CADASTRAR_GRUPO,
 SELECIONAR_GRUPO, CONFIRMAR_GRUPO) = range(14)

FORWARD_COLLECT = 100

def main():
    """Start the bot."""
    # Create the Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Main conversation handler for message sending
    envio_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^opcao[1-4]$")],
        states={
            MENU_ENVIO: [CallbackQueryHandler(menu_envio_handler)],
            RECEBER_MIDIA: [MessageHandler(filters.PHOTO | filters.VIDEO, receber_midia)],
            RECEBER_TEXTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_texto)],
            RECEBER_BOTOES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_botoes)],
            CONFIRMAR_PREVIA: [CallbackQueryHandler(confirmar_previa_handler)],
            EDITAR_ESCOLHA: [CallbackQueryHandler(editar_escolha_handler)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    # Group registration conversation handler
    group_registration_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^opcao6$")],
        states={
            SELECIONAR_GRUPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, selecionar_grupo)],
            CONFIRMAR_GRUPO: [CallbackQueryHandler(encaminhamento_callback_handler)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    # Legacy forwarding conversation handler (for old system if needed)
    forwarding_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^opcao_legacy$")],
        states={
            RECEBER_ENCAMINHADAS: [
                MessageHandler(filters.ALL & ~filters.COMMAND, receber_encaminhadas),
                CallbackQueryHandler(encaminhamento_callback_handler)
            ],
            FORWARD_COLLECT: [
                MessageHandler(filters.ALL & ~filters.COMMAND, receber_encaminhadas),
                CallbackQueryHandler(encaminhamento_callback_handler),
                CommandHandler("pronto", comando_pronto)
            ],
            RECEBER_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link)],
            CONFIRMAR_REPASSAR: [CallbackQueryHandler(encaminhamento_callback_handler)],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(envio_conversation)
    application.add_handler(group_registration_conversation)
    application.add_handler(forwarding_conversation)
    
    # Handle option 5 (message forwarding) separately
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^opcao5$"))
    
    # Handle any other message - either forward to destination group or show menu
    def create_message_handler():
        from utils.storage import get_destination_group
        
        async def handle_message(update, context):
            # Skip if it's a command
            if update.message and update.message.text and update.message.text.startswith('/'):
                return
            
            # Check if we have a destination group registered
            destination_group = get_destination_group()
            if destination_group:
                # Forward the message
                await processar_repassar_mensagem(update, context)
            else:
                # Show main menu
                await handle_any_message(update, context)
        
        return handle_message
    
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, create_message_handler()))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
