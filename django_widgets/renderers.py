import functools
from pathlib import Path

from django.conf import settings
from django.template.backends.django import DjangoTemplates as TemplatesDjango, Template as TemplateDjango, reraise
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from django.template.loader import get_template
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

try:
    from django.template.backends.jinja2 import Jinja2 as TemplatesJinja2, Template as TemplateJinja2, get_exception_info
    import jinja2
except ImportError:
    def TemplatesJinja2(params):
        raise ImportError("jinja2 isn't installed")

    def TemplateJinja2(params):
        raise ImportError("jinja2 isn't installed")


ROOT = Path(__file__).parent


@functools.lru_cache()
def get_default_renderer(root=None):
    renderer_class = import_string(getattr(settings, 'WIDGET_RENDERER', 'django_widgets.renderers.DjangoTemplates'))
    return renderer_class(root)


class BaseRenderer:
    def get_template(self, template_name):
        raise NotImplementedError('subclasses must implement get_template()')

    def render(self, template_name, context=None, request=None):
        template = self.get_template(template_name)
        return template.render(context, request=request).strip()


class EngineMixin:
    def __init__(self, root=None):
        self.root = root

    def get_template(self, template_name):
        return self.engine.get_template(template_name)

    @cached_property
    def engine(self):
        dirs = [str(ROOT / self.backend.app_dirname)]
        if self.root:
            dirs.append(self.root)
        return self.backend({
            'APP_DIRS': True,
            'DIRS': dirs,
            'NAME': 'djangowidgets',
            'OPTIONS': {},
        })


class DjangoTemplates(EngineMixin, BaseRenderer):
    """
    Load Django templates from the built-in widget templates in
    /templates and from apps' 'templates' directory.
    """
    backend = TemplatesDjango


class Jinja2(EngineMixin, BaseRenderer):
    """
    Load Jinja2 templates from the built-in widget templates in
    /jinja2 and from apps' 'jinja2' directory.
    """
    backend = TemplatesJinja2


class DjangoContextRenderer(BaseRenderer):
    def __init__(self, context):
        self.context = context

    def get_template(self, template_name):
        try:
            return TemplateDjango(self.engine.get_template(template_name), self)
        except TemplateDoesNotExist as exc:
            reraise(exc, self)

    @cached_property
    def engine(self):
        return self.context.template.engine


class Jinja2EnvironmentRenderer(BaseRenderer):
    def __init__(self, environment):
        self.env = environment
        self.template_context_processors = []

    def get_template(self, template_name):
        try:
            return TemplateJinja2(self.env.get_template(template_name), self)
        except jinja2.TemplateNotFound as exc:
            raise TemplateDoesNotExist(exc.name, backend=self) from exc
        except jinja2.TemplateSyntaxError as exc:
            new = TemplateSyntaxError(exc.args)
            new.template_debug = get_exception_info(exc)
            raise new from exc


class TemplatesSetting(BaseRenderer):
    """
    Load templates using template.loader.get_template() which is configured
    based on settings.TEMPLATES.
    """

    def get_template(self, template_name):
        return get_template(template_name)
