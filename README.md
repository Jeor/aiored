# aiored — Redhair Quality Setup

Version **1.3.0** uses the supplied Redhair configuration as its defaults, with independently selectable sections. Unselected sections are omitted from the update and preserve your existing settings.

## Import URL

Use this in **AIOStreams → Save & Install → Import Template → URL**, or in your instance’s **Template URLs** setting:

```text
https://raw.githubusercontent.com/Jeor/aiored/main/Redhair-complete-setup-template.json
```

Featured template ID: `custom.redhair.complete`.

Refresh/reimport the template to load version 1.3.0. Updating GitHub does not automatically reapply settings to an installed user configuration.

## Choose what to apply

The wizard’s **What to apply** menu offers:

- **Full setup (Redhair defaults)** — the default; applies all ten sections below.
- **SEL / regex only** — updates all stream expressions, regex patterns, synced profile URLs and score overrides. Keeps add-ons, formatter, sorting, basic filters, result limits, matching, playback and other settings unchanged.
- **Choose sections** — exposes ten independent on/off switches. On applies Redhair’s defaults for that section; off preserves your current values. Switching every section off leaves settings unchanged apart from recording the template version.

| Section | Settings applied when enabled |
| --- | --- |
| SEL and regex | All expression/regex lists, synced URLs, SEL overrides and regex overrides |
| Basic filters | Resolution, quality, language, audio/video, keywords, cached/uncached and other basic filtering |
| Sorting | All global, cached/uncached, movie, series and anime sort orders |
| Result, size and bitrate limits | Result counts, file-size ranges and bitrate settings |
| Add-ons, catalogs and fetching | Add-on list, categories, catalog modifications, groups and dynamic fetching |
| Formatter and posters | Stream formatter and poster service selection |
| Metadata matching and SeaDex | Year/title/episode matching, language inference and SeaDex enablement |
| Deduplication | Duplicate handling settings |
| Playback, downloads and failover | Autoplay, preloading, cache-and-play, owned checks, failover and service wrapping |
| Statistics and errors | Statistics and hidden error resources |

Add-on-dependent catalog/fetching settings stay in the same section so an SEL update cannot accidentally replace them. If you enable a section, it replaces that section’s settings, including your own custom edits in that section. In particular, **SEL / regex only replaces custom SEL and regex edits**, but does not change your sorting; keep Stream Expression Score in your existing sort order to use the scores.

## Formatter choices

When the formatter section is enabled, choose **Redhair (default)**, **Jeormatter**, **Jeormatter Alt**, or **Jeormatter Filename**. The three Jeormatter layouts come from [Jeor/formatter](https://github.com/Jeor/formatter), with the title placement, technical/audio lines, source information, status icons and optional final filename line preserved.

Their old named release-tier checks are removed. The status line uses Redhair’s actual Best/Tier rules:

- SeaDex Best → **🌊 Best**; other SeaDex recommendations → **🌊 Tier 1**, taking priority over score labels.
- Normalized SEL score: **95–100 Best**, **80–94 Tier 1**, **60–79 Tier 2**, **40–59 Tier 3**, **20–39 Tier 4**, **5–19 Tier 5**, **0–4 Subpar**.
- When normalized score data is unavailable, the adapted layouts omit the score badge.

`nSeScore` is relative to the highest positive SEL score in the result set; “Best” is a ranking label, not an absolute quality guarantee. The raw SEL score remains visible. iTunes/Movies Anywhere indicators now use Redhair’s `iT`/`MA` and enhancement-expression labels. Redhair’s own formatter is preserved unchanged.

The selector is hidden for SEL-only imports and when the formatter section is off. Standalone formatter JSONs are also available in [formatters/](formatters/). Rendered fixture previews are in [validation/formatter-previews.json](validation/formatter-previews.json).

## Proxy, services and credentials

**The main template contains no proxy configuration.** It never enables, disables or overwrites an existing proxy. It also never imports service credentials, service selections, account trust, add-on branding or user variants. The service-selection step is skipped to avoid AIOStreams implicitly replacing services during a partial update. For a new installation, configure services separately in AIOStreams.

If an older template import already enabled the unwanted proxy, disable or correct it once in AIOStreams. Omitting proxy settings from new imports preserves the current state; it does not repair a previously saved proxy automatically.

The original uploaded export is not published. `sources/redhair-default-config.json` is a sanitized snapshot, with the proxy configuration removed. Encoded custom manifest URLs and local indexer URLs are replaced with placeholders. Missing add-on credentials and complete connection URLs must be entered in AIOStreams. If the add-ons section is off, its placeholders are omitted too, so an SEL-only update does not prompt for add-on credentials.

The add-on defaults include TorBox/AIOStreams assignments. Applying them requires those services and your own reachable indexer connections. Existing services are preserved rather than automatically configured.

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
python scripts/build_template.py
node --experimental-strip-types validation/verify-sections.mjs
npm ci --ignore-scripts --prefix validation/formatter
validation/formatter/node_modules/.bin/tsc -p validation/formatter/tsconfig.json
node --experimental-strip-types validation/verify-formatters.mjs
npm ci --ignore-scripts --prefix validation/sel
npm run build --prefix validation/sel
node --experimental-strip-types validation/verify.mjs
```

Section validation uses AIOStreams’ actual conditional processor and the same top-level merge behavior as its import wizard. It checks all **1,024 section combinations**, unchanged full defaults, SEL-only and all-off imports, preservation of existing proxy/services/variants, and absence of add-on credential prompts when add-ons are skipped. The schema and optional bundled wizard retain their 198 configuration combinations and 95,904 expression comparisons. Results are in `validation/section-results.json` and `validation/results.json`.

Formatter checks additionally render 51 threshold/SeaDex cases using AIOStreams’ formatter engine, check layout preservation and source-label mapping, and verify all four choices respect the formatter section switch. Results are in `validation/formatter-results.json`.

These are local checks; a live import/playback test against your instance has not been performed.

## Attribution

[Redhair777/AIO-Quality-Profiles](https://github.com/Redhair777/AIO-Quality-Profiles) provides the profiles and verification infrastructure. [Tam-Taro/SEL-Filtering-and-Sorting](https://github.com/Tam-Taro/SEL-Filtering-and-Sorting) provides the optional wizard’s setup structure. [Viren070/AIOStreams](https://github.com/Viren070/AIOStreams) provides the template processor, schema and evaluator. Snapshot commits are in `sources/provenance.json`. This is a community adaptation, not an official release by those authors.
