# Optional bundled-profile wizard

Import **`Redhair-complete-setup-template.json`** into AIOStreams. This is a local adaptation of Tam’s complete setup wizard using all 13 profiles from Redhair’s AIO Quality Profiles repository. It is not an official release by either author.

This document describes **Custom bundled-profile wizard** mode, not the default supplied Redhair configuration. Select that mode during template import.

## Import

Paste this public URL into **Save & Install → Import Template → URL**:

```text
https://raw.githubusercontent.com/Jeor/aiored/main/Redhair-complete-setup-template.json
```

Or download the JSON and import from a file:

1. In AIOStreams, open **Save & Install → Import Template → Import from File** and select `Redhair-complete-setup-template.json`.
2. Load **Redhair Quality — Complete Setup** and select your services, or skip services for P2P.
3. Choose **one Movie / TV Quality Profile** and **one Anime Quality Profile**, or disable anime scoring.
4. Select languages, add-ons, formatter, and any device exclusions. To preserve existing add-ons, choose **None (Use Your Current Addons)**. Enter credentials in AIOStreams when prompted.
5. Load the template, review the resulting configuration, then save and install.

Defaults are **1080p Balanced + Anime 1080p**. All 11 movie/TV profiles and both anime profiles are available in the wizard; profiles in the same category are alternatives and must not be stacked.

This file has been tested locally, but has not been imported into your live AIOStreams instance or tested for playback. The selected instance must allow the required regexes and expression sizes below.

## Instance requirements

The bundled profiles use inline regex and SEL entries. Public hosts may restrict these. The current AIOStreams source defaults to 50,000 total expression characters and 3,000 characters per expression; these are too small for some bundled selections. A self-hosted instance can accommodate every selection in this snapshot with:

```dotenv
MAX_STREAM_EXPRESSIONS_TOTAL_CHARACTERS=150000
MAX_SEL_LENGTH=8000
```

Regex use must also be allowed for your account (for example, an administrator-approved trusted account or `REGEX_FILTER_ACCESS=all` on your own instance). No SEL sync permission is needed because this template has no remote profile sync URLs.

The largest possible selection, including every offered device exclusion, requires at most **126,056 expression characters** and **6,736 characters in one expression**. There are at most 401 expressions in a selection, but the inspected current server excludes ranked expressions from its 200-expression *count* check. Older versions or host-specific validation may differ. Instance restrictions cannot be bypassed by a template.

## What is preserved and what changes

| Area | Behavior |
| --- | --- |
| Setup experience | Tam’s service setup, optional add-on presets, language/subtitle choices, credentials, formatter choices, metadata matching, and deduplication settings |
| Quality rules | Redhair’s complete regex patterns, expression bodies, query-type guards, enabled flags, and numeric scores for the selected profiles |
| Regex isolation | Internal regex names and their SEL references are prefixed with the profile ID to prevent same-name patterns in movie/TV and anime profiles from affecting each other |
| Movie/TV sorting | Cached first, then resolution → quality → Redhair SEL score → seeders; optional score-first mode |
| Anime sorting | Cached first, then SeaDex → Redhair SEL score → resolution → quality → seeders |
| Result pruning | Tam’s SELect engine, score cutoffs, passthroughs, pins, quality boosts and backup logic are removed because they depend on a different scoring system |
| Optional limits | Final maximum result count and device exclusions; no automatic minimum-score cutoff |
| Sync | Bundled snapshot, not automatic upstream sync; rebuild and reimport for updates |

Selecting a profile does **not** impose a hard resolution cap, file-size range, or minimum acceptable score. Redhair’s exported files contain custom-format scoring, not a complete Radarr/Sonarr quality ladder and cutoff configuration. Negative scores lower ranking; they do not automatically exclude streams. The default resolution/quality-first sort can place a higher-resolution result ahead of a higher-scoring lower-resolution result; choose score-first if desired.

Anime scoring depends on AIOStreams classifying the request as `anime.movie` or `anime.series`. Disabling anime scoring does not hide anime streams or remove anime add-ons; the add-on wizard has a separate No Anime option.

Tam’s old Tam/Vidhin/French score sources, synced exclusions, SEL overrides, regex overrides, and variant presets are cleared. Hardcoded 100 GB / 250 Mbps limits and default 3D exclusion are removed. Preferred format lists remain as sort metadata, but the new sort order uses only the criteria listed above. Device exclusions that depended on Tam/Vidhin regex or named-expression matches are omitted. Tam’s display styles remain available, although some decorative tags specific to the old rules will no longer appear.

Import applies configuration changes, including filters and sorting. Existing add-ons and formatter can be retained using their wizard options. The template is designed to replace the previous quality configuration; it does not merge existing custom scoring into Redhair scores.

## Rebuild and verification

The `sources/` folder contains the exact input snapshots. `sources/provenance.json` records upstream commits. To regenerate without network access:

```sh
python scripts/build_template.py
```

To run validation with Node 22.6+:

```sh
npm ci --ignore-scripts --prefix validation/sel
npm run build --prefix validation/sel
node --experimental-strip-types validation/verify.mjs
```

Validation covers:

- 198 movie/TV, anime, service and sort combinations using AIOStreams’ actual template conditional processor.
- The upstream template metadata and wizard-input schema.
- Unchanged patterns, scores, flags, and expressions after reversing only the name prefixes.
- 95,904 original/adapted expression evaluations across four sample releases and all four query types, including opposite-category regex matches to test isolation.
- Optional device exclusions, result limits, retaining add-ons/formatter, and removal of stale sync URLs.

This is not an exhaustive release corpus or a live instance test. The SEL evaluator is the snapshot vendored by Redhair (upstream AIOStreams commit `6b9ee1c8eaf9fb200c69d083315a58bf4ea54018`); the template processor/schema are from the separate current AIOStreams commit recorded in provenance. `validation/results.json` records the latest successful run.

For updates, replace `sources/redhair/*.json` with a reviewed, consistent Redhair snapshot, update its provenance, rebuild, rerun validation, and reimport. The generator fails on unresolved regex references. Do not add the original Redhair sync URLs on top of the bundled entries: doing so would duplicate scores and undo name isolation.

## Sources and attribution

- [Tam-Taro’s complete template](https://github.com/Tam-Taro/SEL-Filtering-and-Sorting/blob/main/AIOStreams%20Templates/Tamtaro-complete-setup-template.json) — wizard, add-on presets, display styles and supporting settings.
- [Redhair777’s AIO Quality Profiles](https://github.com/Redhair777/AIO-Quality-Profiles) — regexes, SEL profiles and vendored evaluator verification infrastructure; sourced upstream from Dictionarry, Dumpstarr and trash-pcd as documented there.
- [AIOStreams](https://github.com/Viren070/AIOStreams) — template processor/schema and underlying evaluator.

The source snapshots and verification code retain their original attribution. No claim of ownership or endorsement is made over upstream work.
