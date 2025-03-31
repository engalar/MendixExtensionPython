"""
Context module for Mendix Studio Pro Python API.
"""

_active_document = "hello mxpy"
_listeners = []

def add_listener(callback):
    """
    Register a callback function to be called when activeDocument changes.
    
    Args:
        callback: A function that will be called with the new document value.
    """
    _listeners.append(callback)

def remove_listener(callback):
    """
    Unregister a previously registered callback function.
    
    Args:
        callback: The function to remove from listeners.
    """
    if callback in _listeners:
        _listeners.remove(callback)

def _notify_listeners(new_value):
    """
    Notify all registered listeners about a change in activeDocument.
    
    Args:
        new_value: The new value of activeDocument.
    """
    for listener in _listeners:
        listener(new_value)

@property
def activeDocument():
    """Get the current active document."""
    return _active_document

@activeDocument.setter
def activeDocument(self, value):
    """
    Set the active document and notify all listeners of the change.
    
    Args:
        value: The new active document value.
    """
    global _active_document
    if _active_document != value:
        _active_document = value
        _notify_listeners(value)