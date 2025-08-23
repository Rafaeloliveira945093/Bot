from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import GROUP_CHAT_ID, MENU_ENVIO, RECEBER_MIDIA, RECEBER_TEXTO, RECEBER_BOTOES, EDITAR_ESCOLHA, FORWARD_COLLECT, SELECIONAR_GRUPO, MENU_EDICAO, ADICIONAR_TEXTO, ADICIONAR_BOTAO_TITULO, REMOVER_PALAVRA, CONFIRMAR_EDICAO
from utils.storage import get_destination_group, set_destination_group, get_destination_groups
import logging

logger = logging.getLogger(__name__)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu button clicks."""
    query = update.callback_query
    
    # Always answer callback, ignore if expired
    try:
        await query.answer()
    except Exception:
        # Ignore expired callbacks, continue processing
        pass
    
    try:
        if query.data == "opcao1":
            from handlers.message_handlers import mostrar_menu_gerenciar_grupos
            return await mostrar_menu_gerenciar_grupos(update, context)
        elif query.data == "opcao2":
            await query.edit_message_text("Você selecionou: Lista de cursos")
            return ConversationHandler.END
        elif query.data == "opcao3":
            await query.edit_message_text("Você selecionou: Grupo VIP")
            return ConversationHandler.END
        elif query.data == "opcao4":
            # Check if there are groups registered
            grupos = context.user_data.get("grupos", [])
            if not grupos:
                keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ Nenhum grupo cadastrado.\n\n"
                    "Use a opção 'Gerenciar grupos' primeiro.",
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
            
            # Show destination selection first
            from handlers.message_handlers import mostrar_selecao_destinos
            return await mostrar_selecao_destinos(update, context, "envio")
        elif query.data == "opcao5":
            # Check if there are groups registered
            grupos = context.user_data.get("grupos", [])
            if not grupos:
                keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "❌ Nenhum grupo cadastrado.\n\n"
                    "Use a opção 'Gerenciar grupos' primeiro.",
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
            
            # Show destination selection first
            from handlers.message_handlers import mostrar_selecao_destinos
            return await mostrar_selecao_destinos(update, context, "repassar")
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        await query.edit_message_text("Erro ao processar seleção. Tente novamente.")
    
    return ConversationHandler.END

async def menu_envio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle message creation menu selections."""
    query = update.callback_query
    
    # Always answer callback, ignore if expired
    try:
        await query.answer()
    except Exception:
        # Ignore expired callbacks, continue processing
        pass
    
    # Always answer callback immediately
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback: {e}")
        try:
            await query.message.reply_text("⚠️ Essa ação expirou. Abra o menu novamente enviando qualquer mensagem.")
            return ConversationHandler.END
        except Exception:
            return ConversationHandler.END
    
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
    
    # Always answer callback, ignore if expired
    try:
        await query.answer()
    except Exception:
        # Ignore expired callbacks, continue processing
        pass
    
    try:
        if query.data == "sim":
            # Send message to selected destination group
            selected_destination = context.user_data.get("selected_destination")
            if not selected_destination:
                await query.edit_message_text("❌ Erro: nenhum destino selecionado.")
                return ConversationHandler.END
            
            midia = context.user_data.get("midia")
            texto = context.user_data.get("texto", "")
            botoes = context.user_data.get("botoes", [])
            
            reply_markup = None
            if botoes:
                reply_markup = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(nome, url=link)] for nome, link in botoes]
                )
            
            destination_chat_id = selected_destination["chat_id"]
            
            if midia:
                tipo, file_id = midia
                if tipo == "photo":
                    await context.bot.send_photo(
                        chat_id=destination_chat_id,
                        photo=file_id,
                        caption=texto,
                        reply_markup=reply_markup
                    )
                elif tipo == "video":
                    await context.bot.send_video(
                        chat_id=destination_chat_id,
                        video=file_id,
                        caption=texto,
                        reply_markup=reply_markup
                    )
            else:
                await context.bot.send_message(
                    chat_id=destination_chat_id,
                    text=texto,
                    reply_markup=reply_markup
                )
            
            # Show success message with return to menu option
            keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ Mensagem enviada para {selected_destination['name']} com sucesso!",
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
    
    # Always answer callback immediately
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Failed to answer callback: {e}")
        try:
            await query.message.reply_text("⚠️ Essa ação expirou. Abra o menu novamente enviando qualquer mensagem.")
            return ConversationHandler.END
        except Exception:
            return ConversationHandler.END
    
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
        if query.data == "finalizar_coleta":
            # User wants to finish collecting and start editing
            user_id = update.effective_user.id
            messages = context.bot_data.get('mensagens_temp', {}).get(user_id, [])
            
            if not messages:
                await query.edit_message_text("❌ Nenhuma mensagem encontrada.")
                return ConversationHandler.END
            
            # Initialize editing data for all messages
            context.user_data["messages_to_edit"] = messages
            context.user_data["edited_data"] = []
            context.user_data["added_buttons"] = []
            
            # Extract text/caption with entities from each message
            for msg_data in messages:
                edited_item = {
                    'text': msg_data['text'],
                    'caption': msg_data['caption'],
                    'entities': msg_data['entities'][:] if msg_data['entities'] else [],
                    'caption_entities': msg_data['caption_entities'][:] if msg_data['caption_entities'] else [],
                    'file_id': msg_data['file_id'],
                    'media_type': msg_data['media_type']
                }
                context.user_data["edited_data"].append(edited_item)
            
            # Show bulk editing menu
            keyboard = [
                [InlineKeyboardButton("✏️ Adicionar texto a todas", callback_data="adicionar_texto_bulk")],
                [InlineKeyboardButton("🔗 Adicionar botão a todas", callback_data="adicionar_botao_bulk")],
                [InlineKeyboardButton("🗑️ Remover palavra de todas", callback_data="remover_palavra_bulk")],
                [InlineKeyboardButton("👁️ Ver prévia de todas", callback_data="previa_bulk")],
                [InlineKeyboardButton("📤 Enviar todas sem editar", callback_data="enviar_bulk")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            total = len(messages)
            await query.edit_message_text(
                f"📝 **Menu de Edição em Lote**\n\n"
                f"Total de mensagens: {total}\n\n"
                "Escolha como deseja editar todas as mensagens:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return MENU_EDICAO
            
        elif query.data == "continuar_coleta":
            # User wants to continue collecting messages
            await query.edit_message_text("📥 Continue enviando mensagens...")
            return FORWARD_COLLECT
            
        elif query.data == "add_msgs":
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
        
        # Group management callbacks
        elif query.data == "cadastrar_grupo":
            from handlers.message_handlers import cadastrar_novo_grupo
            return await cadastrar_novo_grupo(update, context)
        
        elif query.data == "ver_grupos":
            from handlers.message_handlers import mostrar_grupos_cadastrados
            return await mostrar_grupos_cadastrados(update, context)
        
        elif query.data == "gerenciar_grupos":
            from handlers.message_handlers import mostrar_menu_gerenciar_grupos
            return await mostrar_menu_gerenciar_grupos(update, context)
        
        elif query.data.startswith("confirmar_cadastro_"):
            chat_id = query.data.replace("confirmar_cadastro_", "")
            pending_group = context.user_data.get("pending_group", {})
            
            if pending_group:
                # Add group to user's list
                if "grupos" not in context.user_data:
                    context.user_data["grupos"] = []
                
                context.user_data["grupos"].append({
                    "name": pending_group["name"],
                    "chat_id": pending_group["chat_id"],
                    "input": pending_group["input"]
                })
                
                keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ **Grupo cadastrado com sucesso!**\n\n"
                    f"**Nome:** {pending_group['name']}\n"
                    f"**ID:** {pending_group['chat_id']}\n\n"
                    "Agora você pode usar as opções de envio de mensagem!",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                
                # Clear pending data
                context.user_data.pop("pending_group", None)
                return ConversationHandler.END
            else:
                await query.edit_message_text("❌ Erro: dados do grupo não encontrados.")
                return ConversationHandler.END
        
        elif query.data.startswith("remover_grupo_"):
            group_index = int(query.data.replace("remover_grupo_", ""))
            grupos = context.user_data.get("grupos", [])
            
            if 0 <= group_index < len(grupos):
                removed_group = grupos.pop(group_index)
                
                keyboard = [
                    [InlineKeyboardButton("🔙 Voltar aos grupos", callback_data="ver_grupos")],
                    [InlineKeyboardButton("🏠 Menu Principal", callback_data="voltar_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"🗑️ **Grupo removido**\n\n"
                    f"O grupo '{removed_group['name']}' foi removido da lista.",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("❌ Erro ao remover grupo.")
            return SELECIONAR_GRUPO
        
        elif query.data.startswith("destino_"):
            # Handle destination selection for sending messages
            parts = query.data.split("_")
            if len(parts) >= 3:
                action_type = parts[1]  # "envio" or "repassar"
                group_index = int(parts[2])
                
                grupos = context.user_data.get("grupos", [])
                if 0 <= group_index < len(grupos):
                    selected_group = grupos[group_index]
                    context.user_data["selected_destination"] = selected_group
                    
                    if action_type == "envio":
                        # Start message creation flow
                        await query.edit_message_text("Envie a mídia (foto ou vídeo) que deseja postar:")
                        return RECEBER_MIDIA
                    elif action_type == "repassar":
                        # Start message forwarding flow
                        await query.edit_message_text(
                            f"🎯 **Destino selecionado:** {selected_group['name']}\n\n"
                            "📥 **Agora envie as mensagens** que deseja repassar:\n\n"
                            "• Envie quantas mensagens quiser\n"
                            "• Quando terminar, clique em 'Finalizar e editar'"
                        )
                        
                        # Initialize message collection
                        user_id = update.effective_user.id
                        if 'mensagens_temp' not in context.bot_data:
                            context.bot_data['mensagens_temp'] = {}
                        context.bot_data['mensagens_temp'][user_id] = []
                        
                        return RECEBER_ENCAMINHADAS
                else:
                    await query.edit_message_text("❌ Grupo selecionado inválido.")
                    return ConversationHandler.END
            
        elif query.data == "cancelar_cadastro":
            context.user_data.pop("pending_group", None)
            from handlers.message_handlers import mostrar_menu_gerenciar_grupos
            return await mostrar_menu_gerenciar_grupos(update, context)
            
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
    """Handle bulk editing menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "adicionar_texto_bulk":
            await query.edit_message_text("✏️ Digite o texto que deseja adicionar ao final de todas as mensagens:")
            return ADICIONAR_TEXTO
            
        elif query.data == "adicionar_botao_bulk":
            await query.edit_message_text("🔗 Digite o título do botão que será adicionado a todas as mensagens:")
            return ADICIONAR_BOTAO_TITULO
            
        elif query.data == "remover_palavra_bulk":
            await query.edit_message_text("🗑️ Digite a palavra que deseja remover de todas as mensagens:")
            return REMOVER_PALAVRA
            
        elif query.data == "previa_bulk":
            return await mostrar_previa_completa_bulk(update, context)
            
        elif query.data == "enviar_bulk":
            return await enviar_mensagens_bulk(update, context)
            
        elif query.data == "confirmar_envio_bulk":
            return await enviar_mensagens_bulk(update, context)
            
        elif query.data == "voltar_edicao":
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
            await query.edit_message_text(
                f"📝 **Menu de Edição em Lote**\n\n"
                f"Total de mensagens: {total}\n\n"
                "Escolha como deseja editar todas as mensagens:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return MENU_EDICAO
            
    except Exception as e:
        logger.error(f"Error in menu_edicao_handler: {e}")
        await query.edit_message_text("Erro ao processar edição. Tente novamente.")
    
    return MENU_EDICAO

async def mostrar_previa_completa_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show complete preview of all edited messages by actually sending them as previews."""
    try:
        query = update.callback_query
        messages = context.user_data.get("messages_to_edit", [])
        edited_data = context.user_data.get("edited_data", [])
        added_buttons = context.user_data.get("added_buttons", [])
        
        if not messages:
            await query.edit_message_text("❌ Nenhuma mensagem encontrada.")
            return ConversationHandler.END
        
        # Prepare inline keyboard for buttons
        reply_markup = None
        if added_buttons:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn["title"], url=btn["url"])] for btn in added_buttons
            ])
        
        await query.edit_message_text("👁️ **Prévia das mensagens como ficarão no grupo:**")
        
        # Send each message as preview
        for i, (msg_data, edited_item) in enumerate(zip(messages, edited_data)):
            try:
                preview_label = f"📋 Prévia {i+1}:"
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=preview_label
                )
                
                # Send message based on type with preserved formatting
                if edited_item['media_type'] == 'photo':
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'video':
                    await context.bot.send_video(
                        chat_id=update.effective_chat.id,
                        video=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'document':
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'audio':
                    await context.bot.send_audio(
                        chat_id=update.effective_chat.id,
                        audio=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'voice':
                    await context.bot.send_voice(
                        chat_id=update.effective_chat.id,
                        voice=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'sticker':
                    await context.bot.send_sticker(
                        chat_id=update.effective_chat.id,
                        sticker=edited_item['file_id']
                    )
                    # Send caption separately if needed
                    if edited_item['caption']:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=edited_item['caption'],
                            entities=edited_item['caption_entities'],
                            reply_markup=reply_markup,
                            parse_mode=None
                        )
                else:
                    # Text message
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=edited_item['text'],
                        entities=edited_item['entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                
            except Exception as e:
                logger.error(f"Error showing preview for message {i+1}: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ Erro na prévia da mensagem {i+1}"
                )
        
        # Show confirmation buttons
        keyboard = [
            [InlineKeyboardButton("✅ Confirmar e enviar todas", callback_data="confirmar_envio_bulk")],
            [InlineKeyboardButton("🔙 Voltar ao menu de edição", callback_data="voltar_edicao")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="👆 **Prévias acima mostram como as mensagens ficarão no grupo**\n\nConfirmar envio?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return CONFIRMAR_EDICAO
        
    except Exception as e:
        logger.error(f"Error showing bulk preview: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Erro ao mostrar prévia."
        )
        return MENU_EDICAO

async def enviar_mensagens_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send all collected and edited messages to the destination group."""
    try:
        query = update.callback_query
        user_id = update.effective_user.id
        messages = context.user_data.get("messages_to_edit", [])
        edited_texts = context.user_data.get("edited_texts", [])
        added_buttons = context.user_data.get("added_buttons", [])
        
        if not messages:
            await query.edit_message_text("❌ Nenhuma mensagem encontrada.")
            return ConversationHandler.END
        
        # Get selected destination from new group system
        selected_destination = context.user_data.get("selected_destination")
        if not selected_destination:
            await query.edit_message_text("❌ Nenhum grupo de destino selecionado.")
            return ConversationHandler.END
        
        # Prepare inline keyboard for buttons
        reply_markup = None
        if added_buttons:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(btn["title"], url=btn["url"])] for btn in added_buttons
            ])
        
        sent_count = 0
        edited_data = context.user_data.get("edited_data", [])
        destination_chat_id = selected_destination["chat_id"]
        
        for i, (msg_data, edited_item) in enumerate(zip(messages, edited_data)):
            try:
                # Send message based on type with preserved formatting
                if edited_item['media_type'] == 'photo':
                    await context.bot.send_photo(
                        chat_id=destination_chat_id,
                        photo=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'video':
                    await context.bot.send_video(
                        chat_id=destination_chat_id,
                        video=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'document':
                    await context.bot.send_document(
                        chat_id=destination_chat_id,
                        document=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'audio':
                    await context.bot.send_audio(
                        chat_id=destination_chat_id,
                        audio=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'voice':
                    await context.bot.send_voice(
                        chat_id=destination_chat_id,
                        voice=edited_item['file_id'],
                        caption=edited_item['caption'],
                        caption_entities=edited_item['caption_entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                elif edited_item['media_type'] == 'sticker':
                    await context.bot.send_sticker(
                        chat_id=destination_chat_id,
                        sticker=edited_item['file_id']
                    )
                    # Send caption separately if needed
                    if edited_item['caption']:
                        await context.bot.send_message(
                            chat_id=destination_chat_id,
                            text=edited_item['caption'],
                            entities=edited_item['caption_entities'],
                            reply_markup=reply_markup,
                            parse_mode=None
                        )
                else:
                    # Text message
                    await context.bot.send_message(
                        chat_id=destination_chat_id,
                        text=edited_item['text'],
                        entities=edited_item['entities'],
                        reply_markup=reply_markup,
                        parse_mode=None
                    )
                
                    sent_count += 1
                
                except Exception as e:
                    logger.error(f"Error sending message {i+1}: {e}")
                    continue
        
        # Clear temporary storage
        if user_id in context.bot_data.get('mensagens_temp', {}):
            del context.bot_data['mensagens_temp'][user_id]
        
        # Clear user data
        context.user_data.clear()
        
        # Show success message
        keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ **Envio concluído!**\n\n"
            f"Mensagens enviadas: {sent_count}/{len(messages)}\n"
            f"Grupo de destino: {selected_destination['name']}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error sending bulk messages: {e}")
        await update.callback_query.edit_message_text("❌ Erro ao enviar mensagens.")
        return ConversationHandler.END

async def encaminhamento_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callback queries for group management and destination selection."""
    query = update.callback_query
    
    # Always answer callback, ignore if expired
    try:
        await query.answer()
    except Exception:
        # Ignore expired callbacks, continue processing
        pass
    
    try:
        if query.data == "voltar_menu":
            from handlers.message_handlers import start
            await start(update, context)
            return ConversationHandler.END
            
        elif query.data == "cadastrar_grupo":
            from handlers.message_handlers import cadastrar_novo_grupo
            return await cadastrar_novo_grupo(update, context)
            
        elif query.data == "ver_grupos":
            from handlers.message_handlers import mostrar_grupos_cadastrados
            return await mostrar_grupos_cadastrados(update, context)
            
        elif query.data == "gerenciar_grupos":
            from handlers.message_handlers import mostrar_menu_gerenciar_grupos
            return await mostrar_menu_gerenciar_grupos(update, context)
            
        elif query.data.startswith("confirmar_cadastro_"):
            # Extract chat_id from callback data
            chat_id = query.data.replace("confirmar_cadastro_", "")
            try:
                chat_id = int(chat_id) if chat_id.startswith("-") else chat_id
            except ValueError:
                pass  # Keep as string for channel usernames
            
            # Initialize grupos if not exists
            if "grupos" not in context.user_data:
                context.user_data["grupos"] = []
            
            # Get pending group data
            pending_group = context.user_data.get("pending_group")
            if not pending_group:
                await query.edit_message_text("❌ Dados do grupo não encontrados. Tente novamente.")
                return ConversationHandler.END
            
            # Check for duplicates
            grupos_existentes = context.user_data["grupos"]
            for grupo in grupos_existentes:
                if str(grupo["chat_id"]) == str(chat_id):
                    await query.edit_message_text(
                        f"❌ **Grupo já cadastrado**\n\n"
                        f"O grupo `{chat_id}` já está na sua lista como '{grupo['name']}'.",
                        parse_mode="Markdown"
                    )
                    # Show main menu automatically
                    from handlers.message_handlers import start
                    await start(update, context)
                    return ConversationHandler.END
            
            # Add group to user's list
            context.user_data["grupos"].append({
                "chat_id": chat_id,
                "name": pending_group["name"]
            })
            
            # Clear pending data
            if "pending_group" in context.user_data:
                del context.user_data["pending_group"]
            
            # Show success message
            await query.edit_message_text(
                f"✅ **Grupo adicionado com sucesso!**\n\n"
                f"**Nome:** {pending_group['name']}\n"
                f"**ID:** `{chat_id}`\n\n"
                f"Total de grupos: {len(context.user_data['grupos'])}",
                parse_mode="Markdown"
            )
            
            # Automatically show main menu after success
            from handlers.message_handlers import start
            await start(update, context)
            
            return ConversationHandler.END
            
        elif query.data.startswith("destino_"):
            # Handle destination selection for message sending
            parts = query.data.split("_")
            action_type = parts[1]  # "envio" or "repassar"
            grupo_index = int(parts[2])
            
            grupos = context.user_data.get("grupos", [])
            if grupo_index >= len(grupos):
                await query.edit_message_text("❌ Grupo não encontrado.")
                return ConversationHandler.END
            
            selected_group = grupos[grupo_index]
            context.user_data["selected_destination"] = selected_group
            
            # Proceed based on action type
            if action_type == "envio":
                # Show message creation menu
                keyboard = [
                    [InlineKeyboardButton("📷 Mídia", callback_data="midia")],
                    [InlineKeyboardButton("📝 Texto", callback_data="texto")],
                    [InlineKeyboardButton("🔗 Botões", callback_data="botoes")],
                    [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ **Destino selecionado:** {selected_group['name']}\n\n"
                    "Escolha o tipo de conteúdo para enviar:",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                return MENU_ENVIO
                
            elif action_type == "repassar":
                # Start collecting messages for forwarding
                await query.edit_message_text(
                    f"✅ **Destino selecionado:** {selected_group['name']}\n\n"
                    "📨 Agora envie as mensagens que deseja repassar.\n\n"
                    "Use /finalizar quando terminar de enviar todas as mensagens.",
                    parse_mode="Markdown"
                )
                return RECEBER_ENCAMINHADAS
                
        elif query.data.startswith("remover_grupo_"):
            # Handle group removal
            grupo_index = int(query.data.replace("remover_grupo_", ""))
            grupos = context.user_data.get("grupos", [])
            
            if grupo_index >= len(grupos):
                await query.edit_message_text("❌ Grupo não encontrado.")
                return ConversationHandler.END
            
            grupo_removido = grupos.pop(grupo_index)
            
            keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ **Grupo removido**\n\n"
                f"**Nome:** {grupo_removido['name']}\n"
                f"**ID:** `{grupo_removido['chat_id']}`\n\n"
                f"Grupos restantes: {len(grupos)}",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error in encaminhamento_callback_handler: {e}")
        await query.edit_message_text("❌ Erro ao processar ação. Tente novamente.")
        return ConversationHandler.END

async def global_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries outside of conversations (for menu navigation)."""
    query = update.callback_query
    
    # Always answer callback, ignore if expired
    try:
        await query.answer()
    except Exception:
        # Ignore expired callbacks, continue processing action
        pass
    
    try:
        # Handle main menu options
        if query.data == "opcao1":
            from handlers.message_handlers import mostrar_menu_gerenciar_grupos
            await mostrar_menu_gerenciar_grupos(update, context)
        elif query.data == "opcao2":
            await query.edit_message_text("Você selecionou: Lista de cursos")
        elif query.data == "opcao3":
            await query.edit_message_text("Você selecionou: Grupo VIP")
        elif query.data == "opcao4":
            # Check if there are groups registered
            grupos = context.user_data.get("grupos", [])
            if not grupos:
                keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ Nenhum grupo cadastrado.\n\n"
                    "Use a opção 'Gerenciar grupos' primeiro.",
                    reply_markup=reply_markup
                )
            else:
                from handlers.message_handlers import mostrar_selecao_destinos
                await mostrar_selecao_destinos(update, context, "envio")
        elif query.data == "opcao5":
            # Check if there are groups registered
            grupos = context.user_data.get("grupos", [])
            if not grupos:
                keyboard = [[InlineKeyboardButton("🏠 Voltar ao Menu Principal", callback_data="voltar_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ Nenhum grupo cadastrado.\n\n"
                    "Use a opção 'Gerenciar grupos' primeiro.",
                    reply_markup=reply_markup
                )
            else:
                from handlers.message_handlers import mostrar_selecao_destinos
                await mostrar_selecao_destinos(update, context, "repassar")
        elif query.data == "voltar_menu":
            from handlers.message_handlers import start
            await start(update, context)
    except Exception as e:
        logger.error(f"Error in global_callback_handler: {e}")
        await query.edit_message_text("Erro ao processar seleção. Tente novamente.")

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any message outside of conversations - only in private chats."""
    try:
        # Only respond in private chats
        if update.message.chat.type != "private":
            return
            
        # Show main menu
        from handlers.message_handlers import start
        await start(update, context)
    except Exception as e:
        logger.error(f"Error in handle_any_message: {e}")