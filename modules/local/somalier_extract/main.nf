/*
 * somalier extract, with the sketch named from the samplesheet.
 *
 * Adapted from nf-core/somalier/extract. For BAM and CRAM input somalier names
 * the sketch from the read group SM tag unless SOMALIER_SAMPLE_NAME is set, so
 * a tag that differs from the samplesheet `sample` value, or is shared by
 * several files, produces misnamed or colliding sketches. VCF input is named
 * from the VCF sample column, which somalier does not let us override.
 */
process SOMALIER_EXTRACT {
    tag "${meta.id}"
    label 'process_low'

    // conda/container are set centrally in conf/modules.config so the somalier
    // version is pinned in exactly one place across all somalier processes

    input:
    tuple val(meta),  path(input), path(input_index)
    tuple val(meta2), path(fasta)
    tuple val(meta3), path(fai)
    tuple val(meta4), path(sites)

    output:
    tuple val(meta), path("*.somalier"), emit: extract
    tuple val("${task.process}"), val('somalier'), eval('somalier 2>&1 | sed -n \'s/.*version: \\([0-9.]*\\).*/\\1/p\''), emit: versions_somalier, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args        = task.ext.args ?: ''
    def sample_name = meta.filetype in ['bam', 'cram'] ? "export SOMALIER_SAMPLE_NAME='${meta.id}'" : ''
    """
    ${sample_name}
    somalier extract \\
        --sites ${sites} \\
        -f ${fasta} \\
        ${input} \\
        ${args}
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.somalier
    """
}
