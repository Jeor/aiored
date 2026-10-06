import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {createRequire} from 'node:module';
import {makeTemplateSchema} from './template-schema.mjs';
import {applyTemplateConditionals} from './conditionals.ts';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const read=p=>JSON.parse(readFileSync(resolve(root,p),'utf8'));
const templates=read('Redhair-complete-setup-template.json');
const source=read('sources/redhair-default-config.json');
const sections=read('validation/section-fields.json'), paths=read('validation/section-inputs.json');
const keys=Object.keys(sections);
const {z}=createRequire(resolve(root,'validation/sel/package.json'))('zod');
export function defaults(t){return Object.fromEntries(t.metadata.inputs.filter(o=>'default' in o||o.subOptions).map(o=>[o.id,o.subOptions?Object.fromEntries(o.subOptions.filter(s=>'default' in s).map(s=>[s.id,s.default])):o.default]));}
let combinations=0;
for(const t of templates){
 makeTemplateSchema(z).parse(t);
 const isFull=t.metadata.id==='custom.redhair.full';
 assert.equal(t.metadata.version,'1.4.0');
 assert.equal(t.metadata.inputs.filter(o=>o.type==='subsection').length,4);
 if(isFull)assert(!('services' in t.metadata));else assert.deepEqual(t.metadata.services,[]);
 const d=defaults(t);d.applyMode='selected';
 const resolveConfig=(inputs,svcs=[])=>applyTemplateConditionals(t.config,inputs,svcs);
 const full=resolveConfig(d);
 for(const key of ['proxy','services','trusted','variants','showChanges'])assert(!(key in full));
 for(const [key,value] of Object.entries(source)){
  if(['proxy','services','trusted','variants','showChanges','presets','catalogModifications'].includes(key))continue;
  assert.deepEqual(full[key],value,`Changed Redhair default: ${key}`);
 }
 const expectedPresets=structuredClone(source.presets.filter(p=>p.enabled));
 if(isFull)for(const p of expectedPresets)delete p.options.services;
 assert.deepEqual(full.presets,expectedPresets);
 assert.deepEqual(full.catalogModifications,isFull?[]:source.catalogModifications);
 const existing=Object.fromEntries(Object.keys(full).map(k=>[k,{keep:`user-custom-${k}`} ]));
 Object.assign(existing,{proxy:{enabled:true,url:'https://example.invalid/proxy'},services:[{id:'torbox',credentials:{apiKey:'test-only'}}],variants:[{id:'user-variant'}],addonName:'My custom name',trusted:true});
 for(let mask=0;mask<(1<<keys.length);mask++){
  const input=structuredClone(d);
  for(const [i,k] of keys.entries()){const [g,s]=paths[k].split('.');input[g][s]=Boolean(mask&(1<<i));}
  const patch=resolveConfig(input);
  const expected=new Set(['appliedTemplates',...keys.filter((k,i)=>mask&(1<<i)).flatMap(k=>sections[k])]);
  assert.deepEqual(new Set(Object.keys(patch)),expected);
  const merged={...existing,...patch};
  for(const [key,value] of Object.entries(existing))if(!expected.has(key))assert.deepEqual(merged[key],value);
  for(const k of expected)assert.deepEqual(patch[k],full[k]);
  if(!input.connections.addons)assert(!JSON.stringify(patch).includes('template_placeholder'));
  combinations++;
 }
 if(!isFull){
  const only=resolveConfig(defaults(t));
  assert.deepEqual(new Set(Object.keys(only)),new Set(['appliedTemplates',...sections.sel]));
  assert(!JSON.stringify(only).includes('template_placeholder'));
 }
 // Each addon can be included alone; optional selections become enabled and
 // require a fresh endpoint. No other addon or stale catalog entry remains.
 for(const p of source.presets){
  const input=structuredClone(d);input.connections.addonIds=[p.instanceId];input.connections.timeout='20000';
  const cfg=resolveConfig(input,['realdebrid']);
  assert.equal(cfg.presets.length,1);assert.equal(cfg.presets[0].instanceId,p.instanceId);
  assert.equal(cfg.presets[0].enabled,true);assert.equal(cfg.presets[0].options.timeout,20000);
  assert(!JSON.stringify(cfg).includes('<optional_template_placeholder>'));
  for(const c of cfg.catalogModifications)assert.equal(c.addonName,p.options.name);
 }
 const empty=structuredClone(d);empty.connections.addonIds=[];
 const cfg=resolveConfig(empty);assert.deepEqual(cfg.presets,[]);assert.deepEqual(cfg.catalogModifications,[]);
 assert(!JSON.stringify(cfg).includes('template_placeholder'));
 // Enabled routing omits the restriction. An empty array would disable every
 // service in getUsableServices, so explicitly guard against that regression.
 const auto=structuredClone(d);auto.connections.routing='enabled';
 for(const svcs of [[],['realdebrid'],['torbox'],['aiostreams','nzbdav']]){
  const cfg=resolveConfig(auto,svcs);for(const p of cfg.presets)assert(!('services' in p.options));
 }
 const refs=[...JSON.stringify(t).matchAll(/inputs\.([\w.]+)/g)].map(m=>m[1]);
 const declared=new Set(t.metadata.inputs.flatMap(o=>[o.id,...(o.subOptions||[]).map(s=>o.id+'.'+s.id)]));
 assert(refs.every(r=>declared.has(r)),`Undeclared inputs: ${refs.filter(r=>!declared.has(r))}`);
}
const report={version:'1.4.0',result:'pass',sectionToggleCombinations:combinations,templates:2,inlineGroups:4,individualAddonSelections:40,redhairQualityDefaultsPreserved:true,selOnlyPreservesOtherSections:true,proxyAbsent:true,serviceWizardFullSetupOnly:true,liveImportTested:false};
writeFileSync(resolve(root,'validation/section-results.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${combinations} section combinations, 40 addon selections, schemas, defaults, service routing and safe updates.`);
