from pyjade.env import Environment
from pyjade.nodes import Root

templates = (
'''doctype html PUBLIC "-//W3C//DTD XHTML Basic 1.1//EN
html(lang="en")
  head#a
    title= pageTitle
    script(type='text/javascript')
      if (foo) {
         bar()
      }
  body

    prueba#and.as.bs(id="2" class={{ra}} {{as}} p)
    h1 Jade - node template engine
    %a a
    #container: -for b in c
        for r
            // a
            b: | a
      - if (youAreUsingJade)
        p You are amazing
      - else
        p.caca/ hola
        a b
    
    as_self.: a b
    :plain
      a b c

      c b c
      
    //:markdown
      # this is a heading
      
      * oh look
      * it's a list
      * yay

      and some basic text for good measure.


    //:restructured
      this is testing the **reStructuredText** filter.

    
    for a in b-
      c
''',
# template_jade = '''label.
  
#   | Username:

#     input(name='user[name]')

'''!!! 5
html(lang="en")
  head
    title= pageTitle
    script(type='text/javascript')
      if (foo) {
         bar()
      }
  body
    h1.tal#h1_principal(class="otrotal {{asd}}")/
    = 2
    h1 Jade - node template engine
    #container
      - if youAreUsingJade
        p You are amazing
      - else
        p Get on it!
''',

'''!!! 5
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
        
    //
    a.link#myweb(href="http://syrusakbary.com" rel="_blank") Link to my web
    div hello comment
  //[Conditional Comment]
    div hello conditional comment
''','''
a.document_new.grid_4(href='{{ url("document_create")}}') prueba
a.document_new.grid_4(href="{{ url('document_create')}}") prueba
'''
)


from pyjade.ext.jinja import JinjaEnvironment as Environment
#from pyjade.ext.django import DjangoEnvironment as Environment

for template in templates:
    print Root(template, env=Environment())


#for template in templates:
#    try:
#        node =  Root(template, env=Environment())
        # print node.children[0].children[0]
        # print node.children[0].children[0].children[0].children[2].children
        #        print node #, len(template_jade)
    #except Exception as detail:
    #    print "==== ERROR ===="
    #    print "template:"
    #    print template
    #    print "reason:", detail
    #    pass
