"""
Web UI Plugin for KF Searcher
Flask-based web interface similar to VS5
"""

from .app import create_app

__all__ = ['create_app']
