# Cirro Configuration

Two processes, one folder each. Both run this repository.

| Folder | Process id | Entry script | Purpose |
|--------|------------|--------------|---------|
| `identity-qc/` | `process-btc-sample-identity-qc-1-0` | `main.nf` | Sketches every sample, compares all against all, and reports a verdict per pair. |
| `registry/` | `process-btc-sketch-registry-1-0` | `main_registry.nf` | Merges the sketches of identity QC runs into one registry dataset. |

The two forms point at each other's id through the `process` filter on their
folder pickers, so the ids registered in Cirro must match the table above.

## How the Two Fit Together

1. Run **Sample Identity QC** with a samplesheet. Its output dataset holds the
   report and, under `sketches/`, one `.somalier` file per sample.
2. Run **Sketch Registry** on one or more of those datasets. Its output dataset
   holds the merged sketches at the top level, plus `registry_manifest.tsv`
   and `merge_summary.json`.
3. Give that registry dataset to later identity QC runs as the sketch registry.
   Every sample is then also compared against everything in it.

Datasets are immutable, so extending a registry creates a new dataset. Pass the
earlier one as the registry to extend.

## Process Definition Values

These live in Cirro-pipelines, not here. Both use `executor: NEXTFLOW`,
`usesSampleSheet: false` (the form is in path mode), `code.repository:
GITHUBPUBLIC`, and `code.uri: break-through-cancer/concordance-nf`. The
`formJson`, `paramMapJson` and `webOptimizationJson` paths point at the
folder's `process-form.json`, `process-input.json` and `process-output.json`.
Identity QC lists the registry process under `childProcessIds`.

## Checks

```bash
python .cirro/identity-qc/test_preprocess.py
python .cirro/registry/test_preprocess.py
python tests/test_merge_sketches.py
```

The tests need neither pandas nor the Cirro SDK. The Cirro Claude plugin's
`cirro-agent read check-config .cirro/identity-qc` checks the form keywords and
mappings, and has not been run on these folders.

## Privacy

A sketch fully identifies an individual. Restrict access to registry datasets
the way genotype data is restricted, and share one across projects only where
the consent behind each contributing study allows it.
