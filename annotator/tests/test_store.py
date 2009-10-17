import os
import shutil
import tempfile
import commands
from StringIO import StringIO

import annotator.model as model
import annotator.store

class TestMapper:

    service_path = '/.annotation-xyz'
    store = annotator.store.AnnotatorStore(service_path=service_path)
    map = store.get_routes_mapper()

    def test_match_double_slash(self):
        # demonstrate that double slashes mess things up!
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('//annotation/')
        assert out == None
        # assert out['action'] == 'index'

    def test_match_new(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('%s/annotation/new' % self.service_path)
        assert out['action'] == 'new'

    def test_match_index(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('%s/annotation' % self.service_path)
        assert out['action'] == 'index'

    def test_match_show(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('%s/annotation/1' % self.service_path)
        assert out['action'] == 'show'

    def test_match_create(self):
        self.map.environ = { 'REQUEST_METHOD' : 'POST' }
        out = self.map.match('%s/annotation' % self.service_path)
        assert out['action'] == 'create'

        self.map.environ = { 'REQUEST_METHOD' : 'PUT' }
        out = self.map.match('%s/annotation' % self.service_path)
        assert out['action'] == 'create'

    def test_match_delete(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('%s/annotation/delete/1' % self.service_path)
        assert out['action'] == 'delete'
        assert out['id'] == '1'
        self.map.environ = { 'REQUEST_METHOD' : 'DELETE' }
        out = self.map.match('%s/annotation/1' % self.service_path)
        assert out['action'] == 'delete'
        assert out['id'] == '1'
        out = self.map.match('%s/annotation/' % self.service_path)
        assert out['id'] == None

    def test_match_edit(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('%s/annotation/edit/1' % self.service_path)
        assert out['action'] == 'edit'
        assert out['id'] == '1'

    def test_match_update(self):
        self.map.environ = { 'REQUEST_METHOD' : 'PUT' }
        out = self.map.match('%s/annotation/1' % self.service_path)
        assert out['action'] == 'update'
        assert out['id'] == '1'
        self.map.environ = { 'REQUEST_METHOD' : 'POST' }
        out = self.map.match('%s/annotation/1' % self.service_path)
        assert out['action'] == 'update'

    def test_url_for_new(self):
        offset = self.map.generate(controller='annotation', action='new')
        exp = '%s/annotation/new' % self.service_path
        assert offset == exp

    def test_url_for_create(self):
        offset = self.map.generate(controller='annotation', action='create',
                method='POST' )
        exp = '%s/annotation' % self.service_path
        assert offset == exp

    def test_url_for_delete(self):
        offset = self.map.generate(controller='annotation',
                action='delete', id=1, method='GET' )
        exp = '%s/annotation/delete/1' % self.service_path
        assert offset == exp
        offset = self.map.generate(controller='annotation',
                action='delete', id=1, method='DELETE' )
        exp = '%s/annotation/1' % self.service_path
        assert offset == exp

    def test_url_for_edit(self):
        offset = self.map.generate(controller='annotation',
                action='edit', id=1, method='GET')
        exp = '%s/annotation/edit/1' % self.service_path
        assert offset == exp

    def test_url_for_update(self):
        offset = self.map.generate(controller='annotation',
                action='update', id=1, method='POST')
        exp = '%s/annotation/1' % self.service_path
        assert offset == exp, (offset, exp)


class TestAnnotatorStore(object):

    def __init__(self, *args, **kwargs):
        # from paste.deploy import loadapp
        # wsgiapp = loadapp('config:test.ini', relative_to=conf_dir)
        import paste.fixture
        wsgiapp = annotator.store.AnnotatorStore(service_path='/annotation-xyz')
        self.map = wsgiapp.get_routes_mapper()
        self.app = paste.fixture.TestApp(wsgiapp)

    def test_0_annotate_index(self):
        anno_id = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='index')
        res = self.app.get(offset)
        anno = model.Annotation.query.get(anno_id)
        assert anno.uri in res, res

    def test_annotate_show(self):
        anno_id = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='show',
                id=anno_id)
        res = self.app.get(offset)
        anno = model.Annotation.query.get(anno_id)
        assert anno.text in res, res
        assert anno.range in res, res

    def test_annotate_create(self):
        model.repo.rebuilddb()
        offset = self.map.generate(controller='annotation', action='create')
        text = u'any old thing'
        inparams = {'text': text, 'uri': 'http://localhost/',
                'ranges': [{'start': 'p', 'end': 'p'}]
                }
        params = { 'json': model.json.dumps(inparams) }
        print offset
        # test both put and post
        res = self.app.post(offset, params)
        res = self.app.put(offset, params)
        # TODO make this test more selective
        items = model.Annotation.query.all()
        items = list(items)
        assert len(items) == 2, len(items)
        assert items[0].text == text
        assert items[0].range == inparams['ranges'][0]

        # test posting a list
        res = self.app.post(offset, {'json': model.json.dumps(3*[inparams])})
        count = model.Annotation.query.count()
        assert count == 5, count

    def test_annotate_update(self):
        anno_id = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='update',
                id=anno_id)
        newtext = u'This is a NEW note, a NEW note I say.'
        params = { 'text': newtext }
        params = { 'json': model.json.dumps(params) }
        self.app.post(offset, params)
        model.Session.remove()
        anno = model.Annotation.query.get(anno_id)
        assert anno.text == newtext
    
    def test_annotate_delete(self):
        anno_id = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='delete',
                method='GET', id=anno_id)
        self.app.get(offset, '204')
        tmp = model.Annotation.query.get(anno_id)
        assert tmp is None
    
    def _create_annotation(self):
        anno = model.Annotation(
                uri=u'http://xyz.com',
                range=u'1.0 2.0',
                text=u'blah text',
                )
        model.Session.commit()
        anno_id = anno.id
        model.Session.remove()
        return anno_id

    def test_not_found(self):
        offset = self.map.generate(controller='annotation')
        self.app.get(offset, '404')

    def _test_bad_request(self):
        offset = self.map.generate(controller='annotation', action='edit',
                method='GET')
        self.app.get(offset, '400')
        

