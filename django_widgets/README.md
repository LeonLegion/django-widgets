#Widgets for django
## Introduction
Widget is template linked with styles and scripts. Application gives you the ability collect media from 
different widgets and places it in the template wherever you want.


## Initialization

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
            )
        }
        script = {  # tag <script> for inline scripts
            'text/javascript': {# value of attribute type
                'script_id': ('/path/to/script_template.html',)
            }
        }
        css = {  # tag <link>
            'all': (  # value of attribute media
                'http://abolute/path/to/style.css', # value of attribute href
            )
        }
        style = {  # tag <style>
            'all': (  # value of attribute media
                '/path/to/style_template.css'
            )                  
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

##Using

Before using tag widget in template you must

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

### widget

```djangotemplate
{% load widget %}
{% widget 'widget_name' data=widget_data attrs=widget_attr attr_name=attr_value %}
```

### widgetattrs

```djangotemplate
{% widgetattrs %}
{% widgetattrs attr-name=attr_value%}
```

### widgetmedia

```djangotemplate
{% widgetmedia %}
{% widgetmedia 'js' %}
{% widgetmedia 'css' %}
{% widgetmedia 'style' 'widget_name' %}
{% widgetmedia 'script' %}
```
