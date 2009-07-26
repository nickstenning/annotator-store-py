import os
import uuid
from datetime import datetime
import cgi
import logging
logger = logging.getLogger('annotater')

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
# TODO: restrict imports ...
from sqlalchemy import *

metadata = MetaData()

from sqlalchemy.orm import scoped_session, sessionmaker, create_session
from sqlalchemy.orm import relation, backref
# both options now work
# Session = scoped_session(sessionmaker(autoflush=False, transactional=True))
# this is the more testing one ...
Session = scoped_session(sessionmaker(
    autoflush=True,
    autocommit=False,
    ))

mapper = Session.mapper

def set_default_connection():
    cwd = os.getcwd()
    path = os.path.join(cwd, 'testsqlite.db')
    uri = 'sqlite:///%s' % path
    # uri = 'sqlite:///:memory:'
    engine = create_engine(uri, echo=False)
    metadata.bind = engine
    Session.bind = engine

def createdb():
    logger.info('Creating db')
    metadata.create_all()

def cleandb():
    metadata.drop_all()
    logger.info('Cleaned db')

def rebuilddb():
    cleandb()
    createdb()

annotation_table = Table('annotation', metadata,
    Column('id', String(36), primary_key=True, default=lambda:
        str(uuid.uuid4())),
    Column('url', UnicodeText),
    Column('range', UnicodeText),
    Column('note', UnicodeText),
    Column('quote', UnicodeText),
    Column('created', DateTime, default=datetime.now),
    )


class Annotation(object):

    @classmethod
    def delete(self, id):
        anno = self.query.get(id)
        if anno:
            Session.delete(anno)
        Session.commit()

    def __str__(self):
        out = u'%s %s %s' % (self.__class__.__name__, self.id, self.url)
        return out.encode('utf8', 'ignore')

    @classmethod
    def list_annotations_html(cls, url=u''):
        import cgi
        query_results = cls.query.filter(cls.url.startswith(url))
        out = ''
        for item in query_results:
            out += '<pre>%s</pre>' % cgi.escape(str(item)) + '\n\n'
        return out

    @classmethod
    def list_annotations_atom(cls, url=u''):
        query_results = cls.query.filter(cls.url.startswith(url))
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

mapper(Annotation, annotation_table)

