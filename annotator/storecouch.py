import os
import json
import time

import couchdb

couch = couchdb.Server()
DB = None

def setup_db(dbname):
    if dbname in couch:
        return couch[dbname]
    else:
        db = couch.create(dbname)
        return db

def rebuild_db(dbname):
    if dbname in couch:
        del couch[dbname]
    DB = couch.create(dbname)


def test_01():
    rebuild_db('annotator-test')
    testdata = {
        'uri': 'http://abc.com/',
        'note': u'My note'
    }
    DB.update([testdata])


