import os
import uuid
from datetime import datetime
import cgi
try:
    import json
except ImportError:
    import simplejson as json
import logging
logger = logging.getLogger('annotator')

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

def set_default_connection(dburi=None):
    if dburi:
        uri = dburi
    else:
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

class JsonType(TypeDecorator):
    '''Store data as JSON serializing on save and unserializing on use.
    '''
    impl = UnicodeText

    def process_bind_param(self, value, engine):
        if value is None or value == {}: # ensure we stores nulls in db not json "null"
            return None
        else:
            # ensure_ascii=False => allow unicode but still need to convert
            return unicode(json.dumps(value, ensure_ascii=False))

    def process_result_value(self, value, engine):
        if value is None:
            return None
        else:
            return json.loads(value)

    def copy(self):
        return JsonType(self.impl.length)


annotation_table = Table('annotation', metadata,
    Column('id', Unicode(36), primary_key=True, default=lambda:
        unicode(uuid.uuid4())),
    Column('url', UnicodeText),
    # json encoded object looking like
    # format, start, end
    # for default setup start = [element, offset]
    Column('range', JsonType),
    Column('text', UnicodeText),
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
            val = getattr(self, col)
            if isinstance(val, datetime):
                val = unicode(val)
            out[col] = val
        # add ranges back in for jsannotate compatibility
        out['ranges'] = [ self.range ] if self.range else []
        return out
    
    @classmethod
    def from_dict(cls, _dict):
        # TODO: support case where id provided
        id = _dict.get('id', None)
        if id:
            anno = Annotation.query.get(id)
        else:
            anno = Annotation()
        for key in [ 'url', 'text', 'range' ]:
            if key in _dict:
                setattr(anno, key, _dict[key])
        # TODO: decide whether we have range or ranges
        if 'ranges' in _dict and _dict['ranges']: 
            anno.range = _dict['ranges'][0]
        return anno

mapper(Annotation, annotation_table)

