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
