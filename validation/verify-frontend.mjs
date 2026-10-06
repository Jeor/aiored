import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {makeTemplateSchema} from './template-schema.mjs';
import {asConfigArray} from './conditionals.ts';
const root=new URL('../',import.meta.url);
const read=p=>JSON.parse(readFileSync(new URL(p,root),'utf8'));
const {z,ZodError}=createRequire(new URL('validation/sel/package.json',root))('zod');
const ts=createRequire(new URL('validation/formatter/package.json',root))('typescript');
// Run the unmodified upstream validator with its actual schema, conditional
// array reader and error formatter. Only module dependency wiring changes.
function load(path,deps,exports){
 const source=readFileSync(new URL(path,root),'utf8');
 const js=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText
  .replace(/^import .*?;\s*/gms,'').replace(/export /g,'');
 return new Function(...Object.keys(deps),js+`\nreturn {${exports.join(',')}};`)(...Object.values(deps));
}
const {formatZodError}=load('validation/frontend/format-zod-error.ts',{z,ZodError},['formatZodError']);
const {validateTemplate}=load('validation/frontend/validator.ts',{TemplateSchema:makeTemplateSchema(z),asConfigArray,formatZodError},['validateTemplate']);
const presets=read('sources/redhair-default-config.json').presets;
// Capability fixture: all referenced addon types available; real unavailable
// types are tested separately below rather than masking warnings.
const status={settings:{presets:[...new Set(presets.map(p=>p.type))].map(ID=>({ID})),services:{},regexAccess:{level:'all'}}};
const templates=read('Redhair-complete-setup-template.json');
const reports=templates.map(t=>({id:t.metadata.id,...validateTemplate(structuredClone(t),status)}));
console.log(JSON.stringify(reports,null,2));
for(const r of reports){assert.deepEqual(r.errors,[],`${r.id}: frontend errors`);assert.deepEqual(r.warnings,[],`${r.id}: frontend warnings`);assert(r.isValid);}
for(const t of templates){
 const unavailable=structuredClone(status);unavailable.settings.presets=unavailable.settings.presets.filter(p=>p.ID!=='torrentio');
 const report=validateTemplate(structuredClone(t),unavailable);
 assert.deepEqual(report.errors,[]);
 assert.deepEqual(report.warnings,['"torrentio" is not available or disabled on this instance.']);
}
writeFileSync(new URL('validation/frontend-results.json',root),JSON.stringify({version:templates[0].metadata.version,result:'pass',templates:reports,unavailableAddonIdentifiedByType:true,liveInstanceTested:false},null,2)+'\n');
console.log('PASS: real frontend validator accepts the updater without errors or spurious warnings.');
