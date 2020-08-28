from .storage import Storage

__all__ = (
    'add_widget', 'get_widgets',
    'WidgetFailure',
)


class WidgetFailure(Exception):
    pass


def add_widget(request, name, widget, fail_silently=False):
    """
    Attempt to add a widget to the request using the 'widgets' app.
    """
    try:
        widgets: Storage = request._widgets
    except AttributeError:
        if not hasattr(request, 'META'):
            raise TypeError(
                "add_widget() argument must be an HttpRequest object, not "
                "'%s'." % request.__class__.__name__
            )
        if not fail_silently:
            raise WidgetFailure(
                'You cannot add widgets without installing '
                'django_widgets.widgets.middleware.WidgetsMiddleware'
            )
    else:
        return widgets.add(name, widget)


def get_widgets(request) -> Storage:
    """
    Return the widgets storage on the request if it exists, otherwise return
    an empty dict.
    """
    return getattr(request, '_widgets', Storage())
