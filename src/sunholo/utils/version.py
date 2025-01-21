_cached_version = None

def sunholo_version():
    global _cached_version
    if _cached_version is None:
        from importlib.metadata import version
        _cached_version = f"sunholo-{version('sunholo')}"
    return _cached_version