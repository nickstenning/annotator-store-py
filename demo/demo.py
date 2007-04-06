import os

import paste.request

import annotater.model
annotater.model.set_default_connection()
import annotater.store
import annotater.marginalia

# absolute url to annotation service
service_path = '/annotation'

# misc config
this_directory = os.path.dirname(__file__)
html_doc_path = os.path.join(this_directory, 'index.html')

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

class AnnotaterDemo(object):

    def __call__(self, environ, start_response):
        self.store = annotater.store.AnnotaterStore()
        self.media_app = annotater.marginalia.MarginaliaMedia('/')
        self.path = environ['PATH_INFO']
        if self.path.startswith('/debug'):
            return wsgiref.simple_server.demo_app(environ, start_response)
        elif self.path.endswith('.js') or self.path.endswith('.css'):
            return self.media_app(environ, start_response)
        elif self.path.startswith(service_path):
            return self.store(environ, start_response)
        else:
            logger.info('Call to base url /')
            status = '200 OK'
            response_headers = [('Content-type','text/html')]
            start_response(status, response_headers)
            out = file(html_doc_path).read()
            return [out]


if __name__ == '__main__': 
    app = AnnotaterDemo()
    import paste.httpserver
    paste.httpserver.serve(app)
