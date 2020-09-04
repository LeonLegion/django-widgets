from django.utils.safestring import mark_safe
from jinja2.lexer import TOKEN_NAME, TOKEN_EQ, TOKEN_ASSIGN, TOKEN_SUB, TOKEN_STRING, TOKEN_BLOCK_END
from jinja2.ext import Extension, nodes
from django.utils.html import conditional_escape
from jinja2.nodes import Keyword

from ..api import get_widgets
from ..renderers import Jinja2EnvironmentRenderer


class WidgetExtension(Extension):
    tags = {"widget", "widgetattrs", "widgetmedia"}

    def parse(self, parser):
        token = next(parser.stream)
        context = nodes.ContextReference()
        if token.value == "widget":
            args = [context, parser.parse_expression()]
            kwargs = []
            name = parser.stream.next_if(TOKEN_NAME)
            while name:
                key = name.value
                # while parser.stream.current.test(TOKEN_SUB):
                #     key += parser.stream.next_if(TOKEN_SUB).value
                #     name = parser.stream.next_if(TOKEN_NAME)
                #     if name:
                #         key += name.value
                parser.stream.skip_if(TOKEN_ASSIGN)
                if parser.stream.current.test(TOKEN_NAME) or parser.stream.current.test(TOKEN_BLOCK_END):
                    value = nodes.Const('')
                else:
                    value = parser.parse_expression()
                kwargs.append(Keyword(key, value))
                name = parser.stream.next_if(TOKEN_NAME)
            result = self.call_method("_render_widget", args, kwargs, lineno=token.lineno)
        elif token.value == "widgetattrs":
            args = [context]
            kwargs = []
            name = parser.stream.next_if(TOKEN_NAME)
            while name:
                key = name.value
                # while parser.stream.current.test(TOKEN_SUB):
                #     key += parser.stream.next_if(TOKEN_SUB).value
                #     name = parser.stream.next_if(TOKEN_NAME)
                #     if name:
                #         key += name.value
                parser.stream.skip_if(TOKEN_ASSIGN)
                if parser.stream.current.test(TOKEN_NAME) or parser.stream.current.test(TOKEN_BLOCK_END):
                    value = nodes.Const('')
                else:
                    value = parser.parse_expression()
                kwargs.append(Keyword(key, value))
                name = parser.stream.next_if(TOKEN_NAME)

            result = self.call_method("_render_widgetattrs", args, kwargs, lineno=token.lineno)
        elif token.value == "widgetmedia":
            args = [context]
            while not parser.stream.current.test(TOKEN_NAME) and not parser.stream.current.test(TOKEN_BLOCK_END):
                args.append(parser.parse_expression())
            kwargs = []
            while parser.stream.current.test(TOKEN_NAME):
                name = next(parser.stream)
                parser.stream.skip_if(TOKEN_ASSIGN)
                kwargs.append(Keyword(name.value, parser.parse_expression()))

            result = self.call_method("_render_widgetmedia", args, kwargs, lineno=token.lineno)

        return nodes.Output([result], lineno=token.lineno)

    def _render_widget(self, context, name, data=None, attrs=None, **kwargs):
        request = context.get('request')
        storage = get_widgets(request)

        if not storage.has(name):
            return ''

        d = {}
        if kwargs is not None:
            for key, value in kwargs.items():
                d[key] = value
        if attrs is not None:
            d.update(attrs)

        return storage.get(name).render(name, data=data, attrs=d, request=request, renderer=Jinja2EnvironmentRenderer(self.environment))

    def _render_widgetattrs(self, context, attrs=None, **kwargs):
        d = {}
        if kwargs is not None:
            for key, value in kwargs.items():
                d[key] = value
        if attrs is not None:
            d.update(attrs)
        if 'widget' in context and 'attrs' in context['widget']:
            d.update(context['widget']['attrs'])

        result = []
        for key, value in d.items():
            if value is not None and value is not False:
                result.append(key if value == '' or value is True else key + '="' + conditional_escape(value) + '"')

        return mark_safe(' '.join(result))

    def _render_widgetmedia(self, context, manner='all', name=None):
        request = context.get('request')
        storage = get_widgets(request)

        if storage.has(name):
            media = storage.get(name).media
        elif name is None:
            media = storage.media
        else:
            return ''

        if manner in ('css', 'js', 'style', 'script'):
            return mark_safe('\n'.join(getattr(media, 'render_' + manner)(context=context.get_all(), request=request, renderer=Jinja2EnvironmentRenderer(self.environment))))
        elif manner == 'all':
            return mark_safe(media.render(context=context.get_all(), request=request, renderer=Jinja2EnvironmentRenderer(self.environment)))

