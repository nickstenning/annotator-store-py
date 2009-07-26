import os
import wsgiref.util
import logging
def setup_logging():
    level = logging.INFO
    logger = logging.getLogger('annotater')
    logger.setLevel(level)
    log_file_path = 'annotater-debug.log'
    fh = logging.FileHandler(log_file_path, 'w')
    fh.setLevel(level)
    logger.addHandler(fh)
    return logger
logger = setup_logging()
logger.info('START LOGGING')

import paste.request

import annotater.model
annotater.model.set_default_connection()
annotater.model.createdb()
import annotater.store
import annotater.marginalia

# Offset url to annotation store 
# Because of hard-coding in the marginalia js libraries this *must* be set to
# '/annotation'
service_path = '/annotation'

# misc config
this_directory = os.path.dirname(__file__)
html_doc_path = os.path.join(this_directory, 'demo.html')

# where we put the marginalia js
media_mount_path = '/'

class AnnotaterDemo(object):

    def __call__(self, environ, start_response):
        self.store = annotater.store.AnnotaterStore()
        self.media_app = annotater.marginalia.MarginaliaMedia(media_mount_path)
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
            host = 'http://localhost:8080/'
            # use the uri as the identifier
            uri = wsgiref.util.request_uri(environ)
            media = annotater.marginalia.get_media_header(media_mount_path,
                    host,
                    uri)
            buttons = annotater.marginalia.get_buttons(uri)
            values = {
                    'marginalia_media'   : media,
                    'annotation_buttons' : buttons,
                    'page_uri'           : uri,
                    }
            out = out % values
            return [out]


if __name__ == '__main__': 
    app = AnnotaterDemo()
    import paste.httpserver
    from annotater.marginalia import *
    paste.httpserver.serve(app)

