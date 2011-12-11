from filters import plain_filter, cdata_filter, markdown_filter, rst_filter


class Environment(object):
    auto_close_tags = {}
    may_contain_tags = {}
    code_tags = ()
    doctypes = {
        '':'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
        'strict':'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">',
        'frameset':'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">',
        '5':'<!DOCTYPE html>',
        'basic':'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML Basic 1.1//EN" "http://www.w3.org/TR/xhtml-basic/xhtml-basic11.dtd">',
        'mobile':'<!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.2//EN" "http://www.openmobilealliance.org/tech/DTD/xhtml-mobile12.dtd">',
        '1.1':'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">', 
        'xml':'<?xml version="1.0" encoding="utf-8" ?>'
    }
    doctype_tags = ('!!!', 'doctype')
    html_plain_text = ('script', 'style', 'pre')
    html_self_close = (
        'meta'
      , 'img'
      , 'link'
      , 'input'
      , 'area'
      , 'base'
      , 'col'
      , 'br'
      , 'hr'
    )
    html_inline = (
        'a'
      , 'abbr'
      , 'acronym'
      , 'b'
      , 'br'
      , 'code'
      , 'em'
      , 'font'
      , 'i'
      , 'img'
      , 'ins'
      , 'kbd'
      , 'map'
      , 'samp'
      , 'small'
      , 'span'
      , 'strong'
      , 'sub'
      , 'sup'
    )
    
    html_default = 'div'

    write_empty_lines = False
    nl = None       # None == Auto indent
    indent = None   # None == Auto indent
    # nl = ''
    # indent = ''
    
    filters = {
        'plain': plain_filter,
        'cdata': cdata_filter,
        'markdown': markdown_filter,
        'restructured': rst_filter,
    }
