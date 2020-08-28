import copy
from collections import defaultdict
from itertools import chain

import django.forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .renderers import get_default_renderer

MEDIA_TYPES = ('css', 'js', 'style', 'script')


class Media(django.forms.Media):
    def __init__(self, media=None, css=None, js=None, style=None, script=None):
        if media is not None:
            css = getattr(media, 'css', {})
            js = getattr(media, 'js', {})
            style = getattr(media, 'style', {})
            script = getattr(media, 'script', {})
        else:
            if css is None:
                css = {}
            if js is None:
                js = {}  # !!!
            if style is None:
                style = {}
            if script is None:
                script = {}
        self._css_lists = [css]
        self._js_lists = [js]
        self._style_lists = [style]
        self._script_lists = [script]

    @property
    def _js(self):
        js = defaultdict(list)
        for js_list in self._js_lists:
            for method, sublist in js_list.items():
                js[method].append(sublist)
        return {method: self.merge(*lists) for method, lists in js.items()}

    def render_js(self, context=None, renderer=None, request=None):
        methods = sorted(self._js)
        return chain.from_iterable([
            format_html(
                '<script {} type="text/javascript" src="{}"></script>',
                method, self.absolute_path(js)
            ) for js in self._js[method]
        ] for method in methods)

    def render_css(self, context=None, renderer=None, request=None):
        return super().render_css()

    @property
    def _style(self):
        style = defaultdict(list)
        for style_list in self._style_lists:
            for medium, sublist in style_list.items():
                style[medium].append(sublist)
        return {medium: self.merge(*lists) for medium, lists in style.items()}

    def render_style(self, context=None, renderer=None, request=None):
        if renderer is None:
            renderer = get_default_renderer()
        media = sorted(self._style)
        return chain.from_iterable([
            format_html(
                '<style type="text/css" media="{}">\n',
                medium
            ) + '\n'.join(renderer.render(path, context=context, request=request) for path in self._style[medium]) + '\n</style>'
        ] for medium in media)

    @property
    def _script(self):
        script = dict()
        for script_list in self._script_lists:
            for script_type, script_obj in script_list.items():
                for script_id, script_paths in script_obj.items():
                    if script_id not in script:
                        script[script_id] = {'type': script_type, 'paths': list()}
                    script[script_id]['paths'].append(script_paths)
        for script_id, d in script.items():
            script[script_id]['paths'] = self.merge(*d['paths'])
        return script

    def render_script(self, context=None, renderer=None, request=None):
        if renderer is None:
            renderer = get_default_renderer()
        scripts = sorted(self._script)
        return chain.from_iterable([
            format_html(
                '<script type="{}" id="{}">\n',
                self._script[script_id]['type'], script_id
            ) + '\n'.join(renderer.render(path, context=context, request=request) for path in self._script[script_id]['paths']) + '\n</script>'
        ] for script_id in scripts)

    def render(self, context=None, renderer=None, request=None):
        return mark_safe('\n'.join(chain.from_iterable(getattr(self, 'render_' + name)(context=context, renderer=renderer, request=request) for name in MEDIA_TYPES)))

    def __getitem__(self, name):
        """Return a Media object that only contains media of the given type."""
        if name in MEDIA_TYPES:
            return Media(**{str(name): getattr(self, '_' + name)})
        raise KeyError('Unknown media type "%s"' % name)

    def __add__(self, other):
        combined = Media()
        combined._css_lists = self._css_lists + other._css_lists
        combined._js_lists = self._js_lists + other._js_lists
        combined._style_lists = self._style_lists + other._style_lists
        combined._script_lists = self._script_lists + other._script_lists
        return combined


def media_property(cls):
    def _media(self):
        # Get the media property of the superclass, if it exists
        sup_cls = super(cls, self)

        try:
            base = sup_cls.media
        except AttributeError:
            base = Media()

        # Get the media definition for this class
        definition = getattr(cls, 'Media', None)
        if definition:
            extend = getattr(definition, 'extend', True)
            if extend:
                if extend is True:
                    m = base
                else:
                    m = Media()
                    for medium in extend:
                        m = m + base[medium]
                return m + Media(definition)
            return Media(definition)
        return base

    return property(_media)


class MediaDefiningClass(type):
    """
    Metaclass for classes that can have media definitions.
    """

    def __new__(mcs, name, bases, attrs):
        new_class = super(MediaDefiningClass, mcs).__new__(mcs, name, bases, attrs)

        if 'media' not in attrs:
            new_class.media = media_property(new_class)

        return new_class


class Widget(metaclass=MediaDefiningClass):
    root = None
    template_name = None

    def __init__(self, data=None, attrs=None):
        self.data = {} if data is None else data
        self.attrs = {} if attrs is None else attrs.copy()

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.attrs = self.attrs.copy()
        obj.data = copy.deepcopy(self.data)
        memo[id(self)] = obj
        return obj

    def _init_request(self, request):
        return request

    def _reset_request(self, request):
        pass

    def get_template_name(self):
        return self.template_name

    def get_context(self, name, data, attrs):
        context = {
            'widget': {
                'name': name,
                'data': self.data if data is None else data,
                'attrs': self.build_attrs(self.attrs, attrs),
            }
        }
        return context

    def render(self, name, data=None, attrs=None, renderer=None, request=None):
        """Render the widget as an HTML string."""
        context = self.get_context(name, data, attrs)
        request = self._init_request(request)
        result = self._render(context, renderer, request)
        self._reset_request(request)
        return result

    def _render(self, context, renderer=None, request=None):
        if renderer is None:
            renderer = get_default_renderer(self.root)
        template_name = self.get_template_name()
        return mark_safe(renderer.render(template_name, context, request)) if template_name else '';

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build an attribute dictionary."""
        return {**base_attrs, **(extra_attrs or {})}

    def value_from_datadict(self, data, name):
        """
        Given a dictionary of data and this widget's name, return the value
        of this widget or None if it's not provided.
        """
        return data.get(name)

    def value_omitted_from_data(self, data, name):
        return name not in data
