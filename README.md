# Anime Bridge (`baha-qbit`)

Anime Bridge is a local-first bridge between Bangumi, Bahamut Anime Crazy,
Obsidian, and qBittorrent. The project is being delivered incrementally so each
external integration remains replaceable and testable.

## Confirmed scope

- Detect titles whose first release date falls in the current anime quarter.
- Include TV, WEB, movie, and sequel subjects; exclude OVA and other subjects.
- Preserve an extension point for historical or manually selected quarters.
- Stage candidates as checkbox-based Obsidian Markdown before formal import.
- Later subtract the current user's Bahamut favorites and manage approved RSS
  subscriptions and qBittorrent rules through preview-first operations.

## Current milestone

`v0.1.0` is in development. See [project status](docs/STATUS.md),
[tasks](docs/TASKS.md), and [change log](docs/CHANGELOG.md).

No credentials or authenticated account state belong in this repository.

