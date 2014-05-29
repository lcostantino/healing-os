import json

from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from healing.api.controllers import resource

#like mistral
class Data(resource.Resource):
    """Generic data resource."""
    data = wtypes.text
        
    def to_dict(self):
        d = super(Data, self).to_dict()

        if d.get('data'):
            d['data'] = json.loads(d['data'])

        return d

    @classmethod
    def from_dict(cls, d):
        e = cls()

        for key, val in d.items():
            if hasattr(e, key):
                # Nonetype check for dictionary must be explicit
                if key == 'data' and val is not None:
                    val = json.dumps(val)
                setattr(e, key, val)

        return e