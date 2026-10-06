import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {evaluateTemplateCondition} from './conditionals.ts';
const templates=JSON.parse(readFileSync(new URL('../Redhair-complete-setup-template.json',import.meta.url),'utf8'));
for(const t of templates){
 const dialogs=t.metadata.inputs.filter(o=>o.type==='subsection');
 assert.equal(dialogs.length,1,'Only advanced addon settings should need Open');
 assert.equal(dialogs[0].id,'connections');
 const paths=JSON.parse(readFileSync(new URL('./section-inputs.json',import.meta.url),'utf8'));
 for(const id of Object.values(paths))assert(t.metadata.inputs.some(o=>o.id===id&&o.type==='boolean'),'Every section toggle must be top level');
 const picker=t.metadata.inputs.find(o=>o.id==='addonIds'&&o.type==='multi-select');
 assert(picker,'Addon picker must be top level');
 assert.equal(t.metadata.inputs.filter(o=>o.id==='addonIds').length,1);
 const source=JSON.parse(readFileSync(new URL('../sources/redhair-default-config.json',import.meta.url),'utf8'));
 for(const p of source.presets.filter(p=>p.category==='Usenet')){
  assert(picker.options.find(o=>o.value===p.instanceId).label.includes('Usenet'));
  assert(!picker.default.includes(p.instanceId));
 }
 for(const on of [true,false]){
  assert.equal(evaluateTemplateCondition(picker.__if,{addonsEnabled:on},[]),on);
  assert.equal(evaluateTemplateCondition(dialogs[0].__if,{addonsEnabled:on},[]),on);
 }
 assert.deepEqual(dialogs[0].subOptions.map(o=>o.id),['meteorUsenet','routing','timeout']);
 // Top-level controls dispatch directly to wizard state; subsection controls
 // buffer edits until Save and cannot drive a live preview inside that modal.
 const selector=t.metadata.inputs.find(o=>o.id==='formatterStyle');
 assert(selector,'Formatter selector must be on the Options screen, outside a subsection modal');
 for(const style of selector.options.map(o=>o.value)){
  const inputs={applyMode:'selected',formatterEnabled:true,formatterStyle:style};
  const shown=t.metadata.inputs.filter(o=>!o.__if||evaluateTemplateCondition(o.__if,inputs,[]));
  assert.deepEqual(shown.filter(o=>o.id.startsWith('preview_')).map(o=>o.id),['preview_'+style]);
  inputs.formatterEnabled=false;
  assert(!t.metadata.inputs.some(o=>o.id.startsWith('preview_')&&evaluateTemplateCondition(o.__if,inputs,[])));
 }
}
console.log('PASS: selecting each formatter directly exposes exactly its preview; disabled formatter hides previews.');
