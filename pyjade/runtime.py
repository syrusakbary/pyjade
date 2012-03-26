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

def attrs (attrs={},terse=False):
	buf = []
	if bool(attrs):
		buf.append('')
		for k,v in attrs.iteritems():
			if bool(v) or v==None:
				if k=='class' and isinstance(v, (list, tuple)):
					v = ' '.join(map(str,flatten(v)))
				t = v==True
				if t and not terse: v=k
				buf.append('%s'%str(k) if terse and t else '%s="%s"'%(k,str(v)))
	return ' '.join(buf)