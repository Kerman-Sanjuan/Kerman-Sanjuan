# How this profile is built

Every visual on the profile is an SVG generated from `profile.json`. GitHub's
README sanitizer strips CSS, classes and `<style>` blocks, but an SVG loaded
through `<img>` keeps its own stylesheet, its `@font-face` and its SMIL
animations. So the README is a thin layer of links around images.

```
profile.json ──▶ scripts/build.py ──▶ assets/header.svg
                                    assets/buttons/*.svg
                                    assets/cards/*.svg
                                    README.md

GitHub Actions (daily) ──▶ Platane/snk ──▶ scripts/terminal.py ──▶ output branch
                                                                   (terminal.svg)
```

## The pieces

| Piece | What it is | Rebuilt |
|---|---|---|
| `header.svg` | Paper gradient, the faint grid from platform.k3rman.com, a mono eyebrow, the headline typed character by character and the portrait in a circle | when you run the build |
| `buttons/*.svg` | One pill per link, drawn instead of a shields.io badge so the label uses IBM Plex and the corners are actually round | when you run the build |
| `cards/*.svg` | Highlights: a typographic panel, a title, a short body, a label and a pill | when you run the build |
| `output/terminal.svg` | A charcoal terminal holding the contribution snake and the tool icons | every day, by the workflow |

## Build it

```sh
python -m venv .venv && . .venv/bin/activate
pip install pillow

python scripts/fetch_icons.py --version 11.15.0   # only when you change tools
python scripts/build.py --readme README.md
```

`--version 11.15.0` is pinned on purpose: Simple Icons dropped the Azure mark
in later releases.

The terminal needs the snake, so it is not part of `build.py`:

```sh
python scripts/terminal.py --snake dist/snake-dark.svg --out dist/terminal.svg
```

## The colours

The palette is the gruvbox set from `@k3rman/ui-theme`, the same one the
platform and the blog use. Every pairing was checked with the WCAG contrast
formula rather than by eye; the lowest text ratio on the page is 4.66:1
(the sage eyebrow on paper) and the rest sit between 4.7 and 13:1.

| Token | Value | Where |
|---|---|---|
| paper | `#fbf1c7` | header background (with `#f2e5bc` in the gradient) |
| ink | `#3c3836` | headline |
| clay | `#af3a03` | the accent inside the headline, the buttons |
| sage | `#3d6f4f` | the eyebrow |
| muted | `#665c54` | the mono line under the headline |
| coal | `#282828` | terminal and cards |
| sand | `#d5c4a1` | text on charcoal |

The terminal accent is `#fe8019` instead of `#af3a03`, because on charcoal the
dark orange does not read and the light one does. Same rule as the theme: the
accent has one value per mode.

## Things that bite

- **Quotes inside `style="font:..."`.** A family with a space needs a quote, and
  a double quote closes the attribute and breaks the XML. `kit.css_family()`
  emits single quotes for that reason.
- **A clip path must live in `<defs>`.** Putting the whole portrait group inside
  `<defs>` renders the header without a photo and without an error.
- **The typing clips advance one character width at a time.** Add the
  `letter-spacing` to the character width or the last word gets cut
  (`TITLE_CHAR_W`, `CW`).
- **GitHub caches images hard.** For a file in the repo the raw redirect drops
  the query string, so `?v=2` changes nothing; give a changed image a new name.
  The terminal lives on another branch, where `?v=` does work.
- **A repository workflow needs the `workflow` OAuth scope.** A token with only
  `repo` can push the repository but not `.github/workflows/`.

## Credits

The generator structure comes from [jandoni/github-profile-kit](https://github.com/jandoni/github-profile-kit)
(MIT). See `NOTICE` for what changed. Icons: Simple Icons (CC0). Type: IBM Plex
(SIL OFL 1.1, `fonts/LICENSE.txt`).
