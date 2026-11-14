# Quest Sidebar

Your whole quest log down the side of the screen, where the quest tracker normally sits. It shows **every quest, tracked or not**, grouped by zone.

- **The zone you're in opens by itself and jumps to the top.** Fly to the Barrens and the Barrens quests open. Fly on to Ashenvale and those open instead, while the Barrens closes.
- **Click a zone** to open or close it. **Shift-click** pins it open everywhere you go.
- Each quest shows its level (coloured by difficulty), its objectives with progress, and **Ready to turn in** when it's done. A `*` marks tracked quests.
- **Click a quest** to open it in the quest log, **Shift-click** to link it in chat, and **right-click** to track or untrack it (for Questie arrows, for example).
- Drag the panel to move it, scroll it with the mouse wheel, and use `-` to shrink it to its title bar.

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
| `/qsb reset` | Move it back to the side and unpin all zones |

Settings and pinned zones are saved per character.

## Install

Download the release zip and extract it into `World of Warcraft\_forever_\Interface\AddOns\`.

## Tests

`pip install lupa`, then run `python tests/test_questsidebar.py`.
