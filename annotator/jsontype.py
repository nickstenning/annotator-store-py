import json

from sqlalchemy.types import TypeDecorator, UnicodeText

class JsonType(TypeDecorator):
    '''Custom SQLAlchemy type for JSON data (serializing on save and
    unserializing on use).
    '''
    impl = UnicodeText

    def process_bind_param(self, value, engine):
        if value is None or value == {}: # ensure we stores nulls in db not json "null"
            return None
        else:
            return unicode(json.dumps(value, ensure_ascii=False))

    def process_result_value(self, value, engine):
        if value is None:
            return None
        else:
            return json.loads(value)

    def copy(self):
        return JsonType(self.impl.length)