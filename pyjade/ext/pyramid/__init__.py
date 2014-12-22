from pyjade.ext.mako import preprocessor
try:
    from pyramid_mako import MakoRendererFactory
    from pyramid_mako import parse_options_from_settings
    from pyramid_mako import PkgResourceTemplateLookup
    is_pyramid_mako = True
except ImportError:
    from pyramid import mako_templating
    is_pyramid_mako = False


class PyjadeRenderer(object):
    """
    The jade renderer
    """
    def __init__(self, info):
        info.settings['mako.preprocessor'] = preprocessor
        self.makoRenderer = mako_templating.renderer_factory(info)

    def __call__(self, value, system):
        return self.makoRenderer(value, system)


def add_jade_renderer(config, extension, mako_settings_prefix='mako.'):

    renderer_factory = MakoRendererFactory()
    config.add_renderer(extension, renderer_factory)

    def register():
        settings = config.registry.settings
        settings['{0}preprocessor'.format(mako_settings_prefix)] = preprocessor

        opts = parse_options_from_settings(settings, mako_settings_prefix, config.maybe_dotted)
        lookup = PkgResourceTemplateLookup(**opts)

        renderer_factory.lookup = lookup

    config.action(('jade-renderer', extension), register)


def includeme(config):
    if not is_pyramid_mako:
        config.add_renderer(".jade", renderer)
    else:
        config.add_directive('add_jade_renderer', add_jade_renderer)
        config.add_jade_renderer('.jade')
