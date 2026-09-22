import json
import os
import sys
import numpy as np

try:
    import spacy
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
except ImportError:
    print("❌ Critical missing libraries for NLP Engine. Run: pip install scikit-learn spacy numpy")
    print("❌ And don't forget the model: python -m spacy download en_core_web_sm")
    sys.exit(1)

class NLPEngine:
    def __init__(self, data_path="data/intents.json", logger=None):
        self.logger = logger
        self.data_path = data_path
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        self.classifier = LinearSVC(C=1.0, dual="auto")
        self.intents_data = None
        self.is_trained = False
        
        # Load SpaCy for NER (Named Entity Recognition)
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self._log_info("✅ SpaCy English model loaded successfully.")
        except OSError:
            self._log_error("❌ SpaCy model 'en_core_web_sm' not found. Will not be able to do NER.")
            self._log_error("Run: python -m spacy download en_core_web_sm")
            self.nlp = None

        self.train_model()

    def _log_info(self, msg):
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)

    def _log_error(self, msg):
        if self.logger:
            self.logger.error(msg)
        else:
            print(msg)

    def train_model(self):
        """Load intents.json and train the linear SVM classifier."""
        if not os.path.exists(self.data_path):
            self._log_error(f"❌ Intents database not found at {self.data_path}")
            return False

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.intents_data = json.load(f)["intents"]
        except Exception as e:
            self._log_error(f"❌ Error loading intents JSON: {e}")
            return False

        corpus = []
        tags = []

        for intent in self.intents_data:
            tag = intent["tag"]
            for pattern in intent["patterns"]:
                # Simple preprocessing could be added here
                corpus.append(pattern.lower())
                tags.append(tag)

        if not corpus:
            self._log_error("❌ Empty training corpus.")
            return False

        # Fit TF-IDF and Train Classifier
        try:
            X = self.vectorizer.fit_transform(corpus)
            self.classifier.fit(X, tags)
            self.is_trained = True
            
            # Keep array of class labels for confidence scores later if needed
            self.classes_ = self.classifier.classes_
            
            self._log_info(f"✅ NLP Intent Classifier trained on {len(corpus)} examples across {len(self.classes_)} intents.")
            return True
        except Exception as e:
            self._log_error(f"❌ Failed to train NLP Classifier: {e}")
            return False

    def predict_intent(self, text):
        """Predict the intent of a given text."""
        if not self.is_trained:
            self._log_error("❌ Cannot predict. Model is not trained.")
            return {"intent": "unknown", "confidence": 0.0}

        text = text.lower().strip()
        if not text:
            return {"intent": "unknown", "confidence": 0.0}

        # Transform text and predict
        try:
            X_test = self.vectorizer.transform([text])
            
            # Since LinearSVC doesn't output probabilities by default, we use decision_function
            decision_scores = self.classifier.decision_function(X_test)[0]
            
            if len(self.classes_) == 2:
                # Binary classification
                idx = 1 if decision_scores > 0 else 0
                max_score = abs(decision_scores)
            else:
                # Multiclass
                idx = np.argmax(decision_scores)
                max_score = decision_scores[idx]
            
            tag = self.classes_[idx]
            
            # Normalize the decision score roughly to a pseudo-confidence [0, 1]
            # Adjust this threshold logic based on how LinearSVC scales in practice
            confidence = min(0.99, max(0.0, float(max_score)))
            if confidence < 0.2:
                 confidence = confidence * 2 # boost small scores slightly for UI

            # If the best score is less than a small threshold, consider it unknown
            if max_score < 0.15:
                # Way too uncertain
                return {"intent": "unknown", "confidence": 0.1}

            return {
                "intent": tag,
                "confidence": confidence
            }
        except Exception as e:
            self._log_error(f"❌ Prediction error: {e}")
            return {"intent": "unknown", "confidence": 0.0}

    def extract_entities(self, text):
        """Use SpaCy to extract entities (like PERSON, GPE, DATE, ORG) from text."""
        entities = {}
        if not self.nlp:
            return entities
            
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            if ent.text not in entities[ent.label_]:
               entities[ent.label_].append(ent.text)
               
        return entities

    def analyze(self, text):
        """Full analysis pipeline: intent prediction + NER."""
        result = self.predict_intent(text)
        result["entities"] = self.extract_entities(text)
        return result

if __name__ == "__main__":
    # Test script
    print("="*50)
    print("Testing NLP Engine...")
    print("="*50)
    engine = NLPEngine("../data/intents.json")
    
    test_phrases = [
        "turn it up man",
        "make the screen darker",
        "wish a happy birthday to rajesh kumar",
        "what is the weather like in mumbai today",
        "some random garbage text dfskdsfksdnf",
        "how many commands have i given"
    ]
    
    for phrase in test_phrases:
        print(f"\n📝 Phrase: '{phrase}'")
        analysis = engine.analyze(phrase)
        print(f"🎯 Predicted Intent: {analysis['intent']} (Conf: {analysis['confidence']:.2f})")
        if analysis['entities']:
            print(f"🔍 Extracted Entities: {analysis['entities']}")
