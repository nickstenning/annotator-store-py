import annotator.model as model
import annotator.store as store

try:
    import json
except ImportError:
    import simplejson as json

class TestRoutes(object):

    resource_routes = [
        ('GET',    '%s',        'index'),
        ('POST',   '%s',        'create'),
        ('PUT',    '%s/1',      'update'),
        ('DELETE', '%s/1',      'delete'),
        ('GET',    '%s/1',      'show'),

        ('GET',    '%s/search', 'search'), # Custom addition for search
    ]

    def __init__(self, *args, **kwargs):
        self.mount_point   = '/.annotation-xyz'
        self.resource_name = ('foobar', 'foobars')
        self.store         = store.AnnotatorStore(
                               mount_point=self.mount_point,
                               resource_name=self.resource_name
                             )

    def test_map_resource_routes(self):
        for method, url, action in self.resource_routes:
            base = self.mount_point + '/' + self.resource_name[1]
            url = url % base

            self.store.mapper.environ = { 'REQUEST_METHOD' : method }
            out = self.store.mapper.match(url)

            assert out, \
                "Router did not match '%s %s'." % (method, url)

            assert out['action'] == action, \
                "Action '%s' for '%s %s' was not '%s'." % (out['action'], method, url, action)

class TestAnnotatorStore(object):

    def __init__(self, *args, **kwargs):
        import paste.fixture, routes.util
        self.store = store.AnnotatorStore()
        self.app   = paste.fixture.TestApp(self.store)
        self.url   = routes.util.URLGenerator(self.store.mapper, {})

    def teardown(self):
        model.Session.query(model.Annotation).delete()
        model.Session.commit()
        model.Session.remove()

    def create_test_annotation(self):
        anno = model.Annotation(uri=u'http://xyz.com', range=u'1.0 2.0', text=u'blah text')
        model.Session.commit()
        anno = anno.as_dict()
        model.Session.remove()
        return anno

    def test_annotate_index(self):
        anno = self.create_test_annotation()
        resp = self.app.get(self.url('annotations'))

        assert resp.status == 200, "Response code was not 200 OK."

        assert resp.body == json.dumps([anno]), \
            "Response was not the expected JSON list of annotations."

        assert len(json.loads(resp.body)) == 1, \
            "Response did not contain 1 annotation."

        assert json.loads(resp.body)[0]['uri'] == anno['uri'], \
            "The URI of the first annotation in the response was wrong."

    def test_annotate_show(self):
        anno = self.create_test_annotation()
        rsrc = self.url('annotation', id=anno['id'])
        resp = self.app.get(rsrc)

        assert anno['text']  in resp, "Result did not contain annotation text."
        assert anno['range'] in resp, "Result did not contain annotation range."

    def test_annotate_show_not_found(self):
        rsrc = self.url('annotation', id='nonexistent')
        resp = self.app.get(rsrc, expect_errors=True)

        assert resp.status == 404, "Response code was not 404 Not Found."

    def test_annotate_create(self):
        params = {
            'text': 'any old thing',
            'uri': 'http://localhost/',
            'ranges': [{'start': 'p', 'end': 'p'}]
        }
        jsonVal = json.dumps(params)

        url    = self.url('annotations')
        resp   = self.app.post(url, {'json': jsonVal})
        respId = json.loads(resp.body)['id']

        # Check response code
        assert resp.status == 201, "Response code was not 201 Created."

        # Check 'id' (not supplied) provided in response
        assert respId is not None, "'id' not set on create"

        # Check fields correctly set in database
        anno = model.Annotation.query.get(respId)
        anno = anno.as_dict()

        for k in params:
            assert anno[k] == params[k], \
                "'%s' sent to server, but not set in database." % k

        # Check response redirects to resource 'show' URL
        exp = self.url('annotation', id=anno['id'])
        loc = dict(resp.headers)['Location']
        # TODO get URLGenerator to respect HTTP_HOST
        assert loc.endswith(exp), "Location header '%s' was not '%s'" % (loc, exp)

    def test_annotate_update(self):
        anno = self.create_test_annotation()
        rsrc = self.url('annotation', id=anno['id'])

        params  = { 'text': 'This is a NEW note, a NEW note I say.' }
        jsonVal = json.dumps(params)

        resp = self.app.put(rsrc, {'json': jsonVal})

        assert resp.status == 204, "Response code was not 204 No Content."

        anno = model.Annotation.query.get(anno['id'])
        assert anno.text == params['text']

    def test_annotate_delete(self):
        anno = self.create_test_annotation()
        rsrc = self.url('annotation', id=anno['id'])
        resp = self.app.delete(rsrc)

        assert resp.status == 204, "Response code was not 204 No Content."

        tmp = model.Annotation.query.get(anno['id'])
        assert tmp is None, "Annotation was not deleted."

    def test_annotate_delete_not_found(self):
        rsrc = self.url('annotation', id='nonexistent')
        resp = self.app.delete(rsrc, expect_errors=True)

        assert resp.status == 404, "Response code was not 404 Not Found."

    def test_search(self):
        uri1 = u'http://xyz.com'
        uri2 = u'urn:uuid:xxxxx'
        user = u'levin'
        user2 = u'anna'
        anno = model.Annotation(
                uri=uri1,
                text=uri1,
                user=user,
                )
        anno2 = model.Annotation(
                uri=uri1,
                text=uri1 + uri1,
                user=user2,
                )
        anno3 = model.Annotation(
                uri=uri2,
                text=uri2,
                user=user
                )
        model.Session.commit()
        annoid = anno.id
        anno2id = anno2.id
        model.Session.remove()

        url = self.url('search_annotations')
        res = self.app.get(url)
        body = json.loads(res.body)
        assert body['total'] == 3, body

        url = self.url('search_annotations', limit=1)
        res = self.app.get(url)
        body = json.loads(res.body)
        assert body['total'] == 3, body
        assert len(body['results']) == 1

        url = self.url('search_annotations', uri=uri1, all_fields=1)
        res = self.app.get(url)
        body = json.loads(res.body)
        assert body['total'] == 2, body
        out = body['results']
        assert len(out) == 2
        assert out[0]['uri'] == uri1
        assert out[0]['id'] in [ annoid, anno2id ]

        url = self.url('search_annotations', uri=uri1)
        res = self.app.get(url)
        body = model.json.loads(res.body)
        assert body['results'][0].keys() == ['id'], body['results']

        url = self.url('search_annotations', limit=-1)
        res = self.app.get(url)
        body = json.loads(res.body)
        assert len(body['results']) == 3, body

    def test_annotate_jsonp(self):
        anno = self.create_test_annotation()

        url = self.url('annotations', callback='jsonp1234')
        resp = self.app.get(url)

        exp = 'jsonp1234(%s);' % json.dumps([anno])

        assert resp.body == exp, "Response was not JSONP."

        url = self.url('annotation', id=anno['id'], callback='jsonp1234')
        resp = self.app.get(url)

        exp = 'jsonp1234(%s);' % json.dumps(anno)

        assert resp.body == exp, "Response was not JSONP."

    def test_annotate_cors_preflight(self):
        url = self.url('annotations')
        resp = self.app._gen_request('OPTIONS', url, headers={
            'Origin': 'http://localhost'
        })

        headers = dict(resp.headers)

        assert headers['Access-Control-Allow-Methods'] == 'GET, PUT, POST, DELETE, OPTIONS', \
            "Did not send the right Access-Control-Allow-Methods header."

        assert headers['Access-Control-Allow-Origin'] == '*', \
            "Did not send the right Access-Control-Allow-Origin header."
