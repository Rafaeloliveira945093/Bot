import os
import logging
from telegram.ext import ApplicationBuilder, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers.message_handlers import (
    start, receber_midia, receber_texto, receber_botoes, receber_encaminhadas,
    receber_link, comando_pronto, handle_any_message, selecionar_grupo, processar_repassar_mensagem, voltar_menu_principal,
    adicionar_texto_handler, adicionar_botao_titulo_handler, adicionar_botao_link_handler, remover_palavra_handler
)
from handlers.callback_handlers import (
    button_handler, menu_envio_handler, confirmar_previa_handler,
    editar_escolha_handler, encaminhamento_callback_handler, menu_edicao_handler,
    global_callback_handler, handle_any_message
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

# New editing states for option 5
MENU_EDICAO = 101
ADICIONAR_TEXTO = 102
ADICIONAR_BOTAO_TITULO = 103
ADICIONAR_BOTAO_LINK = 104
REMOVER_PALAVRA = 105
CONFIRMAR_EDICAO = 106

def main():
    """Start the bot."""
    # Create the Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Main conversation handler for message sending
    envio_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^opcao4$")],
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
        entry_points=[CallbackQueryHandler(button_handler, pattern="^opcao1$")],
        states={
            SELECIONAR_GRUPO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, selecionar_grupo),
                CallbackQueryHandler(encaminhamento_callback_handler)
            ],
            CONFIRMAR_GRUPO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, selecionar_grupo),
                CallbackQueryHandler(encaminhamento_callback_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    # Forwarding conversation handler with editing menu
    forwarding_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^opcao5$")],
        states={
            RECEBER_ENCAMINHADAS: [
                MessageHandler(filters.ALL & ~filters.COMMAND, receber_encaminhadas)
            ],
            MENU_EDICAO: [
                CallbackQueryHandler(menu_edicao_handler)
            ],
            ADICIONAR_TEXTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, adicionar_texto_handler)
            ],
            ADICIONAR_BOTAO_TITULO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, adicionar_botao_titulo_handler)
            ],
            ADICIONAR_BOTAO_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, adicionar_botao_link_handler)
            ],
            REMOVER_PALAVRA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, remover_palavra_handler)
            ],
            CONFIRMAR_EDICAO: [
                CallbackQueryHandler(menu_edicao_handler)
            ],
            FORWARD_COLLECT: [
                MessageHandler(filters.ALL & ~filters.COMMAND, receber_encaminhadas),
                CallbackQueryHandler(encaminhamento_callback_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(envio_conversation)
    application.add_handler(group_registration_conversation)
    application.add_handler(forwarding_conversation)
    
    # Option 5 is handled by forwarding_conversation
    
    # Handle "voltar_menu" callback from any conversation
    from handlers.message_handlers import voltar_menu_principal
    application.add_handler(CallbackQueryHandler(voltar_menu_principal, pattern="^voltar_menu$"))
    
    # Add global callback handler for menu buttons outside conversations
    from handlers.callback_handlers import global_callback_handler
    application.add_handler(CallbackQueryHandler(global_callback_handler))
    
    # Handle any other message - always show menu (unless in active conversation)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_any_message))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
