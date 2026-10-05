# Visual design

SLAIF Asset Reservation uses the same visual language as the SLAIF public
sites: a cream background, dark teal headings, blue actions, lime highlights
and pale blue panels. Member, management and administration pages share
local typography and a consistent hierarchy.

## Navigation and responsive layout

The header identifies the service and separates member actions from staff
management and administration. On narrow screens, the **Menu** button opens
navigation; Escape closes it and returns focus to the button. Login and
Administration remain visible on the public entry pages.

Forms retain visible labels, nearby field explanations and explicit warnings
for high-impact actions. Wide tables scroll inside a labelled, keyboard-focusable
region rather than widening the page. Table headers and native table semantics
remain available to assistive technology.

## Appearance tokens

Operators can override appearance through the read-only [branding directory](../branding.md).
The override stylesheet loads after packaged styling. Common application tokens:

| Token | Purpose | Default |
| --- | --- | --- |
| `--background` | Page and header background | `#fbfbf9` |
| `--surface` | Cards, fields and tables | `#ffffff` |
| `--text` | Body text | `#23312f` |
| `--heading` | Headings | `#16302e` |
| `--muted` | Supporting text and field guidance | `#52625e` |
| `--accent` | Links, primary buttons and focus | `#086c86` |
| `--border` | Separators | `#d5e0d8` |
| `--lime` | Landing action and highlights | `#a3cc32` |
| `--pale-blue` | Landing and selected navigation | `#c8e1e8` |
| `--footer-background` | Footer background | `#edf4ef` |
| `--font-body` | Body typeface | Roboto, system UI fallback |
| `--font-heading` | Heading typeface | Roboto Condensed, Roboto fallback |

Administration has separate presentation variables, including `--body-bg`,
`--body-fg`, `--body-quiet-color`, `--body-loud-color`, `--header-bg`,
`--header-color`, `--link-fg`, `--darkened-bg`, `--selected-bg`,
`--breadcrumbs-bg`, `--button-bg` and `--button-fg`. Its native controls,
model permissions and protected read-only records remain unchanged.

Choose foreground/background pairs together. Check normal text at a contrast
ratio of at least 4.5:1, large text at least 3:1, visible focus indicators, and
both desktop and mobile layouts. The institutional test fixture demonstrates
an alternate navy/gold palette for the application and administration.

## Packaged fonts and provenance

The browser loads fonts from the application's static files; no external font
service is needed. Roboto and Roboto Condensed are unmodified variable fonts
from [Google Fonts](https://github.com/google/fonts), pinned to revision
`6e8069ff8ba3dab2a397fb30e7fbd243aba9b57a`.

| Local file under `web/static/web/fonts/` | SHA-256 |
| --- | --- |
| `Roboto.ttf` | `d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134` |
| `RobotoCondensed.ttf` | `dace262afcee68a5276f200d8026c57221735c0118ab5fda8c2c0d3dc409a8d0` |

Both are distributed under SIL Open Font License 1.1. Their original copyright
and license notices are packaged alongside them as `roboto-OFL.txt` and
`robotocondensed-OFL.txt`. The [logo provenance](../branding.md#packaged-logo)
is documented separately.

The visual references are [slaif.si](https://slaif.si/),
[doc.slaif.si](https://doc.slaif.si/) and
[SLAIF trainings](https://edu.slaif.si/trainings), inspected in a real browser
on 5 October 2026. The application implements its own templates and CSS.

## Browser qualification

See [Testing](../../TESTING.md) for the role, theme and viewport matrix.
Screenshots support visual review; semantic layout and accessibility assertions
provide durable regression checks without pixel-perfect snapshots.
