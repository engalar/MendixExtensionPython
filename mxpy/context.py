"""
Context module for Mendix Studio Pro Python API.
"""

from .document import Document

activeDocument = Document()

currentApp = None
root = None