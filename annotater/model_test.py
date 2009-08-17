import annotater.model as model
model.set_default_connection()
model.rebuilddb()

class TestAnnotation:

    @classmethod
    def setup_class(self):
        self.url = u'http://xyz.com'
        self.range = u'31.0 32.5'
        anno = model.Annotation(
                url=self.url,
                range=self.range,
                note=u'It is a truth universally acknowledged',
                )
        model.Session.commit()
        self.anno_id = anno.id

    @classmethod
    def teardown_class(self):
        anno = model.Annotation.query.get(self.anno_id)
        model.Session.delete(anno)
        model.Session.commit()
        model.Session.remove()

    def test_0(self):
        out = model.Annotation.query.get(self.anno_id)
        assert out.url == self.url
    
    def test_as_dict(self):
        anno = model.Annotation.query.get(self.anno_id)
        out = anno.as_dict()
        assert out['url'] == self.url, out

    def test_from_dict(self):
        anno = model.Annotation.from_dict({'id': self.anno_id})
        assert anno.url == self.url
        assert anno.range == self.range

    def test_from_dict(self):
        newurl = u'xxxxxxx'
        anno = model.Annotation.from_dict({'url': newurl})
        assert anno.url == newurl


