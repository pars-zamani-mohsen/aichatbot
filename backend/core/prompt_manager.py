from typing import Dict, List
import logging
import re

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self):
        self.query_types = {
            'general': self._general_prompt,
            'product': self._product_prompt,
            'support': self._support_prompt,
            'technical': self._technical_prompt,
            'pricing': self._pricing_prompt
        }

    def detect_query_type(self, query: str) -> str:
        """Detect the type of query based on keywords and patterns"""
        query = query.lower()
        
        # Define category patterns in Persian
        patterns = {
            'product': ['محصول', 'خدمات', 'قیمت', 'خرید', 'سفارش', 'ویژگی', 'مشخصات'],
            'support': ['مشکل', 'خطا', 'راهنما', 'پشتیبانی', 'کمک', 'راهنمایی'],
            'technical': ['نصب', 'تنظیمات', 'پیکربندی', 'تکنیکی', 'فنی'],
            'pricing': ['هزینه', 'قیمت', 'تعرفه', 'پلن', 'طرح', 'اشتراک']
        }
        
        # Count matches for each category
        scores = {}
        for category, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in query)
            scores[category] = score
        
        # Return category with highest score, or 'general' if no clear match
        if scores:
            max_category = max(scores.items(), key=lambda x: x[1])
            if max_category[1] > 0:
                return max_category[0]
        return 'general'

    def get_prompt(self, query: str, context: str, query_type: str = 'general') -> str:
        """Generate appropriate prompt based on query type"""
        if query_type in self.query_types:
            return self.query_types[query_type](query, context)
        return self._general_prompt(query, context)

    def _general_prompt(self, query: str, context: str) -> str:
        """Generate prompt for general queries"""
        return f"""Based on the following information, please answer the user's question in Persian.
If the information is not sufficient to provide a complete answer, please say so honestly.

Context:
{context}

Question: {query}

Please provide a clear and helpful response in Persian, using natural and conversational language.
If you use information from specific sources, cite them using [n] where n is the source number."""

    def _product_prompt(self, query: str, context: str) -> str:
        """Generate prompt for product-related queries"""
        return f"""Based on the following product information, please answer the user's question in Persian.
Focus on providing accurate product details, features, and specifications.

Context:
{context}

Question: {query}

Please provide a detailed response about the product in Persian, using natural and conversational language.
If you use information from specific sources, cite them using [n] where n is the source number."""

    def _support_prompt(self, query: str, context: str) -> str:
        """Generate prompt for support-related queries"""
        return f"""Based on the following support information, please help the user with their issue in Persian.
Focus on providing clear, step-by-step solutions and troubleshooting steps.

Context:
{context}

Question: {query}

Please provide a helpful and supportive response in Persian, using natural and conversational language.
If you use information from specific sources, cite them using [n] where n is the source number."""

    def _technical_prompt(self, query: str, context: str) -> str:
        """Generate prompt for technical queries"""
        return f"""Based on the following technical information, please answer the user's question in Persian.
Focus on providing accurate technical details and implementation steps.

Context:
{context}

Question: {query}

Please provide a technical response in Persian, using natural and conversational language.
If you use information from specific sources, cite them using [n] where n is the source number."""

    def _pricing_prompt(self, query: str, context: str) -> str:
        """Generate prompt for pricing-related queries"""
        return f"""Based on the following pricing information, please answer the user's question in Persian.
Focus on providing clear and accurate pricing details, plans, and options.

Context:
{context}

Question: {query}

Please provide a detailed response about pricing in Persian, using natural and conversational language.
If you use information from specific sources, cite them using [n] where n is the source number."""