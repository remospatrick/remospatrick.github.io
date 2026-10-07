# artisanitsolutions.com

Static site on GitHub Pages: merging to `main` publishes live within a minute or two, so change it through a branch and a pull request. Every page is a standalone HTML file with its own inline `<style>`; `assets/` (Bootstrap, jQuery) is legacy and unused.

## Design system

Pages follow the **Artisan Solutions Design System** (https://claude.ai/design/p/01d13dfc-6e66-40a8-9edd-e5ff28a39060), shared with the Invoicing portal and HelpDesk. When creating or editing a page:

- **Start from a recent article** (e.g. `yardi-analytics-portfolio-decisions.html`) and keep its `:root` block and its `:focus-visible` rules intact. Don't rebuild the CSS from memory.
- **Use the named colour tokens**, never a raw hex value or `rgba(181,101,42,…)`.
- **Copper text depends on size and background:**
  - 24px or larger (headings): brand `var(--copper)` is fine.
  - Under 24px on a light background (sand, white, linen): `var(--copper-ink)`.
  - Under 24px on navy: `var(--copper-on-dark)`.
  - Text that shrinks on phones (`clamp()`, `vw`) counts at its smallest size.
  - Brand copper stays for the wordmark, lines, borders, dots and button fills.
- **Keep keyboard focus visible.** Never set `outline:none` without a `:focus-visible` ring.

## Checks

- `.claude/hooks/check-structured-data.py` (SEO) and `.claude/hooks/check-design-system.py` (tokens, focus ring, small copper text) run automatically after every page edit and block on failures.
- `node .claude/tools/contrast-audit.cjs [page.html …]` measures copper text contrast in Chrome at 1280px and 375px. Run `npm --prefix .claude/tools install` once first. The `publish-post` skill runs it before committing a new post.
