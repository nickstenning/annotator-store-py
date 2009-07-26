"""Annotation storage.

TODO:

1. Move to templates for annotater store forms (?)
"""
import os
import logging

import paste.request

from routes import *

import annotater.model as model

logger = logging.getLogger('annotater')

class AnnotaterStore(object):
    "Application to provide 'annotation' store."

    DEBUG = True

    def __init__(self, service_path='annotation'):
        """Create the WSGI application.

        @param service_path: offset url where this application is mounted.
            Should be specified without leading or trailing '/'.
        """
        self.service_path = service_path

    def get_routes_mapper(self):
        # some extra additions to standard layout from map.resource
        # help to make the url layout a bit nicer for those using the web ui
        map = Mapper()
        map.connect(self.service_path + '/delete/:id',
                controller='annotation',
                action='delete',
                conditions=dict(method=['GET']))
        map.connect(self.service_path + '/edit/:id',
                controller='annotation',
                action='edit',
                conditions=dict(method=['GET']))

        map.resource(self.service_path, self.service_path)

        # map.resource assumes PUT for update but marginalias uses POST the
        # exact mappings for REST seems a hotly contested matter see e.g.
        # http://www.megginson.com/blogs/quoderat/archives/2005/04/03/post-in-rest-create-update-or-action/
        # must have this *after* map.resource as otherwise overrides the create
        # action
        map.connect(self.service_path + '/:id',
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
        # TODO: reinstate
        # self.anno_schema = model.AnnotationSchema()
        if action != 'delete':
            self.query_vals = paste.request.parse_formvars(self.environ)
            for k,v in self.query_vals.items():
                # some reason we are not getting unicode back!
                if isinstance(v, basestring):
                    self.query_vals[k] = unicode(v)
        else: 
            # DELETE from js causes paste.request.parse_formvars to hang since
            # we do not need it for delete if using clean urls just skip
            # TODO: find out why this is and fix it.
            self.query_vals = {}

        if self.DEBUG:
            logger.debug('** CALL TO ANNOTATE')
            logger.debug('path: %s' % self.path)
            logger.debug('environ: %s' % environ)
            logger.debug('mapdict: %s' % self.mapdict)
            logger.debug('query_vals: %s' % self.query_vals)


        if action == 'index':
            return self.index()
        elif action == 'create':
            return self.create()
        elif action == 'update':
            return self.update()
        elif action == 'delete':
            return self.delete()
        else:
            status = '404 Not Found'
            response_headers = [ ('Content-type', 'text/plain'), ]
            self.start_response(status, response_headers)
            return ['Not found or method not allowed']


    def _make_annotate_form(self, form_name, action_url, form_defaults):
        from formencode import htmlfill
        keys = [ 'url' , 'range', 'note' ]
        vals = {}
        for key in keys:
            vals[key] = form_defaults.get(key, '')
        formfields = ''
        for key in keys:
            formfields += \
'''            <label for="%s">%s:</label><input name="%s" id="%s" /><br />
''' % (key, key, key, key)
            
        form = \
'''<html>
    <head></head>
    <body>
        <form name="%s" action="%s" method="POST">
           %s
           <input type="submit" name="submission" value="send the form" />
       </form>
    </body>
</html>''' % (form_name, action_url, formfields)
        
        form = htmlfill.render(form, vals)
        return form

    def index(self):
        format = self.query_vals.get('format', 'html')
        status = '200 OK'
        response_headers = [ ('Content-type', 'text/html') ]
        result = ''
        if format == 'html':
            result = model.Annotation.list_annotations_html()
            result = \
'''<html>
<head>
    <title>Annotations</title>
</head>
<body>
    %s
</body>
</html>''' % (result)
        elif format == 'atom':
            response_headers = [ ('Content-type', 'application/xml') ]
            result = model.Annotation.list_annotations_atom()
        else:
            status = '500 Internal server error'
            result = 'Unknown format: %s' % format
        self.start_response(status, response_headers)
        return [result]
    
    def create(self):
        url = self.query_vals.get('url')
        range = self.query_vals.get('range', u'NO RANGE')
        note = self.query_vals.get('note', u'NO NOTE')
        anno = model.Annotation(
                url=url,
                range=range,
                note=note)
        model.Session.commit()
        status = '201 Created'
        location = '/annotation/%s' % anno.id
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
        new_values = dict(self.query_vals)
        new_values['id'] = id
        for k,v in new_values.items():
            setattr(existing, k, v)
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
    
