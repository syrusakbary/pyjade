======
PyJade
======

PyJade is a high performance port of Jade-lang for python, that converts any .jade source to the each Template-language (Django, Jinja2 or Mako).


NOTE
----
This package is completely rewritten in the 1.X version for be an exact port of Jade, so may be some backwards incompatibilities.


INSTALLATION
============

First, you must do::

    pip install pyjade

Or::

    python setup.py install

Now simply **name your templates with a `.jade` extension** and this jade compiler
will do the rest.  Any templates with other extensions will not be compiled
with the pyjade compiler.


Django
------

In `settings.py`, modify `TEMPLATE_LOADERS` like::

    TEMPLATE_LOADERS = (
        ('pyjade.ext.django.Loader',(
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    )


Jinja2
------

Just add `pyjade.ext.jinja.PyJadeExtension` as extension::

    jinja_env = Environment(extensions=['pyjade.ext.jinja.PyJadeExtension'])


Mako
----

Just add  `pyjade.ext.mako.preprocessor` as preprocessor::

    from pyjade.ext.mako import preprocessor as mako_preprocessor
    mako.template.Template(haml_source,
        preprocessor=mako_preprocessor
    )

**Actually the mako preprocessor is in development mode**

Flask
-----

Just add  `pyjade.ext.jinja.PyJadeExtension` as extension to the environment of the app::

    app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')


Pyramid
-------

Adjust your "your_project/__init__.py" and add the following line somewhere to in the main() function::

    config.include('pyjade.ext.pyramid')


Syntax
======

Exactly the same as the Jade Node.js module (except of cases, which are not implemented)
https://github.com/visionmedia/jade/blob/master/Readme.md

**NOTE: Currently Django has no mixin support**


Example
-------

This code::

    !!! 5
    html(lang="en")
      head
        title= pageTitle
        script(type='text/javascript')
          if (foo) {
             bar()
          }
      body
        h1.title Jade - node template engine
        #container
          if youAreUsingJade
            p You are amazing
          else
            p Get on it!


Converts to::

    <!DOCTYPE html>
    <html lang="en">
      <head>
        <title>{{pageTitle}}</title>
        <script type='text/javascript'>
          if (foo) {
             bar()
          }
        </script>
      </head>
      <body>
        <h1 class="title">Jade - node template engine</h1>
        <div id="container">
          {%if youAreUsingJade%}
            <p>You are amazing</p>
          {%else%}
            <p>Get on it!</p>
          {%endif%}
        </div>
      </body>
    </html>

TESTING
=======

You must have `nose` package installed.
You can do the tests with::
    
    $> ./test.sh


TODOs and BUGS
==============
See: http://github.com/syrusakbary/pyjade/issues