import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sceneState, RISK_NOTICE} from '../site/src/scene-state.mjs';
const vignette = {text:'Synthetic renderer test, never site content.',notice:'Synthetic notice.',card_id:'p_19',card_hash:'sha256:'+'a'.repeat(64),builder_commit:'b'.repeat(40)};
test('definition-only entry omits the scene panel',()=>assert.equal(sceneState({}),'none'));
test('unbound provenance enables the scene presentation',()=>assert.equal(sceneState({vignette}),'scene'));
test('risk notice is exact and takes precedence over any scene',()=>{
 assert.equal(RISK_NOTICE,'No scene is provided for this risk term.');
 assert.equal(sceneState({risk:true,vignette:{card_id:'scenario:private'}}),'risk');
});
test('bound Prep scenario and missing provenance are rejected',()=>{
 for(const patch of [{card_id:'scenario:private'},{card_hash:''},{builder_commit:''},{text:''}])
  assert.throws(()=>sceneState({vignette:{...vignette,...patch}}),/unbound-card/);
});
test('brand and displayed citation/breadcrumb domain use agreed casing',()=>{
 const layout=readFileSync(new URL('../site/src/layouts/Layout.astro',import.meta.url),'utf8');
 const term=readFileSync(new URL('../site/src/pages/terms/[id].astro',import.meta.url),'utf8');
 assert.ok(layout.includes('<strong>PsychTerms</strong>'));
 assert.ok(term.includes('PsychTerms (psychterms.org)'));
 assert.ok(term.includes('>psychterms.org</a> / <span data-entry-content>{entry.id}</span>'));
 assert.ok(!layout.includes('Psych Terms')&&!term.includes('Psych Terms'));
});
