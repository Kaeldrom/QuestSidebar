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
function Widget:Show() self.shown = true; if self.scripts.OnShow then self.scripts.OnShow(self) end end
function Widget:Hide() self.shown = false end
function Widget:IsShown() return self.shown end
function Widget:SetHeight(h) self.height = h end
function Widget:GetPoint() return "TOPRIGHT", nil, "TOPRIGHT", -40, -250 end
function CreateFrame(kind, name)
  local f = setmetatable({ scripts = {}, events = {}, kind = kind }, Widget)
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

-- the quest log: { header or quest }
LOG = {
  { title = "Ashenvale", isHeader = true },
  { title = "Bathran's Hair", level = 22, questID = 1, isComplete = false, obj = { { text = "Bathran's Hair: 2/5", finished = false } } },
  { title = "The Barrens", isHeader = true },
  { title = "Plainstrider Menace", level = 12, questID = 2, isComplete = true, obj = { { text = "Plainstrider Beak: 7/7", finished = true } } },
  { title = "Raptor Thieves", level = 15, questID = 3, isComplete = false, obj = { { text = "Raptor Head: 3/12", finished = false } } },
  { title = "Warrior", isHeader = true, isCollapsed = true },
  { title = "Hidden while collapsed", level = 20, questID = 4, isComplete = false, obj = {} },
}
local function visible()
  local v, skip = {}, false
  for _, e in ipairs(LOG) do
    if e.isHeader then v[#v+1] = e; skip = e.isCollapsed
    elseif not skip then v[#v+1] = e end
  end
  return v
end
WATCHED = { [3] = true }
C_QuestLog = {
  GetNumQuestLogEntries = function() return #visible() end,
  GetInfo = function(i) local e = visible()[i]; if not e then return nil end
    return { title = e.title, level = e.level, isHeader = e.isHeader, isCollapsed = e.isCollapsed, isComplete = e.isComplete, questID = e.questID or 0 } end,
  GetQuestObjectives = function(id) for _, e in ipairs(LOG) do if e.questID == id then return e.obj end end end,
  GetQuestWatchType = function(id) return WATCHED[id] and 0 or nil end,
  AddQuestWatch = function(id) WATCHED[id] = true end,
  RemoveQuestWatch = function(id) WATCHED[id] = nil end,
  GetQuestLink = function(id) return "[quest " .. id .. "]" end,
}
function ExpandQuestHeader(i) local e = visible()[i]; if e and e.isHeader then e.isCollapsed = false; calls[#calls+1] = "expand " .. e.title end end
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

def shown():
    out = []
    for l in lua.eval("QuestSidebar.UI.Lines()").values():
        if l.shown:
            out.append((l.kind, l.text.text))
    return out
def texts(): return [t for _, t in shown()]
def headers(): return [t for k, t in shown() if k == "header"]

ev("PLAYER_LOGIN")
check("panel shown", lua.eval("QuestSidebarFrame:IsShown()"))
check("blizzard tracker hidden", not lua.eval("ObjectiveTrackerFrame:IsShown()"))
ev("PLAYER_ENTERING_WORLD")
check("collapsed blizzard header expanded", "expand Warrior" in list(lua.eval("calls").values()))
check("quest under collapsed header read", any(g.zone == "Warrior" and len(g.quests) == 1 for g in lua.eval("QuestSidebar.ReadLog()").values()))
check("current zone first", "The Barrens" in headers()[0] and "here" in headers()[0])
check("all zones listed", len(headers()) == 3)
check("barrens open", any("Raptor Thieves" in t for t in texts()))
check("objectives shown", any("Raptor Head: 3/12" in t for t in texts()))
check("ashenvale closed", not any("Bathran" in t for t in texts()))
check("complete quest marked", any("Plainstrider" in t and "Ready to turn in" in t for t in texts()))
check("finished quest's objectives hidden", not any("Plainstrider Beak" in t for t in texts()))
check("tracked marker", any("Raptor Thieves" in t and "* " in t for t in texts()))
check("untracked quest still shown", any("Plainstrider Menace" in t for t in texts()))

# fly to Ashenvale
run("ZONE = 'Ashenvale'"); ev("ZONE_CHANGED_NEW_AREA")
check("ashenvale now first + open", "Ashenvale" in headers()[0] and any("Bathran" in t for t in texts()))
check("barrens closed after leaving", not any("Raptor Thieves" in t for t in texts()))

# open Barrens by hand, then move: it closes again
lines = lua.eval("QuestSidebar.UI.Lines()")
def click_header(name, button="LeftButton"):
    for l in lua.eval("QuestSidebar.UI.Lines()").values():
        if l.shown and l.kind == "header" and l.zone == name:
            l.scripts["OnClick"](l, button); return True
    return False
click_header("The Barrens")
check("manual open", any("Raptor Thieves" in t for t in texts()))
run("ZONE = 'Orgrimmar'"); ev("ZONE_CHANGED_NEW_AREA")
check("manual open closes on zone change", not any("Raptor Thieves" in t for t in texts()))
check("no quests here: log order", "Ashenvale" in headers()[0])

# pin Barrens (shift-click): stays open everywhere
run("SHIFT = true"); click_header("The Barrens"); run("SHIFT = false")
check("pinned label", any("The Barrens" in h and "pinned" in h for h in headers()))
run("ZONE = 'Ashenvale'"); ev("ZONE_CHANGED_NEW_AREA")
check("pinned stays open + current open", any("Raptor Thieves" in t for t in texts()) and any("Bathran" in t for t in texts()))
check("pin saved", lua.eval("QuestSidebarDB.pinned['The Barrens']") is True)

# close the current zone by hand
click_header("Ashenvale")
check("current zone can be closed", not any("Bathran" in t for t in texts()))
click_header("Ashenvale")
check("and reopened", any("Bathran" in t for t in texts()))

# quest actions
def click_quest(name, button="LeftButton"):
    for l in lua.eval("QuestSidebar.UI.Lines()").values():
        if l.shown and l.kind == "quest" and name in l.text.text:
            l.scripts["OnClick"](l, button); return True
click_quest("Bathran")
check("click opens quest", "open 1" in list(lua.eval("calls").values()))
run("SHIFT = true"); click_quest("Bathran"); run("SHIFT = false")
check("shift-click links", "link [quest 1]" in list(lua.eval("calls").values()))
click_quest("Bathran", "RightButton"); run("run_timers()")
check("right-click tracks", lua.eval("WATCHED[1]") is True and any("Bathran" in t and "* " in t for t in texts()))

# quest log changes redraw (debounced)
run("table.insert(LOG, 2, { title = 'Elemental Bracers', level = 24, questID = 9, isComplete = false, obj = { { text = 'Intact Elemental Bracer: 0/5', finished = false } } })")
ev("QUEST_LOG_UPDATE"); ev("QUEST_LOG_UPDATE")
check("refresh debounced", lua.eval("#timers") == 1)
run("run_timers()")
check("new quest appears", any("Elemental Bracers" in t for t in texts()))

# settings
run("SlashCmdList.QUESTSIDEBAR('objectives')")
check("objectives off", not any("Intact Elemental" in t for t in texts()))
run("SlashCmdList.QUESTSIDEBAR('objectives')")
run("SlashCmdList.QUESTSIDEBAR('auto')")
run("ZONE = 'The Barrens'; QuestSidebarDB.pinned = {}"); ev("ZONE_CHANGED_NEW_AREA")
check("auto off: zone not opened", not any("Raptor Thieves" in t for t in texts()))
run("SlashCmdList.QUESTSIDEBAR('auto')")
run("SlashCmdList.QUESTSIDEBAR('tracker')")
check("tracker restored", lua.eval("ObjectiveTrackerFrame:IsShown()"))
run("SlashCmdList.QUESTSIDEBAR('tracker')")
check("tracker hidden again", not lua.eval("ObjectiveTrackerFrame:IsShown()"))

# minimise + hide
run("QuestSidebarFrame.scripts = QuestSidebarFrame.scripts")
run("QuestSidebarDB.minimized = true; QuestSidebar.Refresh()")
check("minimised hides lines", len(shown()) == 0)
run("QuestSidebarDB.minimized = nil; QuestSidebar.Refresh()")
run("SlashCmdList.QUESTSIDEBAR('')")
check("slash hides panel", not lua.eval("QuestSidebarFrame:IsShown()") and lua.eval("ObjectiveTrackerFrame:IsShown()"))
run("SlashCmdList.QUESTSIDEBAR('')")
check("slash shows panel", lua.eval("QuestSidebarFrame:IsShown()") and not lua.eval("ObjectiveTrackerFrame:IsShown()"))

# empty log
run("LOG = {}; QuestSidebar.Refresh()")
check("empty log message", any("empty" in t for t in texts()))
run("SlashCmdList.QUESTSIDEBAR('help')")

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
