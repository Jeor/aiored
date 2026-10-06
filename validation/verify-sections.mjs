import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {applyTemplateConditionals} from './conditionals.ts';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const read=p=>JSON.parse(readFileSync(resolve(root,p),'utf8'));
const t=read('Redhair-complete-setup-template.json');
const source=read('sources/redhair-default-config.json');
const sections=read('validation/section-fields.json');
const keys=Object.keys(sections);
const defaults={applyMode:'full',sections:Object.fromEntries(keys.map(k=>[k,true]))};
const resolveConfig=inputs=>applyTemplateConditionals(t.config,inputs,[]);
const full=resolveConfig(defaults);
assert.equal(t.metadata.version,'1.2.0');
assert.deepEqual(t.metadata.services,[],'Service selection must be skipped to prevent implicit service mutations.');
assert.equal(t.metadata.inputs.find(i=>i.id==='applyMode').default,'full');
for(const key of ['proxy','services','trusted','variants','showChanges']) assert(!(key in full));
for(const [key,value] of Object.entries(source)) {
 if(['proxy','services','trusted','variants','showChanges'].includes(key))continue;
 assert.deepEqual(full[key],value,`Changed default: ${key}`);
}
// Assert important boundaries independently of the generated map.
for(const key of ['presets','groups','dynamicAddonFetching','catalogModifications','addonCategoryColors'])assert(sections.addons.includes(key));
for(const key of ['rankedStreamExpressions','excludedStreamExpressions','selOverrides','regexOverrides','syncedRankedRegexUrls','syncedRankedStreamExpressionUrls'])assert(sections.sel.includes(key));
assert.deepEqual(sections.sorting,['sortCriteria']);
assert(sections.formatter.includes('formatter'));
assert(sections.limits.includes('resultLimits'));
assert(!sections.sel.includes('sortCriteria'));
assert(!sections.sel.includes('presets'));
// Emulate the actual top-level {...existing, ...resolvedConfig} import merge.
const existing=Object.fromEntries(Object.keys(full).map(k=>[k,{keep:`user-custom-${k}`} ]));
Object.assign(existing,{proxy:{enabled:true,url:'https://example.invalid/proxy',credentials:'test-only'},services:[{id:'torbox',credentials:{apiKey:'test-only'}}],variants:[{id:'user-variant'}],addonName:'My custom name',trusted:true});
let combinations=0;
for(let mask=0;mask<(1<<keys.length);mask++){
 const selected=Object.fromEntries(keys.map((k,i)=>[k,Boolean(mask&(1<<i))]));
 const patch=resolveConfig({applyMode:'selected',sections:selected});
 const expected=new Set(['appliedTemplates',...keys.filter(k=>selected[k]).flatMap(k=>sections[k])]);
 assert.deepEqual(new Set(Object.keys(patch)),expected,`Unexpected changed fields for mask ${mask}`);
 const merged={...existing,...patch};
 for(const [key,value] of Object.entries(existing)){
  if(!expected.has(key))assert.deepEqual(merged[key],value,`Clobbered ${key} for mask ${mask}`);
 }
 for(const k of expected)assert.deepEqual(patch[k],full[k]);
 if(!selected.addons)assert(!JSON.stringify(patch).includes('template_placeholder'),'Skipped add-ons must not prompt for credentials.');
 combinations++;
}
const only=resolveConfig({applyMode:'selOnly',sections:defaults.sections});
assert.deepEqual(new Set(Object.keys(only)),new Set(['appliedTemplates',...sections.sel]));
assert(!JSON.stringify(only).includes('template_placeholder'));
assert.deepEqual(resolveConfig({applyMode:'selected',sections:Object.fromEntries(keys.map(k=>[k,false]))}),{appliedTemplates:full.appliedTemplates});
assert(!('proxy' in source));
for(const key of ['proxy','services','variants'])assert(!(key in t.config));
const report={version:'1.2.0',result:'pass',sectionToggleCombinations:combinations,fullDefaultsMatchSanitizedSource:true,selOnlyPreservesOtherSections:true,allOffPreservesUserSettings:true,proxyAbsent:true,serviceWizardSkipped:true,liveImportTested:false};
writeFileSync(resolve(root,'validation/section-results.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${combinations} section combinations; full defaults, SEL-only, all-off, credential prompts and proxy omission.`);
