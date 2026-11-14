/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    REGISTRY - merge sketches from identity QC runs into one registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { MERGE_SKETCHES } from '../modules/local/merge_sketches/main'

workflow REGISTRY {

    main:

    if ( !params.sketch_dirs ) {
        error "--sketch_dirs is required: a comma-separated list of identity QC result directories."
    }
    if ( !(params.on_conflict in ['error', 'replace']) ) {
        error "--on_conflict must be 'error' or 'replace', not '${params.on_conflict}'."
    }

    def dirs = params.sketch_dirs.toString().tokenize(',')
        .collect { dir -> dir.trim().replaceFirst(/\/+$/, '') }
        .findAll { dir -> dir }

    ch_fresh = Channel.fromList( dirs )
        .map { dir ->
            def found = files("${dir}/**.somalier")
            if ( !found ) error "No *.somalier sketches found under ${dir}"
            found
        }
        .flatMap { found -> found }
        .collect()

    ch_prior = params.previous_registry
        ? Channel.fromPath("${params.previous_registry.toString().replaceFirst(/\/+$/, '')}/**.somalier", checkIfExists: true).collect()
        : Channel.value( [] )

    MERGE_SKETCHES ( ch_prior, ch_fresh, file("${projectDir}/bin/merge_sketches.py", checkIfExists: true) )

    emit:
    registry = MERGE_SKETCHES.out.registry
}
