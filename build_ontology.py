"""Build the FKIF OWL 2 ontology: Fuzzy OWL 2 datatypes + SWRL encoding of all 129 rules."""
import itertools, os
from owlready2 import *
from fkif import DIMS, DIM_ORDER, L1_TERMS, L2_TERMS, l1_consequent, l2_consequent

# Ontology IRI. This must be a namespace the authors control and that ideally
# resolves. fkif.org is NOT owned by the authors, so the repository URL is used.
# Replace with a w3id.org or PURL entry if a persistent identifier is registered.
IRI = "https://github.com/LoveleenGaur/FKIF_automotive_SME_risk/fkif.owl"
onto = get_ontology(IRI)

FACTOR_OF = {'tech': ['TechnologicalReadiness', 'DataQuality'],
             'org':  ['FinancialCapacity', 'WorkforceAISkills', 'OrganizationalCulture'],
             'sec':  ['Cybersecurity', 'RegulatoryCompliance'],
             'eco':  ['SupplyChainIntegration']}
DIM_NAME = {'tech': 'TechnicalCapability', 'org': 'OrganizationalCapacity',
            'sec': 'SecurityAndCompliance', 'eco': 'EcosystemDependency'}

# Fuzzy OWL 2 datatype annotations (Bobillo & Straccia, 2011 XML syntax)
FUZZY_DT = {
 'PoorDegree':     '<fuzzyOwl2 fuzzyType="datatype"><Datatype type="leftshoulder" a="0" b="0" c="2.5" d="4.5"/></fuzzyOwl2>',
 'ModerateDegree': '<fuzzyOwl2 fuzzyType="datatype"><Datatype type="triangular" a="3.5" b="5.0" c="6.5"/></fuzzyOwl2>',
 'StrongDegree':   '<fuzzyOwl2 fuzzyType="datatype"><Datatype type="rightshoulder" a="5.5" b="7.5" c="10" d="10"/></fuzzyOwl2>',
 'LowRiskDegree':      '<fuzzyOwl2 fuzzyType="datatype"><Datatype type="leftshoulder" a="0" b="0" c="18" d="32"/></fuzzyOwl2>',
 'ModerateRiskDegree': '<fuzzyOwl2 fuzzyType="datatype"><Datatype type="triangular" a="26" b="42" c="60"/></fuzzyOwl2>',
 'HighRiskDegree':     '<fuzzyOwl2 fuzzyType="datatype"><Datatype type="triangular" a="52" b="68" c="84"/></fuzzyOwl2>',
 'CriticalRiskDegree': '<fuzzyOwl2 fuzzyType="datatype"><Datatype type="rightshoulder" a="78" b="90" c="100" d="100"/></fuzzyOwl2>',
}

with onto:
    class AutomotiveSME(Thing): pass
    class RiskFactor(Thing): pass
    class RiskDimension(Thing): pass
    class LinguisticTerm(Thing): pass
    class FavourabilityTerm(LinguisticTerm): pass
    class SubRiskTerm(LinguisticTerm): pass
    class RiskClass(Thing): pass

    class fuzzyLabel(AnnotationProperty): pass

    # favourability terms
    Poor, Moderate, Strong = (FavourabilityTerm(n) for n in ['Poor', 'Moderate', 'Strong'])
    LowR, MediumR, HighR = (SubRiskTerm(n) for n in ['LowSubRisk', 'MediumSubRisk', 'HighSubRisk'])
    LowC, ModC, HighC, CritC = (RiskClass(n) for n in ['LowRisk', 'ModerateRisk', 'HighRisk', 'CriticalRisk'])

    for d in DIM_ORDER:
        RiskDimension(DIM_NAME[d])
        for f in FACTOR_OF[d]:
            RiskFactor(f)

    # data properties: favourability value per factor
    fav_props, term_props = {}, {}
    for d in DIM_ORDER:
        for f in FACTOR_OF[d]:
            dp = types.new_class("has" + f + "Value", (DataProperty, FunctionalProperty,))
            dp.domain, dp.range = [AutomotiveSME], [float]
            fav_props[f] = dp
            op = types.new_class("has" + f + "Term", (ObjectProperty, FunctionalProperty,))
            op.domain, op.range = [AutomotiveSME], [FavourabilityTerm]
            term_props[f] = op

    sub_props = {}
    for d in DIM_ORDER:
        op = types.new_class("has" + DIM_NAME[d] + "SubRisk", (ObjectProperty, FunctionalProperty,))
        op.domain, op.range = [AutomotiveSME], [SubRiskTerm]
        sub_props[d] = op

    class hasRiskClass(ObjectProperty, FunctionalProperty):
        domain, range = [AutomotiveSME], [RiskClass]
    class hasRiskIndex(DataProperty, FunctionalProperty):
        domain, range = [AutomotiveSME], [float]

# Fuzzy OWL 2 annotations on the term individuals
for ind, key in [(Poor, 'PoorDegree'), (Moderate, 'ModerateDegree'), (Strong, 'StrongDegree'),
                 (LowC, 'LowRiskDegree'), (ModC, 'ModerateRiskDegree'),
                 (HighC, 'HighRiskDegree'), (CritC, 'CriticalRiskDegree')]:
    ind.fuzzyLabel = [FUZZY_DT[key]]

TERM_IND = {'poor': 'Poor', 'moderate': 'Moderate', 'strong': 'Strong'}
SUB_IND  = {'low': 'LowSubRisk', 'medium': 'MediumSubRisk', 'high': 'HighSubRisk'}
CLS_IND  = {'Low': 'LowRisk', 'Moderate': 'ModerateRisk', 'High': 'HighRisk', 'Critical': 'CriticalRisk'}

rules = []
with onto:
    # ---- Level 1: 48 rules ----
    for d in DIM_ORDER:
        facs = FACTOR_OF[d]
        for combo in itertools.product(L1_TERMS, repeat=len(facs)):
            cons = l1_consequent(combo)[0]
            ante = ["AutomotiveSME(?x)"] + [
                f"has{f}Term(?x, {TERM_IND[t]})" for f, t in zip(facs, combo)]
            r = Imp(); r.set_as_rule(", ".join(ante) +
                f" -> has{DIM_NAME[d]}SubRisk(?x, {SUB_IND[cons]})")
            rules.append(r)
    # ---- Level 2: 81 rules ----
    for combo in itertools.product(L2_TERMS, repeat=4):
        cons = l2_consequent(combo)[0]
        ante = ["AutomotiveSME(?x)"] + [
            f"has{DIM_NAME[d]}SubRisk(?x, {SUB_IND[t]})" for d, t in zip(DIM_ORDER, combo)]
        r = Imp(); r.set_as_rule(", ".join(ante) + f" -> hasRiskClass(?x, {CLS_IND[cons]})")
        rules.append(r)

print("classes:", len(list(onto.classes())))
print("object properties:", len(list(onto.object_properties())))
print("data properties:", len(list(onto.data_properties())))
print("individuals:", len(list(onto.individuals())))
print("SWRL rules:", len(rules))
onto.save(file="fkif_ontology.owl", format="rdfxml")
print("saved fkif_ontology.owl", os.path.getsize("fkif_ontology.owl"), "bytes")
