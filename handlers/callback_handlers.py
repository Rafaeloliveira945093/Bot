from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import GROUP_CHAT_ID, MENU_ENVIO, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, EDITAR_ESCOLHA, RECEBER_ENCAMINHADAS, FORWARD_COLLECT, RECEBER_LINK, CONFIRMAR_REPASSAR, SELECIONAR_GRUPO, CONFIRMAR_GRUPO, MENU_EDICAO, ADICIONAR_TEXTO, ADICIONAR_BOTAO_TITULO, ADICIONAR_BOTAO_LINK, REMOVER_PALAVRA, CONFIRMAR_EDICAO
from utils.storage import get_destination_group, set_destination_group
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
            # Check if destination group is registered
            destination_group = get_destination_group()
            if not destination_group:
                keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "❌ Nenhum grupo de destino cadastrado.\n\n"
                    "Use a opção 'Cadastrar grupo de destino' primeiro.",
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
            
            # Initialize forwarding session
            context.user_data.clear()
            context.user_data["messages_sent"] = 0
            context.user_data["menu_msg_id"] = None
            
            await query.edit_message_text(
                f"🔄 Repassar mensagens ativado!\n\n"
                f"Grupo de destino: {destination_group}\n\n"
                f"Envie ou encaminhe mensagens para este chat. Elas serão automaticamente enviadas para o grupo cadastrado."
            )
            return RECEBER_ENCAMINHADAS
        elif query.data == "opcao6":
            # Start group registration process
            from handlers.message_handlers import iniciar_cadastro_grupo
            return await iniciar_cadastro_grupo(update, context)
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
            
            # Show success message with return to menu option
            keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ Mensagem enviada ao grupo com sucesso!",
                reply_markup=reply_markup
            )
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
            total_sent = context.user_data.get("messages_sent", 0)
            
            keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if total_sent == 0:
                await query.edit_message_text(
                    "Nenhuma mensagem foi enviada. Operação finalizada.",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    f"✅ Processo finalizado!\n\n"
                    f"Total de mensagens enviadas: {total_sent}",
                    reply_markup=reply_markup
                )
            
            return ConversationHandler.END
            
        elif query.data == "cancelar_encaminhamento":
            keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Operação cancelada.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
            
        elif query.data == "confirmar_repassar":
            await executar_repassar(update, context)
            return ConversationHandler.END
            
        elif query.data == "cancelar_repassar":
            await query.edit_message_text("Reenvio cancelado.")
            return ConversationHandler.END
            
        # Group registration callbacks
        elif query.data == "confirmar_grupo":
            try:
                group_id = context.user_data.get("pending_group_id")
                if group_id and set_destination_group(group_id):
                    keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"✅ Grupo cadastrado com sucesso!\n\n"
                        f"ID: {group_id}\n\n"
                        f"Agora você pode usar a opção 'Repassar mensagens' para enviar conteúdo automaticamente para este grupo.",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text("❌ Erro ao salvar grupo. Tente novamente.")
                return ConversationHandler.END
            except Exception as e:
                logger.error(f"Error confirming group: {e}")
                await query.edit_message_text("Erro ao confirmar grupo.")
                return ConversationHandler.END
                
        elif query.data == "alterar_grupo":
            await query.edit_message_text(
                "Envie o ID ou nome de outro grupo:\n\n"
                "Formato: -100xxxxxxxxx (para supergrupos) ou @nomecanal (para canais públicos)"
            )
            return SELECIONAR_GRUPO
            
        elif query.data == "cancelar_grupo":
            await query.edit_message_text("Cadastro de grupo cancelado.")
            return ConversationHandler.END
            
        elif query.data == "voltar_menu":
            # Clear any conversation state and return to main menu
            context.user_data.clear()
            from handlers.message_handlers import start
            await start(update, context)
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
        
        # Copy individual messages
        for msg in forwarded_items:
            try:
                await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=msg.chat_id,
                    message_id=msg.message_id
                )
                total_sent += 1
            except Exception as e:
                logger.error(f"Error forwarding message {msg.message_id}: {e}")
        
        # Copy media groups
        for group_messages in media_groups.values():
            for msg in group_messages:
                try:
                    await context.bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=msg.chat_id,
                        message_id=msg.message_id
                    )
                    total_sent += 1
                except Exception as e:
                    logger.error(f"Error forwarding media group message {msg.message_id}: {e}")
        
        keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            f"✅ Sucesso! {total_sent} mensagens foram repassadas para {link_destino}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in executar_repassar: {e}")
        await update.callback_query.edit_message_text(
            "Erro ao repassar mensagens. Verifique se o destino é válido e tente novamente."
        )

async def menu_edicao_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle editing menu button clicks."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "adicionar_texto":
            await query.edit_message_text("✏️ Envie o texto que deseja adicionar:")
            return ADICIONAR_TEXTO
        elif query.data == "adicionar_botao":
            await query.edit_message_text("🔗 Envie o título do botão:")
            return ADICIONAR_BOTAO_TITULO
        elif query.data == "remover_palavra":
            await query.edit_message_text("🗑️ Envie a palavra que deseja remover:")
            return REMOVER_PALAVRA
        elif query.data == "pular_edicao":
            # Send original message without editing
            from handlers.message_handlers import enviar_mensagem_editada
            return await enviar_mensagem_editada(update, context)
        elif query.data == "confirmar_envio":
            # Send the edited message
            from handlers.message_handlers import enviar_mensagem_editada
            return await enviar_mensagem_editada(update, context)
        elif query.data == "editar_novamente":
            # Show editing menu again
            keyboard = [
                [InlineKeyboardButton("✏️ Adicionar texto", callback_data="adicionar_texto")],
                [InlineKeyboardButton("🔗 Adicionar botão", callback_data="adicionar_botao")],
                [InlineKeyboardButton("🗑️ Remover palavra", callback_data="remover_palavra")],
                [InlineKeyboardButton("📤 Pular edição e enviar", callback_data="pular_edicao")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📝 **Menu de Edição**\n\n"
                "Escolha como deseja editar a mensagem antes de enviar:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return MENU_EDICAO
            
    except Exception as e:
        logger.error(f"Error in menu_edicao_handler: {e}")
        await query.edit_message_text("Erro ao processar edição. Tente novamente.")
    
    return MENU_EDICAO
