from django.template.loaders.filesystem import Loader as DjFSLoader
from django.template.loaders.app_directories import Loader as DjAppLoader

from pyjade import Root
from env import DjangoEnvironment

def preprocessor(source):
    return unicode(Root(source,env=DjangoEnvironment()))

class FSLoader(DjFSLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        data, fn = super(FSLoader, self) \
            .load_template_source(template_name, template_dirs)

        if not template_name.endswith('.jade'):
            return data, fn

        return preprocessor(data), fn
    load_template_source.is_usable = True

class AppLoader(DjAppLoader):
    is_usable = True

    def load_template_source(self, template_name, template_dirs=None):
        data, fn = super(AppLoader, self) \
            .load_template_source(template_name, template_dirs)

        if not template_name.endswith('.jade'):
            return data, fn

        return preprocessor(data), fn
    load_template_source.is_usable = True