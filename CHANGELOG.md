# Changelog

## Unreleased

- Minimum Nextflow version raised to 26.10.5, the version the fork is tested on.
- `main.nf` no longer uses `return` in the workflow body, which the Nextflow
  26.x parser rejects.
- Boolean parameters given on the command line as `--flag=false` arrive as the
  string `"false"`, which is truthy. `run_contamination`, `run_ancestry`,
  `skip_multiqc`, `fail_on_discordance` and `publish_sketches` are now coerced
  explicitly, so `--run_contamination=false` skips contamination as intended.
- Sketch names for BAM and CRAM input are now set from the samplesheet `sample`
  column through `SOMALIER_SAMPLE_NAME`. Previously the name came from the read
  group `SM` tag, so a mismatch turned declared pairs into registry pairs and
  shared `SM` values collided. The patched process lives in
  `modules/local/somalier_extract`; the vendored nf-core module is unchanged.
- Sample ids are restricted to letters, digits, `.`, `_` and `-`.
- `BAM_CRAM_EXTRACT_SOMALIER` fails when a sketch name differs from the
  samplesheet `sample` value.
- Pairs in which neither sample is declared in the samplesheet are skipped, so
  duplicates already archived in the registry no longer warn on every run. The
  count is reported as `n_pairs_registry_only_skipped` in the summary JSON.

## 0.1.0 - 2026-09-29

Initial release.

- somalier-based SNP concordance / sample-identity QC for BAM, CRAM, VCF, BCF
  and GVCF input.
- Samplesheet carries the expected identity structure (`subject`, `family`), so
  the report produces verdicts rather than raw relatedness numbers.
- `BAM_CRAM_EXTRACT_SOMALIER`: the alignment-input subworkflow nf-core does not
  ship, including on-the-fly indexing.
- Persistent sketch registry via `--registry`, so new samples are compared
  against project history rather than only their own batch.
- Pinned to somalier 0.3.5 rather than the 0.2.19 the nf-core modules carry.
  0.3.x brings CHARR contamination, the pairwise `contamination` subcommand, a
  long-read allele-counting fix (0.3.4) and a hom-ref/hom-alt counting fix
  (0.3.5), and renames `homozygous_concordance` to `concordance`.
- `SOMALIER_CONTAMINATION` local module: no nf-core module exists for the
  subcommand.
- Self-contained HTML report, per-pair and per-sample TSVs, machine-readable
  JSON summary, and MultiQC custom-content sections.
