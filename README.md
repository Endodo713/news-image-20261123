# news-image-20261123 — make.fun competition entry

A single 1024x1024 newspaper front page summing up world news of **Monday 23 November 2026**: one main story (COP31 collapses without a deal) plus three supporting stories (EU's 22nd Russia sanctions, Ukraine sinks a Russian warship off Libya, markets rebound after Friday's crash).

## Badges

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/Endodo713/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/Endodo713/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

Link: https://make.fun/bounty/news-image-20261123

## Design

- Newspaper front page: masthead "THE WORLD IN ONE DAY" + "MONDAY 23 NOVEMBER 2026", one large main panel (red accent), three supporting rows each marked with a color-block square (blue, green, amber).
- Large short headlines (3–6 words), high contrast, legible at thumbnail size.
- Canvas 1024x1024; near-black `#0E1117`, ink `#F5F5F5`, red accent `#E74C3C`.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Python 3.13 stdlib-only PNG generator (zlib + struct, no PIL, no network) |
| `README.md` | This file |
| `LICENSE` | MIT (OSI-approved, SPDX-License-Identifier: MIT) |

## Run

```
export MAKEFUN_OUTPUT_DIR=/output   # optional; defaults to /output
python3 -P -s main.py               # Python 3.13, stdlib only, single file
```

`main.py` writes `/output/entry.png`, validates 1024x1024 and the 1 MiB cap, and produces **byte-identical output on repeated runs** (no network, clock, randomness, subprocesses, or external binaries).
