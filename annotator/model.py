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
try:
    from vdm.sqlalchemy import RevisionedObjectMixin, StatefulObjectMixin, make_revisioned_table, Revisioner, make_revision_table
except ImportError:
    class Dummy(object): pass
    RevisionedObjectMixin = Dummy
    StatefulObjectMixin = object

# Client libraries should set Session using their sqlalchemy Session
# We configure it in Repository.configure
Session = None


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


def make_annotation_table(metadata, make_revisioned=False):
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
        Column('user', UnicodeText),
        Column('tags', JsonType),
        Column('extras', JsonType),
        )
    if make_revisioned:
        annotation_revision_table = make_revisioned_table(annotation_table)
        revision_table = make_revision_table(metadata)
    else:
        annotation_revision_table = None
    return [annotation_table, annotation_revision_table]


class Annotation(RevisionedObjectMixin,StatefulObjectMixin):

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
        if out['extras']:
            for k,v in out['extras'].items():
                out[k] = v
        del out['extras']
        return out

    @classmethod
    def from_dict(cls, _dict):
        id = _dict.get('id', None)
        if id:
            anno = Annotation.query.get(id)
        else:
            anno = Annotation()
            # assert anno is not None
        table = class_mapper(cls).mapped_table
        attrnames = table.c.keys()
        for k,v in _dict.items():
            if k in attrnames:
                setattr(anno, k, v)
            # Support ranges as well as range
            # TODO: decide whether we have range or ranges
            elif k == 'ranges':
                if _dict['ranges']:
                    anno.range = _dict['ranges'][0]
            else:
                anno.extras = anno.extras or {}
                anno.extras[k] = v
        return anno

def map_annotation_object(mapper, annotation_table,
        annotation_revision_table=None, make_revisioned=False):
    '''Map Annotation object with supplied mapper and annotation_table.
    '''
    if make_revisioned:
        mapper(Annotation, annotation_table,
            extension=Revisioner(annotation_revision_table)
            )
    else:
        mapper(Annotation, annotation_table)


class Repository(object):

    def configure(self, dburi):
        from sqlalchemy import MetaData
        from sqlalchemy.orm import scoped_session, sessionmaker, create_session
        engine = create_engine(dburi, echo=False)

        self.metadata = MetaData()
        self.metadata.bind = engine
        # have to do annotator.model.Session =, rather than
        # Session = (o/w just binds to a local variable)
        import annotator.model
        annotator.model.Session = scoped_session(sessionmaker(
            autoflush=True,
            autocommit=False,
            ))
        annotator.model.Session.bind = engine
        mapper = Session.mapper

        make_revisioned = False
        anno_table,anno_rev_table = make_annotation_table(self.metadata,
                make_revisioned)
        map_annotation_object(mapper, anno_table, anno_rev_table, make_revisioned)

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
