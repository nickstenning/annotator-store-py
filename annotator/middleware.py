import os
import re
import wsgifilter.filter

# TODO config for JS Annotator:
# * document uri
# * user info?

class JsAnnotateMiddleware(wsgifilter.filter.Filter):
    '''Add JS annotate into a document'''
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

    body_script_tmpl = '''
    <script>
        jQuery(function($) {
          var annotator_prefix = '%s';
          // an identifier for the document
          var annotator_doc_uri = '%s';
          $('#text-to-annotate').annotator();
          $('#text-to-annotate').annotationStore({'prefix': annotator_prefix});
          // 'uri': annotator_doc_uri});
        });
    </script>
    '''

    def body_script(self, doc_uri):
        return self.body_script_tmpl % (self.server_api + 'annotation', doc_uri)

    jquery_media =  '''
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.3/jquery.min.js"></script>
    <script src="http://jquery-json.googlecode.com/svn/trunk/jquery.json.min.js"></script>
    '''

    head_media = '''
    <script src="%(media_url)s/annotator.min.js"></script>
    <link rel="stylesheet" type="text/css" href="%(media_url)s/annotator.min.css">
    '''

    def modify_html(self, html_doc, doc_uri=None, include_jquery=True):
        '''
        @param include_jquery: include jQuery library (+ json extension)
        required by js annotator. You may wish to set this to False if you are
        already including jQuery.
        '''
        if include_jquery:
            out = self.add_to_head(html_doc, self.jquery_media)
        else:
            out = html_doc
        head_media = self.head_media % { 'media_url': self.media_mount_path }
        out = self.add_to_head(out, head_media)
        out = self.add_to_end_of_body(out, self.body_script(doc_uri))
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

