import paste.fixture

# import annotator.demo as demo

class TestDemo:
    __test__ = False

    # problem here: demo make_app function calls model.repo.configure again 
    # (using demo.ini config -- which we don't really want)
    def test_1(self):
        from paste.deploy import loadapp
        demoapp = loadapp('config:demo.ini', relative_to='.')
        # demoapp = demo.make_app(None, 
        self.app = paste.fixture.TestApp(demoapp)
        res = self.app.get('/')
        assert res

