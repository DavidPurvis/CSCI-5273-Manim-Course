# BUILD AND RECOVERY

Snapshot inputs before rendering. Fingerprints must include WAV bytes and timing as well as rendering code. Assembly has a separate fingerprint. Preserve artifacts until successors verify. Delete only project build caches. A copied source using the original virtual environment is not fresh-environment reproduction.

Rendering captures its input fingerprint before dry run and compares it after rendering. Input changes during a render reject that result. Receipts bind profile, narration bytes, beat-specific alignment and measured durations, stage code, lock and traces. Notes never imply review completion.


## Reproduction

Use a new Python 3.12 environment at build/reproduction/.venv and install requirements.lock with uv pip sync. Run python -m course.tools.reproduction. It copies source and cached assets, excludes environments/caches, runs tests and renders 1.1 and 3.4 sequentially. Results are in build/reproduction/report.json. Package with python -m course.tools.package.

## Artifact dependency and reuse rules

The source snapshot and curated bindings feed verified examples; examples and narration feed compiled timelines; timelines feed dishes; dish receipts feed chapter and combined assembly; assembly plans also feed captions, transcripts and player offsets. Prepared recipe cards, narration Markdown, traces and inventories are generated. Source snapshots and used narration assets are preserved ingredients. Reviews and receipts are version-bound evidence.

`fingerprint_dish` covers the recipe, applied overrides, narration text, actual WAVs, relevant timing, traces, renderer/compiler code, profile and dependency lock. `is_fresh` requires both the matching input identity and the actual output identity. A filename or old .fp file alone cannot authorize reuse. Preview and final profiles are distinct.

`fingerprint_assembly` separately covers the ordered plan/member receipts, export tools, snapshot references and relevant prepared player/coverage data. An export-only edit may reuse current dish renders but must rebuild affected assembled artifacts. Output hashes describe bytes independently of directory location; legacy path-salted receipts are accepted only through the explicit compatibility reader and matching bytes.

## Interrupted or rejected work

Read build/production-progress.json and the latest production log first. Resume `./kitchen run` after correcting the reported ingredient. Current successful dishes are reused; an interrupted render without a valid receipt renders again. A changed input during rendering rejects the result. Never copy a receipt onto a different file or edit a fingerprint to suppress rebuilding.

For a source diagnostic, repair the snapshot/binding or deliberately prepare a new authorized snapshot. For a timing diagnostic, repair the exact occurrence or authored spacing and rebuild timing when the WAV changed. For a numeric diagnostic, correct the model or documented assumption and rerun independent fixtures before rendering. For a layout diagnostic, use authoritative layout overrides where supported; change a recipe's authored topology only when the visual mechanism requires it. Regenerate prepared cards afterward.

After any rendered dish changes, rebuild its chapter, both relevant sidecar captions and the relevant combined output/player. Run media verification on the resulting bytes. Older reviews remain preserved but cannot pass the new hash. Keep production and perceptual completion states separate.

## Packaging and cleanup

Generate documentation from actual recipes, contracts, bindings and resource manifests, not a manually duplicated inventory. Run `.venv/bin/python -m course.tools.package` after checks. The source ZIP contains source, eleven decks, portable notes/figures, cached narration and archived alignment evidence. It excludes virtual environments, build caches, temporary media and optional recognizer caches. The archive is written to a .zip.part file, CRC-tested and atomically renamed.

Preserve the source snapshot, used WAVs, alignment provenance, render/assembly receipts, model verification and review evidence. Cleanup may remove only this project's temporary intermediates after verified successors exist. Do not clean the original vault, instructor originals, another project, or a failed artifact that is still needed to diagnose an unresolved finding.

