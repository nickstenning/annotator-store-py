"""Annotation storage.
"""
import os
import logging
try:
    import json
except ImportError:
    import simplejson as json

import paste.request
import routes
import webob

import annotator.model as model

logger = logging.getLogger('annotator')

class AnnotatorStore(object):
    "Application to provide 'annotation' store."

    def __init__(self, mount_point='/', resource_name=('annotation', 'annotations')):
        """Create the WSGI application.

        @param mount_point: url where this application is mounted.
        @param resource_name: tuple (singular, plural) of the annotation resource name.
        """
        self.mapper = routes.Mapper()

        mount_point = mount_point if mount_point.startswith('/') else '/' + mount_point
        sing, plur  = resource_name

        self.mapper.resource(
            sing,
            plur,
            path_prefix = mount_point,
            collection = {
                'search': 'GET'
            }
        )

        with self.mapper.submapper(
            action='_cors_preflight',
            path_prefix=mount_point,
            conditions=dict(method=["OPTIONS"])
        ) as m:
            m.connect(None, plur)
            m.connect(None, plur + '/{id}')

    def __call__(self, environ, start_response):
        self.mapper.environ = environ
        self.url = routes.util.URLGenerator(self.mapper, environ)

        path = environ['PATH_INFO']
        self.mapdict = self.mapper.match(path)
        self.request = webob.Request(environ)
        self.response = webob.Response(charset='utf8')
        self.format = self.request.params.get('format', 'json')

        if self.format not in ['json']:
            self.response.status = 500
            self.response.body = 'Unknown format: %s' % self.format
            return self.response(environ, start_response)

        if self.mapdict is not None:
            action = self.mapdict['action']
            method = getattr(self, action)
            out = method()
            if out is not None:
                self.response.unicode_body = out
            if self.response.status_int == 204:
                del self.response.headers['content-type']
        else:
            self.response.unicode_body = self._404()

        return self.response(environ, start_response)

    def _204(self):
        self.response.status = 204
        return None

    def _400(self):
           self.response.status = 400
           return u'Bad Request'

    def _404(self):
        self.response.status = 404
        return u'Not Found'

    def _500(self):
        self.response.status = 500
        return u'Internal Server Error'

    def _json(self, result):
        result_json = json.dumps(result)
        if 'callback' in self.request.params:
            self.response.content_type = 'text/javascript'
            return u'%s(%s);' % (self.request.params['callback'], result_json)
        else:
            self.response.content_type = 'application/json'
            return u'%s' % result_json

    def _cors_preflight(self):
        if 'Origin' in self.request.headers:
            self.response.headers.update({
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
                'Access-Control-Max-Age': '86400',
            })
            return self._204()
        else:
            return self._400()

    def index(self):
        result = []
        for anno in model.Annotation.query.limit(100).all():
            result.append(anno.as_dict())
        return self._json(result)

    def show(self):
        id = self.mapdict['id']
        anno = model.Annotation.query.get(id)

        if not anno:
            return self._404()

        result = anno.as_dict()
        return self._json(result)

    def create(self):
        if 'json' in self.request.params:
            params = json.loads(self.request.params['json'])
        else:
            params = dict(self.request.params)
        if isinstance(params, list):
            for objdict in params:
                anno = model.Annotation.from_dict(objdict)
        else:
            anno = model.Annotation.from_dict(params)
        anno.save_changes()

        self.response.status = 201
        self.response.headers['Location'] = self.url('annotation', id=anno.id)

        result = anno.as_dict()
        return self._json(result)

    def update(self):
        id = self.mapdict['id']

        anno = model.Annotation.query.get(id)

        if not anno:
            return self._404()

        if 'json' in self.request.params:
            params = json.loads(self.request.params['json'])
        else:
            params = dict(self.request.params)

        params['id'] = id
        anno = model.Annotation.from_dict(params)
        anno.save_changes()

        return self._204()

    def delete(self):
        id = self.mapdict['id']

        anno = model.Annotation.query.get(id)

        if not anno:
            return self._404()

        try:
            model.Annotation.delete(id)

            return self._204()
        except:
            return self._500()

    def search(self):
        params = [
            (k,v) for k,v in self.request.params.items() if k not in [ 'all_fields', 'offset', 'limit' ]
        ]

        all_fields = self.request.params.get('all_fields', False)
        all_fields = bool(all_fields)

        offset = self.request.params.get('offset', 0)
        limit = int(self.request.params.get('limit', 100))

        if limit < 0:
            limit = None

        q = model.Annotation.query

        for k,v in params:
            kwargs = { k: unicode(v) }
            q = q.filter_by(**kwargs)

        total = q.count()
        results = q.offset(offset).limit(limit).all()

        if all_fields:
            results = [ x.as_dict() for x in results ]
        else:
            results = [ {'id': x.id} for x in results ]

        qresults = {
            'total': total,
            'results': results
        }

        return self._json(qresults)


def make_app(global_config, **local_conf):
    '''Make a wsgi app and return it

    Designed for use by paster or modwsgi etc
    '''
    dburi = local_conf['dburi']
    model.repo.configure(dburi)
    model.repo.createdb()

    app = AnnotatorStore(mount_point=local_conf.get('mount_point') or '/')
    return app

