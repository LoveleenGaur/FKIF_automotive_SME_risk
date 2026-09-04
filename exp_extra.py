"""Additional results: product-sum composition, measurement-error robustness,
dimensional attribution, and veto preservation in the semantic layer."""
import numpy as np, json, itertools, time
from collections import Counter
import skfuzzy as fuzz
from fkif import (FKIF, FAV_UNIV, OUT_UNIV, OUT_MF, DIMS, DIM_ORDER,
                  mf_set, risk_mf_set, build_rules)

RISK_ORDER = ['Low', 'Moderate', 'High', 'Critical']

# ---------------- product-sum variant ----------------
def mamdani_ps(inputs, mfs_in, rules, out_mfs, out_univ):
    """Product t-norm for conjunction, sum aggregation, centroid defuzzification."""
    agg = np.zeros_like(out_univ)
    for combo, cons in rules:
        alpha = 1.0
        for i, t in enumerate(combo):
            alpha *= fuzz.interp_membership(FAV_UNIV, mfs_in[i][t], inputs[i])
            if alpha == 0: break
        if alpha > 0:
            agg = agg + alpha * out_mfs[cons]
    if agg.sum() == 0: return float(np.mean(out_univ))
    return float(np.sum(out_univ * agg) / np.sum(agg))

class FKIF_PS(FKIF):
    def subrisks(self, v):
        out = []
        for d in DIM_ORDER:
            idx = DIMS[d]
            out.append(mamdani_ps([v[i] for i in idx], [self.fac_mf] * len(idx),
                                  self.l1[d], self.sub_mf, FAV_UNIV))
        return out
    def index(self, v):
        return mamdani_ps(self.subrisks(v), [self.sub_mf] * 4, self.l2, OUT_MF, OUT_UNIV)

# ---------------- population ----------------
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

P = make_pop() if __name__=="__main__" else None
res = {}


if __name__ == "__main__":
    # ================= 1. monotonicity: sup-min vs product-sum =================
    def mono_test(model, P, delta, seed):
        rng = np.random.default_rng(seed)
        viol, mx, trials = 0, 0.0, 0
        cls_viol = 0
        for v in P:
            i = rng.integers(0, 8)
            if v[i] + delta > 10: continue
            w = v.copy(); w[i] += delta
            a, b = model.index(v), model.index(w)
            trials += 1
            if b > a + 1e-9:
                viol += 1; mx = max(mx, b - a)
                if RISK_ORDER.index(model.risk_class(b)) > RISK_ORDER.index(model.risk_class(a)):
                    cls_viol += 1
        return trials, viol, mx, cls_viol

    def pareto_test(model, P, cap=None):
        idx = np.array([model.index(v) for v in P])
        n = len(P); pairs = 0; viol = 0; mx = 0.0; cviol = 0
        cls = [model.risk_class(r) for r in idx]
        for i in range(n):
            for j in range(n):
                if i == j: continue
                if np.all(P[i] >= P[j]):
                    pairs += 1
                    if idx[i] > idx[j] + 1e-9:
                        viol += 1; mx = max(mx, idx[i] - idx[j])
                        if RISK_ORDER.index(cls[i]) > RISK_ORDER.index(cls[j]): cviol += 1
        return pairs, viol, mx, cviol

    print("=== monotonicity: sup-min (baseline) vs product-sum ===")
    mono = {}
    for label, model in [("sup-min", FKIF()), ("product-sum", FKIF_PS())]:
        rows = []
        for d in (1, 2, 3):
            t, v, m, cv = mono_test(model, P, d, seed=5 + d)
            rows.append({"perturbation": f"+{d}", "trials": t, "violations": v,
                         "rate_pct": round(100 * v / t, 2), "max_magnitude": round(m, 3),
                         "class_violations": cv})
            print(f"{label:12s} +{d}: {v}/{t} = {100*v/t:5.2f}%  max {m:.3f}  class {cv}")
        p, v, m, cv = pareto_test(model, P)
        rows.append({"perturbation": "Pareto dominance", "trials": p, "violations": v,
                     "rate_pct": round(100 * v / p, 3), "max_magnitude": round(m, 3),
                     "class_violations": cv})
        print(f"{label:12s} Pareto: {v}/{p} = {100*v/p:.3f}%  max {m:.3f}  class {cv}")
        mono[label] = rows
    res["monotonicity"] = mono

    # agreement between the two composition schemes
    m_sm, m_ps = FKIF(), FKIF_PS()
    i_sm = np.array([m_sm.index(v) for v in P]); i_ps = np.array([m_ps.index(v) for v in P])
    from scipy.stats import spearmanr
    rho = spearmanr(i_sm, i_ps).statistic
    c_sm = [m_sm.risk_class(r) for r in i_sm]; c_ps = [m_ps.risk_class(r) for r in i_ps]
    agree = sum(a == b for a, b in zip(c_sm, c_ps)) / len(P)
    anchors_ps = {k: round(m_ps.index(v), 2) for k, v in
                  [("all8", [8]*8), ("all5", [5]*8), ("all2", [2]*8),
                   ("strongtech_weakcomp", [8, 8, 8, 8, 8, 2, 2, 8])]}
    print(f"\nproduct-sum vs sup-min: Spearman {rho:.4f}, class agreement {100*agree:.1f}%")
    print("product-sum anchors:", anchors_ps)
    res["product_sum_vs_supmin"] = {"spearman": round(float(rho), 4),
                                    "class_agreement_pct": round(100 * agree, 1),
                                    "anchors": anchors_ps,
                                    "ps_marginals": dict(Counter(c_ps)),
                                    "sm_marginals": dict(Counter(c_sm))}

    # ================= 2. measurement-error robustness =================
    print("\n=== measurement-error robustness (numeric engine) ===")
    rows = []
    for sigma in (0.25, 0.5, 1.0):
        rng = np.random.default_rng(77)
        stable, shifts, n = 0, [], 0
        for rep in range(5):
            for v, base_i, base_c in zip(P, i_sm, c_sm):
                w = np.clip(np.round(v + rng.normal(0, sigma, 8)), 0, 10)
                r = m_sm.index(w); n += 1
                if m_sm.risk_class(r) == base_c: stable += 1
                shifts.append(abs(r - base_i))
        rows.append({"sigma": sigma, "trials": n, "class_stability_pct": round(100 * stable / n, 1),
                     "mean_abs_index_shift": round(float(np.mean(shifts)), 2),
                     "p95_abs_index_shift": round(float(np.percentile(shifts, 95)), 2)})
        print(f"sigma={sigma}: class stability {100*stable/n:.1f}%, "
              f"mean |dR| {np.mean(shifts):.2f}, p95 {np.percentile(shifts,95):.2f}")
    res["measurement_error"] = rows

    # ================= 3. dimensional attribution =================
    print("\n=== dimensional attribution (index reduction if a dimension were made strong) ===")
    attr = {d: [] for d in DIM_ORDER}
    for v, base in zip(P, i_sm):
        for d in DIM_ORDER:
            w = v.copy()
            for i in DIMS[d]: w[i] = 10.0
            attr[d].append(base - m_sm.index(w))
    att = {d: {"mean": round(float(np.mean(a)), 2), "median": round(float(np.median(a)), 2),
               "max": round(float(np.max(a)), 2)} for d, a in attr.items()}
    for d in DIM_ORDER: print(f"{d:5s}: mean {att[d]['mean']:6.2f}  max {att[d]['max']:6.2f}")
    res["attribution"] = att

    # ================= 4. veto preservation in the symbolic layer =================
    arch = {"digitally mature niche": [9, 8, 7, 8, 8, 8, 8, 8],
            "mid-maturity tier-2":    [5, 5, 5, 5, 5, 5, 5, 5],
            "low-maturity traditional": [2, 2, 3, 2, 2, 2, 2, 3],
            "strong technical, weak compliance": [8, 8, 8, 8, 8, 2, 2, 8]}
    res["archetypes_supmin"] = {k: [round(m_sm.index(v), 2), m_sm.risk_class(m_sm.index(v))]
                                for k, v in arch.items()}
    res["archetypes_ps"] = {k: [round(m_ps.index(v), 2), m_ps.risk_class(m_ps.index(v))]
                            for k, v in arch.items()}
    print("\narchetypes (sup-min):", res["archetypes_supmin"])
    print("archetypes (product-sum):", res["archetypes_ps"])

    json.dump(res, open("extra_results.json", "w"), indent=1)
    np.save("idx_supmin.npy", i_sm); np.save("idx_ps.npy", i_ps)
    print("\nsaved extra_results.json")
