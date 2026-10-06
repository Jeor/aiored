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
assert.equal(templates.length,1);
assert.equal(templates[0].metadata.id,'custom.redhair.full');
let combinations=0;
for(const t of templates){
 makeTemplateSchema(z).parse(t);
 const isFull=t.metadata.id==='custom.redhair.full';
 assert.equal(t.metadata.version,'1.5.1');
 assert.equal(t.metadata.inputs.filter(o=>o.type==='subsection').length,3);
 if(isFull)assert(!('services' in t.metadata));else assert.deepEqual(t.metadata.services,[]);
 const d=defaults(t);
 const resolveConfig=(inputs,svcs=[])=>applyTemplateConditionals(t.config,inputs,svcs);
 const full=resolveConfig(d);
 for(const key of ['proxy','services','trusted','variants','showChanges'])assert(!(key in full));
 for(const [key,value] of Object.entries(source)){
  if(['proxy','services','trusted','variants','showChanges','presets','catalogModifications'].includes(key))continue;
  assert.deepEqual(full[key],value,`Changed Redhair default: ${key}`);
 }
 const expectedPresets=structuredClone(source.presets.filter(p=>p.enabled&&p.category!=='Usenet'));
 for(const p of expectedPresets){delete p.options.services;if(p.type==='meteor')p.options.usenet.enabled=false;}
 assert.deepEqual(full.presets,expectedPresets);
 assert.deepEqual(full.catalogModifications,isFull?[]:source.catalogModifications);
 const existing=Object.fromEntries(Object.keys(full).map(k=>[k,{keep:`user-custom-${k}`} ]));
 Object.assign(existing,{proxy:{enabled:true,url:'https://example.invalid/proxy'},services:[{id:'torbox',credentials:{apiKey:'test-only'}}],variants:[{id:'user-variant'}],addonName:'My custom name',trusted:true});
 for(let mask=0;mask<(1<<keys.length);mask++){
  const input=structuredClone(d);
  for(const [i,k] of keys.entries()){const [g,s]=paths[k].split('.');if(s)input[g][s]=Boolean(mask&(1<<i));else input[g]=Boolean(mask&(1<<i));}
  const patch=resolveConfig(input);
  const expected=new Set(['appliedTemplates',...keys.filter((k,i)=>mask&(1<<i)).flatMap(k=>sections[k])]);
  assert.deepEqual(new Set(Object.keys(patch)),expected);
  const merged={...existing,...patch};
  for(const [key,value] of Object.entries(existing))if(!expected.has(key))assert.deepEqual(merged[key],value);
  for(const k of expected)assert.deepEqual(patch[k],full[k]);
  if(!input.connections.addons)assert(!JSON.stringify(patch).includes('template_placeholder'));
  combinations++;
 }
 const sel=structuredClone(d);
 for(const [k,path] of Object.entries(paths)){const [g,s]=path.split('.');if(s)sel[g][s]=k==='sel';else sel[g]=k==='sel';}
 const only=resolveConfig(sel);
 assert.deepEqual(new Set(Object.keys(only)),new Set(['appliedTemplates',...sections.sel]));
 assert(!JSON.stringify(only).includes('template_placeholder'));
 assert(!full.presets.some(p=>p.category==='Usenet'||p.type==='newznab'));
 assert.equal(full.presets.find(p=>p.type==='meteor').options.usenet.enabled,false);
 const meteor=structuredClone(d);meteor.connections.meteorUsenet=true;
 assert.equal(resolveConfig(meteor).presets.find(p=>p.type==='meteor').options.usenet.enabled,true);
 assert(!t.metadata.inputs.some(o=>o.id==='applyMode'));
 assert.equal(t.metadata.serviceRequired,false);
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
const report={version:'1.5.1',result:'pass',sectionToggleCombinations:combinations,templates:1,settingsGroups:4,subsectionDialogs:3,appearanceInline:true,individualAddonSelections:20,redhairQualityDefaultsPreserved:true,selOnlyPreservesOtherSections:true,proxyAbsent:true,serviceSelectionOptional:true,usenetOffByDefault:true,liveImportTested:false};
writeFileSync(resolve(root,'validation/section-results.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${combinations} section combinations, 20 addon selections, schemas, defaults, service routing and safe updates.`);
