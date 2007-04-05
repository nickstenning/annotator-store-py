import annotater.model
annotater.model.rebuilddb()

class TestAnnotation:

    def setup_class(self):
        self.url = 'http://xyz.com'
        self.anno = annotater.model.Annotation(
                url=self.url,
                range='31.0 32.5',
                note='It is a truth universally acknowledged',
                )

    def teardown_class(cls):
        annotater.model.Annotation.delete(cls.anno.id)

    def test_1(self):
        out = annotater.model.Annotation.get(self.anno.id)
        assert out.url == self.url
    
    def test_list_annotations_html(self):
        out = annotater.model.Annotation.list_annotations_html()
        exp1 = "&lt;Annotation 1 url=u'http://xyz.com'"
        assert exp1 in out

    def test_list_annotations_atom(self):
        out = annotater.model.Annotation.list_annotations_atom(self.url)
        exp1 = '<feed xmlns:ptr="http://www.geof.net/code/annotation/"'
        assert exp1 in out
        exp2 = '<title>%s</title>' % self.anno.note
        assert exp2 in out
        exp3 = '<link rel="related" type="text/html" title="quote_title_not_available_yet" href="%s"/>' % self.anno.url
        print out
        assert exp3 in out


class TestAnnotationSchema:

    schema = annotater.model.AnnotationSchema()

    def test_default(self):
        out = self.schema.from_python(None) 
        assert out == {}

