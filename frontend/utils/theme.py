import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List, Tuple

def apply_custom_theme():
    """Apply custom CSS theme to Streamlit app"""
    
    # Define color palette
    colors = get_theme_colors()
    
    # Custom CSS styling
    custom_css = f"""
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}
    
    /* Header styling */
    .main-header {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }}
    
    .main-header h1 {{
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        margin: 0;
        font-size: 2.5rem;
    }}
    
    .main-header p {{
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }}
    
    /* Card components */
    .finance-card {{
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }}
    
    .finance-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }}
    
    .metric-card {{
        background: linear-gradient(135deg, {colors['light_bg']}, white);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid {colors['border']};
        transition: all 0.3s ease;
    }}
    
    .metric-card:hover {{
        border-color: {colors['primary']};
        transform: translateY(-1px);
    }}
    
    .metric-value {{
        font-family: 'Inter', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: {colors['primary']};
        margin: 0;
    }}
    
    .metric-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: {colors['text_secondary']};
        font-weight: 500;
        margin-top: 0.5rem;
    }}
    
    /* Chat message styling */
    .chat-message {{
        display: flex;
        margin: 1rem 0;
        animation: fadeInUp 0.5s ease;
    }}
    
    .chat-message.user {{
        justify-content: flex-end;
    }}
    
    .chat-message.assistant {{
        justify-content: flex-start;
    }}
    
    .message-bubble {{
        max-width: 70%;
        padding: 1rem 1.5rem;
        border-radius: 20px;
        font-family: 'Inter', sans-serif;
        line-height: 1.5;
        position: relative;
    }}
    
    .message-bubble.user {{
        background: {colors['primary']};
        color: white;
        border-bottom-right-radius: 5px;
    }}
    
    .message-bubble.assistant {{
        background: {colors['light_bg']};
        color: {colors['text_primary']};
        border: 1px solid {colors['border']};
        border-bottom-left-radius: 5px;
        border-left: 3px solid {colors['accent']};
    }}
    
    .message-avatar {{
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin: 0 0.5rem;
        flex-shrink: 0;
    }}
    
    .avatar-user {{
        background: {colors['primary']};
        color: white;
    }}
    
    .avatar-assistant {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
        color: white;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(46, 139, 87, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(46, 139, 87, 0.4);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    /* Secondary button styling */
    .secondary-button {{
        background: transparent !important;
        color: {colors['primary']} !important;
        border: 2px solid {colors['primary']} !important;
    }}
    
    .secondary-button:hover {{
        background: {colors['primary']} !important;
        color: white !important;
    }}
    
    /* Form styling */
    .stTextInput > div > div > input {{
        border-radius: 10px;
        border: 2px solid {colors['border']};
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {colors['primary']};
        box-shadow: 0 0 0 2px rgba(46, 139, 87, 0.1);
    }}
    
    .stSelectbox > div > div > div {{
        border-radius: 10px;
        border: 2px solid {colors['border']};
        font-family: 'Inter', sans-serif;
    }}
    
    .stNumberInput > div > div > input {{
        border-radius: 10px;
        border: 2px solid {colors['border']};
        font-family: 'Inter', sans-serif;
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {colors['light_bg']};
        padding: 0.5rem;
        border-radius: 15px;
        border: 1px solid {colors['border']};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        padding: 0px 20px;
        background-color: transparent;
        border-radius: 10px;
        color: {colors['text_secondary']};
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {colors['primary']} !important;
        color: white !important;
        box-shadow: 0 2px 10px rgba(46, 139, 87, 0.3);
    }}
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
        border-radius: 5px;
    }}
    
    /* Alert styling */
    .stAlert {{
        border-radius: 12px;
        border: none;
        font-family: 'Inter', sans-serif;
    }}
    
    .stSuccess {{
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        color: #155724;
        border-left: 4px solid #28a745;
    }}
    
    .stError {{
        background: linear-gradient(135deg, #f8d7da, #f1b0b7);
        color: #721c24;
        border-left: 4px solid #dc3545;
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, #fff3cd, #ffeeba);
        color: #856404;
        border-left: 4px solid #ffc107;
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, #d1ecf1, #bee5eb);
        color: #0c5460;
        border-left: 4px solid #17a2b8;
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background: linear-gradient(180deg, {colors['light_bg']}, white);
        border-right: 1px solid {colors['border']};
    }}
    
    /* Metric styling */
    .stMetric {{
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid {colors['border']};
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }}
    
    .stMetric > label {{
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: {colors['text_primary']};
    }}
    
    .stMetric > div {{
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: {colors['primary']};
    }}
    
    /* Expander styling */
    .streamlit-expanderHeader {{
        background: {colors['light_bg']};
        border-radius: 10px;
        border: 1px solid {colors['border']};
        font-family: 'Inter', sans-serif;
        font-weight: 500;
    }}
    
    .streamlit-expanderContent {{
        border-radius: 0 0 10px 10px;
        border: 1px solid {colors['border']};
        border-top: none;
    }}
    
    /* File uploader styling */
    .stFileUploader {{
        border: 2px dashed {colors['border']};
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }}
    
    .stFileUploader:hover {{
        border-color: {colors['primary']};
        background: {colors['light_bg']};
    }}
    
    /* Loading spinner */
    .stSpinner > div {{
        border-color: {colors['primary']} transparent transparent transparent;
    }}
    
    /* Custom animations */
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    @keyframes pulse {{
        0%, 100% {{
            transform: scale(1);
        }}
        50% {{
            transform: scale(1.05);
        }}
    }}
    
    .pulse-animation {{
        animation: pulse 2s infinite;
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        
        .main-header {{
            padding: 1.5rem;
        }}
        
        .main-header h1 {{
            font-size: 2rem;
        }}
        
        .message-bubble {{
            max-width: 85%;
        }}
        
        .finance-card {{
            padding: 1rem;
        }}
    }}
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {{
        .finance-card {{
            background: #1a1a1a;
            border-color: #333;
        }}
        
        .message-bubble.assistant {{
            background: #2a2a2a;
            color: #e0e0e0;
            border-color: #444;
        }}
    }}
    
    /* Accessibility improvements */
    .stButton > button:focus {{
        outline: 2px solid {colors['accent']};
        outline-offset: 2px;
    }}
    
    .stTextInput > div > div > input:focus {{
        outline: none;
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stDeployButton {{visibility: hidden;}}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {colors['light_bg']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {colors['border']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {colors['primary']};
    }}
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)

def get_theme_colors() -> Dict[str, str]:
    """Get theme color palette"""
    return {
        'primary': '#2E8B57',        # Sea Green
        'secondary': '#3CB371',      # Medium Sea Green  
        'accent': '#FFD700',         # Gold
        'success': '#28a745',        # Green
        'warning': '#ffc107',        # Yellow
        'error': '#dc3545',          # Red
        'info': '#17a2b8',           # Teal
        
        # Background colors
        'light_bg': '#F8F9FA',       # Light Gray
        'white': '#FFFFFF',          # White
        'dark_bg': '#2C3E50',        # Dark Blue Gray
        
        # Text colors
        'text_primary': '#2C3E50',   # Dark Gray
        'text_secondary': '#6C757D', # Medium Gray
        'text_muted': '#ADB5BD',     # Light Gray
        
        # Border colors
        'border': '#E9ECEF',         # Light Border
        'border_dark': '#6C757D',    # Dark Border
        
        # Chart colors
        'chart_colors': [
            '#2E8B57', '#3CB371', '#FFD700', '#FF6B6B', 
            '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE'
        ]
    }

def get_persona_colors(persona: str) -> Dict[str, str]:
    """Get colors specific to user persona"""
    persona_colors = {
        'student': {
            'primary': '#4ECDC4',      # Turquoise
            'secondary': '#45B7D1',    # Light Blue
            'accent': '#FD79A8',       # Pink
        },
        'professional': {
            'primary': '#2E8B57',      # Sea Green
            'secondary': '#3CB371',    # Medium Sea Green
            'accent': '#FFD700',       # Gold
        },
        'family': {
            'primary': '#FF6B6B',      # Coral
            'secondary': '#4ECDC4',    # Turquoise  
            'accent': '#FFE66D',       # Yellow
        }
    }
    
    base_colors = get_theme_colors()
    persona_specific = persona_colors.get(persona, persona_colors['professional'])
    
    # Override primary colors with persona-specific ones
    base_colors.update(persona_specific)
    return base_colors

def apply_persona_theme(persona: str):
    """Apply persona-specific theme colors"""
    colors = get_persona_colors(persona)
    
    persona_css = f"""
    <style>
    :root {{
        --primary-color: {colors['primary']};
        --secondary-color: {colors['secondary']};
        --accent-color: {colors['accent']};
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']}) !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {colors['primary']} !important;
    }}
    
    .metric-value {{
        color: {colors['primary']} !important;
    }}
    
    .message-bubble.user {{
        background: {colors['primary']} !important;
    }}
    
    .avatar-assistant {{
        background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']}) !important;
    }}
    </style>
    """
    
    st.markdown(persona_css, unsafe_allow_html=True)

def create_gradient_background(color1: str, color2: str, direction: str = "135deg") -> str:
    """Create CSS gradient background"""
    return f"linear-gradient({direction}, {color1}, {color2})"

def get_chart_theme() -> Dict[str, Any]:
    """Get Plotly chart theme configuration"""
    colors = get_theme_colors()
    
    return {
        'layout': {
            'colorway': colors['chart_colors'],
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'font': {
                'family': 'Inter, sans-serif',
                'size': 12,
                'color': colors['text_primary']
            },
            'title': {
                'font': {
                    'family': 'Inter, sans-serif',
                    'size': 18,
                    'color': colors['text_primary']
                },
                'x': 0.5
            },
            'xaxis': {
                'gridcolor': colors['border'],
                'linecolor': colors['border'],
                'tickfont': {'family': 'Inter, sans-serif'},
                'title_font': {'family': 'Inter, sans-serif'}
            },
            'yaxis': {
                'gridcolor': colors['border'], 
                'linecolor': colors['border'],
                'tickfont': {'family': 'Inter, sans-serif'},
                'title_font': {'family': 'Inter, sans-serif'}
            }
        }
    }

def style_plotly_chart(fig: go.Figure, title: str = None) -> go.Figure:
    """Apply consistent styling to Plotly charts"""
    theme = get_chart_theme()
    colors = get_theme_colors()
    
    fig.update_layout(
        **theme['layout'],
        title=title,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right", 
            x=1,
            font=dict(family='Inter, sans-serif')
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    # Update traces with hover styling
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>',
        textfont_size=12,
        textfont_family='Inter'
    )
    
    return fig

def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal") -> str:
    """Create HTML for a styled metric card"""
    colors = get_theme_colors()
    
    delta_html = ""
    if delta:
        delta_color_map = {
            "normal": colors['text_secondary'],
            "inverse": colors['error'],
            "off": colors['text_muted']
        }
        delta_style = f"color: {delta_color_map.get(delta_color, colors['text_secondary'])};"
        delta_html = f'<div class="metric-delta" style="{delta_style} font-size: 0.8rem; margin-top: 0.25rem;">{delta}</div>'
    
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
        {delta_html}
    </div>
    """

def create_status_badge(text: str, status: str = "info") -> str:
    """Create HTML for a status badge"""
    colors = get_theme_colors()
    
    status_colors = {
        'success': colors['success'],
        'warning': colors['warning'],
        'error': colors['error'],
        'info': colors['info'],
        'primary': colors['primary']
    }
    
    bg_color = status_colors.get(status, colors['info'])
    
    return f"""
    <span style="
        background: {bg_color};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
    ">{text}</span>
    """

def create_progress_ring(percentage: float, size: int = 120) -> str:
    """Create HTML/CSS for a circular progress ring"""
    colors = get_theme_colors()
    
    return f"""
    <div style="
        width: {size}px;
        height: {size}px;
        border-radius: 50%;
        background: conic-gradient(
            {colors['primary']} 0deg {percentage * 3.6}deg,
            {colors['border']} {percentage * 3.6}deg 360deg
        );
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        margin: 0 auto;
    ">
        <div style="
            width: {size - 20}px;
            height: {size - 20}px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: {size // 8}px;
            color: {colors['primary']};
        ">
            {percentage:.0f}%
        </div>
    </div>
    """

def create_timeline_item(title: str, description: str, date: str, status: str = "pending") -> str:
    """Create HTML for a timeline item"""
    colors = get_theme_colors()
    
    status_colors = {
        'completed': colors['success'],
        'current': colors['primary'],
        'pending': colors['text_muted']
    }
    
    status_icons = {
        'completed': '✅',
        'current': '🎯',
        'pending': '⏳'
    }
    
    color = status_colors.get(status, colors['text_muted'])
    icon = status_icons.get(status, '⏳')
    
    return f"""
    <div style="
        display: flex;
        padding: 1rem;
        border-left: 3px solid {color};
        margin: 0.5rem 0;
        background: {colors['light_bg'] if status == 'current' else 'transparent'};
        border-radius: 0 10px 10px 0;
    ">
        <div style="
            margin-right: 1rem;
            font-size: 1.5rem;
        ">{icon}</div>
        <div>
            <div style="
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                color: {colors['text_primary']};
                margin-bottom: 0.25rem;
            ">{title}</div>
            <div style="
                font-family: 'Inter', sans-serif;
                color: {colors['text_secondary']};
                font-size: 0.9rem;
                margin-bottom: 0.25rem;
            ">{description}</div>
            <div style="
                font-family: 'Inter', sans-serif;
                color: {colors['text_muted']};
                font-size: 0.8rem;
            ">{date}</div>
        </div>
    </div>
    """

# Animation utilities
def add_fade_in_animation(element_class: str, delay: float = 0) -> str:
    """Add fade-in animation to elements"""
    return f"""
    <style>
    .{element_class} {{
        animation: fadeInUp 0.6s ease {delay}s both;
    }}
    </style>
    """

def add_hover_effects(element_class: str, transform: str = "translateY(-2px)") -> str:
    """Add hover effects to elements"""
    return f"""
    <style>
    .{element_class} {{
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    
    .{element_class}:hover {{
        transform: {transform};
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }}
    </style>
    """

# Theme validation
def validate_theme_colors(colors: Dict[str, str]) -> bool:
    """Validate theme color format"""
    required_colors = ['primary', 'secondary', 'accent', 'text_primary', 'light_bg']
    
    for color_name in required_colors:
        if color_name not in colors:
            return False
        
        color_value = colors[color_name]
        if not (color_value.startswith('#') and len(color_value) == 7):
            return False
    
    return True

# Export theme configuration for external use
def export_theme_config() -> Dict[str, Any]:
    """Export theme configuration for external applications"""
    colors = get_theme_colors()
    
    return {
        'colors': colors,
        'fonts': {
            'primary': 'Inter, sans-serif',
            'secondary': 'Inter, sans-serif'
        },
        'spacing': {
            'xs': '0.25rem',
            'sm': '0.5rem', 
            'md': '1rem',
            'lg': '1.5rem',
            'xl': '2rem'
        },
        'border_radius': {
            'sm': '5px',
            'md': '10px',
            'lg': '15px',
            'xl': '20px'
        },
        'shadows': {
            'sm': '0 2px 10px rgba(0, 0, 0, 0.05)',
            'md': '0 4px 20px rgba(0, 0, 0, 0.08)',
            'lg': '0 8px 30px rgba(0, 0, 0, 0.12)'
        }
    }

