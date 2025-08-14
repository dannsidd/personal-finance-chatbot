import requests
import streamlit as st
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
    
    def set_auth_token(self, token: str):
        """Set authentication token for API calls"""
        self.auth_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user - FIXED to send form data instead of JSON"""
        try:
            # Send form data, not JSON (this fixes the 422 error)
            data = {
                'username': email,  # OAuth2PasswordRequestForm expects 'username', not 'email'
                'password': password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/token",
                data=data,  # Use 'data' for form data, not 'json'
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Invalid email or password", 401)
            elif response.status_code == 422:
                raise APIError("Login request format error", 422)
            else:
                raise APIError(f"Login failed: {response.text}", response.status_code)
                
        except requests.RequestException as e:
            logger.error(f"Login request failed: {e}")
            raise APIError("API request failed")
    
    def register(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register new user - FIXED with proper indentation and error handling"""
        try:
            # Ensure all required fields are present
            required_fields = ['email', 'password', 'first_name', 'last_name']
            missing_fields = [field for field in required_fields if not user_data.get(field)]
            
            if missing_fields:
                raise APIError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Clean the data
            clean_data = {
                'email': user_data['email'].strip().lower(),
                'password': user_data['password'],
                'first_name': user_data['first_name'].strip(),
                'last_name': user_data['last_name'].strip(),
                'persona_preference': user_data.get('persona_preference', 'student'),
                'language_preference': user_data.get('language_preference', 'en')
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=clean_data,
                timeout=30  # Add timeout
            )
            
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                try:
                    error_detail = response.json().get('detail', 'Email already registered')
                except:
                    error_detail = 'Email already registered'
                raise APIError(error_detail, 400)
            elif response.status_code == 422:
                try:
                    error_detail = response.json().get('detail', 'Invalid data format')
                except:
                    error_detail = 'Invalid data format'
                raise APIError(f"Validation error: {error_detail}", 422)
            else:
                raise APIError(f"Registration failed (HTTP {response.status_code})", response.status_code)
                
        except requests.RequestException as e:
            logger.error(f"Registration network error: {e}")
            raise APIError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise APIError(f"Registration error: {str(e)}")
    
    # MISSING METHOD 1: Chat Sessions Management
    def get_chat_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/chat/sessions",
                params={'limit': limit},
                headers=self.session.headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication required", 401)
            else:
                raise APIError(f"Failed to get chat sessions: {response.text}", response.status_code)
                
        except requests.RequestException as e:
            logger.error(f"Get chat sessions request failed: {e}")
            raise APIError("API request failed")
        except Exception as e:
            logger.error(f"Get chat sessions error: {e}")
            raise APIError(f"Get chat sessions error: {str(e)}")
    
    def create_chat_session(self, session_name: str, persona: str = "student", language: str = "en") -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            data = {
                "session_name": session_name,
                "persona": persona,
                "language": language
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/sessions",
                json=data,
                headers=self.session.headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication required", 401)
            else:
                raise APIError(f"Failed to create chat session: {response.text}", response.status_code)
                
        except requests.RequestException as e:
            logger.error(f"Create chat session request failed: {e}")
            raise APIError("API request failed")
        except Exception as e:
            logger.error(f"Create chat session error: {e}")
            raise APIError(f"Create chat session error: {str(e)}")
    
    # MISSING METHOD 2: Chat Generation (Frontend calls this method name)
    def generate_chat_response(self, messages: list, persona: str = "student", language: str = "en", reasoning: bool = False, context: Dict = None) -> Dict[str, Any]:
    
        try:
            # Validate and clean messages
            if not messages:
                raise APIError("No messages provided")
            
            cleaned_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    # Extract only required fields
                    cleaned_msg = {
                        "role": str(msg.get("role", "user")).strip(),
                        "content": str(msg.get("content", "")).strip()
                    }
                    
                    # Validate role
                    if cleaned_msg["role"] not in ["user", "assistant", "system"]:
                        cleaned_msg["role"] = "user"
                    
                    # Validate content
                    if not cleaned_msg["content"]:
                        continue  # Skip empty messages
                    
                    cleaned_messages.append(cleaned_msg)
                else:
                    logger.warning(f"Skipping invalid message format: {type(msg)}")
            
            if not cleaned_messages:
                raise APIError("No valid messages to process")
            
            # Prepare request data
            data = {
                "messages": cleaned_messages,
                "persona": persona,
                "language": language,
                "reasoning": reasoning,
                "context": context or {}
            }
            
            # Log request for debugging (remove in production)
            logger.debug(f"Sending chat request: {len(cleaned_messages)} messages, persona: {persona}")
            
            # Make API call
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/generate",
                json=data,
                headers=self.session.headers,
                timeout=180  # Increased timeout for AI generation
            )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Chat response received successfully")
                return result
                
            elif response.status_code == 401:
                raise APIError("Authentication required - please log in again", 401)
                
            elif response.status_code == 422:
                try:
                    error_detail = response.json()
                    logger.error(f"Validation error details: {error_detail}")
                    raise APIError(f"Request validation failed: {error_detail.get('detail', 'Invalid format')}", 422)
                except:
                    raise APIError("Request format validation failed", 422)
                    
            elif response.status_code == 500:
                raise APIError("AI service temporarily unavailable", 500)
                
            else:
                raise APIError(f"Chat service error (HTTP {response.status_code})", response.status_code)
                
        except requests.exceptions.Timeout:
            raise APIError("Request timed out - AI is taking too long to respond")
            
        except requests.exceptions.ConnectionError:
            raise APIError("Cannot connect to AI service - check if backend is running")
            
        except requests.RequestException as e:
            logger.error(f"Network error in chat generation: {e}")
            raise APIError("Network connection failed")
            
        except Exception as e:
            logger.error(f"Unexpected error in chat generation: {e}")
            raise APIError(f"Unexpected error: {str(e)}")


    
    # Keep the existing chat_generate method for compatibility
    def chat_generate(self, messages: list, persona: str = "student", language: str = "en", reasoning: bool = False, context: Dict = None) -> Dict[str, Any]:
        """Generate chat response - Alternative method name"""
        return self.generate_chat_response(messages, persona, language, reasoning, context)
    
    def update_user_profile(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/users/profile",
                json=update_data,
                headers=self.session.headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication required", 401)
            else:
                raise APIError(f"Profile update failed: {response.text}", response.status_code)
                
        except requests.RequestException as e:
            logger.error(f"Profile update request failed: {e}")
            raise APIError("API request failed")
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            raise APIError(f"Profile update error: {str(e)}")
    
    def analyze_text(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Analyze text using NLU"""
        try:
            data = {
                "text": text,
                "language": language
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/nlu/analyze",
                json=data,
                headers=self.session.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise APIError(f"Text analysis failed: {response.text}", response.status_code)
                
        except requests.RequestException as e:
            logger.error(f"Text analysis request failed: {e}")
            raise APIError("API request failed")
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            raise APIError(f"Text analysis error: {str(e)}")
