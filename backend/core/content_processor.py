import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from collections import Counter
from typing import List, Dict, Tuple
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class TextProcessor:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
            
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.tfidf = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )

    def process_text(self, text: str) -> Dict:
        """Process text and return structured data"""
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Tokenize
        sentences = sent_tokenize(cleaned_text)
        words = word_tokenize(cleaned_text.lower())
        
        # Remove stopwords and lemmatize
        processed_words = [
            self.lemmatizer.lemmatize(word)
            for word in words
            if word.isalnum() and word not in self.stop_words
        ]
        
        # Extract keywords
        keywords = self._extract_keywords(processed_words)
        
        # Generate summary
        summary = self._generate_summary(sentences)
        
        # Categorize content
        category = self._categorize_content(cleaned_text)
        
        return {
            'cleaned_text': cleaned_text,
            'sentences': sentences,
            'keywords': keywords,
            'summary': summary,
            'category': category,
            'word_count': len(processed_words),
            'sentence_count': len(sentences)
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s.]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_keywords(self, words: List[str], top_n: int = 10) -> List[Tuple[str, float]]:
        """Extract keywords using TF-IDF"""
        if not words:
            return []
            
        # Create document for TF-IDF
        doc = ' '.join(words)
        
        # Fit and transform
        tfidf_matrix = self.tfidf.fit_transform([doc])
        
        # Get feature names and scores
        feature_names = self.tfidf.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        # Get top keywords
        top_indices = np.argsort(scores)[-top_n:][::-1]
        keywords = [(feature_names[i], scores[i]) for i in top_indices]
        
        return keywords

    def _generate_summary(self, sentences: List[str], max_sentences: int = 3) -> str:
        """Generate a summary using extractive method"""
        if not sentences:
            return ""
            
        # Create document for TF-IDF
        doc = ' '.join(sentences)
        
        # Fit and transform
        tfidf_matrix = self.tfidf.fit_transform(sentences)
        
        # Calculate sentence scores
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            score = np.mean(tfidf_matrix[i].toarray())
            sentence_scores.append((i, score))
        
        # Get top sentences
        top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:max_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Sort by original order
        
        # Combine sentences
        summary = ' '.join(sentences[i] for i, _ in top_sentences)
        return summary

    def _categorize_content(self, text: str) -> str:
        """Categorize content based on keywords and patterns"""
        text = text.lower()
        
        # Define category patterns
        categories = {
            'product': ['product', 'service', 'price', 'buy', 'purchase', 'order'],
            'about': ['about', 'company', 'team', 'history', 'mission', 'vision'],
            'contact': ['contact', 'address', 'phone', 'email', 'location'],
            'blog': ['blog', 'article', 'post', 'news', 'update'],
            'faq': ['faq', 'question', 'answer', 'help', 'support']
        }
        
        # Count category matches
        category_scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        return 'other'

    def process_batch(self, texts: List[str]) -> List[Dict]:
        """Process a batch of texts"""
        return [self.process_text(text) for text in texts] 