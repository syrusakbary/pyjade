from pyjade import Root, Environment
class MakoEnvironment(Environment): pass

def preprocessor(source):
    return unicode(Root(source,env=MakoEnvironment()))
