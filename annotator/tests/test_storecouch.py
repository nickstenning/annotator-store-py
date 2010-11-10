import json

import paste.proxy
import paste.fixture, routes.util

from annotator.store import AnnotatorStore
from annotator.tests.test_store import AnnotatorStoreTestBase
from annotator.storecouch import rebuild_db, setup_db
DBNAME = 'annotations'
DB = setup_db(DBNAME)

class TestModel:
    def setup(self):
        self.db = rebuild_db('annotator-test')
        self.uri = 'http://abc.com/'
        testdata = {
            'uri': self.uri,
            'note': u'My note'
        }
        self.docid = self.db.create(testdata)

    def test_01(self):
        doc =  self.db[self.docid]
        assert doc['uri'] == self.uri
    
    def test_02_views(self):
        view = self.db.view('annotator/all')
        assert view.total_rows == 1
        for row in view: 
            assert row.id

class TestStoreCouch(AnnotatorStoreTestBase):
    def __init__(self, *args, **kwargs):
        self.proxy_base_url = 'http://localhost:5984/'
        self.store = paste.proxy.Proxy(self.proxy_base_url) 
        self.app   = paste.fixture.TestApp(self.store)
        # TODO: remove this dependency
        self.url   = routes.util.URLGenerator(AnnotatorStore().mapper, {})

    def setup(self):
        rebuild_db(DBNAME)

    def teardown(self):
        # rebuild_db()
        pass
    
    def _create_annotation(self, **kwargs):
        anno = dict(**kwargs)
        DB.save(anno)
        # cross-compatibility with normal setup
        anno['id'] = anno['_id']
        return anno

    def create_test_annotation(self):
        anno = self._create_annotation(uri=u'http://xyz.com', range=u'1.0 2.0', text=u'blah text')
        return anno

    def test_annotate_index(self):
        anno = self.create_test_annotation()
        resp = self.app.get(self.url('annotations'))

        assert resp.status == 200, "Response code was not 200 OK."

    def _check_create(self, respId, params):
        # guaranteed to be correct
        pass

    def _check_update(self, _id, params):
        # guaranteed to be correct
        pass

    def _check_delete(self, _id):
        out = DB.get(_id)
        assert out is None, "Annotation was not deleted"

    def test_search(self):
        uri1 = u'http://xyz.com'
        uri2 = u'urn:uuid:xxxxx'
        user = u'levin'
        user2 = u'anna'
        anno = self._create_annotation(
                uri=uri1,
                text=uri1,
                user=user,
                )
        anno2 = self._create_annotation(
                uri=uri1,
                text=uri1 + uri1,
                user=user2,
                )
        anno3 = self._create_annotation(
                uri=uri2,
                text=uri2,
                user=user
                )

        # url = self.url('search_annotations')
        base_url= '/annotations/_design/annotator/_view/'
        all_query = base_url + 'all'
        res = self.app.get(all_query)
        body = json.loads(res.body)
        assert body['total_rows'] == 3, body
        assert len(body['rows']) == 3

        url = all_query + '?limit=1'
        res = self.app.get(url)
        body = json.loads(res.body)
        assert body['total_rows'] == 3, body
        assert len(body['rows']) == 1

        uri_query = base_url + 'byuri'
        url = uri_query + '?key=""'
        res = self.app.get(url)
        body = json.loads(res.body)
        assert len(body['rows']) == 0, body

        url = uri_query + '?key="%s"' % uri1
        res = self.app.get(url)
        body = json.loads(res.body)
        # results of form {'id': ..., 'key':..., 'value': ...}
        assert 'id' in body['rows'][0].keys(), body['rows']

        url = uri_query + '?key="%s"&include_docs=true' % uri1
        res = self.app.get(url)
        body = json.loads(res.body)
        assert body['total_rows'] == 3, body
        out = body['rows']
        assert len(out) == 2
        assert out[0]['doc']['uri'] == uri1, out
        assert out[0]['id'] in [ anno['id'], anno2['id'] ]

        # default is to show all results 
        # url = all_query + '?limit=-1'
        # res = self.app.get(url)
        # body = json.loads(res.body)
        # assert len(body['rows']) == 3, body

    def test_annotate_cors_preflight(self):
        pass

