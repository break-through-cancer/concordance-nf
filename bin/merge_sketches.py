#!/usr/bin/env python3
"""Merge somalier sketches into one registry directory.

Sketches arrive staged in numbered directories (prior1/, prior2/, fresh1/, ...)
so that same-named files from different datasets never collide on staging.
The sample name is the file name without ".somalier". Two sketches under one
name are the same sample: identical bytes merge silently, differing bytes are
a conflict.

Conflict policy:
  fresh vs fresh   always an error; there is no way to say which one is right
  fresh vs prior   --on-conflict error (default) stops; replace keeps fresh
"""
import argparse
import glob
import hashlib
import json
import os
import shutil
import sys

SUFFIX = ".somalier"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sample_name(path):
    return os.path.basename(path)[: -len(SUFFIX)]


def collect(pattern):
    return sorted(glob.glob(pattern))


def merge(prior_files, fresh_files, on_conflict):
    """Return (chosen, stats, errors). chosen maps name -> (path, source)."""
    chosen = {}
    errors = []
    stats = {"prior": 0, "fresh": len(fresh_files), "added": 0,
             "unchanged": 0, "replaced": 0}

    for path in prior_files:
        name = sample_name(path)
        if os.path.getsize(path) == 0:
            errors.append(f"{name}: empty sketch in the previous registry")
            continue
        if name in chosen:
            if sha256(path) != sha256(chosen[name][0]):
                errors.append(f"{name}: differing sketches within the previous registry")
            continue
        chosen[name] = (path, "prior")
        stats["prior"] += 1

    fresh_seen = {}
    for path in fresh_files:
        name = sample_name(path)
        if os.path.getsize(path) == 0:
            errors.append(f"{name}: empty sketch in the new datasets")
            continue
        digest = sha256(path)
        if name in fresh_seen:
            if digest != fresh_seen[name]:
                errors.append(f"{name}: differing sketches in the new datasets")
            continue
        fresh_seen[name] = digest

        if name not in chosen:
            chosen[name] = (path, "fresh")
            stats["added"] += 1
        elif sha256(chosen[name][0]) == digest:
            stats["unchanged"] += 1
        elif on_conflict == "replace":
            chosen[name] = (path, "replaced")
            stats["replaced"] += 1
        else:
            errors.append(
                f"{name}: already in the previous registry with different content "
                "(rerun with on_conflict=replace to keep the new sketch)"
            )
    return chosen, stats, errors


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prior-glob", default="prior*/*" + SUFFIX)
    ap.add_argument("--fresh-glob", default="fresh*/*" + SUFFIX)
    ap.add_argument("--on-conflict", choices=["error", "replace"], default="error")
    ap.add_argument("--outdir", default="registry")
    ap.add_argument("--manifest", default="registry_manifest.tsv")
    ap.add_argument("--summary", default="merge_summary.json")
    args = ap.parse_args()

    prior = collect(args.prior_glob)
    fresh = collect(args.fresh_glob)
    if not prior and not fresh:
        sys.exit("No sketches found in the previous registry or the new datasets.")

    chosen, stats, errors = merge(prior, fresh, args.on_conflict)
    if errors:
        shown = errors[:20]
        more = f"\n... and {len(errors) - len(shown)} more" if len(errors) > len(shown) else ""
        sys.exit("Registry merge refused:\n" + "\n".join(shown) + more)

    os.makedirs(args.outdir, exist_ok=True)
    with open(args.manifest, "w") as manifest:
        manifest.write("sample\tsha256\tbytes\tsource\n")
        for name in sorted(chosen):
            path, source = chosen[name]
            shutil.copyfile(path, os.path.join(args.outdir, name + SUFFIX))
            manifest.write(f"{name}\t{sha256(path)}\t{os.path.getsize(path)}\t{source}\n")

    stats["total"] = len(chosen)
    with open(args.summary, "w") as fh:
        json.dump(stats, fh, indent=2)
        fh.write("\n")
    print(f"registry: {stats['total']} sketches "
          f"({stats['added']} added, {stats['unchanged']} unchanged, {stats['replaced']} replaced)")


if __name__ == "__main__":
    main()
