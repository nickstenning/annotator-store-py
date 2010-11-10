import os
import json
import time

import couchdb
import couchdb.design

couch = couchdb.Server()

def setup_db(dbname):
    if dbname in couch:
        return couch[dbname]
    else:
        db = couch.create(dbname)
        setup_views(db)
        return db

def rebuild_db(dbname):
    if dbname in couch:
        del couch[dbname]
    return setup_db(dbname)


# Required views
# query by document
# query by user
# query by document and user
# query 
# TODO: general, change from all_fields to include_docs=True ?
# Remove offset ....?
# limit the same
# results format is different: {'total_rows': 3, 'offset':', 'rows': ..
# as opposed to {'total': ,'results': ...}
# could sort this out with a list function ...
def setup_views(db):
    design_doc = 'annotator'
    view = couchdb.design.ViewDefinition(design_doc, 'all', '''
function(doc) {
    emit(doc._id, null);
}
'''
    )
    view.get_doc(db)
    view.sync(db)

    view = couchdb.design.ViewDefinition(design_doc, 'byuri', '''
function(doc) {
    if(doc.uri) {
        emit(doc.uri, null);
    }
}
'''
    )
    view.get_doc(db)
    view.sync(db)


if __name__ == '__main__':
    rebuild_db('annotations')

