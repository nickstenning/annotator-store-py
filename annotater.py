"""
Annotation of a web resource.

@copyright: (c) 2006 Open Knowledge Foundation
@author: Rufus Pollock (Open Knowledge Foundation)
@license: MIT License <http://www.opensource.org/licenses/mit-license.php>
"""
import os

import wsgiref.simple_server
import paste.request
# import genshi.template
# import genshi.output

from routes import *

# annotater stuff
import model

# absolute url to annotation service
# this should go
service_path = '/annotation'

map = Mapper()
map.connect('annotation/delete/:id', controller='annotation', action='delete',
        conditions=dict(method=['GET']))
map.connect('annotation/edit/:id', controller='annotation', action='edit',
        conditions=dict(method=['GET']))

map.resource('annotation')

# map.resource assumes PUT for update but marginalias uses POST
# the exacting mappings for REST seems a hotly contested matter see e.g.
# http://www.megginson.com/blogs/quoderat/archives/2005/04/03/post-in-rest-create-update-or-action/
# must have this *after* map.resource as otherwise overrides the create action
map.connect('annotation/:id', controller='annotation', action='update',
    conditions=dict(method=['POST']))

# misc config
marginalia_path = os.path.abspath('./marginalia')
html_doc_path = os.path.join(marginalia_path, 'index.html')


import logging
def setup_logging():
    level = logging.DEBUG
    logger = logging.getLogger('annotater')
    logger.setLevel(level)
    log_file_path = 'debug.log'
    fh = logging.FileHandler(log_file_path, 'w')
    fh.setLevel(level)
    logger.addHandler(fh)
    logger.info('START LOGGING')
    return logger

logger = setup_logging()

class AnnotaterApp(object):

    def __init__(self):
        pass
    
    def __call__(self, environ, start_response):
        self.environ = environ
        self.map = map
        self.map.environ = environ
        self.start_response = start_response
        self.path = environ['PATH_INFO']
        logger.debug(self.path)
        # special test cases
        if self.path.startswith('/debug'):
            return wsgiref.simple_server.demo_app(environ, start_response)
        elif self.path.startswith('/_js/'):
            status = '200 OK'
            response_headers = [('Content-type','text/plain')]
            start_response(status, response_headers)
            jspath = os.path.join(marginalia_path, self.path[5:])
            jsfile = file(jspath).read()
            return [jsfile]
        elif self.path.endswith('.js') or self.path.endswith('.css'):
            status = '200 OK'
            if self.path.endswith('.js'): filetype = 'text/javascript'
            else: filetype = 'text/css'
            response_headers = [('Content-type', filetype)]
            start_response(status, response_headers)
            jspath = os.path.join(marginalia_path, self.path[1:])
            jsfile = file(jspath).read()
            return [jsfile]
        elif self.path.startswith('/example-annotations.xml'):
            status = '200 OK'
            filetype = 'text/xml'
            response_headers = [('Content-type', filetype)]
            start_response(status, response_headers)
            jspath = os.path.join(marginalia_path, self.path[1:])
            jsfile = file(jspath).read()
            return [jsfile]
        elif self.path.startswith(service_path):
            return self.annotate()
        else:
            logger.info('Call to base url /')
            status = '200 OK'
            response_headers = [('Content-type','text/html')]
            start_response(status, response_headers)
            out = file(html_doc_path).read()
            return [out]

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
         

    def annotate(self):
        query_vals = paste.request.parse_formvars(self.environ)
        request_method = self.environ['REQUEST_METHOD']
        mapdict = self.map.match(self.path)
        format = query_vals.get('format', 'html')
        logger.debug('CALL TO ANNOTATE')
        logger.debug(self.path)
        logger.debug(query_vals)
        logger.debug(self.environ['QUERY_STRING'])
        logger.debug(request_method)
        logger.debug('mapdict: %s' % mapdict)
        action = mapdict['action']
        anno_schema = model.AnnotationSchema()

        if action == 'index':
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
        elif action == 'new':
            status = '200 OK'
            response_headers = [
                    ('Content-type', 'text/html'),
                    ]
            posturl = self.map.generate(controller='annotation', action='create')
            form = \
'''<html>
    <head></head>
    <body>
        <form name='annotation_create' action="%s" method="POST">
           <label>url:</label> <input name="url" id="url" /><br />
           <label>range:</label><input name="range" id="range" /><br />
           <label>note:</label><input name="note" id="note" /><br />
           <input type="submit" name="submission" value="send the form" />
       </form>
    </body>
</html>''' % posturl
            self.start_response(status, response_headers)
            return [ form ]
        elif action == 'create':
            url = query_vals.get('url')
            range = query_vals.get('range', 'NO RANGE')
            note = query_vals.get('note', 'NO NOTE')
            anno = model.Annotation(
                    url=url,
                    range=range,
                    note=note)
            status = '201 Created'
            location = '/annotation/%s' % anno.id
            response_headers = [
                    ('Content-type', 'text/html'),
                    ('Location', location)
                    ]
            self.start_response(status, response_headers)
            return ['']
        elif action == 'edit':
            id = mapdict['id']
            try:
                id = int(id)
            except:
                status = '400 Bad Request'
                response_headers = [
                    ('Content-type', 'text/html'),
                    ]
                self.start_response(status, response_headers)
                msg = '<h1>400 Bad Request</h1><p>No such annotation #%s</p>' % id
                return [msg]
            anno = model.Annotation.get(id)
            posturl = self.map.generate(controller='annotation',
                    action='update', id=anno.id, method='POST')
            print 'Post url:', posturl
            form_defaults = anno_schema.from_python(anno)
            form = self._make_annotate_form('annotate_edit', posturl,
                    form_defaults)
            status = '200 OK'
            response_headers = [
                    ('Content-type', 'text/html'),
                    ]
            self.start_response(status, response_headers)
            return [ form ]

        elif action == 'update':
            id = mapdict['id']
            try:
                id = int(id)
            except:
                status = '400 Bad Request'
                response_headers = [
                    ('Content-type', 'text/html'),
                    ]
                self.start_response(status, response_headers)
                msg = '<h1>400 Bad Request</h1><p>No such annotation #%s</p>' % id
                return [msg]
            new_values = dict(query_vals)
            new_values['id'] = id
            # if this comes from a form POST have to remove submission field
            if new_values.has_key('submission'): # comes from post
                del new_values['submission']
            else: # comes direct from js
                # if this comes from js need to add in all the existing values 
                # for to_python to work
                # this is a bit of a hack but it the easiest way i can think of to
                # merge the values
                current = model.Annotation.get(id)
                current_defaults = anno_schema.from_python(current)
                for key in current_defaults.keys():
                    if not new_values.has_key(key):
                        new_values[key] = current_defaults[key]
                # remove attributes coming from js that we do not yet support
                del new_values['access']
            anno_edited = anno_schema.to_python(new_values)
            status = '204 Updated'
            response_headers = []
            self.start_response(status, response_headers)
            return ['']

        elif action == 'delete':
            id = mapdict['id']
            if id is None:
                status = '400 Bad Request'
                response_headers = [
                    ('Content-type', 'text/html'),
                    ]
                self.start_response(status, response_headers)
                return ['<h1>400 Bad Request</h1><p>Bad ID</p>']
            else:
                status = '204 Deleted'
                response_headers = []
                try:
                    id = int(id)
                    model.Annotation.delete(id)
                    self.start_response(status, response_headers)
                    return ['']
                except:
                    status = '500 Internal server error'
                    self.start_response(status, response_headers)
                    return ['<h1>500 Internal Server Error</h1>Delete failed']
        else:
            status = '404 Not Found'
            response_headers = [
                    ('Content-type', 'text/plain'),
                    ]
            self.start_response(status, response_headers)
            return ['Not found or method not allowed']
    

if __name__ == '__main__': 
    app = AnnotaterApp()
    import paste.httpserver
    paste.httpserver.serve(app)
