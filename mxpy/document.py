class Document:
    def __init__(self):
        self._content = None
        self._listeners = []

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value
        self._notify_listeners()

    def add_listener(self, callback):
        self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback is None:
            self._listeners.clear()
        elif callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self):
        for listener in self._listeners:
            listener(self._content)