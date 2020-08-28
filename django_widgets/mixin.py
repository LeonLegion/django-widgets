from .api import add_widget, get_widgets
from .middleware import WidgetsMiddleware


class MultiWidgetMixin:

    def _init_request(self, request):
        request = super()._init_request(request)
        self._request_widgets = {
            'absent': [],
            'stored': {}
        }
        if not request:
            request = {}  # What kind must be dump request???
            middle = WidgetsMiddleware()
            middle(request)
        return request

    def _reset_request(self, request):
        storage = get_widgets(request)
        for name in self._request_widgets['absent']:
            storage.pop(name)
        for name in self._request_widgets['stored']:
            storage.add(name, self._request_widgets['stored'][name])
        super()._reset_request(request)

    def add_widget(self, request, name, widget, fail_silently=False):
        storage = get_widgets(request)
        if storage.has(name):
            if name not in self._request_widgets['stored']:
                self._request_widgets['stored'][name] = storage.get(name)
        else:
            self._request_widgets['absent'].append(name)

        add_widget(request, name, widget, fail_silently=fail_silently)
