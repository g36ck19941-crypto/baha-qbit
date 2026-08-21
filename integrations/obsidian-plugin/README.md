# Anime Bridge Obsidian plugin

This is a dependency-free desktop-only Obsidian command shell. It delegates all
domain rules and file safety to the Anime Bridge CLI rather than duplicating
them in JavaScript.

Install by copying this directory as `.obsidian/plugins/anime-bridge`, then
enable **Anime Bridge** under Community plugins. Configure either:

- packaged mode: `runnerPath` points to `anime-bridge.exe`, launcher left empty;
- source mode: `runnerPath` points to Python and launcher points to `launcher.py`.

The preview command never applies changes. The apply command shows a second
confirmation, and the CLI still performs its own full conflict check.
