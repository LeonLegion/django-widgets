from .widget import Widget, Media


class Storage:

    def __init__(self):
        self._widgets = dict()

    def has(self, name):
        return name in self._widgets

    def add(self, name, widget):
        if not isinstance(widget, Widget):
            raise TypeError(
                "Storage.set() argument must be an Widget object, not "
                "'%s'." % widget.__class__.__name__
            )
        self._widgets[name] = widget

    def get(self, *args, **kwargs) -> Widget:
        """ Return the value for key if key is in the dictionary, else default. """
        return self._widgets.get(*args, **kwargs)

    def pop(self, key):
        return self._widgets.pop(key, None)

    @property
    def media(self):
        media = Media()
        for name in self._widgets:
            media += self._widgets[name].media
        return media
