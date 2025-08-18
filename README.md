# Bot Telegram em Python

Bot completo para Telegram com menu interativo, criação de mensagens e reenvio automático.

## 🚀 Configuração Local

### 1. Instalar Dependências
```bash
pip install python-telegram-bot python-dotenv
```

### 2. Configurar Token
**Opção A - Arquivo .env (Recomendado):**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env e adicione seu token
# BOT_TOKEN=1234567890:ABCDEFghijklmnopQRSTUVwxyz
```

**Opção B - Variável de Ambiente:**
```bash
# Linux/Mac
export BOT_TOKEN="seu_token_aqui"

# Windows
set BOT_TOKEN=seu_token_aqui
```

### 3. Executar o Bot
```bash
python main.py
```

## 🔧 Configuração no Replit

1. Vá no painel **Secrets** (ícone do cadeado)
2. Adicione uma nova secret:
   - **Key:** BOT_TOKEN
   - **Value:** seu_token_do_telegram
3. Execute o projeto

## 📱 Funcionalidades

- ✅ Menu interativo com 6 opções
- ✅ Criação de mensagens com texto, mídia e botões
- ✅ Reenvio imediato de mensagens
- ✅ Cadastro de grupos de destino
- ✅ Suporte a todos os tipos de mídia
- ✅ Sistema de navegação intuitivo

## 🔒 Segurança

- Token protegido por variáveis de ambiente
- Arquivo .env ignorado pelo Git
- Configuração flexível para desenvolvimento e produção


