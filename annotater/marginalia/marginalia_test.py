import os
from StringIO import StringIO

import twill
from twill import commands as web

import annotater.marginalia


class TestGetMediaHeader:
    base_url = '/marginalia'
    app_url = 'http://localhost:5000'
    page_uri = 'http://demo.openshakespeare.org/demo.html' 

    def test_1(self):
        out = annotater.marginalia.get_media_header(self.base_url,
                self.app_url,
                self.page_uri)
        assert self.base_url in out
        assert self.app_url in out
        assert '<script type="text/javascript" src="' in out
        assert self.page_uri in out

    def test_no_trailing_slash_on_app_url(self):
        app_url = self.app_url + '/'
        out = annotater.marginalia.get_media_header(self.base_url,
                app_url,
                self.page_uri)
        assert app_url not in out
        assert app_url[:-1] in out


class TestGetButtons:

    def test_1(self):
        uri = 'http://demo.openshakespeare.org/view?name=blahblah'
        out = annotater.marginalia.get_buttons(uri)
        assert uri in out


class TestMarginaliaFiles:

    def setup_method(self, name=''):
        # set without trailing slash
        self.base_url = '/marginalia'
        wsgi_app = annotater.marginalia.MarginaliaMedia(self.base_url)
        self.base_url = '/marginalia' + '/'
        twill.add_wsgi_intercept('localhost', 8080, lambda : wsgi_app)
        twill.set_output(StringIO())
        self.siteurl = 'http://localhost:8080'

    def teardown_method(self, name=''):
        twill.remove_wsgi_intercept('localhost', 8080)

    def test_js(self):
        filename = 'domutil.js'
        url = self.siteurl + self.base_url + filename
        print url
        web.go(url)
        web.code(200)
        web.find('ELEMENT_NODE = 1;')

    def test_js_2(self):
        filename = 'lang/en.js'
        url = self.siteurl + self.base_url + filename
        web.go(url)
        web.code(200)


class TestMarginaliaFiles2(TestMarginaliaFiles):
    # a different base name

    def setup_method(self, name=''):
        self.base_url = '/'
        wsgi_app = annotater.marginalia.MarginaliaMedia(self.base_url)
        twill.add_wsgi_intercept('localhost', 8080, lambda : wsgi_app)
        twill.set_output(StringIO())
        self.siteurl = 'http://localhost:8080'

