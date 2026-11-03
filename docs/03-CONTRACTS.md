# CONTRACTS

See course/contracts.py for dataclass contracts. Schema version 1. Frame intervals are half-open. Layout ownership is sources/layout-overrides.yaml. Authoring YAML owns content; recipes and narration Markdown are generated. No generated file owns new content. Missing sources and unresolved anchors are errors.

## Shared records

```python
"""Portable preparation contracts. Intervals are half-open; video times are frames."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class Finding:
    code: str
    severity: str
    artifact_id: str
    location: str
    message: str
    remedy_id: str

@dataclass
class SourceRef:
    source_id: str
    path: str
    heading: str = ''
    pages: list[int] = field(default_factory=list)
    sha256: str = ''
    category: str = ''

@dataclass
class SourceManifest:
    schema_version: int
    snapshot_id: str
    records: list[SourceRef]
    required_decks: list[str]

@dataclass
class TeachingBinding:
    concept_id: str
    primary_beats: list[str]
    supporting_beats: list[str]
    source_refs: list[str]
    explanation_claim: str
    mechanism: str
    example_ids: list[str]
    prediction_pairs: list[list[str]]
    review: str = 'not_reviewed'

@dataclass
class ExampleSpec:
    example_id: str
    adapter: str
    inputs: dict
    assumptions: list[str]
    expected: Any
    verifier: str
    source_refs: list[str]

@dataclass
class NarrationAsset:
    beat_id: str
    written_hash: str
    spoken_hash: str
    configuration_hash: str
    wav_hash: str
    sample_rate: int
    sample_count: int

@dataclass
class WordAlignment:
    narration_identity: str
    aligner_identity: str
    token_mapping: list
    intervals: list
    provenance: list[str]
    mismatch_spans: list = field(default_factory=list)
    corrections: list = field(default_factory=list)

@dataclass
class PhraseAnchor:
    phrase: str
    occurrence: int = 1
    frame_offset: int = 0

@dataclass
class BeatTimeline:
    beat_id: str
    frames: int
    speech: tuple[int,int]
    moves: list[dict]
    captions: list = field(default_factory=list)
    reading: tuple[int,int] | None = None
    prediction: tuple[int,int] | None = None
    cleanup: tuple[int,int] | None = None

@dataclass
class DishTimeline:
    dish_id: str
    fps: int
    beats: list[BeatTimeline]
    total_frames: int
    fingerprint: str = ''

@dataclass
class AssemblyPlan:
    output_id: str
    members: list[str]
    offsets: dict[str,int]
    total_frames: int

@dataclass
class RenderReceipt:
    input_fingerprint: str
    profile: str
    output_hashes: dict
    media_metadata: dict
    findings: list

@dataclass
class ReviewDecision:
    artifact_hash: str
    reviewer: str
    timestamp: str
    category: str
    result: str
    notes: str

@dataclass
class ResourceCatalog:
    notes: dict
    concepts: dict
    lectures: dict
    examples: dict
    formulas: dict
    exercises: dict
    corrections: dict
    figures: dict
    aliases: dict

```


## Actual API inventory

- `model/bgp.py:7`: `select(routes)` — See implementation and tests.
- `model/bgp.py:19`: `may_export(learned_from, to)` — Would this make me carry traffic between two non-customers?
- `model/bgp.py:26`: `export_table()` — See implementation and tests.
- `model/bgp.py:39`: `rel(a, b)` — See implementation and tests.
- `model/bgp.py:49`: `valley_free(path)` — See implementation and tests.
- `model/bgp.py:64`: `hot_potato(costs)` — See implementation and tests.
- `model/bgp.py:68`: `resolve_next_hop(bgp, igp)` — See implementation and tests.
- `model/bgp.py:72`: `trace()` — See implementation and tests.
- `model/convergence.py:5`: `count_to_infinity(steps=4, poison=False, infinity=None)` — X-Y-Z chain after X-Y fails. Y and Z alternate, believing each other's stale value.
- `model/convergence.py:35`: `rip_rounds()` — See implementation and tests.
- `model/convergence.py:39`: `link_cost_change(new_xy, xy=4, yz=1, xz=50)` — Slide topology: distances to X for Y and Z, updating alternately after X-Y changes.
- `model/convergence.py:58`: `convergence_total(stages)` — See implementation and tests.
- `model/convergence.py:65`: `path_available(node, path, chosen)` — A permitted path is available only if the next hop has chosen exactly its suffix.
- `model/convergence.py:72`: `is_stable(permitted, chosen)` — See implementation and tests.
- `model/convergence.py:80`: `solve_spp(permitted)` — Exhaustive search over every path assignment, including 'no path'.
- `model/convergence.py:88`: `s(*x)` — See implementation and tests.
- `model/convergence.py:98`: `label(path)` — See implementation and tests.
- `model/convergence.py:102`: `trace()` — See implementation and tests.
- `model/discovery.py:14`: `same_subnet(a, b, prefix)` — See implementation and tests.
- `model/discovery.py:18`: `next_hop(src, dst, prefix, gateway)` — See implementation and tests.
- `model/discovery.py:22`: `journey(dst=SERVER_IP, ttl=64)` — See implementation and tests.
- `model/discovery.py:41`: `dhcp()` — See implementation and tests.
- `model/discovery.py:48`: `dns_lookup(name='www.example.test', cache=None)` — See implementation and tests.
- `model/discovery.py:60`: `cache_valid(stored_at_s, ttl_s, now_s)` — See implementation and tests.
- `model/discovery.py:64`: `trace()` — See implementation and tests.
- `model/ethernet.py:4`: `fixed_share(capacity_mbps, users)` — See implementation and tests.
- `model/ethernet.py:8`: `serialization_us(size_bytes, rate_mbps)` — See implementation and tests.
- `model/ethernet.py:12`: `min_frame_bits(rate_bps, one_way_s)` — See implementation and tests.
- `model/ethernet.py:16`: `backoff(collision, rate_bps, k)` — See implementation and tests.
- `model/ethernet.py:24`: `learning_switch(frames)` — Compatibility view of independent learning in one forwarding VLAN.
- `model/ethernet.py:41`: `stp(switches, edges)` — Equal-cost simplified STP: lowest ID is root; ties prefer the lowest parent ID.
- `model/ethernet.py:63`: `tree_path(parent, a, b)` — See implementation and tests.
- `model/ethernet.py:86`: `trace()` — See implementation and tests.
- `model/ethernet.py:106`: `switch_step(state, frame, ports)` — Independent VLAN learning; ports have id, vlans, state, and optional trunk.
- `model/ethernet.py:123`: `derive_stp_port_states(tree, topology)` — See implementation and tests.
- `model/examples.py:16`: `load_example_specs(catalog=None)` — See implementation and tests.
- `model/examples.py:21`: `run_example(spec)` — See implementation and tests.
- `model/examples.py:26`: `verify_example(spec, trace)` — See implementation and tests.
- `model/ipv4.py:4`: `to_int(dotted)` — See implementation and tests.
- `model/ipv4.py:9`: `to_dotted(value)` — See implementation and tests.
- `model/ipv4.py:13`: `mask(prefix)` — See implementation and tests.
- `model/ipv4.py:17`: `to_bits(dotted)` — See implementation and tests.
- `model/ipv4.py:21`: `decode(dotted, prefix)` — See implementation and tests.
- `model/ipv4.py:33`: `fragment(total, header, mtu)` — Constant-header arithmetic with DF clear; an already fitting datagram stays whole.
- `model/ipv4.py:53`: `frag_table(frags)` — See implementation and tests.
- `model/ipv4.py:58`: `checksum(words)` — One's-complement sum of 16-bit words, complemented.
- `model/ipv4.py:67`: `header_words(version=4, ihl=5, tos=0, total=1500, ident=7238, flags_frag=16384, ttl=64, proto=6, csum=0, src='192.0.2.10', dst='203.0.113.80')` — See implementation and tests.
- `model/ipv4.py:74`: `checksum_example(ttl=64)` — See implementation and tests.
- `model/ipv4.py:80`: `traceroute(hops, start_ttl_max=None)` — Probes with growing TTL: each one dies at the router where TTL reaches zero.
- `model/ipv4.py:93`: `trace()` — See implementation and tests.
- `model/lpm.py:8`: `matches(routes, dest)` — See implementation and tests.
- `model/lpm.py:13`: `lookup(routes, dest)` — See implementation and tests.
- `model/lpm.py:19`: `class Trie` — See implementation and tests.
- `model/lpm.py:40`: `lookup_budget(rate_bps, packet_bytes)` — See implementation and tests.
- `model/lpm.py:45`: `trace()` — See implementation and tests.
- `model/mobile.py:6`: `tunnel_headers(coa=COA)` — See implementation and tests.
- `model/mobile.py:13`: `encapsulated(inner, overhead=20)` — See implementation and tests.
- `model/mobile.py:17`: `triangle(to_anchor, to_mobile, direct)` — See implementation and tests.
- `model/mobile.py:21`: `handover_states()` — See implementation and tests.
- `model/mobile.py:27`: `handover_steps()` — See implementation and tests.
- `model/mobile.py:33`: `trace()` — See implementation and tests.
- `model/multicast.py:8`: `anycast_pick(routes, failed=())` — See implementation and tests.
- `model/multicast.py:13`: `link_load(stream_mbps, receivers, multicast)` — See implementation and tests.
- `model/multicast.py:17`: `suppression(delays)` — See implementation and tests.
- `model/multicast.py:22`: `membership_timers(query=125, response=10, robustness=2)` — See implementation and tests.
- `model/multicast.py:26`: `prim(edges, start)` — See implementation and tests.
- `model/multicast.py:36`: `kruskal(edges)` — See implementation and tests.
- `model/multicast.py:52`: `rpf(expected_port, arrival_port)` — See implementation and tests.
- `model/multicast.py:56`: `prune_recursive(children, interested, node)` — Keep a branch only when it, or some descendant, has interest.
- `model/multicast.py:62`: `spt_saving(s_rp, rp_r, s_r)` — See implementation and tests.
- `model/multicast.py:66`: `trace()` — See implementation and tests.
- `model/practice.py:11`: `trace()` — See implementation and tests.
- `model/router.py:4`: `output_queue(n, size_bytes, rate_bps)` — See implementation and tests.
- `model/router.py:9`: `hol_round(queues)` — One slot of strict FIFO inputs. Lowest input index wins a contested output.
- `model/router.py:26`: `backlog_bytes(arrive_bps, serve_bps, seconds)` — See implementation and tests.
- `model/router.py:30`: `trace()` — See implementation and tests.
- `model/routing.py:14`: `adjacency(edges)` — See implementation and tests.
- `model/routing.py:22`: `fmt(x)` — See implementation and tests.
- `model/routing.py:26`: `dijkstra(edges, src)` — See implementation and tests.
- `model/routing.py:47`: `path_to(pred, src, n)` — See implementation and tests.
- `model/routing.py:54`: `path_cost(edges, path)` — See implementation and tests.
- `model/routing.py:59`: `dijkstra_table(result, order)` — See implementation and tests.
- `model/routing.py:66`: `dv_rounds(edges, node_order=None)` — Synchronous rounds: every update reads only the previous round's vectors.
- `model/routing.py:84`: `bf_update(options)` — See implementation and tests.
- `model/routing.py:90`: `path_vector_accept(me, path)` — See implementation and tests.
- `model/routing.py:94`: `mpls_swap(table, label)` — See implementation and tests.
- `model/routing.py:106`: `trace()` — See implementation and tests.
- `model/subnet.py:5`: `host_bits(hosts)` — See implementation and tests.
- `model/subnet.py:12`: `normalize(dotted, prefix)` — See implementation and tests.
- `model/subnet.py:16`: `vlsm(parent, prefix, requests)` — See implementation and tests.
- `model/subnet.py:36`: `trace()` — See implementation and tests.
- `model/wireless.py:5`: `snr_db(ratio)` — See implementation and tests.
- `model/wireless.py:9`: `dot(a, b)` — See implementation and tests.
- `model/wireless.py:13`: `cdma_sum(pairs)` — See implementation and tests.
- `model/wireless.py:18`: `cdma_decode(z, code)` — See implementation and tests.
- `model/wireless.py:25`: `cdma_table(d1, d2)` — See implementation and tests.
- `model/wireless.py:31`: `backoff_counter(start, events)` — See implementation and tests.
- `model/wireless.py:43`: `hears(a, b, links=HEARS)` — See implementation and tests.
- `model/wireless.py:47`: `hidden_pair(a, c, receiver, links=HEARS)` — See implementation and tests.
- `model/wireless.py:51`: `nav_defer(heard_frame, duration)` — See implementation and tests.
- `model/wireless.py:55`: `spread(bit, code)` — See implementation and tests.
- `model/wireless.py:59`: `products(z, code)` — See implementation and tests.
- `model/wireless.py:63`: `trace()` — See implementation and tests.
- `stage/captioning.py:5`: `fits_lines(words, width=42)` — See implementation and tests.
- `stage/captioning.py:11`: `aligned_cues(text, speech, times, max_cps=19.5)` — See implementation and tests.
- `stage/card.py:13`: `load_card(dish)` — See implementation and tests.
- `stage/card.py:17`: `load_manifest()` — See implementation and tests.
- `stage/card.py:22`: `split_cues(text, max_chars=84)` — Break a beat's written text into caption cues of at most two lines.
- `stage/card.py:38`: `load_timing()` — See implementation and tests.
- `stage/card.py:43`: `word_times(beat_id, manifest, timing)` — Measured [start, end] for each written word, or None if this exact clip hasn't been measured.
- `stage/card.py:56`: `phrase_time(text, phrase, speech, times)` — When the narration reaches a phrase of the written text, or None if the phrase isn't there.
- `stage/card.py:70`: `timed_cues(text, speech, times)` — Caption cues as (text, offset, duration). A cue stays up until the next one starts.
- `stage/card.py:85`: `beat_times(card, manifest)` — Beats play back to back: narration, then the dish's pad, then any beat-specific hold.
- `stage/card.py:101`: `narration_text()` — See implementation and tests.
- `stage/gallery.py:62`: `class Gallery` — See implementation and tests.
- `stage/moves.py:19`: `move(name, t=1.0)` — See implementation and tests.
- `stage/moves.py:26`: `resolve(value)` — Replace "$module.key.sub" with the frozen trace value.
- `stage/moves.py:41`: `class Stage` — See implementation and tests.
- `stage/moves.py:94`: `heading(s, text)` — See implementation and tests.
- `stage/moves.py:103`: `spine(s, current, zone='full')` — See implementation and tests.
- `stage/moves.py:120`: `clear(s, keep=None)` — See implementation and tests.
- `stage/moves.py:130`: `fade(s, names)` — See implementation and tests.
- `stage/moves.py:138`: `question(s, text, zone='full', name='_q')` — See implementation and tests.
- `stage/moves.py:146`: `rule(s, text, name='_rule')` — See implementation and tests.
- `stage/moves.py:153`: `trap(s, wrong, right, name='_rule')` — The answer that sounds right, struck through, then the correction.
- `stage/moves.py:165`: `pause(s, text, long=False)` — See implementation and tests.
- `stage/moves.py:175`: `text_block(s, name, zone, lines, size=30, color=None)` — See implementation and tests.
- `stage/moves.py:185`: `bullets(s, name, zone, items, show=1, size=30, gap=0.24)` — See implementation and tests.
- `stage/moves.py:204`: `reveal(s, name, n=1)` — See implementation and tests.
- `stage/moves.py:215`: `card(s, kind, text, zone='right_bottom', name='_card')` — See implementation and tests.
- `stage/moves.py:228`: `tex(s, name, zone, tex, size=44, color=None)` — See implementation and tests.
- `stage/moves.py:237`: `net_show(s, name, zone, nodes, links=(), spread=None)` — See implementation and tests.
- `stage/moves.py:244`: `net_add(s, name, nodes=None, links=())` — See implementation and tests.
- `stage/moves.py:254`: `relink(net, key, style)` — See implementation and tests.
- `stage/moves.py:266`: `find_link(net, a, b)` — See implementation and tests.
- `stage/moves.py:275`: `net_state(s, name, nodes=None, links=())` — See implementation and tests.
- `stage/moves.py:286`: `net_path(s, name, path, style='now')` — See implementation and tests.
- `stage/moves.py:292`: `net_badge(s, name, node, text, side='right', state=None)` — See implementation and tests.
- `stage/moves.py:308`: `net_cost(s, name, a, b, cost)` — See implementation and tests.
- `stage/moves.py:316`: `net_move(s, name, node, to)` — See implementation and tests.
- `stage/moves.py:339`: `net_relink(s, name, a, b, style='solid')` — Redraw a link after its endpoint has moved, or add it if new.
- `stage/moves.py:349`: `net_unlink(s, name, a, b)` — See implementation and tests.
- `stage/moves.py:359`: `net_unbadge(s, name, node)` — See implementation and tests.
- `stage/moves.py:369`: `net_pulse(s, name, path, state='now')` — A signal runs along links.
- `stage/moves.py:379`: `net_walk(s, name, path, state='now')` — Trace a path hop by hop, in the direction data travels. It stays until the next walk.
- `stage/moves.py:392`: `net_unwalk(s, name)` — See implementation and tests.
- `stage/moves.py:397`: `msg_send(s, name, a, b, text, kind='label')` — A message with readable contents travels along a link.
- `stage/moves.py:408`: `dock(dev)` — Where a packet rests: on the icon, or just above a labelled box so the label stays readable.
- `stage/moves.py:416`: `packet_spawn(s, name, net, at, layers=('eth', 'ip'))` — See implementation and tests.
- `stage/moves.py:426`: `packet_hop(s, name, to)` — See implementation and tests.
- `stage/moves.py:438`: `packet_both(s, moves)` — Several packets move at the same moment.
- `stage/moves.py:447`: `packet_peel(s, name)` — See implementation and tests.
- `stage/moves.py:455`: `packet_wrap(s, name, kind='eth')` — See implementation and tests.
- `stage/moves.py:467`: `packet_swap(s, name, kind='eth')` — See implementation and tests.
- `stage/moves.py:481`: `packet_flood(s, name, to, keep=False)` — See implementation and tests.
- `stage/moves.py:494`: `packet_drop(s, name)` — See implementation and tests.
- `stage/moves.py:503`: `packet_fade(s, name)` — See implementation and tests.
- `stage/moves.py:509`: `switch_learn(s, table, mac, port, net=None, node=None)` — See implementation and tests.
- `stage/moves.py:517`: `graph_promote(s, name, node, via=None)` — See implementation and tests.
- `stage/moves.py:526`: `graph_relax(s, name, via, node, text, side='right', state='now')` — Try a route through a settled node: a signal crosses the edge, and the neighbor's distance updates.
- `stage/moves.py:544`: `tunnel_re(s, stack, outer, kind='tunnel')` — See implementation and tests.
- `stage/moves.py:550`: `radio_zone(s, net, node, radius=1.6, name=None, kind='radio')` — See implementation and tests.
- `stage/moves.py:559`: `radio_pulse(s, net, node, radius=1.8, kind='radio')` — See implementation and tests.
- `stage/moves.py:566`: `burst(s, net, node=None, between=None)` — See implementation and tests.
- `stage/moves.py:575`: `table_show(s, name, zone, data=None, cols=None, rows=None, show=None, size=30, ghost=(), row_h=0.52)` — See implementation and tests.
- `stage/moves.py:591`: `table_reveal(s, name, n=1)` — See implementation and tests.
- `stage/moves.py:603`: `table_add(s, name, row, state=None)` — See implementation and tests.
- `stage/moves.py:626`: `table_set(s, name, r, c, v, state=None)` — See implementation and tests.
- `stage/moves.py:638`: `table_mark(s, name, r, state='now')` — See implementation and tests.
- `stage/moves.py:644`: `table_flash(s, name, rows, state='candidate')` — Mark several rows in the same instant, the way parallel hardware compares them.
- `stage/moves.py:655`: `bits_show(s, name, zone, rows, reserve=None)` — See implementation and tests.
- `stage/moves.py:665`: `bits_add(s, name, label, value)` — See implementation and tests.
- `stage/moves.py:676`: `bits_mask(s, name, prefix, rows=None)` — See implementation and tests.
- `stage/moves.py:695`: `bits_scan(s, name, label, value)` — Work out a new row one bit at a time: a line sweeps across, and each result bit lands under it.
- `stage/moves.py:710`: `bits_mark(s, name, row, start, end, state='now')` — See implementation and tests.
- `stage/moves.py:717`: `seq_show(s, name, zone, lanes, steps=6)` — See implementation and tests.
- `stage/moves.py:723`: `seq_msg(s, name, a, b, text, kind='ip', state=None)` — See implementation and tests.
- `stage/moves.py:737`: `tl_show(s, name, zone, tracks, span, ticks=None)` — See implementation and tests.
- `stage/moves.py:743`: `tl_block(s, name, track, start, end, text='', kind='data', state=None)` — See implementation and tests.
- `stage/moves.py:759`: `sieve_show(s, name, zone, rungs, routes, size=30)` — See implementation and tests.
- `stage/moves.py:765`: `sieve_step(s, name, rung, keep)` — Compare one row. Whoever loses stops being considered.
- `stage/moves.py:780`: `sieve_win(s, name, route, unused=())` — The survivor wins. Later rows never get looked at.
- `stage/moves.py:791`: `bar_show(s, name, zone, total, header=20, unit=8, rows=3)` — See implementation and tests.
- `stage/moves.py:797`: `bar_ruler(s, name)` — See implementation and tests.
- `stage/moves.py:806`: `bar_cut_mark(m, at, color)` — See implementation and tests.
- `stage/moves.py:812`: `bar_cut(s, name, at, state='now')` — A cut sweeps along the data and lands at a byte position.
- `stage/moves.py:825`: `bar_zoom(s, name, at, state='now')` — See implementation and tests.
- `stage/moves.py:833`: `bar_snap(s, name, at, state='done')` — The zoomed cut moves to a legal position.
- `stage/moves.py:844`: `bar_info_text(m, i, frag)` — See implementation and tests.
- `stage/moves.py:856`: `bar_slice(s, name, i, frag, info=True)` — One fragment drops out of the original and gains its own header.
- `stage/moves.py:892`: `bar_info(s, name, i, frag)` — See implementation and tests.
- `stage/moves.py:902`: `bar_join(s, name)` — The data slides back together, proving nothing was lost. The extra headers stay behind.
- `stage/moves.py:912`: `bar_mark(s, name, what, state='now')` — Outline the headers, the whole data bar, or one row's header.
- `stage/moves.py:924`: `bar_span(s, name, to, text)` — A measure from the start of the data to a byte position: this is what an offset means.
- `stage/moves.py:936`: `bar_note(s, name, tex=None, text=None, side='center', state=None)` — See implementation and tests.
- `stage/moves.py:950`: `tl_ghost(s, name, track, start, end, text='', state='error')` — A trial block, which a later tl.slide can move.
- `stage/moves.py:964`: `tl_slide(s, name, start, end, text='', state='done')` — The trial block slides to where it belongs.
- `stage/moves.py:981`: `stack_show(s, name, zone, layers, width=None, reserve=0)` — reserve leaves room above for layers that will be pushed later.
- `stage/moves.py:992`: `stack_set(s, name, layer, text, kind=None)` — See implementation and tests.
- `stage/moves.py:1003`: `stack_push(s, name, text, kind='eth')` — See implementation and tests.
- `stage/moves.py:1012`: `stack_pop(s, name)` — See implementation and tests.
- `stage/moves.py:1020`: `stack_mark(s, name, layer, state='now')` — See implementation and tests.
- `stage/moves.py:1026`: `fields_show(s, name, zone, rows, unit=0.2)` — See implementation and tests.
- `stage/moves.py:1033`: `fields_mark(s, name, label, state='now')` — See implementation and tests.
- `stage/moves.py:1039`: `queue_show(s, name, zone, items, kind='data', title=None, cell_w=1.0)` — See implementation and tests.
- `stage/moves.py:1048`: `queue_pop(s, name)` — See implementation and tests.
- `stage/moves.py:1055`: `queue_mark(s, name, i, state='error')` — See implementation and tests.
- `stage/moves.py:1061`: `chips_show(s, name, zone, rows, show=None)` — Chip signals, one row each. Rows past show are placed now and appear later.
- `stage/moves.py:1074`: `chips_reveal(s, name)` — See implementation and tests.
- `stage/moves.py:1082`: `chips_flip(s, name, row, values, label)` — A sender's bit of minus one turns its code upside down.
- `stage/moves.py:1095`: `chips_sum(s, name)` — On the air the signals simply add: the waves slide together into the next row.
- `stage/moves.py:1109`: `chips_dot(s, name, a, b, products, total, result)` — Correlate two rows: walk the chips, multiply each pair, add them up, divide by the code length.
- `stage/moves.py:1139`: `plot_show(s, name, zone, xlabel, ylabel, curves, xr=(0, 1), yr=(0, 1))` — See implementation and tests.
- `stage/moves.py:1145`: `plot_mark(s, name, x, y, text='', state='now')` — See implementation and tests.
- `stage/moves.py:1156`: `net_port_state(s, name, device, peer, state)` — See implementation and tests.
- `stage/moves.py:1165`: `observe_stage(stage)` — See implementation and tests.
- `stage/moves.py:1172`: `check_stage(observation, assertions)` — See implementation and tests.
- `stage/parts.py:9`: `T(text, size=28, color=INK, weight='NORMAL')` — See implementation and tests.
- `stage/parts.py:15`: `wrap_lines(text, width, size)` — See implementation and tests.
- `stage/parts.py:28`: `paragraph(text, width, size=30, color=INK, center=False)` — See implementation and tests.
- `stage/parts.py:34`: `zone_box(zone)` — See implementation and tests.
- `stage/parts.py:39`: `place(mob, zone, grow=False)` — See implementation and tests.
- `stage/parts.py:48`: `outline(mob, state, buff=0.09)` — See implementation and tests.
- `stage/parts.py:58`: `icon(kind, text='')` — See implementation and tests.
- `stage/parts.py:105`: `segment_hits_box(p0, p1, center, w, h, pad=0.02)` — Does a straight segment touch a box? Liang-Barsky clipping.
- `stage/parts.py:128`: `class Device` — See implementation and tests.
- `stage/parts.py:149`: `class Net` — A diagram of devices and links. Coordinates are stretched to fill a zone; glyphs keep their size.
- `stage/parts.py:260`: `class Grid` — See implementation and tests.
- `stage/parts.py:300`: `class BitRow` — See implementation and tests.
- `stage/parts.py:323`: `class Ladder` — See implementation and tests.
- `stage/parts.py:346`: `class Tracks` — See implementation and tests.
- `stage/parts.py:373`: `layer_block(text, kind, width=4.6, height=0.62)` — See implementation and tests.
- `stage/parts.py:379`: `class Stack` — See implementation and tests.
- `stage/parts.py:389`: `class Fields` — A header drawn by rows, with cells sized by their share of the row.
- `stage/parts.py:411`: `class Slots` — A FIFO drawn left to right; the head is on the right.
- `stage/parts.py:433`: `class StepWave` — Chip values drawn as a step signal, for code-division sums.
- `stage/parts.py:452`: `class Curves` — See implementation and tests.
- `stage/parts.py:479`: `class Sieve` — Candidates in columns, decision steps in rows. A candidate drops out at the first row it loses.
- `stage/parts.py:515`: `class ByteBar` — A datagram drawn to scale. Slices keep their place under the original, so an offset is visibly a distance.
- `stage/parts.py:596`: `class PacketToken` — See implementation and tests.
- `stage/player.py:20`: `class Dish` — See implementation and tests.
- `stage/signal.py:18`: `tokens(text)` — See implementation and tests.
- `stage/signal.py:28`: `fold(tok)` — See implementation and tests.
- `stage/signal.py:36`: `spoken_words(text, times)` — See implementation and tests.
- `stage/signal.py:46`: `items_on_stage(stage)` — Everything with a name the narration might say: (text, mobject to ring).
- `stage/signal.py:68`: `find(words, start, end, stage, used)` — Highlights due between two moments in the beat, as (time, mobject). used maps an item to when it last lit up.
- `stage/signal.py:102`: `flash(mob)` — See implementation and tests.
- `stage/theme.py:31`: `zones_overlap(a, b)` — See implementation and tests.
- `stage/timeline.py:8`: `resolve_anchor(anchor, text, times, speech, fps=30)` — See implementation and tests.
- `stage/timeline.py:19`: `compile_beat(beat, asset, alignment, text='', pad=2.2, fps=30, defaults=None)` — See implementation and tests.
- `stage/timeline.py:58`: `compile_dish(card, manifest, timing, texts, defaults=None)` — See implementation and tests.
- `stage/timeline.py:79`: `validate_timeline(timeline)` — See implementation and tests.
- `stage/timeline.py:87`: `build_assembly_plan(members, output_id)` — See implementation and tests.
- `stage/timeline.py:94`: `validate_word_alignment(asset, alignment)` — See implementation and tests.
- `stage/timeline.py:105`: `build_captions(text, alignment, policy=None)` — See implementation and tests.
- `stage/timeline.py:112`: `validate_captions(cues, timeline)` — See implementation and tests.
- `stage/timeline.py:122`: `export_transcript(plan, catalog)` — See implementation and tests.
- `tools/assembly.py:8`: `course_plans()` — See implementation and tests.
- `tools/assembly.py:21`: `write_plans(destination=None)` — See implementation and tests.
- `tools/audition.py:17`: `main()` — See implementation and tests.
- `tools/bank.py:14`: `clean(text)` — See implementation and tests.
- `tools/bank.py:22`: `links(text)` — See implementation and tests.
- `tools/bank.py:26`: `recipe_maps()` — Which dishes teach each concept, and the dishes of each chapter.
- `tools/bank.py:40`: `tie(concepts, text, chapter, by_concept, by_chapter, names)` — Linked concepts first, then concept names found in the text, then the whole chapter.
- `tools/bank.py:54`: `exam_cues(by_concept, by_chapter, names)` — See implementation and tests.
- `tools/bank.py:66`: `lecture_questions(by_concept, by_chapter, names)` — See implementation and tests.
- `tools/bank.py:84`: `practice_midterm(by_concept, by_chapter, names)` — See implementation and tests.
- `tools/bank.py:107`: `build()` — See implementation and tests.
- `tools/bank.py:117`: `main()` — See implementation and tests.
- `tools/build_traces.py:11`: `main()` — See implementation and tests.
- `tools/drills.py:14`: `field(key, label, answer, options=None)` — See implementation and tests.
- `tools/drills.py:21`: `address_math(rng)` — See implementation and tests.
- `tools/drills.py:40`: `subnet_sizing(rng)` — See implementation and tests.
- `tools/drills.py:51`: `longest_match(rng)` — See implementation and tests.
- `tools/drills.py:81`: `fragmentation(rng)` — See implementation and tests.
- `tools/drills.py:96`: `switch_learning(rng)` — See implementation and tests.
- `tools/drills.py:127`: `dijkstra(rng)` — See implementation and tests.
- `tools/drills.py:149`: `bellman_ford(rng)` — See implementation and tests.
- `tools/drills.py:165`: `bgp_selection(rng)` — See implementation and tests.
- `tools/drills.py:189`: `cdma(rng)` — See implementation and tests.
- `tools/drills.py:202`: `reverse_path(rng)` — See implementation and tests.
- `tools/drills.py:223`: `build()` — See implementation and tests.
- `tools/drills.py:239`: `main()` — See implementation and tests.
- `tools/ears.py:24`: `raw_tokens(text)` — Lowercase tokens with numbers, addresses, and punctuation in one common form.
- `tools/ears.py:38`: `parse_number(tokens, i)` — Read number words starting at i. Returns the value and the index after them; no number leaves the index at i.
- `tools/ears.py:60`: `fold_numbers(tokens)` — Turn runs of number words into digits, keeping for each output token the index of the input token it came from.
- `tools/ears.py:76`: `norm_with_map(tokens_by_source)` — Normalize a list of source tokens; return the flat tokens and, for each, its source index.
- `tools/ears.py:87`: `transcribe(beat, entry)` — See implementation and tests.
- `tools/ears.py:113`: `align(written, heard, duration, rules)` — A [start, end] time for each written word, plus the share of it that matched and the mismatched segments.
- `tools/ears.py:160`: `expected_differences(rules_data)` — Differences that only reflect spelling: the transcriber wrote the real word where the script holds a respelling.
- `tools/ears.py:169`: `real_differences(seen, rules_data)` — See implementation and tests.
- `tools/ears.py:187`: `main()` — See implementation and tests.
- `tools/evidence.py:9`: `hash_files(paths)` — See implementation and tests.
- `tools/evidence.py:16`: `fingerprint_dish(dish_id, context=None)` — See implementation and tests.
- `tools/evidence.py:33`: `fingerprint_assembly(plan, context=None)` — See implementation and tests.
- `tools/evidence.py:41`: `write_render_receipt(video, dish, profile, findings=(), input_fingerprint=None)` — See implementation and tests.
- `tools/evidence.py:49`: `write_assembly_receipt(video, plan, members, findings=())` — Record the ordered render receipts separately from the assembled output.
- `tools/evidence.py:63`: `artifact_hash(path)` — An output's identity is its bytes, independent of build or package location.
- `tools/evidence.py:71`: `artifact_matches(path, recorded)` — Read schema-1 path-salted receipts while writing portable SHA-256 identities.
- `tools/gemini.py:24`: `packaged_output(root=ROOT)` — See implementation and tests.
- `tools/gemini.py:28`: `default_output(root=ROOT)` — See implementation and tests.
- `tools/gemini.py:34`: `transcript_path(root, name)` — See implementation and tests.
- `tools/gemini.py:39`: `sha(text)` — See implementation and tests.
- `tools/gemini.py:43`: `read_json(path)` — See implementation and tests.
- `tools/gemini.py:54`: `source_documents(root=ROOT)` — Return ordered (portable label, exact UTF-8 text) pairs; fail closed.
- `tools/gemini.py:97`: `manifest_for(brief, documents)` — See implementation and tests.
- `tools/gemini.py:105`: `render(root=ROOT)` — See implementation and tests.
- `tools/gemini.py:156`: `validate_freshness(root=ROOT, output=None)` — Read-only audit of selected handoff, packaged copy, and portable inputs.

Parent transcript/handoff directories take precedence when present. Only
absent parent directories enable standalone fallbacks; missing files within
a present parent directory must be repaired. No preparation imports.
- `tools/gemini.py:185`: `export(root=ROOT, output=None)` — See implementation and tests.
- `tools/gemini.py:205`: `main()` — See implementation and tests.
- `tools/handoff.py:18`: `clone(source, target)` — See implementation and tests.
- `tools/handoff.py:34`: `read_status(source, course)` — Consume refresh()'s shared status without changing release evidence.
- `tools/handoff.py:51`: `validate_handoff(target, status)` — Validate the staged copy before its name can become the destination.
- `tools/handoff.py:74`: `promote(staged, target)` — Rename only validated trees; retain old output and roll back a failed rename.

Each rename is atomic on the shared filesystem. Replacing an existing nonempty
directory takes two renames, so readers can briefly see the destination absent.
- `tools/handoff.py:93`: `bundle_snapshot(snapshot, source_manifest, staged)` — Bundle vault notes and required decks; other provenance stays in the source ZIP.
- `tools/handoff.py:132`: `build_handoff(course, source, destination)` — See implementation and tests.
- `tools/handoff.py:185`: `main(destination=None)` — See implementation and tests.
- `tools/kitchen.py:29`: `dishes()` — See implementation and tests.
- `tools/kitchen.py:33`: `chapter_of(d)` — See implementation and tests.
- `tools/kitchen.py:37`: `run(cmd, **kw)` — See implementation and tests.
- `tools/kitchen.py:41`: `probe_duration(path, stream=None)` — See implementation and tests.
- `tools/kitchen.py:50`: `free_gib()` — See implementation and tests.
- `tools/kitchen.py:54`: `manim(dish, res, media, *extra, env=None)` — See implementation and tests.
- `tools/kitchen.py:61`: `dry_run(dish)` — See implementation and tests.
- `tools/kitchen.py:77`: `fingerprint(dish)` — See implementation and tests.
- `tools/kitchen.py:82`: `fp_path(dish)` — See implementation and tests.
- `tools/kitchen.py:86`: `is_fresh(dish)` — See implementation and tests.
- `tools/kitchen.py:99`: `group_fp(members)` — See implementation and tests.
- `tools/kitchen.py:106`: `check_static()` — Everything that can be verified without running Manim.
- `tools/kitchen.py:189`: `write_coverage(used)` — See implementation and tests.
- `tools/kitchen.py:199`: `cmd_check(args)` — See implementation and tests.
- `tools/kitchen.py:238`: `video_path(dish, quality)` — See implementation and tests.
- `tools/kitchen.py:242`: `cmd_cook(args)` — See implementation and tests.
- `tools/kitchen.py:278`: `fmt(t, sep=',')` — See implementation and tests.
- `tools/kitchen.py:287`: `cues_for(dish, offset=0.0)` — See implementation and tests.
- `tools/kitchen.py:302`: `two_lines(text, width=42)` — See implementation and tests.
- `tools/kitchen.py:311`: `write_subs(cues, srt, vtt)` — See implementation and tests.
- `tools/kitchen.py:319`: `caption_problems(cues)` — See implementation and tests.
- `tools/kitchen.py:332`: `cmd_taste(args)` — See implementation and tests.
- `tools/kitchen.py:393`: `concat(files, out, extra=())` — See implementation and tests.
- `tools/kitchen.py:401`: `verify_playback(path, expected=None)` — See implementation and tests.
- `tools/kitchen.py:419`: `chapter_title(ch)` — See implementation and tests.
- `tools/kitchen.py:426`: `chapter_cues(ch)` — See implementation and tests.
- `tools/kitchen.py:435`: `cmd_plate(args)` — See implementation and tests.
- `tools/kitchen.py:492`: `transcript(chapter_start, output_id='main')` — See implementation and tests.
- `tools/kitchen.py:522`: `pending_reviews()` — Explicit category reviews still missing for the current final renders: four per dish.
- `tools/kitchen.py:538`: `guide(rows, total)` — See implementation and tests.
- `tools/kitchen.py:572`: `cmd_serve(args)` — See implementation and tests.
- `tools/kitchen.py:678`: `second_video(chapters, files, caps)` — The practice walkthrough and warm-up, in their own file with their own markers and captions.
- `tools/kitchen.py:701`: `reproduce(dish='1.1')` — Render a dish from a clean copy of the package, using only supplied source and audio.
- `tools/kitchen.py:724`: `stop(where)` — See implementation and tests.
- `tools/kitchen.py:729`: `cook_everything()` — See implementation and tests.
- `tools/kitchen.py:774`: `freeze()` — Cook from a snapshot, so prep can keep working while a release cooks.
- `tools/kitchen.py:788`: `cmd_run(args)` — See implementation and tests.
- `tools/kitchen.py:803`: `cmd_review(args)` — See implementation and tests.
- `tools/kitchen.py:813`: `cmd_open(args)` — See implementation and tests.
- `tools/kitchen.py:824`: `main()` — See implementation and tests.
- `tools/local_server.py:16`: `make_handler(mounts, on_post=None)` — mounts maps a URL prefix to a folder; the longest matching prefix wins.
- `tools/local_server.py:104`: `create_server(mounts, on_post=None, port=PORT)` — Bind loopback; let the OS choose a free port if the preferred one is busy.
- `tools/local_server.py:115`: `serve(mounts, start='/', on_post=None, port=PORT, open_browser=True)` — See implementation and tests.
- `tools/media_audit.py:9`: `sha256(path)` — See implementation and tests.
- `tools/media_audit.py:16`: `inspect_media(path)` — See implementation and tests.
- `tools/media_audit.py:35`: `verification_identity()` — See implementation and tests.
- `tools/media_audit.py:40`: `main()` — See implementation and tests.
- `tools/narration_assets.py:9`: `catalog_assets()` — See implementation and tests.
- `tools/narration_assets.py:32`: `write_catalog()` — See implementation and tests.
- `tools/narration_assets.py:39`: `export_alignment_evidence()` — Preserve used cached transcriptions; reuse packaged evidence for unchanged assets.
- `tools/narration_assets.py:56`: `validate_alignment_evidence()` — See implementation and tests.
- `tools/package.py:8`: `main()` — See implementation and tests.
- `tools/playback.py:18`: `mounts(root)` — See implementation and tests.
- `tools/playback.py:24`: `asset_path(root, url)` — Resolve a local player URL, rejecting escapes and remote dependencies.
- `tools/playback.py:41`: `sha256(path)` — See implementation and tests.
- `tools/playback.py:49`: `validate_assets(root)` — Return missing/corrupt playback dependencies, without importing the kitchen.
- `tools/playback.py:96`: `write_launcher(destination)` — Install the two stdlib Python files and macOS double-click entry point.
- `tools/playback.py:109`: `main(argv=None)` — See implementation and tests.
- `tools/player_build.py:29`: `assessment_date(root=ROOT)` — Read optional study metadata; absent/null/blank means an undated player.
- `tools/player_build.py:49`: `dish_order(d)` — See implementation and tests.
- `tools/player_build.py:53`: `note_url(relative)` — See implementation and tests.
- `tools/player_build.py:57`: `route(all_dishes)` — The vault's Sunday-to-Wednesday route as a list of boxes, one thing at a time.
- `tools/player_build.py:86`: `slide_name(deck, page)` — See implementation and tests.
- `tools/player_build.py:90`: `render_slides(needed, folder)` — See implementation and tests.
- `tools/player_build.py:103`: `readiness()` — See implementation and tests.
- `tools/player_build.py:113`: `build_data()` — See implementation and tests.
- `tools/player_build.py:155`: `main()` — See implementation and tests.
- `tools/portion.py:7`: `load_authoring(root: Path)` — See implementation and tests.
- `tools/portion.py:12`: `load_overrides(path: Path)` — See implementation and tests.
- `tools/portion.py:16`: `portion_dish(dish: dict, overrides: dict)` — Pure conversion: preserve authored event metadata and merge explicit layout overrides.
- `tools/portion.py:36`: `main()` — See implementation and tests.
- `tools/predictions.py:8`: `load_prediction_contracts()` — See implementation and tests.
- `tools/predictions.py:13`: `validate_prediction_contracts(timelines)` — See implementation and tests.
- `tools/preparation.py:14`: `digest(path)` — See implementation and tests.
- `tools/preparation.py:18`: `discover_vault(root)` — See implementation and tests.
- `tools/preparation.py:23`: `snapshot_sources(inventory, destination)` — See implementation and tests.
- `tools/preparation.py:34`: `write_source_manifest(records)` — See implementation and tests.
- `tools/preparation.py:48`: `parse_note(path)` — See implementation and tests.
- `tools/preparation.py:54`: `audit()` — See implementation and tests.
- `tools/preparation.py:92`: `record_review(decision, store)` — See implementation and tests.
- `tools/preparation.py:99`: `prepare()` — See implementation and tests.
- `tools/preparation.py:116`: `generate_docs(cards, bindings)` — See implementation and tests.
- `tools/preparation.py:164`: `cmd_prepare(args)` — See implementation and tests.
- `tools/preparation.py:180`: `timeline_findings()` — See implementation and tests.
- `tools/preparation.py:201`: `cmd_audit(args)` — See implementation and tests.
- `tools/preparation.py:210`: `cmd_verify(args)` — See implementation and tests.
- `tools/preparation.py:218`: `load_course_resources(snapshot=SNAPSHOT)` — See implementation and tests.
- `tools/preparation.py:233`: `resolve_wikilink(link, catalog)` — See implementation and tests.
- `tools/preparation.py:258`: `validate_resources(catalog)` — See implementation and tests.
- `tools/preparation.py:279`: `load_bindings(path)` — See implementation and tests.
- `tools/preparation.py:283`: `validate_bindings(catalog, dishes, bindings)` — See implementation and tests.
- `tools/preparation.py:306`: `build_coverage_report(catalog, bindings)` — See implementation and tests.
- `tools/preparation.py:310`: `verify_release(context=None)` — See implementation and tests.
- `tools/reference_integrity.py:8`: `collect(root=ROOT)` — See implementation and tests.
- `tools/reference_integrity.py:21`: `validate_reference_integrity(root=ROOT)` — See implementation and tests.
- `tools/release_status.py:8`: `class ReleaseStatus` — See implementation and tests.
- `tools/release_status.py:22`: `calculate(findings, input_findings, revision, current, expected)` — See implementation and tests.
- `tools/release_status.py:36`: `refresh()` — See implementation and tests.
- `tools/reproduction.py:21`: `sha256(path)` — See implementation and tests.
- `tools/reproduction.py:29`: `source_content_identity(root)` — Hash packaged authored/runtime inputs, excluding generated status and docs.

Archive bytes identify the exact candidate tested; this independent identity
survives ZIP timestamps, compression and generated documentation changes.
- `tools/reproduction.py:52`: `extract_candidate(archive, destination, *, max_bytes=20 * 1024 ** 3, max_members=50000)` — Validate all members before extracting; accept only a source/ rooted ZIP.

Reject traversal, Windows paths, symlinks/devices, duplicates, encrypted
entries and excessive expanded size. Never overlay an earlier source tree.
- `tools/reproduction.py:113`: `isolated_env()` — See implementation and tests.
- `tools/reproduction.py:120`: `run_python(python, root, code, *, env=None)` — See implementation and tests.
- `tools/reproduction.py:127`: `validate_environment(python, root, lock)` — See implementation and tests.
- `tools/reproduction.py:156`: `fingerprints(python, root)` — See implementation and tests.
- `tools/reproduction.py:165`: `reproduce(archive=None, *, root=ROOT, base=None, python=None)` — See implementation and tests.
- `tools/reproduction.py:237`: `main(argv=None)` — See implementation and tests.
- `tools/review_page.py:8`: `build(build_dir, pack, dishes, load_card, fp_of)` — See implementation and tests.
- `tools/review_page.py:74`: `save_notes(data, notes_path, build_dir)` — See implementation and tests.
- `tools/review_queue.py:20`: `read_json(path, default=None)` — See implementation and tests.
- `tools/review_queue.py:24`: `texts_and_cards(root)` — See implementation and tests.
- `tools/review_queue.py:42`: `parse_asr(root, manifest, timing)` — See implementation and tests.
- `tools/review_queue.py:83`: `audit_bindings(root, bindings, texts, beats)` — Inspect every binding against actual narration and move IDs, conservatively.
- `tools/review_queue.py:127`: `pending_reviews(artifact_hash)` — See implementation and tests.
- `tools/review_queue.py:133`: `artifact_info(path, receipt=None)` — See implementation and tests.
- `tools/review_queue.py:141`: `build_queue(root=ROOT)` — See implementation and tests.
- `tools/review_queue.py:203`: `write_queue(queue, destination)` — See implementation and tests.
- `tools/review_queue.py:224`: `prepare_pilot(root, queue, destination, max_seconds=90)` — Concatenate complete flagged clips with silence; never upload anything.
- `tools/review_queue.py:280`: `main(argv=None)` — See implementation and tests.
- `tools/snap.py:14`: `run(dish, sheet=True)` — See implementation and tests.
- `tools/snap.py:44`: `main()` — See implementation and tests.
- `tools/snap.py:61`: `still_report(dishes)` — Where the picture stays still, estimated from every animation's scheduled time.
- `tools/sources.py:22`: `main()` — See implementation and tests.
- `tools/still_map.py:16`: `freezes(video, level, least=4)` — See implementation and tests.
- `tools/still_map.py:26`: `beats_of(dish)` — See implementation and tests.
- `tools/still_map.py:42`: `report(dish, level, over)` — See implementation and tests.
- `tools/still_map.py:52`: `main()` — See implementation and tests.
- `tools/stills.py:11`: `stretches(video)` — Every still stretch as (start seconds, length seconds).
- `tools/stills.py:34`: `report(video)` — See implementation and tests.
- `tools/tts.py:22`: `load_rules(config=CONFIG)` — See implementation and tests.
- `tools/tts.py:36`: `spoken_form(text, rules, config=CONFIG)` — See implementation and tests.
- `tools/tts.py:43`: `plain_form(spoken)` — Remove Kokoro's phoneme notation, leaving the word.
- `tools/tts.py:48`: `clip_key(spoken, config=CONFIG)` — See implementation and tests.
- `tools/tts.py:56`: `raw_say(spoken, path, config)` — See implementation and tests.
- `tools/tts.py:63`: `raw_kokoro(spoken, path, config)` — Kokoro speaks each stretch between pause marks; the pauses go in as silence.
- `tools/tts.py:93`: `render_clip(spoken, wav, config=CONFIG)` — Speak the text, then bring it to the course's level and format.
- `tools/tts.py:108`: `synth(job)` — See implementation and tests.
- `tools/tts.py:118`: `main(only=None)` — See implementation and tests.

## Prepared prediction records

A prepared recipe consists of its generated YAML card and its record in recipes/predictions.json. Authoring YAML owns top-level prediction_contracts; portioning exports them losslessly. Each record declares the prediction/answer beat pair, exact answer event IDs and answer-bearing object selectors. Compilation checks the actual frame intervals and event references. These verification declarations belong beside the render card because they describe what a reviewer must inspect. The prediction-verification report separates structural timing checks from hidden/neutral-state perceptual review.


## Compatibility and failure examples

A unique string phrase remains valid. A repeated phrase must supply an occurrence. An explicit pre_roll shifts audio and captions together; it does not resolve two conflicting actions within speech. An inferred important routing, mask, fragmentation or encapsulation anchor is rejected. Changed WAV bytes reject the old alignment. Source references use one-based PDF pages; page zero is invalid. Source-link aliases must resolve uniquely. Exact regression examples are in course/tests/test_timeline.py and test_preparation.py. Template illustrative links are preserved as inert examples, outside the navigation graph.

