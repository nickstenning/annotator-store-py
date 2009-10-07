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
from routes import *

import annotator.model as model

logger = logging.getLogger('annotator')

class AnnotatorStore(object):
    "Application to provide 'annotation' store."

    DEBUG = False

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
        map.connect(self.service_path + '/annotation/delete/:id',
                controller='annotation',
                action='delete',
                conditions=dict(method=['GET']))
        map.connect(self.service_path + '/annotation/edit/:id',
                controller='annotation',
                action='edit',
                conditions=dict(method=['GET']))

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
        self.map = self.get_routes_mapper()
        self.map.environ = environ
        self.start_response = start_response
        self.path = environ['PATH_INFO']
        self.mapdict = self.map.match(self.path)
        action = self.mapdict['action']
        self.query_vals = paste.request.parse_formvars(self.environ)
        for k,v in self.query_vals.items():
            # some reason we are not getting unicode back!
            if isinstance(v, basestring):
                self.query_vals[k] = unicode(v)

        self.format = self.query_vals.get('format', 'json')
        if self.format not in ['json']:
            status = '500 Internal server error'
            result = 'Unknown format: %s' % self.format
            response_headers = [ ('Content-type', 'text/plain'), ]
            self.start_response(status, response_headers)
            return [str(result)]

        if self.DEBUG:
            logger.debug('** CALL TO ANNOTATE')
            logger.debug('path: %s' % self.path)
            logger.debug('environ: %s' % environ)
            logger.debug('mapdict: %s' % self.mapdict)
            logger.debug('query_vals: %s' % self.query_vals)

        if action == 'index':
            return self.index()
        elif action == 'show':
            return self.show()
        elif action == 'create':
            return self.create()
        elif action == 'update':
            return self.update()
        elif action == 'delete':
            return self.delete()
        else:
            self._404()
            return ['Not found or method not allowed']

    json_headers = [ ('Content-type', 'application/json') ]

    def _404(self):
        status = '404 Not Found'
        response_headers = [ ('Content-type', 'text/plain'), ]
        self.start_response(status, response_headers)

    def _dump(self, _struct):
        out = json.dumps(_struct)
        return out.encode('utf8', 'ignore')

    def index(self):
        status = '200 OK'
        result = ''
        response_headers = [ ('Content-type', 'application/xml') ]
        result = []
        for anno in model.Annotation.query.limit(100).all():
            result.append(anno.as_dict())
        self.start_response(status, self.json_headers)
        return [self._dump(result)]

    def show(self):
        id = self.mapdict['id']
        anno = model.Annotation.query.get(id)
        if not anno:
            self._404()
            return ['Not found']

        result = anno.as_dict()
        status = '200 OK'
        self.start_response(status, self.json_headers)
        return [self._dump(result)]
    
    def create(self):
        if 'json' in self.query_vals:
            params = json.loads(self.query_vals['json'])
        else:
            params = dict(self.query_vals)
        if isinstance(params, list):
            for objdict in params:
                anno = model.Annotation.from_dict(objdict)
        else:
            anno = model.Annotation.from_dict(params)
        model.Session.commit()
        status = '201 Created'
        location = '/%s/%s' % (self.service_path, anno.id)
        response_headers = [
                ('Content-type', 'text/html'),
                ('Location', location)
                ]
        self.start_response(status, response_headers)
        return ['']

    def update(self):
        id = self.mapdict['id']
        try:
            existing = model.Annotation.query.get(id)
        except:
            status = '400 Bad Request'
            response_headers = [
                ('Content-type', 'text/html'),
                ]
            self.start_response(status, response_headers)
            msg = '<h1>400 Bad Request</h1><p>No such annotation #%s</p>' % id
            return [msg]
        if 'json' in self.query_vals:
            params = json.loads(self.query_vals['json'])
        else:
            params = dict(self.query_vals)
        params['id'] = id
        anno = model.Annotation.from_dict(params)
        model.Session.commit()
        status = '204 Updated'
        response_headers = []
        self.start_response(status, response_headers)
        return ['']

    def delete(self):
        id = self.mapdict['id']
        response_headers = [ ('Content-type', 'text/html'), ]
        if id is None:
            status = '400 Bad Request'
            response_headers = [ ('Content-type', 'text/html'), ]
            self.start_response(status, response_headers)
            return ['<h1>400 Bad Request</h1><p>Bad ID</p>']
        else:
            status = '204 Deleted'
            try:
                model.Annotation.delete(id)
                response_headers = [ ]
                self.start_response(status, response_headers)
                return []
            except Exception, inst:
                status = '500 Internal server error'
                self.start_response(status, response_headers)
                return ['<h1>500 Internal Server Error</h1>Delete failed\n %s'%
                        inst]
    
