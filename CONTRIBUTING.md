# Contributing

Thanks for helping with **Black Clover: Grimoire Awakening**! This is an early-access fan project, so bug reports and balance feedback are the most useful thing right now.

## Reporting

* **Bugs** and **balance** problems: open an issue with the matching template. Please include the addon version (e.g. `v0.1.0`), your Minecraft version and device, and the `[Scripting]` lines from the content log if there are any (Settings → Creator → Enable Content Log GUI).
* **Ideas:** use the idea template. Crossover content must stay original - no named characters, logos or designs from other series.

## Changing the addon

Everything in `packs/` and `dist/` is generated. Change the sources and rebuild:

* game data (spells, fruits, robes, shops, factions…) → `tools/bc/data.py`
* models, textures, particles, sounds → `tools/bc/`
* gameplay scripts → `src/scripts/`

```
python3 tools/build.py        # needs Python 3.10+, numpy, Pillow, ffmpeg
python3 tools/validate.py     # must print "validation OK"
python3 tools/docs.py         # refresh docs/ when data changes
```

New spells and fruit abilities are usually just a recipe in `tools/bc/data.py` - see [docs/development.md](docs/development.md#adding-a-spell-or-a-fruit).

## Style

* JavaScript: ES modules, `@minecraft/server` 2.0.0 stable APIs only (no experimental toggles), wrap engine calls that may fail in `safe()`.
* Python: plain functions, data in `data.py`, no hand-edited JSON in `packs/`.
* Keep in-game text short and clear; keep everything original.

## Releases

See [docs/development.md](docs/development.md#releasing). Bump `VERSION` in `tools/bc/packgen.py` for every release and add a `CHANGELOG.md` section.
