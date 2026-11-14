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
function Widget:CreateTexture() local t = CreateFrame("Texture"); self.regions = self.regions or {}; table.insert(self.regions, t); return t end
function Widget:GetRegions() return unpack(self.regions or {}) end
function Widget:GetObjectType() return self.kind end
function Widget:SetAlpha(a) self.alpha = a end
function Widget:GetMinMaxValues() return self.min or 0, self.max or 1 end
function Widget:GetValue() return self.value end
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
function Widget:SetValue(v) self.value = v; if self.scripts.OnValueChanged then self.scripts.OnValueChanged(self, v) end end
function Widget:SetTexture(t) self.texture = t end
function Widget:Disable() self.disabled = true end
function Widget:Enable() self.disabled = false end
function Widget:GetParent() return self.parent end
function Widget:SetNormalTexture(t) self.normal = t end
function Widget:GetCenter() return 0, 0 end
function Widget:GetEffectiveScale() return 1 end
function CreateFrame(kind, name, parent, template)
  local f = setmetatable({ scripts = {}, events = {}, kind = kind, parent = parent }, Widget)
  if name then _G[name] = f end
  if template == "BasicFrameTemplateWithInset" then
    f.CloseButton = setmetatable({ scripts = {}, events = {}, kind = "Button", shown = true }, Widget)
    f.Inset = setmetatable({ scripts = {}, events = {}, kind = "Frame", shown = true }, Widget)
  end
  return f
end
Minimap = CreateFrame("Frame"); Minimap.w = 140
CURSOR = { 0, 100 }
function GetCursorPosition() return CURSOR[1], CURSOR[2] end
UIParent = CreateFrame("Frame"); GameTooltip = CreateFrame("GameTooltip"); tinsert = table.insert; UISpecialFrames = {}
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
GROUP = false
function IsInGroup() return GROUP end
PUSHABLE = {}
PUSHES = {}
function QuestLogPushQuest() PUSHES[#PUSHES+1] = SELECTED end
C_QuestLog.IsPushableQuest = function(id) return PUSHABLE[id] ~= false end
ERR_QUEST_PUSH_BUSY_S = "%s is busy."
PARTY = {}            -- { {name=, quests={[id]=true}} }
function GetNumSubgroupMembers() return #PARTY end
function UnitExists(u) local i = tonumber(u:match("party(%d)")); return i and PARTY[i] ~= nil end
function UnitName(u) local i = tonumber(u:match("party(%d)")); return i and PARTY[i] and PARTY[i].name end
C_QuestLog.IsUnitOnQuest = function(u, id) local i = tonumber(u:match("party(%d)")); return PARTY[i].quests[id] == true end
MYLEVEL = 20
function UnitLevel() return MYLEVEL end
MENU = nil
MenuUtil = { CreateContextMenu = function(owner, gen)
  MENU = { items = {} }
  local root = { CreateTitle = function(_, t) MENU.title = t end,
                 CreateButton = function(_, t, f) local b = { text = t, func = f, enabled = true }
                   function b:SetEnabled(v) self.enabled = v end
                   table.insert(MENU.items, b); return b end }
  gen(owner, root)
end }
StaticPopupDialogs = {}
POPUP = nil
function StaticPopup_Show(which, a, b, data) POPUP = { which = which, text = a, data = data }; return POPUP end
ABANDONED = {}
C_QuestLog.SetAbandonQuest = function() ABANDON_SEL = SELECTED end
C_QuestLog.AbandonQuest = function() ABANDONED[#ABANDONED+1] = ABANDON_SEL end
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
check("dash when open, plus when closed", header("The Barrens").plus.shown is False and header("Ashenvale").plus.shown is True)
check("zone bar has a bronze frame", len(header("Ashenvale").border) == 4)
check("current zone gold in All", "|cffffd100The Barrens" in header("The Barrens").text.text)
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

# settings + opacity
check("cog is discreet", lua.eval("QuestSidebar.UI.cog.alpha") == 0.6)
lua.execute("QuestSidebar.UI.cog.scripts.OnClick(QuestSidebar.UI.cog)")
check("cog opens settings", lua.eval("QuestSidebarSettings:IsShown()"))
op = lua.eval("QuestSidebarSettings.items[1]")
check("opacity slider starts at 100%", "100%" in op.label.text)
lua.execute("QuestSidebarSettings.items[1].slider:SetValue(0.5)")
check("opacity saved", abs(lua.eval("QuestSidebarDB.settings.opacity") - 0.5) < 1e-9 and "50%" in lua.eval("QuestSidebarSettings.items[1]").label.text)
regs = [r for r in lua.eval("{QuestSidebarFrame:GetRegions()}").values() if r.kind == "Texture"]
check("window background faded", all(abs((r.alpha or 1) - 0.5) < 1e-9 for r in regs))
check("zone bars faded", all(abs(h.bar.alpha - 0.5) < 1e-9 for h in lua.eval("QuestSidebar.UI.Headers()").values()))
check("text not faded", all(getattr(h.text, "alpha", None) is None for h in lua.eval("QuestSidebar.UI.Headers()").values()))
lua.execute("QuestSidebarSettings.items[1].slider:SetValue(0.02)")
lua.execute("QuestSidebarSettings.items[1].slider.scripts.OnMouseWheel(QuestSidebarSettings.items[1].slider, -5)")
check("wheel clamps to min", lua.eval("QuestSidebarSettings.items[1].slider.value") >= 0)
lua.execute("SlashCmdList.QUESTSIDEBAR('opacity 70')")
check("/qsb opacity 70", abs(lua.eval("QuestSidebarDB.settings.opacity") - 0.7) < 1e-9)
chk = lua.eval("QuestSidebarSettings.items[4]")
lua.execute("local c = QuestSidebarSettings.items[4]; c:SetChecked(false); c.scripts.OnClick(c)")
check("objectives checkbox", lua.eval("QuestSidebarDB.settings.showObjectives") is False)
lua.execute("local c = QuestSidebarSettings.items[4]; c:SetChecked(true); c.scripts.OnClick(c)")
lua.execute("local c = QuestSidebarSettings.items[5]; c:SetChecked(false); c.scripts.OnClick(c)")
check("tracker checkbox brings tracker back", lua.eval("ObjectiveTrackerFrame:IsShown()"))
lua.execute("QuestSidebar.UI.ToggleSettings()")
check("cog closes settings", not lua.eval("QuestSidebarSettings:IsShown()"))
lua.execute("SlashCmdList.QUESTSIDEBAR('settings')")
check("/qsb settings opens", lua.eval("QuestSidebarSettings:IsShown()"))

# ---- minimize instead of X ---------------------------------------------------
lua.execute("QuestSidebarSettings:Hide(); QuestSidebarFrame:Show(); QuestSidebar.UI.SelectTab('all')")
check("X hidden", lua.eval("QuestSidebarFrame.CloseButton:IsShown()") is False)
lua.execute("QuestSidebarFrame.CloseButton:Show()")
check("X stays hidden", lua.eval("QuestSidebarFrame.CloseButton:IsShown()") is False)
check("minimize button styled", "SmallerButton" in (lua.eval("QuestSidebar.UI.minBtn.normal") or ""))
size_before = (lua.eval("QuestSidebarDB.size[1]"), lua.eval("QuestSidebarDB.size[2]")) if lua.eval("QuestSidebarDB.size") else None
lua.execute("QuestSidebar.UI.minBtn.scripts.OnClick(QuestSidebar.UI.minBtn)")
check("minimized: title bar only", lua.eval("QuestSidebarFrame.h") == 30 and lua.eval("QuestSidebarDB.minimized") is True)
check("minimized: list + tabs hidden", not lua.eval("QuestSidebarFrame") is None and lua.eval("QuestSidebarFrame.Inset.shown") is False)
check("restore button styled", "BiggerButton" in lua.eval("QuestSidebar.UI.minBtn.normal"))
lua.execute("QuestSidebarFrame.scripts.OnSizeChanged(QuestSidebarFrame, 300, 30)")
size_now = (lua.eval("QuestSidebarDB.size[1]"), lua.eval("QuestSidebarDB.size[2]")) if lua.eval("QuestSidebarDB.size") else None
check("minimizing doesn't overwrite chosen size", size_now == size_before)
lua.execute("QuestSidebar.Refresh()")
check("minimized: no rows drawn", lua.eval("QuestSidebarFrame.h") == 30)
lua.execute("QuestSidebar.UI.minBtn.scripts.OnClick(QuestSidebar.UI.minBtn)")
check("restored to chosen height", lua.eval("QuestSidebarDB.minimized") is None and lua.eval("QuestSidebarFrame.h") == (size_before[1] if size_before else 460) and lua.eval("QuestSidebarFrame.Inset.shown") is True)
lua.execute("SlashCmdList.QUESTSIDEBAR('min')")
check("/qsb min", lua.eval("QuestSidebarDB.minimized") is True)
lua.execute("SlashCmdList.QUESTSIDEBAR('reset')")
check("reset un-minimizes", lua.eval("QuestSidebarDB.minimized") is None and lua.eval("QuestSidebarFrame.h") == 460)

# ---- minimap button -------------------------------------------------------------
mb = "QuestSidebarMinimapButton"
check("minimap button exists + shown", lua.eval(mb + " ~= nil") and lua.eval(mb + ":IsShown()"))
lua.execute(mb + ".scripts.OnClick(" + mb + ", 'LeftButton')")
check("click hides sidebar", not lua.eval("QuestSidebarFrame:IsShown()") and lua.eval("ObjectiveTrackerFrame:IsShown()"))
lua.execute(mb + ".scripts.OnClick(" + mb + ", 'LeftButton')")
check("click shows sidebar", lua.eval("QuestSidebarFrame:IsShown()"))
lua.execute("QuestSidebarSettings:Hide(); " + mb + ".scripts.OnClick(" + mb + ", 'RightButton')")
check("right-click opens settings", lua.eval("QuestSidebarSettings:IsShown()"))
lua.execute(mb + ".scripts.OnDragStart(" + mb + "); " + mb + ".scripts.OnUpdate(); " + mb + ".scripts.OnDragStop(" + mb + ")")
check("drag saves angle (cursor straight up = 90)", abs(lua.eval("QuestSidebarDB.minimapAngle") - 90) < 1e-6)
lua.execute("local c = QuestSidebarSettings.items[7]; c:SetChecked(false); c.scripts.OnClick(c)")
check("settings checkbox hides minimap button", not lua.eval(mb + ":IsShown()") and lua.eval("QuestSidebarDB.settings.minimap") is False)
lua.execute("SlashCmdList.QUESTSIDEBAR('minimap')")
check("/qsb minimap brings it back", lua.eval(mb + ":IsShown()"))

# ---- share all quests -----------------------------------------------------------
def pushes(): return list(lua.eval("PUSHES").values())
def last_print(): p = lua.eval("printed"); return p[len(p)]
SB = "QuestSidebar.UI.shareBtn"
lua.execute("""LOG = {
  { title = "The Barrens", isHeader = true },
  { title = "Plainstrider Menace", level = 12, questID = 2, isComplete = true, obj = {} },
  { title = "Raptor Thieves", level = 15, questID = 3, isComplete = false, obj = {} },
  { title = "Ashenvale", isHeader = true },
  { title = "Stonetalon Standstill", level = 25, questID = 1, isComplete = false, obj = {} },
}""")
lua.execute("ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone'); SELECTED = 99")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
check("share button in Current Zone", lua.eval(SB + ".shown") and lua.eval(SB + ".text") == "Share all quests")
check("share disabled when solo", lua.eval(SB + ".disabled") is True)
lua.execute("QuestSidebar.ShareZone()")
check("solo: asks to join a party", "Join a party" in last_print() and pushes() == [])
lua.execute("GROUP = true"); ev("GROUP_ROSTER_UPDATE"); lua.execute("run_timers()")
check("share enabled in a group", lua.eval(SB + ".disabled") is False)
lua.execute(SB + ".scripts.OnClick(" + SB + ")")
check("first quest shared at once", pushes() == [2])
check("button says sharing", lua.eval(SB + ".text") == "Sharing..." and lua.eval(SB + ".disabled") is True)
lua.execute(SB + ".scripts.OnClick(" + SB + ")")
check("no double share", pushes() == [2])
lua.execute("run_timers()")
check("second quest after a gap", pushes() == [2, 3])
lua.execute("run_timers()")
check("done: summary", "Shared 2 quests from The Barrens" in last_print())
check("done: selection restored", lua.eval("SELECTED") == 99)
check("done: button back", lua.eval(SB + ".text") == "Share all quests" and lua.eval(SB + ".disabled") is False)
check("only this zone's quests", 1 not in pushes() and 4 not in pushes())

lua.execute("PUSHES = {}; SlashCmdList.QUESTSIDEBAR('share')")
ev("CHAT_MSG_SYSTEM", "Thrall is busy.")
lua.execute("run_timers(); run_timers(); run_timers()")
check("busy: quest retried later", pushes() == [2, 3, 2])
check("busy: still counted once", "Shared 2 quests" in last_print())

lua.execute("PUSHES = {}; PUSHABLE[3] = false; QuestSidebar.ShareZone()")
check("unshareable quest skipped", "1 can't be shared" in last_print())
lua.execute("run_timers(); run_timers()")
check("only shareable pushed", pushes() == [2] and "Shared 1 quest from" in last_print())
lua.execute("PUSHABLE[3] = nil")

lua.execute("PUSHES = {}; QuestSidebar.ShareZone(); GROUP = false; run_timers()")
check("leaving the group stops sharing", pushes() == [2] and "no longer in a group" in last_print())
lua.execute("run_timers(); QuestSidebar.UI.SelectTab('all')")
check("no share button in All", not lua.eval(SB + ".shown"))

# ---- 1.5.0: party markers ------------------------------------------------------------
def reset_log():
    lua.execute("""LOG = {
  { title = "The Barrens", isHeader = true },
  { title = "Raptor Thieves", level = 15, questID = 3, isComplete = false, obj = { { text = "Raptor Head: 3/12", finished = false } } },
  { title = "Plainstrider Menace", level = 12, questID = 2, isComplete = true, obj = {} },
  { title = "Kolkar Leaders", level = 11, questID = 5, isComplete = false, obj = {} },
  { title = "Ashenvale", isHeader = true },
  { title = "Stonetalon Standstill", level = 25, questID = 1, isComplete = false, obj = { { text = "0/12 Befouled Water Elemental slain", finished = false } } },
}""")
reset_log()
lua.execute("PUSHES = {}; GROUP = true; PARTY = { { name = 'Brother', quests = { [3] = true } }, { name = 'Cousin', quests = { [3] = true, [2] = true } } }")
lua.execute("ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone')"); ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
check("party marker: everyone has it", row("Raptor Thieves").tag.text.endswith("2/2|r"))
check("party marker: some have it", "1/2" in row("Plainstrider").tag.text)
check("party marker: nobody", "0/2" in row("Kolkar").tag.text)
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Plainstrider') then r = q end end; r.scripts.OnEnter(r)")
po = lua.eval("QuestSidebar.PartyOn({ questID = 2, index = 3 })")
check("PartyOn names", list(po.have.values()) == ["Cousin"] and list(po.missing.values()) == ["Brother"])

# ---- ready to turn in first -----------------------------------------------------------
check("ready-to-turn-in quests on top", qtitles()[0].find("Plainstrider") >= 0)
check("ready highlight", row("Plainstrider").ready.shown and not row("Raptor").ready.shown)

# ---- share all skips quests the whole party has --------------------------------------------
lua.execute("QuestSidebar.ShareZone()")
check("share skips what everyone has", "1 the whole party already has" in last_print())
lua.execute("run_timers(); run_timers(); run_timers()")
check("only missing quests pushed", sorted(pushes()) == [2, 5])

# ---- right-click menu -------------------------------------------------------------------------
lua.execute("PUSHES = {}; local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.scripts.OnClick(r, 'RightButton')")
items = [ (i.text, i.enabled) for i in lua.eval("MENU.items").values() ]
check("menu title", lua.eval("MENU.title") == "Kolkar Leaders")
check("menu items", [t for t, _ in items][:4] == ["Track", "Share with party", "Link in chat", "Show in quest log"] and "Abandon" in items[4][0])
check("right-click no longer just tracks", lua.eval("WATCHED[5]") is None)
lua.execute("MENU.items[1].func()"); lua.execute("run_timers()")
check("menu: track", lua.eval("WATCHED[5]") is True)
lua.execute("MENU.items[2].func()"); lua.execute("run_timers()")
check("menu: share one quest", pushes() == [5] and "Shared Kolkar Leaders with your party" in last_print())
lua.execute("MENU.items[5].func()")
check("abandon asks first", lua.eval("POPUP.which") == "QUESTSIDEBAR_ABANDON" and lua.eval("POPUP.text") == "Kolkar Leaders" and lua.eval("#ABANDONED") == 0)
lua.execute("StaticPopupDialogs.QUESTSIDEBAR_ABANDON.OnAccept(POPUP, POPUP.data)")
check("abandon after yes", list(lua.eval("ABANDONED").values()) == [5])
lua.execute("GROUP = false; PARTY = {}; QuestSidebar.Refresh()")
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.scripts.OnClick(r, 'RightButton')")
check("menu: share greyed out when solo", lua.eval("MENU.items[2].enabled") is False and "not in a party" in lua.eval("MENU.items[2].text"))
check("no party markers when solo", row("Kolkar").tag.text == "")

# ---- auto-share (off by default) --------------------------------------------------------------
check("auto-share off by default", lua.eval("QuestSidebarDB.settings.autoShare") is False)
lua.execute("PUSHES = {}; GROUP = true; PARTY = { { name = 'Brother', quests = {} } }")
ev("QUEST_ACCEPTED", 5); lua.execute("run_timers(); run_timers(); run_timers()")
check("off: nothing shared on accept", pushes() == [])
lua.execute("QuestSidebar.UI.ToggleSettings()")
names = [i.label.text for i in lua.eval("QuestSidebarSettings.items").values() if i.label]
check("auto-share in settings", "Auto-share new quests with party" in names and "Hide grey (low level) quests" in names)
lua.execute("local c = QuestSidebarSettings.items[8]; c:SetChecked(true); c.scripts.OnClick(c)")
check("settings toggle turns auto-share on", lua.eval("QuestSidebarDB.settings.autoShare") is True)
ev("QUEST_ACCEPTED", 5); lua.execute("run_timers(); run_timers(); run_timers()")
check("on: new quest shared", pushes() == [5])
lua.execute("PUSHES = {}; PARTY[1].quests[5] = true")
ev("QUEST_ACCEPTED", 5); lua.execute("run_timers(); run_timers(); run_timers()")
check("on: not sent back if the party has it", pushes() == [])
lua.execute("PUSHES = {}; PARTY[1].quests[5] = nil")
ev("QUEST_ACCEPTED", 0, 5); lua.execute("run_timers(); run_timers(); run_timers()")
check("on: classic (index, questID) args", pushes() == [5])
lua.execute("PUSHES = {}; GROUP = false")
ev("QUEST_ACCEPTED", 5); lua.execute("run_timers(); run_timers()")
check("on but solo: nothing", pushes() == [])
lua.execute("SlashCmdList.QUESTSIDEBAR('autoshare')")
check("/qsb autoshare toggles", lua.eval("QuestSidebarDB.settings.autoShare") is False)

# ---- hide grey quests ---------------------------------------------------------------------------
lua.execute("MYLEVEL = 20; QuestSidebar.Refresh()")
check("grey shown by default", has("Kolkar"))
lua.execute("local c = QuestSidebarSettings.items[9]; c:SetChecked(true); c.scripts.OnClick(c)")
check("grey hidden (lvl 11 at 20)", not has("Kolkar") and has("Raptor"))
check("grey but complete still shown", has("Plainstrider"))
check("says how many hidden", "1 grey quest hidden" in lua.eval("QuestSidebar.UI.Empty().text"))
lua.execute("SlashCmdList.QUESTSIDEBAR('grey')")
check("/qsb grey shows them again", has("Kolkar"))

# ---- search on All -----------------------------------------------------------------------------
lua.execute("QuestSidebar.UI.SelectTab('all')")
check("search box on All", lua.eval("QuestSidebarSearch.shown"))
lua.execute("QuestSidebarSearch:SetText('RAPTOR'); QuestSidebarSearch.scripts.OnTextChanged(QuestSidebarSearch); run_timers()")
check("search by title", qtitles() == [t for t in qtitles() if "Raptor" in t] and has("Raptor"))
lua.execute("QuestSidebarSearch:SetText('elemental'); QuestSidebarSearch.scripts.OnTextChanged(QuestSidebarSearch); run_timers()")
check("search by objective (zone opens)", has("Stonetalon") and hdrs() == ["Ashenvale"])
lua.execute("QuestSidebarSearch:SetText('barrens'); QuestSidebarSearch.scripts.OnTextChanged(QuestSidebarSearch); run_timers()")
check("search by zone shows the zone", hdrs() == ["The Barrens"] and has("Raptor") and has("Kolkar"))
lua.execute("QuestSidebarSearch:SetText('zzz'); QuestSidebarSearch.scripts.OnTextChanged(QuestSidebarSearch); run_timers()")
check("no matches message", "No quests match" in lua.eval("QuestSidebar.UI.Empty().text") and lua.eval("QuestSidebar.UI.Empty().shown"))
lua.execute("QuestSidebarSearch:SetText(''); QuestSidebarSearch.scripts.OnTextChanged(QuestSidebarSearch); run_timers()")
check("clear search: all zones back", "Ashenvale" in hdrs() and "The Barrens" in hdrs())
lua.execute("QuestSidebar.UI.SelectTab('zone')")
check("no search box on Current Zone", not lua.eval("QuestSidebarSearch.shown"))

# ---- quest log full warning ---------------------------------------------------------------------
lua.execute("QuestSidebar.Refresh()")
check("normal count grey", lua.eval("QuestSidebar.UI.logFull") is False)
lua.execute("C_QuestLog.GetMaxNumQuestsCanAccept = function() return 4 end; QuestSidebar.Refresh()")
check("log full flagged", lua.eval("QuestSidebar.UI.logFull") is True)
lua.execute("C_QuestLog.GetMaxNumQuestsCanAccept = nil; QuestSidebar.Refresh()")

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
