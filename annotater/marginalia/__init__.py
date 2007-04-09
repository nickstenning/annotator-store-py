import os

def get_media_header(media_url_base, annotation_store_fqdn, page_uri):
    """Get html head section including all media links needed for marginalia.

    @param media_url_base: base url for all the links to media files.
    @param annotation_store_fqdn: fully qualified domain name (e.g.
        http://sub.domain.com/) for the annotation store app. Because of
        hard-coding in the marginalia js libraries offset url from the FQDN
        for annotation store then must be '/annotation', i.e. store must reside
        at http://fqdn/annotation/.
    @param page_uri: uri for page you are annotating (used as page identifier)
    """
    if annotation_store_fqdn.endswith('/'):
        annotation_store_fqdn = annotation_store_fqdn[:-1]
    # we re-add a trailing slash so strip if already there
    if media_url_base.endswith('/'):
        media_url_base = media_url_base[:-1]
    values = {
            'media_url' : media_url_base,
            'app_url'   : annotation_store_fqdn,
            'page_uri'  : page_uri,
            }
    html_header = \
'''
	<link rel="stylesheet" type="text/css" href="%(media_url)s/example.css"/>
    <script type="text/javascript" src="%(media_url)s/log.js"></script>
    <script type="text/javascript" src="%(media_url)s/config.js"></script>
    <script type="text/javascript" src="%(media_url)s/html-model.js"></script>
    <script type="text/javascript" src="%(media_url)s/domutil.js"></script>
    <script type="text/javascript" src="%(media_url)s/ranges.js"></script>
    <script type="text/javascript" src="%(media_url)s/post-micro.js"></script>
    <script type="text/javascript" src="%(media_url)s/rest-annotate.js"></script>
    <script type="text/javascript" src="%(media_url)s/lang/en.js"></script>
    <script type="text/javascript" src="%(media_url)s/annotation.js"></script>
    <script type="text/javascript" src="%(media_url)s/smartcopy.js"></script>
    <script type="text/javascript">
      annotationInit( '%(app_url)s', 'anonymous', 'anonymous', null );
      smartcopyInit( );
      function generic_onload()
      {
        showAllAnnotations( "%(page_uri)s#*" );
      };
    </script>
    <!-- must be called after generic_onload is defined -->
    <script type="text/javascript" src="%(media_url)s/onload.js"></script>
''' % values
    return html_header


def get_buttons(page_uri):
    "Get Show/Hide Annotation buttons."
    html = \
'''
  <form>
    <!-- add #* so that all annotations are picked up -->
    <input type="button" onclick='showAllAnnotations( "%(page_uri)s#*")' value="Show Annotations" /><br />
    <input type="button" onclick='hideAllAnnotations( "%(page_uri)s#*")' value="Hide Annotations" /><br />
  </form>
'''
    out = html % { 'page_uri' : page_uri }
    return out


class MarginaliaMedia(object):
    """WSGI App to make available the marginalia media files needed for
    marginalia javascript annotation to work.
    """

    def __init__(self, mount_path):
        """
        @param mount_path: url path at which this app is mounted e.g. /marginalia
        """
        self.mount_path = mount_path
        # remove the trailing slash
        if self.mount_path.endswith('/'):
            self.mount_path = self.mount_path[:-1]
        import paste.urlparser
        self.fileserver_app = paste.urlparser.make_pkg_resources(
                {},
                'annotater',
                'annotater/marginalia'
                )

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        filename = path_info[len(self.mount_path):]
        environ['PATH_INFO'] = filename
        return self.fileserver_app(environ, start_response)
        if filename.endswith('.js') or filename.endswith('.css'):
            status = '200 OK'
            if filename.endswith('.js'): filetype = 'text/javascript'
            else: filetype = 'text/css'
            response_headers = [('Content-type', filetype)]
            start_response(status, response_headers)
            fp = os.path.join(self.media_path, filename)
            fo = file(fp)
            content = fo.read()
            fo.close()
            return [content]
        else:
            status = '404 Not Found'
            response_headers = [('Content-type','text/html')]
            start_response(status, response_headers)
            out = 'File %s not found' % filename
            return [out]

