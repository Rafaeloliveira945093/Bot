import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def validate_button_format(text: str) -> Optional[List[Tuple[str, str]]]:
    """
    Validate and parse button format: NOME|LINK, NOME2|LINK2
    Returns list of (name, link) tuples or None if invalid
    """
    try:
        botoes = []
        partes = [b.strip() for b in text.split(",") if b.strip()]
        
        if not partes:
            return None
        
        for parte in partes:
            if "|" not in parte:
                return None
            
            nome, link = parte.split("|", 1)
            nome = nome.strip()
            link = link.strip()
            
            if not nome or not link:
                return None
            
            # Validate URL format
            if not is_valid_url(link):
                return None
            
            botoes.append((nome, link))
        
        return botoes if botoes else None
    
    except Exception as e:
        logger.error(f"Error validating button format: {e}")
        return None

def is_valid_url(url: str) -> bool:
    """Check if URL is valid (basic validation)."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def validate_telegram_link(link: str) -> bool:
    """Validate Telegram link format."""
    try:
        # Accept t.me links
        if link.startswith("t.me/"):
            username = link.split("/")[-1]
            return is_valid_username(username)
        
        # Accept @username format
        if link.startswith("@"):
            username = link[1:]
            return is_valid_username(username)
        
        # Accept numeric chat IDs
        if link.lstrip("-").isdigit():
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error validating Telegram link: {e}")
        return False

def is_valid_username(username: str) -> bool:
    """Check if username follows Telegram username rules."""
    if not username:
        return False
    
    # Telegram username rules: 5-32 characters, alphanumeric + underscore
    # Must start with letter, can't end with underscore
    if len(username) < 5 or len(username) > 32:
        return False
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*[a-zA-Z0-9]$', username):
        return False
    
    return True

def sanitize_text(text: str, max_length: int = 4096) -> str:
    """Sanitize text for Telegram message sending."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text
