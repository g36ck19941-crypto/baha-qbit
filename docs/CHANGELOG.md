# Changelog

All notable changes are recorded here. The project follows semantic versioning.

## [Unreleased]

### Planned

- Interactive Bahamut login, favorite export, and confidence-aware difference.

### Added

- Pure standard-library parser for user-exported Bahamut `mygather.php` HTML,
  including theme-list scoping, title extraction, SN parsing, deduplication, and
  empty-collection detection.
- Bangumi infobox alias extraction and normalized title variants.
- Conservative cross-site matcher and difference workflow: normalized exact
  matches may be excluded; fuzzy matches remain candidates for manual review.
- Offline `parse-bahamut-html` diagnostic command and representative fixtures.

### Verification

- 11 local tests pass. Authenticated Bahamut access remains unverified and is
  not represented as complete.

## [0.1.0] - 2026-08-21

### Added

- Project charter, durable memory, status panel, agile task board, and repository
  operating rules.
- Frozen definitions for quarter boundaries, included categories, Obsidian
  compatibility, secret handling, and GitHub publishing.
- Dependency-free Python domain model for four quarters and the approved TV,
  Movie, WEB, sequel, and Japanese-origin policy.
- Paginated read-only Bangumi `/v0/subjects` adapter with contextual failures.
- Current-quarter scanner with exact date filtering and subject-ID deduplication.
- Atomic Obsidian candidate renderer with checkboxes, covers, summaries, source
  links, and machine-readable item markers.
- Representative domain, pagination, filtering, and rendering tests.
- Source-checkout launcher, example configuration, architecture/user guides,
  live demonstration record, and newest-three Git archive snapshot utility.

### Safety

- Candidate notes are tagged `anime-bridge-candidates`, not `bangumi`.
- v0.1.0 output warns that Bahamut subtraction has not yet occurred.
- Items without Bangumi's `日本` meta tag are counted and excluded rather than
  being silently mixed into the Japanese seasonal list.

## [0.0.0] - 2026-08-21

- Project initialized after feasibility and risk review.
