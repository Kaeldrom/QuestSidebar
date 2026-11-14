--[[
    The sidebar panel: a title bar, then zone headers with their quests and
    objectives underneath, scrolling with the mouse wheel.
]]

local QSB = QuestSidebar
local UI = {}
QSB.UI = UI

local WIDTH = 270
local MAX_HEIGHT = 520
local H_HEADER, H_QUEST, H_OBJ = 20, 16, 14

local GOLD = "|cffffd100"
local GREY = "|cff9a9a9a"
local GREEN = "|cff33ff66"
local RED = "|cffff5555"
local CYAN = "|cff66ddff"

local panel, scroll, content, title, minBtn
local lines = {}
local db
local scrollY = 0

---------------------------------------------------------------------------
-- helpers
---------------------------------------------------------------------------
local function Hex(c)
    if not c then return "|cffffffff" end
    return ("|cff%02x%02x%02x"):format((c.r or 1) * 255, (c.g or 1) * 255, (c.b or 1) * 255)
end

local function LevelColor(level)
    if GetQuestDifficultyColor and level then return Hex(GetQuestDifficultyColor(level)) end
    return "|cffffffff"
end

local function NewLine(i)
    local b = CreateFrame("Button", nil, content)
    b:SetWidth(WIDTH - 20)
    b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    local hl = b:CreateTexture(nil, "HIGHLIGHT")
    hl:SetAllPoints()
    hl:SetColorTexture(1, 1, 1, 0.07)
    b.bg = b:CreateTexture(nil, "BACKGROUND")
    b.bg:SetAllPoints()
    b.bg:SetColorTexture(1, 0.82, 0, 0.10)
    b.text = b:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    b.text:SetPoint("LEFT", 4, 0)
    b.text:SetPoint("RIGHT", -4, 0)
    b.text:SetJustifyH("LEFT")
    b.text:SetWordWrap(false)
    b.right = b:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    b.right:SetPoint("RIGHT", -4, 0)
    b.right:SetJustifyH("RIGHT")
    b:SetScript("OnClick", function(self, button) UI.OnLineClick(self, button) end)
    b:SetScript("OnEnter", function(self) UI.OnLineEnter(self) end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:EnableMouseWheel(true)
    b:SetScript("OnMouseWheel", function(_, d) UI.Scroll(d) end)
    lines[i] = b
    return b
end

---------------------------------------------------------------------------
-- clicks
---------------------------------------------------------------------------
function UI.OnLineClick(line, button)
    if line.kind == "header" then
        if IsShiftKeyDown() then QSB.TogglePin(line.zone) else QSB.ToggleZone(line.zone) end
    elseif line.kind == "quest" or line.kind == "objective" then
        local q = line.quest
        if IsModifiedClick and IsModifiedClick("CHATLINK") then QSB.LinkQuest(q)
        elseif button == "RightButton" then QSB.ToggleTrack(q)
        else QSB.OpenQuest(q) end
    end
end

function UI.OnLineEnter(line)
    GameTooltip:SetOwner(line, "ANCHOR_LEFT")
    if line.kind == "header" then
        GameTooltip:AddLine(line.zone)
        GameTooltip:AddLine("Click: open/close   Shift-click: " .. (QSB.DB().pinned[line.zone] and "unpin" or "pin open"), 0.8, 0.8, 0.8)
    else
        local q = line.quest
        GameTooltip:AddLine(q.title)
        for _, o in ipairs(q.objectives) do
            GameTooltip:AddLine(o.text, o.finished and 0.5 or 1, o.finished and 0.5 or 1, o.finished and 0.5 or 1)
        end
        GameTooltip:AddLine(" ")
        GameTooltip:AddLine("Click: open   Shift-click: link   Right-click: " .. (q.tracked and "untrack" or "track"), 0.8, 0.8, 0.8)
    end
    GameTooltip:Show()
end

---------------------------------------------------------------------------
-- drawing
---------------------------------------------------------------------------
local lastGroups = {}

function UI.Draw(groups)
    if not panel then return end
    lastGroups = groups
    local total, done = 0, 0
    for _, g in ipairs(groups) do total = total + #g.quests; done = done + g.done end
    title:SetText(CYAN .. "Quests|r " .. GREY .. total .. (done > 0 and ("  (" .. done .. " ready)") or "") .. "|r")

    if db.minimized then
        for _, l in ipairs(lines) do l:Hide() end
        scroll:Hide()
        panel:SetHeight(26)
        minBtn:SetText("+")
        return
    end
    scroll:Show()
    minBtn:SetText("-")

    local n, y = 0, 0
    local function Line(kind, height)
        n = n + 1
        local l = lines[n] or NewLine(n)
        l.kind, l.zone, l.quest = kind, nil, nil
        l:SetHeight(height)
        l:ClearAllPoints()
        l:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        l.right:SetText("")
        l.bg:Hide()
        l:Show()
        y = y + height
        return l
    end

    if total == 0 then
        local l = Line("empty", H_QUEST)
        l.text:SetText(GREY .. "Your quest log is empty.|r")
    end

    local here = QSB.CurrentZone()
    for _, g in ipairs(groups) do
        local open = QSB.IsOpen(g.zone)
        local h = Line("header", H_HEADER)
        h.zone = g.zone
        local tag = ""
        if g.zone == here then tag = GREEN .. "  here|r" elseif QSB.DB().pinned[g.zone] then tag = CYAN .. "  pinned|r" end
        h.text:SetText(GOLD .. (open and "- " or "+ ") .. g.zone .. "|r" .. tag)
        h.right:SetText(GREY .. (g.done > 0 and (g.done .. "/") or "") .. #g.quests .. "|r")
        if g.zone == here then h.bg:Show() end
        if open then
            for _, q in ipairs(g.quests) do
                local l = Line("quest", H_QUEST)
                l.quest = q
                local status = ""
                if q.complete then status = GREEN .. "  Ready to turn in|r"
                elseif q.failed then status = RED .. "  Failed|r" end
                local grp = (q.group and q.group > 0) and (GREY .. " (" .. q.group .. ")|r") or ""
                local track = q.tracked and (CYAN .. "* |r") or "  "
                l.text:SetText(track .. LevelColor(q.level) .. "[" .. (q.level or "?") .. "] " .. q.title .. "|r" .. grp .. status)
                if db.settings.showObjectives and not q.complete then
                    for _, o in ipairs(q.objectives) do
                        local ol = Line("objective", H_OBJ)
                        ol.quest = q
                        ol.text:SetText("      " .. (o.finished and (GREY .. o.text .. "|r") or o.text))
                    end
                end
            end
        end
    end
    for i = n + 1, #lines do lines[i]:Hide() end

    content:SetHeight(math.max(1, y))
    local h = math.min(MAX_HEIGHT, y + 32)
    panel:SetHeight(h)
    UI.maxScroll = math.max(0, y - (h - 32))
    scrollY = math.min(scrollY, UI.maxScroll)
    scroll:SetVerticalScroll(scrollY)
end

function UI.Scroll(delta)
    scrollY = math.max(0, math.min((UI.maxScroll or 0), scrollY - delta * 40))
    scroll:SetVerticalScroll(scrollY)
end

function UI.Lines() return lines end -- tests

---------------------------------------------------------------------------
-- Blizzard's tracker
---------------------------------------------------------------------------
local hooked = {}
-- restore = the player just switched hiding off, so bring it back now
function UI.ApplyTracker(restore)
    for _, name in ipairs({ "ObjectiveTrackerFrame", "QuestWatchFrame", "WatchFrame" }) do
        local f = _G[name]
        if f then
            if not hooked[f] and f.HookScript then
                hooked[f] = true
                f:HookScript("OnShow", function(self)
                    if db.settings.hideTracker and panel:IsShown() and not InCombatLockdown() then self:Hide() end
                end)
            end
            if db.settings.hideTracker and panel:IsShown() then
                if not InCombatLockdown() then f:Hide() end
            elseif restore and not f:IsShown() and not InCombatLockdown() then
                f:Show()
            end
        end
    end
end

---------------------------------------------------------------------------
-- panel
---------------------------------------------------------------------------
function UI.ResetPosition()
    if not panel then return end
    panel:ClearAllPoints()
    panel:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", -40, -250)
end

function UI.ApplyScale()
    if panel then panel:SetScale(db.settings.scale or 1) end
end

function UI.ToggleShown()
    if panel:IsShown() then
        panel:Hide()
        db.hidden = true
        UI.ApplyTracker(true)
        return
    else
        panel:Show()
        db.hidden = nil
        QSB.Refresh()
    end
    UI.ApplyTracker()
end

function UI.Init(savedDB)
    db = savedDB
    panel = CreateFrame("Frame", "QuestSidebarFrame", UIParent, "BackdropTemplate")
    panel:SetSize(WIDTH, 200)
    panel:SetFrameStrata("MEDIUM")
    panel:SetClampedToScreen(true)
    panel:SetMovable(true)
    panel:EnableMouse(true)
    panel:RegisterForDrag("LeftButton")
    if panel.SetBackdrop then
        panel:SetBackdrop({ bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
            edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", tile = true, tileSize = 16, edgeSize = 12,
            insets = { left = 3, right = 3, top = 3, bottom = 3 } })
        panel:SetBackdropColor(0, 0, 0, 0.55)
        panel:SetBackdropBorderColor(0.4, 0.4, 0.4, 0.8)
    end
    panel:SetScript("OnDragStart", function(self) if not db.settings.locked then self:StartMoving() end end)
    panel:SetScript("OnDragStop", function(self)
        self:StopMovingOrSizing()
        local p, _, rp, x, y = self:GetPoint()
        db.point = { p, rp, x, y }
    end)
    panel:EnableMouseWheel(true)
    panel:SetScript("OnMouseWheel", function(_, d) UI.Scroll(d) end)

    title = panel:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    title:SetPoint("TOPLEFT", 10, -7)

    minBtn = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    minBtn:SetSize(20, 18)
    minBtn:SetPoint("TOPRIGHT", -5, -4)
    minBtn:SetText("-")
    minBtn:SetScript("OnClick", function()
        db.minimized = not db.minimized or nil
        QSB.Refresh()
    end)

    scroll = CreateFrame("ScrollFrame", nil, panel)
    scroll:SetPoint("TOPLEFT", 8, -26)
    scroll:SetPoint("BOTTOMRIGHT", -8, 6)
    content = CreateFrame("Frame", nil, scroll)
    content:SetSize(WIDTH - 16, 1)
    scroll:SetScrollChild(content)

    if db.point then
        panel:ClearAllPoints()
        panel:SetPoint(db.point[1], UIParent, db.point[2], db.point[3], db.point[4])
    else
        UI.ResetPosition()
    end
    UI.ApplyScale()
    if db.hidden then panel:Hide() else panel:Show() end
    UI.ApplyTracker()
end
