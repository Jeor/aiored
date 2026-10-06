import {readFileSync,writeFileSync} from 'node:fs';
import {compileTemplate} from '../validation/formatter/dist/formatters/engine/compile.js';
import {collectFieldReferences} from '../validation/formatter/dist/formatters/engine/references.js';
import {comparatorFunctions} from '../validation/formatter/dist/formatters/engine/comparators.js';
const root=new URL('../',import.meta.url);
const styles={redhair:'Redhair',jeormatter:'Jeormatter',jeormatter_alt:'Jeormatter Alt',jeormatter_filename:'Jeormatter Filename'};
const fixture={stream:{title:'Example Film',year:2025,seasonEpisode:[],resolution:'2160p',quality:'BluRay REMUX',encode:'HEVC',visualTags:['HDR10'],audioTags:['TrueHD','Atmos'],audioChannels:['7.1'],languages:['English'],uLanguageCodes:['EN'],uSubtitleCodes:['EN'],library:false,preloading:false,seasonPack:false,size:40e9,folderSize:0,bitrate:50e6,proxied:false,type:'debrid',indexer:null,seeders:0,subbed:false,releaseGroup:'FraMeSToR',seScore:95000,nSeScore:95,seadex:false,seadexBest:false,rseMatched:[],network:'Netflix',editions:[],message:null,filename:'Example.Film.2025.2160p.REMUX.mkv'},addon:{name:'Torrentio'},service:{shortName:'TB',name:'TorBox',cached:true}};
const hooks={comparators:comparatorFunctions,resolveVariable:()=>undefined,resolveValues:()=>undefined};
const previews={};let md='# Formatter previews\n\nThese are actual formatter-engine renders of the same fictional cached 4K Remux stream with a normalized SEL score of 95. Client fonts, wrapping and icons can differ.\n';
for(const [style,label] of Object.entries(styles)){
 const format=JSON.parse(readFileSync(new URL(`formatters/${style}.json`,root),'utf8'));
 const data=structuredClone(fixture);
 for(const text of Object.values(format))for(const field of collectFieldReferences(text)){
  const [section,key]=field.split('.');if(section==='tools')continue;
  data[section]??={};if(!(key in data[section]))data[section][key]=null;
 }
 const result={};for(const [key,text] of Object.entries(format))result[key]=compileTemplate(text,hooks)(data).split('\n').filter(l=>l.trim()&&!l.includes('\u0012')).join('\n').replaceAll('\u0011','\n');
 if(JSON.stringify(result).includes('unknown_propertyName'))throw Error(`Missing fixture field for ${style}`);
 previews[style]=result;
 md+=`\n## ${label}\n\n\`\`\`text\n${result.name}\n${result.description}\n\`\`\`\n`;
}
writeFileSync(new URL('validation/formatter-previews.json',root),JSON.stringify(previews,null,2)+'\n');
writeFileSync(new URL('FORMATTER-PREVIEWS.md',root),md);
console.log('Rendered four formatter previews.');
