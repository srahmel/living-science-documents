# Provide lazy access to submodules (e.g., publications.archive) without importing heavy deps at package import time.
import importlib

def __getattr__(name):
    if name in {"archive", "jats_converter", "citation"}:
        return importlib.import_module(f"{__name__}.{name}")
    raise AttributeError(name)
