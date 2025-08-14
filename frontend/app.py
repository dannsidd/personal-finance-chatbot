import streamlit as st
import sys
import os
from datetime import datetime
import logging

# Add backend folder to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import frontend components using relative paths
from utils.api_client import APIClient, APIError
from utils.theme import apply_custom_theme
from utils.helpers import (
    format_currency, format_date, display_error_message, 
    display_success_message, get_user_avatar
)
from components.auth import render_login_page, check_authentication
from components.chat import render_chat
from components.budget import render_budget
from components.debt import render_debt
from components.goals import render_goals
from components.history import render_chat_history_sidebar

# Page configuration
st.set_page_config(
    page_title="Personal Finance Chatbot",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/issues',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': "# Personal Finance Chatbot\nYour AI-powered financial guidance companion"
    }
)

# Apply custom theme
apply_custom_theme()

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'authenticated': False,
        'user': None,
        'access_token': None,
        'current_session_id': None,
        'messages': [],
        'persona': 'student',
        'language': 'en',
        'reasoning_mode': False,
        'debug_mode': False,
        'api_client': None,
        'page_loaded': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

#def setup_api_client():
#    """Setup API client with authentication"""
#    if st.session_state.api_client is None:
#        api_base_url = st.secrets.get("api_base_url", "http://localhost:8000")
#        st.session_state.api_client = APIClient(api_base_url)
#    
#    if st.session_state.access_token:
#        st.session_state.api_client.set_auth_token(st.session_state.access_token)


def setup_api_client():
    """Setup API client with authentication"""
    if st.session_state.api_client is None:
        # Use env var or fallback URL if secrets not set
        api_base_url = "http://localhost:8000"
        try:
            api_base_url = st.secrets["api_base_url"]
        except Exception:
            pass
        st.session_state.api_client = APIClient(api_base_url)
    
    if st.session_state.access_token:
        st.session_state.api_client.set_auth_token(st.session_state.access_token)


def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Setup API client
    setup_api_client()
    
    # Check authentication
    if not st.session_state.authenticated:
        render_login_page()
        return
    
    # Main application UI
    render_main_application()

def render_main_application():
    """Render the main authenticated application"""
    # Header
    render_header()
    
    # Sidebar
    render_sidebar()
    
    # Main content area
    render_main_content()
    
    # Footer
    render_footer()

def render_header():
    """Render application header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #2E8B57; margin: 0;'>💰 Personal Finance Chatbot</h1>
            <p style='color: #666; margin: 0;'>Your AI-powered financial guidance companion</p>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    """Render application sidebar"""
    with st.sidebar:
        # User profile section
        render_user_profile_section()
        
        # Settings section
        render_settings_section()
        
        # Chat history
        render_chat_history_sidebar()
        
        # Quick actions
        render_quick_actions()

def render_user_profile_section():
    """Render user profile in sidebar"""
    if st.session_state.user:
        user = st.session_state.user
        avatar = get_user_avatar(user.get('email', ''))
        
        st.markdown(f"""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #2E8B57, #3CB371); border-radius: 10px; margin-bottom: 1rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{avatar}</div>
            <div style='color: white; font-weight: bold;'>{user.get('first_name', 'User')}</div>
            <div style='color: #E8F5E8; font-size: 0.9rem;'>{user.get('email', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout_user()

def render_settings_section():
    """Render settings section"""
    st.markdown("### ⚙️ Settings")
    
    # Persona selection
    persona_options = {
        'student': '🎓 Student',
        'professional': '💼 Professional',
        'family': '👨‍👩‍👧‍👦 Family'
    }
    
    selected_persona = st.selectbox(
        "👤 User Type",
        options=list(persona_options.keys()),
        format_func=lambda x: persona_options[x],
        index=list(persona_options.keys()).index(st.session_state.persona),
        key="persona_selector"
    )
    
    if selected_persona != st.session_state.persona:
        st.session_state.persona = selected_persona
        update_user_preferences()
    
    # Language selection
    language_options = {
        'en': '🇺🇸 English',
        'hi': '🇮🇳 हिंदी',
        'ta': '🇮🇳 தமிழ்',
        'te': '🇮🇳 తెలుగు',
        'es': '🇪🇸 Español',
        'fr': '🇫🇷 Français'
    }
    
    selected_language = st.selectbox(
        "🌍 Language",
        options=list(language_options.keys()),
        format_func=lambda x: language_options[x],
        index=list(language_options.keys()).index(st.session_state.language),
        key="language_selector"
    )
    
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        update_user_preferences()
    
    # Advanced settings
    with st.expander("🔧 Advanced"):
        st.session_state.reasoning_mode = st.checkbox(
            "Enable Deep Reasoning",
            value=st.session_state.reasoning_mode,
            help="Use more compute for complex analysis"
        )
        
        st.session_state.debug_mode = st.checkbox(
            "Debug Mode",
            value=st.session_state.debug_mode,
            help="Show additional information"
        )

def render_quick_actions():
    """Render quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("📊 Upload Transactions", use_container_width=True):
        st.session_state.active_tab = "Budget Insights"
        st.rerun()
    
    if st.button("💳 Plan Debt Payoff", use_container_width=True):
        st.session_state.active_tab = "Debt Navigator"
        st.rerun()
    
    if st.button("🎯 Set Financial Goals", use_container_width=True):
        st.session_state.active_tab = "Goal Planner"
        st.rerun()

def render_main_content():
    """Render main content area with tabs"""
    # Tab navigation
    tab_icons = {
        "💬 Chat": "chat",
        "📊 Budget Insights": "budget", 
        "💳 Debt Navigator": "debt",
        "🎯 Goal Planner": "goals"
    }
    
    tabs = st.tabs(list(tab_icons.keys()))
    
    with tabs[0]:  # Chat
        render_chat()
    
    with tabs[1]:  # Budget
        render_budget()
    
    with tabs[2]:  # Debt
        render_debt()
    
    with tabs[3]:  # Goals
        render_goals()

def render_footer():
    """Render application footer"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px; font-size: 0.9rem;'>
            <p>Powered by <strong>IBM Watson & Granite AI</strong> | Built with ❤️ using <strong>Streamlit & FastAPI</strong></p>
            <p>🔒 Your financial data is secure and encrypted | 🌍 Available in multiple languages</p>
            <p style='font-size: 0.8rem; margin-top: 10px;'>
                v1.0.0 | <a href='#'>Privacy Policy</a> | <a href='#'>Terms of Service</a> | <a href='#'>Support</a>
            </p>
        </div>
        """, unsafe_allow_html=True)

def update_user_preferences():
    """Update user preferences in backend"""
    try:
        if st.session_state.api_client and st.session_state.user:
            update_data = {
                'persona_preference': st.session_state.persona,
                'language_preference': st.session_state.language
            }
            
            result = st.session_state.api_client.update_user_profile(update_data)
            st.session_state.user.update(result)
            
    except APIError as e:
        logger.error(f"Failed to update user preferences: {e}")

def logout_user():
    """Logout user and clear session"""
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize
    initialize_session_state()
    
    st.success("✅ Logged out successfully!")
    st.rerun()

if __name__ == "__main__":
    main()

