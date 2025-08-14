import streamlit as st
from datetime import datetime, timedelta
import logging
from utils.api_client import APIError
from utils.helpers import (
    format_date, display_error_message, display_success_message
)

logger = logging.getLogger(__name__)

def render_chat_history_sidebar():
    """Render chat history in sidebar"""
    if not st.session_state.authenticated:
        return
    
    st.markdown("### 💬 Chat History")
    
    try:
        # Get user's chat sessions
        if st.session_state.api_client:
            sessions = st.session_state.api_client.get_chat_sessions(limit=10)
            render_session_list(sessions)
        else:
            render_demo_sessions()
            
    except APIError as e:
        st.error(f"Failed to load chat history: {e.message}")
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        st.error("Failed to load chat history")

def render_session_list(sessions):
    """Render list of chat sessions"""
    if not sessions:
        st.info("No chat history yet")
        return
    
    # Group sessions by date
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    
    today_sessions = []
    yesterday_sessions = []
    week_sessions = []
    older_sessions = []
    
    for session in sessions:
        session_date = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00')).date()
        
        if session_date == today:
            today_sessions.append(session)
        elif session_date == yesterday:
            yesterday_sessions.append(session)
        elif session_date >= week_ago:
            week_sessions.append(session)
        else:
            older_sessions.append(session)
    
    # Render grouped sessions
    if today_sessions:
        st.markdown("**Today**")
        for session in today_sessions:
            render_session_item(session)
    
    if yesterday_sessions:
        st.markdown("**Yesterday**")
        for session in yesterday_sessions:
            render_session_item(session)
    
    if week_sessions:
        st.markdown("**This Week**")
        for session in week_sessions:
            render_session_item(session)
    
    if older_sessions:
        st.markdown("**Older**")
        for session in older_sessions[:5]:  # Show only 5 older sessions
            render_session_item(session)

def render_session_item(session):
    """Render individual session item"""
    session_name = session['session_name']
    created_at = datetime.fromisoformat(session['created_at'].replace('Z', '+00:00'))
    time_str = created_at.strftime("%I:%M %p")
    
    # Truncate long session names
    display_name = session_name[:25] + "..." if len(session_name) > 25 else session_name
    
    if st.button(
        f"💬 {display_name}",
        key=f"session_{session['id']}",
        help=f"Created: {format_date(created_at, 'long')} at {time_str}"
    ):
        load_chat_session(session['id'])

def render_demo_sessions():
    """Render demo chat sessions for offline mode"""
    demo_sessions = [
        {
            'id': 'demo_1',
            'name': 'Emergency Fund Planning',
            'time': '2:30 PM',
            'messages': [
                {'role': 'user', 'content': 'How much should I save for emergencies?'},
                {'role': 'assistant', 'content': 'For your situation as a student, I recommend starting with a $500 mini emergency fund, then building up to 3-6 months of expenses once you have stable income.'}
            ]
        },
        {
            'id': 'demo_2', 
            'name': 'Student Loan Strategy',
            'time': '1:15 PM',
            'messages': [
                {'role': 'user', 'content': 'Should I pay off student loans or save for a house?'},
                {'role': 'assistant', 'content': 'This depends on your loan interest rates and local housing market. Generally, if your student loan rates are below 5%, you might consider doing both simultaneously.'}
            ]
        }
    ]
    
    st.markdown("**Recent Chats**")
    for session in demo_sessions:
        if st.button(f"💬 {session['name']}", key=session['id']):
            load_demo_session(session)

def load_chat_session(session_id):
    """Load a specific chat session"""
    try:
        with st.spinner("Loading chat session..."):
            # Get session messages
            messages = st.session_state.api_client.get_session_messages(session_id)
            
            # Convert to session state format
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00')),
                    'metadata': msg.get('metadata', {})
                })
            
            # Update session state
            st.session_state.messages = formatted_messages
            st.session_state.current_session_id = session_id
            
            display_success_message(f"Loaded chat session")
            st.rerun()
            
    except APIError as e:
        display_error_message("Failed to load chat session", e.message)
    except Exception as e:
        logger.error(f"Session loading error: {e}")
        display_error_message("Failed to load session", str(e))

def load_demo_session(session):
    """Load demo chat session"""
    st.session_state.messages = session['messages']
    st.session_state.current_session_id = session['id']
    display_success_message(f"Loaded: {session['name']}")
    st.rerun()

def render_session_manager():
    """Render session management interface"""
    if not st.session_state.authenticated:
        st.warning("Please log in to manage chat sessions")
        return
    
    st.markdown("### 📚 Manage Chat Sessions")
    
    try:
        if st.session_state.api_client:
            sessions = st.session_state.api_client.get_chat_sessions(limit=20, include_archived=True)
            
            if not sessions:
                st.info("No chat sessions found")
                return
            
            # Session management table
            session_data = []
            for session in sessions:
                session_data.append({
                    'Name': session['session_name'],
                    'Created': format_date(session['created_at'], 'short'),
                    'Messages': session.get('message_count', 0),
                    'Persona': session['persona_used'].title(),
                    'Language': session['language_used'].upper(),
                    'ID': session['id']
                })
            
            df = pd.DataFrame(session_data)
            
            # Display sessions with selection
            selected_sessions = st.multiselect(
                "Select sessions to manage:",
                options=df['ID'].tolist(),
                format_func=lambda x: df[df['ID'] == x]['Name'].iloc[0] if len(df[df['ID'] == x]) > 0 else x
            )
            
            if selected_sessions:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📥 Export Selected", use_container_width=True):
                        export_selected_sessions(selected_sessions)
                
                with col2:
                    if st.button("📁 Archive Selected", use_container_width=True):
                        archive_selected_sessions(selected_sessions)
                
                with col3:
                    if st.button("🗑️ Delete Selected", use_container_width=True):
                        delete_selected_sessions(selected_sessions)
            
            # Display sessions table
            st.dataframe(df.drop('ID', axis=1), use_container_width=True)
            
        else:
            st.info("Session management not available in demo mode")
            
    except Exception as e:
        logger.error(f"Session management error: {e}")
        display_error_message("Failed to load session manager", str(e))

def export_chat_history():
    """Export complete chat history"""
    try:
        if not st.session_state.authenticated:
            st.warning("Please log in to export chat history")
            return
        
        with st.spinner("Preparing chat history export..."):
            if st.session_state.api_client:
                # Get all sessions
                sessions = st.session_state.api_client.get_chat_sessions(limit=100)
                
                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'user_email': st.session_state.user.get('email', ''),
                    'total_sessions': len(sessions),
                    'sessions': []
                }
                
                # Get messages for each session
                for session in sessions:
                    try:
                        messages = st.session_state.api_client.get_session_messages(session['id'])
                        
                        export_data['sessions'].append({
                            'session_info': session,
                            'messages': messages
                        })
                    except Exception as e:
                        logger.warning(f"Failed to export session {session['id']}: {e}")
                        continue
                
                # Create download
                import json
                json_str = json.dumps(export_data, indent=2, default=str)
                
                st.download_button(
                    label="📥 Download Complete Chat History",
                    data=json_str,
                    file_name=f"chat_history_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                display_success_message(f"Exported {len(sessions)} chat sessions")
                
            else:
                st.info("Export not available in demo mode")
                
    except Exception as e:
        logger.error(f"Export failed: {e}")
        display_error_message("Export failed", str(e))

def export_selected_sessions(session_ids):
    """Export selected chat sessions"""
    try:
        with st.spinner(f"Exporting {len(session_ids)} sessions..."):
            export_data = {
                'export_date': datetime.now().isoformat(),
                'sessions': []
            }
            
            for session_id in session_ids:
                try:
                    messages = st.session_state.api_client.get_session_messages(session_id)
                    export_data['sessions'].append({
                        'session_id': session_id,
                        'messages': messages
                    })
                except Exception as e:
                    logger.warning(f"Failed to export session {session_id}: {e}")
                    continue
            
            import json
            json_str = json.dumps(export_data, indent=2, default=str)
            
            st.download_button(
                label=f"📥 Download {len(session_ids)} Sessions",
                data=json_str,
                file_name=f"selected_sessions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        display_error_message("Export failed", str(e))

def archive_selected_sessions(session_ids):
    """Archive selected sessions"""
    # Implementation would call API to archive sessions
    st.info("📁 Archive functionality coming soon!")

def delete_selected_sessions(session_ids):
    """Delete selected sessions"""
    # Implementation would call API to delete sessions
    st.warning("🗑️ Delete functionality coming soon! Please contact support for session deletion.")
