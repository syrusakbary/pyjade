from utils import odict

try:
    from collections import Mapping as MappingType
except ImportError:
    import UserDict
    MappingType = (UserDict.UserDict, UserDict.DictMixin, dict)

def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

def escape(s):
    """Convert the characters &, <, >, ' and " in string s to HTML-safe
    sequences.  Use this if you need to display text that might contain
    such characters in HTML.  Marks return value as markup string.
    """
    if hasattr(s, '__html__'):
        return s.__html__()

    if isinstance(s, str):
        s = unicode(str(s), 'utf8')
    else:
        s = str(s)
    
    return (s
        .replace('&', '&amp;')
        .replace('>', '&gt;')
        .replace('<', '&lt;')
        .replace("'", '&#39;')
        .replace('"', '&#34;')
    )

def attrs (attrs=[],terse=False):
    buf = []
    if bool(attrs):
        buf.append('')
        for k,v in attrs:
            if v!=None and (v!=False or type(v)!=bool):
                if k=='class' and isinstance(v, (list, tuple)):
                    v = ' '.join(map(str,flatten(v)))
                t = v==True and type(v)==bool
                if t and not terse: v=k
                buf.append('%s'%k if terse and t else '%s="%s"'%(k,v))
    return ' '.join(buf)

def is_mapping(value):
    return isinstance(value, MappingType)