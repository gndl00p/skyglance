try:
    import ujson as _json
except ImportError:
    import json as _json


_DEFAULT = {"last_data": None}


def load(path):
    try:
        with open(path, "r") as f:
            raw = f.read()
        if not raw.strip():
            return dict(_DEFAULT)
        return _json.loads(raw)
    except (OSError, ValueError):
        return dict(_DEFAULT)


def save(path, data):
    with open(path, "w") as f:
        f.write(_json.dumps(data))
