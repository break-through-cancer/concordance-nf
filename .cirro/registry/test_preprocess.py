"""Offline test for preprocess.py. Needs neither pandas nor the Cirro SDK:

    python test_preprocess.py
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location("preprocess", pathlib.Path(__file__).with_name("preprocess.py"))
pre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pre)


def test_normalize_strips_slashes_and_repeats():
    picked = ["s3://b/a/data/", " s3://b/b/data//", "s3://b/a/data", ""]
    assert pre.normalize_dirs(picked) == ["s3://b/a/data", "s3://b/b/data"]


def test_normalize_accepts_strings_and_none():
    assert pre.normalize_dirs("s3://b/a/, s3://b/b") == ["s3://b/a", "s3://b/b"]
    assert pre.normalize_dirs(None) == []


def test_check_dirs():
    assert pre.check_dirs(["s3://b/a"]) == []
    assert "at least one" in pre.check_dirs([])[0]
    assert pre.check_dirs(["/local/path"]) == ["Folder 1 is not an S3 location."]
    assert "comma" in pre.check_dirs(["s3://b/a,b"])[0]


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_")]
    for name, fn in tests:
        fn()
        print("PASS ", name)
    print(f"all {len(tests)} checks passed")
