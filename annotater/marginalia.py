import os

def get_media_header(media_url_base, app_url):
    """Get all html head needed for marginalia.
    @param media_url:
    """
    values = {
            'media_url' : media_url_base,
            'app_url'   : app_url
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
    </script>
''' % values
    return html_header


class MarginaliaMedia(object):
    """WSGI App to make available the marginalia media files needed for
    marginalia javascript annotation to work.
    """

    def __init__(self, media_path, mount_path):
        """
        @param media_path: path on disk to marginalia media files directory.
        @param mount_path: url path at which this app is mounted e.g. /marginalia
        """
        self.media_path = media_path
        if mount_path.endswith('/'):
            mount_path = mount_path[:-1]
        if not mount_path.startswith('/'):
            mount_path = '/' + mount_path
        self.mount_path = mount_path

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        filename = path_info[len(self.mount_path):]
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

