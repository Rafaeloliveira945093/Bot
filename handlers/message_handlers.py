from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import GROUP_CHAT_ID, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, CONFIRMAR_PREVIA, RECEBER_ENCAMINHADAS, FORWARD_COLLECT, RECEBER_LINK, CONFIRMAR_REPASSAR
from utils.validators import validate_button_format, validate_telegram_link
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send main menu when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("1 – Grupos e canais", callback_data="opcao1")],
        [InlineKeyboardButton("2 – Lista de cursos", callback_data="opcao2")],
        [InlineKeyboardButton("3 – Grupo VIP", callback_data="opcao3")],
        [InlineKeyboardButton("4 – Enviar mensagem", callback_data="opcao4")],
        [InlineKeyboardButton("5 – Repassar mensagens encaminhadas", callback_data="opcao5")]
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
    """Handle forwarded messages collection."""
    try:
        msg = update.message
        
        # Initialize collections
        context.user_data.setdefault("forwarded_items", [])
        context.user_data.setdefault("media_groups", {})
        
        # Handle media groups (albums)
        if msg.media_group_id:
            group_id = msg.media_group_id
            context.user_data["media_groups"].setdefault(group_id, []).append(msg)
        else:
            # Check for protected content
            if getattr(msg, "has_protected_content", False):
                await msg.reply_text("Conteúdo protegido contra cópia. Encaminhe outro item.")
                return FORWARD_COLLECT
            
            context.user_data["forwarded_items"].append(msg)
        
        # Update menu with current count
        total = len(context.user_data["forwarded_items"]) + sum(
            len(g) for g in context.user_data["media_groups"].values()
        )
        
        if not context.user_data.get("menu_msg_id"):
            menu = await msg.reply_text(
                f"Encaminhe mensagens. Quando terminar, clique em Finalizar.\n"
                f"Itens coletados: {total}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Adicionar mais mensagens", callback_data="add_msgs")],
                    [InlineKeyboardButton(f"Finalizar ({total} coletados)", callback_data="finalizar_encaminhamento")],
                    [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
                ])
            )
            context.user_data["menu_msg_id"] = menu.message_id
        else:
            await atualizar_menu_encaminhamento(
                context, msg.chat_id, context.user_data["menu_msg_id"], total
            )
        
        return FORWARD_COLLECT
    except Exception as e:
        logger.error(f"Error receiving forwarded messages: {e}")
        await update.message.reply_text("Erro ao processar mensagem encaminhada.")
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
