"""Frame-exact membership for chapters, the main course, and independent supplements."""
from dataclasses import asdict
from course.catalog import is_main
import json
from course.stage.card import ROOT,load_card,load_manifest,load_timing,narration_text
from course.stage.timeline import compile_dish,build_assembly_plan


def course_plans():
    from course.stage.moves import REGISTRY
    from course.tools.kitchen import dishes
    manifest,timing,texts=load_manifest(),load_timing(),narration_text()
    defaults={k:v['t'] for k,v in REGISTRY.items()}
    members=[compile_dish(load_card(d),manifest,timing,texts,defaults) for d in dishes()]
    plans={name:build_assembly_plan([d for d in members if is_main(d.dish_id)==main],name)
           for name,main in [('main',True),('supplements',False)]}
    for ch in sorted({d.dish_id.split('.')[0] for d in members},key=int):
        plans['chapter-'+ch]=build_assembly_plan([d for d in members if d.dish_id.split('.')[0]==ch],'chapter-'+ch)
    return plans


def write_plans(destination=None):
    destination=destination or ROOT/'build/assembly'
    destination.mkdir(parents=True,exist_ok=True)
    plans=course_plans()
    for name,plan in plans.items():
        (destination/(name+'.json')).write_text(json.dumps(asdict(plan),indent=2))
    return plans
