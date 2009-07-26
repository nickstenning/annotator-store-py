import os
from StringIO import StringIO

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


class TestFormatEntry:

    starttext = unicode('''Blah \xc3\xa6
blah &amp; blah''', 'utf-8')
    exp = u'''
    <div id="m2" class="hentry">
        <h3 class="entry-title">Test Stuff</h3>
        <div class="entry-content">
            Blah \xe6
blah &amp; blah
        </div><!-- /entry-content -->
        <p class="metadata">
            <a rel="bookmark" href="http://demo.openshakespeare.org/#m2">#</a>
            <span class="author">Nemo</span>
        </p>
        <div class="notes">
            <button class="createAnnotation" onclick="createAnnotation('m2',true)" title="Click here to create an annotation">&gt;</button>
            <ol>
                <li></li>
            </ol>
        </div><!-- /notes -->
    </div><!-- /hentry -->
'''
    
    def test_format(self):
        newtitle = 'Test Stuff'
        page_url = 'http://demo.openshakespeare.org/'
        out = annotater.marginalia.format_entry(
                content=self.starttext,
                page_uri=page_url,
                title=newtitle,
                id='m2',
                author='Nemo',
                )
        exp = self.exp.encode('utf-8')
        print '"%s"' % out.encode('utf-8')
        print '"%s"' % exp
        for count in range(len(out)):
            end = max(count+5, len(out)) 
            if out[count] != self.exp[count]:
                print 'Error:', count, exp[count:count+5]
        assert out == self.exp


import paste.fixture
class TestMarginaliaFiles:
    # set with trailing slash
    base_url = '/marginalia/'

    @classmethod
    def setup_class(self):
        wsgiapp = annotater.marginalia.MarginaliaMedia(self.base_url)
        self.app = paste.fixture.TestApp(wsgiapp)

    def test_js(self):
        filename = 'domutil.js'
        url = self.base_url + filename
        res = self.app.get(url)
        assert 'ELEMENT_NODE = 1;' in res, (url, res)

        filename = 'onload.js'
        res = self.app.get(self.base_url + filename)

    # ditto here
    def test_js_2(self):
        filename = 'lang/en.js'
        url = self.base_url + filename
        print url
        res = self.app.get(url)


class TestMarginaliaFiles2(TestMarginaliaFiles):
    # a different base name
    base_url = '/'

