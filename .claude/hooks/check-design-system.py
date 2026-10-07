"""PostToolUse hook for .html edits: keeps pages consistent with the Artisan Solutions Design System
(https://claude.ai/design/p/01d13dfc-6e66-40a8-9edd-e5ff28a39060, README rule 6).

Blocking (exit 2, stderr goes back to Claude):
  - :root is missing the design-system text coppers (--copper-ink, --copper-on-dark)
  - no :focus-visible rule with an outline (keyboard focus must stay visible)
  - small copper text: a rule sets text colour to brand copper / a copper tint AND a font-size under
    24px. Small copper text must use --copper-ink (light backgrounds) or --copper-on-dark (navy).
Exempt: wordmarks (selectors containing "logo" or "wm") and faded decorative numerals (alpha < .35).
Rules without a font-size can't be judged statically — the rendered audit covers those:
  node .claude/tools/contrast-audit.cjs <page>.html"""
import json, os, re, sys

path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
if not path.endswith(".html"):
    sys.exit(0)

text = open(path, encoding="utf-8").read()
style = re.search(r"<style[^>]*>(.*?)</style>", text, re.S)
if not style:
    sys.exit(0)
css = re.sub(r"/\*.*?\*/", "", style.group(1), flags=re.S)
errors = []

root = re.search(r":root\s*\{([^}]*)\}", css)
for token in ("--copper-ink", "--copper-on-dark"):
    if not root or token + ":" not in root.group(1).replace(" ", ""):
        errors.append(f":root is missing {token} (copy the :root block from a recent article)")

if not re.search(r":focus-visible[^{]*\{[^}]*outline\s*:", css):
    errors.append("no :focus-visible rule with an outline: keep the design system's focus ring "
                  "(:where(a,button,input,select,textarea,summary,[tabindex]):focus-visible{...})")

COPPER = re.compile(r"(?:^|[\s;])color\s*:\s*(var\(--copper(?:-lt)?\)|rgba\(\s*181\s*,\s*101\s*,\s*42\s*(?:,\s*([\d.]+))?\s*\))")

def px(size):
    size = size.strip()
    clamp = re.match(r"clamp\(\s*([^,]+),", size)
    if clamp:
        size = clamp.group(1).strip()  # smallest size the text can shrink to
    m = re.match(r"([\d.]+)(px|rem|em)$", size)
    if not m:
        return None
    return float(m.group(1)) * (1 if m.group(2) == "px" else 16)

rules = [(" ".join(sel.split()), body) for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css)]
# Selectors that also get an AA copper somewhere (e.g. a media query for the sizes where they shrink).
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
    print(f"{path} (design system):\n  " + "\n  ".join(errors), file=sys.stderr)
    sys.exit(2)
