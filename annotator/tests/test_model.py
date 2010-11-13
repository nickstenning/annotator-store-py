from annotator.model import Annotation

def assertProp(obj, name, val):
    if type(obj).__name__ == 'dict':
        lhs = obj[name]
    else:
        lhs = getattr(obj, name)

    assert lhs == val, 'Property `%s` != %s -- was %s instead.' % (name, val, lhs)

class TestAnnotation(object):

    def setup(self):
        self.uri = u'http://xyz.com'
        self.ranges = [{'start': 'p 19', 'end': 'div 23'}]
        self.tags = [u'abc', u'xyz']

        self.anno = Annotation(
            uri=self.uri,
            ranges=self.ranges,
            note=u'It is a truth universally acknowledged',
            user=u'myuserid',
            tags=self.tags,
            extras={u'extra1': u'extraval1'}
        )

    def test_as_dict(self):
        out = self.anno.as_dict()
        assertProp(out, 'uri', self.uri)
        assertProp(out, 'tags', self.tags)
        assertProp(out, 'ranges', self.ranges)
        assertProp(out, 'extra1', u'extraval1')

    def test_merge_dict(self):
        self.anno.merge_dict({'id': 123, 'text': "Foobar"})
        assertProp(self.anno, 'id', 123)
        assertProp(self.anno, 'text', 'Foobar')
        assertProp(self.anno, 'tags', self.tags)

    def test_from_dict(self):
        r = {"start":"/html/body/p[2]/strong", "end":"/html/body/p[2]/strong", "startOffset":22, "endOffset":27}

        anno = Annotation.from_dict({'id': 456, 'text': "Hello", 'ranges': [r]})
        assertProp(anno, 'id', 456)
        assertProp(anno, 'text', 'Hello')
        assertProp(anno, 'ranges', [r])

