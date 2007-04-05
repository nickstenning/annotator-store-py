import os
from datetime import datetime
import cgi

import sqlobject

def set_default_connection():
    cwd = os.getcwd()
    uri = 'sqlite://%s/sqlite.db' % cwd
    # uri = 'sqlite:///:memory:'
    connection = sqlobject.connectionForURI(uri)
    sqlobject.sqlhub.processConnection = connection
    createdb()

# must not set this here as annotater and its model will be reused in other
# applications that will set up there own database connections
# set_default_connection()

# note we run this at bottom of module to auto create db tables on import
def createdb():
    Annotation.createTable(ifNotExists=True)

def cleandb():
    Annotation.dropTable(ifExists=True)

def rebuilddb():
    cleandb()
    createdb()

class Annotation(sqlobject.SQLObject):

    url = sqlobject.UnicodeCol()
    range = sqlobject.StringCol()
    note = sqlobject.UnicodeCol()
    quote = sqlobject.UnicodeCol(default=None)
    created = sqlobject.DateTimeCol(default=datetime.now) 

    @classmethod
    def list_annotations_html(cls, url='', userid='', exlude=''):
        import cgi
        query_results = cls.select(cls.q.url.startswith(url))
        out = ''
        for item in query_results:
            out += '<pre>%s</pre>' % cgi.escape(str(item)) + '\n\n'
        return out

    @classmethod
    def list_annotations_atom(cls, url='', userid='', exlude=''):
        query_results = cls.select(cls.q.url.startswith(url))
        # create the Atom by hand -- maybe in future we can use a library
        ns_xhtml = '' 
        annotation_service = 'http://localhost:8080/annotation'
        def make_element(name, value):
            newelem = '<%s>%s</%s>\n' % (name, value, name)
            return newelem
        def make_entries(results):
            entries = ''
            for item in results:
                tentry = ''
                tentry += make_element('ptr:range', item.range)
                # Annotation note as title
                tnote = cgi.escape(item.note) 
                tentry += make_element('title', tnote)
                tentry += '<link rel="self" type="application/xml" href="%s/%s"/>\n' % ( annotation_service, item.id)
                tentry += \
'<link rel="related" type="text/html" title="%s" href="%s"/>\n' % (
                        'quote_title_not_available_yet',
                        cgi.escape(item.url, quote=True)
                        )
                tentry = '<entry>\n%s\n</entry>' % tentry
                entries += tentry
            return entries

        atom = \
u'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns:ptr="http://www.geof.net/code/annotation/" xmlns="http://www.w3.org/2005/Atom" ptr:annotation-version="0.2">
    %s
    %s
    %s
    %s
</feed>''' % (
    make_element('updated', datetime.now()),
    make_element('title', 'Annotations'),
    make_element('id', 'tag:%s' % datetime.now()),
    make_entries(query_results)
    )
        return atom.encode('utf8')


from formencode import sqlschema
class AnnotationSchema(sqlschema.SQLSchema):

    wrap = Annotation

