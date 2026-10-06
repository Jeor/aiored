# Section defaults

An enabled section replaces its matching settings. Off preserves your current values.

## SEL and regex

Redhair defaults: live 2160p Remux + Anime Remux 1080p profiles, supplied Original/English/Tamil language scoring, exclusion expressions and nine score overrides. Replaces all SEL/regex lists and sync URLs, including your custom rules.

## Basic filters

Redhair defaults: exclude uncached streams, 240p/144p, CAM/SCR/TS/TC and 3D; prefer 2160p then 1080p, Remux/WEB-DL/WEBRip and debrid/Usenet. Digital-release filtering is enabled. Clears other basic filter lists to the supplied defaults.

## Sorting

Redhair defaults: cached first. Cached results prioritize library, resolution, quality, then SEL score; cached anime uses SeaDex then SEL score. Uncached order: stream type, seeders, matched expressions, SEL score, size. Replaces all sort orders.

## Result, size and bitrate limits

Redhair defaults: conjunctive caps of 3 results per service, 3 per resolution and 4 per quality; a stream must fit all caps. Global size range is 50 MB–100 GB for movies, series and anime; resolution-specific ranges also cap at 100 GB. Metadata runtime is used for bitrate calculation. SEL exclusions can impose additional limits.

## Add-ons, catalogs and fetching

Template default: 9 non-Usenet add-ons enabled. All Usenet entries and Meteor Usenet search are off; opt in below. This differs from Redhair’s supplied export, which enabled Usenet sources. Applying replaces the add-on list and catalog/category settings; dynamic fetching and groups are disabled. Customize the selection, service routing and timeouts below.

## Formatter

Redhair default: original Redhair stream layout. Choose a Jeormatter alternative below to change the layout while retaining Redhair Best/Tier scoring. Does not change poster settings.

## Poster settings

Redhair default: RPDB poster service. Applies poster settings independently of the stream formatter.

## Metadata matching and SeaDex

Redhair defaults: SeaDex enabled; year matching enabled with strict movie years and initial air dates; exact title matching for movies/series; strict season/episode matching. Episode-title matching request types and language-inference sources are empty.

## Deduplication

Redhair defaults: deduplicate by filename and info hash, per service for cached/uncached results, and a single result for P2P. Prefer library results. Duplicate merging and failover variants are enabled.

## Playback, downloads and failover

Redhair defaults: preload the first Usenet result; owned checks on; next-episode precaching and cache-and-play off. Failover supports Usenet/debrid across types, with 5 attempts and 1 in parallel, before limiting. Service wrapping is enabled for TorBox. Autoplay matching attributes: resolution, quality, encode and visual tags.

## Statistics and errors

Redhair defaults: show add-on, filtering and timing statistics at the bottom. No resource errors are hidden.
