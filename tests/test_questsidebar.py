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
function Widget:SetAttribute(k, v) self.attrs = self.attrs or {}; self.attrs[k] = v end
function Widget:GetAttribute(k) return self.attrs and self.attrs[k] end
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
    -- like the real modern client: no isComplete here, ask IsComplete/IsFailed
    return { title = e.title, level = e.level, isHeader = e.isHeader, isCollapsed = e.isCollapsed, questID = e.questID or 0 } end,
  IsComplete = function(id) for _, e in ipairs(LOG) do if e.questID == id then return e.isComplete == true end end return false end,
  IsFailed = function(id) for _, e in ipairs(LOG) do if e.questID == id then return e.isComplete == -1 end end return false end,
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
NOW = 0
function GetTime() return NOW end
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
def link(): return lua.eval("QuestSidebar.UI.readyLink")
check("its quests", has("Raptor Thieves") and not has("Stonetalon"))
check("finished quest not in Current Zone", not has("Plainstrider"))
check("ready line points at Turn in", link().shown and "1 ready to turn in" in link().text.text and "open Turn in" in link().text.text)
r = row("Raptor Thieves")
check("level + title", "[15] Raptor Thieves" in r.title.text)
check("objective with dash", r.objectives.text == "- Raptor Head: 3/12")
check("quest details shown", r.details.text == DETAILS3 if (DETAILS3 := "Bring 12 Raptor Heads to Regthar Deathgate.") else False)
check("selection restored after reading details", lua.eval("SELECTED") == 99)
check("tracked checkbox", r.track.checked is True)
check("in-progress icon", r.icon.texture.endswith("IncompleteQuestIcon"))
lua.execute("local l = QuestSidebar.UI.readyLink; l.scripts.OnClick(l)")
check("ready line opens the Turn in tab", lua.eval("QuestSidebar.UI.tab") == "turnin" and has("Plainstrider") and not has("Raptor"))
p = row("Plainstrider")
check("tracked checkbox (turn in)", p.track.checked is False)
check("complete: ready to turn in", "Ready to turn in" in p.objectives.text and "Beak" not in p.objectives.text)
check("complete icon", p.icon.texture.endswith("ActiveQuestIcon"))
lua.execute("QuestSidebar.UI.SelectTab('zone')")

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
check("party marker: nobody", "0/2" in row("Kolkar").tag.text)
lua.execute("QuestSidebar.UI.SelectTab('all')")
check("party marker: some have it", "1/2" in row("Plainstrider").tag.text)
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Plainstrider') then r = q end end; r.scripts.OnEnter(r)")
po = lua.eval("QuestSidebar.PartyOn({ questID = 2, index = 3 })")
check("PartyOn names", list(po.have.values()) == ["Cousin"] and list(po.missing.values()) == ["Brother"])

# ---- ready to turn in first -----------------------------------------------------------
check("ready highlight", row("Plainstrider").ready.shown and not row("Raptor").ready.shown)
lua.execute("QuestSidebar.UI.SelectTab('zone')")
check("finished quests left out of Current Zone", not has("Plainstrider") and has("Raptor"))

# ---- share all skips quests the whole party has --------------------------------------------
lua.execute("QuestSidebar.ShareZone()")
check("share skips what everyone has", "1 the whole party already has" in last_print())
lua.execute("run_timers(); run_timers(); run_timers()")
check("only missing quests pushed", sorted(pushes()) == [2, 5])

# ---- right-click menu -------------------------------------------------------------------------
lua.execute("PUSHES = {}; local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.scripts.OnClick(r, 'RightButton')")
items = [ (i.text, i.enabled) for i in lua.eval("MENU.items").values() ]
check("menu title", lua.eval("MENU.title") == "Kolkar Leaders")
check("menu items", [t for t, _ in items][1:5] == ["Track", "Share with party", "Link in chat", "Show in quest log"] and "Abandon" in items[5][0])
check("right-click no longer just tracks", lua.eval("WATCHED[5]") is None)
lua.execute("MENU.items[2].func()"); lua.execute("run_timers()")
check("menu: track", lua.eval("WATCHED[5]") is True)
lua.execute("MENU.items[3].func()"); lua.execute("run_timers()")
check("menu: share one quest", pushes() == [5] and "Shared Kolkar Leaders with your party" in last_print())
lua.execute("MENU.items[6].func()")
check("abandon asks first", lua.eval("POPUP.which") == "QUESTSIDEBAR_ABANDON" and lua.eval("POPUP.text") == "Kolkar Leaders" and lua.eval("#ABANDONED") == 0)
lua.execute("StaticPopupDialogs.QUESTSIDEBAR_ABANDON.OnAccept(POPUP, POPUP.data)")
check("abandon after yes", list(lua.eval("ABANDONED").values()) == [5])
lua.execute("GROUP = false; PARTY = {}; QuestSidebar.Refresh()")
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.scripts.OnClick(r, 'RightButton')")
check("menu: share greyed out when solo", lua.eval("MENU.items[3].enabled") is False and "not in a party" in lua.eval("MENU.items[3].text"))
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
check("finished quest still counted on the ready line", link().shown and "ready to turn in" in link().text.text)
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

# ---- 1.6.0: finished quests stand out in Current Zone --------------------------------------
reset_log()
lua.execute("""TURNIN = { [2] = "Return to Regthar Deathgate at the Center Plains." }
function GetQuestLogCompletionText() return TURNIN[SELECTED] or "" end
GROUP = false; PARTY = {}; SELECTED = 99; ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
def sections(): return [l.text.text for l in lua.eval("QuestSidebar.UI.Sections()").values() if l.shown]
check("no ready section in Current Zone now", sections() == [] and not has("Plainstrider"))
check("ready line instead", link().shown and "1 ready to turn in" in link().text.text)
check("in-progress quests listed", has("Raptor") and has("Kolkar"))
check("no gold edge on unfinished", not row("Raptor").readyEdge.shown)
check("in-progress quests keep their summary", row("Raptor").details.text == "Bring 12 Raptor Heads to Regthar Deathgate.")
lua.execute("QuestSidebar.UI.SelectTab('turnin')")
p = row("Plainstrider")
check("gold edge in Turn in", p.readyEdge.shown)
check("tick on ready line", "ReadyCheck-Ready" in p.objectives.text and "Ready to turn in" in p.objectives.text)
check("turn-in NPC shown", p.details.text == "Return to Regthar Deathgate at the Center Plains.")
check("selection restored after turn-in read", lua.eval("SELECTED") == 99)

lua.execute("QuestSidebar.UI.SelectTab('all')")
check("header done count green (All)", "|cff40c040" in header("The Barrens").count.text)
check("no sections in All", sections() == [])
check("All: lighter wash, no edge", row("Plainstrider").ready.shown and not row("Plainstrider").readyEdge.shown)

lua.execute("""for _, e in ipairs(LOG) do if e.questID == 2 then e.isComplete = false end end
QuestSidebar.UI.SelectTab('zone')""")
check("no sections when nothing is finished", sections() == [])
check("no ready line when nothing is finished", not link().shown and has("Plainstrider"))

lua.execute("TURNIN = {}; for _, e in ipairs(LOG) do if e.questID == 5 then e.isComplete = true end end; QuestSidebar.UI.SelectTab('turnin')")
check("no turn-in text: falls back to summary", row("Kolkar").details.text in ("", None) or row("Kolkar").details.shown is False)

# ---- 1.7.0: fastest route ------------------------------------------------------------------
reset_log()
lua.execute("""SUPER = nil; ROUTES = 0; CTRL = false
function IsControlKeyDown() return CTRL end
C_SuperTrack = { SetSuperTrackedQuestID = function(id) SUPER = id end }
WATCHED = {}
ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")

# without Shortest Path Forever: the game's quest arrow
check("no router detected", lua.eval("QuestSidebar.HasRouter()") is False)
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Raptor') then r = q end end; r.route.scripts.OnClick(r.route)")
check("fallback: super-tracks the quest", lua.eval("SUPER") == 3 and lua.eval("WATCHED[3]") is True)
check("fallback: says to install SPF", "Shortest Path Forever" in last_print())
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.scripts.OnClick(r, 'RightButton')")
check("menu: arrow item first without SPF", "quest arrow" in lua.eval("MENU.items[1].text"))

# with Shortest Path Forever
lua.execute("""ShortestPathForeverTravelToTrackedQuestButton = CreateFrame('Button')
ShortestPathForeverTravelToTrackedQuestButton.Click = function(self, b) ROUTES = ROUTES + 1; ROUTED = SUPER end""")
check("router detected", lua.eval("QuestSidebar.HasRouter()") is True)
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.scripts.OnClick(r, 'RightButton')")
check("menu: fastest route first", "Fastest route there" in lua.eval("MENU.items[1].text"))
lua.execute("MENU.items[1].func()")
check("route: SPF journey to that quest", lua.eval("ROUTES") == 1 and lua.eval("ROUTED") == 5)
lua.execute("QuestSidebar.UI.SelectTab('all'); CTRL = true; local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Plainstrider') then r = q end end; r.scripts.OnClick(r, 'LeftButton'); CTRL = false; QuestSidebar.UI.SelectTab('zone')")
check("ctrl-click routes", lua.eval("ROUTES") == 2 and lua.eval("ROUTED") == 2)
lua.execute("WATCHED = { [3] = true }; QuestSidebar.Refresh(); SlashCmdList.QUESTSIDEBAR('route')")
check("/qsb route picks the tracked quest", lua.eval("ROUTES") == 3 and lua.eval("ROUTED") == 3)
lua.execute("COMBAT = true; QuestSidebar.RouteTo({ questID = 1, title = 'x' }); COMBAT = false")
check("no routing in combat", lua.eval("ROUTES") == 3 and "combat" in last_print())

# ---- 1.8.0: Turn in tab -------------------------------------------------------------------------
reset_log()
lua.execute("""for _, e in ipairs(LOG) do if e.questID == 1 then e.isComplete = true end end
TURNIN = { [2] = "Return to Regthar Deathgate at the Center Plains." }
ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
check("tab shows ready count", "2" in lua.eval("QuestSidebar.UI.tabTurnIn.text") and "Turn in" in lua.eval("QuestSidebar.UI.tabTurnIn.text"))
lua.execute("QuestSidebar.UI.tabTurnIn.scripts.OnClick(QuestSidebar.UI.tabTurnIn)")
check("Turn in tab selected", lua.eval("QuestSidebar.UI.tab") == "turnin" and lua.eval("QuestSidebar.UI.tabTurnIn.disabled") is True)
check("only finished quests", sorted(qtitles()) == sorted([t for t in qtitles() if "Plainstrider" in t or "Stonetalon" in t]) and len(qtitles()) == 2)
check("every zone, current zone first", hdrs() == ["The Barrens", "Ashenvale"])
check("current zone gold in Turn in", "|cffffd100The Barrens" in header("The Barrens").text.text)
check("turn-in NPC shown", row("Plainstrider").details.text.startswith("Return to Regthar"))
check("gold edge on rows", row("Stonetalon").readyEdge.shown)
check("no share/search here", not lua.eval("QuestSidebar.UI.shareBtn.shown") and not lua.eval("QuestSidebarSearch.shown"))
lua.execute("ZONE = 'Ashenvale'"); ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
check("follows you: Ashenvale first now", hdrs() == ["Ashenvale", "The Barrens"])
lua.execute("for _, e in ipairs(LOG) do e.isComplete = false end; QuestSidebar.Refresh()")
check("nothing to turn in", qtitles() == [] and "Nothing to turn in" in lua.eval("QuestSidebar.UI.Empty().text"))
check("tab count clears", lua.eval("QuestSidebar.UI.tabTurnIn.text") == "Turn in")
lua.execute("QuestSidebar.UI.SelectTab('all')")
check("All re-enables Turn in tab", lua.eval("QuestSidebar.UI.tabTurnIn.disabled") is False)
lua.execute("SlashCmdList.QUESTSIDEBAR('turnin')")
check("/qsb turnin", lua.eval("QuestSidebar.UI.tab") == "turnin")
lua.execute("SlashCmdList.QUESTSIDEBAR('min')")
check("minimize hides the new tab", lua.eval("QuestSidebar.UI.tabTurnIn.shown") is False)
lua.execute("SlashCmdList.QUESTSIDEBAR('min')")
check("restore shows it", lua.eval("QuestSidebar.UI.tabTurnIn.shown") is True)

# ---- 1.8.1: route button toggles; finished quests read from IsComplete --------------------------------
check("finished state comes from C_QuestLog.IsComplete", lua.eval("C_QuestLog.GetInfo(2).isComplete") is None)
reset_log()
lua.execute("QuestSidebar.StopRoute(true)")  # an earlier test left a route running
lua.execute("""SUPER = nil; ROUTES = 0; CLEARS = 0; WATCHED = {}
ShortestPathForeverClearJourneyButton = CreateFrame('Button')
ShortestPathForeverClearJourneyButton.Click = function() CLEARS = CLEARS + 1 end
C_SuperTrack.GetSuperTrackedQuestID = function() return SUPER or 0 end
SPF_ACTIVE = true
ShortestPathForever = { API = { Active = function() return SPF_ACTIVE end } }
ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('turnin')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
check("Turn in tab lists the finished quest", qtitles() and "Plainstrider" in qtitles()[0])

lua.execute("QuestSidebar.UI.SelectTab('zone'); run_timers()")
def raptor_route(): lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Raptor') then r = q end end; r.route.scripts.OnClick(r.route)"); lua.execute("run_timers()")
raptor_route()
check("first click routes", lua.eval("ROUTES") == 1 and lua.eval("SUPER") == 3 and lua.eval("WATCHED[3]") is True)
check("route button glows", row("Raptor").route.on.shown and not row("Kolkar").route.on.shown)
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Raptor') then r = q end end; r.scripts.OnClick(r, 'RightButton')")
check("menu offers stop", "Stop the route" in lua.eval("MENU.items[1].text"))
raptor_route()
check("second click stops", lua.eval("ROUTES") == 1 and lua.eval("CLEARS") == 1 and "Stopped the route" in last_print())
check("stop clears the arrow", lua.eval("SUPER") == 0)
check("stop untracks what routing tracked", lua.eval("WATCHED[3]") is None)
check("glow off", not row("Raptor").route.on.shown)

lua.execute("WATCHED = { [3] = true }; QuestSidebar.Refresh()")
raptor_route(); raptor_route()
check("already-tracked quest stays tracked after stop", lua.eval("WATCHED[3]") is True)

raptor_route()
lua.execute("SPF_ACTIVE = false; QuestSidebar.Refresh()")
check("journey ended by itself: glow off", not row("Raptor").route.on.shown)
n = lua.eval("ROUTES")
raptor_route()
check("then a click routes again", lua.eval("ROUTES") == n + 1)
lua.execute("SPF_ACTIVE = true")
n = lua.eval("ROUTES")
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.route.scripts.OnClick(r.route); run_timers()")
check("routing another quest switches", lua.eval("ROUTES") == n + 1 and lua.eval("SUPER") == 5 and row("Kolkar").route.on.shown and not row("Raptor").route.on.shown)

# ---- 1.8.2: X closes settings ----
lua.execute("QuestSidebarSettings:Hide(); QuestSidebar.UI.ToggleSettings()")
check("settings open", lua.eval("QuestSidebarSettings:IsShown()"))
lua.execute("QuestSidebarSettings.close.scripts.OnClick(QuestSidebarSettings.close)")
check("X closes settings", not lua.eval("QuestSidebarSettings:IsShown()"))
lua.execute("QuestSidebar.UI.cog.scripts.OnClick(QuestSidebar.UI.cog)")
check("cog still opens it after", lua.eval("QuestSidebarSettings:IsShown()"))

# ---- 1.9.0: XP on turn-ins ---------------------------------------------------------------------------
reset_log()
lua.execute("""for _, e in ipairs(LOG) do if e.questID == 1 then e.isComplete = true end end
XP = { [2] = 1250, [1] = 3400, [3] = 900 }
XPCALLS = 0
function GetQuestLogRewardXP(id) XPCALLS = XPCALLS + 1; return XP[id] or 0 end
function UnitXPMax() return 18500 end
function GetMaxPlayerLevel() return 60 end
function BreakUpLargeNumbers(n) local s = tostring(n); return (s:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", "")) end
NOW = NOW + 60; MYLEVEL = 20; ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
check("no XP shown on unfinished quests", "XP" not in row("Raptor").objectives.text)
check("ready line shows the total XP", "2 ready to turn in" in link().text.text and "4,650 XP" in link().text.text)
lua.execute("QuestSidebar.UI.SelectTab('all')")
check("XP on the ready line", "+1,250 XP" in row("Plainstrider").objectives.text)
lua.execute("QuestSidebar.UI.SelectTab('zone')")

calls = lua.eval("XPCALLS")
lua.execute("QuestSidebar.Refresh(); QuestSidebar.Refresh()")
check("XP is cached", lua.eval("XPCALLS") == calls)

lua.execute("QuestSidebar.UI.SelectTab('turnin')")
sec = sections()
check("Turn in tab total", sec and "Total 4,650 XP" in sec[0])
check("share of a level", "25% of a level" in sec[0])
check("each turn-in has its XP", "+3,400 XP" in row("Stonetalon").objectives.text)

lua.execute("XP[2] = 1500; MYLEVEL = 21"); ev("PLAYER_LEVEL_UP", 21); lua.execute("run_timers()")
check("level up refreshes XP", "+1,500 XP" in row("Plainstrider").objectives.text)

lua.execute("MYLEVEL = 60; QuestSidebar.Refresh()")
check("max level: no XP", "XP" not in row("Plainstrider").objectives.text and not any("Total" in t for t in sections()))
lua.execute("MYLEVEL = 20; XP = {}; QuestSidebar.Refresh()")
check("no XP reward: nothing shown", "XP" not in row("Plainstrider").objectives.text)
lua.execute("MYLEVEL = 22; QuestSidebar.Refresh()")
check("reward not loaded yet: nothing shown", "XP" not in row("Plainstrider").objectives.text)
lua.execute("XP = { [2] = 1700 }; NOW = NOW + 2; QuestSidebar.Refresh()")
check("not asked again straight away", "XP" not in row("Plainstrider").objectives.text)
lua.execute("NOW = NOW + 11; QuestSidebar.Refresh()")
check("asked again after 10s and shown", "+1,700 XP" in row("Plainstrider").objectives.text)
lua.execute("GetQuestLogRewardXP = nil; QuestSidebar.Refresh()")
check("client without the call: fine", "Ready to turn in" in row("Plainstrider").objectives.text)

lua.execute("""for _, e in ipairs(LOG) do if e.questID and not e.isHeader then e.isComplete = true end end
ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone')""")
check("all done here: says so", "Nothing left to do in The Barrens" in lua.eval("QuestSidebar.UI.Empty().text") and qtitles() == [])
check("all done here: ready line still there", link().shown)
lua.execute("for _, e in ipairs(LOG) do e.isComplete = false end; QuestSidebar.Refresh()")

# ---- 1.10.0: Turn in tab by hand-in place + chain route ------------------------------------------------
reset_log()
lua.execute("""
for _, e in ipairs(LOG) do if e.questID == 1 or e.questID == 5 then e.isComplete = true end end
TURNIN = {}
-- Questie's database: who finishes each quest, and where they stand
local QUESTS = { [2] = { { 100 } }, [1] = { { 101 } }, [5] = { { 102 } } }
local NPCS = {
  [100] = { name = "Thrall", zoneID = 1637, spawns = { [1637] = { { 31, 37 } } } },
  [101] = { name = "Kildrath", zoneID = 1637, spawns = { [1637] = { { 60, 50 } } } },
  [102] = { name = "Regthar Deathgate", zoneID = 17, spawns = { [17] = { { 45, 58 } } } },
}
LibQuestieDB = {
  Quest = { Get = function(id, key) local q = QUESTS[id]; if key == "finishedBy" then return q end end },
  Npc = { Get = function(id, key) local n = NPCS[id]; return n and n[key] end },
}
local ZONES = { [1637] = 1454, [17] = 1413 }
QuestieLoader = { ImportModule = function(self, name)
  if name == "ZoneDB" then return { GetUiMapIdByAreaId = function(_, a) return ZONES[a] end } end end }
local NAMES = { [1454] = "Orgrimmar", [1413] = "The Barrens" }
function CreateVector2D(x, y) return { x = x, y = y, GetXY = function(v) return v.x, v.y end } end
C_Map = {
  GetMapInfo = function(m) return NAMES[m] and { name = NAMES[m] } end,
  GetWorldPosFromMapPos = function(m, v) return 1, CreateVector2D(m * 1000 + v.x * 100, v.y * 100) end,
  GetBestMapForUnit = function() return PLAYER_MAP end,
  GetPlayerMapPosition = function() return CreateVector2D(PLAYER_X, PLAYER_Y) end,
}
PLAYER_MAP, PLAYER_X, PLAYER_Y = 1454, 0.58, 0.50   -- standing next to Kildrath in Orgrimmar
NAV = nil; CANCELS = 0
ShortestPathForever = { API = {
  Active = function() return NAV ~= nil end,
  NavigateRoute = function(owner, stops) NAV = { owner = owner, stops = stops }; return true end,
  Cancel = function(owner) CANCELS = CANCELS + 1; NAV = nil; return true end,
} }
NOW = NOW + 60; ZONE = 'Orgrimmar'; QuestSidebar.UI.SelectTab('turnin')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")

check("grouped by hand-in place", hdrs() == ["Orgrimmar", "The Barrens"])
check("quests from other zones hand in at Orgrimmar", [t for t in qtitles()][:2] == [t for t in qtitles() if "Stonetalon" in t or "Plainstrider" in t])
check("nearest first inside a place", "Stonetalon" in qtitles()[0] and "Plainstrider" in qtitles()[1])
check("hand-in NPC named", row("Stonetalon").details.text == "Hand in to Kildrath in Orgrimmar.")
check("game's own turn-in text wins over the NPC name", row("Plainstrider").details.text.startswith("Return to Regthar"))
check("place headers have a route-all button", header("Orgrimmar").chain.shown and header("The Barrens").chain.shown)
check("plain count on place headers", header("Orgrimmar").count.text == "2")

# start the chain at Orgrimmar
lua.execute("local h; for _, x in ipairs(QuestSidebar.UI.Headers()) do if x.shown and x.zone == 'Orgrimmar' then h = x end end; h.chain.scripts.OnClick(h.chain); run_timers()")
stops = list(lua.eval("NAV.stops").values())
check("one journey with a stop per hand-in", lua.eval("NAV.owner") == "QuestSidebar" and len(stops) == 2)
check("nearest stop first", stops[0].questID == 1 and stops[1].questID == 2)
check("stops name the NPC", stops[0].title.startswith("Kildrath:") and stops[1].title.startswith("Thrall:"))
check("stops wait for the hand-in", stops[0].hold is True)
check("stop coordinates from Questie", abs(stops[1].x - 0.31) < 1e-9 and stops[1].map == 1454)
check("only that place's quests", all(s.questID != 5 for s in stops))
check("header glows while routing", header("Orgrimmar").chain.on.shown and not header("The Barrens").chain.on.shown)
check("chat says the order", "nearest first: Stonetalon Standstill, Plainstrider Menace" in last_print())

# hand in the first: re-planned from here with what's left
lua.execute("for i, e in ipairs(LOG) do if e.questID == 1 then table.remove(LOG, i) break end end; PLAYER_X, PLAYER_Y = 0.6, 0.5")
ev("QUEST_TURNED_IN", 1); lua.execute("run_timers(); run_timers()")
stops = list(lua.eval("NAV.stops").values())
check("after a hand-in: the rest re-planned", len(stops) == 1 and stops[0].questID == 2)
lua.execute("for i, e in ipairs(LOG) do if e.questID == 2 then table.remove(LOG, i) break end end")
ev("QUEST_TURNED_IN", 2); lua.execute("run_timers(); run_timers()")
check("all done: finished message", "All handed in at Orgrimmar" in last_print() and lua.eval("QuestSidebar.ChainZone()") is None)
check("journey cancelled at the end", lua.eval("NAV") is None)

# toggle: start then stop
reset_log()
lua.execute("for _, e in ipairs(LOG) do if e.questID == 1 or e.questID == 5 then e.isComplete = true end end; QuestSidebar.Refresh()")
lua.execute("local h; for _, x in ipairs(QuestSidebar.UI.Headers()) do if x.shown and x.zone == 'Orgrimmar' then h = x end end; h.chain.scripts.OnClick(h.chain); run_timers()")
c = lua.eval("CANCELS")
lua.execute("local h; for _, x in ipairs(QuestSidebar.UI.Headers()) do if x.shown and x.zone == 'Orgrimmar' then h = x end end; h.chain.scripts.OnClick(h.chain); run_timers()")
check("second click stops the chain", lua.eval("QuestSidebar.ChainZone()") is None and lua.eval("CANCELS") == c + 1 and "Stopped the turn-in route" in last_print())

# a single quest route replaces a chain
lua.execute("local h; for _, x in ipairs(QuestSidebar.UI.Headers()) do if x.shown and x.zone == 'Orgrimmar' then h = x end end; h.chain.scripts.OnClick(h.chain); run_timers()")
lua.execute("local r; for _, q in ipairs(QuestSidebar.UI.Quests()) do if q.shown and q.title.text:find('Kolkar') then r = q end end; r.route.scripts.OnClick(r.route); run_timers()")
check("single route replaces the chain", lua.eval("QuestSidebar.ChainZone()") is None)
lua.execute("QuestSidebar.StopRoute(true)")

# without Shortest Path: the arrow steps through them
lua.execute("ShortestPathForever = nil; ShortestPathForeverTravelToTrackedQuestButton = nil; SUPER = nil")
lua.execute("local h; for _, x in ipairs(QuestSidebar.UI.Headers()) do if x.shown and x.zone == 'Orgrimmar' then h = x end end; h.chain.scripts.OnClick(h.chain); run_timers()")
check("no SPF: arrow on the nearest", lua.eval("SUPER") == 1)
lua.execute("for i, e in ipairs(LOG) do if e.questID == 1 then table.remove(LOG, i) break end end")
ev("QUEST_TURNED_IN", 1); lua.execute("run_timers(); run_timers()")
check("no SPF: arrow moves to the next", lua.eval("SUPER") == 2)
lua.execute("QuestSidebar.StopChain(true)")

# without Questie: grouped by the quest's own zone, as before
lua.execute("LibQuestieDB = nil; QuestieLoader = nil")
check("place lookup is cached", lua.eval("QuestSidebar.TurnInPlace({ questID = 5 }).zone") == "The Barrens")

# ---- 1.11.0: Earthen Echo hands in at Mulgore, not the objective's map ----------------------------------
lua.execute("""
LOG = {
  { title = "Wetlands", isHeader = true },
  { title = "Earthen Echo", level = 31, questID = 98823, isComplete = true, obj = {} },
}
-- real QuestieDB rows for this quest (decoded from QuestieDB_Forever.toc)
LibQuestieDB = {
  Quest = { Get = function(id, key) if id == 98823 and key == "finishedBy" then return { { 259118 } } end end },
  Npc = { Get = function(id, key)
    local n = { name = "Muln Earthfury", zoneID = 215, spawns = { [215] = { { 33.42, 22.59 } } } }
    if id == 259118 then return n[key] end end },
  Support = { Get = function(m) if m == "ZoneDB" then return { private = {
    areaIdToUiMapId = "return { [215] = 1412, [17732] = 1437, [17223] = 1412 }",
    areaIdToUiMapIdOverride = "return { [0] = 0 }" } } end end },
}
-- Questie has loaded but its ZoneDB hasn't started up yet
QuestieLoader = { ImportModule = function(self, name) return { GetUiMapIdByAreaId = function() return nil end } end }
C_Map.GetMapInfo = function(m) return ({ [1412] = { name = "Mulgore" }, [1437] = { name = "Wetlands" }, [99001] = { name = "Excavation Site: Wetlands" } })[m] end
-- the game's quest map points at the objective
function GetQuestUiMapID() return 99001 end
C_QuestLog.GetQuestsOnMap = function() return {} end
NOW = NOW + 60; ZONE = 'Thunder Bluff'; QuestSidebar.UI.SelectTab('turnin')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
check("Earthen Echo under Mulgore", hdrs() == ["Mulgore"])
check("names Muln Earthfury", row("Earthen Echo").details.text == "Hand in to Muln Earthfury in Mulgore.")
check("not the objective's map", "Excavation" not in " ".join(hdrs()))

# ---- 1.11.0: quest item buttons ------------------------------------------------------------------------
reset_log()
lua.execute("""
SPECIAL = { [3] = { "|cffffffff|Hitem:5056:0|h[Raptor Lure]|h|r", "Interface\\\\Icons\\\\INV_Misc_Bone_01", 3, false } }
function GetQuestLogSpecialItemInfo(index)
  local e = C_QuestLog.GetInfo(index); local s = e and SPECIAL[e.questID]
  if s then return s[1], s[2], s[3], s[4] end
end
BAGS = { [6000] = 1 }
C_Item = { GetItemCount = function(id) return BAGS[id] or 0 end,
           GetItemSpell = function(id) if id == 6000 then return "Use", 123 end end,
           GetItemIconByID = function(id) return "icon" .. id end }
LibQuestieDB.Quest.Get = function(id, key) if id == 5 and key == "sourceItemId" then return 6000 end end
COMBAT = false; ZONE = 'The Barrens'; QuestSidebar.UI.SelectTab('zone')""")
ev("ZONE_CHANGED_NEW_AREA"); lua.execute("run_timers()")
def item_buttons(): return [b for b in lua.eval("QuestSidebar.UI.ItemButtons()").values() if b.shown]
bs = item_buttons()
check("buttons for quests with items", len(bs) == 2)
attrs = sorted(b.attrs["item"] for b in bs)
check("secure item attributes", attrs == ["item:5056", "item:6000"] and all(b.attrs["type"] == "item" for b in bs))
raptor = [b for b in bs if b.attrs["item"] == "item:5056"][0]
check("game's quest item: charges + log index", raptor.count.text == "3" and raptor.logIndex is not None)
check("tooltip names the quest", raptor.questTitle == "Raptor Thieves")
check("Questie source item used when the game flags none", any(b.attrs["item"] == "item:6000" and b.icon.texture == "icon6000" for b in bs))

lua.execute("BAGS = {}"); ev("BAG_UPDATE_DELAYED"); lua.execute("run_timers()")
check("item gone from bags: button gone", sorted(b.attrs["item"] for b in item_buttons()) == ["item:5056"])

lua.execute("for _, e in ipairs(LOG) do if e.questID == 3 then e.isComplete = true end end; QuestSidebar.Refresh()")
check("finished quest: no item button", item_buttons() == [])
lua.execute("SPECIAL[3][4] = true; QuestSidebar.UI.SelectTab('turnin')")
check("unless the item is still wanted when done (Turn in tab)", len(item_buttons()) == 1)
lua.execute("for _, e in ipairs(LOG) do if e.questID == 3 then e.isComplete = false end end; SPECIAL[3][4] = false; QuestSidebar.UI.SelectTab('zone')")

# combat: buttons are locked; they catch up afterwards
lua.execute("COMBAT = true; SPECIAL[5] = { '|Hitem:777:0|h[x]|h', 'tex', 1, false }; QuestSidebar.Refresh()")
check("in combat: no changes", len(item_buttons()) == 1 and lua.eval("QuestSidebar.UI.ItemsDirty()") is True)
lua.execute("COMBAT = false"); ev("PLAYER_REGEN_ENABLED"); lua.execute("run_timers()")
check("after combat: caught up", len(item_buttons()) == 2 and lua.eval("QuestSidebar.UI.ItemsDirty()") is False)
lua.execute("SPECIAL[5] = nil; QuestSidebar.Refresh()")

lua.execute("SlashCmdList.QUESTSIDEBAR('min')")
check("minimized: buttons hidden", item_buttons() == [])
lua.execute("SlashCmdList.QUESTSIDEBAR('min')")
check("restored: back", len(item_buttons()) == 1)
lua.execute("QuestSidebarFrame:Hide()")
check("sidebar hidden: buttons hidden", item_buttons() == [])
lua.execute("QuestSidebarFrame:Show(); QuestSidebar.UI.SelectTab('zone')")
lua.execute("QuestSidebar.UI.ToggleSettings(); local c; for _, it in ipairs(QuestSidebarSettings.items) do if it.label and it.label.text == 'Quest item buttons' then c = it end end; c:SetChecked(false); c.scripts.OnClick(c)")
check("setting turns them off", item_buttons() == [] and lua.eval("QuestSidebarDB.settings.questItems") is False)
lua.execute("local c; for _, it in ipairs(QuestSidebarSettings.items) do if it.label and it.label.text == 'Quest item buttons' then c = it end end; c:SetChecked(true); c.scripts.OnClick(c)")
check("and back on", len(item_buttons()) == 1)

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
