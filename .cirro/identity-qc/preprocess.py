"""
preprocess.py -- Cirro preprocess hook for sample identity QC.

Runs before Nextflow starts. Cirro validation of the samplesheet table is
advisory (invalid rows do not block Run), so this repeats the pipeline's own
checks and stops with a message naming the row and column, instead of failing
after the run has been submitted.

It also rewrites the sheet with surrounding whitespace removed and blank rows
dropped, and turns the registry folder into a path a glob can extend.
"""
import re

ID_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
REQUIRED = ["sample", "subject", "alignment"]
SEX_VALUES = {"", "male", "female", "unknown"}
ALIGNMENT_SUFFIXES = (".bam", ".cram", ".vcf", ".vcf.gz", ".bcf", ".bcf.gz",
                      ".gvcf", ".gvcf.gz", ".g.vcf", ".g.vcf.gz")
INDEX_SUFFIXES = (".bai", ".crai", ".csi", ".tbi")
MAX_REPORTED = 15


def normalize_rows(rows):
    """Strip whitespace from every cell and drop rows with no content."""
    cleaned = []
    for row in rows:
        row = {key: str(value).strip() for key, value in row.items()}
        if any(row.values()):
            cleaned.append(row)
    return cleaned


def strip_trailing_slash(uri):
    """A folder picked from Cirro ends in '/', and a glob joined onto it gets '//'."""
    return str(uri).strip().rstrip("/")


def validate_rows(rows, columns):
    """Return a list of problems; row numbers count data rows from 1."""
    problems = []
    missing = [name for name in REQUIRED if name not in columns]
    if missing:
        return [f"The samplesheet has no column named {', '.join(missing)}."]
    if not rows:
        return ["The samplesheet has no rows. Add at least one sample."]

    first_row_of = {}
    sample_rows = {}
    for number, row in enumerate(rows, 1):
        for name in REQUIRED:
            if not row.get(name):
                problems.append(f"Row {number}: {name} is empty.")

        sample = row.get("sample", "")
        if sample:
            sample_rows.setdefault(sample, []).append(number)
            if not ID_PATTERN.fullmatch(sample):
                problems.append(f"Row {number}: sample may contain only letters, digits, '.', '_' and '-'.")
        for name in ("subject", "family"):
            value = row.get(name, "")
            if value and not ID_PATTERN.fullmatch(value):
                problems.append(f"Row {number}: {name} may contain only letters, digits, '.', '_' and '-'.")

        alignment = row.get("alignment", "")
        if alignment:
            lowered = alignment.lower()
            if not lowered.endswith(ALIGNMENT_SUFFIXES):
                problems.append(f"Row {number}: alignment must be BAM, CRAM, VCF, BCF or GVCF.")
            elif lowered.endswith((".bcf", ".bcf.gz")) and not row.get("index"):
                problems.append(f"Row {number}: BCF input needs an index.")
            if alignment in first_row_of:
                problems.append(f"Row {number}: the same file as row {first_row_of[alignment]}. "
                                "Two samples cannot share one file.")
            else:
                first_row_of[alignment] = number

        index = row.get("index", "")
        if index and not index.lower().endswith(INDEX_SUFFIXES):
            problems.append(f"Row {number}: index must end in .bai, .crai, .csi or .tbi.")

        if row.get("sex", "").lower() not in SEX_VALUES:
            problems.append(f"Row {number}: sex must be male, female or unknown.")

    for numbers in sample_rows.values():
        if len(numbers) > 1:
            problems.append("Rows " + ", ".join(map(str, numbers)) + " repeat one sample id.")
    return problems


def describe(rows):
    subjects = {}
    for row in rows:
        subjects.setdefault(row["subject"], 0)
        subjects[row["subject"]] += 1
    singles = sum(1 for count in subjects.values() if count == 1)
    return len(rows), len(subjects), singles


def format_problems(problems):
    shown = problems[:MAX_REPORTED]
    extra = len(problems) - len(shown)
    text = "The samplesheet needs fixing:\n" + "\n".join("  - " + p for p in shown)
    return text + (f"\n  ... and {extra} more" if extra > 0 else "")


def main():
    import pandas as pd
    from cirro.helpers.preprocess_dataset import PreprocessDataset

    ds = PreprocessDataset.from_running()

    path = ds.params.get("input")
    if not path:
        raise ValueError("Fill in the samplesheet before running.")
    try:
        sheet = pd.read_csv(path, dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        raise ValueError("The samplesheet is empty. Add at least one sample.") from None

    columns = list(sheet.columns)
    rows = normalize_rows(sheet.to_dict("records"))
    problems = validate_rows(rows, columns)
    if problems:
        raise ValueError(format_problems(problems))

    pd.DataFrame(rows, columns=columns).to_csv(path, index=None)

    registry = ds.params.get("registry")
    if registry:
        ds.add_param("registry", strip_trailing_slash(registry))
    elif "registry" in ds.params:
        ds.remove_param("registry")

    samples, subjects, singles = describe(rows)
    print(f"[INFO] {samples} samples under {subjects} subjects ({singles} subjects with a single sample)")
    print(f"[INFO] Registry: {'yes' if registry else 'no'}")


if __name__ == "__main__":
    main()
