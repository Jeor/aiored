# aiored — Redhair Quality Setup

Version **1.5.0** starts from Redhair’s supplied configuration and lets you customize which sections, add-ons and formatter to apply.

## Import URL

Keep this URL in your instance’s **Template URLs** setting:

```text
https://raw.githubusercontent.com/Jeor/aiored/main/Redhair-complete-setup-template.json
```

The URL now provides one template: **Redhair Quality — Setup and updater** (`custom.redhair.full`). Use it for both new setups and selective updates. The separate partial-update template has been removed from the list.

Featured template ID: `custom.redhair.full`. Remove the old `custom.redhair.complete` featured ID if you added it. Refresh/reimport to load v1.5.0; GitHub changes do not automatically reapply your configuration.

The old direct full/update URLs remain compatibility aliases for the same updater and ID; they no longer expose different workflows.

## Four groups, one Options screen

Choose exactly which sections to apply. On replaces that section; off preserves your existing settings. The switches start on, using Redhair’s defaults.

| Group | Independent switches and controls |
| --- | --- |
| Quality and ranking | SEL / regex, basic filters, sorting, size / bitrate / result limits, metadata matching / SeaDex, deduplication |
| Add-ons and connections | Apply add-ons, choose individual add-ons, service assignments, timeout |
| Appearance | Apply formatter / posters, choose one of four formatters, see its preview |
| Playback and diagnostics | Apply playback / download / failover settings; apply statistics / error settings |

On the optional **Services** step, choose services for a new setup or click **Skip** to preserve existing accounts during an update. Quality, connections and playback controls open their settings dialogs. Appearance stays directly on the Options screen so choosing a formatter immediately changes the visible preview; no Save or reopening is needed. No additional wizard steps are added. Proxy settings, variants and account trust are omitted from the updater.

SEL-only updates preserve add-ons, formatter, sorting and every other section, but replace your custom SEL / regex edits. Keep Stream Expression Score in your existing sort order to use the updated scores.

## Customize add-ons and services

The default selection contains **9 non-Usenet add-ons**: Store, SeaDex, nekoBT, Torz, Debridio, Torrentio, Meteor, Comet and M-Fusion. All Usenet entries, including the AIOStreams Library entry, are off by default. Meteor’s Usenet option also defaults off and has its own opt-in switch. The remaining 11 entries are available as optional choices. Selected entries are enabled; deselected entries are omitted and do not prompt for connection details. Applying this section replaces the add-on list, catalogs, category colors, groups and fetching settings. Turn it off to preserve your own add-ons.

Choose **Use my enabled services** to let each add-on use the services it supports from your enabled accounts. This is the full-setup default, so the configuration works with your service selection instead of restricting it to Redhair’s accounts. **Redhair’s original service assignments** retains the original TorBox / AIOStreams / NZBDAV restrictions and is an optional alternative. Catalog customizations tied to those assignments are retained only in Redhair mode, and only for selected add-ons.

The default timeout is **4 seconds for Debridio and 5 seconds for every other bundled add-on**. Choosing **10, 20 or 30 seconds** applies that timeout to every selected add-on. Longer timeouts allow slower sources more time but can delay results. Each section description now lists the concrete Redhair settings it applies; switching the section off preserves your settings instead. The Credentials screen asks for your own required indexer endpoints, custom manifests and other add-on credentials. Select only the sources you intend to configure.

Service selection is separate from the section switches. **Click Skip on the Services step to preserve your existing services and credentials.** Leaving a configuration section off does not undo an explicit service selection. For an SEL-only update, skip services, leave SEL / regex on and switch off the other nine sections.

## Formatter choices

When the formatter section is enabled, choose **Redhair (default)**, **Jeormatter**, **Jeormatter Alt**, or **Jeormatter Filename**. The three Jeormatter layouts come from [Jeor/formatter](https://github.com/Jeor/formatter), with the title placement, technical/audio lines, source information, status icons and optional final filename line preserved.

Their old named release-tier checks are removed. The status line uses Redhair’s actual Best/Tier rules:

- SeaDex Best → **🌊 Best**; other SeaDex recommendations → **🌊 Tier 1**, taking priority over score labels.
- Normalized SEL score: **95–100 Best**, **80–94 Tier 1**, **60–79 Tier 2**, **40–59 Tier 3**, **20–39 Tier 4**, **5–19 Tier 5**, **0–4 Subpar**.
- When normalized score data is unavailable, the adapted layouts omit the score badge.

`nSeScore` is relative to the highest positive SEL score in the result set; “Best” is a ranking label, not an absolute quality guarantee. The raw SEL score remains visible. iTunes/Movies Anywhere indicators now use Redhair’s `iT`/`MA` and enhancement-expression labels. Redhair’s own formatter is preserved unchanged.

The selector is hidden for SEL-only imports and when the formatter section is off. Standalone formatter JSONs are also available in [formatters/](formatters/). [Compare all four formatter previews](FORMATTER-PREVIEWS.md). The same rendered samples appear under the formatter selector; selecting a style changes its preview. These use a fictional stream and actual formatter-engine output, with client-dependent fonts and wrapping.

## Proxy and credentials

The updater contains proxy configuration or saved API keys. Existing proxy settings are preserved. If an earlier import enabled an unwanted proxy, disable or correct it once in AIOStreams.

The original uploaded export is not published. `sources/redhair-default-config.json` is sanitized: proxy removed, encoded custom manifests and private indexer URLs replaced with placeholders. When you select services, the updater collects your own credentials using AIOStreams’ native credential screen. Clicking Skip preserves existing services and credentials.

## Redhair defaults

The default quality profiles remain **2160p Remux** and **Anime Remux 1080p**, synced from Redhair’s original public URLs. Their live upstream scoring, the supplied inline language scores (Original/English/Tamil), all nine SEL overrides, bitrate and low-score exclusion expressions, sorting, formatter and limits are retained in the relevant sections.

The supplied result limits are conjunctive: **3 per service, 3 per resolution, 4 per quality**. Uncached results are excluded by the basic filters section. Live sync can change scores over time. The supplied configuration’s same-name regex behavior is preserved; this template does not rename synced patterns.

Only a selected section clears its obsolete inline or synced rules. This prevents the earlier bundled configuration from stacking with Redhair’s rules while preserving unselected customizations.

## Optional bundled-profile wizard

The earlier 13-profile Tam-style wizard is available separately:

```text
https://raw.githubusercontent.com/Jeor/aiored/main/Redhair-custom-profile-template.json
```

Its ID is `custom.redhair.profiles`. See [BUNDLED-PROFILES.md](BUNDLED-PROFILES.md). It is a fixed snapshot and a separate full-profile workflow, not the section-based update template. It has normal service onboarding. Do not apply it on top of the main template expecting a partial update.

Your instance must allow the selected regexes/SEL sources. If it reports expression-size errors, an administrator must adjust its limits. All optional bundled-mode selections fit these previously documented settings:

```dotenv
MAX_STREAM_EXPRESSIONS_TOTAL_CHARACTERS=150000
MAX_SEL_LENGTH=8000
```

## Rebuild and validate

```sh
npm ci --ignore-scripts --prefix validation/formatter
validation/formatter/node_modules/.bin/tsc -p validation/formatter/tsconfig.json
npm ci --ignore-scripts --prefix validation/sel
python scripts/build_template.py
node --experimental-strip-types validation/verify-frontend.mjs
node --experimental-strip-types validation/verify-preview-selection.mjs
node --experimental-strip-types validation/verify-sections.mjs
node --experimental-strip-types validation/verify-formatters.mjs
npm run build --prefix validation/sel
node --experimental-strip-types validation/verify.mjs
```

Section validation uses AIOStreams’ actual conditional processor and top-level merge behavior. It checks **1,024 section combinations**, **20 individual add-on selections**, empty selections, timeout controls, service routing, preserved Redhair quality defaults, SEL-only updates and skipped credentials. The template schema and the actual frontend wizard validator are checked, including dropdown value types and add-on availability inspection. Results are in `validation/section-results.json`.

Formatter checks render **51 threshold / SeaDex scenarios**, verify all four previews, layout preservation, source-label mapping and section isolation. The optional bundled-profile checks retain their 198 combinations and 95,904 expression comparisons. Results are in `validation/formatter-results.json` and `validation/results.json`.

These are local checks; a live import/playback test against your instance has not been performed.

## Attribution

[Redhair777/AIO-Quality-Profiles](https://github.com/Redhair777/AIO-Quality-Profiles) provides the profiles and verification infrastructure. [Tam-Taro/SEL-Filtering-and-Sorting](https://github.com/Tam-Taro/SEL-Filtering-and-Sorting) provides the optional wizard’s setup structure. [Viren070/AIOStreams](https://github.com/Viren070/AIOStreams) provides the template processor, schema and evaluator. Snapshot commits are in `sources/provenance.json`. This is a community adaptation, not an official release by those authors.
