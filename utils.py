# utils.py
from datetime import datetime
from html import escape

def escape_html(text: str) -> str:
    """Escape HTML special characters in text"""
    return escape(text) if text else ""

def format_datetime(dt_str: str) -> str:
    """Format database datetime string to readable format"""
    if not dt_str:
        return "Неизвестно"
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return dt_str