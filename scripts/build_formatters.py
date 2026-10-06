"""Adapt Jeormatter's data references without redesigning its layouts."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
STYLES = {'redhair':'Redhair (default)', 'jeormatter':'Jeormatter', 'jeormatter_alt':'Jeormatter Alt', 'jeormatter_filename':'Jeormatter Filename'}


def build_formatters():
    red = json.loads((ROOT/'sources/redhair-default-config.json').read_text())['formatter']['definitions']['custom']
    # Use the exact SeaDex/normalized-score thresholds from the supplied formatter.
    badge = red['description'].split('\n')[-1].split('{stream.library::istrue')[0]
    assert badge.startswith('{stream.seadexBest::istrue')
    assert all(f'::>={n}' in badge for n in (95,80,60,40,20,5))
    # Compact inline placement. Missing score data must not be labeled Subpar.
    badge = badge.replace('["','[" · ').replace('stream.seadex::isfalse::and::stream.nSeScore', 'stream.seadex::isfalse::and::stream.nSeScore::exists::and::stream.nSeScore')
    variants = {'redhair':red}
    for style in STYLES:
        if style == 'redhair':continue
        original = json.loads((ROOT/f'sources/jeormatter/{style}.json').read_text())
        adapted = {}
        for key,text in original.items():
            if '{stream.quality::~remux[' in text:
                start = text.index('{stream.quality::~remux[')
                end = text.index('{stream.visualTags::remove',start)
                text = text[:start] + text[end:]
            if '{stream.seadex::istrue[' in text:
                start = text.index('{stream.seadex::istrue[')
                end = text.index('{service.cached[',start)
                block = text[start:end]
                prefix = '{stream.seadex::istrue["{stream.seadexBest::istrue[" · ★ SD Best"||" · ☆ SD Alt"]}"||"'
                assert block.startswith(prefix) and block.endswith('"]}')
                fallback = block[len(prefix):-3]
                fallback = fallback.replace("::in('iTunes')", "::in('iT','iTunes Enhancement')")
                fallback = fallback.replace("::in('Movies Anywhere','MoviesAnywhere','MA')", "::in('MA','Movies Anywhere Enhancement')")
                # Same network/edition fallback as before, still hidden for SeaDex.
                text = text[:start] + badge + '{stream.seadex::istrue[""||"' + fallback + '"]}' + text[end:]
            adapted[key] = text
        assert not any(token in json.dumps(adapted) for token in ('Remux T1','HD Bluray T1','Web T1','SD Best','SD Alt'))
        assert adapted['description'].count('\n') == original['description'].count('\n')
        if style == 'jeormatter_filename':assert adapted['description'].endswith('\n{stream.filename}')
        variants[style] = adapted
    (ROOT/'formatters').mkdir(exist_ok=True)
    for style, value in variants.items():
        (ROOT/f'formatters/{style}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    return variants

if __name__ == '__main__': build_formatters()
