"""Operational detail incorporated into generated architecture documents."""
NOTES = {
'05-NARRATION-AND-TIMELINE': '''

## Inputs, ownership and order

Edit spoken content in authoring/chNN.yaml. The portioner generates narration/<dish>.md and recipes/<dish>.yaml. Pronunciation configuration owns spoken substitutions; never repair a pronunciation by changing a generated transcript alone. Narration catalog identities include written text, spoken text, voice configuration and actual WAV bytes. Keep the archived alignment-evidence JSON beside the WAVs; an unchanged asset can be rebuilt without running the optional speech recognizer.

Run preparation after an authorized content change. Audit validates that measured audio sample counts agree with manifest durations and that word timing belongs to those exact audio bytes. For regenerated audio, rebuild alignment before compiling. A transcription mismatch requires correction or a documented timing review; interpolated important anchors cannot become trusted merely because the clip renders.

## Compiler execution contract

`validate_word_alignment` runs before `resolve_anchor`; `compile_beat` resolves occurrences and creates the speech, setup, movement, reading, prediction and cleanup intervals. `compile_dish` concatenates these frame intervals. `validate_timeline` rejects overlaps and overruns that the recipe does not explicitly allow. Frames use 30 fps and half-open intervals. Speech containment rounds upward; chapter offsets sum compiled frame counts rather than rounded seconds.

At playback, `Dish.play_beat` waits until each scheduled start before calling a move function. Creating a mutating move early can alter visible state before its narration; this is prohibited. Explicit simultaneous moves retain their authored relationship. A move does not gain time by shortening a reading hold, speeding the voice, or borrowing from the next beat.

## Prediction and caption procedure

Authoring prediction_contracts name the question beat, answer beat, exact answer events and object selectors. Portioning exports recipes/predictions.json; timeline compilation writes the corresponding protected intervals to build/prediction-verification.json. Structural validation establishes ordering and references. Inspect the actual video to establish that the named objects stayed hidden or neutral and that no incidental highlight supplied the answer.

Captions derive from written narration mapped onto spoken-word intervals. The caption grouping algorithm chooses word boundaries under the two-line, 42-character and 19.5-character-per-second policy. It preserves addresses and protocol tokens where possible. Conflicting readability and synchronization requirements are findings, not permission to slide captions away from speech. Native Manim captions and exported SRT/VTT use the same compiled offsets. The lower caption area remains reserved; formula and prediction banners sit above it.

Use the main assembly plan for chapters 1–12 and the supplementary plan for chapters 13–14. Each plan starts at zero independently. Transcript PDF references remain one-based instructor pages. Verify a changed narration segment, its anchors, its caption cues and the downstream chapter offset before accepting a rebuild.
''',
'06-VERIFICATION': '''

## Runbook and evidence locations

1. Run `.venv/bin/python -m pytest course/tests -q`. These checks cover the frozen instructor examples, invalid model inputs, portable sources, metadata preservation, receipt invalidation, timing and geometry. Retain the actual test output; a source inventory is not a test result.
2. Run `./kitchen audit`. Inspect build/audit.json and build/prediction-verification.json. Every source reference, all 176 bindings and every prepared timeline must resolve. This command checks prepared ingredients without regenerating authoring.
3. Run `./kitchen check` for scene dry runs, or `--quick` for preparation-only checks when unchanged scene runs already have evidence. Treat dry-run geometry and state assertions as automatic evidence with their stated scope.
4. Run `./kitchen run` and then `.venv/bin/python -m course.tools.media_audit`. The media audit checks all 64 dishes, 14 chapter files and two combined files. It fully decodes video/audio, seeks at multiple positions, verifies final resolution/frame rate, counts audio/caption packets and checks combined chapter markers. Cache reuse requires matching media bytes and verifier code.
5. Run fresh-environment reproduction as documented in SETUP.md. Require passing copied-source tests, successful 1.1 and 3.4 preview renders and unchanged input fingerprints.
6. Record explicit review results using `./kitchen review`; then run `./kitchen verify-release`. Keep unresolved findings visible in build/release-verification.json.

## Independent calculation obligations

Subnet tests compare normalized networks and allocation boundaries with Python ipaddress, including the /23 pool and the 31-interface /26. LPM tests compare matching prefix lengths independently of BGP policy. Fragment checks reconstruct the original payload and validate eight-byte offsets, final-fragment flags and impossible MTUs. Shortest paths are checked independently of animation traces, with the instructor path and first hop frozen separately.

Distance-vector checks evaluate neighbor advertisements and updates, including recipient-specific poison reverse and a larger-cycle limitation. BGP checks distinguish route selection, export eligibility and internal next-hop reachability. Multicast checks separate membership, reverse-path tests and shared/source-tree objectives. CDMA checks use direct scalar sums/dot products. Mobility checks preserve inner endpoints while outer tunnel destinations and forwarding state change.

For the VLAN fixture, admission precedes source learning; destination lookup follows learning. Assert the exact four table updates and egress sets. For STP, retain all physical links and assert the specified discarding endpoints. For radio, compare actual drawing coordinates and pulse radii against claimed reception sets, rather than validating a separate idealized diagram.

## Perceptual review standard

Watch transitions around ingress, learning, lookup, route failure, prediction release and handover; still images alone cannot establish causal order. Inspect early, middle and late frames of every chapter for clipping and misleading labels. Listen to the rendered audio for protocol names, formulas, addresses, intelligibility and pauses. Compare caption text and boundaries with that audio, including chapter joins and seeks. Record scope and any sampling limitations.

A ReviewDecision identifies the exact artifact hash, category, reviewer, timestamp, result and notes. A saved note changes no category. A changed artifact requires a new decision; a review of an earlier render is historical evidence. Generic approval of previews does not approve unseen chapters. Coverage review must read the actual bound explanations and source corrections rather than simply count 176 entries.
''',
'07-BUILD-AND-RECOVERY': '''

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
''',
'08-WORK-ORDERS': '''

## Order 1 — source snapshot

Inputs: supplied vault, preserved review and project lecture assets. Use discover_vault, snapshot_sources, parse_note, resolve_wikilink, load_course_resources and validate_resources. Run `./kitchen prepare --vault <path>` only for an intentional snapshot update. Inspect sources/snapshot/manifest.json and its structured vault source-manifest. Completion requires eleven referenced decks, matching hashes, portable note/figure/PDF links and no unresolved ambiguity. Original absolute paths are provenance only.

## Order 2 — contracts and ownership

Use course/contracts.py and course/tools/portion.py. Maintain authoritative authoring YAML, sources/teaching-bindings.yaml, sources/layout-overrides.yaml, example specs and correction/pronunciation decisions. Use load_authoring, load_overrides and portion_dish; export prepared cards, narration and prediction records. Run metadata preservation tests. Completion requires stable IDs, occurrence-qualified anchors, assertions, holds, prediction selectors and preserved overrides after generation. Consult the generated API inventory in 03-CONTRACTS.md for exact current signatures.

## Order 3 — portable consumers and coverage

Use load_course_resources for source import, question bank, readiness data, practice checks and player notes. Use validate_bindings and build_coverage_report for the 176 targets; use sources/resource-destinations.yaml for guides/examples. Run source/coverage tests and audit, then open a packaged note and instructor PDF from the player. Completion requires working local source links with the original vault unavailable. Every binding names explanatory beats and visible mechanisms; substantive sufficiency still requires content review.

## Order 4 — models and instructor fixtures

Use the fixed example adapter registry, load_example_specs, run_example and verify_example. Exercise switch_step and derive_stp_port_states, computed poison-reverse advertisements, and fragmentation input validation. Compare the four-event VLAN fixture, STP discarding endpoints, Dijkstra path/cost/first hop, stable-path assignments and seven commercial relationship cases with frozen instructor assumptions. Run independent numeric tests before accepting traces. Completion requires passing expected values and invalid-domain checks without source-driven dynamic imports or hardcoded visual answers.

## Order 5 — compile and prove dish 1.1

Use validate_word_alignment, resolve_anchor, compile_beat, compile_dish and validate_timeline. Render `./kitchen cook 1.1 --preview`, then taste it. Verify packet endpoints, changing Ethernet envelopes, actual audio identity, phrase timing, selectable captions and protected prediction/reading holds. Completion requires one frame schedule shared by renderer, captions and exports. Important inferred anchors need correction or explicit timing review, never a silent acceptance.

## Order 6 — prescribed scene amendments

Retain generated scene inventory in 04-SCENE-RECIPES.md as the exact work list. Amend 2.3 STP endpoints and 2.4 VLAN learning/lookup/flooding; move 6.1's symbolic relaxation after the worked distances and 6.2's symbolic Bellman–Ford after numerical comparison. Reserve caption space, preserve inner/outer address semantics, and inspect actual radio geometry. Keep stable beat IDs. Run targeted scene checks, then final renders and transition review for each affected dish. Unrelated choreography remains intact.

## Order 7 — assembly and evidence

Use build_assembly_plan, build_captions, validate_captions and export_transcript; main and supplements use independent plans. Use observe_stage/check_stage at event completion, fingerprint_dish/fingerprint_assembly, write_render_receipt and record_review. Run `./kitchen run`, media_audit and verify-release. Completion requires current receipts, exact frame membership, correct caption/chapter structure, audio streams, seeking and decoding. Explicit category reviews remain separate from automatic media verification and notes.

## Order 8 — reproduction and handoff

Follow SETUP.md to create a second locked Python 3.12 environment. Run course.tools.reproduction: copied-source tests plus sequential preview renders 1.1 and 3.4 using packaged WAVs. Generate the nine documents, source ZIP, viewing guide and current evidence. Run audit and verify-release; inspect implementation-status.json. MISE COMPLETE means prepared ingredients pass. MEDIA VERIFIED means current actual media passes automatic checks. RELEASE VERIFIED additionally requires current content/visual/audio/caption reviews and successful reproduction. Deliver unresolved findings with their affected ingredient and prescribed remedy; never convert an unperformed review into a pass.
'''
}
