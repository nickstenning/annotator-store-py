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
import annotator.js

# Put this here because we use in html_doc
# Offset url to annotation store 
server_api = '/.annotator_api'

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
    <div id="serialize">
      <button class="clear">Clear all</button>
      <button class="save">Save annotations</button>
      <button class="load">Load annotations</button><br />
      <textarea cols="80" rows="15"></textarea>
    </div>
  </body>
</html>
''' % server_api

# TODO: turn this into middleware
class AnnotatorDemo(object):
    head_media = '''
    <script src="%(media_url)s/jsannotate.min.js"></script>
    <link rel="stylesheet" type="text/css" href="%(media_url)s/jsannotate.min.css">
    '''

    body_script = '''
    <script>
      jQuery(function () {
        window.jsannotator = new Annotator();
        var rest_api = '%(server_api)s';
        var rest_annotation = rest_api + '/annotation';

        $('#serialize button.load').click(function () {
          $.getJSON(rest_annotation, function (data) {
            window.jsannotator.loadAnnotations(data);
            // also dump them to the textarea
            $('#serialize textarea').val($.toJSON(data));
          });
        });

        $('#serialize button.save').click(function () {
          var data = $.toJSON(window.jsannotator.dumpAnnotations());
          $.post(rest_annotation, { "json": data } );
          // also dump them to the textarea
          $('#serialize textarea').val(
            data
          );
        });

        $('#serialize button.clear').live('click', function () {
          window.jsannotator.clearAll();
          $('#serialize textarea').val('');
        });
      });
    </script>
    '''

    def __init__(self, media_mount_path, server_api,
            jsannotate_code):
        self.media_mount_path = media_mount_path
        self.server_api = server_api
        self.jsannotate_code = jsannotate_code

    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type','text/html')]
        start_response(status, response_headers)
        # use the uri as the identifier
        uri = wsgiref.util.request_uri(environ)
        head_media = self.head_media % { 'media_url': self.media_mount_path }
        out = self.add_to_head(html_doc, head_media)
        out = self.add_to_end_of_body(out, self.body_script % { 'server_api': self.server_api})
        return [out]

    _end_head_re = re.compile(r'</head.*?>', re.I|re.S)
    _end_body_re = re.compile(r'</body>.*?>', re.I|re.S)

    def add_to_head(self, html, extra_html):
        '''
        Adds extra_html to the end of the html page (before </body>)
        '''
        match = self._end_head_re.search(html)
        if not match:
            # maybe we should raise
            return html + extra_html
        else:
            return html[:match.start()] + extra_html + html[match.start():]
    
    def add_to_end_of_body(self, html, extra_html):
        match = self._end_body_re.search(html)
        if not match:
            # maybe we should raise
            return html + extra_html
        else:
            return html[:match.start()] + extra_html + html[match.start():]


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
    annotator.model.set_default_connection(dburi)
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

