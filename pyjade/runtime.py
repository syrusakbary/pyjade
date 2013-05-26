from __future__ import absolute_import
from .utils import odict
import types
import six

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
    if isinstance(s, six.binary_type):
        s = six.text_type(str(s), 'utf8')
    elif isinstance(s, six.text_type):
        s = s
    else:
        s = str(s)

    return (s
        .replace('&', '&amp;')
        .replace('>', '&gt;')
        .replace('<', '&lt;')
        .replace("'", '&#39;')
        .replace('"', '&#34;')
    )

def attrs (attrs=[],terse=False, undefined=None):
    buf = []
    if bool(attrs):
        buf.append(u'')
        for k,v in attrs:
            if undefined is not None and isinstance(v, undefined):
                continue
            if v!=None and (v!=False or type(v)!=bool):
                if k=='class' and isinstance(v, (list, tuple)):
                    v = u' '.join(map(str,flatten(v)))
                t = v==True and type(v)==bool
                if t and not terse: v=k
                buf.append(u'%s'%k if terse and t else u'%s="%s"'%(k,escape(v)))
    return u' '.join(buf)

def is_mapping(value):
    return isinstance(value, MappingType)

def iteration(obj, num_keys):
    """
    Jade iteration supports "for 'value' [, key]?" iteration only.
    PyJade has implicitly supported value unpacking instead, without
    the list indexes. Trying to not break existing code, the following
    rules are applied:

      1. If the object is a mapping type, return it as-is, and assume
         the caller has the correct set of keys defined.

      2. If the object's values are iterable (and not string-like):
         a. If the number of keys matches the cardinality of the object's
            values, return the object as-is.
         b. If the number of keys is one more than the cardinality of
            values, return a list of [v(0), v(1), ... v(n), index]

      3. Else the object's values are not iterable, or are string like:
         a. if there's only one key, return the list
         b. otherwise return a list of (value,index) tuples

    """
    if is_mapping(obj):
        return obj

    head = next(iter(obj), None)
    if head:
        try:
            if not isinstance(head, six.string_types):
                card = len(head)
                if num_keys == card:
                    return obj
                if num_keys == card + 1:
                    return [list(value) + [index] for index, value in enumerate(obj)]
        except Exception:
            # Not iterable
            pass

    # Empty list, or other unknown case
    return obj if num_keys == 1 else [(value,index) for index, value in enumerate(obj)]
