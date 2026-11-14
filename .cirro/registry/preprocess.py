"""
preprocess.py -- Cirro preprocess hook for the sketch registry.

The folder picker returns each dataset's data folder with a trailing slash, and
anything joined onto that gets '//'. This turns the picked folders into the
comma-separated sketch_dirs list the workflow reads, with the slashes removed.
"""

MAX_REPORTED = 10


def normalize_dirs(value):
    """Accept a list or a comma-separated string; strip slashes, drop blanks and repeats."""
    items = value.split(",") if isinstance(value, str) else list(value or [])
    seen = []
    for item in items:
        cleaned = str(item).strip().rstrip("/")
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


def check_dirs(dirs):
    """Return a list of problems with the picked folders."""
    if not dirs:
        return ["Pick at least one Sample Identity QC result."]
    problems = []
    for position, item in enumerate(dirs, 1):
        if not item.startswith("s3://"):
            problems.append(f"Folder {position} is not an S3 location.")
        elif "," in item:
            problems.append(f"Folder {position} contains a comma, which the workflow cannot take.")
    return problems[:MAX_REPORTED]


def main():
    from cirro.helpers.preprocess_dataset import PreprocessDataset

    ds = PreprocessDataset.from_running()

    dirs = normalize_dirs(ds.params.get("sketches"))
    problems = check_dirs(dirs)

    previous = ds.params.get("previous_registry")
    previous = previous.strip().rstrip("/") if previous else ""
    if previous and previous in dirs:
        problems.append("The registry to extend is also listed under the results to add.")
    if problems:
        raise ValueError("The form needs fixing:\n" + "\n".join("  - " + p for p in problems))

    ds.add_param("sketch_dirs", ",".join(dirs))
    ds.remove_param("sketches")

    if previous:
        ds.add_param("previous_registry", previous)
    elif "previous_registry" in ds.params:
        ds.remove_param("previous_registry")

    print(f"[INFO] Adding sketches from {len(dirs)} datasets; extending a registry: {'yes' if previous else 'no'}")


if __name__ == "__main__":
    main()
