from course.tools.release_status import calculate


def test_review_and_media_states_are_independent():
    s=calculate([{'code':'REVIEW'}],[],'r',64,64)
    assert s.automatic_media_verified and not s.release_verified
    assert calculate([],[],'r',64,64).release_verified
    assert not calculate([{'code':'STALE_RENDER'}],[],'r',63,64).release_verified
    assert not calculate([{'code':'STALE_REPRODUCTION'}],[],'r',64,64).reproduction_verified
    assert not calculate([{'code':'REVIEW'}],[],'changed',64,64).release_verified


def test_live_proof_changes_with_source_or_reviewer(tmp_path):
    from course.tools.release_status import live_proof
    (tmp_path/'course').mkdir();(tmp_path/'course/a.py').write_text('old')
    a=live_proof(tmp_path);(tmp_path/'course/a.py').write_text('new');b=live_proof(tmp_path)
    assert a!=b
    p=tmp_path/'build/review/decisions.jsonl';p.parent.mkdir(parents=True);p.write_text('revoked')
    assert live_proof(tmp_path)!=b
