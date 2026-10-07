"""PostToolUse hook for .html and assets/css/*.css edits: keeps the site consistent with the Artisan Solutions
Design System (https://claude.ai/design/p/01d13dfc-6e66-40a8-9edd-e5ff28a39060, README rule 6).

Shared styles live in assets/css/: site.css (design-system tokens, reset, focus ring; every page links it),
article.css (Insights articles) and legal.css (privacy/terms). Pages keep only page-specific CSS inline.

Blocking (exit 2, stderr goes back to Claude):
  - a page doesn't link assets/css/site.css
  - a page redefines design-system tokens inline (tokens live only in site.css, so pages can't drift)
  - site.css loses --copper-ink / --copper-on-dark or the :focus-visible ring
  - small copper text: a rule sets text colour to brand copper / a copper tint AND a font-size under 24px
    (checked across the page's inline CSS and the stylesheets it links, or the edited .css file).
    Small copper text must use --copper-ink (light backgrounds) or --copper-on-dark (navy).
Exempt: wordmarks (selectors with "logo" or "wm"), faded decorative numerals (alpha < .35), and selectors
that are also given an AA copper elsewhere (e.g. a media query for the sizes where they shrink).
Rules without a font-size can't be judged statically; the rendered audit covers those:
  node .claude/tools/contrast-audit.cjs <page>.html"""
import json, os, re, sys

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
norm = path.replace("\\", "/")
is_html = norm.endswith(".html")
is_css = norm.endswith(".css") and "/assets/css/" in "/" + norm and os.path.basename(norm) in ("site.css", "article.css", "legal.css")
if not (is_html or is_css):
    sys.exit(0)

root_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.abspath(path))
TOKENS = ("--copper-ink", "--copper-on-dark")
DS_TOKENS = re.compile(r"--(?:navy(?:-dk|-md|-lt)?|copper(?:-lt|-pl|-ms|-ink|-on-dark)?|sand|linen|pebble|slate|ink|white)\s*:")
strip = lambda css: re.sub(r"/\*.*?\*/", "", css, flags=re.S)
read = lambda p: open(p, encoding="utf-8").read()
errors = []


def site_css_errors(css):
    errs = []
    root = re.search(r":root\s*\{([^}]*)\}", css)
    for token in TOKENS:
        if not root or token + ":" not in root.group(1).replace(" ", ""):
            errs.append(f"site.css :root is missing {token}")
    # The site-wide ring specifically: a narrower rule (e.g. the form fields' ring) doesn't cover links and buttons.
    if not re.search(r":where\([^)]*\ba\b[^)]*\bbutton\b[^)]*\):focus-visible\s*\{[^}]*outline\s*:", css):
        errs.append("site.css lost the :focus-visible ring (:where(a,button,input,select,textarea,summary,[tabindex]):focus-visible{...})")
    return errs


if is_html:
    text = read(path)
    inline = strip("\n".join(re.findall(r"<style[^>]*>(.*?)</style>", text, re.S)))
    linked = re.findall(r'<link[^>]+href="assets/css/((?:site|article|legal)\.css)"', text)
    if "site.css" not in linked:
        errors.append('page must link the shared stylesheet: <link rel="stylesheet" href="assets/css/site.css"/> '
                      "(articles also assets/css/article.css), placed before any inline <style>")
    if DS_TOKENS.search(inline):
        errors.append("inline <style> redefines design-system tokens; they live only in assets/css/site.css")
    sheets = [strip(read(os.path.join(root_dir, "assets", "css", f))) for f in linked
              if os.path.exists(os.path.join(root_dir, "assets", "css", f))]
    if "site.css" in linked and os.path.exists(os.path.join(root_dir, "assets", "css", "site.css")):
        errors += site_css_errors(strip(read(os.path.join(root_dir, "assets", "css", "site.css"))))
    css = "\n".join(sheets + [inline])
else:
    css = strip(read(path))
    if os.path.basename(norm) == "site.css":
        errors += site_css_errors(css)

COPPER = re.compile(r"(?:^|[\s;])color\s*:\s*(var\(--copper(?:-lt)?\)|rgba\(\s*181\s*,\s*101\s*,\s*42\s*(?:,\s*([\d.]+))?\s*\))")


def px(size):
    size = size.strip()
    clamp = re.match(r"clamp\(\s*([^,]+),", size)
    if clamp:
        size = clamp.group(1).strip()  # smallest size the text can shrink to
    m = re.match(r"([\d.]+)(px|rem|em)$", size)
    return float(m.group(1)) * (1 if m.group(2) == "px" else 16) if m else None


rules = [(" ".join(sel.split()), body) for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)]
fixed = {sel for sel, body in rules if re.search(r"color\s*:\s*var\(--copper-(?:ink|on-dark)\)", body)}
for sel, body in rules:
    if re.search(r"logo|wm", sel) or sel in fixed:
        continue
    c = COPPER.search(body)
    size = re.search(r"font-size\s*:\s*([^;]+)", body)
    if not c or not size:
        continue
    alpha = float(c.group(2)) if c.group(2) else 1
    size_px = px(size.group(1))
    if alpha >= 0.35 and size_px is not None and size_px < 24:
        errors.append(f'"{sel}" is {size_px:g}px copper text ({c.group(1)}): under 24px use '
                      "var(--copper-ink) on light backgrounds or var(--copper-on-dark) on navy")

if errors:
    print(f"{path} (design system):\n  " + "\n  ".join(dict.fromkeys(errors)), file=sys.stderr)
    sys.exit(2)
