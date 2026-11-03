"""Fixed reviewed example adapters; source text cannot name arbitrary imports."""
import json
from pathlib import Path
from course.model import ipv4,routing,convergence,bgp,ethernet,wireless,multicast

ADAPTERS={
 'prefix':lambda i:ipv4.decode(i['address'],i['prefix']),
 'fragments':lambda i:ipv4.fragment(i['total'],i['header'],i['mtu']),
 'shortest':lambda i:routing.dijkstra(routing.SLIDE_26,'t')['paths']['v'],
 'stable':lambda i:convergence.trace()['slide30_solutions'],
 'valleys':lambda i:[bgp.valley_free(p)[1] for p in bgp.SLIDE_PATHS],
 'stp':lambda i:ethernet.stp(ethernet.STP_SWITCHES,ethernet.STP_EDGES)['active'],
 'cdma':lambda i:wireless.cdma_sum([(i['bits'][0],wireless.C1),(i['bits'][1],wireless.C2)])}


def load_example_specs(catalog=None):
 p=Path(__file__).resolve().parents[2]/'sources/example-specs.json'
 return json.loads(p.read_text())


def run_example(spec):
 if spec['adapter'] not in ADAPTERS:raise ValueError('unknown example adapter')
 return ADAPTERS[spec['adapter']](spec['inputs'])


def verify_example(spec,trace):
 # Expected literals are curated separately from adapters, with source references.
 got=json.loads(json.dumps(trace));return dict(example_id=spec['example_id'],passed=got==spec['expected'],expected=spec['expected'],actual=got)
