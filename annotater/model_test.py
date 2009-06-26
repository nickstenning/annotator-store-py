import annotater.model as model
model.set_default_connection()
model.rebuilddb()

class TestAnnotation:

    @classmethod
    def setup_class(self):
        self.url = u'http://xyz.com'
        anno = model.Annotation(
                url=self.url,
                range=u'31.0 32.5',
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
    
    def test_1_list_annotations_html(self):
        out = model.Annotation.list_annotations_html()
        exp1 = "Annotation %s http://xyz.com" % self.anno_id
        assert exp1 in out, out

    def test_2_list_annotations_atom(self):
        anno = model.Annotation.query.get(self.anno_id)
        out = model.Annotation.list_annotations_atom(self.url)
        exp1 = '<feed xmlns:ptr="http://www.geof.net/code/annotation/"'
        assert exp1 in out
        exp2 = '<title>%s</title>' % anno.note
        assert exp2 in out
        exp3 = '<link rel="related" type="text/html" title="quote_title_not_available_yet" href="%s"/>' % anno.url
        print out
        assert exp3 in out


