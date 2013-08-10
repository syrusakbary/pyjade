import os
from django.conf import settings
from pyjade.utils import process


settings.configure(
    TEMPLATE_DIRS=("cases/",),
    TEMPLATE_LOADERS = (
        ('pyjade.ext.django.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    )
)
import django.template
import django.template.loader
from pyjade.ext.django import Compiler as DjangoCompiler


def django_process(src, filename):
    compiled = process(src, filename=filename, compiler=DjangoCompiler)
    print(compiled)
    t = django.template.Template(compiled)

    ctx = django.template.Context()
    return t.render(ctx)

filename = 'fun/files/' + os.path.basename(__file__).replace('.py', '.jade')

result = django_process(open(filename).read(), filename)

print result
