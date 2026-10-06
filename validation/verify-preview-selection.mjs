import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {evaluateTemplateCondition} from './conditionals.ts';
const templates=JSON.parse(readFileSync(new URL('../Redhair-complete-setup-template.json',import.meta.url),'utf8'));
for(const t of templates){
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
