"""Final audit of claims that were asserted but not machine-checked."""
import itertools, re
from collections import defaultdict
import rdflib
from rdflib import RDF

print("=" * 70)
print("AUDIT 1: arithmetic in Table 9's combined-trials row")
print("=" * 70)
trials = [367, 337, 297, 48513]
PUBLISHED_COMBINED = 49514
print(f"  367 + 337 + 297 + 48,513 = {sum(trials):,}")
print(f"  Table 9 states {PUBLISHED_COMBINED:,} -> "
      f"{'OK' if sum(trials)==PUBLISHED_COMBINED else 'MISMATCH'}")

print()
print("=" * 70)
print("AUDIT 2: what does the HermiT run actually establish?")
print("=" * 70)
g = rdflib.Graph(); g.parse("fkif_ontology.owl")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")
sme = [s for s in g.subjects(RDF.type, None)
       if 'AutomotiveSME' in str(g.value(s, RDF.type) or '')]
print(f"  AutomotiveSME individuals in the serialized ontology: {len(sme)}")
print("  The schema-level HermiT run therefore checks the class hierarchy,")
print("  property declarations and rule syntax, but no SWRL rule can fire, so")
print("  it does not by itself establish that the rule set is single-valued.")
print("  Determinism and totality are established by Audit 3 below; consistency")
print("  of the POPULATED 400-case graph is established by populated_check.py.")
print("  The paper reports all three separately, which is why this is not a defect.")

print()
print("=" * 70)
print("AUDIT 3: is the SWRL rule set deterministic and total? (direct check)")
print("=" * 70)
SWRL = rdflib.Namespace("http://www.w3.org/2003/11/swrl#")
def local(u): return str(u).split('#')[-1]
def rlist(n):
    o = []
    while n is not None and n != RDF.nil:
        o.append(g.value(n, RDF.first)); n = g.value(n, RDF.rest)
    return o
def atoms(ln):
    a = []
    for x in rlist(ln):
        t = g.value(x, RDF.type)
        if t == SWRL.IndividualPropertyAtom:
            a.append((local(g.value(x, SWRL.propertyPredicate)),
                      local(g.value(x, SWRL.argument2))))
    return a
rules = [(atoms(g.value(i, SWRL.body)), atoms(g.value(i, SWRL.head))[0])
         for i in g.subjects(RDF.type, SWRL.Imp)]

index = defaultdict(list)
for body, head in rules:
    index[(head[0], tuple(sorted(body)))].append(head[1])

# determinism: no antecedent maps to two different consequents
conflicts = {k: v for k, v in index.items() if len(set(v)) > 1}
dupes = {k: v for k, v in index.items() if len(v) > 1}
print(f"  distinct antecedents: {len(index)}   total rules: {len(rules)}")
print(f"  antecedents with conflicting consequents: {len(conflicts)}")
print(f"  duplicated antecedents:                   {len(dupes)}")

# totality: every antecedent combination in the Cartesian product is covered
DIMFAC = {'TechnicalCapability': ['TechnologicalReadiness', 'DataQuality'],
          'OrganizationalCapacity': ['FinancialCapacity', 'WorkforceAISkills',
                                     'OrganizationalCulture'],
          'SecurityAndCompliance': ['Cybersecurity', 'RegulatoryCompliance'],
          'EcosystemDependency': ['SupplyChainIntegration']}
TERMS = ['Poor', 'Moderate', 'Strong']
SUBS = ['LowSubRisk', 'MediumSubRisk', 'HighSubRisk']
missing = []
for dim, facs in DIMFAC.items():
    for combo in itertools.product(TERMS, repeat=len(facs)):
        key = ("has" + dim + "SubRisk",
               tuple(sorted(("has" + f + "Term", t) for f, t in zip(facs, combo))))
        if key not in index: missing.append(key)
for combo in itertools.product(SUBS, repeat=4):
    key = ("hasRiskClass",
           tuple(sorted(("has" + d + "SubRisk", t)
                        for d, t in zip(DIMFAC, combo))))
    if key not in index: missing.append(key)
expected = 9 + 27 + 9 + 3 + 81
print(f"  expected antecedent combinations: {expected}")
print(f"  uncovered combinations:           {len(missing)}")
print(f"  => rule set is {'DETERMINISTIC and TOTAL' if not conflicts and not missing else 'DEFECTIVE'}")

print()
print("=" * 70)
print("AUDIT 4: cross-check every arithmetic claim in the manuscript tables")
print("=" * 70)
# Published values are inlined so this check is self-contained and does not
# depend on the manuscript source, which is not distributed with the code.
rows = [("Table 4 +1", 21, 600, 3.50), ("Table 4 +2", 20, 600, 3.33),
        ("Table 4 +3", 26, 600, 4.33), ("Table 4 orig", 11, 400, 2.75),
        ("Table 4 pareto", 60, 48023, 0.12),
        ("Table 9 +1", 6, 367, 1.63), ("Table 9 +2", 5, 337, 1.48),
        ("Table 9 +3", 11, 297, 3.70), ("Table 9 pareto", 39, 48513, 0.08),
        ("Table 8 exact", 338, 400, 84.5), ("Table 8 within1", 393, 400, 98.2),
        ("Table 8 overlap-free", 140, 140, 100.0),
        ("Table 8 overlapping", 198, 260, 76.2),
        ("Table 8 interior", 55, 62, 88.7)]
for name, num, den, stated in rows:
    calc = 100 * num / den
    ok = abs(calc - stated) < 0.06
    print(f"  {name:22s} {num:6d}/{den:<6d} = {calc:6.2f}%  stated {stated:6.2f}%  "
          f"{'OK' if ok else '<<< MISMATCH'}")
