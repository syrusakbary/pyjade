from setuptools import setup,find_packages

setup(name='pyjade',
      version = '1.6',
      download_url = 'git@github.com:syrusakbary/pyjade.git',
      packages = find_packages(),
      author = 'Syrus Akbary',
      author_email = 'me@syrusakbary.com',
      description = 'Jade syntax adapter for Django, Jinja2 and Mako templates',
      long_description=open('README.rst').read(),
      keywords = 'jade template converter',
      url = 'http://github.com/syrusakbary/pyjade',
      license = 'MIT',
      entry_points = {
          'console_scripts' : ['pyjade = pyjade.convert:convert_file',]
      }
    )