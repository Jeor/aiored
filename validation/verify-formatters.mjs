import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {compileTemplate} from './formatter/dist/formatters/engine/compile.js';
import {parseTemplate} from './formatter/dist/formatters/engine/parser.js';
import {comparatorFunctions} from './formatter/dist/formatters/engine/comparators.js';
import {evaluateTemplateCondition,applyTemplateConditionals} from './conditionals.ts';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const read=p=>JSON.parse(readFileSync(resolve(root,p),'utf8'));
const t=read('Redhair-full-setup-template.json');
const source=read('sources/redhair-default-config.json').formatter;
const styles=['redhair','jeormatter','jeormatter_alt','jeormatter_filename'];
assert.deepEqual(read('formatters/redhair.json'),source.definitions.custom);
assert.equal(t.metadata.inputs.find(x=>x.id==='formatterStyle').default,'redhair');
const hooks={comparators:comparatorFunctions,resolveVariable:()=>undefined,resolveValues:()=>undefined,onDepthExceeded:()=>{throw Error('Formatter nesting too deep');}};
const base={stream:{title:'Example Film',year:2025,seasonEpisode:[],resolution:'2160p',quality:'BluRay REMUX',visualTags:['HDR10'],audioTags:['TrueHD','Atmos'],audioChannels:['7.1'],uLanguageCodes:['EN'],uSubtitleCodes:['EN'],library:false,preloading:false,seasonPack:false,size:40e9,folderSize:0,bitrate:50e6,proxied:false,type:'debrid',indexer:null,seeders:0,subbed:false,releaseGroup:'FraMeSToR',seScore:95000,nSeScore:95,seadex:false,seadexBest:false,rseMatched:[],network:'Netflix',editions:[],message:null,filename:'Example.Film.2025.2160p.REMUX.mkv'},addon:{name:'Torrentio'},service:{shortName:'TB',name:'TorBox',cached:true}};
const scenarios=[
 ...[[100,'🏆 Best'],[95,'🏆 Best'],[94,'🏆 Tier 1'],[80,'🏆 Tier 1'],[79,'🏆 Tier 2'],[60,'🏆 Tier 2'],[59,'🏆 Tier 3'],[40,'🏆 Tier 3'],[39,'🏆 Tier 4'],[20,'🏆 Tier 4'],[19,'🏆 Tier 5'],[5,'🏆 Tier 5'],[4,'🗑️ Subpar'],[0,'🗑️ Subpar']].map(([nSeScore,label])=>({patch:{nSeScore},label})),
 {patch:{seadex:true,seadexBest:true,nSeScore:0},label:'🌊 Best'},
 {patch:{seadex:true,seadexBest:false,nSeScore:100},label:'🌊 Tier 1'},
 {patch:{nSeScore:null},label:null},
];
let renders=0;const previews=read('validation/formatter-previews.json');
for(const style of styles){
 const formatter=read(`formatters/${style}.json`);
 for(const [field,text] of Object.entries(formatter))assert.deepEqual(parseTemplate(text).diagnostics,[],`${style}.${field} parse errors`);
 const full=applyTemplateConditionals(t.config,{formatterEnabled:true,formatterStyle:style},[]);
 assert.deepEqual(full.formatter,{id:'custom',definitions:{custom:formatter}});
 assert(!('posterService' in full),'Formatter-only must preserve posters');
 const postersOnly=applyTemplateConditionals(t.config,{formatterEnabled:false,postersEnabled:true},[]);
 assert.equal(postersOnly.posterService,'rpdb');
 assert(!('formatter' in postersOnly),'Posters-only must preserve formatter');
 for(const mode of ['selOnly','selected']){
  const cfg=applyTemplateConditionals(read('Redhair-update-template.json').config,{applyMode:mode,formatterStyle:style,formatterEnabled:false,quality:{sel:true}},[]);
  assert(!('formatter' in cfg));assert(!('posterService' in cfg));
 }
 if(style==='redhair')continue;
 const original=read(`sources/jeormatter/${style}.json`);
 assert.equal(formatter.description.split('\n').length,original.description.split('\n').length);
 if(style!=='jeormatter_alt')assert.equal(formatter.name,original.name);
 const name=compileTemplate(formatter.name,hooks),description=compileTemplate(formatter.description,hooks);
 for(const {patch,label} of scenarios){
  const data={...base,stream:{...base.stream,...patch}};
  const renderedDescription=description(data);
  if(label)assert(renderedDescription.startsWith(label+' · '),`${style}: badge must begin first description line`);
  else assert(!renderedDescription.startsWith(' · '));
  const output=name(data)+'\n'+renderedDescription;
  assert(!output.includes('{stream.')&&!output.includes('::')&&!output.includes('unknown_propertyName'),`${style}: unrendered template syntax`);
  const badges=output.match(/(?:🏆|🌊) (?:Best|Tier [1-5])|🗑️ Subpar/g)||[];
  assert.deepEqual(badges,label?[label]:[],`${style} ${JSON.stringify(patch)} badge`);
  if(style==='jeormatter_filename')assert(output.endsWith(base.stream.filename));
  renders++;
 }
 // Redhair expression labels, not the old iTunes label, drive the source hint.
 const it=description({...base,stream:{...base.stream,rseMatched:['iT'],network:null}});
 assert(it.includes(' · iTunes'));
 const ma=description({...base,stream:{...base.stream,rseMatched:['MA'],network:null}});
 assert(ma.includes(' · MA'));
 assert.deepEqual(previews[style],{name:name(base),description:description(base)});
}
assert.equal(Object.keys(previews).length,4);
for(const [style,p] of Object.entries(previews)){
 assert(!JSON.stringify(p).includes('unknown_propertyName'));
 const alert=t.metadata.inputs.find(o=>o.id==='preview_'+style);
 assert.equal(alert.description,p.name+'\n'+p.description,'Preview must contain only formatter output');
 const alerts=t.metadata.inputs.filter(o=>o.id.startsWith('preview_'));
 assert.deepEqual(alerts.filter(o=>evaluateTemplateCondition(o.__if,{formatterEnabled:true,formatterStyle:style},[])).map(o=>o.id),['preview_'+style]);
 assert.equal(alerts.filter(o=>evaluateTemplateCondition(o.__if,{formatterEnabled:false,formatterStyle:style},[])).length,0);
}
writeFileSync(resolve(root,'validation/formatter-results.json'),JSON.stringify({version:'1.7.0',result:'pass',styles:4,adaptedBadgeScenarios:renders,sectionIsolation:true,redhairOriginalUnchanged:true,liveClientTested:false},null,2)+'\n');
console.log(`PASS: four formatter options; ${renders} rendered badge scenarios; layout, source labels and section isolation.`);
