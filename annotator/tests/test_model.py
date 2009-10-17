import annotator.model as model
model.repo.rebuilddb()

class TestAnnotation:

    @classmethod
    def setup_class(self):
        self.uri = u'http://xyz.com'
        self.range = {'start': 'p 19', 'end': 'div 23'}
        anno = model.Annotation(
                uri=self.uri,
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
        assert out.uri == self.uri
    
    def test_as_dict(self):
        anno = model.Annotation.query.get(self.anno_id)
        out = anno.as_dict()
        assert out['uri'] == self.uri, out
        assert out['range'] == self.range, out
        assert isinstance(out['created'], basestring)
        assert out['ranges'] == [ self.range ]

    def test_from_dict_existing(self):
        anno = model.Annotation.from_dict({'id': self.anno_id})
        assert anno.uri == self.uri, anno.uri
        assert anno.range == self.range

    def test_from_dict_new(self):
        newuri = u'xxxxxxx'
        anno = model.Annotation.from_dict({'uri': newuri})
        assert anno.uri == newuri

    def test_from_dict_ranges(self):
        range = {"start":"/html/body/p[2]/strong", "end":"/html/body/p[2]/strong", "startOffset":22, "endOffset":27}
        anno = model.Annotation.from_dict({'ranges': [range] })
        assert anno.range == range, anno.range

