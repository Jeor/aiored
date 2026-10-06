"""Build a Tam-style wizard with isolated, unmodified Redhair scoring semantics."""
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / 'sources/redhair'


def rename_references(expression, names):
    # Only rewrite string arguments directly inside regexMatched(...).
    # Strings passed to quality(), language(), etc. must remain untouched.
    tokens = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|[()]|.', re.S)
    result, stack, previous = [], [], ''
    for match in tokens.finditer(expression):
        token = match.group()
        if token == '(':
            stack.append(previous)
        elif token == ')':
            stack.pop()
        elif token.startswith('"') and stack and stack[-1] == 'regexMatched':
            name = json.loads(token)
            if name not in names:
                raise ValueError(f'Unresolved regex reference: {name}')
            prefix = names[name][:-len(name)]
            token = '"' + json.dumps(prefix)[1:-1] + token[1:]
        elif token.startswith("'") and stack and stack[-1] == 'regexMatched':
            raise ValueError('Unexpected single-quoted regex name; review source')
        result.append(token)
        if not token.isspace():
            previous = token
    assert not stack
    return ''.join(result)


def build_custom():
    template = json.loads((ROOT / 'sources/tamtaro-complete.json').read_text())
    cfg = template['config']
    original_inputs = template['metadata']['inputs']
    keep = {'header.languageSettings', 'languages', 'strictLanguage', 'subtitles',
            'header.addonSettings', 'addonPreset', 'includeAddon', 'header.otherSettings',
            'formatterChoice', 'torboxTier', 'deviceExclude', 'misc', 'header.catalogsNotice'}
    inputs = [x for x in original_inputs if x['id'] in keep]
    for option in inputs:
        if option['id'] == 'deviceExclude':
            option['options'] = [x for x in option['options'] if x['value'] not in ('dvOnlyNonRemux', 'DVP7')]
        if option['id'] == 'misc':
            option['subOptions'] = [x for x in option['subOptions'] if x['id'] not in ('keepScore', 'ignoreRSE')]
            option['description'] = 'Statistics, digital release filtering, and add-on appearance.'
            for sub in option['subOptions']:
                if sub['id'] == 'addonName':
                    sub['default'] = 'AIO Quality'
                    sub['options'] = [{'value': 'AIO Quality', 'label': 'AIO Quality'}, {'value':'none','label':'Keep Existing Name'}]
                if sub['id'] == 'addonLogo':
                    sub['default'] = 'none'
        if option['id'] == 'formatterChoice':
            option['description'] = 'Tam’s display styles. Full rseMatched exposes Redhair custom-format matches. None retains your formatter. Some decorative Tam-specific tags do not apply to Redhair.'
    slugs = sorted(p.name.removesuffix('.expressions.json') for p in PROFILES.glob('*.expressions.json'))
    movies = [s for s in slugs if not s.startswith('anime-')]
    anime = [s for s in slugs if s.startswith('anime-')]
    def label(s):
        return s.replace('-', ' ').title().replace('Hdr', 'HDR')
    inputs[:0] = [
        {'id':'profileNotice', 'type':'alert', 'intent':'info', 'name':'Redhair Quality Setup',
         'description':'Choose one movie/TV profile and optionally one anime profile. All patterns and scores are bundled from Redhair; internal regex names are isolated per profile. No Tam/Vidhin scoring or SELect pruning is applied. Reimport a rebuilt template for updates.'},
        {'id':'qualityProfile','name':'Movie / TV Quality Profile','type':'select','required':True,
         'description':'Select exactly one Redhair movie/TV profile. Scores do not impose hard resolution or size limits.',
         'default':'1080p-balanced','options':[{'value':s,'label':label(s)} for s in movies]},
        {'id':'animeProfile','name':'Anime Quality Profile','type':'select','required':True,
         'default':'anime-1080p','options':[{'value':'none','label':'Disabled'}]+[{'value':s,'label':label(s)} for s in anime],
         'description':'Independent of anime add-ons. Disabled removes anime scoring, not anime results.'},
        {'id':'qualitySort','name':'Quality Sort Order','type':'select','required':True,
         'default':'resolution-quality-score','options':[
             {'value':'resolution-quality-score','label':'Resolution → Quality → Redhair Score'},
             {'value':'score-first','label':'Redhair Score → Resolution → Quality'}],
         'description':'Cached streams come first. The default follows Redhair’s documented example; score-first allows format scores to outrank resolution/source. Anime uses SeaDex → Score.'},
        {'id':'maxResults','name':'Maximum Results','type':'number','default':0,'min':0,
         'description':'0 keeps all results. A positive number applies a final result limit.'},
    ]
    template['metadata'] = {'id':'custom.redhair.complete','name':'Redhair Quality — Complete Setup',
        'description':'Tam-style setup wizard with all 13 Redhair quality profiles. Choose one movie/TV and one optional anime profile; regex patterns, query guards and scores are preserved. Bundled profiles have isolated regex names to prevent cross-profile matching. Includes Tam’s optional add-on presets and formatter styles. No Tam/Vidhin ranking, SELect pruning or live profile sync. Community adaptation, not an official Redhair release.',
        'author':'Local adaptation','source':'custom','version':'1.0.0','category':'AIO','serviceRequired':False,'inputs':inputs}
    cfg['appliedTemplates'] = [{'id':'custom.redhair.complete','version':'1.0.0'}]
    cfg['addonDescription'] = 'AIOStreams with Redhair quality profiles and a Tam-style setup wizard.'
    # Explicit resets replace old scoring/filtering when applying over an existing setup.
    for key in list(cfg):
        if key.startswith('synced') or 'RegexPatterns' in key or key.endswith('StreamExpressions'):
            cfg[key] = []
    for kind in ['Excluded','Included','Required','Preferred','Ranked']:
        cfg[f'synced{kind}RegexUrls'] = []
        cfg[f'synced{kind}StreamExpressionUrls'] = []
    cfg['selOverrides'] = []
    cfg['regexOverrides'] = []
    cfg['preferredLanguages'] = ['{{inputs.languages}}','Original','Dual Audio','Multi','Dubbed','Unknown']
    cfg['preferredSubtitles'] = ['{{inputs.subtitles}}']
    cfg['preferredStreamTypes'] = []
    cfg['excludedVisualTags'] = []
    cfg['size'] = {}
    cfg['bitrate'] = {'useMetadataRuntime':True}
    cfg['variants'] = []
    cfg['enableSeadex'] = {'__switch':'inputs.animeProfile','cases':{'none':False},'default':True}
    cfg['resultLimits'] = {'mode':'conjunctive','global':{'__if':'inputs.maxResults > 0','__value':'{{inputs.maxResults}}'}}
    # Only explicit device exclusions survive from Tam's SEL filters.
    original = json.loads((ROOT / 'sources/tamtaro-complete.json').read_text())
    cfg['excludedStreamExpressions'] = [x for x in original['config']['excludedStreamExpressions'] if x.get('__if','').startswith('inputs.deviceExclude includes ') and not any(t in x['expression'] for t in ('regexMatched(', 'rseMatched('))]
    for item in cfg['excludedStreamExpressions']:
        assert not any(word in item['expression'] for word in ('regexMatched(', 'selScore(', 'streamExpressionScore('))
    def criteria(keys): return [{'key':k,'direction':'desc'} for k in keys]
    regular = {'__switch':'inputs.qualitySort','cases':{
        'score-first':criteria(['cached','streamExpressionScore','resolution','quality','seeders'])},
        'default':criteria(['cached','resolution','quality','streamExpressionScore','seeders'])}
    cfg['sortCriteria'] = {'global':regular,'series':[],
        'anime':criteria(['cached','seadex','streamExpressionScore','resolution','quality','seeders']),
        'cached':[],'uncached':[], 'movies':[], 'cachedMovies':[], 'uncachedMovies':[],
        'cachedSeries':[], 'uncachedSeries':[], 'cachedAnime':[], 'uncachedAnime':[]}
    for slug in slugs:
        regexes = json.loads((PROFILES / f'{slug}.regexes.json').read_text())
        expressions = json.loads((PROFILES / f'{slug}.expressions.json').read_text())
        names = {r['name']:f'{slug}::{r["name"]}' for r in regexes}
        assert len(names) == len(regexes), f'Duplicate regex names in {slug}'
        for r in regexes: r['name'] = names[r['name']]
        for e in expressions: e['expression'] = rename_references(e['expression'], names)
        condition = f'inputs.{"animeProfile" if slug.startswith("anime-") else "qualityProfile"} == {slug}'
        cfg['rankedRegexPatterns'].append({'__if':condition,'__value':regexes})
        cfg['rankedStreamExpressions'].append({'__if':condition,'__value':expressions})
    # Guard against retained wizard controls pointing at removed sections.
    declared = set()
    def collect(options, prefix=''):
        for o in options:
            declared.add(prefix+o['id'])
            collect(o.get('subOptions',[]), prefix+o['id']+'.')
    collect(inputs)
    refs = set(re.findall(r'inputs\.([\w.]+)', json.dumps(template)))
    assert not refs-declared, refs-declared
    return template


def build():
    template = build_custom()
    supplied = json.loads((ROOT / 'sources/redhair-default-config.json').read_text())
    original = copy.deepcopy(supplied)
    # Credentials are collected by AIOStreams' service wizard, never overwritten by empty exports.
    supplied.pop('services', None)
    supplied['appliedTemplates'] = [{'id':'custom.redhair.complete', 'version':'1.1.0'}]
    supplied['presets'] = {'__if':'inputs.importExportAddons', '__value': supplied['presets']}
    # Clear the prior template's fields absent from the export, so old scoring cannot stack.
    for key in template['config']:
        if key not in supplied and (key.startswith('synced') or 'RegexPatterns' in key or key.endswith('StreamExpressions')):
            supplied[key] = []
    supplied['bitrate'] = {'useMetadataRuntime':True}
    supplied['variants'] = []
    custom = template['config']
    template['config'] = {key: {'__switch':'inputs.setupMode',
        'cases':{'custom':custom.get(key, {'__remove':True})},
        'default':supplied.get(key, {'__remove':True})}
        for key in sorted(set(custom) | set(supplied))}
    template['config']['appliedTemplates'] = supplied['appliedTemplates']
    for option in template['metadata']['inputs']:
        prior = option.get('__if')
        option['__if'] = 'inputs.setupMode == custom' + (f' and {prior}' if prior else '')
    template['metadata']['inputs'][:0] = [
        {'id':'setupMode','name':'Setup Defaults','description':'Use the supplied Redhair configuration, or customize the previous bundled-profile wizard.',
         'type':'select','required':True,'default':'redhair','options':[
             {'value':'redhair','label':'Redhair supplied configuration (default)'},
             {'value':'custom','label':'Custom bundled-profile wizard'}]},
        {'id':'exportNotice','name':'Redhair supplied defaults','type':'alert','intent':'info',
         '__if':'inputs.setupMode == redhair',
         'description':'2160p Remux + Anime Remux 1080p, synced from Redhair. Uses the supplied filters, score overrides, sorting, formatter and result limits. Choose services and enter credentials separately. Local indexer addresses require your own connection URLs. Disabled custom add-on URLs have been replaced with placeholders.'},
        {'id':'importExportAddons','name':'Import Redhair add-ons','type':'boolean','default':True,
         '__if':'inputs.setupMode == redhair',
         'description':'Import the supplied add-on list (including TorBox/AIOStreams assignments and indexer URL placeholders). Disable to keep your current add-ons. Enter missing keys and connection URLs in AIOStreams.'},
    ]
    template['metadata']['version'] = '1.1.0'
    template['metadata']['description'] = 'Defaults to the supplied Redhair configuration: synced 2160p Remux and Anime Remux 1080p, its filters, scores, sorting, formatter and limits. Service credentials are entered separately. Optional custom mode retains the earlier Tam-style bundled-profile wizard. Encoded custom add-on URLs are replaced with placeholders. Community adaptation, not an official Redhair release.'
    output = ROOT / 'Redhair-complete-setup-template.json'
    output.write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {output.name} v1.1.0')

if __name__ == '__main__': build()
