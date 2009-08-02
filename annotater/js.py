'''Integrate required javascript into the web (WSGI) application.
'''
import os

'''
config for JS Annotater:
    * document uri
    * where server annotater api is located
    * user info?
'''

def get_media_header(media_url_base, server_api, document_uri):
    """html head section including media and js links needed for the js app.

    @param media_url_base: base url for all the links to media files.
    @param server_api: path on this domain to annotation server api (needs to be on this
    domain because XmlHttpRequest objects are bound by the
    same origin security policy).
    
    fully qualified domain name (e.g.
        http://sub.domain.com/) for the annotation store app. Because of
        hard-coding in the marginalia js libraries offset url from the FQDN
        for annotation store then must be '/annotation', i.e. store must reside
        at http://fqdn/annotation/.
    @param document_uri: uri for page you are annotating (used as page identifier)
    """
    if server_api.endswith('/'):
        server_api = server_api[:-1]
    # we re-add a trailing slash so strip if already there
    if media_url_base.endswith('/'):
        media_url_base = media_url_base[:-1]
    values = {
            'media_url' : media_url_base,
            'app_url'   : server_api,
            'document_uri'  : document_uri,
            }
    html_header = \
'''
    <script type="text/javascript" src="%(media_url)s/loader.js"></script>
    <script type="text/javascript">
      annotationInit( '%(app_url)s');
      showAllAnnotations( '%(document_uri)s' );
    </script>
''' % values
    return html_header


class AnnotaterMedia(object):
    """WSGI App to make available the media (js+css) files needed for
    marginalia javascript annotation to work.
    """

    def __init__(self, mount_path, media_path, **kwargs):
        """
        @param mount_path: url path at which this app is mounted
        @param media_path: path on disk to media files
        """
        self.mount_path = mount_path
        # remove the trailing slash
        if self.mount_path.endswith('/'):
            self.mount_path = self.mount_path[:-1]
        import paste.urlparser
        self.fileserver_app = paste.urlparser.StaticURLParser(media_path)

    def __call__(self, environ, start_response):
        if environ.get('PATH_INFO', '').startswith(self.mount_path):
            path_info = environ['PATH_INFO']
            filename = path_info[len(self.mount_path):]
            environ['PATH_INFO'] = filename
            return self.fileserver_app(environ, start_response)
        else:
            pass

