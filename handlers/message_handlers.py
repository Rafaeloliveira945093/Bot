from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import GROUP_CHAT_ID, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, CONFIRMAR_PREVIA, RECEBER_ENCAMINHADAS, FORWARD_COLLECT, RECEBER_LINK, CONFIRMAR_REPASSAR, CADASTRAR_GRUPO, SELECIONAR_GRUPO, CONFIRMAR_GRUPO, MENU_EDICAO, ADICIONAR_TEXTO, ADICIONAR_BOTAO_TITULO, ADICIONAR_BOTAO_LINK, REMOVER_PALAVRA, CONFIRMAR_EDICAO
from utils.validators import validate_button_format, validate_telegram_link
from utils.storage import get_destination_group, set_destination_group
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send main menu when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("1 – Grupos e canais", callback_data="opcao1")],
        [InlineKeyboardButton("2 – Lista de cursos", callback_data="opcao2")],
        [InlineKeyboardButton("3 – Grupo VIP", callback_data="opcao3")],
        [InlineKeyboardButton("4 – Enviar mensagem", callback_data="opcao4")],
        [InlineKeyboardButton("5 – Repassar mensagens", callback_data="opcao5")],
        [InlineKeyboardButton("6 – Cadastrar grupo de destino", callback_data="opcao6")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("Escolha uma opção:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Escolha uma opção:", reply_markup=reply_markup)

async def receber_midia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle media (photo or video) upload."""
    try:
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            context.user_data["midia"] = ("photo", file_id)
            logger.info(f"Photo received: {file_id}")
        elif update.message.video:
            file_id = update.message.video.file_id
            context.user_data["midia"] = ("video", file_id)
            logger.info(f"Video received: {file_id}")
        else:
            await update.message.reply_text("Por favor, envie uma foto ou vídeo.")
            return RECEBER_MIDIA
        
        await update.message.reply_text("Agora envie o texto da mensagem:")
        return RECEBER_TEXTO
    except Exception as e:
        logger.error(f"Error receiving media: {e}")
        await update.message.reply_text("Erro ao processar mídia. Tente novamente.")
        return RECEBER_MIDIA

async def receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text input for message content."""
    try:
        text = update.message.text
        if len(text) > 1000:  # Reasonable limit for caption
            await update.message.reply_text("Texto muito longo. Limite de 1000 caracteres.")
            return RECEBER_TEXTO
        
        context.user_data["texto"] = text
        await update.message.reply_text(
            "Agora envie os botões no formato:\n\n"
            "NOME1|LINK1, NOME2|LINK2\n\n"
            "Exemplo:\nVIP|https://t.me/grupovip, Cursos|https://t.me/cursos"
        )
        return RECEBER_BOTOES
    except Exception as e:
        logger.error(f"Error receiving text: {e}")
        await update.message.reply_text("Erro ao processar texto. Tente novamente.")
        return RECEBER_TEXTO

async def receber_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button format input and validate."""
    try:
        texto = update.message.text
        botoes = validate_button_format(texto)
        
        if botoes is None:
            await update.message.reply_text(
                "Formato inválido. Envie os botões como: NOME|LINK, NOME2|LINK2\n"
                "Certifique-se de que todos os links são válidos."
            )
            return RECEBER_BOTOES
        
        context.user_data["botoes"] = botoes
        await mostrar_previa(update, context)
        return CONFIRMAR_PREVIA
    except Exception as e:
        logger.error(f"Error receiving buttons: {e}")
        await update.message.reply_text("Erro ao processar botões. Tente novamente.")
        return RECEBER_BOTOES

async def mostrar_previa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show preview of the message to be sent."""
    try:
        midia = context.user_data.get("midia")
        texto = context.user_data.get("texto", "")
        botoes = context.user_data.get("botoes", [])
        
        reply_markup = None
        if botoes:
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton(nome, url=link)] for nome, link in botoes]
            )
        
        # Send preview exactly as it will be posted
        if midia:
            tipo, file_id = midia
            if tipo == "photo":
                await update.message.reply_photo(
                    photo=file_id, 
                    caption=texto, 
                    reply_markup=reply_markup
                )
            elif tipo == "video":
                await update.message.reply_video(
                    video=file_id, 
                    caption=texto, 
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(texto, reply_markup=reply_markup)
        
        # Confirmation menu
        keyboard = [
            [InlineKeyboardButton("Confirmar", callback_data="sim")],
            [InlineKeyboardButton("Editar", callback_data="editar")]
        ]
        reply_markup_confirm = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Está correto?", reply_markup=reply_markup_confirm)
    except Exception as e:
        logger.error(f"Error showing preview: {e}")
        await update.message.reply_text("Erro ao mostrar prévia. Tente novamente.")

async def receber_encaminhadas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle forwarded messages for option 5 - collect multiple messages."""
    try:
        msg = update.message
        
        # Get destination group
        from utils.storage import get_destination_group
        destination_group = get_destination_group()
        
        if not destination_group:
            keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await msg.reply_text(
                "❌ Nenhum grupo de destino cadastrado.\n\n"
                "Use a opção 'Cadastrar grupo de destino' primeiro.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        
        # Check for protected content
        if getattr(msg, "has_protected_content", False):
            await msg.reply_text("Conteúdo protegido contra cópia. Envie outro item.")
            return FORWARD_COLLECT
        
        # Initialize message collection for this user
        user_id = update.effective_user.id
        if 'mensagens_temp' not in context.bot_data:
            context.bot_data['mensagens_temp'] = {}
        
        if user_id not in context.bot_data['mensagens_temp']:
            context.bot_data['mensagens_temp'][user_id] = []
        
        # Store the original message with all formatting preserved
        message_data = {
            'message': msg,
            'text': msg.text,
            'caption': msg.caption,
            'entities': msg.entities,
            'caption_entities': msg.caption_entities,
            'file_id': None,
            'media_type': None
        }
        
        # Extract file_id and media type for different message types
        if msg.photo:
            message_data['file_id'] = msg.photo[-1].file_id
            message_data['media_type'] = 'photo'
        elif msg.video:
            message_data['file_id'] = msg.video.file_id
            message_data['media_type'] = 'video'
        elif msg.document:
            message_data['file_id'] = msg.document.file_id
            message_data['media_type'] = 'document'
        elif msg.audio:
            message_data['file_id'] = msg.audio.file_id
            message_data['media_type'] = 'audio'
        elif msg.voice:
            message_data['file_id'] = msg.voice.file_id
            message_data['media_type'] = 'voice'
        elif msg.sticker:
            message_data['file_id'] = msg.sticker.file_id
            message_data['media_type'] = 'sticker'
        else:
            message_data['media_type'] = 'text'
        
        context.bot_data['mensagens_temp'][user_id].append(message_data)
        
        # Show collection status and continue/finish options
        total_messages = len(context.bot_data['mensagens_temp'][user_id])
        keyboard = [
            [InlineKeyboardButton("✅ Finalizar e editar", callback_data="finalizar_coleta")],
            [InlineKeyboardButton("🔄 Continuar enviando", callback_data="continuar_coleta")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg.reply_text(
            f"📥 Mensagem {total_messages} salva!\n\n"
            f"Total de mensagens: {total_messages}\n\n"
            "Deseja continuar enviando mensagens ou finalizar para editar todas de uma vez?",
            reply_markup=reply_markup
        )
        
        return FORWARD_COLLECT
        
    except Exception as e:
        logger.error(f"Error receiving forwarded messages: {e}")
        await update.message.reply_text("Erro ao processar mensagem.")
        return FORWARD_COLLECT

async def adicionar_texto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle adding text to all messages in bulk editing."""
    try:
        text_to_add = update.message.text
        edited_data = context.user_data.get("edited_data", [])
        
        # Add text to all messages
        for item in edited_data:
            if item['media_type'] == 'text':
                # For text messages, append to text
                if item['text']:
                    item['text'] = item['text'] + "\n\n" + text_to_add
                else:
                    item['text'] = text_to_add
            else:
                # For media messages, append to caption
                if item['caption']:
                    item['caption'] = item['caption'] + "\n\n" + text_to_add
                else:
                    item['caption'] = text_to_add
        
        context.user_data["edited_data"] = edited_data
        
        await update.message.reply_text("✅ Texto adicionado a todas as mensagens! Voltando ao menu de edição...")
        
        # Show bulk editing menu again
        messages = context.user_data.get("messages_to_edit", [])
        keyboard = [
            [InlineKeyboardButton("✏️ Adicionar texto a todas", callback_data="adicionar_texto_bulk")],
            [InlineKeyboardButton("🔗 Adicionar botão a todas", callback_data="adicionar_botao_bulk")],
            [InlineKeyboardButton("🗑️ Remover palavra de todas", callback_data="remover_palavra_bulk")],
            [InlineKeyboardButton("👁️ Ver prévia de todas", callback_data="previa_bulk")],
            [InlineKeyboardButton("📤 Enviar todas sem editar", callback_data="enviar_bulk")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total = len(messages)
        await update.message.reply_text(
            f"📝 **Menu de Edição em Lote**\n\n"
            f"Total de mensagens: {total}\n\n"
            "Escolha como deseja editar todas as mensagens:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MENU_EDICAO
        
    except Exception as e:
        logger.error(f"Error adding text: {e}")
        await update.message.reply_text("Erro ao adicionar texto. Tente novamente.")
        return MENU_EDICAO

async def adicionar_botao_titulo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button title input."""
    try:
        context.user_data["button_title"] = update.message.text
        await update.message.reply_text("💬 Agora envie o link do botão:")
        return ADICIONAR_BOTAO_LINK
        
    except Exception as e:
        logger.error(f"Error handling button title: {e}")
        await update.message.reply_text("Erro ao processar título. Tente novamente.")
        return ADICIONAR_BOTAO_TITULO

async def adicionar_botao_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button link input and add button to all messages."""
    try:
        button_link = update.message.text
        button_title = context.user_data.get("button_title", "")
        
        # Validate URL
        if not (button_link.startswith("http://") or button_link.startswith("https://")):
            await update.message.reply_text("❌ Link inválido. Use um link completo (http:// ou https://)")
            return ADICIONAR_BOTAO_LINK
        
        # Add button to list (will be applied to all messages)
        if "added_buttons" not in context.user_data:
            context.user_data["added_buttons"] = []
        
        context.user_data["added_buttons"].append({
            "title": button_title,
            "url": button_link
        })
        
        await update.message.reply_text("✅ Botão adicionado a todas as mensagens! Voltando ao menu de edição...")
        
        # Show bulk editing menu again
        messages = context.user_data.get("messages_to_edit", [])
        keyboard = [
            [InlineKeyboardButton("✏️ Adicionar texto a todas", callback_data="adicionar_texto_bulk")],
            [InlineKeyboardButton("🔗 Adicionar botão a todas", callback_data="adicionar_botao_bulk")],
            [InlineKeyboardButton("🗑️ Remover palavra de todas", callback_data="remover_palavra_bulk")],
            [InlineKeyboardButton("👁️ Ver prévia de todas", callback_data="previa_bulk")],
            [InlineKeyboardButton("📤 Enviar todas sem editar", callback_data="enviar_bulk")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total = len(messages)
        await update.message.reply_text(
            f"📝 **Menu de Edição em Lote**\n\n"
            f"Total de mensagens: {total}\n\n"
            "Escolha como deseja editar todas as mensagens:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MENU_EDICAO
        
    except Exception as e:
        logger.error(f"Error adding button: {e}")
        await update.message.reply_text("Erro ao adicionar botão. Tente novamente.")
        return ADICIONAR_BOTAO_LINK

async def remover_palavra_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle word removal from all messages."""
    try:
        word_to_remove = update.message.text.strip()
        edited_data = context.user_data.get("edited_data", [])
        
        # Remove word from all messages
        for item in edited_data:
            if item['media_type'] == 'text' and item['text']:
                # Remove from text content
                updated_text = item['text'].replace(word_to_remove, "")
                updated_text = " ".join(updated_text.split())
                item['text'] = updated_text
            elif item['caption']:
                # Remove from caption content
                updated_caption = item['caption'].replace(word_to_remove, "")
                updated_caption = " ".join(updated_caption.split())
                item['caption'] = updated_caption
        
        context.user_data["edited_data"] = edited_data
        
        await update.message.reply_text(f"✅ Palavra '{word_to_remove}' removida de todas as mensagens! Voltando ao menu de edição...")
        
        # Show bulk editing menu again
        messages = context.user_data.get("messages_to_edit", [])
        keyboard = [
            [InlineKeyboardButton("✏️ Adicionar texto a todas", callback_data="adicionar_texto_bulk")],
            [InlineKeyboardButton("🔗 Adicionar botão a todas", callback_data="adicionar_botao_bulk")],
            [InlineKeyboardButton("🗑️ Remover palavra de todas", callback_data="remover_palavra_bulk")],
            [InlineKeyboardButton("👁️ Ver prévia de todas", callback_data="previa_bulk")],
            [InlineKeyboardButton("📤 Enviar todas sem editar", callback_data="enviar_bulk")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        total = len(messages)
        await update.message.reply_text(
            f"📝 **Menu de Edição em Lote**\n\n"
            f"Total de mensagens: {total}\n\n"
            "Escolha como deseja editar todas as mensagens:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return MENU_EDICAO
        
    except Exception as e:
        logger.error(f"Error removing word: {e}")
        await update.message.reply_text("Erro ao remover palavra. Tente novamente.")
        return REMOVER_PALAVRA

async def mostrar_previa_edicao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show preview of edited message."""
    try:
        original_msg = context.user_data["original_message"]
        edited_text = context.user_data.get("edited_text", "")
        added_buttons = context.user_data.get("added_buttons", [])
        
        # Create preview message
        preview_text = "📋 **Prévia da mensagem editada:**\n\n"
        
        if edited_text:
            preview_text += edited_text
        else:
            preview_text += "_[Mensagem sem texto]_"
        
        # Create reply markup with added buttons
        keyboard = []
        for button in added_buttons:
            keyboard.append([InlineKeyboardButton(button["title"], url=button["url"])])
        
        # Add confirmation buttons
        keyboard.extend([
            [InlineKeyboardButton("✅ Confirmar envio", callback_data="confirmar_envio")],
            [InlineKeyboardButton("✏️ Editar novamente", callback_data="editar_novamente")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Show preview
        if original_msg.photo or original_msg.video or original_msg.document or original_msg.audio:
            # For media messages, show media with edited caption
            if original_msg.photo:
                await original_msg.reply_photo(
                    photo=original_msg.photo[-1].file_id,
                    caption=preview_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            elif original_msg.video:
                await original_msg.reply_video(
                    video=original_msg.video.file_id,
                    caption=preview_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            elif original_msg.document:
                await original_msg.reply_document(
                    document=original_msg.document.file_id,
                    caption=preview_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            elif original_msg.audio:
                await original_msg.reply_audio(
                    audio=original_msg.audio.file_id,
                    caption=preview_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        else:
            # For text messages
            await original_msg.reply_text(
                preview_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        return CONFIRMAR_EDICAO
        
    except Exception as e:
        logger.error(f"Error showing preview: {e}")
        await update.message.reply_text("Erro ao mostrar prévia. Tente novamente.")
        return MENU_EDICAO

async def enviar_mensagem_editada(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send the edited message to destination group."""
    try:
        original_msg = context.user_data["original_message"]
        destination_group = context.user_data["destination_group"]
        edited_text = context.user_data.get("edited_text", "")
        added_buttons = context.user_data.get("added_buttons", [])
        
        # Create reply markup with added buttons
        reply_markup = None
        if added_buttons:
            keyboard = []
            for button in added_buttons:
                keyboard.append([InlineKeyboardButton(button["title"], url=button["url"])])
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Check if message was edited (has new text or buttons)
        was_edited = (edited_text != (original_msg.text or original_msg.caption or "")) or added_buttons
        
        if was_edited:
            # Send as new message with edited content
            if original_msg.photo:
                await context.bot.send_photo(
                    chat_id=destination_group,
                    photo=original_msg.photo[-1].file_id,
                    caption=edited_text,
                    reply_markup=reply_markup
                )
            elif original_msg.video:
                await context.bot.send_video(
                    chat_id=destination_group,
                    video=original_msg.video.file_id,
                    caption=edited_text,
                    reply_markup=reply_markup
                )
            elif original_msg.document:
                await context.bot.send_document(
                    chat_id=destination_group,
                    document=original_msg.document.file_id,
                    caption=edited_text,
                    reply_markup=reply_markup
                )
            elif original_msg.audio:
                await context.bot.send_audio(
                    chat_id=destination_group,
                    audio=original_msg.audio.file_id,
                    caption=edited_text,
                    reply_markup=reply_markup
                )
            elif original_msg.voice:
                # Voice notes can't have captions, so send text separately if edited
                await context.bot.send_voice(
                    chat_id=destination_group,
                    voice=original_msg.voice.file_id
                )
                if edited_text:
                    await context.bot.send_message(
                        chat_id=destination_group,
                        text=edited_text,
                        reply_markup=reply_markup
                    )
            else:
                # Text message
                await context.bot.send_message(
                    chat_id=destination_group,
                    text=edited_text,
                    reply_markup=reply_markup
                )
        else:
            # Use copy_message for unedited content
            await context.bot.copy_message(
                chat_id=destination_group,
                from_chat_id=original_msg.chat_id,
                message_id=original_msg.message_id
            )
        
        # Show success message
        keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
        reply_markup_success = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "✅ Mensagem enviada com sucesso!",
            reply_markup=reply_markup_success
        )
        
        # Clean up user data
        context.user_data.pop("original_message", None)
        context.user_data.pop("edited_text", None)
        context.user_data.pop("added_buttons", None)
        context.user_data.pop("button_title", None)
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error sending edited message: {e}")
        await update.callback_query.edit_message_text("❌ Erro ao enviar mensagem.")
        return ConversationHandler.END

async def atualizar_menu_encaminhamento(context, chat_id, menu_msg_id, total):
    """Update the forwarding menu with current count."""
    try:
        keyboard = [
            [InlineKeyboardButton("Adicionar mais mensagens", callback_data="add_msgs")],
            [InlineKeyboardButton(f"Finalizar ({total} coletados)", callback_data="finalizar_encaminhamento")],
            [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=menu_msg_id,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error updating forwarding menu: {e}")

async def comando_pronto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /pronto command to finish collecting messages."""
    try:
        total_items = len(context.user_data.get("forwarded_items", [])) + sum(
            len(g) for g in context.user_data.get("media_groups", {}).values()
        )
        
        if total_items == 0:
            await update.message.reply_text(
                "Você não encaminhou nenhuma mensagem. Encaminhe ao menos uma antes de digitar /pronto."
            )
            return RECEBER_ENCAMINHADAS
        
        await update.message.reply_text("Agora envie o link de destino (grupo, canal ou chat):")
        return RECEBER_LINK
    except Exception as e:
        logger.error(f"Error in comando_pronto: {e}")
        await update.message.reply_text("Erro ao processar comando. Tente novamente.")
        return RECEBER_ENCAMINHADAS

async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle destination link input."""
    try:
        link = update.message.text.strip()
        
        if not validate_telegram_link(link):
            await update.message.reply_text(
                "Link inválido. Envie um link do Telegram válido (t.me/username) ou ID do chat."
            )
            return RECEBER_LINK
        
        context.user_data["link_destino"] = link
        
        # Show confirmation with summary
        total_items = len(context.user_data.get("forwarded_items", [])) + sum(
            len(g) for g in context.user_data.get("media_groups", {}).values()
        )
        
        keyboard = [
            [InlineKeyboardButton("Confirmar envio", callback_data="confirmar_repassar")],
            [InlineKeyboardButton("Cancelar", callback_data="cancelar_repassar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Destino: {link}\n"
            f"Total de itens: {total_items}\n\n"
            f"Confirma o envio?",
            reply_markup=reply_markup
        )
        
        return CONFIRMAR_REPASSAR
    except Exception as e:
        logger.error(f"Error receiving link: {e}")
        await update.message.reply_text("Erro ao processar link. Tente novamente.")
        return RECEBER_LINK

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any message that doesn't match other handlers - show main menu."""
    await start(update, context)

async def voltar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to main menu and clear any conversation state."""
    context.user_data.clear()
    await update.callback_query.edit_message_text("Voltando ao menu principal...")
    await start(update, context)
    return ConversationHandler.END

# New functions for group registration and message forwarding

async def iniciar_cadastro_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the group registration process by listing available groups."""
    try:
        # Get bot's chats/groups
        bot_user = await context.bot.get_me()
        
        # Since we can't directly list all chats, we'll ask user to add bot to groups first
        await update.callback_query.edit_message_text(
            "Para cadastrar um grupo de destino, primeiro adicione este bot aos grupos/canais desejados como administrador.\n\n"
            "Depois, envie o ID do grupo ou canal que deseja usar como destino.\n\n"
            "Formato: -100xxxxxxxxx (para supergrupos) ou @nomecanal (para canais públicos)"
        )
        return SELECIONAR_GRUPO
    except Exception as e:
        logger.error(f"Error starting group registration: {e}")
        await update.callback_query.edit_message_text("Erro ao iniciar cadastro. Tente novamente.")
        return ConversationHandler.END

async def selecionar_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle group selection by ID or username."""
    try:
        group_input = update.message.text.strip()
        
        # Validate and convert input
        chat_id = None
        if group_input.startswith("-"):
            try:
                chat_id = int(group_input)
            except ValueError:
                await update.message.reply_text("ID de grupo inválido. Use o formato: -100xxxxxxxxx")
                return SELECIONAR_GRUPO
        elif group_input.startswith("@"):
            chat_id = group_input
        else:
            await update.message.reply_text(
                "Formato inválido. Use:\n"
                "- ID do grupo: -100xxxxxxxxx\n"
                "- Nome do canal: @nomecanal"
            )
            return SELECIONAR_GRUPO
        
        # Test if bot can send message to this group
        try:
            test_message = await context.bot.send_message(
                chat_id=chat_id,
                text="🤖 GRUPO ATIVADO\n\nEste grupo foi selecionado como destino para repassar mensagens."
            )
            
            # Store for confirmation
            context.user_data["pending_group_id"] = chat_id
            context.user_data["test_message_id"] = test_message.message_id
            
            # Show confirmation menu
            keyboard = [
                [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar_grupo")],
                [InlineKeyboardButton("🔄 Alterar", callback_data="alterar_grupo")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_grupo")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Mensagem de teste enviada para: {chat_id}\n\n"
                f"Confirma este grupo como destino das mensagens?",
                reply_markup=reply_markup
            )
            return CONFIRMAR_GRUPO
            
        except Exception as e:
            logger.error(f"Error testing group access: {e}")
            await update.message.reply_text(
                "❌ Não foi possível enviar mensagem para este grupo.\n\n"
                "Verifique se:\n"
                "• O bot foi adicionado ao grupo\n"
                "• O bot tem permissão para enviar mensagens\n"
                "• O ID/nome está correto\n\n"
                "Tente novamente:"
            )
            return SELECIONAR_GRUPO
            
    except Exception as e:
        logger.error(f"Error in selecionar_grupo: {e}")
        await update.message.reply_text("Erro ao processar seleção. Tente novamente.")
        return SELECIONAR_GRUPO

async def processar_repassar_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process and forward any message to the registered destination group."""
    try:
        destination_group = get_destination_group()
        if not destination_group:
            await update.message.reply_text(
                "❌ Nenhum grupo de destino cadastrado.\n"
                "Use a opção 'Cadastrar grupo de destino' primeiro."
            )
            return
        
        message = update.message
        
        # Copy the message to destination group preserving all content
        try:
            if message.photo:
                # Photo with caption
                await context.bot.send_photo(
                    chat_id=destination_group,
                    photo=message.photo[-1].file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    reply_markup=message.reply_markup
                )
            elif message.video:
                # Video with caption  
                await context.bot.send_video(
                    chat_id=destination_group,
                    video=message.video.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    reply_markup=message.reply_markup
                )
            elif message.document:
                # Document
                await context.bot.send_document(
                    chat_id=destination_group,
                    document=message.document.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    reply_markup=message.reply_markup
                )
            elif message.audio:
                # Audio
                await context.bot.send_audio(
                    chat_id=destination_group,
                    audio=message.audio.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    reply_markup=message.reply_markup
                )
            elif message.voice:
                # Voice message
                await context.bot.send_voice(
                    chat_id=destination_group,
                    voice=message.voice.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    reply_markup=message.reply_markup
                )
            elif message.video_note:
                # Video note (circle video)
                await context.bot.send_video_note(
                    chat_id=destination_group,
                    video_note=message.video_note.file_id,
                    reply_markup=message.reply_markup
                )
            elif message.sticker:
                # Sticker
                await context.bot.send_sticker(
                    chat_id=destination_group,
                    sticker=message.sticker.file_id,
                    reply_markup=message.reply_markup
                )
            elif message.animation:
                # GIF/Animation
                await context.bot.send_animation(
                    chat_id=destination_group,
                    animation=message.animation.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    reply_markup=message.reply_markup
                )
            elif message.text:
                # Text message
                await context.bot.send_message(
                    chat_id=destination_group,
                    text=message.text,
                    entities=message.entities,
                    reply_markup=message.reply_markup
                )
            else:
                # Fallback for other message types
                await context.bot.copy_message(
                    chat_id=destination_group,
                    from_chat_id=message.chat_id,
                    message_id=message.message_id
                )
            
            # Confirm to user with return to menu option
            keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "✅ Mensagem repassada com sucesso!",
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error sending message to destination: {e}")
            await update.message.reply_text(
                "❌ Erro ao repassar mensagem.\n"
                "Verifique se o bot ainda tem acesso ao grupo de destino."
            )
            
    except Exception as e:
        logger.error(f"Error in processar_repassar_mensagem: {e}")
        await update.message.reply_text("Erro ao processar mensagem.")
