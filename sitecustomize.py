import os

root = os.path.dirname(os.path.abspath(__file__))
path = os.environ.get("PATH", "")
parts = path.split(os.pathsep) if path else []
if root not in parts:
    os.environ["PATH"] = root + os.pathsep + path
