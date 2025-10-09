from pydantic import field_serializer

from .__types_adapter import AdapterResource

class Resource(AdapterResource):
    @field_serializer("uri")
    def serialize_uri(self, uri):
        return str(self.uri)