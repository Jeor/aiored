import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {makeTemplateSchema} from './template-schema.mjs';
import {readFileSync, readdirSync, writeFileSync} from 'node:fs';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {dirname, resolve} from 'node:path';
import {applyTemplateConditionals} from './conditionals.ts';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = path => JSON.parse(readFileSync(resolve(root,path),'utf8'));
const publishedTemplate = read('Redhair-complete-setup-template.json');
const template = read('Redhair-custom-profile-template.json');
const inputs = {};
function defaults(options, target) {
  for (const o of options) {
    if(o.subOptions) defaults(o.subOptions, target[o.id]={});
    else if('default' in o) target[o.id]=o.default;
  }
}
defaults(template.metadata.inputs, inputs);
const slugs=readdirSync(resolve(root,'sources/redhair')).filter(x=>x.endsWith('.expressions.json')).map(x=>x.replace('.expressions.json',''));
const movie=slugs.filter(x=>!x.startsWith('anime-'));
const anime=['none',...slugs.filter(x=>x.startsWith('anime-'))];
let combinations=0;
for(const m of movie) for(const a of anime) for(const services of [[],['realdebrid'],['torbox']]) for(const sort of ['resolution-quality-score','score-first']) {
  const cfg=applyTemplateConditionals(template.config,{...inputs,qualityProfile:m,animeProfile:a,qualitySort:sort},services);
  assert(!JSON.stringify(cfg).includes('{{inputs.'));
  assert(!JSON.stringify(cfg).includes('<SYNCED:'));
  assert.equal(cfg.rankedStreamExpressions.length,read(`sources/redhair/${m}.expressions.json`).length+(a==='none'?0:read(`sources/redhair/${a}.expressions.json`).length));
  const names=cfg.rankedRegexPatterns.map(r=>r.name);
  assert.equal(new Set(names).size,names.length);
  assert(cfg.sortCriteria.global.some(x=>x.key==='streamExpressionScore'));
  assert.equal(cfg.excludedStreamExpressions.length,0);
  for(const [k,v] of Object.entries(cfg)) if(k.startsWith('synced')) assert.deepEqual(v,[]);
  combinations++;
}
// Optional controls resolve without carrying Tam's dependent scoring engine.
const optionInput=structuredClone(inputs);
optionInput.addonPreset='none'; optionInput.formatterChoice='retain'; optionInput.maxResults=12;
optionInput.deviceExclude=template.metadata.inputs.find(o=>o.id==='deviceExclude').options.map(o=>o.value);
const optional=applyTemplateConditionals(template.config,optionInput,['realdebrid']);
assert(!('presets' in optional)); assert(!('formatter' in optional));
assert.equal(optional.resultLimits.global,12);
assert.equal(optional.excludedStreamExpressions.length,optionInput.deviceExclude.length);
console.log(`PASS: ${combinations} profile/service/sort combinations, optional controls and no stale sync sources.`);

const engine=process.argv[2] || resolve(root,'validation/sel/dist/vendor/streamExpression.js');
const {StreamSelector}=await import(pathToFileURL(resolve(engine)));
const {z}=createRequire(pathToFileURL(resolve(engine)))('zod');
for (const t of [publishedTemplate].flat()) makeTemplateSchema(z).parse(t);
makeTemplateSchema(z).parse(template);
console.log('PASS: upstream template metadata and wizard input schema.');
const filenames=[
 ['Example.2025.1080p.AMZN.WEB-DL.DDP5.1.H.264-NTb.mkv','1080p','WEB-DL','AVC'],
 ['Example.2025.2160p.UHD.BluRay.REMUX.HEVC.DV.TrueHD.Atmos.7.1-FraMeSToR.mkv','2160p','BluRay REMUX','HEVC'],
 ['[DemiHuman] Example - 01 (1080p BluRay REMUX x265 10bit FLAC TrueHD 5.1).mkv','1080p','BluRay REMUX','HEVC'],
 ['Example.2025.720p.WEBRip.x264.AAC-YIFY.mkv','720p','WEBRip','AVC'],
];
function regexMatches(regexes,filename) {
 return regexes.filter(r=>{const m=/^\/(.*)\/([a-z]*)$/.exec(r.pattern); const re=m?new RegExp(m[1],m[2]):new RegExp(r.pattern); return re.test(filename);}).map(r=>r.name);
}
function fixture(row,names){
 const [filename,resolution,quality,encode]=row;
 return {id:'fixture',type:'debrid',filename,folderName:'',addon:{instanceId:'fixture',name:'fixture',preset:{id:'fixture',type:'fixture',options:{}},manifestUrl:'https://example.com/manifest.json',enabled:true,resources:['stream'],timeout:20000},
 parsedFile:{resolution,quality,encode,audioChannels:['5.1'],visualTags:['10bit'],audioTags:['TrueHD','FLAC'],languages:['English','Japanese'],releaseGroup:'DemiHuman',seasonPack:false},
 service:{id:'realdebrid',cached:true},size:4.2e9,rankedRegexesMatched:names};
}
let evaluations=0;
for(const slug of slugs){
 const origR=read(`sources/redhair/${slug}.regexes.json`), origE=read(`sources/redhair/${slug}.expressions.json`);
 const branch=template.config.rankedRegexPatterns.find(b=>b.__if.endsWith(` == ${slug}`)).__value;
 const expr=template.config.rankedStreamExpressions.find(b=>b.__if.endsWith(` == ${slug}`)).__value;
 assert.deepEqual(branch.map(r=>({...r,name:r.name.slice(slug.length+2)})),origR);
 assert.deepEqual(expr.map(e=>({...e,expression:e.expression.replaceAll(`${slug}::`,'')})),origE);
 // Mix every possible opposite-category regex into the stream, demonstrating namespace isolation.
 const opposite=template.config.rankedRegexPatterns.filter(b=>slug.startsWith('anime-')?!b.__if.includes('inputs.animeProfile'):b.__if.includes('inputs.animeProfile')).flatMap(b=>b.__value);
 for(const row of filenames){
  const source=fixture(row,regexMatches(origR,row[0]));
  const adapted=fixture(row,regexMatches([...branch,...opposite],row[0]));
  for(const queryType of ['movie','series','anime.movie','anime.series']){
   const selector=new StreamSelector({queryType,isAnime:queryType.startsWith('anime.')});
   for(let i=0;i<origE.length;i++){
    const before=(await selector.select([source],origE[i].expression)).map(x=>x.id);
    const after=(await selector.select([adapted],expr[i].expression)).map(x=>x.id);
    assert.deepEqual(after,before,`${slug} ${queryType} expression ${i}`);
    evaluations+=2;
   }
  }
 }
 console.log(`PASS: ${slug} — exact scores/patterns preserved, expression matching equivalent with mixed regexes.`);
}
const selector=new StreamSelector({queryType:'movie',isAnime:false});
for(const item of optional.excludedStreamExpressions) await selector.select([fixture(filenames[0],[])],item.expression);
const report={template:'Redhair-complete-setup-template.json',defaultConfiguration:'section-based supplied Redhair defaults; see section-results.json',profileCount:slugs.length,combinations,expressionEvaluations:evaluations,fixtures:filenames.length,result:'pass',limitations:'Local template processor and Redhair-vendored AIOStreams evaluator; no live instance import/playback test.'};
writeFileSync(resolve(root,'validation/results.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${evaluations} original/adapted expression evaluations.`);
