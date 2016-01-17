from datetime import datetime
import json

class JSONEncoderWithDatetime(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return super(JSONEncoderWithDatetime, self).default(obj)

def dumps(obj, encoder=JSONEncoderWithDatetime()):
    return encoder.encode(obj)