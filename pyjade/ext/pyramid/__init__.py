from pyramid import mako_templating
from pyjade.ext.mako import preprocessor

def includeme(config):
    config.add_renderer(".jade", PyjadeRenderer)

class PyjadeRenderer(object):
    """
    The jade renderer
    """
    def __init__(self, info):
        info.settings['mako.preprocessor'] = preprocessor
        self.makoRenderer = mako_templating.renderer_factory(info)

    def __call__(self, value, system):
        return self.makoRenderer(value, system)
