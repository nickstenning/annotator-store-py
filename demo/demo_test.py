from StringIO import StringIO

import twill
from twill import commands as web

import demo


class TestAnnotaterDemo:

    def setup_method(self, name=''):
        wsgi_app = demo.AnnotaterDemo()
        twill.add_wsgi_intercept('localhost', 8080, lambda : wsgi_app)
        self.outp = StringIO()
        twill.set_output(self.outp)
        self.siteurl = 'http://localhost:8080/'

    def teardown_method(self, name=''):
        # remove intercept.
        twill.remove_wsgi_intercept('localhost', 8080)

    def test_js(self):
        filename = 'domutil.js'
        url = self.siteurl + filename
        web.go(url)
        web.code(200)
        web.find('ELEMENT_NODE = 1;')

    def test_show_root(self):
        web.go(self.siteurl)
        web.code(200)
        web.title('Annotation Example')
        web.find('Web Annotation Demo')
        web.find('Show Annotations')

