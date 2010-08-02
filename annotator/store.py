"""Annotation storage.
"""
import os
import logging
try:
    import json
except ImportError:
    import simplejson as json

import paste.request
from routes import Mapper
import webob

import annotator.model as model

logger = logging.getLogger('annotator')

class AnnotatorStore(object):
    "Application to provide 'annotation' store."

    def __init__(self, service_path=''):
        """Create the WSGI application.

        @param service_path: offset url where this application is mounted.
        """
        if service_path and not service_path.startswith('/'):
            service_path = '/' + service_path
        self.service_path = service_path
        # singular or plural ...
        self.anno_rest_name = 'annotations'

    def get_routes_mapper(self):
        map = Mapper()

        ## ======================
        ## REST API: /annotations/

        # some extra additions to standard layout from map.resource
        # help to make the url layout a bit nicer for those using the web ui
        map.connect(self.service_path + '/' + self.anno_rest_name + '/delete/:id',
                controller='annotation',
                action='delete',
                conditions=dict(method=['GET']))

        # PUT does not seem connected to create by default
        map.connect(self.service_path + '/' + self.anno_rest_name,
                controller='annotation',
                action='create',
                conditions=dict(method=['PUT', 'POST']))

        map.resource('annotation', self.anno_rest_name,
                path_prefix=self.service_path, controller='annotation')

        # map.resource assumes PUT for update but we want to use POST as well
        # exact mappings for REST seems a hotly contested matter see e.g.
        # http://www.megginson.com/blogs/quoderat/archives/2005/04/03/post-in-rest-create-update-or-action/
        # must have this *after* map.resource as otherwise overrides the create
        # action
        map.connect(self.service_path + '/%s/:id' % self.anno_rest_name,
                controller='annotation',
                action='update',
                conditions=dict(method=['POST']))

        ## ==========
        ## Search API
        map.connect(self.service_path + '/search',
                controller='annotation', action='search', id=None
                )

        return map

    def __call__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.map = self.get_routes_mapper()
        self.map.environ = environ
        path = environ['PATH_INFO']
        self.mapdict = self.map.match(path)
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
            self._404()
        return self.response(environ, start_response)

    def _404(self):
        self.response.status = 404
        self.response.body = 'Not found'

    def _json(self, result):
        result_json = json.dumps(result)
        if 'callback' in self.request.params:
            self.response.content_type = 'text/javascript'
            return u'%s(%s);' % (self.request.params['callback'], result_json)
        else:
            self.response.content_type = 'application/json'
            return u'%s' % result_json

    def index(self):
        result = []
        for anno in model.Annotation.query.limit(100).all():
            result.append(anno.as_dict())
        return self._json(result)

    def show(self):
        id = self.mapdict['id']
        anno = model.Annotation.query.get(id)
        if not anno:
            self._404()
            return ['Not found']
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
        location = self.map.generate(controller='annotation', action='show', id=anno.id)
        self.response.headers['location'] = location
        return self._json({'id': anno.id})

    def update(self):
        id = self.mapdict['id']
        try:
            existing = model.Annotation.query.get(id)
        except:
            status = '400 Bad Request'
            self.response.status = 400
            msg = u'<h1>400 Bad Request</h1><p>No such annotation #%s</p>' % id
            return msg
        if 'json' in self.request.params:
            params = json.loads(self.request.params['json'])
        else:
            params = dict(self.request.params)
        params['id'] = id
        anno = model.Annotation.from_dict(params)
        anno.save_changes()
        self.response.status = 204
        return None

    def delete(self):
        id = self.mapdict['id']
        if id is None:
            self.response.status = 400
            return u'<h1>400 Bad Request</h1><p>Bad ID</p>'
        else:
            self.response.status = 204 # deleted
            try:
                model.Annotation.delete(id)
                return None
            except Exception, inst:
                self.response.status = 500
                return u'<h1>500 Internal Server Error</h1>Delete failed\n %s'% inst

    def search(self):
        params = [ (k,v) for k,v in self.request.params.items() if k not in [ 'all_fields', 'offset', 'limit' ]
                ]
        all_fields = self.request.params.get('all_fields', False)
        all_fields = bool(all_fields)
        offset = self.request.params.get('offset', 0)
        limit = int(self.request.params.get('limit', 100))
        if limit < 0:
            limit = None
        # important we use session off model.Annotation as Annotation may be
        # used by external library (and hence using an external session)
        if all_fields:
            q = model.Annotation.query
        else:
            # only supported in sqlalchemy >= 0.5
            # so have to do it the inefficient way
            # sess = model.Annotation.query.session
            # q = sess.query(model.Annotation.id)
            q = model.Annotation.query
        for k,v in params:
            kwargs = { k: unicode(v) }
            q = q.filter_by(**kwargs)
        total = q.count()
        q = q.offset(offset)
        q = q.limit(limit)
        results = q.all()
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
    app = AnnotatorStore()
    return app

