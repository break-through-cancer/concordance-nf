"""Offline test for preprocess.py. Needs neither pandas nor the Cirro SDK:

    python test_preprocess.py
"""
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location("preprocess", pathlib.Path(__file__).with_name("preprocess.py"))
pre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pre)

COLUMNS = ["sample", "subject", "alignment", "index", "family", "sex", "batch"]


def row(sample="s1", subject="p1", alignment="s3://b/a.cram", **extra):
    base = {"sample": sample, "subject": subject, "alignment": alignment,
            "index": "", "family": "", "sex": "", "batch": ""}
    base.update(extra)
    return base


def test_valid_sheet_has_no_problems():
    rows = [row("s1", "p1", "s3://b/a.cram"), row("s2", "p1", "s3://b/b.bam", sex="female"),
            row("s3", "p2", "s3://b/c.vcf.gz")]
    assert pre.validate_rows(rows, COLUMNS) == []


def test_empty_sheet_and_missing_columns():
    assert "no rows" in pre.validate_rows([], COLUMNS)[0]
    assert "subject" in pre.validate_rows([{"sample": "a"}], ["sample", "alignment"])[0]


def test_empty_required_cells_are_named():
    problems = pre.validate_rows([row(subject="")], COLUMNS)
    assert problems == ["Row 1: subject is empty."]


def test_id_patterns():
    problems = pre.validate_rows([row(sample="bad id"), row("s2", subject="p/1", family="f 1")], COLUMNS)
    assert any(p.startswith("Row 1: sample") for p in problems)
    assert any(p.startswith("Row 2: subject") for p in problems)
    assert any(p.startswith("Row 2: family") for p in problems)


def test_duplicate_sample_ids_and_shared_files():
    rows = [row("s1", alignment="s3://b/a.cram"), row("s1", alignment="s3://b/b.cram"),
            row("s2", alignment="s3://b/a.cram")]
    problems = pre.validate_rows(rows, COLUMNS)
    assert "Rows 1, 2 repeat one sample id." in problems
    assert any("Row 3: the same file as row 1" in p for p in problems)


def test_alignment_and_index_rules():
    problems = pre.validate_rows([
        row("a", alignment="s3://b/a.txt"),
        row("b", alignment="s3://b/b.bcf"),
        row("c", alignment="s3://b/c.cram", index="s3://b/c.cram.idx"),
    ], COLUMNS)
    assert any(p.startswith("Row 1: alignment") for p in problems)
    assert "Row 2: BCF input needs an index." in problems
    assert any(p.startswith("Row 3: index") for p in problems)
    assert pre.validate_rows([row("b", alignment="s3://b/b.bcf", index="s3://b/b.bcf.csi")], COLUMNS) == []


def test_sex_values():
    assert pre.validate_rows([row(sex="Male")], COLUMNS) == []
    assert pre.validate_rows([row(sex="x")], COLUMNS) == ["Row 1: sex must be male, female or unknown."]


def test_normalize_strips_and_drops_blank_rows():
    rows = pre.normalize_rows([row(" s1 ", "p1 "), {k: "" for k in COLUMNS}, row("s2", "p2")])
    assert [r["sample"] for r in rows] == ["s1", "s2"] and rows[0]["subject"] == "p1"


def test_strip_trailing_slash():
    assert pre.strip_trailing_slash("s3://b/ds/data/") == "s3://b/ds/data"
    assert pre.strip_trailing_slash("s3://b/ds/data") == "s3://b/ds/data"
    assert pre.strip_trailing_slash(" s3://b/ds/data// ") == "s3://b/ds/data"


def test_describe_counts_subjects_and_singletons():
    rows = [row("a", "p1"), row("b", "p1"), row("c", "p2")]
    assert pre.describe(rows) == (3, 2, 1)


def test_format_problems_truncates():
    text = pre.format_problems([f"p{i}" for i in range(40)])
    assert "p0" in text and "p14" in text and "p15" not in text and "and 25 more" in text


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_")]
    for name, fn in tests:
        fn()
        print("PASS ", name)
    print(f"all {len(tests)} checks passed")
