import os
import re
import wsgiref.util
import logging
logger = logging.getLogger('annotator')
logging.basicConfig(level=logging.INFO, filename='annotator-debug.log',
        filemode='w')
logger.info('START LOGGING')

import paste.request

import annotator.model
import annotator.store

# Put this here because we use in html_doc
# Offset url to annotation store 
server_api = '/.annotator_api'

# TODO: turn this into middleware
class AnnotatorDemo(object):
    def __init__(self, media_mount_path, server_api,
            jsannotate_code):
        self.media_mount_path = media_mount_path
        self.server_api = server_api

    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type','text/html')]
        path = environ['PATH_INFO']
        start_response(status, response_headers)
        if path == '/':
            return self.index()
        elif path.startswith('/annotate'):
            self.environ = environ
            return self.annotate()
        else:
            return 'Not Found'

    html_tmpl = '''
<html>
  <head>
    <title>JS annotation test</title>
    <link rel="stylesheet" type="text/css" href="http://m.okfn.org/okftext/css/okftext/text_basic.css" media="all" />
  </head>
  <body>
    <h1>Annotator Demo</h1>
    <div>
    %s
    </div>
  </body>
</html>
'''

    def index(self):
        content = '''
        <form method="POST" action="annotate">
        <p>
        <label>Enter some text to annotate:</label>
        </p>
        <textarea name="text" cols="100" rows="20"></textarea>
        <p>
        <input type="submit" name="Submit" id="Submit" value="Submit" />
        </p>
        </form>
        '''
        return self.html_tmpl % content
    
    def annotate(self):
        import webob
        req = webob.Request(self.environ)
        text = req.params.get('text', '')
        if text:
            content = '''<pre>%s</pre>''' % text
            import annotator.middleware
            modifier = annotator.middleware.JsAnnotateMiddleware(None,
                    self.media_mount_path, self.server_api)
            out = self.html_tmpl % content
            out = modifier.modify_html(out)
            return out
        else:
            return self.html_tmpl % 'No text was provided ...'


import paste.urlparser
def make_media_app(mount_path, media_path, **kwargs):
    '''
    @param mount_path: url path at which this app is mounted
    @param media_path: path on disk to media files
    '''
    fileserver_app = paste.urlparser.StaticURLParser(media_path)
    return fileserver_app

# dedicated function for use from paster
def make_app(global_config, **local_conf):
    dburi = local_conf['dburi']
    annotator.model.repo.configure(dburi)
    annotator.model.createdb()

    jsannotate_path = local_conf['jsannotate']
    # where we put the marginalia js
    media_mount_path = '/.jsannotate'

    jsannotate_code = os.path.join(jsannotate_path, 'pkg')
    imgpath = os.path.join(jsannotate_path, 'img')

    import paste.urlmap
    demoapp = paste.urlmap.URLMap()
    demoapp['/'] = AnnotatorDemo(media_mount_path, server_api, jsannotate_code)
    demoapp[media_mount_path] = make_media_app(media_mount_path,
            jsannotate_code)
    # should be inside media app but isn't yet
    demoapp['/img'] = paste.urlparser.StaticURLParser(imgpath)

    # we don't need to mount store anywhere since urlmap will strip off prefix
    demoapp[server_api] = annotator.store.AnnotatorStore()

    return demoapp


if __name__ == '__main__': 
    app = make_app()
    import paste.httpserver
    paste.httpserver.serve(app)

