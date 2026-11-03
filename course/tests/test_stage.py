"""Stage geometry checks that need no render."""
from course.stage.parts import Net, segment_hits_box


def test_segment_hits_box():
    assert segment_hits_box((0, 0), (2, 0), (1, 0), 0.5, 0.5)
    assert not segment_hits_box((0, 1), (2, 1), (1, 0), 0.5, 0.5)
    assert segment_hits_box((0, 0), (2, 2), (1, 1), 0.1, 0.1)
    assert not segment_hits_box((0, 0), (0.2, 0.2), (1, 1), 0.1, 0.1)


def test_dish_1_1_switch_label_stays_off_every_link():
    """A device with links left, right, and down must seat its label above, not on the left link."""
    nodes = {"L": {"k": "laptop", "at": [0, 0], "l": "Laptop"}, "S": {"k": "switch", "at": [2, 0], "l": "Switch"},
             "R1": {"k": "router", "at": [4.4, 0], "l": "R1"}, "R2": {"k": "router", "at": [7.4, 0], "l": "R2"},
             "W": {"k": "server", "at": [10, 0], "l": "Web server"}}
    net = Net("top", nodes, [["L", "S"], ["S", "R1"], ["R1", "R2"], ["R2", "W"]])
    net.add_device("D", {"k": "server", "at": [2, -1.1], "l": "192.0.2.53"})
    net.add_link("S", "D")
    net.clear_labels()
    for dev in net.devices.values():
        assert not net.on_link(dev.label), dev.label.text


def test_radio_geometry_matches_declared_reception():
    import numpy as np
    from course.stage.card import load_card
    from course.stage.parts import Net
    card=load_card('14.4')
    expected={
        'hidden':{'A':{'B'},'C':{'B'}},
        'exposed':{'B':{'A','C'},'C':{'B','D'}},
        'rts':{'B':{'A','C'}},
        'changed':{'A':{'E','B'},'B':{'A','C'}}}
    for key,receivers in expected.items():
        beat=next(b for b in card['beats'] if b['id']=='14.4.'+key)
        spec=next(r['net.show'] for r in beat['moves'] if 'net.show' in r)
        net=Net(spec['zone'],spec['nodes'],spec['links'],spec.get('spread'))
        for sender,wanted in receivers.items():
            pulse=next(r['radio.pulse'] for r in beat['moves'] if 'radio.pulse' in r and r['radio.pulse']['node']==sender)
            heard={n for n,device in net.devices.items() if n!=sender and np.linalg.norm(device.anchor()-net.devices[sender].anchor())<=pulse['radius']}
            assert heard==wanted,(key,sender,heard,wanted)
    rts=next(b for b in card['beats'] if b['id']=='14.4.rts')
    frames=[r['seq.msg'] for r in rts['moves'] if 'seq.msg' in r]
    assert [(f['a'],f['b']) for f in frames]==[('A','B'),('B','A'),('A','B'),('B','A')]


def test_context_strip_text_comes_from_the_lesson():
    from course.stage.context import last_sentence, lesson_question, step_name
    card = {"beats": [{"stage": "question", "moves": [{"heading": {"text": "x"}}, {"q": {"text": "Ready? Are you on the Internet yet?"}}]},
                      {"stage": "state", "moves": []}, {"stage": "rule", "moves": []}, {"stage": "state", "moves": []}]}
    assert lesson_question(card) == "Ready? Are you on the Internet yet?"
    assert last_sentence(lesson_question(card)) == "Are you on the Internet yet?"
    assert step_name("state") == "Track the state"
    assert lesson_question({"beats": [{"stage": "state", "moves": []}]}) is None


def staged_net():
    from course.stage.moves import REGISTRY, Stage
    stage = Stage(None)
    REGISTRY["net.show"]["fn"](stage, name="n", zone="top", nodes={"A": {"k": "laptop", "at": [0, 0], "l": "A"}, "B": {"k": "router", "at": [6, 0], "l": "B"}}, links=[["A", "B"]])
    return stage, REGISTRY


def test_clear_keeps_the_context_strip():
    from manim import VGroup
    stage, registry = staged_net()
    stage.objs["_context"] = VGroup()
    registry["clear"]["fn"](stage)
    assert "_context" in stage.objs and "n" not in stage.objs


def test_moved_device_and_packet_leave_a_trace_that_clear_removes():
    stage, registry = staged_net()
    registry["net.move"]["fn"](stage, name="n", node="A", to=[3, 0])
    assert ("n", "ghost", "A") in stage.marks
    registry["packet.spawn"]["fn"](stage, name="p", net="n", at="A")
    registry["packet.hop"]["fn"](stage, name="p", to="B")
    assert ("p", "trail", 0) in stage.marks
    registry["clear"]["fn"](stage)
    assert not stage.marks


def test_table_change_is_marked_only_when_it_fits():
    from course.stage.moves import REGISTRY, Stage
    stage = Stage(None)
    REGISTRY["table.show"]["fn"](stage, name="t", zone="top", cols=["Name value here", "x"], rows=[["1", "?"]])
    grid = stage.get("t")
    REGISTRY["table.set"]["fn"](stage, name="t", r=0, c=0, v="2")
    assert (0, 0) in grid.kstrikes
    REGISTRY["table.set"]["fn"](stage, name="t", r=0, c=1, v="done")
    assert (0, 1) not in grid.kstrikes


def test_spotlight_restores_exact_opacity():
    from course.stage.parts import opacity_state, scale_opacity, Grid
    grid = Grid(["a"], [["1"], ["2"]], 30)
    before = [row[1].copy() for row in opacity_state(grid)]
    state = opacity_state(grid)
    scale_opacity(state, 0.32)
    scale_opacity(state, 1.0)
    assert all((part[1] == old).all() for part, old in zip(opacity_state(grid), before))


def test_prune_keeps_what_is_inside_a_temporary_group():
    from manim import Group, VGroup, VMobject
    from course.stage.player import keep_live
    table, gone, stray = VGroup(VMobject()), VMobject(), VMobject()
    group = Group(table, gone)
    live = {id(m) for m in table.get_family()}
    assert keep_live([group, stray], live) == [table]
