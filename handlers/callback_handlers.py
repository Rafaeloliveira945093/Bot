from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import GROUP_CHAT_ID, MENU_ENVIO, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, EDITAR_ESCOLHA, RECEBER_ENCAMINHADAS, FORWARD_COLLECT, RECEBER_LINK, CONFIRMAR_REPASSAR
import logging

logger = logging.getLogger(__name__)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu button clicks."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "opcao1":
            await query.edit_message_text("Você selecionou: Grupos e canais")
            return ConversationHandler.END
        elif query.data == "opcao2":
            await query.edit_message_text("Você selecionou: Lista de cursos")
            return ConversationHandler.END
        elif query.data == "opcao3":
            await query.edit_message_text("Você selecionou: Grupo VIP")
            return ConversationHandler.END
        elif query.data == "opcao4":
            keyboard = [
                [InlineKeyboardButton("MÍDIA", callback_data="midia")],
                [InlineKeyboardButton("TEXTO", callback_data="texto")],
                [InlineKeyboardButton("BOTÕES", callback_data="botoes")],
                [InlineKeyboardButton("INICIAR", callback_data="iniciar")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Escolha o tipo de conteúdo ou clique em INICIAR para começar:",
                reply_markup=reply_markup
            )
            return MENU_ENVIO
        elif query.data == "opcao5":
            # Initialize forwarding session
            context.user_data.clear()
            context.user_data["forwarded_items"] = []
            context.user_data["media_groups"] = {}
            context.user_data["menu_msg_id"] = None
            
            await query.edit_message_text("Encaminhe uma ou mais mensagens para este chat.")
            await mostrar_menu_encaminhamento(update, context)
            return RECEBER_ENCAMINHADAS
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        await query.edit_message_text("Erro ao processar seleção. Tente novamente.")
    
    return ConversationHandler.END

async def menu_envio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle message creation menu selections."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "midia":
            await query.edit_message_text("Você selecionou: MÍDIA.")
            return MENU_ENVIO
        elif query.data == "texto":
            await query.edit_message_text("Você selecionou: TEXTO.")
            return MENU_ENVIO
        elif query.data == "botoes":
            await query.edit_message_text("Você selecionou: BOTÕES.")
            return MENU_ENVIO
        elif query.data == "iniciar":
            await query.edit_message_text("Envie a mídia (foto ou vídeo) que deseja postar:")
            return RECEBER_MIDIA
    except Exception as e:
        logger.error(f"Error in menu_envio_handler: {e}")
        await query.edit_message_text("Erro ao processar seleção. Tente novamente.")
    
    return MENU_ENVIO

async def confirmar_previa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle preview confirmation."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "sim":
            # Send message to group
            midia = context.user_data.get("midia")
            texto = context.user_data.get("texto", "")
            botoes = context.user_data.get("botoes", [])
            
            reply_markup = None
            if botoes:
                reply_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(nome, url=link)] for nome, link in botoes]
                )
            
            if midia:
                tipo, file_id = midia
                if tipo == "photo":
                    await context.bot.send_photo(
                        chat_id=GROUP_CHAT_ID,
                        photo=file_id,
                        caption=texto,
                        reply_markup=reply_markup
                    )
                elif tipo == "video":
                    await context.bot.send_video(
                        chat_id=GROUP_CHAT_ID,
                        video=file_id,
                        caption=texto,
                        reply_markup=reply_markup
                    )
            else:
                await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=texto,
                    reply_markup=reply_markup
                )
            
            await query.edit_message_text("Mensagem enviada ao grupo com sucesso!")
            return ConversationHandler.END
            
        elif query.data == "editar":
            keyboard = [
                [InlineKeyboardButton("MÍDIA", callback_data="editar_midia")],
                [InlineKeyboardButton("TEXTO", callback_data="editar_texto")],
                [InlineKeyboardButton("BOTÕES", callback_data="editar_botoes")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Qual parte deseja editar?", reply_markup=reply_markup)
            return EDITAR_ESCOLHA
    except Exception as e:
        logger.error(f"Error in confirmar_previa_handler: {e}")
        await query.edit_message_text("Erro ao processar confirmação. Tente novamente.")
    
    return ConversationHandler.END

async def editar_escolha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit choice selection."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "editar_midia":
            await query.edit_message_text("Envie a nova mídia (foto ou vídeo):")
            return RECEBER_MIDIA
        elif query.data == "editar_texto":
            await query.edit_message_text("Envie o novo texto:")
            return RECEBER_TEXTO
        elif query.data == "editar_botoes":
            await query.edit_message_text(
                "Envie os novos botões no formato:\nNOME|LINK, NOME2|LINK2"
            )
            return RECEBER_BOTOES
    except Exception as e:
        logger.error(f"Error in editar_escolha_handler: {e}")
        await query.edit_message_text("Erro ao processar edição. Tente novamente.")
    
    return EDITAR_ESCOLHA

async def encaminhamento_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle forwarding menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "add_msgs":
            await query.edit_message_text("Continue encaminhando mensagens...")
            return FORWARD_COLLECT
            
        elif query.data == "finalizar_encaminhamento":
            total_items = len(context.user_data.get("forwarded_items", [])) + sum(
                len(g) for g in context.user_data.get("media_groups", {}).values()
            )
            
            if total_items == 0:
                await query.edit_message_text("Nenhuma mensagem foi coletada. Operação cancelada.")
                return ConversationHandler.END
            
            await query.edit_message_text("Agora envie o link de destino (grupo, canal ou chat):")
            return RECEBER_LINK
            
        elif query.data == "cancelar_encaminhamento":
            await query.edit_message_text("Operação cancelada.")
            return ConversationHandler.END
            
        elif query.data == "confirmar_repassar":
            await executar_repassar(update, context)
            return ConversationHandler.END
            
        elif query.data == "cancelar_repassar":
            await query.edit_message_text("Reenvio cancelado.")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in encaminhamento_callback_handler: {e}")
        await query.edit_message_text("Erro ao processar seleção. Tente novamente.")
    
    return FORWARD_COLLECT

async def mostrar_menu_encaminhamento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show forwarding menu."""
    keyboard = [
        [InlineKeyboardButton("Adicionar mais mensagens", callback_data="add_msgs")],
        [InlineKeyboardButton("Finalizar", callback_data="finalizar_encaminhamento")],
        [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if context.user_data.get("menu_msg_id"):
            await update.effective_chat.edit_message_reply_markup(
                message_id=context.user_data["menu_msg_id"],
                reply_markup=reply_markup
            )
        else:
            msg = await update.effective_chat.send_message(
                "Quando terminar, clique em Finalizar.\nPara cancelar, clique em Cancelar.",
                reply_markup=reply_markup
            )
            context.user_data["menu_msg_id"] = msg.message_id
    except Exception as e:
        logger.error(f"Error showing forwarding menu: {e}")

async def executar_repassar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute the forwarding of collected messages."""
    try:
        link_destino = context.user_data.get("link_destino")
        forwarded_items = context.user_data.get("forwarded_items", [])
        media_groups = context.user_data.get("media_groups", {})
        
        # Convert link to chat_id if it's a username
        chat_id = link_destino
        if link_destino.startswith("t.me/"):
            chat_id = f"@{link_destino.split('/')[-1]}"
        elif link_destino.startswith("@"):
            chat_id = link_destino
        else:
            try:
                chat_id = int(link_destino)
            except ValueError:
                await update.callback_query.edit_message_text("Formato de link inválido.")
                return
        
        total_sent = 0
        
        # Forward individual messages
        for msg in forwarded_items:
            try:
                await context.bot.forward_message(
                    chat_id=chat_id,
                    from_chat_id=msg.chat_id,
                    message_id=msg.message_id
                )
                total_sent += 1
            except Exception as e:
                logger.error(f"Error forwarding message {msg.message_id}: {e}")
        
        # Forward media groups
        for group_messages in media_groups.values():
            for msg in group_messages:
                try:
                    await context.bot.forward_message(
                        chat_id=chat_id,
                        from_chat_id=msg.chat_id,
                        message_id=msg.message_id
                    )
                    total_sent += 1
                except Exception as e:
                    logger.error(f"Error forwarding media group message {msg.message_id}: {e}")
        
        await update.callback_query.edit_message_text(
            f"Sucesso! {total_sent} mensagens foram repassadas para {link_destino}"
        )
        
    except Exception as e:
        logger.error(f"Error in executar_repassar: {e}")
        await update.callback_query.edit_message_text(
            "Erro ao repassar mensagens. Verifique se o destino é válido e tente novamente."
        )
