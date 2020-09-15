# Widgets for django

## Introduction
Widget is template linked with styles and scripts. Application gives you the ability collect media from 
different widgets and places it in the template wherever you want.

## INSTALLATION
You can get Django Widgets Engine by using pip::

    $ pip install django-widgets-engine

## Initialization
Add to your Django settings
```python
INSTALLED_APPS = [
    #...
    'django_widgets',
    #...
]

MIDDLEWARE = [
    #...
    'django_widgets.middleware.WidgetsMiddleware',
    #...
]
```

You can also build tag set into templates
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'jinja2')],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'jinja2.Environment',
            'extensions': ['django_widgets.jinja2tags.widget'],
            # ...
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            # ...
            'builtins': [
                'django_widgets.templatetags.widget'
            ],
        },
    },
]
```

## Class Widget

```python
import django_widgets


class WidgetFoo(django_widgets.Widget):
    root = '...'
    # default folder with templates
    template_name = 'template.html'
    # path to template

    class Media:
        extend = False  # include media from parent class
        js = {  # tag <script> for external scripts
            'async': (  # download method (async, defer). Maybe empty string
                'https://absolute/path/to/script.js', # value of attribute src
            ) # tuple
        }
        script = {  # tag <script> for inline scripts
            'text/javascript': {  # value of attribute type
                'script_id': (  # value of attribute id
                    '/path/to/script_template.html',
                )  # tuple
            }
        }
        css = {  # tag <link>
            'all': (  # value of attribute media
                'http://abolute/path/to/style.css', # value of attribute href
            ) # tuple
        }
        style = {  # tag <style>
            'all': (  # value of attribute media
                '/path/to/style_template.css',
            )  # tuple                
        }   
```

## Mixin

When you need use one widget inside other you can use MultiWidgetMixin.

```python
import django_widgets


class MultiWidget(django_widgets.MultiWidgetMixin, django_widgets.Widget):
    template_name = 'multiwidget.html'

    def _init_request(self, request):
        request = super()._init_request(request)
        self.add_widget(request, 'widget_name', WidgetFoo())
        return request
```

## Using

You must use add_widget before using tag widget in template

```python
from django_widgets.api import add_widget
from django.views.generic import TemplateView
from .widgets import WidgetFoo


class MyView(TemplateView):
    template_name = "my_view.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        add_widget(request, 'widget_name', WidgetFoo()) 

```

## Tags
In Django Template before use you need load tag set
```djangotemplate
{% load widget %}
```

### widget
You can call a widget in a template with data and attributes

```djangotemplate
{% widget 'widget_name' data=widget_data attrs=widget_attr_dict attr-name=attr_value %}
```

### widgetattrs
Use this tag in widget template. It mixes attributes from template, call widget and widget declaration 
```djangotemplate
{% widgetattrs %}
{% widgetattrs attrs=widget_attr_dict %}
{% widgetattrs attr-name=attr_value %}
```

### widgetmedia

```djangotemplate
{% widgetmedia %}  {# output all media for all widgets #}
{% widgetmedia 'js' %} {# print <script src="...">  for all widgets #}
{% widgetmedia 'css' %} {# print <link> for all widgets #}
{% widgetmedia 'style' %} {# print <style> for all widgets #}
{% widgetmedia 'script' name='widget_name'  %} {# print <script> for widjet with specified name #}
{% widgetmedia name='widget_name' %}  {# output all media for widjet with specified name#}
```
