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

`v0.4.0.dev0` includes the Bangumi scanner, conservative Bahamut matching core,
conflict-safe Obsidian import core, and preview-first local qBittorrent RSS
control. Authenticated Bahamut automation and the final GUI remain pending. See
[the user guide](docs/USER_GUIDE.md), [live demo record](docs/DEMO.md),
[project status](docs/STATUS.md),
[tasks](docs/TASKS.md), and [change log](docs/CHANGELOG.md).

Source-checkout example:

```powershell
python launcher.py scan --date 2026-08-21
```

The candidate output is deliberately not a formal Obsidian library entry until
the Bahamut subtraction and checkbox import milestones are complete.

No credentials or authenticated account state belong in this repository.
