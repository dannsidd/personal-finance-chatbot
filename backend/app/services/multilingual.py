from transformers import pipeline, AutoTokenizer, AutoModel
from typing import Dict, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

class MultilingualService:
    def __init__(self):
        try:
            # Language detection
            self.language_detector = pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection"
            )
            
            # Translation models for Indian languages
            self.translators = {
                'hi': None,  # Hindi
                'ta': None,  # Tamil
                'te': None,  # Telugu
                'bn': None,  # Bengali
                'gu': None,  # Gujarati
                'mr': None,  # Marathi
            }
            
            # Load translation models on demand
            self.model_mapping = {
                'hi': 'Helsinki-NLP/opus-mt-en-hi',
                'ta': 'Helsinki-NLP/opus-mt-en-ta',
                'te': 'Helsinki-NLP/opus-mt-en-te',
                'bn': 'Helsinki-NLP/opus-mt-en-bn',
                'gu': 'Helsinki-NLP/opus-mt-en-gu',
                'mr': 'Helsinki-NLP/opus-mt-en-mr'
            }
            
            logger.info("Multilingual service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize multilingual service: {e}")
            self.language_detector = None
            self.translators = {}
    
    async def detect_language(self, text: str) -> Dict:
        """Detect language of input text"""
        try:
            if not self.language_detector or not text.strip():
                return {"language": "en", "confidence": 1.0}
            
            result = self.language_detector(text)
            
            # Extract the most confident prediction
            if isinstance(result, list) and len(result) > 0:
                prediction = result[0]
                detected_lang = prediction.get('label', 'en')
                confidence = prediction.get('score', 0.0)
                
                # Map detected language to our supported languages
                supported_languages = {
                    'en': 'en', 'hindi': 'hi', 'tamil': 'ta', 'telugu': 'te',
                    'bengali': 'bn', 'gujarati': 'gu', 'marathi': 'mr',
                    'spanish': 'es', 'french': 'fr'
                }
                
                mapped_lang = supported_languages.get(detected_lang.lower(), 'en')
                
                return {
                    "language": mapped_lang,
                    "confidence": confidence,
                    "original_detection": detected_lang
                }
            
            return {"language": "en", "confidence": 1.0}
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {"language": "en", "confidence": 1.0}
    
    async def translate_to_english(self, text: str, source_language: str) -> str:
        """Translate text from source language to English"""
        try:
            if source_language == 'en' or not text.strip():
                return text
            
            # Load translator if not already loaded
            if source_language not in self.translators or self.translators[source_language] is None:
                await self._load_translator(source_language)
            
            translator = self.translators.get(source_language)
            if translator is None:
                logger.warning(f"No translator available for {source_language}, returning original text")
                return text
            
            # Translate to English
            translated = translator(text)
            if isinstance(translated, list) and len(translated) > 0:
                return translated[0].get('translation_text', text)
            
            return text
            
        except Exception as e:
            logger.error(f"Translation to English failed: {e}")
            return text  # Return original text as fallback
    
    async def translate_from_english(self, text: str, target_language: str) -> str:
        """Translate text from English to target language"""
        try:
            if target_language == 'en' or not text.strip():
                return text
            
            # Load reverse translator if available
            reverse_model = self.model_mapping.get(target_language, '').replace('en-', f'{target_language}-').replace(f'-{target_language}', '-en')
            
            # For now, return English text with language marker
            # In production, implement proper reverse translation
            return text
            
        except Exception as e:
            logger.error(f"Translation from English failed: {e}")
            return text
    
    async def _load_translator(self, language_code: str):
        """Load translation model for specific language"""
        try:
            model_name = self.model_mapping.get(language_code)
            if model_name:
                # Load model in background to avoid blocking
                translator = pipeline("translation", model=model_name)
                self.translators[language_code] = translator
                logger.info(f"Loaded translator for {language_code}")
            else:
                logger.warning(f"No translation model available for {language_code}")
                
        except Exception as e:
            logger.error(f"Failed to load translator for {language_code}: {e}")
            self.translators[language_code] = None
    
    def get_cultural_context(self, language: str) -> Dict:
        """Get cultural context for financial advice"""
        cultural_contexts = {
            'hi': {
                'currency': 'INR',
                'festivals': ['Diwali', 'Holi', 'Eid'],
                'investment_options': ['PPF', 'EPF', 'NSC', 'ELSS', 'FD'],
                'banking_terms': ['Chit Fund', 'SHG', 'Cooperative Bank'],
                'family_structure': 'Joint Family'
            },
            'ta': {
                'currency': 'INR',
                'festivals': ['Pongal', 'Diwali'],
                'regional_focus': 'South India',
                'investment_options': ['PPF', 'EPF', 'Gold'],
                'family_structure': 'Joint Family'
            },
            'te': {
                'currency': 'INR',
                'festivals': ['Ugadi', 'Dussehra'],
                'regional_focus': 'Andhra Pradesh/Telangana',
                'investment_options': ['PPF', 'EPF', 'Real Estate'],
                'family_structure': 'Joint Family'
            }
        }
        
        return cultural_contexts.get(language, {
            'currency': 'USD',
            'festivals': [],
            'investment_options': ['401k', 'IRA', 'Stocks'],
            'family_structure': 'Nuclear Family'
        })

# Global instance
multilingual_service = MultilingualService()

