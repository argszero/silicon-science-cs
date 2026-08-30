# H3 Evidence — a11y_first self-description (issue #45, revision R81)

This file makes the H3 grouping variable (a11y_first) auditable. For each of the
four libraries classified accessibility-first in `corpus.json`, we quote the
exact self-description evidence, at the census snapshot SHA (2026-08-29). All
quotes were fetched from the pinned commit via jsDelivr (or the GitHub REST
API for repository descriptions) on 2026-08-30.

Extractor blindness: `extract.py` contains **no** reference to `a11y_first`
(`grep a11y_first extract.py` → exit 1). The field lives only in `corpus.json`
and is consumed by `reproduce.py` (aggregation) and `validate.py` (ground
truth). Corpus selection, file sampling, and density counting cannot be
influenced by it.

## 1. microsoft/fluentui — a11y_first: yes (pinned SHA eb2f46eace4915f136f5da23582cca90a852db7c)

- **Root README.md, "FluentUI Insights" section** — the Fluent UI design-system
  video series dedicates **"EP06: Accessible by default"**:
  > "EP06: Accessible by default"
  > https://learn.microsoft.com/en-us/shows/fluent-ui-insights/fluent-ui-insights-accessible-by-default
  (linked from the pinned README at the census SHA)
- Fluent's v9 positioning (supporting): "Accessible by default" is a stated
  Fluent 2 design principle in the same series (EP06 title, above).

## 2. radix-ui/primitives — a11y_first: yes (pinned SHA f7ecd5ab16f5e1e820eb5786a1419a98a2d594ae)

- **README.md (first paragraph)**:
  > "**An open-source UI component library for building high-quality,
  > accessible design systems and web apps.**"
  (https://github.com/radix-ui/primitives, at the pinned SHA)
- GitHub repository description (2026-08-30, API):
  "Radix Primitives is an open-source UI component library for building
  high-quality, accessible design systems and web apps. Maintained by @workos."

## 3. ariakit/ariakit — a11y_first: yes (pinned SHA a73e2268652a24bf929bb2d2d153f46dd4f74637)

- **readme.md (lowercase filename, line 6)**:
  > "Toolkit with accessible components, styles, and examples for your next web app."
- GitHub repository description (2026-08-30, API):
  "Toolkit with accessible components, styles, and examples for your next web app"
- Note: ariakit's *library* manifests declare no axe-family runtime testing
  dependency; its axe-core lives in the docs app (`app/`), which is why H3
  counts it as axe_family=no at strict library level while still classifying
  the library as a11y-first by self-description.

## 4. reach/reach-ui — a11y_first: yes (pinned SHA b3d94d22811db6b5c0f272b9a7e2e3c1bb4699ae)

- **GitHub repository description** (the repo's own self-description on its
  GitHub page; README itself opens with the accessibility symbol):
  > "The Accessible Foundation for React Apps and Design Systems"
- **README.md heading** (pinned SHA):
  > "# Welcome to Reach UI Development ♿️"

---

*All evidence captured 2026-08-30 from the pinned census SHAs; see
`corpus.json` for the snapshot field.*
