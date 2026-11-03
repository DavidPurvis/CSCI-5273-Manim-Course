import json
from course.tools import reference_integrity as r


def test_reordering_or_inserting_a_referenced_event_fails(tmp_path,monkeypatch):
    (tmp_path/'sources').mkdir();(tmp_path/'sources/event-reference-baseline.json').write_text(json.dumps({'events':{'a:move:0':'packet'}}))
    monkeypatch.setattr(r,'collect',lambda root:{'a:move:0':'unrelated'})
    assert r.validate_reference_integrity(tmp_path)
    monkeypatch.setattr(r,'collect',lambda root:{'a:move:0':'packet'})
    assert not r.validate_reference_integrity(tmp_path)
