from django.utils.deprecation import MiddlewareMixin

from .storage import Storage


class WidgetsMiddleware(MiddlewareMixin):
    """
    Middleware that handles view's widgets.
    """

    def process_request(self, request):
        request._widgets = Storage()
