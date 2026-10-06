"""Build a Tam-style wizard with isolated, unmodified Redhair scoring semantics."""
import copy
from build_formatters import build_formatters, STYLES
import json
import re
import subprocess
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
    'sel': ('SEL and regex', 'Redhair defaults: live 2160p Remux + Anime Remux 1080p profiles, supplied Original/English/Tamil language scoring, exclusion expressions and nine score overrides. Replaces all SEL/regex lists and sync URLs, including your custom rules.'),
    'filters': ('Basic filters', 'Redhair defaults: exclude uncached streams, 240p/144p, CAM/SCR/TS/TC and 3D; prefer 2160p then 1080p, Remux/WEB-DL/WEBRip and debrid/Usenet. Digital-release filtering is enabled. Clears other basic filter lists to the supplied defaults.'),
    'sorting': ('Sorting', 'Redhair defaults: cached first. Cached results prioritize library, resolution, quality, then SEL score; cached anime uses SeaDex then SEL score. Uncached order: stream type, seeders, matched expressions, SEL score, size. Replaces all sort orders.'),
    'limits': ('Result, size and bitrate limits', 'Redhair defaults: conjunctive caps of 3 results per service, 3 per resolution and 4 per quality; a stream must fit all caps. Global size range is 50 MB–100 GB for movies, series and anime; resolution-specific ranges also cap at 100 GB. Metadata runtime is used for bitrate calculation. SEL exclusions can impose additional limits.'),
    'addons': ('Add-ons, catalogs and fetching', 'Redhair defaults: 14 enabled add-ons, with 6 disabled entries offered as optional choices below. Applying replaces the add-on list and catalog/category settings; dynamic fetching and groups are disabled. Customize the selection, service routing and timeouts below.'),
    'formatter': ('Formatter and posters', 'Redhair defaults: original Redhair stream layout and RPDB poster service. The Jeormatter alternatives below change the stream layout while retaining Redhair Best/Tier scoring; the poster choice remains RPDB.'),
    'matching': ('Metadata matching and SeaDex', 'Redhair defaults: SeaDex enabled; year matching enabled with strict movie years and initial air dates; exact title matching for movies/series; strict season/episode matching. Episode-title matching request types and language-inference sources are empty.'),
    'deduplication': ('Deduplication', 'Redhair defaults: deduplicate by filename and info hash, per service for cached/uncached results, and a single result for P2P. Prefer library results. Duplicate merging and failover variants are enabled.'),
    'playback': ('Playback, downloads and failover', 'Redhair defaults: preload the first Usenet result; owned checks on; next-episode precaching and cache-and-play off. Failover supports Usenet/debrid across types, with 5 attempts and 1 in parallel, before limiting. Service wrapping is enabled for TorBox. Autoplay matching attributes: resolution, quality, encode and visual tags.'),
    'diagnostics': ('Statistics and errors', 'Redhair defaults: show add-on, filtering and timing statistics at the bottom. No resource errors are hidden.'),
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
    formatter_variants = build_formatters()
    supplied['formatter'] = {'__switch':'inputs.formatterStyle',
        'cases':{key:{'id':'custom','definitions':{'custom':value}} for key,value in formatter_variants.items()},
        'default':supplied['formatter']}
    subprocess.run(['node', str(ROOT/'scripts/render_previews.mjs')], check=True)
    previews = json.loads((ROOT/'validation/formatter-previews.json').read_text())
    section_fields = {section: [] for section in SECTIONS}
    groups = {
        'quality': ('Quality and ranking', ['sel','filters','sorting','limits','matching','deduplication']),
        'connections': ('Add-ons and connections', ['addons']),
        'display': ('Appearance', ['formatter']),
        'behavior': ('Playback and diagnostics', ['playback','diagnostics']),
    }
    paths = {section: f'{group}.{section}' for group,(_,sections) in groups.items() for section in sections}
    paths['formatter'] = 'formatterEnabled'
    original_presets = copy.deepcopy(supplied['presets'])
    selected_default = [p['instanceId'] for p in original_presets if p['enabled']]
    presets = []
    for preset in original_presets:
        preset = copy.deepcopy(preset)
        preset['enabled'] = True
        # Only selected add-ons reach the credential collector. Newly enabled
        # custom/indexer connections must supply their own endpoint as well.
        preset = json.loads(json.dumps(preset).replace('<optional_template_placeholder>', '<template_placeholder>'))
        options = preset['options']
        if 'services' in options:
            options['services'] = {'__if':'inputs.connections.routing == redhair', '__value':options['services']}
        options['timeout'] = {'__switch':'inputs.connections.timeout', 'cases':{'original':options['timeout'], '10000':10000, '20000':20000, '30000':30000},
                              'default':options['timeout']}
        # Availability validation reads type before resolving conditionals.
        # Keep the preset fields beside __if rather than inside __value.
        presets.append({'__if':f"inputs.connections.addonIds includes {preset['instanceId']}", **preset})
    supplied['presets'] = presets
    supplied['catalogModifications'] = [
        {'__if':f"inputs.connections.addonIds includes {'2d1' if c['addonName']=='Library' else '6fd'} and inputs.connections.routing == redhair", '__value':c}
        for c in supplied['catalogModifications']]
    templates = []
    for is_full in (True, False):
        template_id = 'custom.redhair.full' if is_full else 'custom.redhair.complete'
        def active(section):
            condition = f'inputs.{paths[section]}'
            if not is_full:
                condition = 'inputs.applyMode != selOnly and ' + condition
                if section == 'sel': condition += ' or inputs.applyMode == selOnly'
            return condition
        config = {}
        for key,value in supplied.items():
            section = section_for(key)
            if is_full: section_fields[section].append(key)
            config[key] = {'__if':active(section),'__value':value}
        config['appliedTemplates'] = [{'id':template_id,'version':'1.4.2'}]
        inputs = []
        if not is_full:
            inputs.append({'id':'applyMode','name':'What to update','type':'select','required':True,'default':'selOnly',
                'description':'SEL / regex only preserves all other settings. Choose sections to update more; every switch remains editable.',
                'options':[{'value':'selOnly','label':'SEL / regex only'},{'value':'selected','label':'Choose sections (Redhair defaults)'}]})
        inputs.append({'id':'notice','name':'Customize before applying','type':'alert','intent':'info',
            'description':('Choose your services in the Services step, then customize the four groups below. Switch off any section to preserve it. For SEL-only updates, choose the Update existing setup template instead. Service selection is applied separately from these section switches.' if is_full else
            'Your services and credentials are preserved. Enabled sections replace their existing settings; disabled sections stay unchanged. For service onboarding, choose Full setup instead.') + ' Proxy settings and user variants are always preserved.'})
        for group,(name,sections) in groups.items():
            sub=[{'id':key,'name':'Apply '+SECTIONS[key][0],'description':SECTIONS[key][1]+' Off keeps your current settings.','type':'boolean','default':True} for key in sections]
            if group == 'connections':
                sub.extend([
                    {'id':'addonIds','name':'Add-ons to include','type':'multi-select','default':selected_default,
                     '__if':active('addons'),'description':'Default selection: '+', '.join(p['options']['name'] for p in original_presets if p['enabled'])+'. Optional (off by default): '+', '.join(p['options']['name'] for p in original_presets if not p['enabled'])+'. Selected entries replace the add-on list; deselected entries do not request credentials. Supply your own endpoints on the Credentials screen.',
                     'options':[{'value':p['instanceId'],'label':p['options']['name']+(' (optional)' if not p['enabled'] else '')} for p in original_presets]},
                    {'id':'routing','name':'Add-on service assignments','type':'select','default':'enabled' if is_full else 'redhair',
                     '__if':active('addons'),'description':'Use my enabled services (Full setup default): each add-on uses your enabled accounts that it supports. Redhair assignments (Update default): Store/Meteor → TorBox; Library, Althub, U-Crawler, N-Central, T-Rasa and D-Slug → AIOStreams; Indexarr → NZBDAV. Other add-ons have no explicit service restriction. Redhair’s Library/Store catalog customizations apply only in Redhair mode. This controls add-on routing, not your saved accounts.',
                     'options':[{'value':'enabled','label':'Use my enabled services (recommended for new setup)'},{'value':'redhair','label':'Redhair’s original service assignments'}]},
                    {'id':'timeout','name':'Add-on timeout','type':'select','default':'original',
                     '__if':active('addons'),'description':'Redhair defaults: Debridio waits up to 4 seconds; every other bundled add-on waits up to 5 seconds. The 10 / 20 / 30 second choices give every selected add-on that same timeout. Longer waits can include slower sources but may delay results. This does not change playback timeouts.',
                     'options':[{'value':'original','label':'Redhair: Debridio 4s, all others 5s'},{'value':'10000','label':'10 seconds for every selected add-on'},{'value':'20000','label':'20 seconds for every selected add-on'},{'value':'30000','label':'30 seconds for every selected add-on'}]},
                ])
            if group == 'display':
                sub.append({'id':'formatterStyle','name':'Formatter style','type':'select','required':True,'default':'redhair',
                    '__if':active('formatter'),'description':'Preview updates when you select a style. Redhair (default): multi-line name with source, resolution, score and size. Jeormatter: title as the name, compact technical details below. Alt: quality as the name, title below. Filename: Jeormatter plus the complete filename. All use Redhair’s Best/Tier scoring.',
                    'options':[{'value':key,'label':label} for key,label in STYLES.items()]})
                for style,preview in previews.items():
                    sub.append({'id':'preview_'+style,'type':'alert','intent':'info-basic','name':STYLES[style]+' preview',
                        '__if':active('formatter')+f' and inputs.formatterStyle == {style}',
                        'description':'**Stream name**\n'+preview['name']+'\n\n**Stream description**\n'+preview['description']+'\n\nSample cached 4K Remux, normalized score 95. Client wrapping may differ. [Compare all four previews](https://github.com/Jeor/aiored/blob/main/FORMATTER-PREVIEWS.md).'})
            if group == 'display':
                # Subsection dialogs buffer local edits until Save. Keep the
                # selector and conditional previews at wizard level so they
                # respond to the same onValuesChange event immediately.
                header={'id':'appearanceHeader','name':'Appearance','type':'alert','intent':'info-basic',
                        'description':'Choose a formatter and view its sample here without opening a settings dialog.'}
                sub[0]['id']='formatterEnabled'
                if not is_full:
                    header['__if']='inputs.applyMode != selOnly'
                    sub[0]['__if']='inputs.applyMode != selOnly'
                inputs.extend([header, *sub])
                continue
            option={'id':group,'name':name,'type':'subsection','subsectionIntent':'inline',
                'description':'Enable the sections you want to replace; switch off anything you want to keep.', 'subOptions':sub}
            if not is_full: option['__if']='inputs.applyMode != selOnly'
            inputs.append(option)
        # Formatter choice is a top-level control for immediate preview updates.
        config['formatter']['__value']['__switch']='inputs.formatterStyle'
        metadata={'id':template_id,'name':'Redhair Quality — '+('Full setup' if is_full else 'Update existing setup'),
            'version':'1.4.2','description':('Customizable Redhair defaults with service onboarding, add-on selection and four formatter previews.' if is_full else
                'Safely update SEL / regex only or selected sections while preserving services, credentials and unselected customizations.'),
            'author':'Local adaptation','source':'custom','category':'AIO','serviceRequired':False,'inputs':inputs}
        if not is_full: metadata['services']=[]
        templates.append({'metadata':metadata,'config':copy.deepcopy(config)})
    # AIOStreams supports arrays at template URLs. Keep the established URL so
    # existing installations discover both workflows without changing settings.
    (ROOT/'Redhair-complete-setup-template.json').write_text(json.dumps(templates,ensure_ascii=False,indent=2)+'\n')
    for template,filename in zip(templates,('Redhair-full-setup-template.json','Redhair-update-template.json')):
        (ROOT/filename).write_text(json.dumps(template,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'validation/section-fields.json').write_text(json.dumps(section_fields,indent=2)+'\n')
    (ROOT/'validation/section-inputs.json').write_text(json.dumps(paths,indent=2)+'\n')
    print('Built v1.4.2: full setup + safe updates, four settings groups and immediate formatter previews.')

if __name__ == '__main__': build()
