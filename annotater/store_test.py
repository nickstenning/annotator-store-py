import os
import shutil
import tempfile
import commands
from StringIO import StringIO

import twill
from twill import commands as web

import annotater.model
annotater.model.set_default_connection()
import annotater.store

class TestMapper:

    store = annotater.store.AnnotaterStore()
    map = store.get_routes_mapper()

    def test_match_double_slash(self):
        # demonstrate that double slashes mess things up!
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('//annotation/')
        assert out == None
        # assert out['action'] == 'index'

    def test_match_new(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('/annotation/new')
        assert out['action'] == 'new'

    def test_match_index(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('/annotation')
        assert out['action'] == 'index'

    def test_match_create(self):
        self.map.environ = { 'REQUEST_METHOD' : 'POST' }
        out = self.map.match('/annotation')
        assert out['action'] == 'create'

    def test_match_delete(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('/annotation/delete/1')
        assert out['action'] == 'delete'
        assert out['id'] == '1'
        self.map.environ = { 'REQUEST_METHOD' : 'DELETE' }
        out = self.map.match('/annotation/1')
        assert out['action'] == 'delete'
        assert out['id'] == '1'
        out = self.map.match('/annotation/')
        assert out['id'] == None

    def test_match_edit(self):
        self.map.environ = { 'REQUEST_METHOD' : 'GET' }
        out = self.map.match('/annotation/edit/1')
        assert out['action'] == 'edit'
        assert out['id'] == '1'
        self.map.environ = { 'REQUEST_METHOD' : 'PUT' }
        out = self.map.match('/annotation/1')
        assert out['action'] == 'update'
        assert out['id'] == '1'
        self.map.environ = { 'REQUEST_METHOD' : 'POST' }
        out = self.map.match('/annotation/1')
        assert out['action'] == 'update'

    def test_url_for_new(self):
        offset = self.map.generate(controller='annotation', action='new')
        exp = '/annotation/new'
        assert offset == exp

    def test_url_for_create(self):
        offset = self.map.generate(controller='annotation', action='create',
                method='POST' )
        exp = '/annotation'
        assert offset == exp

    def test_url_for_delete(self):
        offset = self.map.generate(controller='annotation',
                action='delete', id=1, method='GET' )
        exp = '/annotation/delete/1'
        assert offset == exp
        offset = self.map.generate(controller='annotation',
                action='delete', id=1, method='DELETE' )
        exp = '/annotation/1'
        assert offset == exp

    def test_url_for_edit(self):
        offset = self.map.generate(controller='annotation',
                action='edit', id=1, method='GET')
        exp = '/annotation/edit/1'
        assert offset == exp


class TestStatic:
    
    def test__make_annotate_form(self):
        app = annotater.store.AnnotaterStore()
        defaults = { 'url' : 'http://www.blackandwhite.com' }
        out = app._make_annotate_form(form_name='formname', action_url='.',
                form_defaults=defaults)
        exp1 = '<label for="url">url:</label><input name="url" id="url" \
value="%s" /><br />' % defaults['url']
        assert exp1 in out


class TestAnnotaterStore:

    store = annotater.store.AnnotaterStore()
    map = store.get_routes_mapper()

    def setup_method(self, name=''):
        twill.add_wsgi_intercept('localhost', 8080, lambda : self.store)
        self.outp = StringIO()
        twill.set_output(self.outp)
        self.siteurl = 'http://localhost:8080/'

    def teardown_method(self, name=''):
        # remove intercept.
        twill.remove_wsgi_intercept('localhost', 8080)

    def test_annotate_get(self):
        anno = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='index')
        url = self.siteurl + offset[1:]
        web.go(url)
        web.code(200)
        web.find(anno.url)
        web.find(anno.range)

    def test_annotate_get_atom(self):
        anno = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='index')
        url = self.siteurl + offset[1:] + '?format=atom'
        web.go(url)
        web.code(200)
        web.find(anno.note)
        web.find(anno.range)
        out = web.show()
        exp1 = '<feed xmlns:ptr="http://www.geof.net/code/annotation/"'
        assert exp1 in out

    def test_annotate_new(self):
        # exercises both create and new
        annotater.model.rebuilddb()
        offset = self.map.generate(controller='annotation', action='new',
                method='GET')
        url = self.siteurl + offset[1:]
        web.go(url)
        web.code(200)
        note = 'any old thing'
        web.fv('', 'url', 'http://localhost/')
        web.fv('', 'note', note)
        web.submit()
        web.code(201)
        # TODO make this test more selective
        items = annotater.model.Annotation.select()
        items = list(items)
        assert len(items) == 1
        assert items[0].note == note

    def test_annotate_delete(self):
        anno = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='delete',
                method='GET', id=anno.id)
        url = self.siteurl + offset[1:] + '?blah='
        web.go(url)
        web.code(204)
        tmp = annotater.model.Annotation.select(annotater.model.Annotation.q.id == anno.id)
        num = len(list(tmp))
        assert num == 0
    
    def _create_annotation(self):
        anno = annotater.model.Annotation(
                url='http://xyz.com',
                range='1.0 2.0',
                note='blah note',
                )
        return anno

    def test_annotate_edit(self):
        anno = self._create_annotation()
        offset = self.map.generate(controller='annotation', action='edit',
                id=anno.id, method='GET')
        url = self.siteurl + offset[1:]
        web.go(url)
        web.code(200)
        newnote = u'This is a NEW note, a NEW note I say.'
        web.fv('', 'note', newnote)
        web.submit()
        web.code(204)
        assert anno.note == newnote
    
    def test_not_found(self):
        offset = self.map.generate(controller='annotation')
        url = self.siteurl + offset[1:] + '/blah'
        web.go(url)
        web.code(404)

    def test_bad_request(self):
        offset = self.map.generate(controller='annotation', action='edit',
                method='GET')
        url = self.siteurl + offset[1:]
        web.go(url)
        web.code(400)
        

