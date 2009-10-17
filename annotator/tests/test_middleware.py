import paste.fixture

import annotator.middleware


class DemoWsgiApp(object):
    demo_html = '''<html>
        <head>
            <title>Demo Html<title>
        </head>
        <body>
            <h1>Demo Html</h1>
        </body>
    </html>
    '''

    def __call__(self, environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type','text/html')]
        start_response(status, response_headers)
        return [self.demo_html]

class TestJsAnnotateMiddleware:

    def __init__(self, *args, **kwargs):
        demoapp = DemoWsgiApp()
        self.media_path = '.jsannotate-media'
        self.server_path = '.annotator-store'
        self.wsgiapp = annotator.middleware.JsAnnotateMiddleware(demoapp,
                self.media_path, self.server_path)
        self.app = paste.fixture.TestApp(self.wsgiapp)

    def test_1(self):
        res = self.app.get('/')
        assert 'Demo Html' in res

    def test_head_media(self):
        res = self.app.get('/')
        assert 'annotator.min.js' in res, res

    def test_body_script_1(self):
        docuri = 'made-up-doc-uri'
        body_script = self.wsgiapp.body_script(docuri)
        assert docuri in body_script

    def test_body_script_2(self):
        res = self.app.get('/')
        docuri = None
        body_script = self.wsgiapp.body_script(docuri)
        assert body_script in res, res
    
