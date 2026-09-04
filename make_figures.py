"""All FKIF figures, navy/teal/amber, 600 dpi."""
import numpy as np, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import skfuzzy as fuzz
from fkif import FKIF, FAV_UNIV, mf_set, risk_mf_set, OUT_UNIV, OUT_MF
from exp_extra import FKIF_PS

NAVY, TEAL, AMBER = '#1B3A5C', '#2A9D8F', '#E9A13B'
SLATE, LIGHT, PALE = '#5A6B7D', '#C9D6E0', '#EEF3F7'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9.5,
    'axes.edgecolor': SLATE, 'axes.labelcolor': NAVY, 'axes.labelsize': 10.5,
    'axes.titlesize': 11, 'axes.titleweight': 'bold', 'axes.titlecolor': NAVY,
    'xtick.color': SLATE, 'ytick.color': SLATE, 'axes.linewidth': 0.9,
    'legend.frameon': True, 'legend.framealpha': 0.95, 'legend.edgecolor': LIGHT,
    'figure.dpi': 600, 'savefig.dpi': 600, 'savefig.bbox': 'tight',
})
os.makedirs('figs', exist_ok=True)
def save(fig, name):
    fig.savefig(f'figs/{name}.png', dpi=600, facecolor='white')
    plt.close(fig); print('  ', name)

m, mps = FKIF(), FKIF_PS()

# ---------------- FIG: architecture ----------------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    def box(x, y, w, h, text, fc, ec, tc='white', fs=8.2, weight='bold'):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.4",
                                    fc=fc, ec=ec, lw=1.1))
        ax.text(x + w/2, y + h/2, text, ha='center', va='center',
                color=tc, fontsize=fs, weight=weight, linespacing=1.4)
    def arrow(x1, y1, x2, y2, c=SLATE, ls='-'):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                     mutation_scale=10, color=c, lw=1.1, ls=ls, shrinkA=1, shrinkB=1))

    # --- Stage A band (top) ---
    ax.add_patch(FancyBboxPatch((4, 78), 92, 17, boxstyle="round,pad=0.4,rounding_size=1.4",
                                fc='white', ec=AMBER, lw=1.2, ls=(0, (5, 3))))
    ax.text(7, 91.5, "STAGE A   ROUGH-SET ATTRIBUTE REDUCTION", fontsize=8.2,
            color=AMBER, weight='bold', va='center')
    ax.text(50, 83.5, "decision table  D = (U, C ∪ {d})      →      IND(B),  POS$_B$(d),  γ$_B$(d)"
                      "      →      reduct B,  core CORE(C)",
            ha='center', va='center', fontsize=7.8, color=NAVY)

    # --- input ---
    box(2, 40, 15, 13, "Favorability\nvector\nv(x) ∈ [0,10]$^{8}$", PALE, NAVY, NAVY, 8.2)

    # --- Stage B label ---
    ax.text(21, 73, "STAGE B   HIERARCHICAL FUZZY INFERENCE", fontsize=8.2,
            color=TEAL, weight='bold', va='center')

    subs = [("$\\mathcal{F}_1$  Technical capability\n2 factors · 9 rules", 55.5, TEAL),
            ("$\\mathcal{F}_2$  Organizational capacity\n3 factors · 27 rules", 43.0, TEAL),
            ("$\\mathcal{F}_3$  Security and compliance\n2 factors · 9 rules", 30.5, NAVY),
            ("$\\mathcal{F}_4$  Ecosystem dependency\n1 factor · 3 rules", 18.0, TEAL)]
    for t, y, c in subs:
        box(21, y, 30, 10, t, c, c, 'white', 7.6)
        arrow(17, 46.5, 21, y + 5)
        arrow(51, y + 5, 60, 41)

    box(60, 32, 20, 18, "$\\mathcal{G}$   Level-2\naggregation\n81 rules\nw = (1, 1, 1.5, 0.7)\ncompliance veto",
        NAVY, NAVY, 'white', 7.8)
    arrow(80, 41, 83, 41)
    box(83, 33, 16.5, 16, "R(x) ∈ [0,100]\n\nρ(R) ∈ {Low,\nModerate,\nHigh, Critical}", PALE, NAVY, NAVY, 7.0)

    # --- semantic layer band (bottom) ---
    ax.add_patch(FancyBboxPatch((4, 1), 92, 12, boxstyle="round,pad=0.4,rounding_size=1.4",
                                fc=PALE, ec=AMBER, lw=1.2))
    ax.text(7, 10, "SEMANTIC LAYER", fontsize=8.2, color=AMBER, weight='bold', va='center')
    ax.text(50, 4.8, "OWL 2 ontology  ·  Fuzzy OWL 2 datatype annotations  ·  129 SWRL rules  ·"
                     "  SPARQL-queryable supplier risk graph",
            ha='center', va='center', fontsize=7.4, color=NAVY)
    arrow(36, 18, 36, 13.5, AMBER)
    arrow(70, 32, 70, 13.5, AMBER)
    ax.text(38, 15.5, "rule base export", fontsize=7, color=SLATE, va='center')
    ax.text(72, 22, "assessed cases", fontsize=7, color=SLATE, va='center')
    save(fig, 'fig_architecture')

# ---------------- FIG: membership functions ----------------
def fig_membership():
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.7))
    mf = mf_set(FAV_UNIV)
    for (name, y), c, ls in zip(mf.items(), [NAVY, TEAL, AMBER], ['-', '--', '-.']):
        axes[0].plot(FAV_UNIV, y, color=c, lw=2, ls=ls, label=name)
        axes[0].fill_between(FAV_UNIV, y, alpha=0.10, color=c)
    axes[0].set_xlabel('Favorability'); axes[0].set_ylabel('Membership degree')
    axes[0].set_title('(a) Risk-factor and sub-risk terms')
    axes[0].legend(fontsize=8, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.02))
    axes[0].set_xlim(0, 10); axes[0].set_ylim(0, 1.12)
    for (name, y), c, ls in zip(OUT_MF.items(), [TEAL, '#7FB3A8', AMBER, NAVY],
                                ['-', '--', '-.', ':']):
        axes[1].plot(OUT_UNIV, y, color=c, lw=2, ls=ls, label=name)
        axes[1].fill_between(OUT_UNIV, y, alpha=0.10, color=c)
    axes[1].set_xlabel('Overall AI-adoption risk index'); axes[1].set_ylabel('Membership degree')
    axes[1].set_title('(b) Overall risk terms')
    axes[1].legend(fontsize=7.5, ncol=2, loc='lower center')
    axes[1].set_xlim(0, 100); axes[1].set_ylim(0, 1.12)
    for a in axes: a.grid(alpha=0.22, ls=':', color=LIGHT)
    fig.tight_layout(); save(fig, 'fig_membership')

# ---------------- FIG: compliance sweep ----------------
def fig_sweep():
    xs = np.arange(0, 10.01, 0.1)
    base = [8.] * 8
    y_v, y_nv = [], []
    mnv = FKIF(veto=False)
    for x in xs:
        v = list(base); v[5] = v[6] = x
        y_v.append(m.index(v)); y_nv.append(mnv.index(v))
    y_v, y_nv = np.array(y_v), np.array(y_nv)
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    for b, lab in [(30, 'Low / Moderate'), (55, 'Moderate / High'), (80, 'High / Critical')]:
        ax.axhline(b, color=LIGHT, ls=':', lw=1.1, zorder=0)
        ax.text(0.15, b + 1.4, lab, fontsize=7.2, color=SLATE, ha='left')
    ax.plot(xs, y_nv, color=AMBER, lw=2.4, ls='--', label='Compensatory variant (veto disabled)')
    ax.plot(xs, y_v, color=NAVY, lw=2.6, label='FKIF (compliance veto active)')
    ax.fill_between(xs, y_nv, y_v, where=(y_v > y_nv), color=TEAL, alpha=0.16,
                    label='Escalation attributable to the veto')
    ax.axvline(4.4, color=TEAL, ls='-.', lw=1.2)
    ax.annotate('escalation released\nat favorability 4.4', xy=(4.4, 78), xytext=(5.4, 84),
                fontsize=8, color=NAVY, arrowprops=dict(arrowstyle='->', color=SLATE, lw=1))
    ax.annotate('', xy=(2.6, 68.0), xytext=(2.6, 42.7),
                arrowprops=dict(arrowstyle='<->', color=NAVY, lw=1.3))
    ax.text(2.85, 55, '25.3 index units', fontsize=8.6, color=NAVY, weight='bold', va='center')
    ax.annotate('bounded residual\nnon-monotonicity (≤1.25)', xy=(5.85, 15.8), xytext=(6.1, 4),
                fontsize=7.6, color=SLATE,
                arrowprops=dict(arrowstyle='->', color=SLATE, lw=0.9))
    ax.set_xlabel('Compliance favorability (cybersecurity and regulatory readiness)')
    ax.set_ylabel('Overall AI-adoption risk index')
    ax.set_xlim(0, 10); ax.set_ylim(0, 100); ax.set_xticks(range(11))
    ax.legend(fontsize=7.8, loc='upper right', bbox_to_anchor=(0.995, 0.52))
    ax.grid(alpha=0.18, ls=':', color=LIGHT)
    fig.tight_layout(); save(fig, 'fig_sweep')

# ---------------- FIG: control surface ----------------
def fig_surface():
    g = np.arange(0, 10.01, 0.4)
    Z = np.zeros((len(g), len(g)))
    for i, a in enumerate(g):
        for j, b in enumerate(g):
            Z[i, j] = m.subrisks([a, b, 5, 5, 5, 5, 5, 5])[0]
    X, Y = np.meshgrid(g, g)
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list('fkif', [TEAL, '#EAD9A8', AMBER, NAVY])
    cf = ax.contourf(X, Y, Z.T, levels=14, cmap=cmap, alpha=0.92)
    cs = ax.contour(X, Y, Z.T, levels=8, colors='white', linewidths=0.7)
    ax.clabel(cs, inline=True, fontsize=7, fmt='%.1f')
    cb = fig.colorbar(cf, ax=ax, pad=0.02); cb.set_label('Technical sub-risk', color=NAVY, fontsize=9.5)
    cb.outline.set_edgecolor(SLATE)
    ax.set_xlabel('Technological readiness'); ax.set_ylabel('Data quality')
    fig.tight_layout(); save(fig, 'fig_surface')

# ---------------- FIG: class marginals (published N=400 figures) ----------------
def fig_marginals():
    labels = ['Low', 'Moderate', 'High', 'Critical']
    fkif_c = [183, 17, 30, 170]; refA = [93, 110, 127, 70]; refB = [142, 106, 85, 67]
    x = np.arange(4); w = 0.27
    fig, ax = plt.subplots(figsize=(6.4, 3.5))
    for off, d, c, lab in [(-w, fkif_c, NAVY, 'FKIF'), (0, refA, TEAL, 'Ref. A (Schumacher)'),
                           (w, refB, AMBER, 'Ref. B (TOE composite)')]:
        bars = ax.bar(x + off, d, w, color=c, edgecolor='white', lw=0.8, label=lab)
        ax.bar_label(bars, fontsize=7.6, color=SLATE, padding=2)
    ax.text(1.5, 196, 'FKIF populates the Moderate class an order of magnitude\n'
            'less densely than either compensatory reference',
            fontsize=7.8, color=NAVY, ha='center', va='top', linespacing=1.4)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel('Profiles assigned (N = 400)'); ax.set_xlabel('Assigned risk class')
    ax.legend(fontsize=8.2, loc='upper center', ncol=3, bbox_to_anchor=(0.5,1.0)); ax.grid(axis='y', alpha=0.2, ls=':', color=LIGHT); ax.set_axisbelow(True)
    ax.set_ylim(0, 240)
    fig.tight_layout(); save(fig, 'fig_marginals')

# ---------------- FIG: product-sum ablation ----------------
def fig_productsum():
    r = json.load(open('extra_results.json'))
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))
    labs = ['+1', '+2', '+3', 'Pareto\ndominance']
    sm = [d['rate_pct'] for d in r['monotonicity']['sup-min']]
    ps = [d['rate_pct'] for d in r['monotonicity']['product-sum']]
    x = np.arange(4); w = 0.35
    b1 = axes[0].bar(x - w/2, sm, w, color=AMBER, edgecolor='white', label='sup-min (baseline)')
    b2 = axes[0].bar(x + w/2, ps, w, color=TEAL, edgecolor='white', label='product-sum')
    axes[0].bar_label(b1, fmt='%.2f%%', fontsize=7.4, color=SLATE, padding=2)
    axes[0].bar_label(b2, fmt='%.0f', fontsize=7.4, color=SLATE, padding=2)
    axes[0].set_xticks(x); axes[0].set_xticklabels(labs, fontsize=8.5)
    axes[0].set_ylabel('Index-order violation rate (%)')
    axes[0].set_title('(a) Monotonicity by composition')
    axes[0].legend(fontsize=8); axes[0].grid(axis='y', alpha=0.2, ls=':', color=LIGHT)
    axes[0].set_axisbelow(True); axes[0].set_ylim(0, 4.6)

    xs = np.arange(4.6, 8.01, 0.05)
    base = [8.] * 8
    y_sm, y_ps = [], []
    for x in xs:
        v = list(base); v[5] = v[6] = x
        y_sm.append(m.index(v)); y_ps.append(mps.index(v))
    axes[1].plot(xs, y_sm, color=AMBER, lw=2.2, label='sup-min')
    axes[1].plot(xs, y_ps, color=TEAL, lw=2.2, ls='--', label='product-sum')
    axes[1].annotate('residual bump\neliminated', xy=(5.85, 15.4), xytext=(6.45, 14.4),
                     fontsize=7.8, color=NAVY,
                     arrowprops=dict(arrowstyle='->', color=SLATE, lw=0.9))
    axes[1].set_xlabel('Compliance favorability'); axes[1].set_ylabel('Risk index')
    axes[1].set_title('(b) Sweep detail')
    axes[1].legend(fontsize=8); axes[1].grid(alpha=0.2, ls=':', color=LIGHT)
    fig.tight_layout(); save(fig, 'fig_productsum')

# ---------------- FIG: semantic layer ----------------
def fig_semantic():
    r = json.load(open('semantic_results.json'))
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.4))
    order = ['Low', 'Moderate', 'High', 'Critical']
    num = [r['numeric_marginals'].get(k, 0) for k in order]
    sym = [r['symbolic_marginals'].get(k, 0) for k in order]
    x = np.arange(4); w = 0.36
    b1 = axes[0].bar(x - w/2, num, w, color=NAVY, edgecolor='white',
                     label='Numeric Mamdani engine')
    b2 = axes[0].bar(x + w/2, sym, w, color=TEAL, edgecolor='white',
                     label='OWL 2 + SWRL reasoning')
    axes[0].bar_label(b1, fontsize=7.4, color=SLATE, padding=2)
    axes[0].bar_label(b2, fontsize=7.4, color=SLATE, padding=2)
    axes[0].set_xticks(x); axes[0].set_xticklabels(order, fontsize=8.5)
    axes[0].set_ylabel('Profiles assigned (N = 400)')
    axes[0].set_title('(a) Numeric vs symbolic class marginals')
    axes[0].legend(fontsize=7.8); axes[0].grid(axis='y', alpha=0.2, ls=':', color=LIGHT)
    axes[0].set_axisbelow(True); axes[0].set_ylim(0, 215)

    vals = [100 * r['exact'] / r['n'], 100 * r['within_one'] / r['n'], 100.0, 100.0]
    names = ['Exact class\nagreement', 'Within one\nband', 'SWRL rules\nrecovered', 'Rule-base\ncoverage']
    bars = axes[1].barh(names[::-1], vals[::-1], color=[TEAL, TEAL, AMBER, NAVY][::-1],
                        edgecolor='white', height=0.6)
    axes[1].bar_label(bars, fmt='%.1f%%', fontsize=8.2, color=SLATE, padding=3)
    axes[1].set_xlim(0, 118); axes[1].set_xlabel('Percent')
    axes[1].set_title('(b) Semantic-layer fidelity')
    axes[1].grid(axis='x', alpha=0.2, ls=':', color=LIGHT); axes[1].set_axisbelow(True)
    axes[1].tick_params(labelsize=8.2)
    fig.tight_layout(); save(fig, 'fig_semantic')

# ---------------- FIG: attribution ----------------
def fig_attribution():
    r = json.load(open('extra_results.json'))['attribution']
    names = {'tech': 'Technical\ncapability', 'org': 'Organizational\ncapacity',
             'sec': 'Security and\ncompliance', 'eco': 'Ecosystem\ndependency'}
    ks = ['sec', 'tech', 'eco', 'org']
    means = [r[k]['mean'] for k in ks]; maxs = [r[k]['max'] for k in ks]
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    y = np.arange(4)
    ax.barh(y, maxs, 0.55, color=PALE, edgecolor=LIGHT, label='maximum')
    bars = ax.barh(y, means, 0.55, color=[NAVY, TEAL, AMBER, SLATE], edgecolor='white', label='mean')
    ax.bar_label(bars, fmt='%.2f', fontsize=8, color=SLATE, padding=3)
    ax.set_yticks(y); ax.set_yticklabels([names[k] for k in ks], fontsize=8.6)
    ax.set_xlabel('Reduction in risk index if the dimension were made fully favorable')
    ax.legend(fontsize=8, loc='lower right'); ax.grid(axis='x', alpha=0.2, ls=':', color=LIGHT)
    ax.set_axisbelow(True); ax.invert_yaxis()
    fig.tight_layout(); save(fig, 'fig_attribution')

print('generating figures:')
fig_architecture(); fig_membership(); fig_sweep(); fig_surface()
fig_marginals(); fig_productsum(); fig_semantic(); fig_attribution()
