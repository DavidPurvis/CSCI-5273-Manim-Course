"""Compile authoritative dishes and layout overrides into recipes and narration."""
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]


def load_authoring(root:Path)->list[dict]:
    return [dish for path in sorted((root/'authoring').glob('ch*.yaml'))
            for dish in yaml.safe_load_all(path.read_text())]


def load_overrides(path:Path)->dict:
    return yaml.safe_load(path.read_text()) or {} if path.exists() else {}


def portion_dish(dish:dict,overrides:dict)->dict:
    """Pure conversion: preserve authored event metadata and merge explicit layout overrides."""
    did=str(dish['dish']);beats=[];script=[f"# Dish {did}: {dish['title']}",'']
    for authored in dish['beats']:
        bid=f"{did}.{authored['id']}";page=authored.get('pdf')
        if page is None:pdf=None
        elif isinstance(page,list) and isinstance(page[0],str):pdf=page
        else:pdf=[authored.get('deck',dish['deck'])]+(page if isinstance(page,list) else [page])
        beat={'id':bid,'stage':authored['stage'],'narration':bid,'pdf':pdf,
              'concepts':authored.get('c') or [],'clarifications':authored.get('clar') or [],
              'moves':authored.get('moves') or [],'adjust':overrides.get(bid,{})}
        for key in ('pre_roll','event_id','assertions','reading_hold','prediction','answer_objects','hold'):
            if key in authored:beat[key]=authored[key]
        beats.append(beat)
        script.extend([f'## {bid}',' '.join(authored['say'].split()),''])
    card={'dish':did,'title':dish['title'],'deck':dish['deck'],'target_min':dish['target_min'],
          'concepts':dish.get('concepts') or [],'pad':dish.get('pad',2.2),'beats':beats}
    return {'recipe':card,'narration':'\n'.join(script),'prediction_contracts':dish.get('prediction_contracts',[])}


def main():
    overrides=load_overrides(ROOT/'sources/layout-overrides.yaml')
    dishes=load_authoring(ROOT)
    prediction_contracts=[]
    for dish in dishes:
        prepared=portion_dish(dish,overrides);did=str(dish['dish'])
        prediction_contracts.extend(prepared['prediction_contracts'])
        (ROOT/'recipes'/f'{did}.yaml').write_text(yaml.safe_dump(prepared['recipe'],sort_keys=False,allow_unicode=True,width=120))
        (ROOT/'narration'/f'{did}.md').write_text(prepared['narration'])
    import json
    (ROOT/'recipes/predictions.json').write_text(json.dumps({'schema_version':1,'predictions':prediction_contracts},indent=2))
    print(f'portioned {len(dishes)} dishes')

if __name__=='__main__':main()
