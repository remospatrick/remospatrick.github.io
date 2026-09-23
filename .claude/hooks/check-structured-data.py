"""PostToolUse hook for .html/.xml edits.
Blocking (exit 2, stderr goes back to Claude): broken JSON-LD, malformed sitemap XML, missing/empty SEO tags, URL mismatches.
Non-blocking (additionalContext): title/description over Google's display length — most existing pages already exceed it."""
import html, json, os, re, sys, xml.dom.minidom

SITE = "https://artisanitsolutions.com/"
NO_SEO = {"privacy-policy.html", "terms-of-service.html"}  # utility pages, intentionally minimal
BASE_TAGS = ["description", "keywords", "author", "robots", "viewport",
             "og:title", "og:description", "og:type", "og:url", "og:image", "og:image:alt",
             "og:image:width", "og:image:height", "og:site_name", "og:locale",
             "twitter:card", "twitter:title", "twitter:description", "twitter:image"]
ARTICLE_TAGS = ["article:author", "article:publisher", "article:section", "article:tag"]

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
if not path.endswith((".html", ".xml")):
    sys.exit(0)

name = os.path.basename(path)
text = open(path, encoding="utf-8").read()
errors, warnings = [], []

if path.endswith(".xml"):
    try:
        xml.dom.minidom.parseString(text.encode("utf-8"))
    except Exception as e:
        errors.append(f"malformed XML: {e}")
else:
    ld = []
    for i, block in enumerate(re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.S | re.I), 1):
        try:
            ld.append(json.loads(block))
        except json.JSONDecodeError as e:
            errors.append(f"JSON-LD block {i}: {e}")

    if name not in NO_SEO:
        meta = {k: html.unescape(v).strip() for k, v in
                re.findall(r'<meta\s+(?:name|property)="([^"]+)"\s+content="([^"]*)"', text)}
        canonical = re.search(r'<link rel="canonical" href="([^"]*)"', text)
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        is_article = meta.get("og:type") == "article"

        for tag in BASE_TAGS + (ARTICLE_TAGS if is_article else []):
            if not meta.get(tag):
                errors.append(f"missing or empty meta: {tag}")
        if not title or not title.group(1).strip():
            errors.append("missing <title>")
        if not canonical:
            errors.append('missing <link rel="canonical">')
        if len(re.findall(r"<h1[\s>]", text)) != 1:
            errors.append("page must have exactly one <h1>")
        if meta.get("og:image") and not meta["og:image"].startswith("https://"):
            errors.append("og:image must be an absolute https URL")

        if canonical:
            url = canonical.group(1)
            expected = SITE if name == "index.html" else SITE + name
            if url != expected:
                errors.append(f"canonical is {url}, expected {expected}")
            if meta.get("og:url") and meta["og:url"] != url:
                errors.append(f"og:url {meta['og:url']} != canonical {url}")
            for obj in ld:
                if obj.get("@type") == "Article":
                    for key in ("url", "mainEntityOfPage"):
                        if obj.get(key) and obj[key] != url:
                            errors.append(f"JSON-LD Article {key} {obj[key]} != canonical {url}")

        if title and len(html.unescape(title.group(1).strip())) > 60:
            warnings.append(f"<title> is {len(html.unescape(title.group(1).strip()))} chars; Google truncates around 60")
        if len(meta.get("description", "")) > 160:
            warnings.append(f"meta description is {len(meta['description'])} chars; Google truncates around 160")

if errors:
    print(f"{path}:\n  " + "\n  ".join(errors + warnings), file=sys.stderr)
    sys.exit(2)
if warnings:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                      "additionalContext": f"SEO warnings for {name} (not blocking): " + "; ".join(warnings)}}))
