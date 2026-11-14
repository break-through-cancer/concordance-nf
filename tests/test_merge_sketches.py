#!/usr/bin/env python3
"""
Regression test for bin/merge_sketches.py.

Stages synthetic sketches the way MERGE_SKETCHES does (numbered directories)
and checks each merge and conflict path. Stdlib only:

    python3 tests/test_merge_sketches.py
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "bin", "merge_sketches.py")


def stage(root, prior, fresh):
    """prior and fresh are lists of {name: content} dicts, one per directory."""
    for prefix, groups in (("prior", prior), ("fresh", fresh)):
        for i, group in enumerate(groups, 1):
            os.makedirs(os.path.join(root, f"{prefix}{i}"))
            for name, content in group.items():
                with open(os.path.join(root, f"{prefix}{i}", name + ".somalier"), "w") as fh:
                    fh.write(content)


def run(prior, fresh, on_conflict="error"):
    with tempfile.TemporaryDirectory() as root:
        stage(root, prior, fresh)
        proc = subprocess.run(
            [sys.executable, SCRIPT, "--on-conflict", on_conflict],
            cwd=root, capture_output=True, text=True)
        result = {"rc": proc.returncode, "err": proc.stderr}
        if proc.returncode == 0:
            result["names"] = sorted(f[: -len(".somalier")] for f in os.listdir(os.path.join(root, "registry")))
            s2 = os.path.join(root, "registry", "s2.somalier")
            if os.path.exists(s2):
                with open(s2) as fh:
                    result["s2"] = fh.read()
            with open(os.path.join(root, "merge_summary.json")) as fh:
                result["summary"] = json.load(fh)
            with open(os.path.join(root, "registry_manifest.tsv")) as fh:
                result["manifest"] = fh.read().splitlines()
        return result


def main():
    failures = []

    def check(label, ok, detail=""):
        print(("PASS  " if ok else "FAIL  ") + label)
        if not ok:
            failures.append(label + (": " + detail if detail else ""))

    r = run([{"s0": "a", "s1": "b"}], [{"s1": "b", "s2": "c"}, {"s2": "c", "s3": "d"}])
    check("merge adds new, skips identical", r["rc"] == 0 and r["names"] == ["s0", "s1", "s2", "s3"], str(r))
    check("summary counts", r["rc"] == 0 and r["summary"]["added"] == 2 and r["summary"]["unchanged"] == 1
          and r["summary"]["total"] == 4, str(r.get("summary")))
    check("manifest lists every sample with its source",
          r["rc"] == 0 and len(r["manifest"]) == 5 and r["manifest"][1].endswith("\tprior"), str(r.get("manifest")))

    r = run([], [{"s1": "b"}])
    check("no previous registry is fine", r["rc"] == 0 and r["names"] == ["s1"], str(r))

    r = run([{"s2": "old"}], [{"s2": "new"}])
    check("fresh vs prior conflict stops by default",
          r["rc"] != 0 and "s2" in r["err"] and "on_conflict=replace" in r["err"], str(r))

    r = run([{"s2": "old"}], [{"s2": "new"}], on_conflict="replace")
    check("replace keeps the fresh sketch",
          r["rc"] == 0 and r["s2"] == "new" and r["summary"]["replaced"] == 1, str(r))

    r = run([], [{"s2": "x"}, {"s2": "y"}], on_conflict="replace")
    check("fresh vs fresh conflict always stops", r["rc"] != 0 and "s2" in r["err"], str(r))

    r = run([{"s0": ""}], [{"s1": "b"}])
    check("empty previous sketch stops", r["rc"] != 0 and "empty" in r["err"], str(r))

    r = run([], [{"s1": ""}])
    check("empty new sketch stops", r["rc"] != 0 and "empty" in r["err"], str(r))

    r = run([], [])
    check("nothing to merge stops", r["rc"] != 0 and "No sketches" in r["err"], str(r))

    print()
    if failures:
        print("FAILED (%d):" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
