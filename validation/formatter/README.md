# Formatter engine verification

`vendor/` copies AIOStreams’ formatter engine and its utility dependencies from the `aiostreams` commit recorded in `sources/provenance.json`. `utils/constants.ts` contains only the verbatim LANGUAGES constant needed by the language utilities. No runtime logic is stubbed or changed. See `../AIOStreams-LICENSE`.

```sh
npm ci --ignore-scripts --prefix validation/formatter
validation/formatter/node_modules/.bin/tsc -p validation/formatter/tsconfig.json
node --experimental-strip-types validation/verify-formatters.mjs
```

Fixtures use normalized parse values directly, exercising the actual parser/compiler without booting an AIOStreams instance. This does not replace a live client rendering test. Generated `dist/` and `node_modules/` are excluded from the repository.
