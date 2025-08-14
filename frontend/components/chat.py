import streamlit as st
from datetime import datetime
from utils.api_client import APIClient, APIError
from utils.helpers import (
    display_error_message, display_success_message,
    format_date, sanitize_input
)
import logging
import time
import json

logger = logging.getLogger(__name__)

def render_chat_interface():
    """Render the main chat interface"""
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your finances..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = generate_ai_response(prompt)
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"I apologize, but I encountered an error: {str(e)}"
                    st.error(error_msg)
                    logger.error(f"Chat generation failed: {e}")

def generate_ai_response(user_input: str) -> str:
    """Generate AI response with proper error handling - FIXED VERSION"""
    try:
        # Check if user is authenticated
        if not st.session_state.get('authenticated', False):
            return "Please log in to use the chat feature."
        
        # Check if API client exists
        if not hasattr(st.session_state, 'api_client') or st.session_state.api_client is None:
            return "API connection not available. Please refresh the page."
        
        # Prepare messages in correct format for backend
        messages = []
        
        # Add recent conversation history (last 10 messages for context)
        recent_messages = st.session_state.messages[-10:]  # Last 10 messages
        for msg in recent_messages:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                # Only include role and content - remove timestamps and metadata
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user message
        messages.append({
            "role": "user", 
            "content": user_input
        })
        
        # Get user preferences
        persona = st.session_state.get('persona', 'student')
        language = st.session_state.get('language', 'en')
        
        # Prepare context
        context = {
            "has_budget_data": False,
            "has_debt_data": False,
            "has_goals": False
        }
        
        # FIXED: Call API with individual parameters, not a single dict
        response = st.session_state.api_client.generate_chat_response(
            messages=messages,          # List of message dicts
            persona=persona,           # String
            language=language,         # String
            reasoning=False,           # Boolean
            context=context           # Dict
        )
        
        # Extract response text
        if isinstance(response, dict):
            return response.get('text', 'I received your message but had trouble generating a response.')
        else:
            return str(response)
            
    except APIError as e:
        logger.error(f"API Error in chat: {e.message}")
        return f"I'm having trouble connecting to my AI system. Error: {e.message}"
        
    except Exception as e:
        logger.error(f"Unexpected error in chat: {e}")
        return "I encountered an unexpected error. Please try again or contact support."

# Keep your other render functions but remove the duplicate generate_ai_response
def render_chat():
    """Render main chat interface"""
    st.markdown("### 💬 Chat with Your Finance Coach")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        display_chat_messages()
        
        # Message input
        render_message_input()
        
        # Suggested prompts for new users
        if len(st.session_state.messages) == 0:
            render_suggested_prompts()

def display_chat_messages():
    """Display chat message history"""
    if not st.session_state.messages:
        # Welcome message
        render_welcome_message()
        return
    
    # Display messages
    for i, message in enumerate(st.session_state.messages):
        render_chat_message(message, i)

def render_welcome_message():
    """Render welcome message for new chat"""
    persona = st.session_state.get('persona', 'student')
    user_name = st.session_state.user.get('first_name', 'there') if st.session_state.get('user') else 'there'
    
    persona_greetings = {
        'student': f"Hi {user_name}! 🎓 I'm here to help you with student finances, budgeting, and building good money habits. What would you like to explore?",
        'professional': f"Hello {user_name}! 💼 I'm your professional finance assistant. I can help with investments, tax strategies, and career-focused financial planning. How can I assist you today?",
        'family': f"Welcome {user_name}! 👨‍👩‍👧‍👦 I'm here to help with family financial planning, from budgeting to saving for your children's future. What financial goals are you working on?"
    }
    
    greeting = persona_greetings.get(persona, f"Hello {user_name}! I'm your personal finance assistant. How can I help you today?")
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #2E8B57, #3CB371); color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;'>
        <div style='display: flex; align-items: center; margin-bottom: 1rem;'>
            <div style='width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;'>
                🤖
            </div>
            <div>
                <div style='font-weight: bold; font-size: 1.1rem;'>Your AI Finance Coach</div>
                <div style='font-size: 0.9rem; opacity: 0.9;'>{persona.title()} Mode • {st.session_state.get("language", "en").upper()}</div>
            </div>
        </div>
        <div style='font-size: 1rem; line-height: 1.5;'>
            {greeting}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_chat_message(message, index):
    """Render individual chat message"""
    role = message.get('role', 'user')
    content = message.get('content', '')
    timestamp = message.get('timestamp', datetime.now())
    
    # Format timestamp
    time_str = format_date(timestamp, 'datetime') if isinstance(timestamp, (str, datetime)) else ''
    
    if role == 'user':
        render_user_message(content, time_str, index)
    else:
        render_assistant_message(content, time_str, {}, index)

def render_user_message(content, timestamp, index):
    """Render user message"""
    user_avatar = "👤"
    
    st.markdown(f"""
    <div style='display: flex; justify-content: flex-end; margin: 1rem 0;'>
        <div style='max-width: 70%; background: #E3F2FD; padding: 1rem; border-radius: 15px 15px 5px 15px; position: relative;'>
            <div style='font-size: 0.9rem; margin-bottom: 0.5rem;'>{content}</div>
            <div style='font-size: 0.7rem; color: #666; text-align: right;'>{timestamp}</div>
        </div>
        <div style='width: 35px; height: 35px; background: #2196F3; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-left: 0.5rem; font-size: 1.2rem;'>
            {user_avatar}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_assistant_message(content, timestamp, metadata, index):
    """Render assistant message"""
    st.markdown(f"""
    <div style='display: flex; justify-content: flex-start; margin: 1rem 0;'>
        <div style='width: 35px; height: 35px; background: linear-gradient(135deg, #2E8B57, #3CB371); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 0.5rem; font-size: 1.2rem;'>
            🤖
        </div>
        <div style='max-width: 70%; background: #F8F9FA; padding: 1rem; border-radius: 15px 15px 15px 5px; border-left: 3px solid #2E8B57;'>
            <div style='font-size: 0.9rem; margin-bottom: 0.5rem; line-height: 1.6;'>{content}</div>
            <div style='font-size: 0.7rem; color: #666;'>{timestamp}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_message_input():
    """Render message input area"""
    # Create columns for input and button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Use session state for input to clear after sending
        if 'message_input' not in st.session_state:
            st.session_state.message_input = ""
        
        user_input = st.text_input(
            "Type your message...",
            value=st.session_state.message_input,
            placeholder=get_input_placeholder(),
            key="message_input_field",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 Send", type="primary", use_container_width=True)
    
    # Handle message sending
    if send_button and user_input.strip():
        handle_user_message(user_input.strip())
        # Clear input
        st.session_state.message_input = ""
        st.rerun()

def get_input_placeholder():
    """Get placeholder text based on persona"""
    persona = st.session_state.get('persona', 'student')
    placeholders = {
        'student': "Ask about budgeting, student loans, or building credit...",
        'professional': "Ask about investments, retirement planning, or tax strategies...",
        'family': "Ask about family budgeting, emergency funds, or saving for kids..."
    }
    return placeholders.get(persona, "Ask me anything about your finances...")

def handle_user_message(message_text):
    """Handle user message and generate AI response"""
    try:
        # Sanitize input
        clean_message = sanitize_input(message_text, max_length=2000)
        
        # Add user message to history
        user_message = {
            'role': 'user',
            'content': clean_message,
            'timestamp': datetime.now()
        }
        st.session_state.messages.append(user_message)
        
        # Generate AI response using the fixed function
        response_text = generate_ai_response(clean_message)
        
        # Add AI response to history
        ai_message = {
            'role': 'assistant',
            'content': response_text,
            'timestamp': datetime.now()
        }
        st.session_state.messages.append(ai_message)
        
    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        display_error_message("Failed to process your message", str(e))

def render_suggested_prompts():
    """Render suggested prompts for new users"""
    persona = st.session_state.get('persona', 'student')
    
    suggestions = {
        'student': [
            "How can I save money while paying off student loans?",
            "What's a good budget for a college student?",
            "Should I get a credit card in college?",
            "How do I build credit as a student?"
        ],
        'professional': [
            "How should I allocate my 401(k) contributions?",
            "What's the best debt payoff strategy for my situation?",
            "How much should I have in emergency savings?",
            "Should I invest in index funds or individual stocks?"
        ],
        'family': [
            "How can we pay off debt while saving for our kids' education?",
            "What's a realistic family emergency fund goal?",
            "How do we balance multiple financial priorities?",
            "Should we refinance our mortgage?"
        ]
    }
    
    persona_suggestions = suggestions.get(persona, suggestions['professional'])
    
    st.markdown("### 💡 Try asking:")
    
    # Display suggestions in columns
    cols = st.columns(2)
    
    for i, suggestion in enumerate(persona_suggestions):
        col = cols[i % 2]
        
        with col:
            if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                handle_user_message(suggestion)
                st.rerun()

def clear_chat_history():
    """Clear chat history"""
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
