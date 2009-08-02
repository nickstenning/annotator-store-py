import os
from StringIO import StringIO

import annotater.js


class TestGetMediaHeader:
    base_url = '/marginalia'
    app_url = 'http://localhost:5000'
    page_uri = 'http://demo.openshakespeare.org/demo.html' 

    def test_1(self):
        out = annotater.js.get_media_header(self.base_url,
                self.app_url,
                self.page_uri)
        assert self.base_url in out
        assert self.app_url in out
        assert '<script type="text/javascript" src="' in out
        assert self.page_uri in out

    def test_no_trailing_slash_on_app_url(self):
        app_url = self.app_url + '/'
        out = annotater.js.get_media_header(self.base_url,
                app_url,
                self.page_uri)
        assert app_url not in out
        assert app_url[:-1] in out


