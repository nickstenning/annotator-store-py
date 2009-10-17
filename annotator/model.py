'''Annotation domain model.

If you are using this as a library you will want to use just the
make_annotation_table method and the Annotation object.
'''
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
from sqlalchemy import Table, Column
from sqlalchemy.types import *
from sqlalchemy.orm import relation, backref, class_mapper, object_session


class JsonType(TypeDecorator):
    '''Custom SQLAlchemy type for JSON data (serializing on save and
    unserializing on use).
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


def make_annotation_table(metadata):
    annotation_table = Table('annotation', metadata,
        Column('id', Unicode(36), primary_key=True, default=lambda:
            unicode(uuid.uuid4())),
        # docid
        Column('uri', UnicodeText),
        # json encoded object looking like
        # format, start, end
        # for default setup start = [element, offset]
        Column('range', JsonType),
        Column('text', UnicodeText),
        Column('quote', UnicodeText),
        Column('created', DateTime, default=datetime.now),
        )
    return annotation_table


class Annotation(object):

    def save_changes(self):
        sess = object_session(self)
        # TODO: deal with case where we should only flush ...
        sess.commit()

    @classmethod
    def delete(self, id):
        anno = self.query.get(id)
        if anno:
            sess = object_session(anno)
            sess.delete(anno)
            anno.save_changes()

    def __str__(self):
        out = u'%s %s' % (self.__class__.__name__, self.as_dict())
        return out.encode('utf8', 'ignore')
    
    def as_dict(self):
        table = class_mapper(self.__class__).mapped_table
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
        id = _dict.get('id', None)
        if id:
            anno = Annotation.query.get(id)
        else:
            anno = Annotation()
            # assert anno is not None
        for key in [ 'uri', 'text', 'range' ]:
            if key in _dict:
                setattr(anno, key, _dict[key])
        # TODO: decide whether we have range or ranges
        if 'ranges' in _dict and _dict['ranges']: 
            anno.range = _dict['ranges'][0]
        return anno

def map_annotation_object(mapper, annotation_table):
    mapper(Annotation, annotation_table)


from sqlalchemy.orm import scoped_session, sessionmaker, create_session
Session = scoped_session(sessionmaker(
    autoflush=True,
    autocommit=False,
    ))
class Repository(object):

    def configure(self, dburi):
        from sqlalchemy import MetaData

        engine = create_engine(dburi, echo=False)

        self.metadata = MetaData()
        self.metadata.bind = engine
        Session.bind = engine
        mapper = Session.mapper

        anno_table = make_annotation_table(self.metadata)
        map_annotation_object(mapper, anno_table)

#         def set_default_connection(dburi=None):
#                 cwd = os.getcwd()
#                 path = os.path.join(cwd, 'testsqlite.db')
#                 uri = 'sqlite:///%s' % path
#             # uri = 'sqlite:///:memory:'

    def createdb(self):
        logger.info('Creating db')
        self.metadata.create_all()

    def cleandb(self):
        self.metadata.drop_all()
        logger.info('Cleaned db')

    def rebuilddb(self):
        self.cleandb()
        self.createdb()

repo = Repository()
