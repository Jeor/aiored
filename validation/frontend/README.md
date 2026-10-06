# AIOStreams frontend validation fixtures

`validator.ts` is an unmodified copy of `packages/frontend/src/lib/templates/validator.ts` from AIOStreams commit `d61b9e3735b133eeb683b18c3ef6c07c3e4b82da`.
`format-zod-error.ts` is copied from `packages/core/src/utils/format-zod-error.ts` at the same commit. See `../AIOStreams-LICENSE`.

`../verify-frontend.mjs` transpiles these files in memory and supplies their real schema, conditional-array reader and error formatter. Type-only dependencies are erased. It uses a fixture instance with the referenced add-on types enabled, then a second fixture with Torrentio unavailable to check accurate warnings. This does not connect to a live instance.

The frontend validator performs checks beyond the shared Zod schema: select option values must be strings, and the add-on availability pass inspects each raw conditional preset's `type` before resolving inputs. Before the v1.4.1 fix this test reproduced three timeout option errors and twenty `undefined` add-on warnings in each template.
