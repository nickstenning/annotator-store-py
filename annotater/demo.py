import os
import re
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

# Put this here because we use in html_doc
# Offset url to annotation store 
server_api = '/.annotater_api'

html_doc = '''
<html>
  <head>
    <title>JS annotation test</title>
  </head>
  <body>
    <h1>Javascript annotation service test</h1>
    <h2>Documentation</h2>
    <p>Server is located at <a href="%s/annotation/">here</a>
    </p>

    <h2>Demo Text</h2>
    <p>
      <strong>Pellentesque habitant morbi tristique</strong> senectus et netus et malesuada fames ac turpis egestas. Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu libero sit amet quam egestas semper. <em>Aenean ultricies mi vitae est.</em>
    </p>
    <p>
      Mauris placerat eleifend leo. Quisque sit amet est et sapien ullamcorper pharetra. Vestibulum erat wisi, condimentum sed, <code>commodo vitae</code>, ornare sit amet, wisi. Aenean fermentum, elit eget tincidunt condimentum, eros ipsum rutrum orci, sagittis tempus lacus enim ac dui. <a href="#">Donec non enim</a> in turpis pulvinar facilisis. Ut felis.
    </p>
  </body>
</html>
''' % server_api

class AnnotaterDemo(object):

    def __init__(self, app, media_mount_path, server_api,
            jsannotate_code):
        self.app = app
        self.server_api = server_api
        self.store = annotater.store.AnnotaterStore(server_api)
        self.media_mount_path = media_mount_path
        self.media_app = annotater.js.AnnotaterMedia(media_mount_path,
                jsannotate_code)

    def __call__(self, environ, start_response):
        self.path = environ['PATH_INFO']
        if self.path.startswith(self.media_mount_path):
            return self.media_app(environ, start_response)
        elif self.path.startswith(self.server_api):
            return self.store(environ, start_response)
        else:
            logger.info('Call to %s' % self.path)
            status = '200 OK'
            response_headers = [('Content-type','text/html')]
            start_response(status, response_headers)
            # use the uri as the identifier
            uri = wsgiref.util.request_uri(environ)
            media = annotater.js.get_media_header(self.media_mount_path,
                    self.server_api, uri)
            out = self.add_to_head(html_doc, media)
            return [out]

    _end_head_re = re.compile(r'</head.*?>', re.I|re.S)

    def add_to_head(self, html, extra_html):
        """
        Adds extra_html to the end of the html page (before </body>)
        """
        match = self._end_head_re.search(html)
        if not match:
            # maybe we should raise
            return html + extra_html
        else:
            return html[:match.start()] + extra_html + html[match.start():]


def make_app(global_config, **local_conf):
    # where we put the marginalia js
    media_mount_path = '/.jsannotate'

    jsannotate_code = '/home/rgrp/hgroot/jsannotate/js/'

    app = AnnotaterDemo(None, media_mount_path, server_api, jsannotate_code)
    return app


if __name__ == '__main__': 
    app = make_app()
    import paste.httpserver
    paste.httpserver.serve(app)

