#!/usr/bin/env python3
"""Build the apps showcase as a static site.

Reads home.md and apps/*/app.md, and writes plain HTML to site/dist: a home
page with a card for every app, and one page per app with its screenshots,
clips and links. Python 3 standard library only, so the GitHub Pages workflow
can run it with no install step:

    python site/build.py

Options (mainly for the tests):

    --root DIR   the repository root (default: the folder above site/)
    --out DIR    where to write the site (default: <root>/site/dist)

Adapted from the DataCrafter showcase's build script. Licensed MIT.
"""

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

MARKER = ".built-by-build-py"

IMAGE_TYPES = {".png", ".jpg", ".jpeg"}
VIDEO_TYPES = {".mp4"}
HOME_KEYS = ("title", "name", "url")
APP_KEYS = ("title", "summary", "licence")

# Every app says who may use its code. "Copyright" means the source is mine; anything else
# is the name of an open-source licence, and the app must then link its source.
CLOSED = "Copyright"

# The links an app can carry, in the order its buttons show. The first one present is
# the main button. "source" is always last and always plain, because the point of this
# site is that a visitor never has to read code to try an app.
LINKS = (
    ("play", "Play it"),
    ("download", "Download it"),
    ("website", "Visit the website"),
    ("source", "See the source code"),
)

# A folder name is <number>-<name>. The number orders the cards; the name is the page's
# address, so apps/001-conquest is served at /conquest/.
FOLDER = re.compile(r"([0-9]{3})-([a-z0-9]+(?:-[a-z0-9]+)*)")

STYLE = """
:root{
  --bg:#FBFAF7;
  --surface:#FFFFFF;
  --text:#1C1D21;
  --muted:#5D6270;
  --line:#E3E1DA;
  --accent:#1F6F68;
  --accent-text:#FFFFFF;
  --shadow:0 1px 2px rgba(20,20,30,.06),0 4px 16px rgba(20,20,30,.05);
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --maxw:1080px;
  --gutter:clamp(16px,5vw,48px);
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#15171B;
    --surface:#1D2026;
    --text:#ECEDEF;
    --muted:#A3A8B3;
    --line:#2D313A;
    --accent:#5CC2B6;
    --accent-text:#0E1A19;
    --shadow:none;
    color-scheme:dark;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
  font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}
a:focus-visible,.button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
h1,h2,h3{margin:0 0 12px;line-height:1.15;letter-spacing:-.02em;font-weight:650}
h1{font-size:clamp(30px,4.4vw,46px)}
h2{font-size:clamp(22px,2.6vw,28px)}
h3{font-size:20px}
p{margin:0 0 14px}
.wrap{max-width:var(--maxw);margin:0 auto;padding-inline:var(--gutter)}
header{border-bottom:1px solid var(--line)}
.nav{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;
  gap:8px 24px;padding-block:16px}
.brand{font-weight:650;font-size:18px;color:var(--text);text-decoration:none}
.nav ul{display:flex;flex-wrap:wrap;gap:20px;margin:0;padding:0;list-style:none}
.nav a{text-decoration:none}
main{padding-block:48px 72px}
section{margin-bottom:56px}
.lede{font-size:clamp(18px,2vw,20px);color:var(--muted);max-width:680px}
.intro p{max-width:680px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:24px;
  margin:0;padding:0;list-style:none}
.card{position:relative;display:flex;flex-direction:column;background:var(--surface);
  border:1px solid var(--line);border-radius:10px;overflow:hidden;box-shadow:var(--shadow)}
.card:hover{border-color:var(--accent)}
.card:focus-within{outline:2px solid var(--accent);outline-offset:3px}
.cover{display:block;width:100%;aspect-ratio:16/10;object-fit:cover;object-position:left top;
  border-bottom:1px solid var(--line)}
.cover-text{display:flex;align-items:center;justify-content:center;width:100%;aspect-ratio:16/10;
  border-bottom:1px solid var(--line);background:var(--bg);color:var(--accent);
  font-size:56px;font-weight:700;letter-spacing:-.03em}
.card-body{display:flex;flex-direction:column;gap:8px;padding:18px 20px 20px;flex:1}
.card h3{margin:0}
.card-link{color:var(--text);text-decoration:none}
/* The title's link covers the whole card, so the card is one link named by its title. */
.card-link::after{content:"";position:absolute;inset:0}
.card-link:focus-visible{outline:none}
.card:hover .card-link{color:var(--accent)}
.summary{color:var(--muted);font-size:15px;margin:0}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:auto 0 0;padding:6px 0 0;list-style:none}
.tags li{font-size:12px;font-weight:600;color:var(--muted);border:1px solid var(--line);
  border-radius:999px;padding:2px 10px}
.actions{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0 8px}
.button{display:inline-block;padding:10px 18px;border-radius:8px;font-weight:600;
  text-decoration:none;border:1px solid var(--accent);color:var(--accent)}
.button.main{background:var(--accent);color:var(--accent-text)}
.button:hover{filter:brightness(1.08)}
.platforms{font-size:14px;color:var(--muted);margin-bottom:8px}
.rights-line{margin-bottom:28px}
.tags li.rights{color:var(--ink);border-color:var(--ink)}
.about{max-width:700px}
.media{display:grid;gap:32px;margin-top:40px}
.media figure{margin:0}
.media img,.media video{display:block;max-width:100%;height:auto;border:1px solid var(--line);
  border-radius:8px;box-shadow:var(--shadow)}
figcaption{font-size:14px;color:var(--muted);margin-top:10px;max-width:700px}
.back{margin-top:48px}
footer{border-top:1px solid var(--line);padding-block:28px;font-size:14px;color:var(--muted)}
footer p{margin:0}
"""


class BuildError(Exception):
    """A problem in the repository content that must fail the build."""


# ---------------------------------------------------------------- parsing


def parse_front_matter(text, source):
    """Split a .md file into (front matter dict, body text).

    The front matter is a small YAML subset: "key: value" lines, and a "media:"
    list whose items each carry "file:" and "alt:". The opening "---" is
    optional; the closing "---" is required.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        lines = lines[1:]
    try:
        end = next(i for i, line in enumerate(lines) if line.strip() == "---")
    except StopIteration:
        raise BuildError(f"{source}: no closing '---' after the front matter")

    meta = {"media": []}
    in_media = False
    for number, raw in enumerate(lines[:end], start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.strip()
        if in_media and raw[:1] in (" ", "\t"):
            if stripped.startswith("- "):
                meta["media"].append({})
                stripped = stripped[2:].strip()
            if not meta["media"]:
                raise BuildError(f"{source}: line {number}: media field before any '- ' item")
            key, value = _split_pair(stripped, source, number)
            meta["media"][-1][key] = value
            continue
        in_media = False
        key, value = _split_pair(stripped, source, number)
        if key == "media":
            if value:
                raise BuildError(f"{source}: line {number}: 'media:' takes a list on the lines below")
            in_media = True
        else:
            meta[key] = value

    body = "\n".join(lines[end + 1:]).strip()
    return meta, body


def _split_pair(text, source, number):
    if ":" not in text:
        raise BuildError(f"{source}: line {number}: expected 'key: value'")
    key, value = text.split(":", 1)
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return key.strip(), value


def check_https(meta, keys, source):
    for key in keys:
        if meta.get(key) and not meta[key].startswith("https://"):
            raise BuildError(f"{source}: '{key}' must be an https:// address")


def check_app(meta, source):
    for key in APP_KEYS:
        if not meta.get(key):
            raise BuildError(f"{source}: front matter is missing '{key}'")
    check_https(meta, [key for key, _ in LINKS], source)
    if meta["licence"] != CLOSED and not meta.get("source"):
        raise BuildError(f"{source}: an open-source app ('licence: {meta['licence']}') needs its 'source' link")
    for item in meta["media"]:
        if not item.get("file"):
            raise BuildError(f"{source}: a media item has no 'file'")
        if not item.get("alt"):
            raise BuildError(f"{source}: media '{item['file']}' has no 'alt' text")
        for key in ("file", "poster"):
            name = item.get(key)
            if not name:
                continue
            if Path(name).name != name:
                raise BuildError(f"{source}: media '{name}' must sit in the app's own folder")
            allowed = IMAGE_TYPES if key == "poster" else IMAGE_TYPES | VIDEO_TYPES
            if Path(name).suffix.lower() not in allowed:
                kinds = "PNG or JPG" if key == "poster" else "PNG, JPG or MP4"
                raise BuildError(f"{source}: media '{name}' is not {kinds}")


LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def inline_markdown(text):
    """Escape text, turning [label](https://...) into a link."""
    out, pos = [], 0
    for match in LINK.finditer(text):
        out.append(html.escape(text[pos:match.start()]))
        label, url = match.group(1), match.group(2)
        if url.startswith(("https://", "http://")):
            out.append(f'<a href="{html.escape(url)}">{html.escape(label)}</a>')
        else:
            out.append(html.escape(label))
        pos = match.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def paragraphs(text):
    """Plain text to HTML paragraphs. Blank lines separate paragraphs."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    return "\n".join(f"<p>{inline_markdown(' '.join(b.split()))}</p>" for b in blocks)


# ---------------------------------------------------------------- reading


def load_home(root):
    source = root / "home.md"
    if not source.is_file():
        raise BuildError("home.md is missing")
    meta, body = parse_front_matter(source.read_text(encoding="utf-8"), "home.md")
    for key in HOME_KEYS:
        if not meta.get(key):
            raise BuildError(f"home.md: front matter is missing '{key}'")
    check_https(meta, ("url", "github", "linkedin"), "home.md")
    meta["url"] = meta["url"].rstrip("/")
    return meta, body


def load_app(folder):
    source = f"apps/{folder.name}/app.md"
    match = FOLDER.fullmatch(folder.name)
    if not match:
        raise BuildError(f"apps/{folder.name}: a folder name is <number>-<name>, for example "
                         "001-my-app, in lower-case letters, digits and hyphens")
    meta, body = parse_front_matter((folder / "app.md").read_text(encoding="utf-8"), source)
    check_app(meta, source)
    for item in meta["media"]:
        for key in ("file", "poster"):
            if item.get(key) and not (folder / item[key]).is_file():
                raise BuildError(f"{source}: media '{item[key]}' is not in the folder")
    return {"folder": folder, "slug": match.group(2), "meta": meta, "body": body}


def load_apps(root):
    base = root / "apps"
    if not base.is_dir():
        return []
    folders = sorted(p for p in base.iterdir() if p.is_dir() and (p / "app.md").is_file())
    apps = [load_app(folder) for folder in folders]
    seen = {}
    for app in apps:
        if app["slug"] in seen:
            raise BuildError(f"apps/{app['folder'].name}: the name '{app['slug']}' is also used by "
                             f"apps/{seen[app['slug']]}; two apps cannot share one address")
        seen[app["slug"]] = app["folder"].name
    return apps


def platforms_of(meta):
    return [p.strip() for p in meta.get("platforms", "").split(",") if p.strip()]


def images_of(app):
    return [m for m in app["meta"]["media"] if Path(m["file"]).suffix.lower() in IMAGE_TYPES]


# ---------------------------------------------------------------- rendering


def page(home, title, body, prefix="", description="", path="", image=""):
    """Wrap a body in the site shell. prefix is the relative path back to the site root.

    path and image are site-relative, for the canonical address and the preview card a
    link shows when it is pasted into a chat or a social post.
    """
    site = home["title"]
    full_title = site if title == site else f"{title} | {site}"
    canonical = f"{home['url']}/{path}"
    meta = [f'<link rel="canonical" href="{html.escape(canonical)}">',
            f'<meta property="og:title" content="{html.escape(title)}">',
            f'<meta property="og:url" content="{html.escape(canonical)}">',
            '<meta property="og:type" content="website">']
    if description:
        meta.append(f'<meta name="description" content="{html.escape(description)}">')
        meta.append(f'<meta property="og:description" content="{html.escape(description)}">')
    if image:
        meta.append(f'<meta property="og:image" content="{html.escape(home["url"] + "/" + image)}">')
        meta.append('<meta name="twitter:card" content="summary_large_image">')
    nav = [f'<li><a href="{prefix}index.html#apps">Apps</a></li>']
    if home.get("github"):
        nav.append(f'<li><a href="{html.escape(home["github"])}">GitHub</a></li>')
    if home.get("linkedin"):
        nav.append(f'<li><a href="{html.escape(home["linkedin"])}">LinkedIn</a></li>')
    head = "\n".join(meta)
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full_title)}</title>
{head}
<style>{STYLE}</style>
</head>
<body>
<header><div class="wrap nav">
  <a class="brand" href="{prefix}index.html">{html.escape(home["name"])}</a>
  <nav aria-label="Site"><ul>
    {"".join(nav)}
  </ul></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
  <p>Made by {html.escape(home["name"])} in Australia.</p>
</div></footer>
</body>
</html>
"""


def rights_label(meta):
    """Short form for a card: 'Open source (MIT)' or 'Copyright'."""
    return CLOSED if meta["licence"] == CLOSED else f"Open source ({meta['licence']})"


def rights_sentence(meta, owner):
    """Long form for an app's page."""
    if meta["licence"] == CLOSED:
        return f"Copyright {owner}. The source is not public."
    return f"Open source under the {meta['licence']} licence. Fork it, build it, change it."


def render_tags(meta):
    tags = "".join(f"<li>{html.escape(p)}</li>" for p in platforms_of(meta))
    rights = f'<li class="rights">{html.escape(rights_label(meta))}</li>'
    return f'<ul class="tags" aria-label="Runs on, and who may use the code">{rights}{tags}</ul>'


def render_card(app):
    """One app as a card. The whole card is one link, named by the title.

    The cover is decorative (alt=""), because the title already names the link and the
    app's page carries every picture with its own alt text. An app with no pictures yet
    gets its initial letter as a cover, so the grid stays even.
    """
    meta = app["meta"]
    images = images_of(app)
    if images:
        src = html.escape(f"{app['slug']}/{images[0]['file']}")
        cover = f'<img class="cover" src="{src}" alt="" loading="lazy">'
    else:
        cover = f'<div class="cover-text" aria-hidden="true">{html.escape(meta["title"][:1])}</div>'
    return f"""<li class="card">
{cover}
<div class="card-body">
<h3><a class="card-link" href="{html.escape(app['slug'])}/index.html">{html.escape(meta["title"])}</a></h3>
<p class="summary">{html.escape(meta["summary"])}</p>
{render_tags(meta)}
</div>
</li>"""


def render_home(home, intro, apps):
    cards = "\n".join(render_card(app) for app in apps) if apps else ""
    grid = f'<ul class="grid">\n{cards}\n</ul>' if apps else "<p>No apps yet.</p>"
    lede = f'<p class="lede">{html.escape(home["tagline"])}</p>' if home.get("tagline") else ""
    cover = next((f"{a['slug']}/{images_of(a)[0]['file']}" for a in apps if images_of(a)), "")
    body = f"""<section class="intro">
<h1>{html.escape(home["title"])}</h1>
{lede}
{paragraphs(intro)}
</section>
<section aria-labelledby="apps">
<h2 id="apps">Apps</h2>
{grid}
</section>"""
    return page(home, home["title"], body, description=home.get("tagline", ""), image=cover)


def render_actions(meta):
    buttons, first = [], True
    for key, label in LINKS:
        if not meta.get(key):
            continue
        kind = "button main" if first and key != "source" else "button"
        first = False
        buttons.append(f'<a class="{kind}" href="{html.escape(meta[key])}">{label}</a>')
    return f'<div class="actions">{"".join(buttons)}</div>' if buttons else ""


def render_media(app):
    figures = []
    for item in app["meta"]["media"]:
        src = html.escape(item["file"])
        alt = html.escape(item["alt"])
        if Path(item["file"]).suffix.lower() in VIDEO_TYPES:
            poster = f' poster="{html.escape(item["poster"])}"' if item.get("poster") else ""
            # Muted and looped, like a moving screenshot. The controls let a visitor pause it.
            tag = (f'<video controls muted loop playsinline preload="metadata"{poster} '
                   f'src="{src}" aria-label="{alt}"><a href="{src}">{alt}</a></video>')
        else:
            # Linked to the full-size file, so a phone can open it to read the detail.
            tag = f'<a href="{src}"><img src="{src}" alt="{alt}" loading="lazy"></a>'
        figures.append(f"<figure>{tag}<figcaption>{alt}</figcaption></figure>")
    return '<div class="media">\n' + "\n".join(figures) + "\n</div>" if figures else ""


def render_app_page(home, app):
    meta = app["meta"]
    platforms = platforms_of(meta)
    runs_on = f'<p class="platforms">Runs on {html.escape(", ".join(platforms))}</p>' if platforms else ""
    rights = f'<p class="platforms rights-line">{html.escape(rights_sentence(meta, home["name"]))}</p>'
    body = f"""<article>
<h1>{html.escape(meta["title"])}</h1>
<p class="lede">{html.escape(meta["summary"])}</p>
{render_actions(meta)}
{runs_on}
{rights}
<div class="about">
{paragraphs(app["body"])}
</div>
{render_media(app)}
</article>
<p class="back"><a href="../index.html#apps">Back to all apps</a></p>"""
    images = images_of(app)
    image = f"{app['slug']}/{images[0]['file']}" if images else ""
    return page(home, meta["title"], body, prefix="../", description=meta["summary"],
                path=f"{app['slug']}/", image=image)


def render_404(home):
    body = """<section>
<h1>That page is not here</h1>
<p>The address may be out of date. <a href="/index.html">See all the apps</a>.</p>
</section>"""
    # Served for any missing path, so its links are root-absolute, not relative.
    return page(home, "Not found", body, prefix="/", path="404.html")


# ---------------------------------------------------------------- writing


def prepare_out(out):
    """Empty the output folder, but only if this script made it.

    The folder itself is kept and only its contents removed, because Windows
    will not delete a folder that another process (a preview server) has open.
    """
    if out.exists():
        if any(out.iterdir()) and not (out / MARKER).exists():
            raise BuildError(f"{out} is not empty and was not made by build.py; refusing to clear it")
        for child in out.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    out.mkdir(parents=True, exist_ok=True)
    (out / MARKER).write_text("This folder is generated by site/build.py.\n", encoding="utf-8")


def build(root, out):
    """Build the site. Returns a short summary dict."""
    root, out = Path(root), Path(out)
    home, intro = load_home(root)
    apps = load_apps(root)

    prepare_out(out)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "index.html").write_text(render_home(home, intro, apps), encoding="utf-8")
    (out / "404.html").write_text(render_404(home), encoding="utf-8")
    media = 0
    for app in apps:
        dest = out / app["slug"]
        dest.mkdir()
        (dest / "index.html").write_text(render_app_page(home, app), encoding="utf-8")
        for item in app["meta"]["media"]:
            for key in ("file", "poster"):
                if item.get(key):
                    shutil.copy2(app["folder"] / item[key], dest / item[key])
            media += 1
    return {"apps": len(apps), "media": media}


def main(argv=None):
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Build the apps showcase site.")
    parser.add_argument("--root", type=Path, default=here.parent)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    out = args.out or args.root / "site" / "dist"
    try:
        summary = build(args.root, out)
    except BuildError as err:
        print(f"build.py: {err}", file=sys.stderr)
        return 1
    apps = "app" if summary["apps"] == 1 else "apps"
    files = "media file" if summary["media"] == 1 else "media files"
    print(f"Built {out}: {summary['apps']} {apps}, {summary['media']} {files}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
