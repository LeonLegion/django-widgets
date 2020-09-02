from jinja2.ext import Extension, nodes
from django.utils.html import conditional_escape

from ..api import get_widgets
from ..renderers import Jinja2EnvironmentRenderer


class WidgetExtension(Extension):
    tags = {"widget", "widgetattrs", "widgetmedia"}

    def parse(self, parser):
        token = next(parser.stream)
        context = nodes.ContextReference()
        if token.value == "widget":
            args = [context, parser.parse_expression()]
            result = self.call_method("_render_widget", args, lineno=token.lineno)
        elif token.value == "widgetattrs":
            args = [context]
            result = self.call_method("_render_widgetattrs", args, lineno=token.lineno)
        elif token.value == "widgetmedia":
            args = [context]
            result = self.call_method("_render_widgetmedia", args, lineno=token.lineno)

        return nodes.Output([result], lineno=token.lineno)

    def _render_widget(self, context, name):
        request = context.get('request')
        storage = get_widgets(request)

        if not storage.has(name):
            return ''

        data = dict()
        d = {}
        # if kwargs is not None:
        #     for key, value in kwargs.items():
        #         d[key] = value
        # if attrs is not None:
        #     d.update(attrs)

        return storage.get(name).render(name, data=data, attrs=d, request=request, renderer=Jinja2EnvironmentRenderer(self.environment))

    def _render_widgetattrs(self, context):
        d = {}
        # if kwargs is not None:
        #     for key, value in kwargs.items():
        #         d[key] = value
        # if attrs is not None:
        #     d.update(attrs)
        # if 'widget' in context and 'attrs' in context['widget']:
        #     d.update(context['widget']['attrs'])

        result = []
        for key, value in d.items():
            if value is not None and value is not False:
                if value == '' or value is True:
                    result.append(key)
                else:
                    result.append(key + '="' + conditional_escape(value) + '"')

        return ' '.join(result)

    def _render_widgetattrs(self, context):
        return ''
