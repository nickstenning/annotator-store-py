import os
import uuid
from datetime import datetime
import cgi
import logging
logger = logging.getLogger('annotater')

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
# TODO: restrict imports ...
from sqlalchemy.types import *
from sqlalchemy import orm

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
    # json encoded object looking like
    # format, start, end
    # for default setup start = [element, offset]
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
    
    def as_dict(self):
        table = orm.class_mapper(self.__class__).mapped_table
        out = {}
        for col in table.c.keys():
            out[col] = unicode(getattr(self, col))
        return out
    
    @classmethod
    def from_dict(cls, _dict):
        # TODO: support case where id provided
        id = _dict.get('id', None)
        if id:
            anno = Annotation.query.get(id)
        else:
            anno = Annotation()
        url = _dict.get('url', None)
        range = _dict.get('range', None)
        note = _dict.get('note', None)
        anno.url = url
        anno.range = range
        anno.note = note
        return anno

mapper(Annotation, annotation_table)

