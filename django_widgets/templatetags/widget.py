import re

from django import template
from django.template.exceptions import TemplateSyntaxError
from django.template.library import SimpleNode
from inspect import getfullargspec
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from ..api import get_widgets
from ..renderers import DjangoContextRenderer

register = template.Library()


def widget(context, name, data=None, attrs=None, **kwargs):
    storage = get_widgets(context.request)

    if not storage.has(name):
        return ''

    d = {}
    if kwargs is not None:
        for key, value in kwargs.items():
            d[key] = value
    if attrs is not None:
        d.update(attrs)

    return storage.get(name).render(name, data=data, attrs=d, request=context.request, renderer=DjangoContextRenderer(context))


def widget_attrs(context, attrs=None, **kwargs):
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


@register.simple_tag(name='widgetmedia', takes_context=True)
def widget_media(context, manner='all', name=None):
    storage = get_widgets(context.request)

    if storage.has(name):
        media = storage.get(name).media
    elif name is None:
        media = storage.media
    else:
        return ''

    if manner in ('css', 'js', 'style', 'script'):
        return mark_safe('\n'.join(getattr(media, 'render_' + manner)(context=context.flatten(), request=context.request, renderer=DjangoContextRenderer(context))))
    elif manner == 'all':
        return mark_safe(media.render(context=context.flatten(), request=context.request, renderer=DjangoContextRenderer(context)))

    return ''


def register_simple_tag(func=None, takes_context=None, name=None):
    params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)

    def compile_func(parser, token):
        bits = token.split_contents()[1:]
        args, kwargs = parse_bits(
            parser, bits, params, varargs, varkw, defaults,
            kwonly, kwonly_defaults, takes_context, name,
        )
        return SimpleNode(func, takes_context, args, kwargs, None)

    register.tag(name, compile_func)


register_simple_tag(func=widget, name='widget', takes_context=True)
register_simple_tag(func=widget_attrs, name='widgetattrs', takes_context=True)


# Regex for token keyword arguments
kwarg_re = re.compile(r"(?:([a-zA-Z0-9_:@\-]+)=)?(.+)")


def token_kwargs(bits, parser):
    """
    Parse token keyword arguments and return a dictionary of the arguments
    retrieved from the ``bits`` token list.

    `bits` is a list containing the remainder of the token (split by spaces)
    that is to be checked for arguments. Valid arguments are removed from this
    list.

    There is no requirement for all remaining token ``bits`` to be keyword
    arguments, so return the dictionary as soon as an invalid argument format
    is reached.
    """
    if not bits:
        return {}
    match = kwarg_re.match(bits[0])
    kwarg_format = match and match.group(1)
    if not kwarg_format:
        return {}

    kwargs = {}
    while bits:
        match = kwarg_re.match(bits[0])
        if not match or not match.group(1):
            return kwargs
        key, value = match.groups()
        del bits[:1]

        kwargs[key] = parser.compile_filter(value)

    return kwargs


def parse_bits(parser, bits, params, varargs, varkw, defaults,
               kwonly, kwonly_defaults, takes_context, name):
    """
    Parse bits for template tag helpers simple_tag and inclusion_tag, in
    particular by detecting syntax errors and by extracting positional and
    keyword arguments.
    """
    if takes_context:
        if params[0] == 'context':
            params = params[1:]
        else:
            raise TemplateSyntaxError(
                "'%s' is decorated with takes_context=True so it must "
                "have a first argument of 'context'" % name)
    args = []
    kwargs = {}
    unhandled_params = list(params)
    unhandled_kwargs = [
        kwarg for kwarg in kwonly
        if not kwonly_defaults or kwarg not in kwonly_defaults
    ]
    for bit in bits:
        # First we try to extract a potential kwarg from the bit
        kwarg = token_kwargs([bit], parser)
        if kwarg:
            # The kwarg was successfully extracted
            param, value = kwarg.popitem()
            if param not in params and param not in unhandled_kwargs and varkw is None:
                # An unexpected keyword argument was supplied
                raise TemplateSyntaxError(
                    "'%s' received unexpected keyword argument '%s'" %
                    (name, param))
            elif param in kwargs:
                # The keyword argument has already been supplied once
                raise TemplateSyntaxError(
                    "'%s' received multiple values for keyword argument '%s'" %
                    (name, param))
            else:
                # All good, record the keyword argument
                kwargs[str(param)] = value
                if param in unhandled_params:
                    # If using the keyword syntax for a positional arg, then
                    # consume it.
                    unhandled_params.remove(param)
                elif param in unhandled_kwargs:
                    # Same for keyword-only arguments
                    unhandled_kwargs.remove(param)
        else:
            if kwargs:
                raise TemplateSyntaxError(
                    "'%s' received some positional argument(s) after some "
                    "keyword argument(s)" % name)
            else:
                # Record the positional argument
                args.append(parser.compile_filter(bit))
                try:
                    # Consume from the list of expected positional arguments
                    unhandled_params.pop(0)
                except IndexError:
                    if varargs is None:
                        raise TemplateSyntaxError(
                            "'%s' received too many positional arguments" %
                            name)
    if defaults is not None:
        # Consider the last n params handled, where n is the
        # number of defaults.
        unhandled_params = unhandled_params[:-len(defaults)]
    if unhandled_params or unhandled_kwargs:
        # Some positional arguments were not supplied
        raise TemplateSyntaxError(
            "'%s' did not receive value(s) for the argument(s): %s" %
            (name, ", ".join("'%s'" % p for p in unhandled_params + unhandled_kwargs)))
    return args, kwargs
