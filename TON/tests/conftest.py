import os
import sys


def _ensure_src_on_path() -> None:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src = os.path.join(repo_root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)


_ensure_src_on_path()

