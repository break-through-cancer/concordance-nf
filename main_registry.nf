#!/usr/bin/env nextflow
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    break-through-cancer/concordance-nf - sketch registry
    https://github.com/break-through-cancer/concordance-nf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Merges the sketches published by identity QC runs into one registry
    directory, which a later run reads through --registry. Sketches are fully
    identifying, so treat the registry as sensitive data.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

nextflow.enable.dsl = 2

include { REGISTRY } from './workflows/registry'

def helpMessage() {
    log.info """
    concordance-nf registry - merge somalier sketches into one registry

    Usage:
        nextflow run break-through-cancer/concordance-nf -main-script main_registry.nf -profile docker \\
            --sketch_dirs results_a,results_b \\
            --outdir registry

    Required:
        --sketch_dirs        Comma-separated identity QC result directories; each
                             must hold *.somalier files (sketches/ by default).

    Optional:
        --previous_registry  An earlier registry to extend.
        --on_conflict        error | replace (default: error). A sample already in
                             the previous registry with different content stops the
                             merge, or is replaced by the new sketch.
        --outdir             Default ./results
    """
}

workflow {
    if ( params.help ) {
        helpMessage()
    }
    else {
        REGISTRY()
    }
}
