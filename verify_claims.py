"""Verify three claims asserted in the revised manuscript."""
import numpy as np, json
from collections import Counter
from scipy.stats import spearmanr
import skfuzzy as fuzz
from fkif import FKIF, FAV_UNIV, DIMS, DIM_ORDER, mf_set, risk_mf_set
from exp_extra import FKIF_PS, make_pop

P = make_pop(2026, 400)
m, mps = FKIF(), FKIF_PS()
i_sm = np.load('idx_supmin.npy'); i_ps = np.load('idx_ps.npy')

print("=" * 68)
print("CHECK 1: what accounts for the sup-min / product-sum rank correlation")
print("=" * 68)
u_sm, u_ps = np.unique(i_sm), np.unique(i_ps)
print(f"distinct index values: sup-min {len(u_sm)}, product-sum {len(u_ps)} (of 400)")
top = Counter(np.round(i_sm, 3)).most_common(5)
print("most common sup-min index values:", top)
print(f"share of population on the 3 largest plateaus: "
      f"{sum(c for _, c in top[:3]) / 400:.1%}")
# Does the pair ORDER ever genuinely disagree beyond ties?
disc = 0; tie_sm = 0
n = len(i_sm)
for a in range(n):
    for b in range(a + 1, n):
        d1, d2 = i_sm[a] - i_sm[b], i_ps[a] - i_ps[b]
        if abs(d1) < 1e-9:
            tie_sm += 1
        elif d1 * d2 < 0:
            disc += 1
tot = n * (n - 1) // 2
print(f"pairs tied under sup-min : {tie_sm}/{tot} = {100*tie_sm/tot:.1f}%")
print(f"pairs with GENUINELY REVERSED order: {disc}/{tot} = {100*disc/tot:.3f}%")
rho_all = spearmanr(i_sm, i_ps).statistic
mask = np.array([abs(i_sm[k] - np.median(i_sm)) >= 0 for k in range(n)])
print(f"Spearman (all)      : {rho_all:.4f}")
print(f"Pearson (all)       : {np.corrcoef(i_sm, i_ps)[0,1]:.4f}")
print(f"max |difference|    : {np.max(np.abs(i_sm - i_ps)):.3f} index units")
print(f"mean |difference|   : {np.mean(np.abs(i_sm - i_ps)):.3f}")

print()
print("=" * 68)
print("CHECK 2: shape of the measurement-error shift distribution")
print("=" * 68)
c_sm = [m.risk_class(r) for r in i_sm]
for sigma in (0.25, 0.5, 1.0):
    rng = np.random.default_rng(77)
    shifts, stable, tot_t = [], 0, 0
    for rep in range(5):
        for v, base_i, base_c in zip(P, i_sm, c_sm):
            w = np.clip(np.round(v + rng.normal(0, sigma, 8)), 0, 10)
            r = m.index(w); tot_t += 1
            if m.risk_class(r) == base_c: stable += 1
            shifts.append(abs(r - base_i))
    s = np.array(shifts)
    print(f"sigma={sigma}: stability {100*stable/tot_t:5.1f}%  "
          f"unchanged index {100*np.mean(s < 1e-9):5.1f}%  "
          f"median {np.median(s):.2f}  p90 {np.percentile(s,90):6.2f}  "
          f"p99 {np.percentile(s,99):6.2f}  max {s.max():6.2f}")

print()
print("=" * 68)
print("CHECK 3: is symbolic/numeric divergence confined to term-overlap regions?")
print("=" * 68)
FAC_MF = mf_set(FAV_UNIV)
def memberships(x):
    return {t: fuzz.interp_membership(FAV_UNIV, FAC_MF[t], x)
            for t in ['poor', 'moderate', 'strong']}
def n_active(x):
    return sum(1 for v in memberships(x).values() if v > 1e-9)

# recompute symbolic classes
import rdflib
from rdflib import RDF
SWRL = rdflib.Namespace("http://www.w3.org/2003/11/swrl#")
g = rdflib.Graph(); g.parse("fkif_ontology.owl")
def local(u): return str(u).split('#')[-1]
def read_list(node):
    out = []
    while node is not None and node != RDF.nil:
        out.append(g.value(node, RDF.first)); node = g.value(node, RDF.rest)
    return out
def read_atoms(ln):
    at = []
    for a in read_list(ln):
        t = g.value(a, RDF.type)
        if t == SWRL.ClassAtom: at.append(('class', local(g.value(a, SWRL.classPredicate))))
        elif t == SWRL.IndividualPropertyAtom:
            at.append(('prop', local(g.value(a, SWRL.propertyPredicate)),
                       local(g.value(a, SWRL.argument2))))
    return at
parsed = [(read_atoms(g.value(i, SWRL.body)), read_atoms(g.value(i, SWRL.head)))
          for i in g.subjects(RDF.type, SWRL.Imp)]
def fchain(facts):
    d = dict(facts); ch = True
    while ch:
        ch = False
        for b, h in parsed:
            if all(a[0] == 'class' or d.get(a[1]) == a[2] for a in b):
                p, val = h[0][1], h[0][2]
                if d.get(p) != val: d[p] = val; ch = True
    return d
FACTOR_OF = {'tech': ['TechnologicalReadiness', 'DataQuality'],
             'org': ['FinancialCapacity', 'WorkforceAISkills', 'OrganizationalCulture'],
             'sec': ['Cybersecurity', 'RegulatoryCompliance'],
             'eco': ['SupplyChainIntegration']}
FLAT = [f for d in DIM_ORDER for f in FACTOR_OF[d]]
TI = {'poor': 'Poor', 'moderate': 'Moderate', 'strong': 'Strong'}
N2C = {'LowRisk': 'Low', 'ModerateRisk': 'Moderate', 'HighRisk': 'High', 'CriticalRisk': 'Critical'}
def term_of(x):
    ms = memberships(x); return max(ms, key=ms.get)

sym = []
for v in P:
    facts = {"has" + f + "Term": TI[term_of(val)] for f, val in zip(FLAT, v)}
    sym.append(N2C[fchain(facts)['hasRiskClass']])

overlap_counts = np.array([sum(n_active(x) > 1 for x in v) for v in P])
agree = np.array([a == b for a, b in zip(sym, c_sm)])
print(f"mean # factors in a term-overlap region:")
print(f"   agreeing cases   : {overlap_counts[agree].mean():.2f}")
print(f"   disagreeing cases: {overlap_counts[~agree].mean():.2f}")
print(f"cases with ZERO factors in an overlap region: "
      f"{(overlap_counts==0).sum()}, of which agree: {agree[overlap_counts==0].sum()}"
      f" ({100*agree[overlap_counts==0].mean():.1f}%)")
print(f"cases with >=1 factor in an overlap region : "
      f"{(overlap_counts>0).sum()}, of which agree: {agree[overlap_counts>0].sum()}"
      f" ({100*agree[overlap_counts>0].mean():.1f}%)")
