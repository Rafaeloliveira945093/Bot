from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import GROUP_CHAT_ID, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, CONFIRMAR_PREVIA, RECEBER_ENCAMINHADAS, FORWARD_COLLECT, RECEBER_LINK, CONFIRMAR_REPASSAR, CADASTRAR_GRUPO, SELECIONAR_GRUPO, CONFIRMAR_GRUPO
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
    """Handle forwarded messages collection and immediate forwarding to registered group."""
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
        
        # Initialize counter if not exists
        context.user_data.setdefault("messages_sent", 0)
        
        # Check for protected content
        if getattr(msg, "has_protected_content", False):
            await msg.reply_text("Conteúdo protegido contra cópia. Encaminhe outro item.")
            return FORWARD_COLLECT
        
        # Forward message immediately to destination group
        try:
            await context.bot.forward_message(
                chat_id=destination_group,
                from_chat_id=msg.chat_id,
                message_id=msg.message_id
            )
            
            context.user_data["messages_sent"] += 1
            
            # Show confirmation and menu
            if not context.user_data.get("menu_msg_id"):
                menu = await msg.reply_text(
                    f"✅ Mensagem enviada! Total: {context.user_data['messages_sent']}\n\n"
                    f"Continue enviando mensagens ou finalize.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Continuar enviando", callback_data="add_msgs")],
                        [InlineKeyboardButton("Finalizar", callback_data="finalizar_encaminhamento")],
                        [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
                    ])
                )
                context.user_data["menu_msg_id"] = menu.message_id
            else:
                # Update existing menu
                await context.bot.edit_message_text(
                    chat_id=msg.chat_id,
                    message_id=context.user_data["menu_msg_id"],
                    text=f"✅ Mensagem enviada! Total: {context.user_data['messages_sent']}\n\n"
                         f"Continue enviando mensagens ou finalize.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Continuar enviando", callback_data="add_msgs")],
                        [InlineKeyboardButton("Finalizar", callback_data="finalizar_encaminhamento")],
                        [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
                    ])
                )
            
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await msg.reply_text(
                "❌ Erro ao enviar mensagem para o grupo.\n"
                "Verifique se o bot ainda tem acesso ao grupo de destino."
            )
        
        return FORWARD_COLLECT
        
    except Exception as e:
        logger.error(f"Error receiving forwarded messages: {e}")
        await update.message.reply_text("Erro ao processar mensagem.")
        return FORWARD_COLLECT

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
                await context.bot.forward_message(
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
