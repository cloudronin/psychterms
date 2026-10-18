"""Record source-by-source decisions. A family policy does not approve every item."""
from pathlib import Path
import csv,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
rows=[]
def add(ident,title,url,licence,policy,decision,role,version,reason,confirmed=True):
 evidence={'policy_url':policy,'reviewed_on':'2026-10-18','finding':reason,'licence_confirmed':confirmed}
 evidence['sha256']=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
 rows.append({'id':ident,'candidate':title,'url':url,'licence':licence,'licence_source_url':policy,'licence_confirmed':confirmed,'pinned_version':version,'roles':role,'decision':decision,'reason':reason,'evidence':evidence,'asset_pin_required':True})
add('mesh-2026','MeSH descriptors','https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/mesh_browser/d2026.bin','public-domain-US-government','https://www.nlm.nih.gov/databases/download/terms_and_conditions_mesh.html','yes',['term_list','aliases','links','draft_basis','supports_definition'],'2026 descriptor edition','NLM terms permit use with conspicuous acknowledgement and no implied endorsement; descriptor records only.')
add('wikidata','Wikidata structured data','https://www.wikidata.org/wiki/Wikidata:Data_access','CC0-1.0','https://www.wikidata.org/wiki/Wikidata:Copyright','yes',['term_list','aliases','links'],'Per-entity revision IDs required','Structured namespaces only; no Wikipedia/Wiktionary prose; pin each entity revision.')
add('nimh','NIMH-authored text','https://www.nimh.nih.gov/health/topics','public-domain-US-government','https://www.nimh.nih.gov/site-info/policies','yes',['draft_basis','supports_definition'],'Live policy reviewed 2026-10-18; each content page needs snapshot','Own text is public domain unless otherwise indicated; no images, external materials, misleading modification or endorsement.')
add('samhsa','SAMHSA glossary/publications','https://library.samhsa.gov/','unconfirmed','https://www.samhsa.gov/about/laws-regulations-policies','no',['draft_basis'],'No approved edition pinned','No blanket permission inferred from .gov; select and verify a specific publication with a public-domain notice.',False)
add('nih','NIH-authored glossary pages','https://www.nih.gov/about-nih/frequently-asked-questions','public-domain-US-government','https://www.nih.gov/about-nih/frequently-asked-questions','yes',['draft_basis','supports_definition'],'FAQ policy reviewed 2026-10-18; per-page snapshot required','NIH states most own site information is public domain; excludes marked third-party content and journal articles merely funded by NIH.')
add('hhs','HHS glossaries','https://www.hhs.gov/','unconfirmed','https://www.hhs.gov/web/policies-and-standards/','no',['draft_basis'],'No glossary edition approved','Specific glossary rights page not confirmed; not a blanket .gov approval.',False)
add('medlineplus-genetics','MedlinePlus Genetics NLM-authored summaries','https://medlineplus.gov/genetics/','public-domain-US-government','https://medlineplus.gov/about/using/usingcontent/','yes',['draft_basis','supports_definition'],'Snapshot and reviewed date required for each genetics summary','NLM-produced Genetics text is distinguished from licensed encyclopaedia, drug and consumer materials; only own unmarked text.')
add('medlineplus-licensed','MedlinePlus licensed encyclopedia and drug text','https://medlineplus.gov/encyclopedia.html','third-party-licences','https://medlineplus.gov/about/using/usingcontent/','no',['draft_basis'],'Current licensed-content policy','Hosting on MedlinePlus is not permission to adapt third-party encyclopedia, illustration, or drug content.')
add('va-ptsd','VA National Center for PTSD staff public-domain articles','https://www.ptsd.va.gov/publications/staff_articles.asp','public-domain-US-government','https://www.ptsd.va.gov/publications/staff_articles.asp','yes',['draft_basis','supports_definition'],'Per-article publication and rights notice required','The staff-articles page identifies public-domain PDFs; only specifically designated government works, not every linked journal article. No instrument items or DSM criteria copied.')
add('cdc','CDC-authored glossary text','https://www.cdc.gov/mental-health/about/index.html','public-domain-US-government','https://www.cdc.gov/other/agencymaterials.html','yes',['draft_basis','supports_definition'],'Agency-materials policy reviewed 2026-10-18; per-page snapshot required','Most own content is public domain; marked contractor/grantee/third-party materials excluded; attribution and no endorsement notice required.')
add('ncit','NCI Thesaurus','https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/','CC-BY-4.0','https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/ThesaurusTermsofUse.htm','yes',['term_list','draft_basis','supports_definition'],'Release identifier and archive checksum required','Current NCI terms explicitly state CC BY 4.0, not public domain. Preserve source-specific definition credits; filter psychology relevance.')
add('eric','ERIC Thesaurus','https://eric.ed.gov/?ti=all','unconfirmed','https://eric.ed.gov/?copyright','no',['term_list','draft_basis','aliases','links'],'Unapproved pending rights confirmation','Current official copyright page and 2025 Thesaurus download provide no confirmed specific reuse grant for Thesaurus text; the archive contains no licence notice. Download availability alone is insufficient; keep excluded.',False)
add('nhs','NHS.UK-owned topic and glossary text','https://www.nhs.uk/mental-health/','OGL-UK-3.0','https://www.nhs.uk/our-policies/terms-and-conditions/','yes',['draft_basis','supports_definition'],'Terms retrieved 2026-10-18; per-page snapshot required','NHS-owned content under OGL v3 except exclusions; include prescribed attribution; no logos, third-party content or modified clinical advice.')
add('nice','NICE content','https://www.nice.org.uk/','NICE-UK-only-restricted','https://www.nice.org.uk/reusing-our-content/nice-uk-open-content-licence','no',['draft_basis'],'NICE UK Open Content Licence reviewed 2026-10-18','Not general OGL v3: UK-only terms and explicit permission required for AI purposes. Excluded.')
add('aihw','Australian Institute of Health and Welfare text','https://www.aihw.gov.au/mental-health','CC-BY-4.0','https://www.aihw.gov.au/copyright','yes',['draft_basis','supports_definition'],'Copyright policy reviewed 2026-10-18; per-publication edition required','CC BY 4.0 unless stated otherwise; third-party materials, older exceptions and logos excluded; indicate adaptations.')
add('australian-health','Australian Department of Health website text','https://www.health.gov.au/topics/mental-health-and-suicide-prevention','restricted-web-reuse','https://www.health.gov.au/using-our-websites/copyright','no',['draft_basis'],'Copyright notice reviewed 2026-10-18','Observed notice does not establish blanket CC BY for this use; do not infer from another Australian agency.')
add('eu-publications','EU Publications Office publications','https://op.europa.eu/','CC-BY-4.0-item-verification-needed','https://op.europa.eu/en/web/about-us/legal-notices/publications-office-of-the-european-union-copyright','no',['draft_basis'],'No psychology publication edition selected','Portal editorial policy is CC BY 4.0, but publication-specific notices govern each downloadable work. No specific psychology publication pinned yet.')
add('baldwin-1901','Baldwin Dictionary of Philosophy and Psychology, 1901','https://psychclassics.yorku.ca/Baldwin/Dictionary/','historical-item-verification-needed','https://psychclassics.yorku.ca/Baldwin/Dictionary/','no',['draft_basis'],'1901; digitized edition not yet cleared','Historical candidate only. Verify edition, original text boundaries and archive rights statement before ingesting; modern editorial additions excluded.',False)
add('james-1890','William James, Principles of Psychology, volume 1','https://www.gutenberg.org/ebooks/57628','public-domain-US','https://www.gutenberg.org/ebooks/57628','yes',['draft_basis'],'1890 original; Gutenberg ebook 57628; snapshot required','Catalogue identifies public domain in the USA; use original historical text, retain historical framing and exclude modern additions. Do not present dated views as current consensus.')
add('titchener-1912','Titchener, The Schema of Introspection, 1912','https://psychclassics.yorku.ca/Titchener/introspection.htm','historical-item-verification-needed','https://psychclassics.yorku.ca/Titchener/introspection.htm','no',['draft_basis'],'1912; archive transcription needs rights confirmation','Pre-1929 publication alone does not pin the digital edition or its additions. Keep out until the exact rights statement is recorded.',False)
add('york-archive','York Classics archive as a collection','https://psychclassics.yorku.ca/','mixed','https://psychclassics.yorku.ca/','no',['draft_basis'],'No blanket archive edition','Collection includes item-specific reproduction notices and later works; never treat the whole archive as public domain.')
add('bccampus-intro-2014','BCcampus Introduction to Psychology, first Canadian edition','https://opentextbc.ca/introductiontopsychology/','CC-BY-NC-SA-4.0','https://opentextbc.ca/introductiontopsychology/','no',['draft_basis'],'2014 first Canadian edition','Own book licence is NC-SA. Excluded despite being an open textbook.')
add('bccampus-other','Other BCcampus CC BY psychology textbooks','https://collection.bccampus.ca/','unconfirmed','https://collection.bccampus.ca/','no',['draft_basis'],'No eligible specific edition selected','Platform openness is not an edition-specific licence. Select a named CC BY edition before admitting content.',False)
add('lumen-lifespan','Lumen Lifespan Development About page / original component','https://courses.lumenlearning.com/wm-lifespandevelopment/about/','mixed-components','https://courses.lumenlearning.com/wm-lifespandevelopment/about/','no',['draft_basis'],'Waymaker Lifespan Development, live course','About page identifies original CC BY 3.0 material but enhancements and components require individual credit checks. Do not blanket approve the course.')
add('plos','PLOS research-method articles','https://journals.plos.org/plosone/s/licenses-and-copyright','CC-BY-4.0-item-verification-needed','https://journals.plos.org/plosone/s/licenses-and-copyright','no',['draft_basis','supports_definition'],'Publisher policy checked; no DOI selected','Publisher CC BY policy confirmed. Admit a specific DOI/revision only after article licence and excluded materials are checked.')
add('frontiers','Frontiers research-method articles','https://www.frontiersin.org/about/policies-and-publication-ethics','article-specific','https://www.frontiersin.org/about/policies-and-publication-ethics','no',['draft_basis','supports_definition'],'No DOI selected','No article-specific licence and revision recorded yet; a publisher name is not a drafting packet.',False)
add('bmc','BMC research-method articles','https://www.biomedcentral.com/about/policies/copyright','article-specific','https://www.biomedcentral.com/about/policies/copyright','no',['draft_basis','supports_definition'],'No DOI selected','Check each article for CC BY versus other available licences and pin DOI/revision; no selected article yet.',False)
for ident,title,url,licence,policy,reason in [
 ('noba','Noba','https://nobaproject.com/','CC-BY-NC-SA-4.0','https://nobaproject.com/','Noncommercial and ShareAlike; excluded.'),
 ('openstax','OpenStax Psychology 2e','https://openstax.org/books/psychology-2e/pages/preface','CC-BY-NC-SA-4.0','https://openstax.org/books/psychology-2e/pages/preface','Current Psychology 2e edition is NC-SA; excluded.'),
 ('wikipedia','Wikipedia prose','https://en.wikipedia.org/','CC-BY-SA-4.0','https://en.wikipedia.org/wiki/Wikipedia:Copyrights','ShareAlike prose excluded; background URLs alone do not become drafting basis.'),
 ('wiktionary','Wiktionary prose','https://en.wiktionary.org/','CC-BY-SA','https://en.wiktionary.org/wiki/Wiktionary:Copyrights','ShareAlike text excluded.'),
 ('who-icd11','WHO / ICD-11 content','https://icd.who.int/','WHO-own-terms-ND','https://www.who.int/about/policies/publishing/copyright','No-derivatives/own terms; excluded by policy.'),
 ('umls','UMLS','https://www.nlm.nih.gov/research/umls/','own-licence','https://www.nlm.nih.gov/research/umls/license.html','Own licence and source vocabularies; excluded.'),
 ('snomed','SNOMED CT','https://www.snomed.org/','own-licence','https://www.snomed.org/get-snomed','Own licence; excluded.')]:
 add(ident,title,url,licence,policy,'no',[], 'Policy exclusion; no asset admitted',reason,False)
# Item-specific checks supersede the initial collection-level exclusions.
byid={r['id']:r for r in rows}
for ident,licence,version,finding in [
 ('baldwin-1901','public-domain-US','1901 New York Macmillan original; archive index checked 2026-10-18','The source reproduces the original title page and 1901 New York publication. Original US-published text is public domain; modern archive/editorial additions are excluded.'),
 ('titchener-1912','public-domain-US','1912 American Journal of Psychology 23, 485–508','Original 1912 US article identified on its own archive page; original text only, excluding modern editorial material.'),
]:
 r=byid[ident];r.update(licence=licence,pinned_version=version,decision='yes',licence_confirmed=True,reason=finding)
 r['evidence'].update(finding=finding,licence_confirmed=True,rights_basis='original US publication before 1929')
 r['evidence']['sha256']=hashlib.sha256(json.dumps({k:v for k,v in r['evidence'].items() if k!='sha256'},sort_keys=True).encode()).hexdigest()
r=byid['bmc'];r.update(candidate='BMC: Characterising and justifying sample size sufficiency in interview-based studies',url='https://link.springer.com/article/10.1186/s12874-018-0594-7',licence='CC-BY-4.0',licence_source_url='https://link.springer.com/article/10.1186/s12874-018-0594-7',licence_confirmed=True,pinned_version='Version of record 2018-11-21; DOI 10.1186/s12874-018-0594-7',decision='yes',reason='Own article Rights and permissions explicitly gives CC BY 4.0. Use only source-supported qualitative-method concepts, not article findings as universal claims.')
r['evidence']={'policy_url':r['url'],'reviewed_on':'2026-10-18','finding':r['reason'],'licence_confirmed':True};r['evidence']['sha256']=hashlib.sha256(json.dumps(r['evidence'],sort_keys=True).encode()).hexdigest()
for ident,title,url,version,reason in [
 ('plos','PLOS: Ten Simple Rules for Writing Research Papers','https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003453','2014-01-30; DOI 10.1371/journal.pcbi.1003453','Article copyright notice links to CC BY 4.0. Limited to source-supported research/writing concepts; not a general psychology glossary.'),
 ('frontiers','Frontiers: Calculating and reporting effect sizes to facilitate cumulative science','https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2013.00863/full','2013 volume 4; DOI 10.3389/fpsyg.2013.00863','Own article gives CC BY; publisher open-access policy links to CC BY 4.0. Research-method scope only; individual claims must be supported by packet.'),
]:
 r=byid[ident];r.update(candidate=title,url=url,licence='CC-BY-4.0',licence_source_url=url,licence_confirmed=True,pinned_version=version,decision='yes',reason=reason)
 r['evidence']={'policy_url':url,'reviewed_on':'2026-10-18','finding':reason,'licence_confirmed':True}
 r['evidence']['sha256']=hashlib.sha256(json.dumps(r['evidence'],sort_keys=True).encode()).hexdigest()
# Additional source verified at the publisher after the initial inventory.
stat_policy=ROOT/'.private/coverage-audit/onlinestatbook-policy.html'
existing=ROOT/'data/sources.json'
stat_existing=None
if existing.exists():
 stat_existing=next((r for r in json.loads(existing.read_text())['sources'] if r['id']=='onlinestatbook-v2'),None)
if stat_existing:
 rows.append(stat_existing);byid['onlinestatbook-v2']=stat_existing
elif stat_policy.exists():
 policy_sha=hashlib.sha256(stat_policy.read_bytes()).hexdigest()
 add('onlinestatbook-v2','Online Statistics Education, version 2 (David M. Lane, project leader)','https://onlinestatbook.com/2/index.html','public-domain-US','https://onlinestatbook.com/2/index.html','yes',['term_list','aliases','draft_basis','supports_definition'],'Version 2; publisher statement snapshot 2026-10-18; SHA-256 '+policy_sha,'The project owner explicitly places the work in the public domain and requests attribution. Restrict to its own version-2 course/glossary content; exclude external linked material.')
 rows[-1]['evidence']['policy_snapshot_sha256']=policy_sha
# Preserve additional individually verified historical editions.
if existing.exists():
 for verified in json.loads(existing.read_text())['sources']:
  if verified['id'] in ('baldwin-1902-v2','tuke-1892'):
   rows.append(verified);byid[verified['id']]=verified
# Raw downloaded policy and edition hashes are distinct from hashes of review findings.
snapshot_path=ROOT/'reports/source-snapshots.json'
if snapshot_path.exists():
 snapshots={v['file']:v for v in json.loads(snapshot_path.read_text())['snapshots'] if v['status']=='downloaded'}
 for ident,name in [('mesh-2026','mesh-policy.html'),('nimh','nimh-policy.html'),('ncit','ncit-policy.html'),('nhs','nhs-policy.html'),('wikidata','wikidata-policy.html')]:
  if name in snapshots:byid[ident]['evidence']['policy_snapshot_sha256']=snapshots[name]['sha256']
 if 'mesh-d2026.bin' in snapshots:byid['mesh-2026']['content_snapshot_sha256']=snapshots['mesh-d2026.bin']['sha256']
obj={'schema_version':1,'checked_on':'2026-10-18','policy':'A yes admits only the stated scope. Every actual packet still requires a pinned asset, source-specific exception check and allowed role. Unconfirmed candidates are no. Evidence hashes pin this review finding, not unread content.','sources':rows}
(ROOT/'data/sources.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
fields=['id','candidate','licence','licence_source_url','licence_confirmed','pinned_version','roles','decision','reason']
with (ROOT/'reports/source-inventory.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader()
 for row in rows:w.writerow({k:'; '.join(row[k]) if isinstance(row[k],list) else row[k] for k in fields})
print(json.dumps({'candidate_rows':len(rows),'yes':sum(r['decision']=='yes' for r in rows),'no':sum(r['decision']=='no' for r in rows),'unconfirmed_are_excluded':True},indent=2))
