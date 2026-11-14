# Changelog

## 1.6.0 - 2026-11-14

- Finished quests stand out much more in the **Current Zone** tab:
  - They have their own **Ready to turn in** section at the top, with a count. The rest follow under **In progress**.
  - Each one has a gold edge down the left, a stronger gold highlight, and a green tick next to "Ready to turn in".
  - When the game provides it, the quest says who to hand it in to (for example "Return to Regthar Deathgate..."). If it doesn't, you see the usual quest summary.
- The finished count on zone headers is green.

## 1.5.0 - 2026-11-14

- **Party markers.** In a party, each quest shows how many party members have it, for example `1/2`. Hover over the quest to see who has it and who doesn't.
- **Share all quests** now skips quests your whole party already has.
- **Right-click menu** on a quest: Track, Share with party, Link in chat, Show in quest log, and Abandon quest (it asks first). Right-click used to only track the quest.
- **Auto-share new quests with party.** A new setting, **off by default**. When it's on, any quest you pick up while in a party is shared straight away. Quests the whole party already has are not sent back. `/qsb autoshare` turns it on and off too.
- **Ready to turn in** quests move to the top of their zone with a soft gold highlight.
- **Search box** on the All tab. It searches quest names, objectives and zone names.
- **Quest log full warning.** The count in the title turns orange when you have 3 or fewer slots left, and red when the log is full.
- **Hide grey quests.** A new setting (`/qsb grey`) that hides quests far below your level. Quests that are ready to turn in always stay visible.

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
