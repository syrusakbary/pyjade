from jinja2.ext import Extension
import os
from pyjade.utils import process
from pyjade.runtime import attrs
class PyJadeExtension(Extension):

    def __init__(self, environment):
        super(PyJadeExtension, self).__init__(environment)

        environment.extend(
            jade_file_extensions=('.jade',),
            # jade_env=JinjaEnvironment(),
        )
        environment.globals['__pyjade_attrs'] = attrs

    def preprocess(self, source, name, filename=None):
        if name and not os.path.splitext(name)[1] in self.environment.jade_file_extensions:
            return source
        procesed= process(source,name)
        # print procesed
        return procesed