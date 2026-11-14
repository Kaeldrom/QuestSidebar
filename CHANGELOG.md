# Changelog

## 1.4.0 - 2026-11-14

- New **Share all quests** button in the Current Zone tab. In a party, it shares every quest you have for the zone you are in, one after another, with a short gap between each.
- If a party member is busy (they still have the last shared quest open), that quest is tried again at the end, up to 3 times.
- Quests that the game won't let you share are skipped, and the chat message tells you how many.
- When you're not in a group the button is greyed out. `/qsb share` does the same as the button.

## 1.3.1 - 2026-11-14

- The settings button is now a proper cog symbol. It is gold when you hover over it.

## 1.3.0 - 2026-11-14

- The close X is replaced by a **minimize** button. It shrinks the window to its title bar, and clicking again restores it to the size you chose. `/qsb min` does the same.
- **Minimap button:** click to show or hide the sidebar, right-click for settings, drag to move it around the minimap. You can turn it off in settings or with `/qsb minimap`.
- Reset size & position also restores a minimized window.

## 1.2.0 - 2026-11-14

- Settings panel: click the small cog in the title bar (or `/qsb settings`). It has an **Opacity** slider, a **Size** slider, and checkboxes for opening the zone you're in, showing objectives, hiding Blizzard's tracker, and locking the position.
- Opacity fades the window background and zone bars only. Quest text and buttons stay solid. `/qsb opacity 70` works too.
- Zone bars restyled after the world-map quest log: a dark brown bar with a thin bronze frame, the zone name in large off-white text, and a flat yellow - (open) or + (closed). In the All tab, the zone you're in reads gold.

## 1.1.0 - 2026-11-14

- New look, based on the quest log in the world map: grey zone bars with gold names and -/+ buttons, quest icons, "[level] Title" coloured by difficulty, "- objective" lines, (Dungeon)/(Elite) tags, an open button and a track checkbox on every quest.
- Two tabs: **Current Zone** (the default) shows only the quests for where you are, with each quest's objective text, and updates as you travel. **All** shows every zone like before.
- Zones are sorted A-Z. A leading "The" is ignored, so The Barrens sorts under B.
- The window can be resized with the grip in the bottom-right corner, and keeps its size and position. Opening and closing zones scrolls inside the window instead of making it grow or move. There's a scroll bar when the list is longer than the window.
- Click a quest to show or hide its objectives.
- Closing the window (X) brings Blizzard's tracker back. Reopening it starts on Current Zone.

## 1.0.0 - 2026-11-14

- First release.
