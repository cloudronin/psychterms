"""Deterministic scope and field assignment before paid drafting."""
import json,re
from core import ROOT,digest

VERSION=4
ROOTS={
 'diagnosis':['F03'],
 'biological':['A08','C10','G11.561','D27.505.954.427.700'],
 'development':['I02'],
 'ethics':['K01.752.566.479','N05.350'],
 'research methods':['E05.581.500','H01.770.644.728','E05.318.740','H01.548.832','N05.715.360.750','N06.850.520.830'],
}
PATTERNS=[
 ('ethics',r'\bethic|confidential|informed consent|duty to (?:warn|protect)|mandated report|professional boundar'),
 ('assessment',r'psychometr|psychological test|psychological assess|intelligence (?:scale|test)|risk assessment|personality (?:test|inventory)|neuropsychological test'),
 ('diagnosis',r'mental disorder|psychiatric disorder|personality disorder|schizophren|psychosis|autism|attention deficit|substance use disorder'),
 ('counselling skills',r'counsel|psychotherap|cognitive behavio.{0,5} therap|client.cent|therapeutic alliance'),
 ('development',r'child development|developmental psycholog|language acquisition|infant attachment|educational|\bacademic\b|\bacademia\b|\bscholastic\b|academic achievement|school performance'),
 ('learning',r'\blearning\b|conditioned (?:response|stimulus)|classical conditioning|operant|reinforcement|\bhabit\b|behavio(?:u)?r'),
 ('social',r'\bsocial\b|interpersonal|prejudice|stereotyp|group dynamics|gender identity'),
 ('cognition',r'\bacalculia\b|cognit|attention|\bmemory\b|percept|conscious|\bmental\b|\bthought\b|reasoning|judgment|emotion|affective|intelligence|creativity'),
 ('biological',r'\bneur|\bbrain\b|hippocamp|cerebr|amygdala|\baxon|synap|vestibul|\bretina|\bauditory|\bvisual|cranial nerve|abducens|dopamin|serotonin|norepinephr|acetylcholine|action potential|refractory period|\bgaba\b'),
 ('mental health',r'addiction|withdrawal|abused substance|alcohol|psychiatr|anxiety|\bstress\b|well.being|trauma|suicid|self.harm|\babuse\b|\bneglect\b|overdose'),
]

def decide(packet,independent=None):
    source=packet['source'];text=' '.join([packet.get('source_label',''),packet.get('text','')]).casefold()
    if 'Gene or Genome' in packet.get('semantic_types',[]) and not re.search(r'\b(?:gene|allele)\b',packet['term'],re.I):
        return {'eligible':False,'field':None,'rule':'gene-record-sense-mismatch','reason':'The source is a gene or allele record, not a definition of the requested psychology concept.','policy_version':VERSION}
    text=re.sub(r'\b(?:oxidative|cellular|mechanical|shear|endoplasmic reticulum) stress\b','',text)
    if packet['term'].casefold()=='ability' and packet.get('source_label','').casefold()=='ability':
        return {'eligible':True,'field':'cognition','rule':'exact-foundational-concept-ability','policy_version':VERSION}
    if source in ('baldwin-1901','baldwin-1902-v2','james-1890','titchener-1912','tuke-1892'):
        return {'eligible':True,'field':'history','rule':'permitted-historical-psychology-text','policy_version':VERSION}
    if source in ('onlinestatbook-v2','plos','frontiers','bmc'):
        return {'eligible':True,'field':'research methods','rule':'admitted-method-source','policy_version':VERSION}
    if source.startswith(('article-','nimh-page-')):
        term=packet['term'].casefold()
        term_pattern=r'\b'+r'\W+'.join(re.escape(w) for w in re.findall(r'\w+',term))+r'\b'
        gene_context=re.search(term_pattern+r'\s+(?:(?:is|encodes)\s+(?:a|an)\s+)?(?:wt\s+)?(?:gene|allele)\b',text)
        if gene_context and not re.search(r'\b(?:gene|allele)\b',term):return {'eligible':False,'field':None,'rule':'article-gene-record-sense-mismatch','reason':'The article uses the requested label as a gene or allele name rather than the requested psychology concept.','policy_version':VERSION}
        methods=r'\b(?:factor analysis|path analysis|mediation analysis|moderated mediation|linear regression|logistic regression|multiple regression|regression analysis|regression coefficient|multilevel model|analysis of variance|anova|meta.analysis|effect size|confidence interval|standard error|sample size|random sampling|random assignment|randomi[sz]ation|hypothesis test|research design|quasi.experimental|statistical|experiment)\b'
        if re.search(methods,term):return {'eligible':True,'field':'research methods','rule':'article-requested-method-concept','policy_version':VERSION}
        for field,pattern in PATTERNS:
            if re.search(pattern,term):return {'eligible':True,'field':field,'rule':'article-requested-concept:'+field,'policy_version':VERSION}
    trees=packet.get('tree_numbers',[])
    if not trees and independent is not None:trees=independent.get(packet['source_record'],{}).get('tree_numbers',[])
    for field,roots in ROOTS.items():
        if any(t==prefix or t.startswith(prefix+'.') for t in trees for prefix in roots):
            return {'eligible':True,'field':field,'rule':'source-taxonomy:'+next(t for t in trees if any(t==p or t.startswith(p+'.') for p in roots)),'policy_version':VERSION}
    for field,pattern in PATTERNS:
        if re.search(pattern,text):return {'eligible':True,'field':field,'rule':'psychology-context:'+field,'policy_version':VERSION}
    if any(re.match(r'^F0[124](?:\.|$)',t) for t in trees):
        return {'eligible':True,'field':'cognition','rule':'psychology-taxonomy','policy_version':VERSION}
    if source.startswith('nimh-page-'):return {'eligible':True,'field':'mental health','rule':'verified-nimh-owned-patient-education-context','policy_version':VERSION}
    return {'eligible':False,'field':None,'rule':'no-psychology-counselling-neural-method-or-historical-context','reason':'The pinned source packet does not establish a psychology, counselling, neural, educational, ethical or research-method context.','policy_version':VERSION}

def independent_records(root=ROOT):
    return {r['record_id']:r for r in json.loads((root/'data/term-candidates.json').read_text())['candidates']}
