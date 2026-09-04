"""Semantic-layer experiment.

(1) HermiT consistency + classification of the FKIF ontology.
(2) SWRL rules are parsed back OUT of the serialized OWL file and forward-chained,
    so the fidelity test is against the published artifact, not against Python objects.
(3) Symbolic verdicts are compared with the numeric Mamdani engine.
"""
import numpy as np, time, json
from collections import Counter
import rdflib
from rdflib import RDF
import skfuzzy as fuzz
from fkif import FKIF, FAV_UNIV, DIMS, DIM_ORDER, mf_set

RISK_ORDER = ['Low', 'Moderate', 'High', 'Critical']
SWRL = rdflib.Namespace("http://www.w3.org/2003/11/swrl#")

g = rdflib.Graph(); g.parse("fkif_ontology.owl")
def local(u): return str(u).split('#')[-1]

def read_list(node):
    out = []
    while node is not None and node != RDF.nil:
        out.append(g.value(node, RDF.first)); node = g.value(node, RDF.rest)
    return out

def read_atoms(listnode):
    atoms = []
    for a in read_list(listnode):
        t = g.value(a, RDF.type)
        if t == SWRL.ClassAtom:
            atoms.append(('class', local(g.value(a, SWRL.classPredicate))))
        elif t == SWRL.IndividualPropertyAtom:
            atoms.append(('prop', local(g.value(a, SWRL.propertyPredicate)),
                          local(g.value(a, SWRL.argument2))))
    return atoms

parsed = []
for imp in g.subjects(RDF.type, SWRL.Imp):
    parsed.append((read_atoms(g.value(imp, SWRL.body)),
                   read_atoms(g.value(imp, SWRL.head))))
print(f"SWRL rules recovered from fkif_ontology.owl: {len(parsed)}")
L1 = [x for x in parsed if x[1][0][1].endswith('SubRisk')]
L2 = [x for x in parsed if x[1][0][1] == 'hasRiskClass']
print(f"  level-1 sub-risk rules: {len(L1)}   level-2 risk-class rules: {len(L2)}")

def forward_chain(facts):
    derived = dict(facts); changed = True
    while changed:
        changed = False
        for body, head in parsed:
            if all(a[0] == 'class' or derived.get(a[1]) == a[2] for a in body):
                p, v = head[0][1], head[0][2]
                if derived.get(p) != v:
                    derived[p] = v; changed = True
    return derived

from owlready2 import get_ontology, sync_reasoner_hermit
onto = get_ontology("file://fkif_ontology.owl").load()
t0 = time.time()
with onto:
    sync_reasoner_hermit(debug=0)
hermit_t = time.time() - t0
print(f"HermiT: ontology consistent, classified in {hermit_t:.2f}s")

def make_pop(seed=2026, n=400):
    rng = np.random.default_rng(seed); P = []
    for _ in range(n):
        lat = rng.uniform(1, 10)
        v = np.clip(np.round(lat + rng.normal(0, 1, 8)), 0, 10)
        if rng.random() < 0.30:
            d = DIM_ORDER[rng.integers(0, 4)]
            red = rng.uniform(3, 5)
            for i in DIMS[d]: v[i] = np.clip(np.round(v[i] - red), 0, 10)
        P.append(v)
    return np.array(P)

FAC_MF = mf_set(FAV_UNIV)
def term_of(x):
    ms = {t: fuzz.interp_membership(FAV_UNIV, FAC_MF[t], x)
          for t in ['poor', 'moderate', 'strong']}
    return max(ms, key=ms.get)
TERM_IND = {'poor': 'Poor', 'moderate': 'Moderate', 'strong': 'Strong'}
FACTOR_OF = {'tech': ['TechnologicalReadiness', 'DataQuality'],
             'org': ['FinancialCapacity', 'WorkforceAISkills', 'OrganizationalCulture'],
             'sec': ['Cybersecurity', 'RegulatoryCompliance'],
             'eco': ['SupplyChainIntegration']}
FLAT = [f for d in DIM_ORDER for f in FACTOR_OF[d]]
NAME2CLS = {'LowRisk': 'Low', 'ModerateRisk': 'Moderate',
            'HighRisk': 'High', 'CriticalRisk': 'Critical'}

P = make_pop()
model = FKIF()
num_idx = np.array([model.index(v) for v in P])
num_cls = [model.risk_class(r) for r in num_idx]

t0 = time.time(); sym_cls = []; unresolved = 0
for v in P:
    facts = {"has" + f + "Term": TERM_IND[term_of(val)] for f, val in zip(FLAT, v)}
    rc = forward_chain(facts).get('hasRiskClass')
    if rc is None: unresolved += 1; sym_cls.append(None)
    else: sym_cls.append(NAME2CLS[rc])
sym_t = time.time() - t0

n = len(P)
ok = sum(1 for a, b in zip(sym_cls, num_cls) if a == b)
adj = sum(1 for a, b in zip(sym_cls, num_cls)
          if a and abs(RISK_ORDER.index(a) - RISK_ORDER.index(b)) <= 1)
print(f"\nunresolved (no rule fired): {unresolved}")
print(f"symbolic vs numeric exact class agreement: {ok}/{n} = {100*ok/n:.1f}%")
print(f"symbolic vs numeric within one band      : {adj}/{n} = {100*adj/n:.1f}%")
print(f"SWRL forward chaining: {1000*sym_t/n:.1f} ms/case")
dis = Counter((b, a) for a, b in zip(sym_cls, num_cls) if a != b)
print("disagreements (numeric -> symbolic):")
for (b, a), c in sorted(dis.items(), key=lambda kv: -kv[1]):
    print(f"   {b:9s} -> {str(a):9s}  {c}")
print("numeric marginals :", dict(Counter(num_cls)))
print("symbolic marginals:", dict(Counter(sym_cls)))

json.dump({"n": n, "rules_recovered": len(parsed), "L1": len(L1), "L2": len(L2),
           "exact": ok, "within_one": adj, "unresolved": unresolved,
           "hermit_seconds": round(hermit_t, 2),
           "swrl_ms_per_case": round(1000 * sym_t / n, 2),
           "numeric_marginals": dict(Counter(num_cls)),
           "symbolic_marginals": {str(k): v for k, v in Counter(sym_cls).items()},
           "disagreements": {f"{b}->{a}": c for (b, a), c in dis.items()}},
          open("semantic_results.json", "w"), indent=1)
np.save("population_2026.npy", P); np.save("numeric_index_2026.npy", num_idx)
