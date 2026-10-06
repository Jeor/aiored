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


# Every imported field belongs to exactly one selectable section.
SECTIONS = {
    'sel': ('SEL and regex', 'All stream expressions, regex patterns, synced URLs and score overrides. Replaces the selected section, including custom SEL edits.'),
    'filters': ('Basic filters', 'Resolution, quality, language, audio/video, keyword, cached-stream and other basic filters.'),
    'sorting': ('Sorting', 'All cached, uncached, movie, series and anime sort orders.'),
    'limits': ('Result, size and bitrate limits', 'Result counts, size ranges and bitrate settings.'),
    'addons': ('Add-ons, catalogs and fetching', 'Add-on list, category colors, catalogs, groups and dynamic fetching. Includes connection placeholders for your own endpoints.'),
    'formatter': ('Formatter and posters', 'Stream display formatter and poster service selection.'),
    'matching': ('Metadata matching and SeaDex', 'Year/title/episode matching, language inference and SeaDex enablement.'),
    'deduplication': ('Deduplication', 'Duplicate handling and grouping rules.'),
    'playback': ('Playback, downloads and failover', 'Autoplay, preloading, cache-and-play, owned checks, failover and service wrapping.'),
    'diagnostics': ('Statistics and errors', 'Statistics display and hidden error resources.'),
}


def section_for(key):
    if key.startswith('synced') or 'RegexPatterns' in key or key.endswith('StreamExpressions') or key in ('selOverrides','regexOverrides'):
        return 'sel'
    explicit = {
        'sorting': ['sortCriteria'],
        'limits': ['resultLimits','size','bitrate'],
        'addons': ['presets','addonCategoryColors','catalogModifications','mergedCatalogs','dynamicAddonFetching','groups'],
        'formatter': ['formatter','posterService','usePosterRedirectApi'],
        'matching': ['yearMatching','titleMatching','seasonEpisodeMatching','episodeTitleMatching','languageInference','enableSeadex'],
        'deduplication': ['deduplicator'],
        'playback': ['autoPlay','precacheNextEpisode','preloadStreams','cacheAndPlay','checkOwned','failover','serviceWrap'],
        'diagnostics': ['statistics','hideErrorsForResources'],
    }
    for section, keys in explicit.items():
        if key in keys: return section
    if key.startswith(('excluded','included','required','preferred','exclude','include')) or key in ('seederRangeTypes','ageRangeTypes','digitalReleaseFilter'):
        return 'filters'
    raise ValueError(f'Unassigned configuration field: {key}')


def build():
    # Retain the original profile wizard as a separate optional template.
    bundled = build_custom()
    bundled['metadata']['id'] = 'custom.redhair.profiles'
    bundled['metadata']['name'] = 'Redhair Quality — Bundled Profile Wizard'
    bundled['config']['appliedTemplates'] = [{'id':'custom.redhair.profiles','version':'1.0.0'}]
    bundled['config'].pop('proxy', None)
    (ROOT / 'Redhair-custom-profile-template.json').write_text(json.dumps(bundled,ensure_ascii=False,indent=2)+'\n')
    supplied = json.loads((ROOT / 'sources/redhair-default-config.json').read_text())
    # Never touch account credentials, proxy settings, trust or user variants.
    for key in ('services','proxy','trusted','showChanges','variants'):
        supplied.pop(key, None)
    # Clear old rules only when their own section is selected.
    for key in bundled['config']:
        if key not in supplied and (key.startswith('synced') or 'RegexPatterns' in key or key.endswith('StreamExpressions')):
            supplied[key] = []
    supplied['bitrate'] = {'useMetadataRuntime':True}
    section_fields = {section: [] for section in SECTIONS}
    config = {}
    for key, value in supplied.items():
        section = section_for(key)
        section_fields[section].append(key)
        condition = f'inputs.applyMode == full or inputs.applyMode == selected and inputs.sections.{section}'
        if section == 'sel': condition += ' or inputs.applyMode == selOnly'
        config[key] = {'__if':condition, '__value':value}
    config['appliedTemplates'] = [{'id':'custom.redhair.complete','version':'1.2.0'}]
    template = {'metadata': {
        'id':'custom.redhair.complete','name':'Redhair Quality — Complete Setup','version':'1.2.0',
        'description':'Redhair supplied defaults with independently selectable sections. Apply full setup, SEL/regex only, or selected sections. Unselected fields are omitted to preserve existing customizations. Never imports proxy settings, service credentials or variants. Default profiles: synced 2160p Remux and Anime Remux 1080p.',
        'author':'Local adaptation','source':'custom','category':'AIO',
        'services':[], 'serviceRequired':False,
        'inputs':[
            {'id':'applyMode','name':'What to apply','type':'select','required':True,'default':'full',
             'description':'Full setup applies Redhair’s defaults. SEL/regex only preserves everything else. Choose sections enables individual switches.',
             'options':[{'value':'full','label':'Full setup (Redhair defaults)'},{'value':'selOnly','label':'SEL / regex only'},{'value':'selected','label':'Choose sections'}]},
            {'id':'sections','name':'Sections to apply','type':'subsection','subsectionIntent':'inline',
             '__if':'inputs.applyMode == selected','description':'Enabled sections replace their current settings. Disabled sections stay exactly as they are.',
             'subOptions':[{'id':key,'name':name,'description':description,'type':'boolean','default':True} for key,(name,description) in SECTIONS.items()]},
            {'id':'notice','name':'Your existing connections are preserved','type':'alert','intent':'info',
             'description':'Proxy settings, service credentials and variants are never imported. Configure services separately for a new setup. Importing add-ons replaces the add-on list and may prompt for connection details. SEL/regex includes synced 2160p Remux + Anime Remux 1080p and Redhair’s score overrides.'},
        ]}, 'config':config}
    (ROOT / 'Redhair-complete-setup-template.json').write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n')
    (ROOT / 'validation/section-fields.json').write_text(json.dumps(section_fields,indent=2)+'\n')
    print(f'Built v1.2.0 with {len(SECTIONS)} independently selectable sections; proxy omitted.')

if __name__ == '__main__': build()
