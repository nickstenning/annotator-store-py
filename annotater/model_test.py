import annotater.model as model
model.set_default_connection()
model.rebuilddb()

class TestAnnotation:

    @classmethod
    def setup_class(self):
        self.url = u'http://xyz.com'
        self.range = {'start': 'p 19', 'end': 'div 23'}
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
        assert out['range'] == self.range, out
        assert isinstance(out['created'], basestring)
        assert out['ranges'] == [ self.range ]

    def test_from_dict_existing(self):
        anno = model.Annotation.from_dict({'id': self.anno_id})
        assert anno.url == self.url, anno.url
        assert anno.range == self.range

    def test_from_dict_new(self):
        newurl = u'xxxxxxx'
        anno = model.Annotation.from_dict({'url': newurl})
        assert anno.url == newurl

    def test_from_dict_ranges(self):
        range = {"start":"/html/body/p[2]/strong", "end":"/html/body/p[2]/strong", "startOffset":22, "endOffset":27}
        anno = model.Annotation.from_dict({'ranges': [range] })
        assert anno.range == range, anno.range

