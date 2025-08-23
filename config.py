import os
from typing import Optional

# Try to load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Arquivo .env carregado com sucesso")
except ImportError:
    print("python-dotenv não instalado, usando variáveis de ambiente do sistema")
except Exception as e:
    print(f"Aviso: Não foi possível carregar .env: {e}")

# Bot configuration
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN não encontrado. "
        "Para uso local: crie um arquivo .env com BOT_TOKEN=seu_token "
        "Para Replit: adicione BOT_TOKEN no painel Secrets"
    )

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
CADASTRAR_GRUPO = 11
SELECIONAR_GRUPO = 12
CONFIRMAR_GRUPO = 13
MENU_PRINCIPAL = 14

FORWARD_COLLECT = 100

# New editing states for option 5
MENU_EDICAO = 101
ADICIONAR_TEXTO = 102
ADICIONAR_BOTAO_TITULO = 103
ADICIONAR_BOTAO_LINK = 104
REMOVER_PALAVRA = 105
CONFIRMAR_EDICAO = 106

# Message limits
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024

# Storage for registered destination group
DESTINATION_GROUP_KEY = "destination_group_id"
