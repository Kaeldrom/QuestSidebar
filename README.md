# Quest Sidebar

Your whole quest log down the side of the screen, where the quest tracker normally sits. It shows **every quest, tracked or not**, grouped by zone.

- **Two tabs.** **Current Zone** (the default) shows just the quests for where you are, with their objective text, and switches as you fly from the Barrens to Ashenvale. **All** lists every zone, A-Z, with the zone you're in opened for you.
- It looks like the quest log in the world map: zone bars with -/+ buttons, "[level] Title" coloured by difficulty, "- objective" lines, (Dungeon)/(Elite) tags, an open button and a track checkbox.
- **Click a zone** to open or close it. **Shift-click** pins it open everywhere you go.
- **Click a quest** to show or hide its objectives, **Shift-click** to link it, and **right-click** or use the checkbox to track it. The ▶ button opens it in the quest log.
- **Resize** with the grip in the bottom-right corner, **drag** to move, and scroll with the mouse wheel or the scroll bar. Size and position are remembered, and opening zones never makes the window grow or jump.

By default it hides Blizzard's quest tracker so the two don't overlap (`/qsb tracker` to change that). Zone headers come from your quest log, so class, profession and dungeon quests get their own groups too.

## Commands

| Command | What it does |
|---|---|
| `/qsb` | Show/hide the sidebar |
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
