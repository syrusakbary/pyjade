import hashlib

from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader, get_template_from_string, find_template_loader, make_origin
import os

from django.conf import settings
from pyjade.ext.django import Compiler
from pyjade import Parser

from pyjade.utils import process
# from django.template.loaders.cached import Loader

class Loader(BaseLoader):
    is_usable = True

    def __init__(self, loaders):
        self.template_cache = {}
        self._loaders = loaders
        self._cached_loaders = []

    @property
    def loaders(self):
        # Resolve loaders on demand to avoid circular imports
        if not self._cached_loaders:
            # Set self._cached_loaders atomically. Otherwise, another thread
            # could see an incomplete list. See #17303.
            cached_loaders = []
            for loader in self._loaders:
                cached_loaders.append(find_template_loader(loader))
            self._cached_loaders = cached_loaders
        return self._cached_loaders

    def find_template(self, name, dirs=None):
        for loader in self.loaders:
            try:
                template, display_name = loader(name, dirs)
                return (template, make_origin(display_name, loader, name, dirs))
            except TemplateDoesNotExist:
                pass
        raise TemplateDoesNotExist(name)

    def load_template_source(self, template_name, template_dirs=None):
        for loader in self.loaders:
            try:
                return loader.load_template_source(template_name,template_dirs)
            except TemplateDoesNotExist:
                pass
        raise TemplateDoesNotExist(template_name)

    def load_template(self, template_name, template_dirs=None):
        key = template_name
        if template_dirs:
            # If template directories were specified, use a hash to differentiate
            key = '-'.join([template_name, hashlib.sha1('|'.join(template_dirs)).hexdigest()])

        
        if settings.DEBUG or key not in self.template_cache:

            if os.path.splitext(template_name)[1] in ('.jade',):
                try:
                    source, display_name = self.load_template_source(template_name, template_dirs)
                    source=process(source,filename=template_name,compiler=Compiler)
                    origin = make_origin(display_name, self.load_template_source, template_name, template_dirs)
                    template = get_template_from_string(source, origin, template_name)
                except NotImplementedError:
                    template, origin = self.find_template(template_name, template_dirs)
            else:
                template, origin = self.find_template(template_name, template_dirs)
            if not hasattr(template, 'render'):
                try:
                    template = get_template_from_string(process(source,filename=template_name,compiler=Compiler), origin, template_name)
                except TemplateDoesNotExist:
                    # If compiling the template we found raises TemplateDoesNotExist,
                    # back off to returning he source and display name for the template
                    # we were asked to load. This allows for correct identification (later)
                    # of the actual template that does not exist.
                    return template, origin
            self.template_cache[key] = template
        return self.template_cache[key], None

    # def _preprocess(self, source, name, filename=None):
    #     parser = Parser(source,filename=filename)
    #     block = parser.parse()
    #     compiler = Compiler(block)
    #     return compiler.compile().strip()

    def reset(self):
        "Empty the template cache."
        self.template_cache.clear()
