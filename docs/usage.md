# Usage

## Requirements

Nextflow **≥ 26.10.5** and one of Docker, Singularity/Apptainer or Conda. No
somalier installation needed — the container is pinned by the pipeline.

26.10.5 is the version this fork is tested on. Earlier releases may work, but
they are not tested. The vendored nf-core `htslib/bgziptabix` module needs
25.04.0 or later, because the parser in 24.10 and earlier rejects its
process-scope variables.

## Typical invocations

Routine batch QC:

```bash
nextflow run Biocentric/concordance-nf -profile docker --input samplesheet.csv --fasta /ref/GRCh38.fa --outdir results
```

Against archived history — the mode this pipeline is really for:

```bash
nextflow run Biocentric/concordance-nf -profile docker --input new_batch.csv --fasta /ref/GRCh38.fa --registry /archive/somalier-sketches --outdir results
```

As a CI gate:

```bash
nextflow run Biocentric/concordance-nf -profile docker --input samplesheet.csv --fasta /ref/GRCh38.fa --fail_on_discordance --outdir results
```

Ensembl-style contig names (`1`, not `chr1`):

```bash
nextflow run Biocentric/concordance-nf -profile docker --input samplesheet.csv --fasta /ref/GRCh38.fa --genome GRCh38_nochr --outdir results
```

## Sample Naming

The `sample` column names each sketch. For BAM and CRAM input the pipeline sets
`SOMALIER_SAMPLE_NAME` to that value, so the read group `SM` tag is ignored.
Several files may share one `SM` tag, as germline and tumor files often do,
without colliding.

VCF input cannot be renamed this way, because somalier takes the name from the
VCF sample column. The VCF must hold one sample, and that column must equal the
`sample` value. The pipeline stops with an error when a sketch name differs from
the `sample` value.

Sample ids may contain only letters, digits, `.`, `_` and `-`.

## Building a registry

Point `--registry` at a directory and publish each run's sketches into it:

```bash
cp results/sketches/*.somalier /archive/somalier-sketches/
```

The sketches are build-comparable (somalier ≥ 0.2.16), so a registry can mix
GRCh37, GRCh38 and CHM13 extractions. The one exception is `GRCh38_rna`, which
uses different coordinates — keep RNA sketches in a separate registry.

Set `--publish_sketches=false` if you do not want them in the output directory.

Pairs in which neither sample is in the samplesheet are skipped, so duplicates
already archived in the registry do not warn on every run. The summary JSON
reports the count as `n_pairs_registry_only_skipped`.

## Thresholds

The defaults suit WGS at ≥ 15×. Adjust for other regimes:

- **Low depth (5–15×)** — leave the identity thresholds alone; raise
  `--min_depth` only if you want a louder warning. Relatedness degrades
  gracefully here.
- **Below ~5×** — hard-call concordance is the wrong tool. Hets read as homs, so
  relatedness biases downward and IBS0 gets noisy. Use a genotype-likelihood
  method (NgsRelate2, `bcftools gtcheck --homs-only`) instead of tuning this
  pipeline's thresholds.
- **Targeted panels** — lower `--min_sites`; a small panel legitimately yields
  far fewer usable sites. Identity itself needs very few markers: ~50
  independent MAF≈0.5 SNPs give a random-match probability around 10⁻²¹.
- **Tumour samples** — leave `--identity_max_ibs0_rate` alone. LOH depresses
  het-based concordance for a genuine same-patient pair but cannot create IBS0,
  which is why the decision leans on IBS0.
- **FFPE/degraded** — C>T deamination inflates apparent discordance. Consider a
  transversion-only sites file.

## Known behaviour worth knowing

**Extract from alignments, not joint VCFs.** Joint calling shares information
across samples, which inflates apparent concordance. The pipeline accepts VCFs
because sometimes that is all you have, but BAM/CRAM is the correct input.

**MZ twins are indistinguishable.** No SNP panel separates them; the pipeline
will report `CONFIRMED_MATCH` for two genuinely different people who happen to
be monozygotic twins.

**Contamination mimics relatedness.** A ~5% contaminated sample shows spurious
low-level kinship to its contaminant. `--run_contamination` is on by default for
exactly this reason: the pairwise estimate is directional, so it distinguishes
contamination from a real pedigree relationship.

**Command-line params beat profile params.** On Nextflow 26.10.5 a `--param`
on the command line overrides the same `params` entry set by a `-profile`
config. `-profile test` sets its own thresholds, which you can override the same
way. Write boolean flags as `--flag=false`; the pipeline coerces the string to a
boolean.

## Environments where the project directory is not on ordinary local disk

The report script is staged as a regular process input rather than run from
`bin/` on `PATH`, so it does not need the execute bit and works on filesystems
that cannot carry one (FUSE mounts, some network shares).

Containers are a separate matter. If the project directory sits on a filesystem
the container runtime's own user cannot read — a FUSE mount without
`user_allow_other`, say — Docker and Singularity will fail to stage inputs from
it even though Nextflow itself reads it fine. Keep `NXF_WORK` on local disk, and
if input staging still fails, run from a copy of the pipeline on local disk.
