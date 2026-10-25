# nick2468.github.io

My apps showcase: a small website with screenshots, short clips and a play or download
button for each app I have built. It exists so that people can see the apps without
reading GitHub.

The site is plain HTML, built by a Python script with no packages to install. GitHub Pages
publishes it at `https://nick2468.github.io` each time `main` is pushed.

## Layout

| Path | What |
|---|---|
| `home.md` | The home page: the site's title, my name, the site address, and the intro text. |
| `apps/` | One folder per app. Each holds an `app.md` and the app's pictures and clips. |
| `site/build.py` | Turns `home.md` and `apps/` into the website, in `site/dist`. |
| `site/test_build.py` | The tests for the build script. |
| `.github/workflows/pages.yml` | Tests, builds and publishes the site on each push to `main`. |

`site/dist` is not committed. The build makes it fresh each time.

## Add or change an app

1. Make a folder under `apps/`, named `<number>-<name>`, for example `008-my-game`. The
   number sets the card's place on the home page. The name becomes the page's address, so
   `008-my-game` is served at `/my-game/`.
2. Put the screenshots and clips in that folder.
3. Write `app.md` in the folder. Copy an existing one as a start.
4. Build and look at it (see "Preview on this machine").
5. Commit and push. The site updates a minute or two later.

### What goes in app.md

```
---
title: My Game
summary: One line for the card and the top of the page.
platforms: iPad, Web browser
play: https://example.com
media:
  - file: 01-main-screen.png
    alt: One sentence on what the picture shows.
  - file: 02-a-turn.mp4
    alt: One sentence on what the clip shows.
    poster: 02-a-turn.png
---
A few short paragraphs about the app. Blank lines split paragraphs.
A link looks like [this](https://example.com).
```

| Field | Needed | What it is |
|---|---|---|
| `title` | yes | The app's name. |
| `summary` | yes | One line, shown on the card and under the title. |
| `platforms` | no | What it runs on, separated by commas. Shown as tags. |
| `play` | no | A web address where the app runs in a browser. Shows a "Play it" button. |
| `download` | no | A web address for the installer. Shows a "Download it" button. |
| `website` | no | The app's own website. Shows a "Visit the website" button. |
| `source` | no | The code on GitHub. Always the plain, second button, never the main one. |
| `media` | no | The pictures and clips, in the order the page shows them. |

Every link must start with `https://`. Each media item needs `file` and `alt`. A clip can
also have a `poster`, the picture shown before it plays. Files must be PNG, JPG or MP4 and
sit in the app's own folder. The build stops with a plain message if anything is wrong,
including a media file that is named but missing.

The first picture in `media` is the card's cover on the home page. An app with no pictures
gets its first letter as a cover instead.

### Pictures and clips

- **Screenshots:** 1440 x 900 pixels suits the page. Keep each under about 1 MB.
- **Clips:** record with the Windows Snipping Tool (Win + Shift + R), which saves MP4. Keep
  a clip short (under a minute) and silent: the page plays clips muted and on a loop, like a
  moving screenshot. GitHub refuses any file over 100 MB, and git keeps every old version of
  a file forever, so put anything long on YouTube instead and link to it from the text.

## Preview on this machine

```bash
python site/build.py
```

Then open `site/dist/index.html` in a browser. To serve it like the real site, run
`python -m http.server 8095 --directory site/dist` and open `http://localhost:8095`.

To run the tests:

```bash
python -m unittest discover -s site
```

## Publishing

The workflow in `.github/workflows/pages.yml` runs on each push to `main`. It runs the
tests, builds the site and publishes `site/dist`. If the tests or the build fail, nothing
is published and the live site stays as it was.

One setting makes this work, set once: in the repository on GitHub, **Settings > Pages >
Build and deployment > Source** must be **GitHub Actions**.

### A domain of my own, later

GitHub Pages can serve the site at a domain such as `nickwalker.dev` as well. Buy the
domain, add it under **Settings > Pages > Custom domain**, and point its DNS at GitHub as
that page explains. Then change `url:` in `home.md` to the new address, so link previews
point at the right place.
