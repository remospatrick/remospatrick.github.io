# artisanitsolutions.com

Static site on GitHub Pages: merging to `main` publishes live within a minute or two, so change it through a branch and a pull request.

## Stylesheets

Shared CSS lives in `assets/css/`. Pages link it and keep only page-specific CSS in an inline `<style>`:

| File | Linked by | Holds |
|---|---|---|
| `site.css` | every page | design-system colour tokens, reset, keyboard focus ring |
| `article.css` | every Insights article | article layout and components (nav, breadcrumb, hero, cards, pull quote, footer…) |
| `legal.css` | privacy policy, terms | their full stylesheet |

`index.html` and `blog.html` are one-off designs and keep their own CSS inline. `bootstrap.css`, `landing-page.css` and `pe-icon-7-stroke.css` are legacy and unused.

- **A design-system change goes in one file:** colours in `site.css`, article components in `article.css`. Don't copy shared rules into a page.
- **A new article** links `<link rel="stylesheet" href="assets/css/site.css"/>` then `<link rel="stylesheet" href="assets/css/article.css"/>`, before its own `<style>`. Copy the `<head>` of a recent article. Its inline `<style>` holds only what's unique to that post.
- **Order matters:** linked files load before the inline `<style>`. A rule moved into a shared file must not be overridden by a page rule that used to come after it. Check with a before/after screenshot when moving CSS between files.

## Design system

Pages follow the **Artisan Solutions Design System** (https://claude.ai/design/p/01d13dfc-6e66-40a8-9edd-e5ff28a39060), shared with the Invoicing portal and HelpDesk. When creating or editing a page:

- **Never redefine the colour tokens in a page.** They live only in `site.css`.
- **Use the named colour tokens**, never a raw hex value or `rgba(181,101,42,…)`.
- **Copper text depends on size and background:**
  - 24px or larger (headings): brand `var(--copper)` is fine.
  - Under 24px on a light background (sand, white, linen): `var(--copper-ink)`.
  - Under 24px on navy: `var(--copper-on-dark)`.
  - Text that shrinks on phones (`clamp()`, `vw`) counts at its smallest size.
  - Brand copper stays for the wordmark, lines, borders, dots and button fills.
- **Keep keyboard focus visible.** Never set `outline:none` without a `:focus-visible` ring.

## Checks

- `.claude/hooks/check-structured-data.py` (SEO) and `.claude/hooks/check-design-system.py` run automatically after every page or `assets/css` edit and block on failures. The design check covers: the `site.css` link, no inline token redefinitions, the tokens and focus ring in `site.css`, and small copper text in the page's inline CSS plus the stylesheets it links.
- `node .claude/tools/contrast-audit.cjs [page.html …]` measures copper text contrast in Chrome at 1280px and 375px. Run `npm --prefix .claude/tools install` once first. The `publish-post` skill runs it before committing a new post.
