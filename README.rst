======
PyJade
======

PyJade is a high performance port of Jade-lang for python, that converts any .jade source to the each Template-language (Django, Jinja2, Mako or Tornado).


UTILITIES
=========
To simply output the conversion to your console::

    pyjade [-c django|jinja|mako|tornado] input.jade [output.html]


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

In `settings.py`, add a `loader` to `TEMPLATES` like so:

.. code:: python

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.core.context_processors.request'
                ],
                'loaders': [
                    # PyJade part:   ##############################
                    ('pyjade.ext.django.Loader', (
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    ))
                ],
                'builtins': ['pyjade.ext.django.templatetags'],  # Remove this line for Django 1.8
            },
        },
    ]


Jinja2
------

Just add `pyjade.ext.jinja.PyJadeExtension` as extension

.. code:: python

    jinja_env = Environment(extensions=['pyjade.ext.jinja.PyJadeExtension'])


Mako
----

Just add  `pyjade.ext.mako.preprocessor` as preprocessor

.. code:: python

    from pyjade.ext.mako import preprocessor as mako_preprocessor
    mako.template.Template(haml_source,
        preprocessor=mako_preprocessor
    )


Flask
-----

Just add  `pyjade.ext.jinja.PyJadeExtension` as extension to the environment of the app

.. code:: python

    app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')


Pyramid
-------

Adjust your "your_project/__init__.py" and add the following line somewhere to in the main() function

.. code:: python

    config.include('pyjade.ext.pyramid')


Tornado Templates
-----------------

Append this after importing tornado.template

.. code:: python

    from tornado import template
    from pyjade.ext.tornado import patch_tornado
    patch_tornado()

    (...)


Syntax
======

Exactly the same as the Jade Node.js module (except of cases, which are not implemented)
https://github.com/visionmedia/jade/blob/master/README.md


Example
-------

This code

.. code:: jade

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


Converts to

.. code:: html

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


Register filters
================

If you want to register a function as a filter, you only have to
decorate the function with ``pyjade.register_filter("filter_name")``

.. code:: python

    import pyjade

    @pyjade.register_filter('capitalize')
    def capitalize(text,ast):
      return text.capitalize()


TESTING
=======

You must have `nose` package installed.
You can do the tests with::
    
    ./test.sh


TODOs and BUGS
==============
See: http://github.com/syrusakbary/pyjade/issues
