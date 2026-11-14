--[[
    Quest Sidebar
    Your whole quest log down the side of the screen, tracked or not, grouped by
    zone. The zone you're in jumps to the top and opens by itself; fly to the
    Barrens and the Barrens quests open, fly on to Ashenvale and those open instead.

    Data side: reads the quest log into groups. The panel lives in QuestSidebar_UI.lua.

    QuestSidebarDB = { settings = { autoZone, hideTracker, locked, scale }, pinned = { [zone]=true }, point = {...}, size = {w, h}, hidden }
]]

local ADDON = ...
local QSB = {}
QuestSidebar = QSB

local DEFAULTS = { autoZone = true, hideTracker = true, locked = false, scale = 1, showObjectives = true, opacity = 1 }

local db
QSB.open = {}          -- zones opened by hand this visit (cleared when you change zone)
QSB.closed = {}        -- the current zone, closed by hand
local currentZone

local function Print(msg)
    DEFAULT_CHAT_FRAME:AddMessage("|cff66ddffQuest Sidebar|r: " .. tostring(msg))
end
QSB.Print = Print

local function IsSecret(v)
    return issecretvalue ~= nil and issecretvalue(v)
end

function QSB.DB() return db end

---------------------------------------------------------------------------
-- Reading the quest log
---------------------------------------------------------------------------
local function NumEntries()
    if C_QuestLog and C_QuestLog.GetNumQuestLogEntries then return (C_QuestLog.GetNumQuestLogEntries()) end
    return (GetNumQuestLogEntries())
end

local function Entry(i)
    if C_QuestLog and C_QuestLog.GetInfo then
        local e = C_QuestLog.GetInfo(i)
        if not e then return nil end
        return { title = e.title, level = e.level, isHeader = e.isHeader, isCollapsed = e.isCollapsed,
                 isComplete = e.isComplete, questID = e.questID, isHidden = e.isHidden, suggestedGroup = e.suggestedGroup,
                 index = i }
    end
    local title, level, _, isHeader, isCollapsed, isComplete, _, questID = GetQuestLogTitle(i)
    if not title then return nil end
    return { title = title, level = level, isHeader = isHeader, isCollapsed = isCollapsed,
             isComplete = isComplete, questID = questID, index = i }
end

-- Quests under a header that is collapsed in Blizzard's quest log are invisible
-- to addons, so open those headers (the sidebar does the collapsing now).
local function ExpandBlizzardHeaders()
    if InCombatLockdown and InCombatLockdown() then return false end
    local expanded = false
    for i = NumEntries(), 1, -1 do
        local e = Entry(i)
        if e and e.isHeader and e.isCollapsed then
            if ExpandQuestHeader then pcall(ExpandQuestHeader, i) end
            expanded = true
        end
    end
    return expanded
end

local function Objectives(e)
    local list = {}
    local objs = C_QuestLog and C_QuestLog.GetQuestObjectives and e.questID and C_QuestLog.GetQuestObjectives(e.questID)
    if objs then
        for _, o in ipairs(objs) do
            if o.text and o.text ~= "" and not IsSecret(o.text) then
                list[#list + 1] = { text = o.text, finished = o.finished }
            end
        end
    elseif GetNumQuestLeaderBoards then
        for j = 1, (GetNumQuestLeaderBoards(e.index) or 0) do
            local text, _, finished = GetQuestLogLeaderBoard(j, e.index)
            if text and text ~= "" then list[#list + 1] = { text = text, finished = finished } end
        end
    end
    return list
end

function QSB.IsTracked(questID, index)
    if C_QuestLog and C_QuestLog.GetQuestWatchType then return C_QuestLog.GetQuestWatchType(questID) ~= nil end
    if IsQuestWatched then return IsQuestWatched(index) and true or false end
    return false
end

-- "Dungeon", "Elite", "Raid"... or nil
function QSB.TagText(questID)
    if not questID or questID == 0 then return nil end
    if C_QuestLog and C_QuestLog.GetQuestTagInfo then
        local info = C_QuestLog.GetQuestTagInfo(questID)
        if info and info.tagName and info.tagName ~= "" and not IsSecret(info.tagName) then return info.tagName end
    end
    return nil
end

-- The quest's short objective text ("Scout the gazebo on Mystral Lake..."), cached
-- because reading it means briefly selecting the quest in Blizzard's log.
local detailCache = {}
function QSB.Details(q)
    if detailCache[q.questID] ~= nil then return detailCache[q.questID] or nil end
    local text
    if GetQuestLogQuestText then
        if C_QuestLog and C_QuestLog.SetSelectedQuest then
            local old = C_QuestLog.GetSelectedQuest and C_QuestLog.GetSelectedQuest()
            C_QuestLog.SetSelectedQuest(q.questID)
            local _, objectives = GetQuestLogQuestText()
            text = objectives
            if old and old ~= 0 then C_QuestLog.SetSelectedQuest(old) end
        elseif SelectQuestLogEntry and GetQuestLogSelection then
            local old = GetQuestLogSelection()
            SelectQuestLogEntry(q.index)
            local _, objectives = GetQuestLogQuestText()
            text = objectives
            if old and old > 0 then SelectQuestLogEntry(old) end
        end
    end
    if text and (text == "" or IsSecret(text)) then text = nil end
    detailCache[q.questID] = text or false
    return text
end

-- { {zone, quests = { {title, level, questID, index, complete, objectives, tracked} }, total, done }, ... }
function QSB.ReadLog()
    if ExpandBlizzardHeaders() then
        -- the log reshuffles after expanding; the QUEST_LOG_UPDATE that follows redraws us
    end
    local groups, group = {}, nil
    for i = 1, NumEntries() do
        local e = Entry(i)
        if e and not IsSecret(e.title) then
            if e.isHeader then
                group = { zone = e.title, quests = {}, done = 0 }
                groups[#groups + 1] = group
            elseif not e.isHidden and e.title then
                if not group then
                    group = { zone = "Other", quests = {}, done = 0 }
                    groups[#groups + 1] = group
                end
                local complete = e.isComplete == true or e.isComplete == 1
                group.quests[#group.quests + 1] = {
                    title = e.title, level = e.level, questID = e.questID, index = i, complete = complete,
                    failed = e.isComplete == -1, group = e.suggestedGroup,
                    objectives = Objectives(e), tracked = QSB.IsTracked(e.questID, i),
                    tag = QSB.TagText(e.questID),
                }
                if complete then group.done = group.done + 1 end
            end
        end
    end
    -- drop empty headers
    for i = #groups, 1, -1 do
        if #groups[i].quests == 0 then table.remove(groups, i) end
    end
    return groups
end

---------------------------------------------------------------------------
-- Which zone are we in, and which groups are open?
---------------------------------------------------------------------------
local function ZoneNames()
    local names = {}
    for _, f in ipairs({ GetRealZoneText, GetZoneText }) do
        local z = f and f()
        if z and z ~= "" and not IsSecret(z) then names[z] = true end
    end
    if C_Map and C_Map.GetBestMapForUnit then
        -- also the parent zone when standing in a sub-area that has its own map
        local id = C_Map.GetBestMapForUnit("player")
        local guard = 0
        while id and guard < 4 do
            local info = C_Map.GetMapInfo(id)
            if not info then break end
            if info.name and not IsSecret(info.name) then names[info.name] = true end
            if info.mapType and Enum and Enum.UIMapType and info.mapType <= Enum.UIMapType.Zone then break end
            id = info.parentMapID
            guard = guard + 1
        end
    end
    return names
end

function QSB.CurrentZone() return currentZone end

-- the quest-log header that matches where we are (headers are zone names)
function QSB.MatchZone(groups)
    local names = ZoneNames()
    for _, g in ipairs(groups) do
        if names[g.zone] then return g.zone end
    end
    return GetRealZoneText and GetRealZoneText() or nil
end

function QSB.IsOpen(zone)
    if db.pinned[zone] then return true end
    if zone == currentZone and db.settings.autoZone then return not QSB.closed[zone] end
    return QSB.open[zone] == true
end

function QSB.ToggleZone(zone)
    if zone == currentZone and db.settings.autoZone then
        QSB.closed[zone] = not QSB.closed[zone] or nil
        if db.pinned[zone] then db.pinned[zone] = nil; QSB.closed[zone] = true end
    elseif db.pinned[zone] then
        db.pinned[zone] = nil
        QSB.open[zone] = nil
    else
        QSB.open[zone] = not QSB.open[zone] or nil
    end
    QSB.Refresh()
end

function QSB.TogglePin(zone)
    if db.pinned[zone] then db.pinned[zone] = nil else db.pinned[zone] = true end
    QSB.Refresh()
end

-- A-Z by zone name (a leading "The " is ignored, so The Barrens sorts under B)
local function SortKey(zone)
    return (zone:gsub("^[Tt]he%s+", "")):lower()
end
QSB.SortKey = SortKey

function QSB.Ordered(groups)
    local out = {}
    for _, g in ipairs(groups) do out[#out + 1] = g end
    table.sort(out, function(a, b) return SortKey(a.zone) < SortKey(b.zone) end)
    return out
end

-- the group for where we are standing, or nil
function QSB.HereGroup(groups)
    for _, g in ipairs(groups) do if g.zone == currentZone then return g end end
end

-- per-quest show/hide of objectives (click the quest)
QSB.questFolded = {}
function QSB.ToggleQuest(q)
    QSB.questFolded[q.questID] = not QSB.questFolded[q.questID] or nil
    QSB.Refresh()
end

local function OnZoneChanged()
    local groups = QSB.ReadLog()
    local zone = QSB.MatchZone(groups)
    if zone ~= currentZone then
        currentZone = zone
        if db.settings.autoZone then
            wipe(QSB.open)   -- close what you opened by hand somewhere else; pinned zones stay
            wipe(QSB.closed)
        end
    end
    QSB.Refresh(groups)
end
QSB.OnZoneChanged = OnZoneChanged

---------------------------------------------------------------------------
-- Actions on a quest
---------------------------------------------------------------------------
function QSB.OpenQuest(q)
    if QuestLogFrame and SelectQuestLogEntry then
        SelectQuestLogEntry(q.index)
        if not QuestLogFrame:IsShown() then ShowUIPanel(QuestLogFrame) end
        if QuestLog_Update then QuestLog_Update() end
    elseif QuestMapFrame_OpenToQuestDetails then
        QuestMapFrame_OpenToQuestDetails(q.questID)
    elseif ToggleQuestLog then
        ToggleQuestLog()
    end
end

function QSB.LinkQuest(q)
    local link = (C_QuestLog and C_QuestLog.GetQuestLink and C_QuestLog.GetQuestLink(q.questID))
        or (GetQuestLink and GetQuestLink(q.questID))
    if link and ChatEdit_InsertLink then ChatEdit_InsertLink(link) end
end

function QSB.ToggleTrack(q)
    if C_QuestLog and C_QuestLog.AddQuestWatch then
        if q.tracked then C_QuestLog.RemoveQuestWatch(q.questID) else C_QuestLog.AddQuestWatch(q.questID) end
    elseif AddQuestWatch then
        if q.tracked then RemoveQuestWatch(q.index) else AddQuestWatch(q.index) end
    end
    QSB.QueueRefresh()
end

---------------------------------------------------------------------------
-- Refresh plumbing
---------------------------------------------------------------------------
function QSB.Refresh(groups)
    if not QSB.UI then return end
    groups = groups or QSB.ReadLog()
    QSB.UI.Draw(QSB.Ordered(groups))
end

local queued = false
function QSB.QueueRefresh()
    if queued then return end
    queued = true
    C_Timer.After(0.2, function()
        queued = false
        QSB.Refresh()
    end)
end

---------------------------------------------------------------------------
-- Slash commands
---------------------------------------------------------------------------
local function OnOff(v) return v and "|cff33ff66on|r" or "|cffff6666off|r" end

local function Slash(msg)
    local cmd, arg = (msg or ""):lower():match("^%s*(%S*)%s*(.-)%s*$")
    local s = db.settings
    if cmd == "" or cmd == "toggle" then
        QSB.UI.ToggleShown()
    elseif cmd == "settings" or cmd == "options" or cmd == "config" then
        QSB.UI.ToggleSettings()
    elseif cmd == "opacity" and tonumber(arg) then
        local v = tonumber(arg)
        if v > 1 then v = v / 100 end
        s.opacity = math.max(0.1, math.min(1, v))
        QSB.UI.ApplyOpacity()
        Print("Opacity " .. math.floor(s.opacity * 100 + 0.5) .. "%")
    elseif cmd == "auto" then
        s.autoZone = not s.autoZone
        Print("Open the zone you're in automatically: " .. OnOff(s.autoZone))
        QSB.Refresh()
    elseif cmd == "tracker" then
        s.hideTracker = not s.hideTracker
        Print("Hide Blizzard's quest tracker: " .. OnOff(s.hideTracker) .. (s.hideTracker and "" or " (a /reload brings it back fully)"))
        QSB.UI.ApplyTracker(true)
    elseif cmd == "lock" then
        s.locked = not s.locked
        Print("Panel locked: " .. OnOff(s.locked))
    elseif cmd == "objectives" then
        s.showObjectives = not s.showObjectives
        Print("Show objectives: " .. OnOff(s.showObjectives))
        QSB.Refresh()
    elseif cmd == "scale" and tonumber(arg) then
        s.scale = math.max(0.5, math.min(2, tonumber(arg)))
        QSB.UI.ApplyScale()
        Print("Scale " .. s.scale)
    elseif cmd == "reset" then
        wipe(db.pinned)
        QSB.UI.ResetPosition()
        Print("Back to the default size and position, and all zones unpinned.")
        QSB.Refresh()
    else
        Print("/qsb - show/hide the sidebar")
        Print("/qsb auto - open the zone you're in automatically (" .. OnOff(s.autoZone) .. ")")
        Print("/qsb tracker - hide Blizzard's quest tracker (" .. OnOff(s.hideTracker) .. ")")
        Print("/qsb objectives - show objective lines (" .. OnOff(s.showObjectives) .. ")")
        Print("/qsb settings - open the settings (or click the cog on the window)")
        Print("/qsb opacity 70 | lock | scale 0.8 | reset")
        Print("Click a zone to open/close it, Shift-click to pin it open. Click a quest to open it, Shift-click to link, right-click to track.")
    end
end

---------------------------------------------------------------------------
-- Events
---------------------------------------------------------------------------
local frame = CreateFrame("Frame")
QSB.frame = frame

frame:SetScript("OnEvent", function(_, event)
    if event == "PLAYER_LOGIN" then
        QuestSidebarDB = QuestSidebarDB or {}
        db = QuestSidebarDB
        db.settings = db.settings or {}
        db.pinned = db.pinned or {}
        for k, v in pairs(DEFAULTS) do if db.settings[k] == nil then db.settings[k] = v end end
        if QSB.UI then QSB.UI.Init(db) end
        for _, ev in ipairs({ "QUEST_LOG_UPDATE", "QUEST_WATCH_LIST_CHANGED", "UNIT_QUEST_LOG_CHANGED", "QUEST_ACCEPTED",
                              "QUEST_REMOVED", "QUEST_TURNED_IN", "ZONE_CHANGED_NEW_AREA", "ZONE_CHANGED",
                              "ZONE_CHANGED_INDOORS", "PLAYER_ENTERING_WORLD", "PLAYER_REGEN_ENABLED" }) do
            pcall(frame.RegisterEvent, frame, ev)
        end
        SLASH_QUESTSIDEBAR1 = "/qsb"
        SLASH_QUESTSIDEBAR2 = "/questsidebar"
        SlashCmdList.QUESTSIDEBAR = Slash
    elseif event == "ZONE_CHANGED_NEW_AREA" or event == "PLAYER_ENTERING_WORLD" or event == "ZONE_CHANGED"
        or event == "ZONE_CHANGED_INDOORS" then
        if db then OnZoneChanged() end
    elseif event == "PLAYER_REGEN_ENABLED" then
        if db then QSB.UI.ApplyTracker(); QSB.QueueRefresh() end
    elseif db then
        QSB.QueueRefresh()
    end
end)
frame:RegisterEvent("PLAYER_LOGIN")

function QuestSidebar_Toggle() QSB.UI.ToggleShown() end
