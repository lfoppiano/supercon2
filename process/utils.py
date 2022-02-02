from datetime import datetime, date

from bson import ObjectId


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (ObjectId)):
        return str(obj)
    raise TypeError("Type %s not serializable" % type(obj))
