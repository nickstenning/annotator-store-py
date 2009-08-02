import os
import wsgiref.util
import logging
logger = logging.getLogger('annotater')
logging.basicConfig(level=logging.INFO, filename='annotater-debug.log',
        filemode='w')
logger.info('START LOGGING')

import paste.request

import annotater.model
annotater.model.set_default_connection()
annotater.model.createdb()
import annotater.store
import annotater.js

# Offset url to annotation store 
# Because of hard-coding in the marginalia js libraries this *must* be set to
# '/annotation'
service_path = '/annotation'

# misc config
this_directory = os.path.dirname(__file__)
html_doc_path = os.path.join(this_directory, '../demo/demo.html')

# where we put the marginalia js
media_mount_path = '/'
# host where are running the app
host = 'http://localhost:5000/'

class AnnotaterDemo(object):

    def __call__(self, environ, start_response):
        self.store = annotater.store.AnnotaterStore()
        self.media_app = annotater.js.MarginaliaMedia(media_mount_path)
        self.path = environ['PATH_INFO']
        if self.path.startswith('/debug'):
            return wsgiref.simple_server.demo_app(environ, start_response)
        elif self.path.endswith('.js') or self.path.endswith('.css'):

            return self.media_app(environ, start_response)
        elif self.path.startswith(service_path):
            return self.store(environ, start_response)
        else:
            logger.info('Call to %s' % self.path)
            status = '200 OK'
            response_headers = [('Content-type','text/html')]
            start_response(status, response_headers)
            out = file(html_doc_path).read()
            # use the uri as the identifier
            uri = wsgiref.util.request_uri(environ)
            media = annotater.js.get_media_header(media_mount_path,
                    host,
                    uri)
            buttons = annotater.js.get_buttons(uri)
            values = {
                    'marginalia_media'   : media,
                    'annotation_buttons' : buttons,
                    'page_uri'           : uri,
                    }
            out = out % values
            return [out]

def make_app(global_config, **local_conf):
    app = AnnotaterDemo()
    return app


if __name__ == '__main__': 
    app = make_app()
    import paste.httpserver
    paste.httpserver.serve(app)

