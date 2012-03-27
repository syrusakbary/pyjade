PyJade
======

PyJade is a high performance port of Jade-lang for python, that converts any .jade source to the each Template-language (Django, Jinja2 or Mako).


NOTE
----
This package is **completely rewritten in the 1.X version** for be an exact port of Jade, so may be some *backwards incompatibilities*.

********************************************************************

INSTALLATION
============

First, you must do:

```console
  pip install pyjade
```

Or:

```console
  python setup.py install
```

Now simply **name your templates with a `.jade` extension** and this jade compiler
will do the rest.  Any templates with other extensions will not be compiled
with the pyjade compiler.


Django
------

In `settings.py`, modify `TEMPLATE_LOADERS` like:

```python
TEMPLATE_LOADERS = (
    ('pyjade.ext.django.Loader',(
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)
```

Jinja2
------

Just add `pyjade.ext.jinja.PyJadeExtension` as extension:

```python
jinja_env = Environment(extensions=['pyjade.ext.jinja.PyJadeExtension'])
```

Mako
----

Just add  `pyjade.ext.mako.preprocessor` as preprocessor:

```python
from pyjade.ext.mako import preprocessor as mako_preprocessor
mako.template.Template(jade_source,
    preprocessor=mako_preprocessor
)
```

**Actually the mako preprocessor is in development mode**

Flask
-----

Just add  `pyjade.ext.jinja.PyJadeExtension` as extension to the environment of the app::

```python
app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
```

Pyramid
-------

Adjust your "your_project/__init__.py" and add the following line somewhere to in the main() function:

```python
config.include('pyjade.ext.pyramid')
```

Syntax
======

Exactly the same as the Jade Node.js module (except of cases, which are not implemented)
https://github.com/visionmedia/jade/blob/master/Readme.md

**NOTE: Currently Django has no mixin support**

Main differences
----------------

Interpolation is not supported, so you must use the interpolation of the template engine.
Instead of do `{#somevar}` just do `{{somevar}}` in Jinja2 or Django

Example
-------

This code:

```jade
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
```


Converts to:

```html
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
```

TESTING
=======

You must have `nose` package installed.
You can do the tests with
    
```console
$> ./test.sh
```


TODOs and BUGS
==============
See: http://github.com/syrusakbary/pyjade/issues