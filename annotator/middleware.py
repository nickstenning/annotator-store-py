import os
import re
import wsgifilter.filter

# TODO config for JS Annotator:
# * document uri
# * user info?

class JsAnnotateMiddleware(wsgifilter.filter.Filter):
    '''Add JS annotate into a document'''

    head_media = '''
    <script src="%(media_url)s/jsannotate.min.js"></script>
    <link rel="stylesheet" type="text/css" href="%(media_url)s/jsannotate.min.css">
    '''

    body_script = '''
    <script>
      jQuery(function () {
        // TODO: JSAnnotate.config
        // configure with docid (if not already defined ...)
        var rest_api = '%(server_api)s';
        var rest_annotation = rest_api + '/annotation';
        window.jsannotator = new Annotator();
    });
    </script>
    '''

    def __init__(self, app, media_mount_path, server_api):
        '''
        @param app: wsgi app to wrap
        @param media_mount_path: url path to where js annotate files are
        located
        @param server_api: url path to RESTful annotator store API
        '''
        super(JsAnnotateMiddleware, self).__init__(app)
        self.media_mount_path = media_mount_path
        self.server_api = server_api

    def filter(self, environ, headers, data):
        return self.modify_html(data)

    def modify_html(self, html_doc):
        head_media = self.head_media % { 'media_url': self.media_mount_path }
        out = self.add_to_head(html_doc, head_media)
        out = self.add_to_end_of_body(out, self.body_script % { 'server_api': self.server_api})
        return out

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

