# NARRATION AND TIMELINE

Samantha, 140 words/minute. Preserve cached WAV bytes. ASR alignment and interpolation are distinct; neither proves intelligibility. Legacy timing lacks provenance and requires migration. Caption policy: two lines, 42 characters/line, target 19.5 characters/second. Resolve repeated phrase occurrences explicitly. Use one compiled frame timeline for video and exports.

Scene setup uses authoritative `pre_roll` seconds, quantized to frames. Audio and captions begin at the compiled speech start; unanchored setup runs before it. Internal anchor conflicts remain errors. Every deliberate cue change is recorded in sources/choreography-decisions.json.


## Timing pipeline

Raw cached transcription → written/spoken token mapping → ASR/interpolated interval provenance → occurrence-qualified phrase anchors → integer frame schedule. The renderer invokes mutating move functions only at their start. Anchor conflicts are errors, not permission to speed up animations. Audio-byte identity invalidates timing. Caption intervals and animation schedules use 30 fps. Prediction holds prevent incidental highlighting. `build/audit.json` identifies authored conflicts. No transcription score establishes perceptual review.

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

