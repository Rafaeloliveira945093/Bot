from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)

GROUP_CHAT_ID = -1002869921534  

MENU_ENVIO, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, CONFIRMAR_PREVIA, EDITAR_ESCOLHA, MENU_REPASSAR, RECEBER_ENCAMINHADAS, RECEBER_LINK, CONFIRMAR_REPASSAR, EDITAR_REPASSAR = range(11)
FORWARD_COLLECT, RECEBER_LINK, CONFIRMAR_REPASSAR, EDITAR_REPASSAR = 100, 101, 102, 103

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("1 – Grupos e canais", callback_data="opcao1")],
        [InlineKeyboardButton("2 – Lista de cursos", callback_data="opcao2")],
        [InlineKeyboardButton("3 – Grupo VIP", callback_data="opcao3")],
        [InlineKeyboardButton("4 – Enviar mensagem", callback_data="opcao4")],
        [InlineKeyboardButton("5 – Repassar mensagens encaminhadas", callback_data="opcao5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Envia boas-vindas sempre que receber qualquer mensagem
    await update.message.reply_text("Escolha uma opção:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "opcao1":
        await query.edit_message_text("Você selecionou: Grupos e canais")
    elif query.data == "opcao2":
        await query.edit_message_text("Você selecionou: Lista de cursos")
    elif query.data == "opcao3":
        await query.edit_message_text("Você selecionou: Grupo VIP")
    elif query.data == "opcao4":
        keyboard = [
            [InlineKeyboardButton("MÍDIA", callback_data="midia")],
            [InlineKeyboardButton("TEXTO", callback_data="texto")],
            [InlineKeyboardButton("BOTÕES", callback_data="botoes")],
            [InlineKeyboardButton("INICIAR", callback_data="iniciar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Escolha o tipo de conteúdo ou clique em INICIAR para começar:", reply_markup=reply_markup)
        return MENU_ENVIO
    elif query.data == "opcao5":
        context.user_data["encaminhadas"] = []
        context.user_data["menu_msg_id"] = None
        await query.edit_message_text("Encaminhe uma ou mais mensagens para este chat.")
        await mostrar_menu_encaminhamento(update, context)
        return RECEBER_ENCAMINHADAS
    return ConversationHandler.END

async def menu_envio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
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

async def receber_midia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        context.user_data["midia"] = ("photo", file_id)
    elif update.message.video:
        file_id = update.message.video.file_id
        context.user_data["midia"] = ("video", file_id)
    else:
        await update.message.reply_text("Por favor, envie uma foto ou vídeo.")
        return RECEBER_MIDIA
    await update.message.reply_text("Agora envie o texto da mensagem:")
    return RECEBER_TEXTO

async def receber_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["texto"] = update.message.text
    await update.message.reply_text(
        "Agora envie os botões no formato:\n\nNOME1|LINK1, NOME2|LINK2\n\nExemplo:\nVIP|https://t.me/grupovip, Cursos|https://t.me/cursos"
    )
    return RECEBER_BOTOES

async def receber_botoes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text
    botoes = []
    partes = [b.strip() for b in texto.split(",") if b.strip()]
    erro = False
    for parte in partes:
        if "|" in parte:
            nome, link = parte.split("|", 1)
            nome = nome.strip()
            link = link.strip()
            if nome and link:
                botoes.append((nome, link))
            else:
                erro = True
        else:
            erro = True
    if erro or not botoes:
        await update.message.reply_text(
            "Formato inválido. Envie os botões como: NOME|LINK, NOME2|LINK2"
        )
        return RECEBER_BOTOES
    context.user_data["botoes"] = botoes
    await mostrar_previa(update, context)
    return CONFIRMAR_PREVIA

async def mostrar_previa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    midia = context.user_data.get("midia")
    texto = context.user_data.get("texto", "")
    botoes = context.user_data.get("botoes", [])
    reply_markup = None
    if botoes:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(nome, url=link)] for nome, link in botoes]
        )
    # Envia a prévia exatamente como será publicada no grupo
    if midia:
        tipo, file_id = midia
        if tipo == "photo":
            await update.message.reply_photo(photo=file_id, caption=texto, reply_markup=reply_markup)
        elif tipo == "video":
            await update.message.reply_video(video=file_id, caption=texto, reply_markup=reply_markup)
    else:
        await update.message.reply_text(texto, reply_markup=reply_markup)
    # Logo abaixo, exibe o menu de confirmação/edição
    keyboard = [
        [InlineKeyboardButton("Confirmar", callback_data="sim")],
        [InlineKeyboardButton("Editar", callback_data="editar")]
    ]
    reply_markup_confirm = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Está correto?", reply_markup=reply_markup_confirm)

async def confirmar_previa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "sim":
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
                await context.bot.send_photo(chat_id=GROUP_CHAT_ID, photo=file_id, caption=texto, reply_markup=reply_markup)
            elif tipo == "video":
                await context.bot.send_video(chat_id=GROUP_CHAT_ID, video=file_id, caption=texto, reply_markup=reply_markup)
        else:
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=texto, reply_markup=reply_markup)
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

async def editar_escolha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
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

async def mostrar_menu_encaminhamento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Adicionar mais mensagens", callback_data="add_msgs")],
        [InlineKeyboardButton("Finalizar", callback_data="finalizar_encaminhamento")],
        [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Envia ou atualiza o menu fixo
    if context.user_data.get("menu_msg_id"):
        try:
            await update.effective_chat.edit_message_reply_markup(
                message_id=context.user_data["menu_msg_id"],
                reply_markup=reply_markup
            )
        except Exception:
            pass
    else:
        msg = await update.effective_chat.send_message(
            "Quando terminar, clique em Finalizar.\nPara cancelar, clique em Cancelar.",
            reply_markup=reply_markup
        )
        context.user_data["menu_msg_id"] = msg.message_id

# Utilitário para atualizar o menu fixo
async def atualizar_menu_encaminhamento(context, chat_id, menu_msg_id, total):
    keyboard = [
        [InlineKeyboardButton(f"Adicionar mais mensagens", callback_data="add_msgs")],
        [InlineKeyboardButton(f"Finalizar ({total} coletados)", callback_data="finalizar_encaminhamento")],
        [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=menu_msg_id,
            reply_markup=reply_markup
        )
    except Exception:
        pass

# Handler para coletar mensagens encaminhadas:
async def receber_encaminhadas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    # Inicializa lista de itens e grupos
    context.user_data.setdefault("forwarded_items", [])
    context.user_data.setdefault("media_groups", {})
    # Media group (álbum)
    if msg.media_group_id:
        group_id = msg.media_group_id
        context.user_data["media_groups"].setdefault(group_id, []).append(msg)
        # Aguarda mais itens do grupo (Telegram envia em sequência)
        # Só registra quando não vier mais do mesmo grupo (tratado no menu)
    else:
        # Conteúdo protegido
        if getattr(msg, "is_protected_content", False):
            await msg.reply_text("Conteúdo protegido contra cópia. Encaminhe outro item.")
            return FORWARD_COLLECT
        context.user_data["forwarded_items"].append(msg)
    # Atualiza menu fixo
    total = len(context.user_data["forwarded_items"]) + sum(len(g) for g in context.user_data["media_groups"].values())
    if not context.user_data.get("menu_msg_id"):
        menu = await msg.reply_text(
            f"Encaminhe mensagens. Quando terminar, clique em Finalizar.\nItens coletados: {total}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Adicionar mais mensagens", callback_data="add_msgs")],
                [InlineKeyboardButton(f"Finalizar ({total} coletados)", callback_data="finalizar_encaminhamento")],
                [InlineKeyboardButton("Cancelar", callback_data="cancelar_encaminhamento")]
            ])
        )
        context.user_data["menu_msg_id"] = menu.message_id
    else:
        await atualizar_menu_encaminhamento(context, msg.chat_id, context.user_data["menu_msg_id"], total)
    return FORWARD_COLLECT

async def comando_pronto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.user_data.get("encaminhadas"):
        await update.message.reply_text("Você não encaminhou nenhuma mensagem. Encaminhe ao menos uma antes de digitar /pronto.")
        return RECEBER_ENCAMINHADAS
    await update.message.reply_text("Agora envie o link de destino (grupo, canal ou chat):")
    return RECEBER_LINK  # <-- AVANÇA PARA O PRÓXIMO ESTADO

# Handler para coletar o link de destino:
async def receber_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    link = update.message.text.strip()
    # Validação simples: t.me/username ou chat_id
    if link.startswith("t.me/"):
        await update.message.reply_text("Por favor, peça para o destino enviar uma mensagem para o bot ou informe o @username ou chat_id.")
        return RECEBER_LINK
    context.user_data["destino"] = link
    await mostrar_previa_repassar(update, context)
    return CONFIRMAR_REPASSAR

# Função para mostrar a prévia das mensagens encaminhadas:
async def mostrar_previa_repassar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = context.user_data.get("forwarded_items", [])
    destino = context.user_data.get("destino", "")
    preview = f"Prévia do repasse para: {destino}\n\n"
    for idx, item in enumerate(items, 1):
        if isinstance(item, list):  # Media group
            preview += f"{idx}. [Álbum com {len(item)} mídias]\n"
            for m in item:
                if m.photo:
                    preview += "   - Foto\n"
                elif m.video:
                    preview += "   - Vídeo\n"
                elif m.document:
                    preview += "   - Documento\n"
                elif m.audio:
                    preview += "   - Áudio\n"
                elif m.voice:
                    preview += "   - Voz\n"
                elif m.sticker:
                    preview += "   - Sticker\n"
                if m.caption:
                    preview += f"     Legenda: {m.caption}\n"
        else:
            if item.text:
                preview += f"{idx}. Texto: {item.text}\n"
            elif item.photo:
                preview += f"{idx}. Foto\n"
                if item.caption:
                    preview += f"   Legenda: {item.caption}\n"
            elif item.video:
                preview += f"{idx}. Vídeo\n"
                if item.caption:
                    preview += f"   Legenda: {item.caption}\n"
            elif item.document:
                preview += f"{idx}. Documento\n"
                if item.caption:
                    preview += f"   Legenda: {item.caption}\n"
            elif item.audio:
                preview += f"{idx}. Áudio\n"
                if item.caption:
                    preview += f"   Legenda: {item.caption}\n"
            elif item.voice:
                preview += f"{idx}. Voz\n"
            elif item.sticker:
                preview += f"{idx}. Sticker\n"
    await update.message.reply_text(preview)
    keyboard = [
        [InlineKeyboardButton("Confirmar", callback_data="confirmar_repassar")],
        [InlineKeyboardButton("Editar", callback_data="editar_repassar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Está correto?", reply_markup=reply_markup)

# Handler para confirmação ou edição:
async def confirmar_repassar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "confirmar_repassar":
        destino = context.user_data.get("destino")
        items = context.user_data.get("forwarded_items", [])

        if not destino:
            await query.message.reply_text("Destino não definido. Envie novamente o link ou chat_id.")
            return RECEBER_LINK

        enviados = 0  # Contador de itens enviados

        for item in items:
            if isinstance(item, list):  # Media group
                media_objs = []
                for m in item:
                    if getattr(m, "is_protected_content", False):
                        continue  # Ignora mídias protegidas
                    if m.photo:
                        media_objs.append(InputMediaPhoto(media=m.photo[-1].file_id, caption=m.caption or ""))
                    elif m.video:
                        media_objs.append(InputMediaVideo(media=m.video.file_id, caption=m.caption or ""))
                    elif m.document:
                        media_objs.append(InputMediaDocument(media=m.document.file_id, caption=m.caption or ""))
                if media_objs:
                    try:
                        await query.bot.send_media_group(chat_id=destino, media=media_objs)
                        enviados += len(media_objs)
                    except Exception:
                        await query.message.reply_text(
                            "Não foi possível enviar um dos álbuns. Verifique se o destino é válido."
                        )
            else:
                if getattr(item, "is_protected_content", False):
                    continue  # Ignora itens protegidos
                try:
                    await item.copy_to(chat_id=destino)
                    enviados += 1
                except Exception:
                    await query.message.reply_text(
                        "Não foi possível copiar um dos itens. Verifique se o destino é válido."
                    )

        if enviados > 0:
            await query.edit_message_text(f"Mensagens repassadas com sucesso! ({enviados} itens enviados)")
        else:
            await query.edit_message_text("Nenhum item pôde ser repassado. Todos eram protegidos ou o destino é inválido.")

        return ConversationHandler.END

    elif query.data == "editar_repassar":
        keyboard = [
            [InlineKeyboardButton("Alterar link de destino", callback_data="editar_link")],
            [InlineKeyboardButton("Remover todos os itens", callback_data="editar_msgs")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("O que deseja editar?", reply_markup=reply_markup)
        return EDITAR_REPASSAR


# Handler para edição:
async def editar_repassar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "editar_link":
        await query.edit_message_text("Envie o novo link de destino:")
        return RECEBER_LINK
    elif query.data == "editar_msgs":
        context.user_data["forwarded_items"] = []
        await query.edit_message_text("Encaminhe novamente as mensagens para este chat. Clique em Finalizar quando terminar.")
        return FORWARD_COLLECT

async def confirmar_conexao(app):
    bot_info = await app.bot.get_me()
    print(f"Bot [{bot_info.first_name}] conectado com sucesso e online.")

async def menu_encaminhamento_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    total = len(context.user_data.get("forwarded_items", [])) + sum(len(g) for g in context.user_data.get("media_groups", {}).values())
    if query.data == "add_msgs":
        await query.edit_message_reply_markup(reply_markup=query.message.reply_markup)
        await query.message.reply_text("Continue encaminhando mensagens para este chat.")
        return FORWARD_COLLECT
    elif query.data == "finalizar_encaminhamento":
        # Finaliza media groups (adiciona todos como conjuntos)
        for group in context.user_data.get("media_groups", {}).values():
            context.user_data["forwarded_items"].append(group)
        context.user_data["media_groups"] = {}
        if not context.user_data.get("forwarded_items"):
            await query.message.reply_text("Você não encaminhou nenhuma mensagem. Encaminhe ao menos uma antes de finalizar.")
            return FORWARD_COLLECT
        # Remove menu fixo
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        context.user_data["menu_msg_id"] = None
        await query.message.reply_text("Agora envie o link de destino (grupo, canal ou chat):")
        return RECEBER_LINK
    elif query.data == "cancelar_encaminhamento":
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        context.user_data["menu_msg_id"] = None
        context.user_data["forwarded_items"] = []
        context.user_data["media_groups"] = {}
        await query.message.reply_text("Processo cancelado. Voltando ao menu principal.")
        return ConversationHandler.END

def main() -> None:
    token = input("Digite o token do bot do Telegram: ").strip()
    app = ApplicationBuilder().token(token).post_init(confirmar_conexao).build()
    conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^opcao4$|^opcao5$")],
    states={
        # Menu de envio de mídia/texto/botões
        MENU_ENVIO: [
            CallbackQueryHandler(menu_envio_handler, pattern="^(midia|texto|botoes|iniciar)$")
        ],
        RECEBER_MIDIA: [
            MessageHandler(filters.PHOTO | filters.VIDEO, receber_midia)
        ],
        RECEBER_TEXTO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receber_texto)
        ],
        RECEBER_BOTOES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receber_botoes)
        ],
        CONFIRMAR_PREVIA: [
            CallbackQueryHandler(confirmar_previa_handler, pattern="^(sim|editar)$")
        ],
        EDITAR_ESCOLHA: [
            CallbackQueryHandler(editar_escolha_handler, pattern="^editar_(midia|texto|botoes)$")
        ],

        # Menu de encaminhamento de mensagens
        RECEBER_ENCAMINHADAS: [
            MessageHandler(filters.FORWARDED & ~filters.COMMAND, receber_encaminhadas)
        ],
        FORWARD_COLLECT: [
            MessageHandler(filters.FORWARDED & ~filters.COMMAND, receber_encaminhadas),
            CallbackQueryHandler(menu_encaminhamento_handler,
                                 pattern="^(add_msgs|finalizar_encaminhamento|cancelar_encaminhamento)$")
        ],
        RECEBER_LINK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receber_link)
        ],
        CONFIRMAR_REPASSAR: [
            CallbackQueryHandler(confirmar_repassar_handler, pattern="^(confirmar_repassar|editar_repassar)$")
        ],
        EDITAR_REPASSAR: [
            CallbackQueryHandler(editar_repassar_handler, pattern="^(editar_link|editar_msgs)$")
        ]
    },
    fallbacks=[]
)

    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(opcao1|opcao2|opcao3)$"))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.run_polling()

if __name__ == '__main__':
    main()