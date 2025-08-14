import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Any, List, Dict, Optional
import re
import hashlib
import plotly.colors

def format_currency(amount: float, currency: str = "USD", show_symbol: bool = True) -> str:
    """Format currency with proper symbol and formatting"""
    symbols = {
        "USD": "$",
        "EUR": "€", 
        "GBP": "£",
        "INR": "₹",
        "CAD": "C$",
        "AUD": "A$"
    }
    
    symbol = symbols.get(currency, "$") if show_symbol else ""
    
    if abs(amount) >= 1_000_000:
        return f"{symbol}{amount/1_000_000:.1f}M"
    elif abs(amount) >= 1_000:
        return f"{symbol}{amount/1_000:.1f}K"
    else:
        return f"{symbol}{amount:,.2f}"

def format_date(date_input: Any, format_type: str = "short") -> str:
    """Format date with different format options"""
    if isinstance(date_input, str):
        try:
            date_obj = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
        except:
            return date_input
    elif isinstance(date_input, (datetime, date)):
        date_obj = date_input
    else:
        return str(date_input)
    
    formats = {
        "short": "%m/%d/%Y",
        "long": "%B %d, %Y",
        "iso": "%Y-%m-%d",
        "datetime": "%m/%d/%Y %I:%M %p"
    }
    
    return date_obj.strftime(formats.get(format_type, formats["short"]))

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format percentage with proper symbol"""
    return f"{value:.{decimal_places}f}%"

def get_user_avatar(user_email: str) -> str:
    """Generate user avatar using email hash"""
    # Create a simple avatar using email hash
    hash_value = hashlib.md5(user_email.encode()).hexdigest()
    colors = ["🔵", "🟢", "🟡", "🟠", "🔴", "🟣", "🟤", "⚫"]
    return colors[int(hash_value[0], 16) % len(colors)]

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
def format_persona_display(persona: str) -> str:
    """Format persona display name from identifier"""
    return persona.replace("_", " ").title()

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not isinstance(text, str):
        text = str(text)
    
    # Remove potential harmful characters
    text = re.sub(r'[<>\"\'&]', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()

def generate_colors(n: int) -> List[str]:
    """Generate n distinct colors for charts"""
    if n <= 10:
        return plotly.colors.qualitative.Set3[:n]
    else:
        # Generate additional colors
        base_colors = plotly.colors.qualitative.Set3
        additional_colors = plotly.colors.qualitative.Pastel[:n-len(base_colors)]
        return base_colors + additional_colors

def create_download_link(data: Any, filename: str, file_type: str = "csv") -> str:
    """Create download link for data"""
    if file_type == "csv" and isinstance(data, pd.DataFrame):
        csv_data = data.to_csv(index=False)
        return st.download_button(
            label=f"📥 Download {filename}",
            data=csv_data,
            file_name=filename,
            mime="text/csv"
        )
    elif file_type == "json":
        import json
        json_data = json.dumps(data, indent=2)
        return st.download_button(
            label=f"📥 Download {filename}",
            data=json_data,
            file_name=filename,
            mime="application/json"
        )
    else:
        return st.download_button(
            label=f"📥 Download {filename}",
            data=str(data),
            file_name=filename
        )

def show_loading_spinner(message: str = "Loading..."):
    """Show loading spinner with message"""
    return st.spinner(message)

def display_error_message(message: str, details: Optional[str] = None):
    """Display error message with optional details"""
    st.error(f"❌ {message}")
    if details:
        with st.expander("🔍 Error Details"):
            st.text(details)

def display_success_message(message: str, details: Optional[str] = None):
    """Display success message with optional details"""
    st.success(f"✅ {message}")
    if details:
        st.info(details)

def display_warning_message(message: str, details: Optional[str] = None):
    """Display warning message with optional details"""
    st.warning(f"⚠️ {message}")
    if details:
        st.info(details)

def display_info_message(message: str, details: Optional[str] = None):
    """Display info message with optional details"""
    st.info(f"ℹ️ {message}")
    if details:
        with st.expander("📋 More Information"):
            st.text(details)

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, return default if division by zero"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-len(suffix)] + suffix

def format_large_number(number: float, precision: int = 1) -> str:
    """Format large numbers with appropriate suffixes"""
    if abs(number) >= 1e9:
        return f"{number/1e9:.{precision}f}B"
    elif abs(number) >= 1e6:
        return f"{number/1e6:.{precision}f}M"
    elif abs(number) >= 1e3:
        return f"{number/1e3:.{precision}f}K"
    else:
        return f"{number:.{precision}f}"

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0 if new_value == 0 else float('inf')
    return ((new_value - old_value) / old_value) * 100

def group_list_items(items: List[Any], group_size: int = 3) -> List[List[Any]]:
    """Group list items into chunks of specified size"""
    return [items[i:i + group_size] for i in range(0, len(items), group_size)]

def get_financial_emoji(category: str) -> str:
    """Get appropriate emoji for financial categories"""
    emoji_map = {
        "housing": "🏠",
        "groceries": "🛒", 
        "transport": "🚗",
        "dining": "🍽️",
        "entertainment": "🎬",
        "shopping": "🛍️",
        "healthcare": "🏥",
        "childcare": "👶",
        "subscriptions": "📱",
        "debt": "💳",
        "savings": "💰",
        "investment": "📈",
        "emergency_fund": "🚨",
        "vacation": "✈️",
        "education": "🎓",
        "retirement": "🏖️",
        "miscellaneous": "📦"
    }
    return emoji_map.get(category.lower(), "💼")

def format_duration(months: int) -> str:
    """Format duration in months to human readable format"""
    if months == float('inf'):
        return "Never (payment too low)"
    elif months <= 0:
        return "Immediate"
    elif months == 1:
        return "1 month"
    elif months <= 12:
        return f"{months} months"
    elif months <= 24:
        years = months / 12
        return f"{years:.1f} years"
    else:
        years = months // 12
        remaining_months = months % 12
        if remaining_months == 0:
            return f"{years} years"
        else:
            return f"{years} years, {remaining_months} months"

