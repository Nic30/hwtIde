from flask.wrappers import Response
import json


def jsonResp(data):
    return Response(response=json.dumps(
        data,
        default=_defaultToJson),
        status=200, mimetype="application/json")


def _defaultToJson(obj):
    if hasattr(obj, "toJson"):
        return obj.toJson()
    return obj.__dict__
