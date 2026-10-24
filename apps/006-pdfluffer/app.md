---
title: PDFluffer
summary: A PDF reader and editor for Windows with no ads, no account and no nag screens. Fill forms, sign, and fix up scans.
platforms: Windows
licence: MIT
download: https://github.com/nick2468/pdfluffer/releases/latest
source: https://github.com/nick2468/pdfluffer
media:
  - file: 01-form.png
    alt: Three PDFs open in tabs. The active one is a form with its fields filled in, and the orange dot on the tab shows it has unsaved changes.
  - file: 02-signature.png
    alt: The signature dialog on a flat form. A signature typed as a name, ready to place on the page and keep for next time.
  - file: 03-menu.png
    alt: The app menu, with the Document tools: insert another PDF, rotate pages, flatten, revert to saved, and the saved signatures.
---
I built PDFluffer because every PDF app I tried wanted me to pay for the basics, and
reminded me of that on every page. It does the things most people need from a PDF app
and nothing else: read several files in tabs, search and copy text, fill in forms, add
text anywhere on a flat form, and sign. Saved signatures come back next time, and you can
rename them.

It saves straight back to the file, asks once before the first overwrite and never again,
and reopens your tabs where you left them. A digitally signed PDF gets a badge, and a
warning before any change that would break the signature.

The Document menu adds the tools the paid apps charge for: insert another PDF, rotate
pages, and flatten a form so the answers and signatures become a permanent part of the
page before you send it. A scanned PDF, which is only a picture, can be made searchable
with the OCR built into Windows, so you can select and copy its text.

Under the skin it is the same PDF engine as Firefox, inside a small Windows app. It never
touches the network: no telemetry, no update checks, nothing uploaded.
