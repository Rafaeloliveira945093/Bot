import os
from typing import Optional

# Bot configuration
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Group chat ID for posting messages
GROUP_CHAT_ID: int = -1002869921534

# Conversation states
MENU_ENVIO = 0
RECEBER_MIDIA = 1
RECEBER_TEXTO = 2
RECEBER_BOTOES = 3
CONFIRMAR_PREVIA = 4
EDITAR_ESCOLHA = 5
MENU_REPASSAR = 6
RECEBER_ENCAMINHADAS = 7
RECEBER_LINK = 8
CONFIRMAR_REPASSAR = 9
EDITAR_REPASSAR = 10

FORWARD_COLLECT = 100

# Message limits
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
