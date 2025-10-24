"""Middleware d'intégration pour FastAPI"""
from .fastapi_middleware import LearningMiddleware, get_learning_middleware

__all__ = ['LearningMiddleware', 'get_learning_middleware']
