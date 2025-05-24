class ChatbotError(Exception):
    """خطای پایه برای چت‌بات"""
    pass

class APIError(ChatbotError):
    """خطای API"""
    pass

class ModelError(ChatbotError):
    """خطای مدل"""
    pass

class DatabaseError(ChatbotError):
    """خطای دیتابیس"""
    pass

class CrawlerError(ChatbotError):
    """خطای کراولر"""
    pass

class EmbeddingError(ChatbotError):
    """خطای امبدینگ"""
    pass

class SearchError(ChatbotError):
    """خطای جستجو"""
    pass

class PromptError(ChatbotError):
    """خطای پرامپت"""
    pass 