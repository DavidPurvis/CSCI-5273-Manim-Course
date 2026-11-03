# VERIFICATION

Numeric tests use ipaddress, Floyd–Warshall, payload reconstruction, scalar CDMA arithmetic, and explicit model answers. Source hashes are audited. Visual/audio/caption/content review is separate from automatic checks. Unknown provenance is not a pass. Fresh-environment reproduction must render 1.1 and 3.4. See implementation-status.json for uncompleted acceptance work.

## Explicit review scope

A content pass means the current dish substantively explains every bound concept and communicates its source corrections; use the bindings and scene inventory to check this. A visual pass covers clipping, labels, arrows and state transitions. An audio pass requires listening for intelligibility and pronunciation. A caption pass checks timing, text and readability. Source-frame sampling and ASR agreement are evidence with limited scope; neither passes all four categories. A note without explicit category results changes no review state.

Run python -m course.tools.media_audit after production to decode and seek every delivered MP4, inspect audio/caption packets and marker counts, and record content hashes. It caches checks only for unchanged bytes and verifier code.


## Runbook and evidence locations

1. Run `.venv/bin/python -m pytest course/tests -q`. These checks cover the frozen instructor examples, invalid model inputs, portable sources, metadata preservation, receipt invalidation, timing and geometry. Retain the actual test output; a source inventory is not a test result.
2. Run `./kitchen audit`. Inspect build/audit.json and build/prediction-verification.json. Every source reference, all 176 bindings and every prepared timeline must resolve. This command checks prepared ingredients without regenerating authoring.
3. Run `./kitchen check` for scene dry runs, or `--quick` for preparation-only checks when unchanged scene runs already have evidence. Treat dry-run geometry and state assertions as automatic evidence with their stated scope.
4. Run `./kitchen run` and then `.venv/bin/python -m course.tools.media_audit`. The media audit checks all catalogued lessons and chapter files and two combined files. It fully decodes video/audio, seeks at multiple positions, verifies final resolution/frame rate, counts audio/caption packets and checks combined chapter markers. Cache reuse requires matching media bytes and verifier code.
5. Run fresh-environment reproduction as documented in SETUP.md. Require passing copied-source tests, successful 1.1 and 3.4 preview renders and unchanged input fingerprints.
6. Record explicit review results using `./kitchen review`; then run `./kitchen verify-release`. Keep unresolved findings visible in build/release-verification.json.

## Independent calculation obligations

Subnet tests compare normalized networks and allocation boundaries with Python ipaddress, including the /23 pool and the 31-interface /26. LPM tests compare matching prefix lengths independently of BGP policy. Fragment checks reconstruct the original payload and validate eight-byte offsets, final-fragment flags and impossible MTUs. Shortest paths are checked independently of animation traces, with the instructor path and first hop frozen separately.

Distance-vector checks evaluate neighbor advertisements and updates, including recipient-specific poison reverse and a larger-cycle limitation. BGP checks distinguish route selection, export eligibility and internal next-hop reachability. Multicast checks separate membership, reverse-path tests and shared/source-tree objectives. CDMA checks use direct scalar sums/dot products. Mobility checks preserve inner endpoints while outer tunnel destinations and forwarding state change.

For the VLAN fixture, admission precedes source learning; destination lookup follows learning. Assert the exact four table updates and egress sets. For STP, retain all physical links and assert the specified discarding endpoints. For radio, compare actual drawing coordinates and pulse radii against claimed reception sets, rather than validating a separate idealized diagram.

## Perceptual review standard

Watch transitions around ingress, learning, lookup, route failure, prediction release and handover; still images alone cannot establish causal order. Inspect early, middle and late frames of every chapter for clipping and misleading labels. Listen to the rendered audio for protocol names, formulas, addresses, intelligibility and pauses. Compare caption text and boundaries with that audio, including chapter joins and seeks. Record scope and any sampling limitations.

A ReviewDecision identifies the exact artifact hash, category, reviewer, timestamp, result and notes. A saved note changes no category. A changed artifact requires a new decision; a review of an earlier render is historical evidence. Generic approval of previews does not approve unseen chapters. Coverage review must read the actual bound explanations and source corrections rather than simply count 176 entries.

