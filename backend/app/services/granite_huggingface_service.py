from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from typing import Dict, Any, List, Optional
import logging
import json
import re
import os
from app.config import settings

logger = logging.getLogger(__name__)

class GraniteHuggingFaceService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize Granite model from Hugging Face
        self.model = None
        self.tokenizer = None
        
        # Load models
        self.load_granite_model()
        self.load_additional_models()
        
        logger.info("Granite HuggingFace Service initialized successfully")
    
    def load_granite_model(self):
        """Load IBM Granite 3.3-2B-Base model from Hugging Face"""
        try:
            # Use the lightweight 2B base model
            model_name = os.getenv("GRANITE_MODEL_NAME", "ibm-granite/granite-3.3-2b-base")
            
            logger.info(f"Loading Granite model: {model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # For base models, we may need to set pad_token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model with optimizations for 2B base model
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,  # Use float32 for CPU compatibility
                device_map=None,  # Let's handle device placement manually
                trust_remote_code=True,
                load_in_8bit=False  # Not needed for 2B model
            )
            
            # Move model to device
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("Granite 3.3-2B-Base model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Granite 3.3-2B-Base model: {e}")
            # Fallback to even smaller model if needed
            try:
                fallback_model = "ibm-granite/granite-3.0-2b-instruct"
                logger.info(f"Falling back to: {fallback_model}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                    
                self.model = AutoModelForCausalLM.from_pretrained(
                    fallback_model,
                    torch_dtype=torch.float32,
                    device_map=None,
                    trust_remote_code=True
                )
                self.model.to(self.device)
                self.model.eval()
                
                logger.info("Fallback Granite 2B model loaded successfully")
                
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                raise
    
    def load_additional_models(self):
        """Load additional models for sentiment and NLU tasks"""
        try:
            # Sentiment analysis pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
            
            # Emotion analysis pipeline
            self.emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Additional NLU models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load additional models: {e}")
            self.sentiment_pipeline = None
            self.emotion_pipeline = None
    
    async def generate_response(
        self, 
        messages: List[Dict], 
        persona: str = "student", 
        language: str = "en",
        reasoning: bool = False,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Generate AI response using Granite 2B base model"""
        try:
            # Build conversation for base model (no chat template)
            formatted_input = self._build_conversation_for_base_model(messages, persona, language, context)
            
            # Generate response
            response_text = await self._generate_with_granite_base(formatted_input, reasoning)
            
            return {
                "text": response_text,
                "model_used": "granite-3.3-2b-base-huggingface",
                "persona": persona,
                "language": language,
                "reasoning_used": reasoning
            }
            
        except Exception as e:
            logger.error(f"Granite generation failed: {e}")
            return {
                "text": "I apologize, but I'm having trouble processing your request right now. Please try again in a moment.",
                "model_used": "fallback",
                "error": str(e)
            }
    
    def _build_conversation_for_base_model(self, messages: List[Dict], persona: str, language: str, context: Dict = None):
        """Build conversation for base model (simple text format, no chat template)"""
        
        # Build system prompt
        system_prompt = self._build_system_prompt(persona, language, context)
        
        # Format as simple text for base model
        conversation_text = f"{system_prompt}\n\n"
        
        # Add conversation history (last 5 messages for context)
        for message in messages[-5:]:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "user":
                conversation_text += f"Human: {content}\n"
            else:
                conversation_text += f"Assistant: {content}\n"
        
        # Add prompt for new response
        conversation_text += "Assistant:"
        
        return conversation_text
    
    async def _generate_with_granite_base(self, formatted_input: str, reasoning: bool = False) -> str:
        try:
            inputs = self.tokenizer(
                formatted_input, 
                return_tensors="pt", 
                truncation=True, 
                max_length=1024  # Reduced for faster processing
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=128,        # ✅ Reduced from 256 for faster response
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    # ❌ REMOVED early_stopping=True - not valid for greedy/sampling
                )
            
            # Decode response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new generated text
            new_text = full_response[len(formatted_input):].strip()
            
            # Clean up the response
            if new_text.startswith(":"):
                new_text = new_text[1:].strip()
            
            # Stop at natural breakpoints
            stop_sequences = ["\nHuman:", "\nUser:", "\n\n"]
            for stop in stop_sequences:
                if stop in new_text:
                    new_text = new_text.split(stop)[0].strip()
            
            return new_text if new_text else "I understand your question. Let me help you with that."
            
        except Exception as e:
            logger.error(f"Granite base model generation error: {e}")
            return "I apologize, but I encountered an error generating a response."
    
    def _build_system_prompt(self, persona: str, language: str, context: Dict = None) -> str:
        """Build persona-specific system prompt for financial guidance"""
        
        base_prompt = """You are a helpful, empathetic personal finance assistant. You provide clear, actionable advice on budgeting, debt management, savings, and basic investments.

IMPORTANT GUIDELINES:
- Always be supportive and encouraging
- Never guarantee specific financial returns
- For tax advice, always confirm assumptions about jurisdiction and filing status first
- Provide specific, actionable recommendations when possible
- Use examples relevant to the user's situation
- Be culturally sensitive and adapt to regional financial practices
- Keep responses concise and practical"""

        persona_adaptations = {
            "student": """
PERSONA: Student/Early Career
- Use simple, easy-to-understand language
- Focus on basics: budgeting, building credit, student loans, emergency funds
- Emphasize small wins and building good habits
- Reference student-specific scenarios""",
            
            "professional": """
PERSONA: Working Professional  
- Use more sophisticated financial terminology
- Assume familiarity with 401(k), tax-advantaged accounts, investment basics
- Be concise and data-driven in responses
- Focus on optimization and efficiency""",
            
            "family": """
PERSONA: Family Finance Manager
- Focus on family financial challenges and priorities
- Address multiple competing needs (childcare, education, housing)
- Be especially empathetic about financial stress
- Provide step-by-step, practical guidance"""
        }
        
        language_note = ""
        if language != "en":
            language_note = f"\nRespond in {language} language, using culturally appropriate financial terms and examples."
        
        context_note = ""
        if context:
            if context.get('has_budget_data'):
                context_note += "\n- User has uploaded budget data"
            if context.get('has_debt_data'):
                context_note += "\n- User has debt information"
            if context.get('has_goals'):
                context_note += "\n- User has set financial goals"
        
        return f"{base_prompt}\n\n{persona_adaptations.get(persona, persona_adaptations['student'])}{language_note}{context_note}"
    
    async def analyze_text(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Analyze text for intent, entities, sentiment, and emotion"""
        try:
            if len(text.strip()) == 0:
                return self._empty_analysis()
            
            # Extract intent using Granite
            intent = await self._extract_intent_with_granite_base(text)
            
            # Extract financial entities using simple methods (base model may be less reliable for structured tasks)
            entities = self._simple_entity_extraction(text)
            
            # Analyze sentiment using specialized model
            sentiment = self._analyze_sentiment(text)
            
            # Analyze emotion using specialized model
            emotion = self._analyze_emotion(text)
            
            # Extract keywords using simple NLP
            keywords = self._extract_keywords(text)
            
            return {
                "intent": intent,
                "entities": entities,
                "sentiment": sentiment,
                "emotion": emotion,
                "keywords": keywords
            }
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return self._empty_analysis()
    
    async def _extract_intent_with_granite_base(self, text: str) -> str:
        """Extract financial intent using Granite base model"""
        try:
            intent_prompt = f"""Classify this financial query into one category:
budget_analysis, debt_management, goal_planning, investment_advice, tax_guidance, insurance_planning, or general_chat

Query: "{text}"

Category:"""
            
            inputs = self.tokenizer(intent_prompt, return_tensors="pt", truncation=True, max_length=512).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=20,
                    temperature=0.3,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            new_text = response[len(intent_prompt):].strip().lower()
            
            # Extract the category from response
            categories = ['budget_analysis', 'debt_management', 'goal_planning', 'investment_advice', 
                         'tax_guidance', 'insurance_planning', 'general_chat']
            
            for category in categories:
                if category.replace('_', ' ') in new_text or category in new_text:
                    return category
            
            return 'general_chat'
            
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return 'general_chat'
    
    def _simple_entity_extraction(self, text: str) -> List[Dict]:
        """Simple regex-based entity extraction"""
        entities = []
        
        # Extract money amounts
        money_pattern = r'\$[\d,]+\.?\d*|\d+\.?\d*\s*(?:dollars?|USD|cents?)'
        for match in re.finditer(money_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": "MONEY",
                "confidence": 0.8
            })
        
        # Extract percentages
        percent_pattern = r'\d+\.?\d*\s*%|\d+\.?\d*\s*percent'
        for match in re.finditer(percent_pattern, text, re.IGNORECASE):
            entities.append({
                "text": match.group(),
                "type": "PERCENT", 
                "confidence": 0.8
            })
        
        return entities
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using specialized Hugging Face model"""
        try:
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(text)[0]
                
                label_map = {
                    'NEGATIVE': 'negative',
                    'POSITIVE': 'positive',
                    'NEUTRAL': 'neutral'
                }
                
                label = label_map.get(result['label'], 'neutral')
                score = result['score']
                
                if label == 'negative':
                    score = -score
                elif label == 'neutral':
                    score = 0.0
                
                return {"score": score, "label": label}
            else:
                return {"score": 0.0, "label": "neutral"}
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"score": 0.0, "label": "neutral"}
    
    def _analyze_emotion(self, text: str) -> Dict[str, float]:
        """Analyze emotion using specialized Hugging Face model"""
        try:
            if self.emotion_pipeline:
                results = self.emotion_pipeline(text)
                
                emotion_scores = {
                    "sadness": 0.0,
                    "joy": 0.0, 
                    "fear": 0.0,
                    "disgust": 0.0,
                    "anger": 0.0
                }
                
                for result in results:
                    emotion = result['label'].lower()
                    score = result['score']
                    
                    if emotion in emotion_scores:
                        emotion_scores[emotion] = score
                
                return emotion_scores
            else:
                return {"sadness": 0.0, "joy": 0.0, "fear": 0.0, "disgust": 0.0, "anger": 0.0}
                
        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
            return {"sadness": 0.0, "joy": 0.0, "fear": 0.0, "disgust": 0.0, "anger": 0.0}
    
    def _extract_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Simple keyword extraction"""
        import collections
        
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = collections.Counter([w for w in words if w not in stop_words])
        
        keywords = []
        for word, freq in word_freq.most_common(5):
            keywords.append({
                "text": word,
                "relevance": min(freq / len(words), 1.0) if words else 0.0
            })
        
        return keywords
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            "intent": "general_chat",
            "entities": [],
            "sentiment": {"score": 0.0, "label": "neutral"},
            "emotion": {"sadness": 0.0, "joy": 0.0, "fear": 0.0, "disgust": 0.0, "anger": 0.0},
            "keywords": []
        }

# Global instance
granite_huggingface_service = GraniteHuggingFaceService()
