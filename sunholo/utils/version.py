def sunholo_version():
    from importlib.metadata import version
    return f"sunholo-{version('sunholo')}"