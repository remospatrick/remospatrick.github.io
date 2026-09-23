---
name: publish-post
description: Wire a finished blog post (<slug>.html) into blog.html, sitemap.xml and index.html, check its URLs, and commit once
disable-model-invocation: true
---

Publish `$ARGUMENTS` (a post file in the repo root, e.g. `yardi-foo.html`). Site URL: `https://artisanitsolutions.com/<slug>.html`.
Read the post first to get its headline, description, category (`articleSection`), and read time. Copy the markup of the most recent existing entry in each file; don't invent new structure.

## 1. The post itself
Check that each of these equals the page URL exactly: `<link rel="canonical">`, `og:url`, the Article JSON-LD `url` and `mainEntityOfPage`, and the last BreadcrumbList `item`. Fix any that don't match.

## 2. blog.html
- JSON-LD: append a `BlogPosting` object to the `"blogPost": [...]` array (headline, url, description, author, articleSection).
- Grid: append an `<a class="article-card reveal">` after the last card, with comment `<!-- Article N — Category -->` (N = previous + 1). Set `data-category` to one of `yardi-consulting`, `market-insights`, `data-migration`, `report-customization`, and add `ac-tag`, `ac-title`, `ac-excerpt` and `ac-meta` ("N min read").
- Footer "Insights" list: add a `<li>` just before "All Articles".

## 3. sitemap.xml
- Add an `<!-- Article: <headline> -->` `<url>` block after the last article entry, with lastmod = today (YYYY-MM-DD), changefreq `monthly` and priority `0.8`.
- Set the homepage (`/`) and `blog.html` lastmod to today.

## 4. index.html (homepage insights: always the 2 newest posts)
- The `insights-grid` has 2 `insight-card`s. Put the new post in Article 1, move the old Article 1 to Article 2, and drop the old Article 2.
- Footer "Insights" list: put the new post first, keep the one after it, remove the rest, and keep "All Articles" last.

## 5. Commit
Show `git diff --stat` and confirm that exactly these files changed: the post, blog.html, sitemap.xml and index.html. Then make one commit: `Publish <headline>`. Do not push unless asked.
