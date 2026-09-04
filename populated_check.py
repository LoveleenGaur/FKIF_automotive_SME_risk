"""Assert all 400 assessed cases into the ontology and check the POPULATED graph."""
import time, numpy as np
import skfuzzy as fuzz
from owlready2 import get_ontology, sync_reasoner_hermit
from fkif import FAV_UNIV, DIMS, DIM_ORDER, mf_set
from exp_extra import make_pop
import rdflib
from rdflib import RDF

SWRL = rdflib.Namespace("http://www.w3.org/2003/11/swrl#")
g = rdflib.Graph(); g.parse("fkif_ontology.owl")
def local(u): return str(u).split('#')[-1]
def rl(n):
    o=[]
    while n is not None and n != RDF.nil:
        o.append(g.value(n, RDF.first)); n=g.value(n, RDF.rest)
    return o
def at(ln):
    a=[]
    for x in rl(ln):
        if g.value(x, RDF.type) == SWRL.IndividualPropertyAtom:
            a.append((local(g.value(x, SWRL.propertyPredicate)),
                      local(g.value(x, SWRL.argument2))))
    return a
rules=[(at(g.value(i,SWRL.body)), at(g.value(i,SWRL.head))[0])
       for i in g.subjects(RDF.type, SWRL.Imp)]

def derive_all(facts):
    """Accumulate ALL derived values, so a multi-valued rule set would show up."""
    d = {k: {v} for k, v in facts.items()}
    changed=True
    while changed:
        changed=False
        for body, head in rules:
            if all(v in d.get(p, set()) for p, v in body):
                s = d.setdefault(head[0], set())
                if head[1] not in s: s.add(head[1]); changed=True
    return d

FAC = mf_set(FAV_UNIV)
def term_of(x):
    ms={t: fuzz.interp_membership(FAV_UNIV, FAC[t], x) for t in ['poor','moderate','strong']}
    return {'poor':'Poor','moderate':'Moderate','strong':'Strong'}[max(ms, key=ms.get)]
FACTOR_OF={'tech':['TechnologicalReadiness','DataQuality'],
           'org':['FinancialCapacity','WorkforceAISkills','OrganizationalCulture'],
           'sec':['Cybersecurity','RegulatoryCompliance'],
           'eco':['SupplyChainIntegration']}
FLAT=[f for d in DIM_ORDER for f in FACTOR_OF[d]]

P = make_pop(2026, 400)
multi = 0
onto = get_ontology("file://fkif_ontology.owl").load()
SME = onto.AutomotiveSME
TI = {'Poor': onto.Poor, 'Moderate': onto.Moderate, 'Strong': onto.Strong}
SUB = {n: onto[n] for n in ['LowSubRisk','MediumSubRisk','HighSubRisk']}
CLS = {n: onto[n] for n in ['LowRisk','ModerateRisk','HighRisk','CriticalRisk']}
DN = {'tech':'TechnicalCapability','org':'OrganizationalCapacity',
      'sec':'SecurityAndCompliance','eco':'EcosystemDependency'}

with onto:
    for i, v in enumerate(P):
        facts = {"has"+f+"Term": term_of(val) for f, val in zip(FLAT, v)}
        d = derive_all(facts)
        for k, s in d.items():
            if len(s) > 1: multi += 1
        ind = SME(f"SME_{i:03d}")
        for f, val in zip(FLAT, v):
            setattr(ind, "has"+f+"Value", float(val))
            setattr(ind, "has"+f+"Term", TI[term_of(val)])
        for dm in DIM_ORDER:
            setattr(ind, "has"+DN[dm]+"SubRisk",
                    SUB[list(d["has"+DN[dm]+"SubRisk"])[0]])
        ind.hasRiskClass = CLS[list(d["hasRiskClass"])[0]]

print(f"individuals asserted: 400")
print(f"properties receiving MORE THAN ONE derived value: {multi}")
t=time.time()
with onto:
    sync_reasoner_hermit(debug=0)
el=time.time()-t
print(f"HermiT on the POPULATED graph (400 cases): consistent, {el:.2f}s")
onto.save(file="fkif_supplier_graph.owl", format="rdfxml")
import os; print("saved fkif_supplier_graph.owl", os.path.getsize("fkif_supplier_graph.owl"), "bytes")
