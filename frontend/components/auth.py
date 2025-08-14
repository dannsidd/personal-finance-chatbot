import streamlit as st
from utils.api_client import APIClient, APIError
from utils.helpers import validate_email, display_error_message, display_success_message
import logging

logger = logging.getLogger(__name__)

def render_login_page():
    """Render login/registration page"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #2E8B57; font-size: 3rem; margin-bottom: 0;'>💰</h1>
        <h2 style='color: #2E8B57; margin: 0;'>Personal Finance Chatbot</h2>
        <p style='color: #666; font-size: 1.2rem;'>Your AI-powered financial guidance companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        
        with tab1:
            render_login_form()
        
        with tab2:
            render_signup_form()

def render_login_form():
    """Render login form"""
    st.markdown("### Welcome Back!")
    
    with st.form("login_form"):
        email = st.text_input(
            "📧 Email",
            placeholder="Enter your email address",
            help="Use the email you registered with"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter your password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            login_submitted = st.form_submit_button(
                "🚀 Login",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            demo_submitted = st.form_submit_button(
                "🎮 Try Demo",
                use_container_width=True
            )
    
    if login_submitted:
        handle_login(email, password)
    
    if demo_submitted:
        handle_demo_login()

def render_signup_form():
    """Render signup form"""
    st.markdown("### Join Us Today!")
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input(
                "👤 First Name",
                placeholder="Your first name"
            )
        
        with col2:
            last_name = st.text_input(
                "👤 Last Name", 
                placeholder="Your last name"
            )
        
        email = st.text_input(
            "📧 Email",
            placeholder="Enter your email address",
            help="We'll use this for login and important updates"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Create a strong password",
            help="Minimum 8 characters"
        )
        
        confirm_password = st.text_input(
            "🔒 Confirm Password",
            type="password",
            placeholder="Confirm your password"
        )
        
        # User preferences
        st.markdown("**Choose your profile:**")
        
        persona = st.selectbox(
            "👤 I am a...",
            options=['student', 'professional', 'family'],
            format_func=lambda x: {
                'student': '🎓 Student/Early Career',
                'professional': '💼 Working Professional',
                'family': '👨‍👩‍👧‍👦 Family Manager'
            }[x]
        )
        
        language = st.selectbox(
            "🌍 Preferred Language",
            options=['en', 'hi', 'ta', 'te', 'es', 'fr'],
            format_func=lambda x: {
                'en': '🇺🇸 English',
                'hi': '🇮🇳 हिंदी (Hindi)',
                'ta': '🇮🇳 தமிழ் (Tamil)',
                'te': '🇮🇳 తెలుగు (Telugu)',
                'es': '🇪🇸 Español',
                'fr': '🇫🇷 Français'
            }[x]
        )
        
        # Terms acceptance
        terms_accepted = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            help="Please read our terms and privacy policy"
        )
        
        signup_submitted = st.form_submit_button(
            "🎉 Create Account",
            type="primary",
            use_container_width=True
        )
    
    if signup_submitted:
        handle_signup(
            email, password, confirm_password, first_name, 
            last_name, persona, language, terms_accepted
        )

def handle_login(email: str, password: str):
    """Handle user login"""
    # Validation
    if not email or not password:
        display_error_message("Please fill in all fields")
        return
    
    if not validate_email(email):
        display_error_message("Please enter a valid email address")
        return
    
    # Setup API client
    if st.session_state.api_client is None:
        api_base_url = st.secrets.get("api_base_url", "http://localhost:8000")
        st.session_state.api_client = APIClient(api_base_url)
    
    try:
        with st.spinner("🔐 Logging you in..."):
            # Login
            login_result = st.session_state.api_client.login(email, password)
            
            # Store authentication data
            st.session_state.access_token = login_result['access_token']
            st.session_state.user = login_result['user']
            st.session_state.authenticated = True
            
            # Update API client with token
            st.session_state.api_client.set_auth_token(st.session_state.access_token)
            
            # Update session preferences from user profile
            user = st.session_state.user
            st.session_state.persona = user.get('persona_preference', 'student')
            st.session_state.language = user.get('language_preference', 'en')
            
            display_success_message(
                f"Welcome back, {user.get('first_name', 'User')}!",
                "You've been logged in successfully."
            )
            
            # Force rerun to show main app
            st.rerun()
            
    except APIError as e:
        display_error_message(
            "Login failed",
            f"Please check your credentials and try again. {e.message}"
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        display_error_message("An unexpected error occurred", str(e))

def handle_signup(
    email: str, password: str, confirm_password: str,
    first_name: str, last_name: str, persona: str,
    language: str, terms_accepted: bool
):
    """Handle user signup"""
    # Validation
    if not all([email, password, confirm_password, first_name]):
        display_error_message("Please fill in all required fields")
        return
    
    if not validate_email(email):
        display_error_message("Please enter a valid email address")
        return
    
    if password != confirm_password:
        display_error_message("Passwords do not match")
        return
    
    if len(password) < 8:
        display_error_message("Password must be at least 8 characters long")
        return
    
    if not terms_accepted:
        display_error_message("Please accept the Terms of Service and Privacy Policy")
        return
    
    # Setup API client
    if st.session_state.api_client is None:
        api_base_url = st.secrets.get("api_base_url", "http://localhost:8000")
        st.session_state.api_client = APIClient(api_base_url)
    
    try:
        with st.spinner("🎉 Creating your account..."):
            # Register user
            user_data = {
                'email': email,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
                'persona_preference': persona,
                'language_preference': language
            }
            
            register_result = st.session_state.api_client.register(user_data)
            
            display_success_message(
                "Account created successfully!",
                "You can now log in with your credentials."
            )
            
            # Auto-login after successful registration
            handle_login(email, password)
            
    except APIError as e:
        if "already registered" in e.message.lower():
            display_error_message(
                "Email already registered",
                "Please use a different email or try logging in."
            )
        else:
            display_error_message("Registration failed", e.message)
    except Exception as e:
        logger.error(f"Signup error: {e}")
        display_error_message("An unexpected error occurred", str(e))

def handle_demo_login():
    """Handle demo login with sample user"""
    try:
        with st.spinner("🎮 Setting up demo account..."):
            # Create demo user data
            st.session_state.user = {
                'id': 'demo-user-123',
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User',
                'persona_preference': 'professional',
                'language_preference': 'en'
            }
            st.session_state.authenticated = True
            st.session_state.access_token = 'demo-token'
            st.session_state.persona = 'professional'
            st.session_state.language = 'en'
            
            display_success_message(
                "Welcome to the demo!",
                "You can explore all features with sample data."
            )
            
            st.rerun()
            
    except Exception as e:
        logger.error(f"Demo login error: {e}")
        display_error_message("Demo setup failed", str(e))

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def render_user_profile():
    """Render user profile management"""
    if not check_authentication():
        st.error("Please log in to view your profile")
        return
    
    user = st.session_state.user
    
    st.markdown("### 👤 Your Profile")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input(
                "First Name",
                value=user.get('first_name', ''),
                placeholder="Your first name"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name",
                value=user.get('last_name', ''),
                placeholder="Your last name"
            )
        
        st.text_input(
            "Email",
            value=user.get('email', ''),
            disabled=True,
            help="Email cannot be changed"
        )
        
        persona = st.selectbox(
            "Profile Type",
            options=['student', 'professional', 'family'],
            index=['student', 'professional', 'family'].index(user.get('persona_preference', 'student')),
            format_func=lambda x: {
                'student': '🎓 Student/Early Career',
                'professional': '💼 Working Professional', 
                'family': '👨‍👩‍👧‍👦 Family Manager'
            }[x]
        )
        
        language = st.selectbox(
            "Language",
            options=['en', 'hi', 'ta', 'te', 'es', 'fr'],
            index=['en', 'hi', 'ta', 'te', 'es', 'fr'].index(user.get('language_preference', 'en')),
            format_func=lambda x: {
                'en': '🇺🇸 English',
                'hi': '🇮🇳 हिंदी',
                'ta': '🇮🇳 தமிழ்',
                'te': '🇮🇳 తెలుగు',
                'es': '🇪🇸 Español',
                'fr': '🇫🇷 Français'
            }[x]
        )
        
        update_submitted = st.form_submit_button(
            "💾 Update Profile",
            type="primary"
        )
    
    if update_submitted:
        try:
            update_data = {
                'first_name': first_name,
                'last_name': last_name,
                'persona_preference': persona,
                'language_preference': language
            }
            
            if st.session_state.api_client:
                result = st.session_state.api_client.update_user_profile(update_data)
                st.session_state.user.update(result)
                st.session_state.persona = persona
                st.session_state.language = language
                
                display_success_message("Profile updated successfully!")
                
        except APIError as e:
            display_error_message("Profile update failed", e.message)
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            display_error_message("An unexpected error occurred", str(e))

