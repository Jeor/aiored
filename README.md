# aiored — Redhair Quality Setup

Version **1.1.0** defaults to the Redhair configuration supplied by the repository owner. The existing template URL and featured ID are unchanged.

## Import

In **AIOStreams → Save & Install → Import Template → URL**, use:

```text
https://raw.githubusercontent.com/Jeor/aiored/main/Redhair-complete-setup-template.json
```

For the instance’s **Template URLs** setting, use the same URL. The **Featured template ID** is:

```text
custom.redhair.complete
```

Refresh/reimport the template and select **Redhair supplied configuration (default)**. Choose services and enter credentials in AIOStreams. Updating the repository does not automatically rewrite an already-installed user configuration.

## Default configuration

The supplied export is the source of truth for filters, sorting, formatter, matching, deduplication, score overrides, limits, add-on configuration and enabled/disabled states:

- Synced **2160p Remux** movie/TV profile and **Anime Remux 1080p** profile, using the original Redhair URLs.
- Original resolution, source-quality and visual-tag exclusions; uncached streams excluded.
- Original bitrate filter, conditional low-score exclusion, ongoing-season-pack filter, and disabled test expression.
- Original two inline language score expressions (Original/English/Tamil) and all nine SEL overrides.
- Original cached/uncached sorting, including SeaDex-first cached anime sorting.
- Conjunctive result limits: **3 per service, 3 per resolution, 4 per quality**.
- Original formatter, size limits, matching and playback settings.

The wizard defaults to importing the supplied add-ons. Turn **Import Redhair add-ons** off to retain your current add-on list. The supplied presets include TorBox/AIOStreams service assignments and indexer URL placeholders; those require your own corresponding services, credentials and reachable indexer instance. Missing add-on credentials must be entered in AIOStreams before those add-ons work.

## Credential handling and migration

The original uploaded export is **not** published. `sources/redhair-default-config.json` is the sanitized input snapshot.

Two disabled custom add-ons contained encoded configuration URLs. One decoded URL contained non-empty credential-like fields, so **both complete manifest URLs are replaced with optional placeholders**. Their disabled states are preserved. No encoded URL or its decoded contents are included in this repository.

Local NZBHydra endpoint URLs are also replaced with credential-input placeholders (required for enabled indexers, optional for disabled ones). Enter your complete indexer URL, including any desired indexer-selection query, in AIOStreams. Local hostnames and original endpoint query values are not published in the sanitized snapshot.

The export’s empty service credential objects are omitted from the generated template so service selection and credentials are handled by AIOStreams’ wizard. Filter/sync fields absent from the export are explicitly cleared when needed to prevent the previous bundled ranking system from stacking with the new defaults. The prior template’s extra bitrate caps and variants are cleared. No account keys are embedded.

The default intentionally retains the supplied sync URLs and overrides as provided; it does not apply the optional bundled mode’s regex-name isolation. Upstream profile updates can therefore change default-mode scores over time, and same-name patterns across upstream profiles retain the behavior of the supplied setup.

## Optional previous wizard

Select **Custom bundled-profile wizard** to use the previous 13-profile Tam-style wizard instead. Its options and limits are documented in [BUNDLED-PROFILES.md](BUNDLED-PROFILES.md). It remains a fixed snapshot and is not combined with the default synced configuration.

The instance must permit the selected mode’s regexes/SEL sources. If your host reports expression-size errors, its administrator must adjust the relevant limits. For all optional bundled-mode selections, the previously documented settings remain:

```dotenv
MAX_STREAM_EXPRESSIONS_TOTAL_CHARACTERS=150000
MAX_SEL_LENGTH=8000
```

## Rebuild and validate

```sh
python scripts/build_template.py
npm ci --ignore-scripts --prefix validation/sel
npm run build --prefix validation/sel
node --experimental-strip-types validation/verify.mjs
```

Validation compares every non-service field of the resolved default mode against the sanitized supplied configuration. It also checks service credential handling and add-on retention, validates the upstream template schema, and reruns the optional wizard’s 198 configuration combinations and 95,904 expression comparisons. Results are in `validation/results.json`.

This is local validation, not a live import or playback test of your instance. The supplied configuration’s live sync behavior and private add-on connectivity require the actual instance.

## Attribution

- [Redhair777/AIO-Quality-Profiles](https://github.com/Redhair777/AIO-Quality-Profiles): quality profiles and verification infrastructure.
- [Tam-Taro/SEL-Filtering-and-Sorting](https://github.com/Tam-Taro/SEL-Filtering-and-Sorting): the optional wizard’s setup structure and supporting settings.
- [Viren070/AIOStreams](https://github.com/Viren070/AIOStreams): template processor, schema and evaluator.

This is a community adaptation, not an official release by those authors. Original snapshot commits are recorded in `sources/provenance.json`.
