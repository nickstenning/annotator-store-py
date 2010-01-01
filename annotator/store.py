"""Annotation storage.

TODO:

1. Move to templates for annotator store forms (?)
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

    def get_routes_mapper(self):
        # some extra additions to standard layout from map.resource
        # help to make the url layout a bit nicer for those using the web ui
        map = Mapper()
        map.connect(self.service_path + 'debug', controller='annotation', action='debug')
        map.connect(self.service_path + '/annotation/delete/:id',
                controller='annotation',
                action='delete',
                conditions=dict(method=['GET']))
        map.connect(self.service_path + '/annotation/edit/:id',
                controller='annotation',
                action='edit',
                conditions=dict(method=['GET']))

        # PUT does not seem connected to create by default
        map.connect(self.service_path + '/annotation',
                controller='annotation',
                action='create',
                conditions=dict(method=['PUT', 'POST']))

        map.resource('annotation', 'annotation', path_prefix=self.service_path)

        # map.resource assumes PUT for update but we want to use POST as well
        # exact mappings for REST seems a hotly contested matter see e.g.
        # http://www.megginson.com/blogs/quoderat/archives/2005/04/03/post-in-rest-create-update-or-action/
        # must have this *after* map.resource as otherwise overrides the create
        # action
        map.connect(self.service_path + '/annotation/:id',
                controller='annotation',
                action='update',
                conditions=dict(method=['POST']))
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

    def _set_json_header(self):
        self.response.content_type = 'application/json'

    def _404(self):
        self.response.status = 404
        self.response.body = 'Not found'

    def _dump(self, _struct):
        out = json.dumps(_struct)
        # return out.encode('utf8', 'ignore')
        return unicode(out)

    def debug(self):
        self.response.content_type = 'text/plain'
        return self.request.params.items()

    def index(self):
        result = []
        for anno in model.Annotation.query.limit(100).all():
            result.append(anno.as_dict())
        self._set_json_header()
        return self._dump(result)

    def show(self):
        id = self.mapdict['id']
        anno = model.Annotation.query.get(id)
        if not anno:
            self._404()
            return ['Not found']
        self._set_json_header()
        result = anno.as_dict()
        return self._dump(result)
    
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
        location = '/%s/%s' % (self.service_path, anno.id)
        self.response.headers['location'] = location
        return u''

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
    
