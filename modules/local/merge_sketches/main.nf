/*
 * MERGE_SKETCHES
 *
 * Folds new sketches into a registry directory. Each input list stages into
 * numbered directories, so sketches that share a file name across datasets
 * reach the script side by side instead of failing on staging. The script is
 * staged as an input for the same reason as in CONCORDANCE_REPORT.
 */
process MERGE_SKETCHES {
    label 'process_single'

    // conda/container set in conf/modules.config

    input:
    path prior, stageAs: 'prior?/*'
    path fresh, stageAs: 'fresh?/*'
    path merge_script

    output:
    path "registry/*.somalier",  emit: registry
    path "registry_manifest.tsv", emit: manifest
    path "merge_summary.json",    emit: summary
    tuple val("${task.process}"), val('python'), eval('python3 --version | sed "s/Python //"'), emit: versions_python, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    python3 ${merge_script} \\
        --on-conflict ${params.on_conflict} \\
        --outdir registry
    """

    stub:
    """
    mkdir registry
    touch registry/stub.somalier registry_manifest.tsv merge_summary.json
    """
}
