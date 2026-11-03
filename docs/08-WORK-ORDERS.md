# WORK ORDERS

1. Snapshot resources. 2. Contracts and overrides. 3. Portable consumers. 4. VLAN/STP/poison models. 5. Timeline compiler and dish 1.1. 6. Scene changes. 7. Assembly receipts and reviews. 8. Fresh reproduction and source packaging. Each order needs tests and evidence; consult implementation-status.json before claiming completion.

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

