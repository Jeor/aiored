// Exact AIOStreams TemplateSchema / OptionDefinition closure; commit in sources/provenance.json.
export function makeTemplateSchema(z) {
const SERVICES = [
  'realdebrid',
  'debridlink',
  'premiumize',
  'alldebrid',
  'torbox',
  'easydebrid',
  'debrider',
  'putio',
  'pikpak',
  'offcloud',
  'seedr',
  'easynews',
  'nzbdav',
  'altmount',
  'stremio_nntp',
  'stremthru_newz',
  'aiostreams',
  'torrin',
];
const ServiceIds=z.enum(SERVICES);
const OptionDefinition = z.looseObject({
  id: z.string().min(1),
  name: z.string(),
  description: z.string(),
  showInSimpleMode: z.boolean().optional(),
  advanced: z.boolean().optional(),
  emptyIsUndefined: z.boolean().optional(),
  type: z.enum([
    'string',
    'password',
    'number',
    'boolean',
    'select',
    'select-with-custom',
    'multi-select',
    'url',
    'alert',
    'socials',
    'oauth',
    'subsection',
    'custom-nntp-servers',
    'nab-endpoint',
  ]),
  nab: z
    .object({
      namespace: z.enum(['newznab', 'torznab']),
      preset: z.string().min(1),
    })
    .optional(),
  oauth: z
    .object({
      authorisationUrl: z.string().url(),
      oauthResultField: z.object({
        name: z.string().min(1),
        description: z.string().min(1),
      }),
    })
    .optional(),
  required: z.boolean().optional(),
  default: z.any().optional(),
  forced: z.any().optional(),
  options: z
    .array(
      z.object({
        value: z.any(),
        label: z.string().min(1),
        // for 'nab-endpoint': where this indexer shows the user their api key
        apiKeyUrl: z.string().url().optional(),
      })
    )
    .optional(),
  get subOptions() {
    return z.array(OptionDefinition).optional();
  },
  intent: z
    .enum([
      'alert',
      'info',
      'success',
      'warning',
      'info-basic',
      'success-basic',
      'warning-basic',
      'alert-basic',
    ])
    .optional(),
  subsectionIntent: z
    .enum(['default', 'block', 'inline', 'pill', 'link', 'banner'])
    .optional(),
  buttonIntent: z.string().optional(),
  socials: z
    .array(
      z.object({
        id: z.enum([
          'website',
          'github',
          'discord',
          'ko-fi',
          'patreon',
          'buymeacoffee',
          'github-sponsors',
          'donate',
        ]),
        url: z.string().url(),
      })
    )
    .optional(),
  constraints: z
    .object({
      min: z.number().min(1).optional(), // for string inputs, consider this the minimum length.
      max: z.number().min(1).optional(), // and for number inputs, consider this the minimum and maximum value.
      forceInUi: z.boolean().optional(), // if true, the UI components will enforce these constraints.
    })
    .optional(),
});

const TemplateSchema = z.object({
  metadata: z.object({
    id: z
      .string()
      .min(1)
      .max(100)
      .optional()
      .transform((val) => val ?? crypto.randomUUID()),
    name: z.string().min(1).max(100), // name of the template
    description: z.string().min(1).max(1000), // description of the template
    author: z.string().min(1).max(20), // author of the template
    source: z
      .enum(['builtin', 'custom', 'external', 'community'])
      .optional()
      .default('builtin'),
    version: z
      .stringFormat('semver', /^[0-9]+\.[0-9]+\.[0-9]+$/)
      .optional()
      .default('1.0.0'),
    category: z.string().min(1).max(20), // category of the template
    tags: z.array(z.string().min(1).max(20)).max(5).optional(), // multi-tag; `category` stays as the single-tag fallback
    services: z.array(ServiceIds).optional(),
    serviceRequired: z.boolean().optional(), // whether a service is required for this template or not.
    setToSaveInstallMenu: z.boolean().optional().default(true), // whether to set the menu to save-install after importing the template
    sourceUrl: z.url().optional(), // URL from which the template was imported (for auto-updates)
    inputs: z.array(OptionDefinition).optional(), // template-creator-defined options shown to the user before loading
    changelog: z
      .array(
        z.object({
          date: z.string(),
          version: z.string(),
          content: z.string(),
        })
      )
      .optional(), // version history entries for tracking updates applied by users
    changelogUrl: z.url().optional(), // URL to a remote CHANGELOG.md file (alternative to inline changelog)
  }),
  config: z.any(),
});


return TemplateSchema;
}
