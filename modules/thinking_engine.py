# modules/thinking_engine.py - The "Brain" of AI Assistent Assistant

import re
import os
import sys
from datetime import datetime
import wikipedia

class ThinkingEngine:
    def __init__(self, db_manager=None):
        self.db = db_manager

        
        # Intent Categories
        self.INTENT_MAP = {
            'query': ['what', 'who', 'where', 'how', 'when', 'tell', 'search', 'find'],
            'action': ['open', 'start', 'run', 'delete', 'remove', 'clean', 'capture', 'set'],
            'memory': ['remember', 'save', 'store', 'recall', 'forget'],
            'conversational': ['hello', 'hi', 'hey', 'how are you', 'good morning', 'thanks', 'bye']
        }

    def analyze(self, text):
        """
        Think about the user input and decide the best course of action.
        Returns: { 'intent_type': str, 'entities': list, 'action_plan': str, 'confidence': float }
        """
        text = text.lower().strip()
        print(f"🧠 AI Assistent is thinking about: '{text}'...")
        
        # 1. Decision Logic: What is the main intent?
        intent_type = self._detect_intent_group(text)
        
        # 2. Entity Extraction: Who/What are we talking about?
        entities = self._extract_basic_entities(text)
        
        # 3. Action Plan: How to solve this?
        action_plan, response = self._create_action_plan(intent_type, text, entities)
        
        return {
            'intent_type': intent_type,
            'entities': entities,
            'action_plan': action_plan,
            'response': response,
            'confidence': 0.9
        }

    def _detect_intent_group(self, text):
        """Categorize the sentence into high-level groups (DYNAMMICALY)"""
        # 1. Action Words
        if any(word in text for word in self.INTENT_MAP['action']):
            return 'system_action'
            
        # 2. Memory Words
        if any(word in text for word in self.INTENT_MAP['memory']):
            return 'memory_operation'
            
        # 3. Conversational Words
        if any(word in text for word in ['hello', 'hi', 'hey', 'thanks', 'bye']):
            return 'conversational'
            
        # 4. If nothing else, treat it as a potential Knowledge Query (DYNAMIC)
        # Any sentence longer than 2 words that isn't a greeting/action is likely a query
        if len(text.split()) >= 2:
            return 'knowledge_query'
            
        return 'conversational'

    def _extract_basic_entities(self, text):
        """Identify main objects in the sentence (Dynamic Extraction)"""
        entities = []
        
        # Stop words to clean the query
        stop_words = ['is', 'a', 'the', 'an', 'what', 'who', 'tell', 'me', 'about', 'search', 'find', 'for', 'please', 'know']
        
        # Split text into words
        words = text.split()
        
        # Filter out common stop words and keep the "Topic"
        topic_words = [w for w in words if w not in stop_words]
        
        if topic_words:
            topic = " ".join(topic_words)
            entities.append({'type': 'topic', 'value': topic})

        return entities

    def _create_action_plan(self, intent_type, text, entities):
        """Decide the next step and generate an initial response"""
        if intent_type == 'knowledge_query':
            topic = entities[0]['value'] if entities else text
            print(f"📖 AI Assistent Brain is researching '{topic}' on Wikipedia...")
            try:
                summary = wikipedia.summary(topic, sentences=2, auto_suggest=True)
                return "INTERNAL_DB_SEARCH_FALLBACK_TO_WEB", f"Boss, I found this on Wikipedia: {summary}"
            except wikipedia.exceptions.DisambiguationError as e:
                options = e.options[:2]
                return "INTERNAL_DB_SEARCH_FALLBACK_TO_WEB", f"Wikipedia has multiple entries for '{topic}'. Did you mean {options[0]} or {options[1]}?"
            except:
                return "INTERNAL_DB_SEARCH_FALLBACK_TO_WEB", f"Boss, I tried to research '{topic}' but I couldn't find a clear answer."
            
        if intent_type == 'system_action':
            app = entities[0]['value'] if entities else "unknown"
            return "EXECUTE_SYSTEM_COMMAND", f"Boss, I understood you want to run a system action for '{app}', but I need to learn this command pattern first."
            
        if intent_type == 'memory_operation':
            return "STORE_IN_KNOWLEDGE_BASE", "OK boss! I'm storing that in my head right now."
            
        # For conversational intents, give a friendly reply
        responses = [
            "I'm thinking about what you said, boss!",
            "Got it! What would you like to do next?",
            "Boss, tell me more about that!",
            "I'm listening and learning from you!"
        ]
        import random
        return "GENERATE_HUMAN_RESPONSE", random.choice(responses)

    def confirm_action(self, action_description):
        """Logic to decide if we need to ask the user before proceeding"""
        sensitive_actions = ['delete', 'remove', 'shutdown', 'format', 'clear']
        if any(word in action_description.lower() for word in sensitive_actions):
            return True
        return False

# Example Usage Test
if __name__ == "__main__":
    brain = ThinkingEngine()
    test_inputs = [
        "What is the capital of India?",
        "Please open Notepad for me",
        "Remember that my birthday is in July",
        "Hello AI Assistent, how are you today?"
    ]
    
    for inp in test_inputs:
        result = brain.analyze(inp)
        print(f"Input: {inp}")
        print(f"Result: {result}\n")
