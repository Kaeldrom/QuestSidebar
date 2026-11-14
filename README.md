# Quest Sidebar

Your whole quest log down the side of the screen, where the quest tracker normally sits. It shows **every quest, tracked or not**, grouped by zone.

- **Two tabs.** **Current Zone** (the default) shows just the quests for where you are, with their objective text, and switches as you fly from the Barrens to Ashenvale. **All** lists every zone, A-Z, with the zone you're in opened for you.
- It looks like the quest log in the world map: zone bars with -/+ buttons, "[level] Title" coloured by difficulty, "- objective" lines, (Dungeon)/(Elite) tags, an open button and a track checkbox.
- **Click a zone** to open or close it. **Shift-click** pins it open everywhere you go.
- **Click a quest** to show or hide its objectives, **Shift-click** to link it, and **right-click** or use the checkbox to track it. The ▶ button opens it in the quest log.
- **Resize** with the grip in the bottom-right corner, **drag** to move, and scroll with the mouse wheel or the scroll bar. Size and position are remembered, and opening zones never makes the window grow or jump.

The **minimize** button in the top corner shrinks it to its title bar. The **minimap button** shows or hides it (right-click for settings, drag to move). Click the small **cog** in the title bar for settings: opacity, size, and the options below.

By default it hides Blizzard's quest tracker so the two don't overlap (`/qsb tracker` to change that). Zone headers come from your quest log, so class, profession and dungeon quests get their own groups too.

## Commands

| Command | What it does |
|---|---|
| `/qsb` | Show/hide the sidebar (or click the minimap button) |
| `/qsb share` | Share all your quests for the zone you are in with your party (same as the **Share all quests** button) |
| `/qsb autoshare` | Share quests you pick up with your party on/off (off by default, also in settings) |
| `/qsb grey` | Hide grey (low level) quests on/off |
| `/qsb route` | Fastest route to your tracked quest here (or Ctrl-click any quest, or use its map button). Full routes need Shortest Path Forever |
| `/qsb min` | Minimize to the title bar / restore |
| `/qsb minimap` | Minimap button on/off |
| `/qsb settings` | Open the settings (same as the cog in the title bar) |
| `/qsb opacity 70` | Background opacity, 10 to 100 |
| `/qsb auto` | Open the zone you're in automatically on/off |
| `/qsb tracker` | Hide Blizzard's quest tracker on/off |
| `/qsb objectives` | Objective lines on/off |
| `/qsb lock` | Stop the panel being dragged |
| `/qsb scale 0.8` | Make it smaller or bigger (0.5 to 2) |
| `/qsb reset` | Default size and position, unpin all zones |

Settings and pinned zones are saved per character.

## Install

Download the release zip and extract it into `World of Warcraft\_forever_\Interface\AddOns\`.

## Tests

`pip install lupa`, then run `python tests/test_questsidebar.py`.
