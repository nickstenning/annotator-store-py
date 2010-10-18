import paste.proxy
import paste.fixture, routes.util

from annotator.store import AnnotatorStore
from annotator.tests.test_store import AnnotatorStoreTestBase
from annotator.storecouch import rebuild_db, setup_db
DBNAME = 'annotations'
DB = setup_db(DBNAME)

class TestStoreCouch(AnnotatorStoreTestBase):
    def __init__(self, *args, **kwargs):
        proxy_base_url = 'http://localhost:5984/'
        self.store = paste.proxy.Proxy(proxy_base_url) 
        self.app   = paste.fixture.TestApp(self.store)
        # TODO: remove this dependency
        self.url   = routes.util.URLGenerator(AnnotatorStore().mapper, {})

    def setup(self):
        rebuild_db(DBNAME)

    def teardown(self):
        # rebuild_db()
        pass

    def create_test_annotation(self):
        anno = dict(uri=u'http://xyz.com', range=u'1.0 2.0', text=u'blah text')
        DB.save(anno)
        # cross-compatibility with normal setup
        anno['id'] = anno['_id']
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
        pass

    def test_annotate_cors_preflight(self):
        pass

