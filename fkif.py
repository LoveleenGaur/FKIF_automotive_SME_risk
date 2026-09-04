"""FKIF: Fuzzy Knowledge-Inference Framework, reimplemented from the manuscript spec."""
import numpy as np, itertools
import skfuzzy as fuzz

# ---------------- Membership functions ----------------
FAV_UNIV = np.arange(0, 10.0001, 0.1)      # sub-risk / favorability universe, step 0.1
OUT_UNIV = np.arange(0, 100.0001, 1.0)     # overall risk universe, step 1.0

def mf_set(univ, shift=0.0, overlap=0.0):
    """Three-term partition on [0,10]. shift translates; overlap widens/narrows."""
    poor = fuzz.trapmf(univ, [0, 0, 2.5 + shift - overlap, 4.5 + shift + overlap])
    mod  = fuzz.trimf(univ, [3.5 + shift - overlap, 5.0 + shift, 6.5 + shift + overlap])
    strg = fuzz.trapmf(univ, [5.5 + shift - overlap, 7.5 + shift + overlap, 10, 10])
    return {'poor': poor, 'moderate': mod, 'strong': strg}

def risk_mf_set(univ, shift=0.0, overlap=0.0):
    m = mf_set(univ, shift, overlap)
    return {'low': m['poor'], 'medium': m['moderate'], 'high': m['strong']}

OUT_MF = {
    'Low':      fuzz.trapmf(OUT_UNIV, [0, 0, 18, 32]),
    'Moderate': fuzz.trimf(OUT_UNIV, [26, 42, 60]),
    'High':     fuzz.trimf(OUT_UNIV, [52, 68, 84]),
    'Critical': fuzz.trapmf(OUT_UNIV, [78, 90, 100, 100]),
}

# ---------------- Structure ----------------
FACTORS = ['tech_readiness', 'data_quality',
           'financial', 'workforce', 'culture',
           'cybersecurity', 'regulatory',
           'supply_chain']
DIMS = {'tech': [0, 1], 'org': [2, 3, 4], 'sec': [5, 6], 'eco': [7]}
DIM_ORDER = ['tech', 'org', 'sec', 'eco']

L1_TERMS = ['poor', 'moderate', 'strong']
L1_LAMBDA = {'poor': 2, 'moderate': 1, 'strong': 0}
L2_TERMS = ['low', 'medium', 'high']
L2_LAMBDA = {'low': 0, 'medium': 1, 'high': 2}
RISK_ORDER = ['Low', 'Moderate', 'High', 'Critical']

def l1_consequent(combo):
    k = len(combo)
    sigma = sum(L1_LAMBDA[c] for c in combo) / (2 * k)
    if sigma < 0.34:   return 'low', sigma
    if sigma < 0.67:   return 'medium', sigma
    return 'high', sigma

def l2_consequent(combo, w=(1.0, 1.0, 1.5, 0.7), t=(0.28, 0.58, 0.82), veto=True):
    sigma = sum(wi * L2_LAMBDA[c] for wi, c in zip(w, combo)) / (2 * sum(w))
    if   sigma < t[0]: base = 'Low'
    elif sigma < t[1]: base = 'Moderate'
    elif sigma < t[2]: base = 'High'
    else:              base = 'Critical'
    if veto:
        sec = combo[2]
        if sec == 'high':
            others_high = any(combo[i] == 'high' for i in (0, 1, 3))
            if others_high:
                base = 'Critical'
            else:
                base = max(base, 'High', key=lambda c: RISK_ORDER.index(c))
    return base, sigma

def build_rules(w=(1.0, 1.0, 1.5, 0.7), t=(0.28, 0.58, 0.82), veto=True):
    l1 = {}
    for d in DIM_ORDER:
        k = len(DIMS[d])
        l1[d] = [(combo, l1_consequent(combo)[0])
                 for combo in itertools.product(L1_TERMS, repeat=k)]
    l2 = [(combo, l2_consequent(combo, w, t, veto)[0])
          for combo in itertools.product(L2_TERMS, repeat=4)]
    return l1, l2

# ---------------- Mamdani inference ----------------
def mamdani(inputs, mfs_in, rules, out_mfs, out_univ):
    agg = np.zeros_like(out_univ)
    for combo, cons in rules:
        alpha = min(fuzz.interp_membership(FAV_UNIV, mfs_in[i][t], inputs[i])
                    for i, t in enumerate(combo))
        if alpha > 0:
            agg = np.fmax(agg, np.fmin(alpha, out_mfs[cons]))
    if agg.sum() == 0:
        return float(np.mean(out_univ))
    return float(fuzz.defuzz(out_univ, agg, 'centroid'))

class FKIF:
    def __init__(self, w=(1.0, 1.0, 1.5, 0.7), t=(0.28, 0.58, 0.82), veto=True,
                 shift=0.0, overlap=0.0, bounds=(30, 55, 80)):
        self.w, self.t, self.veto, self.bounds = w, t, veto, bounds
        self.fac_mf = mf_set(FAV_UNIV, shift, overlap)
        self.sub_mf = risk_mf_set(FAV_UNIV, shift, overlap)
        self.l1, self.l2 = build_rules(w, t, veto)

    def subrisks(self, v):
        out = []
        for d in DIM_ORDER:
            idx = DIMS[d]
            ins = [v[i] for i in idx]
            mfs = [self.fac_mf] * len(idx)
            out.append(mamdani(ins, mfs, self.l1[d], self.sub_mf, FAV_UNIV))
        return out

    def index(self, v):
        r = self.subrisks(v)
        mfs = [self.sub_mf] * 4
        return mamdani(r, mfs, self.l2, OUT_MF, OUT_UNIV)

    def risk_class(self, R):
        b = self.bounds
        if R < b[0]: return 'Low'
        if R < b[1]: return 'Moderate'
        if R < b[2]: return 'High'
        return 'Critical'

    def assess(self, v):
        R = self.index(v)
        return R, self.risk_class(R)

if __name__ == '__main__':
    m = FKIF()
    print('rules L1:', sum(len(r) for r in m.l1.values()), ' L2:', len(m.l2),
          ' total:', sum(len(r) for r in m.l1.values()) + len(m.l2))
    tests = {
        'uniformly strong (all 8)':  [8] * 8,
        'uniformly moderate (all 5)': [5] * 8,
        'uniformly poor (all 2)':     [2] * 8,
        'strong tech, weak compliance': [8, 8, 8, 8, 8, 2, 2, 8],
    }
    for name, v in tests.items():
        R, c = m.assess(v)
        print(f'{name:32s} {R:7.2f}  {c}')
    mv = FKIF(veto=False)
    R, c = mv.assess([8, 8, 8, 8, 8, 2, 2, 8])
    print(f'{"strong tech, weak comp (no veto)":32s} {R:7.2f}  {c}')
