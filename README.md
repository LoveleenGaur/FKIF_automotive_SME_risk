# FKIF — A Fuzzy Knowledge-Inference Framework for AI-Adoption Risk Assessment in Automotive SMEs

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/LoveleenGaur/FKIF_automotive_SME_risk/blob/main/FKIF_automotive_SME_risk_FINAL.ipynb)

Reproducible code for the paper *A Fuzzy Knowledge-Inference Framework for AI-Adoption Risk Assessment in Automotive SMEs*, accepted in the International Journal of Software Science and Computational Intelligence (IJSSCI).

**FKIF** is a two-stage rough-fuzzy inference framework for assessing the risk of AI adoption in automotive small and medium-sized enterprises. Eight literature-grounded, automotive-specific risk factors are represented as linguistic variables over an information system; rough-set analysis establishes the non-redundancy of the taxonomy; and a hierarchical Mamdani inference process, anchored, compliance-weighted, and **non-compensatory**, produces an interpretable overall AI-Adoption Risk Index.

The framework is also published as a **machine-readable semantic representation**: an OWL 2 ontology carrying Fuzzy OWL 2 datatype annotations and a complete SWRL encoding of all 129 inference rules, together with the populated 400-case supplier risk graph.

The framework uses **no primary human data**. It is validated through anchor calibration, monotonicity analysis, convergent validity against four reference instruments spanning the compensatory spectrum, sensitivity analysis over every design parameter, robustness to input measurement error, and a semantic-layer fidelity check.

## Repository contents

### Notebook and framework

| File | Description |
|---|---|
| `FKIF_automotive_SME_risk_FINAL.ipynb` | Original notebook: sub-systems, aggregation with compliance veto, reference instruments, convergent validity, rough-set core. Produces Tables 3 to 7. |
| `fkif.py` | Framework module: membership functions, severity schema, rule generation, Mamdani inference, compliance veto, class mapping. Imported by all scripts below. |
| `requirements.txt` | Python dependencies. A Java runtime is also required for the reasoner checks. |

### Semantic layer

| File | Description |
|---|---|
| `build_ontology.py` | Builds the OWL 2 ontology with Fuzzy OWL 2 datatype annotations and all 129 SWRL rules |
| `exp_semantic.py` | Recovers the SWRL rules from the serialized ontology, forward-chains them, and compares verdicts against the numeric engine |
| `populated_check.py` | Asserts all 400 cases with derived facts, checks the populated graph under HermiT, detects any multi-valued property |
| `fkif_ontology.owl` | Schema, term individuals with fuzzy annotations, 129 SWRL rules |
| `fkif_supplier_graph.owl` | The same ontology populated with 400 assessed suppliers and their verdicts |

### Extended analyses and verification

| File | Description |
|---|---|
| `exp_extra.py` | Product-sum composition variant, monotonicity protocol, measurement-error robustness, dimensional attribution |
| `audit.py` | Arithmetic cross-check of every rate in Tables 4, 8, 9, plus exhaustive determinism and totality check over the SWRL antecedents |
| `verify_claims.py` | Diagnostics behind three in-text claims: composition-operator correlation, measurement-error distribution shape, term-overlap explanation of symbolic divergence |
| `make_figures.py` | Generates all eight figures at 600 dpi |
| `semantic_results.json`, `extra_results.json` | Raw result records backing Tables 8, 9, 10 |

### Figures

Committed under `Figures/` as `Figure1` through `Figure8` in both PNG and TIF at 600 dpi, numbered to match the published manuscript.

| Figure | Content |
|---|---|
| 1 | Framework architecture, including the semantic layer |
| 2 | Membership functions of the risk factors and the overall risk index |
| 3 | Class marginals, FKIF against References A and B |
| 4 | Compliance sweep with and without the veto |
| 5 | Control surface of the technical-capability sub-system |
| 6 | Fidelity of the semantic representation |
| 7 | Effect of the composition operator on monotonicity |
| 8 | Dimensional attribution across the evaluation population |

Note that `make_figures.py` writes to `figs/` using descriptive names such as `fig_architecture.png`. The files under `Figures/` are those outputs renamed to the manuscript numbering above.

## How to run

### Option A — Google Colab

Click the badge above and run all cells. This covers the notebook only. The semantic scripts need a Java runtime for the HermiT reasoner and are not expected to run in a stock Colab session.

### Option B — Local

```bash
git clone https://github.com/LoveleenGaur/FKIF_automotive_SME_risk.git
cd FKIF_automotive_SME_risk
pip install -r requirements.txt
java -version    # required by owlready2 for HermiT; Java 17 or 21
```

Then the notebook for Tables 3 to 7:

```bash
jupyter notebook FKIF_automotive_SME_risk_FINAL.ipynb
```

And the scripts, in this order, for Tables 8 to 10 and the figures:

```bash
python build_ontology.py     # writes fkif_ontology.owl
python exp_semantic.py       # writes semantic_results.json
python populated_check.py    # writes fkif_supplier_graph.owl
python exp_extra.py          # writes extra_results.json and the index arrays
python audit.py              # checks only, prints results
python verify_claims.py      # diagnostics only, prints results
python make_figures.py       # writes figs/*.png
```

`make_figures.py` reads the JSON and array files written by the two experiment scripts, so it must run last.

## Reproducibility

All stochastic steps use fixed seeds, so every reported figure and statistic is deterministic and regenerable.

| Analysis | Population | Seed |
|---|---|---|
| Convergent validity and sensitivity (Tables 3 to 7) | 400 profiles | 11 |
| Monotonicity trials (Table 4) | 400 profiles | 5 and 2026 |
| Rough-set decision table | 180 cases | 3 |
| Semantic fidelity, composition, measurement error, attribution (Tables 8 to 10) | 400 profiles, fresh draw | 2026 |

The extended analyses deliberately use a separate draw from the same generative model, so their numbers neither reuse nor contradict the population behind Tables 3 to 7. Tested with Python 3.10 and above, scikit-fuzzy 0.5.0.

## Key results

- **Anchors.** Uniformly strong 12.83 (Low), uniformly moderate 42.67 (Moderate), uniformly poor 91.62 (Critical)
- **Convergent validity.** Spearman 0.838 to 0.897 against four references spanning the compensatory spectrum; quadratic-weighted Cohen's kappa 0.710 to 0.834; within-one-band agreement 85.8% to 98.0%
- **Monotonicity.** Under sup-min composition the crisp index is monotone up to a bounded residual of 1.25 index units with zero class-order violations. Under **product-sum composition the index is exactly monotone**, with zero violations across all 48,513 dominance-ordered pairs, while every anchor and 100% of class assignments are preserved
- **Rough-set core.** All eight factors, establishing formal non-redundancy of the taxonomy
- **Semantic fidelity.** 129 SWRL rules, deterministic and total by exhaustive check; schema and populated 400-case graph both consistent under HermiT; symbolic reasoning reproduces the numeric verdict exactly for 84.5% of cases and within one class for 98.2%; agreement is 100% wherever no factor lies in a term-overlap region
- **Measurement-error robustness.** Class stability 99.0%, 93.9%, and 89.5% at input noise of 0.25, 0.50, and 1.00
- **Dimensional attribution.** Security and compliance dominates at a mean index reduction of 14.78 units against 0.82 to 1.71 for the other three dimensions

## Citation

```bibtex
@article{Gaur_FKIF,
  author  = {Gaur, Loveleen},
  title   = {A Fuzzy Knowledge-Inference Framework for AI-Adoption Risk Assessment in Automotive SMEs},
  journal = {International Journal of Software Science and Computational Intelligence (IJSSCI)},
  year    = {},
  note    = {Accepted. Add volume, issue, pages, and DOI upon publication}
}
```

## Disclaimer

This repository accompanies a methodological framework paper. Case profiles are synthetically generated; the reference instruments are operationalized from published models cited in the manuscript. The framework validates methodological convergence and formal behavior, not empirical field accuracy. Primary expert elicitation and field validation are identified as future work.

## License

Released under the MIT License. See `LICENSE`.
