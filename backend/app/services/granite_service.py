from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from typing import Dict, Any, List, Optional
import logging
import json
import re
from app.config import settings

logger = logging.getLogger(__name__)

class GraniteService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize Granite models from Hugging Face
        self.models = {}
        self.tokenizers = {}
        
        # Load main conversation model
        self.load_conversation_model()
        
        # Load sentiment analysis model
        self.load_sentiment_model()
        
        logger.info("Granite Service initialized successfully")
    
    def load_conversation_model(self):
        """Load Granite conversation model from Hugging Face"""
        try:
            model_name = "ibm-granite/granite-3.3-8b-instruct"
            
            logger.info(f"Loading conversation model: {model_name}")
            
            self.tokenizers['conversation'] = AutoTokenizer.from_pretrained(model_name)
            self.models['conversation'] = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True
            )
            
            if self.device == "cpu":
                self.models['conversation'].to(self.device)
                
            logger.info("Conversation model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load conversation model: {e}")
            # Fallback to smaller model
            try:
                model_name = "ibm-granite/granite-3.2-2b-instruct"
                logger.info(f"Falling back to smaller model: {model_name}")
                
                self.tokenizers['conversation'] = AutoTokenizer.from_pretrained(model_name)
                self.models['conversation'] = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    device_map=None
                )
                self.models['conversation'].to(self.device)
                
                logger.info("Fallback model loaded successfully")
                
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                raise
    
    def load_sentiment_model(self):
        """Load sentiment analysis model"""
        try:
            # Use Hugging Face sentiment pipeline with a reliable model
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
            
            # Also load emotion analysis
            self.emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Sentiment and emotion models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load sentiment models: {e}")
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
        """Generate AI response using Granite model"""
        try:
            # Build system prompt based on persona and language
            system_prompt = self._build_system_prompt(persona, language, context)
            
            # Format conversation for Granite
            formatted_prompt = self._format_conversation_for_granite(system_prompt, messages, reasoning)
            
            # Generate response
            response_text = await self._generate_with_granite(formatted_prompt)
            
            return {
                "text": response_text,
                "model_used": "granite-huggingface",
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
    
    async def analyze_text(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Analyze text for intent, entities, sentiment, and emotion using Granite + other models"""
        try:
            if len(text.strip()) == 0:
                return self._empty_analysis()
            
            # Extract intent using Granite
            intent = await self._extract_intent_with_granite(text)
            
            # Extract entities using Granite
            entities = await self._extract_entities_with_granite(text)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(text)
            
            # Analyze emotion
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
    
    def _build_system_prompt(self, persona: str, language: str, context: Dict = None) -> str:
        """Build persona-specific system prompt"""
        
        base_prompt = """You are a helpful, empathetic personal finance assistant. You provide clear, actionable advice on budgeting, debt management, savings, and basic investments.

IMPORTANT GUIDELINES:
- Always be supportive and encouraging
- Never guarantee specific financial returns
- For tax advice, always confirm assumptions about jurisdiction and filing status first
- Provide specific, actionable recommendations when possible
- Use examples relevant to the user's situation
- Be culturally sensitive and adapt to regional financial practices"""
        
        persona_adaptations = {
            "student": """
PERSONA: Student/Early Career
- Use simple, easy-to-understand language
- Focus on basics: budgeting, building credit, student loans, emergency funds
- Emphasize small wins and building good habits
- Reference student-specific scenarios (textbooks, dorm life, part-time jobs)
- Be encouraging about starting small""",
            
            "professional": """
PERSONA: Working Professional  
- Use more sophisticated financial terminology
- Assume familiarity with 401(k), tax-advantaged accounts, investment basics
- Be concise and data-driven in responses
- Focus on optimization and efficiency
- Reference career-specific scenarios (salary negotiation, job changes, benefits)""",
            
            "family": """
PERSONA: Family Finance Manager
- Focus on family financial challenges and priorities
- Address multiple competing needs (childcare, education, housing)
- Be especially empathetic about financial stress
- Provide step-by-step, practical guidance
- Reference family scenarios (school expenses, medical costs, family goals)
- Consider joint decision-making between partners"""
        }
        
        language_note = ""
        if language != "en":
            language_note = f"\nRespond in {language} language, using culturally appropriate financial terms and examples."
        
        context_note = ""
        if context:
            if context.get('has_budget_data'):
                context_note += "\n- User has uploaded budget data, reference their specific spending patterns"
            if context.get('has_debt_data'):
                context_note += "\n- User has debt information, provide specific payoff strategies"
            if context.get('has_goals'):
                context_note += "\n- User has set financial goals, help them stay on track"
        
        return f"{base_prompt}\n\n{persona_adaptations.get(persona, persona_adaptations['student'])}{language_note}{context_note}"
    
    def _format_conversation_for_granite(self, system_prompt: str, messages: List[Dict], reasoning: bool = False) -> str:
        """Format conversation for Granite model"""
        
        # Use Granite's chat template format
        conversation = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add recent messages
        for message in messages[-10:]:  # Keep last 10 messages
            conversation.append({
                "role": message.get("role", "user"),
                "content": message.get("content", "")
            })
        
        # Apply Granite's chat template
        tokenizer = self.tokenizers['conversation']
        formatted = tokenizer.apply_chat_template(
            conversation,
            tokenize=False,
            add_generation_prompt=True
        )
        
        return formatted
    
    async def _generate_with_granite(self, formatted_prompt: str) -> str:
        """Generate text using Granite model"""
        try:
            tokenizer = self.tokenizers['conversation']
            model = self.models['conversation']
            
            # Tokenize input
            inputs = tokenizer(
                formatted_prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=4096
            ).to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            # Decode response
            full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new generated text
            new_text = full_response[len(formatted_prompt):].strip()
            
            return new_text
            
        except Exception as e:
            logger.error(f"Granite generation error: {e}")
            return "I apologize, but I encountered an error generating a response."
    
    async def _extract_intent_with_granite(self, text: str) -> str:
        """Extract financial intent using Granite model"""
        try:
            intent_prompt = f"""Classify the following financial query into one of these categories:
- budget_analysis: questions about spending, budgeting, expense tracking
- debt_management: questions about debt payoff, loans, credit cards
- goal_planning: questions about saving, financial goals, target planning  
- investment_advice: questions about investing, portfolios, retirement accounts
- tax_guidance: questions about taxes, deductions, tax planning
- insurance_planning: questions about insurance, coverage, protection
- general_chat: general conversation or unclear financial intent

Query: "{text}"

Category:"""
            
            tokenizer = self.tokenizers['conversation']
            model = self.models['conversation']
            
            inputs = tokenizer(intent_prompt, return_tensors="pt", truncation=True, max_length=512).to(self.device)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=50,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the category from response
            categories = ['budget_analysis', 'debt_management', 'goal_planning', 'investment_advice', 
                         'tax_guidance', 'insurance_planning', 'general_chat']
            
            response_lower = response.lower()
            for category in categories:
                if category.replace('_', ' ') in response_lower or category in response_lower:
                    return category
            
            return 'general_chat'
            
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return 'general_chat'
    
    async def _extract_entities_with_granite(self, text: str) -> List[Dict]:
        """Extract financial entities using Granite model"""
        try:
            entity_prompt = f"""Extract financial entities from this text and format as JSON:
Text: "{text}"

Find these entity types:
- MONEY: dollar amounts, currencies
- PERCENT: percentages, interest rates
- DATE: dates, time periods
- ORG: banks, financial institutions
- PRODUCT: financial products (loans, cards, accounts)

Format as JSON array: [{{"text": "entity", "type": "TYPE", "confidence": 0.9}}]

JSON:"""
            
            tokenizer = self.tokenizers['conversation']
            model = self.models['conversation']
            
            inputs = tokenizer(entity_prompt, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.3,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Try to extract JSON from response
            try:
                # Find JSON in response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    entities = json.loads(json_str)
                    return entities if isinstance(entities, list) else []
            except:
                pass
            
            # Fallback: simple regex-based entity extraction
            return self._simple_entity_extraction(text)
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return self._simple_entity_extraction(text)
    
    def _simple_entity_extraction(self, text: str) -> List[Dict]:
        """Simple fallback entity extraction"""
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
        """Analyze sentiment using Hugging Face model"""
        try:
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(text)[0]
                
                # Convert to Watson-like format
                label_map = {
                    'NEGATIVE': 'negative',
                    'POSITIVE': 'positive',
                    'NEUTRAL': 'neutral'
                }
                
                label = label_map.get(result['label'], 'neutral')
                score = result['score']
                
                # Convert score to range [-1, 1]
                if label == 'negative':
                    score = -score
                elif label == 'neutral':
                    score = 0.0
                
                return {
                    "score": score,
                    "label": label
                }
            else:
                return {"score": 0.0, "label": "neutral"}
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {"score": 0.0, "label": "neutral"}
    
    def _analyze_emotion(self, text: str) -> Dict[str, float]:
        """Analyze emotion using Hugging Face model"""
        try:
            if self.emotion_pipeline:
                results = self.emotion_pipeline(text)
                
                # Convert to Watson-like format
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
        # Simple TF-IDF based keyword extraction
        import collections
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = collections.Counter([w for w in words if w not in stop_words])
        
        keywords = []
        for word, freq in word_freq.most_common(5):
            keywords.append({
                "text": word,
                "relevance": min(freq / len(words), 1.0)
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
granite_service = GraniteService()
