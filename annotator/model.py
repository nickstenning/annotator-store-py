'''Annotation domain model.

If you are using this as a library you will want to use just the
make_annotation_table method and the Annotation object.
'''
import os
import uuid
import logging
from datetime import datetime

logger = logging.getLogger('annotator')

from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.types import Unicode, UnicodeText, DateTime, String
from sqlalchemy.orm import sessionmaker, scoped_session, object_session
from sqlalchemy.orm import mapper, class_mapper, clear_mappers, reconstructor

# Local
from jsontype import JsonType

# Global session maker
Session = scoped_session(sessionmaker(autoflush=True, autocommit=False))

# Global metadata instance
metadata = None

# Model configuration
def configure(dburi):
    global metadata

    engine = create_engine(dburi, echo=False)
    metadata = MetaData(bind=engine)
    Session.configure(bind=engine)

    # Annotation table
    annotation_table = Table('annotation', metadata,
        Column('id', Unicode(36), primary_key=True, default=lambda:unicode(uuid.uuid4())),
        Column('uri', UnicodeText),
        Column('ranges', JsonType),
        Column('text', UnicodeText),
        Column('quote', UnicodeText),
        Column('created', String(26), default=lambda:str(datetime.now())),
        Column('user', UnicodeText),
        Column('tags', JsonType),
        Column('extras', JsonType),
    )

    clear_mappers()
    mapper(Annotation, annotation_table)

def createdb():
    logger.info('Creating db')
    metadata.create_all()

def cleandb():
    metadata.drop_all()
    logger.info('Cleaned db')

def rebuilddb():
    cleandb()
    createdb()

class Annotation(object):
    def __init__(self, **kwargs):
        self.reconstruct()
        self.merge_dict(kwargs)

    @reconstructor
    def reconstruct(self):
        self.extras = {}
        self.table = class_mapper(self.__class__).mapped_table

    def __str__(self):
        out = u'<%s %s>' % (self.__class__.__name__, self.as_dict())
        return out.encode('utf8', 'ignore')

    def as_dict(self):
        out = {}

        for col in self.table.c.keys():
            val = getattr(self, col)
            if isinstance(val, datetime):
                val = unicode(val)
            out[col] = val

        if out['extras']:
            for k,v in out['extras'].items():
                out[k] = v

        del out['extras']

        return out

    def merge_dict(self, anno_dict):
        attrnames = self.table.c.keys()

        for k, v in anno_dict.items():
            if k in attrnames:
                setattr(self, k, v)
            else:
                self.extras[k] = v

        return self

    @classmethod
    def from_dict(cls, anno_dict):
        anno = Annotation()
        return anno.merge_dict(anno_dict)