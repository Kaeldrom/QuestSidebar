"""Runs Quest Sidebar against a mock WoW API in real Lua 5.1.  pip install lupa  then:  python tests/test_questsidebar.py"""
import os, sys
try:
    from lupa import lua51 as L
except ImportError:
    import lupa as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MOCK = r'''
printed = {}; calls = {}
function wipe(t) for k in pairs(t) do t[k] = nil end return t end
DEFAULT_CHAT_FRAME = { AddMessage = function(_, m) printed[#printed+1] = m end }
timers = {}
C_Timer = { After = function(_, f) timers[#timers+1] = f end }
function run_timers() local t = timers; timers = {}; for _, f in ipairs(t) do f() end end

Widget = {}
Widget.__index = function(t, k)
  local v = rawget(Widget, k); if v ~= nil then return v end
  if type(k) == "string" and k:find("^%u") then return function() end end
end
function Widget:SetScript(k, fn) self.scripts[k] = fn end
function Widget:GetScript(k) return self.scripts[k] end
function Widget:HookScript(k, fn) self.scripts[k] = fn end
function Widget:RegisterEvent(e) self.events[e] = true end
function Widget:CreateFontString() return CreateFrame("FontString") end
function Widget:CreateTexture() return CreateFrame("Texture") end
function Widget:SetText(t) self.text = t end
function Widget:GetText() return self.text or "" end
function Widget:GetStringHeight() local n = 1; for _ in (self.text or ""):gmatch("\n") do n = n + 1 end; return n * 14 end
function Widget:GetStringWidth() return #(self.text or "") * 5 end
function Widget:Show() local was = self.shown; self.shown = true; if not was and self.scripts.OnShow then self.scripts.OnShow(self) end end
function Widget:Hide() local was = self.shown; self.shown = false; if was and self.scripts.OnHide then self.scripts.OnHide(self) end end
function Widget:IsShown() return self.shown end
function Widget:SetSize(w, h) self.w, self.h = w, h end
function Widget:SetHeight(h) self.h = h end
function Widget:SetWidth(w) self.w = w end
function Widget:GetHeight() return self.h or 300 end
function Widget:GetWidth() return self.w or 300 end
function Widget:GetLeft() return 1500 end
function Widget:GetTop() return 900 end
function Widget:SetChecked(v) self.checked = v end
function Widget:GetChecked() return self.checked end
function Widget:SetVerticalScroll(v) self.vscroll = v end
function Widget:SetMinMaxValues(a, b) self.min, self.max = a, b end
function Widget:SetValue(v) self.value = v end
function Widget:SetTexture(t) self.texture = t end
function Widget:Disable() self.disabled = true end
function Widget:Enable() self.disabled = false end
function Widget:GetParent() return self.parent end
function CreateFrame(kind, name, parent)
  local f = setmetatable({ scripts = {}, events = {}, kind = kind, parent = parent }, Widget)
  if name then _G[name] = f end
  return f
end
UIParent = CreateFrame("Frame"); GameTooltip = CreateFrame("GameTooltip")
ObjectiveTrackerFrame = CreateFrame("Frame"); ObjectiveTrackerFrame.shown = true
function InCombatLockdown() return COMBAT end
SHIFT = false
function IsShiftKeyDown() return SHIFT end
function IsModifiedClick() return SHIFT end
function GetQuestDifficultyColor(l) return { r = 1, g = l > 20 and 0.1 or 1, b = 0.1 } end

LOG = {
  { title = "The Barrens", isHeader = true },
  { title = "Plainstrider Menace", level = 12, questID = 2, isComplete = true, obj = { { text = "Plainstrider Beak: 7/7", finished = true } } },
  { title = "Raptor Thieves", level = 15, questID = 3, isComplete = false, obj = { { text = "Raptor Head: 3/12", finished = false } } },
  { title = "Ashenvale", isHeader = true },
  { title = "Stonetalon Standstill", level = 25, questID = 1, isComplete = false, obj = { { text = "0/12 Befouled Water Elemental slain", finished = false } } },
  { title = "Crafting", isHeader = true },
  { title = "Craftsman's Writ", level = 60, questID = 7, isComplete = false, obj = {} },
  { title = "Blackfathom Deeps", isHeader = true, isCollapsed = true },
  { title = "The Essence of Aku'Mai", level = 22, questID = 4, isComplete = false, obj = { { text = "11/20 Sapphire of Aku'Mai", finished = false } } },
}
TAGS = { [4] = "Dungeon" }
DETAILS = { [3] = "Bring 12 Raptor Heads to Regthar Deathgate.", [1] = "Scout the gazebo on Mystral Lake." }
local function visible()
  local v, skip = {}, false
  for _, e in ipairs(LOG) do
    if e.isHeader then v[#v+1] = e; skip = e.isCollapsed
    elseif not skip then v[#v+1] = e end
  end
  return v
end
WATCHED = { [3] = true }
SELECTED = 99
C_QuestLog = {
  GetNumQuestLogEntries = function() return #visible() end,
  GetInfo = function(i) local e = visible()[i]; if not e then return nil end
    return { title = e.title, level = e.level, isHeader = e.isHeader, isCollapsed = e.isCollapsed, isComplete = e.isComplete, questID = e.questID or 0 } end,
  GetQuestObjectives = function(id) for _, e in ipairs(LOG) do if e.questID == id then return e.obj end end end,
  GetQuestWatchType = function(id) return WATCHED[id] and 0 or nil end,
  AddQuestWatch = function(id) WATCHED[id] = true end,
  RemoveQuestWatch = function(id) WATCHED[id] = nil end,
  GetQuestLink = function(id) return "[quest " .. id .. "]" end,
  GetQuestTagInfo = function(id) return TAGS[id] and { tagName = TAGS[id] } or nil end,
  GetSelectedQuest = function() return SELECTED end,
  SetSelectedQuest = function(id) SELECTED = id end,
}
function GetQuestLogQuestText() calls[#calls+1] = "read " .. SELECTED; return "desc", DETAILS[SELECTED] or "" end
function ExpandQuestHeader(i) local e = visible()[i]; if e and e.isHeader then e.isCollapsed = false end end
ZONE = "The Barrens"
function GetRealZoneText() return ZONE end
function GetZoneText() return ZONE end
function QuestMapFrame_OpenToQuestDetails(id) calls[#calls+1] = "open " .. id end
function ChatEdit_InsertLink(l) calls[#calls+1] = "link " .. l end
SlashCmdList = {}
'''

passed = failed = 0
def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL:", name)

lua = L.LuaRuntime(unpack_returned_tuples=True)
lua.execute(MOCK)
for f in ("QuestSidebar.lua", "QuestSidebar_UI.lua"):
    lua.execute("local f = assert(loadstring(...)); f('QuestSidebar')", open(os.path.join(ROOT, f), encoding="utf-8").read())
ev = lua.eval("function(e, ...) QuestSidebar.frame:GetScript('OnEvent')(QuestSidebar.frame, e, ...) end")
run = lua.execute
calls = lambda: list(lua.eval("calls").values())

def hdrs(): return [h.zone for h in lua.eval("QuestSidebar.UI.Headers()").values() if h.shown]
def qrows(): return [q for q in lua.eval("QuestSidebar.UI.Quests()").values() if q.shown]
def qtitles(): return [q.title.text for q in qrows()]
def has(name): return any(name in t for t in qtitles())
def row(name):
    for q in qrows():
        if name in q.title.text: return q
def header(name):
    for h in lua.eval("QuestSidebar.UI.Headers()").values():
        if h.shown and h.zone == name: return h

ev("PLAYER_LOGIN"); ev("PLAYER_ENTERING_WORLD")
P = "QuestSidebarFrame"
check("panel shown", lua.eval(P + ":IsShown()"))
check("tracker hidden", not lua.eval("ObjectiveTrackerFrame:IsShown()"))
check("Current Zone tab by default", lua.eval("QuestSidebar.UI.tab") == "zone")

# --- Current Zone tab ---------------------------------------------------------
check("only the current zone", hdrs() == ["The Barrens"])
check("its quests", has("Raptor Thieves") and has("Plainstrider Menace") and not has("Stonetalon"))
r = row("Raptor Thieves")
check("level + title", "[15] Raptor Thieves" in r.title.text)
check("objective with dash", r.objectives.text == "- Raptor Head: 3/12")
check("quest details shown", r.details.text == DETAILS3 if (DETAILS3 := "Bring 12 Raptor Heads to Regthar Deathgate.") else False)
check("selection restored after reading details", lua.eval("SELECTED") == 99)
check("tracked checkbox", r.track.checked is True and row("Plainstrider").track.checked is False)
p = row("Plainstrider")
check("complete: ready to turn in", "Ready to turn in" in p.objectives.text and "Beak" not in p.objectives.text)
check("complete icon", p.icon.texture.endswith("ActiveQuestIcon") and r.icon.texture.endswith("IncompleteQuestIcon"))

# details are cached (log selection isn't poked every redraw)
n_reads = sum(1 for c in calls() if c.startswith("read"))
run("QuestSidebar.Refresh()")
check("details cached", sum(1 for c in calls() if c.startswith("read")) == n_reads)

# fly to Ashenvale: current zone tab follows
run("ZONE = 'Ashenvale'"); ev("ZONE_CHANGED_NEW_AREA")
check("current zone follows the player", hdrs() == ["Ashenvale"] and has("Stonetalon") and not has("Raptor"))
check("ashenvale details", row("Stonetalon").details.text == "Scout the gazebo on Mystral Lake.")
run("ZONE = 'Orgrimmar'"); ev("ZONE_CHANGED_NEW_AREA")
check("no quests here message", hdrs() == [] and lua.eval("QuestSidebar.UI.Empty():IsShown()") and "Orgrimmar" in lua.eval("QuestSidebar.UI.Empty().text"))

# --- All tab -----------------------------------------------------------------
run("QuestSidebar.UI.SelectTab('all')")
check("A-Z (The ignored)", hdrs() == ["Ashenvale", "The Barrens", "Blackfathom Deeps", "Crafting"])
check("collapsed Blizzard header read", lua.eval("QuestSidebar.ReadLog()[4].zone") == "Blackfathom Deeps")
check("zones closed away from them", qrows() == [])
run("ZONE = 'The Barrens'"); ev("ZONE_CHANGED_NEW_AREA")
check("current zone auto-opens in All", has("Raptor Thieves") and not has("Stonetalon"))
check("all tab: no details text", row("Raptor Thieves").details.text == "")
check("open/close icons", header("The Barrens").toggle.texture.endswith("MinusButton-Up") and header("Ashenvale").toggle.texture.endswith("PlusButton-Up"))
header("Blackfathom Deeps").scripts["OnClick"](header("Blackfathom Deeps"))
q = row("Essence")
check("dungeon tag", q is not None and "(Dungeon)" in q.tag.text)
run("SHIFT = true"); header("Crafting").scripts["OnClick"](header("Crafting")); run("SHIFT = false")
run("ZONE = 'Ashenvale'"); ev("ZONE_CHANGED_NEW_AREA")
check("pinned stays, hand-opened closes", has("Craftsman") and not has("Essence") and has("Stonetalon"))

# window keeps its size whatever opens
h_before = lua.eval(P + ".h")
for z in ["The Barrens", "Blackfathom Deeps"]:
    header(z).scripts["OnClick"](header(z))
check("window height unchanged by expanding", lua.eval(P + ".h") == h_before)
check("scrolls when content is taller", lua.eval("QuestSidebar.UI.maxScroll") > 0)
run("QuestSidebar.UI.Scroll(-100)")
check("scroll clamps at bottom", lua.eval("QuestSidebar.UI.bar.value") == lua.eval("QuestSidebar.UI.maxScroll"))
run("QuestSidebar.UI.Scroll(100)")
check("scroll clamps at top", lua.eval("QuestSidebar.UI.bar.value") == 0)

# resize: saved, survives reload
run(P + ".scripts.OnSizeChanged(" + P + ", 360, 600); run_timers()")
check("size saved", lua.eval("QuestSidebarDB.size[1]") == 360 and lua.eval("QuestSidebarDB.size[2]") == 600)
check("rows follow the new width", row("Stonetalon").w == 360 - 34)

# quest interactions
r = row("Stonetalon")
r.scripts["OnClick"](r, "LeftButton")
check("click folds objectives", row("Stonetalon").objectives.text == "")
row("Stonetalon").scripts["OnClick"](row("Stonetalon"), "LeftButton")
check("click unfolds", "Befouled" in row("Stonetalon").objectives.text)
r = row("Stonetalon")
r.open.scripts["OnClick"](r.open)
check("open button", "open 1" in calls())
r.track.scripts["OnClick"](r.track); run("run_timers()")
check("checkbox tracks", lua.eval("WATCHED[1]") is True and row("Stonetalon").track.checked is True)
run("SHIFT = true"); row("Stonetalon").scripts["OnClick"](row("Stonetalon"), "LeftButton"); run("SHIFT = false")
check("shift-click links", "link [quest 1]" in calls())

# close / Alt+Z / reopen
run(P + ":Hide()")
check("closing brings the tracker back", lua.eval("ObjectiveTrackerFrame:IsShown()") and lua.eval("QuestSidebarDB.hidden") is True)
run(P + ":Show()")
check("reopens on Current Zone", lua.eval("QuestSidebar.UI.tab") == "zone" and not lua.eval("ObjectiveTrackerFrame:IsShown()"))
run("local f = " + P + "; f.shown = false; f.IsShown = function() return true end; f.scripts.OnHide(f); f.IsShown = nil; f.shown = true")
check("Alt+Z doesn't count as closing", lua.eval("QuestSidebarDB.hidden") is None)

# reload keeps size + position
saved = lua.eval("QuestSidebarDB")
lua2 = L.LuaRuntime(unpack_returned_tuples=True); lua2.execute(MOCK)
lua2.execute("QuestSidebarDB = { settings = { autoZone = true, hideTracker = true, showObjectives = true, scale = 1 }, pinned = {}, size = { 360, 600 }, point = { 'TOPLEFT', 'BOTTOMLEFT', 1500, 900 } }")
for f in ("QuestSidebar.lua", "QuestSidebar_UI.lua"):
    lua2.execute("local f = assert(loadstring(...)); f('QuestSidebar')", open(os.path.join(ROOT, f), encoding="utf-8").read())
lua2.eval("function() QuestSidebar.frame:GetScript('OnEvent')(QuestSidebar.frame, 'PLAYER_LOGIN') end")()
check("size restored", lua2.eval("QuestSidebarFrame.w") == 360 and lua2.eval("QuestSidebarFrame.h") == 600)

# slash
run("SlashCmdList.QUESTSIDEBAR('objectives'); QuestSidebar.UI.SelectTab('zone'); ZONE = 'The Barrens'"); ev("ZONE_CHANGED_NEW_AREA")
check("objectives off", row("Raptor").objectives.text == "")
run("SlashCmdList.QUESTSIDEBAR('objectives')")
run("SlashCmdList.QUESTSIDEBAR('reset')")
check("reset size", lua.eval(P + ".w") == 300 and lua.eval("QuestSidebarDB.size") is None)
run("SlashCmdList.QUESTSIDEBAR('help')")

run("LOG = {}; QuestSidebar.UI.SelectTab('all')")
check("empty log", "empty" in lua.eval("QuestSidebar.UI.Empty().text"))

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
