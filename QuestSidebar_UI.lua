--[[
    The sidebar window, styled after the quest log in WoW's world map:
      * grey zone header bars with gold names and a -/+ button
      * each quest: a round quest icon, "[level] Title" coloured by difficulty,
        "- objective" lines, a (Dungeon)/(Elite) tag, an open button and a track checkbox
    Two tabs: Current Zone (default) and All. The window is resizable, keeps its size
    and position, and scrolls inside instead of growing.
]]

local QSB = QuestSidebar
local UI = {}
QSB.UI = UI

local DEFAULT_W, DEFAULT_H = 300, 460
local MIN_W, MIN_H, MAX_W, MAX_H = 230, 180, 700, 1200
local HEADER_H = 24
local PAD = 6

local GREY = "|cff9a9a9a"
local GREEN = "|cff40c040"
local RED = "|cffff4040"
local TAG = "|cff4fd24f"

local ICON_INCOMPLETE = "Interface\\GossipFrame\\IncompleteQuestIcon"
local ICON_COMPLETE = "Interface\\GossipFrame\\ActiveQuestIcon"
local ICON_PLUS = "Interface\\Buttons\\UI-PlusButton-Up"
local ICON_MINUS = "Interface\\Buttons\\UI-MinusButton-Up"
local ICON_OPEN = "Interface\\Buttons\\UI-SpellbookIcon-NextPage-Up"

local db
local panel, scroll, content, tabZone, tabAll, empty
local headers, quests = {}, {}
local scrollY = 0
UI.tab = "zone"

---------------------------------------------------------------------------
-- helpers
---------------------------------------------------------------------------
local function Hex(c)
    if not c then return "|cffffffff" end
    return ("|cff%02x%02x%02x"):format((c.r or 1) * 255, (c.g or 1) * 255, (c.b or 1) * 255)
end

local function LevelColor(level)
    if GetQuestDifficultyColor and level then return Hex(GetQuestDifficultyColor(level)) end
    return "|cffffd100"
end

local function Width()
    return math.max(MIN_W, (db and db.size and db.size[1]) or DEFAULT_W) - 34
end

local function SetGradient(tex, r1, g1, b1, a1, r2, g2, b2, a2)
    tex:SetColorTexture(1, 1, 1, 1)
    local ok = CreateColor and pcall(tex.SetGradient, tex, "HORIZONTAL", CreateColor(r1, g1, b1, a1), CreateColor(r2, g2, b2, a2))
    if not ok then tex:SetColorTexture(r1, g1, b1, a1) end
end

---------------------------------------------------------------------------
-- pooled rows
---------------------------------------------------------------------------
local function NewHeader()
    local h = CreateFrame("Button", nil, content)
    h:SetHeight(HEADER_H)
    h.bar = h:CreateTexture(nil, "BACKGROUND")
    h.bar:SetAllPoints()
    SetGradient(h.bar, 0.30, 0.30, 0.30, 0.95, 0.14, 0.14, 0.14, 0.90)
    h.edge = h:CreateTexture(nil, "BORDER")
    h.edge:SetPoint("BOTTOMLEFT")
    h.edge:SetPoint("BOTTOMRIGHT")
    h.edge:SetHeight(1)
    h.edge:SetColorTexture(0, 0, 0, 0.8)
    local hl = h:CreateTexture(nil, "HIGHLIGHT")
    hl:SetAllPoints()
    hl:SetColorTexture(1, 1, 1, 0.06)
    h.text = h:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
    h.text:SetPoint("LEFT", 8, 0)
    h.text:SetJustifyH("LEFT")
    h.text:SetWordWrap(false)
    h.count = h:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    h.count:SetPoint("RIGHT", -28, 0)
    h.toggle = h:CreateTexture(nil, "ARTWORK")
    h.toggle:SetSize(16, 16)
    h.toggle:SetPoint("RIGHT", -6, 0)
    h:RegisterForClicks("LeftButtonUp")
    h:SetScript("OnClick", function(self)
        if IsShiftKeyDown() then QSB.TogglePin(self.zone) else QSB.ToggleZone(self.zone) end
    end)
    h:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine(self.zone)
        GameTooltip:AddLine("Click: open/close   Shift-click: " .. (db.pinned[self.zone] and "unpin" or "keep open everywhere"), 0.8, 0.8, 0.8)
        GameTooltip:Show()
    end)
    h:SetScript("OnLeave", function() GameTooltip:Hide() end)
    h:EnableMouseWheel(true)
    h:SetScript("OnMouseWheel", function(_, d) UI.Scroll(d) end)
    return h
end

local function NewQuest()
    local r = CreateFrame("Button", nil, content)
    r:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    local hl = r:CreateTexture(nil, "HIGHLIGHT")
    hl:SetAllPoints()
    hl:SetColorTexture(1, 1, 1, 0.05)

    r.icon = r:CreateTexture(nil, "ARTWORK")
    r.icon:SetSize(20, 20)
    r.icon:SetPoint("TOPLEFT", 4, -1)

    r.title = r:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    r.title:SetPoint("TOPLEFT", 30, -3)
    r.title:SetJustifyH("LEFT")
    r.title:SetWordWrap(true)

    r.objectives = r:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    r.objectives:SetJustifyH("LEFT")
    r.objectives:SetWordWrap(true)
    r.objectives:SetSpacing(1)

    r.details = r:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    r.details:SetJustifyH("LEFT")
    r.details:SetWordWrap(true)
    r.details:SetTextColor(0.80, 0.75, 0.62)

    r.track = CreateFrame("CheckButton", nil, r, "UICheckButtonTemplate")
    r.track:SetSize(22, 22)
    r.track:SetPoint("TOPRIGHT", 0, 2)
    r.track:SetScript("OnClick", function(self) QSB.ToggleTrack(self:GetParent().quest) end)
    r.track:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine(self:GetChecked() and "Stop tracking" or "Track this quest")
        GameTooltip:Show()
    end)
    r.track:SetScript("OnLeave", function() GameTooltip:Hide() end)

    r.open = CreateFrame("Button", nil, r)
    r.open:SetSize(18, 18)
    r.open:SetPoint("RIGHT", r.track, "LEFT", -2, 0)
    r.open:SetNormalTexture(ICON_OPEN)
    r.open:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    r.open:SetScript("OnClick", function(self) QSB.OpenQuest(self:GetParent().quest) end)
    r.open:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine("Open in the quest log")
        GameTooltip:Show()
    end)
    r.open:SetScript("OnLeave", function() GameTooltip:Hide() end)

    r.tag = r:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    r.tag:SetPoint("RIGHT", r.open, "LEFT", -2, 0)
    r.tag:SetJustifyH("RIGHT")

    r:SetScript("OnClick", function(self, button)
        local q = self.quest
        if IsModifiedClick and IsModifiedClick("CHATLINK") then QSB.LinkQuest(q)
        elseif button == "RightButton" then QSB.ToggleTrack(q)
        else QSB.ToggleQuest(q) end
    end)
    r:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine(self.quest.title)
        GameTooltip:AddLine("Click: show/hide objectives   Shift-click: link in chat   Right-click: track", 0.8, 0.8, 0.8, true)
        GameTooltip:Show()
    end)
    r:SetScript("OnLeave", function() GameTooltip:Hide() end)
    r:EnableMouseWheel(true)
    r:SetScript("OnMouseWheel", function(_, d) UI.Scroll(d) end)
    return r
end

---------------------------------------------------------------------------
-- drawing
---------------------------------------------------------------------------
local function FillQuest(r, q, width, showDetails)
    r.quest = q
    r:SetWidth(width)
    r.icon:SetTexture(q.complete and ICON_COMPLETE or ICON_INCOMPLETE)
    if q.failed then r.icon:SetVertexColor(1, 0.3, 0.3) else r.icon:SetVertexColor(1, 1, 1) end

    local tag = q.tag and (TAG .. "(" .. q.tag .. ")|r") or ""
    r.tag:SetText(tag)
    local tagW = q.tag and ((r.tag:GetStringWidth() or 0) + 4) or 0
    r.title:SetWidth(width - 30 - 46 - tagW)
    r.title:SetText(LevelColor(q.level) .. "[" .. (q.level or "?") .. "] " .. q.title .. "|r")
    r.track:SetChecked(q.tracked)

    local h = math.max(22, (r.title:GetStringHeight() or 14) + 6)

    local folded = QSB.questFolded[q.questID]
    local objText
    if not folded then
        local parts = {}
        if q.complete then
            parts[#parts + 1] = GREEN .. "- Ready to turn in|r"
        elseif q.failed then
            parts[#parts + 1] = RED .. "- Failed|r"
        elseif db.settings.showObjectives then
            for _, o in ipairs(q.objectives) do
                parts[#parts + 1] = o.finished and (GREY .. "- " .. o.text .. "|r") or ("- " .. o.text)
            end
        end
        if #parts > 0 then objText = table.concat(parts, "\n") end
    end
    r.objectives:ClearAllPoints()
    r.objectives:SetPoint("TOPLEFT", 30, -h)
    r.objectives:SetWidth(width - 36)
    if objText then
        r.objectives:SetText(objText)
        r.objectives:Show()
        h = h + (r.objectives:GetStringHeight() or 14) + 2
    else
        r.objectives:SetText("")
        r.objectives:Hide()
    end

    local details = showDetails and not folded and QSB.Details(q)
    r.details:ClearAllPoints()
    r.details:SetPoint("TOPLEFT", 30, -h - 2)
    r.details:SetWidth(width - 36)
    if details then
        r.details:SetText(details)
        r.details:Show()
        h = h + (r.details:GetStringHeight() or 12) + 4
    else
        r.details:SetText("")
        r.details:Hide()
    end
    r:SetHeight(h + PAD)
    return h + PAD
end

local lastGroups = {}

function UI.Draw(groups)
    if not panel then return end
    lastGroups = groups
    local width = Width()
    local nh, nq, y = 0, 0, 0
    local here = QSB.CurrentZone()

    local total = 0
    for _, g in ipairs(groups) do total = total + #g.quests end
    if UI.SetTitle then UI.SetTitle("Quests  " .. GREY .. total .. "/25|r") end

    local function Header(g, open)
        nh = nh + 1
        local h = headers[nh] or NewHeader()
        headers[nh] = h
        h.zone = g.zone
        h:SetWidth(width)
        h:ClearAllPoints()
        h:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        local mark = (g.zone == here and UI.tab == "all") and (GREEN .. "  •|r") or (db.pinned[g.zone] and "|cff66ddff  •|r" or "")
        h.text:SetText(g.zone .. mark)
        h.count:SetText(GREY .. (g.done > 0 and (g.done .. "/") or "") .. #g.quests .. "|r")
        h.toggle:SetTexture(open and ICON_MINUS or ICON_PLUS)
        h:Show()
        y = y + HEADER_H + 4
    end

    local function Quest(q, details)
        nq = nq + 1
        local r = quests[nq] or NewQuest()
        quests[nq] = r
        r:ClearAllPoints()
        r:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        y = y + FillQuest(r, q, width, details)
        r:Show()
    end

    empty:Hide()
    if UI.tab == "zone" then
        local g = QSB.HereGroup(groups)
        if g then
            Header(g, true)
            for _, q in ipairs(g.quests) do Quest(q, true) end
        else
            empty:SetText(GREY .. "No quests for " .. (here or "this zone") .. ".|r\n\n" .. "Open the |cffffd100All|r tab to see your other quests.")
            empty:Show()
        end
    else
        for _, g in ipairs(groups) do
            local open = QSB.IsOpen(g.zone)
            Header(g, open)
            if open then
                for _, q in ipairs(g.quests) do Quest(q, false) end
            end
        end
        if total == 0 then
            empty:SetText(GREY .. "Your quest log is empty.|r")
            empty:Show()
        end
    end
    for i = nh + 1, #headers do headers[i]:Hide() end
    for i = nq + 1, #quests do quests[i]:Hide() end

    content:SetWidth(width)
    content:SetHeight(math.max(1, y))
    -- the window keeps its size: content just scrolls
    local view = (scroll:GetHeight() or 300)
    UI.maxScroll = math.max(0, y - view)
    scrollY = math.min(scrollY, UI.maxScroll)
    UI.ApplyScroll()
end

function UI.ApplyScroll()
    scroll:SetVerticalScroll(scrollY)
    if UI.bar then
        UI.bar:SetMinMaxValues(0, UI.maxScroll or 0)
        UI.bar:SetValue(scrollY)
        if (UI.maxScroll or 0) > 0 then UI.bar:Show() else UI.bar:Hide() end
    end
end

function UI.Scroll(delta)
    scrollY = math.max(0, math.min((UI.maxScroll or 0), scrollY - delta * 40))
    UI.ApplyScroll()
end

function UI.SelectTab(tab)
    UI.tab = tab
    scrollY = 0
    if tab == "zone" then tabZone:Disable(); tabAll:Enable() else tabZone:Enable(); tabAll:Disable() end
    QSB.Refresh()
end

-- tests
function UI.Headers() return headers end
function UI.Quests() return quests end
function UI.Empty() return empty end

---------------------------------------------------------------------------
-- Blizzard's tracker
---------------------------------------------------------------------------
local hooked = {}
-- restore = the player just switched hiding off (or closed us), so bring it back now
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
-- window
---------------------------------------------------------------------------
local function SavePosition()
    -- store the top-left corner so resizing and expanding never move the window
    local left, top = panel:GetLeft(), panel:GetTop()
    if left and top then db.point = { "TOPLEFT", "BOTTOMLEFT", left, top } end
end

local function ApplyPosition()
    panel:ClearAllPoints()
    if db.point then
        panel:SetPoint(db.point[1], UIParent, db.point[2], db.point[3], db.point[4])
    else
        panel:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", -40, -230)
    end
end

function UI.ResetPosition()
    if not panel then return end
    db.point, db.size = nil, nil
    panel:SetSize(DEFAULT_W, DEFAULT_H)
    ApplyPosition()
end

function UI.ApplyScale()
    if panel then panel:SetScale(db.settings.scale or 1) end
end

function UI.ToggleShown()
    if panel:IsShown() then panel:Hide() else panel:Show() end
end

function UI.Init(savedDB)
    db = savedDB
    local ok, f = pcall(CreateFrame, "Frame", "QuestSidebarFrame", UIParent, "BasicFrameTemplateWithInset")
    if not ok or not f then
        f = CreateFrame("Frame", "QuestSidebarFrame", UIParent, "BackdropTemplate")
        if f.SetBackdrop then
            f:SetBackdrop({ bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background-Dark",
                edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border", tile = true, tileSize = 32, edgeSize = 24,
                insets = { left = 6, right = 6, top = 6, bottom = 6 } })
        end
    end
    panel = f
    local size = db.size or { DEFAULT_W, DEFAULT_H }
    panel:SetSize(size[1], size[2])
    panel:SetFrameStrata("MEDIUM")
    panel:SetClampedToScreen(true)
    panel:SetMovable(true)
    panel:SetResizable(true)
    if panel.SetResizeBounds then panel:SetResizeBounds(MIN_W, MIN_H, MAX_W, MAX_H)
    elseif panel.SetMinResize then panel:SetMinResize(MIN_W, MIN_H); panel:SetMaxResize(MAX_W, MAX_H) end
    panel:EnableMouse(true)
    panel:RegisterForDrag("LeftButton")
    panel:SetScript("OnDragStart", function(self) if not db.settings.locked then self:StartMoving() end end)
    panel:SetScript("OnDragStop", function(self) self:StopMovingOrSizing(); SavePosition() end)

    local titleText = type(panel.TitleText) == "table" and panel.TitleText
    if not titleText then
        titleText = panel:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
        titleText:SetPoint("TOP", 0, -5)
    end
    function UI.SetTitle(t) titleText:SetText(t) end
    UI.SetTitle("Quests")

    -- tabs
    tabZone = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    tabZone:SetSize(110, 22)
    tabZone:SetPoint("TOPLEFT", 10, -28)
    tabZone:SetText("Current Zone")
    tabZone:SetScript("OnClick", function() UI.SelectTab("zone") end)
    tabAll = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    tabAll:SetSize(60, 22)
    tabAll:SetPoint("LEFT", tabZone, "RIGHT", 4, 0)
    tabAll:SetText("All")
    tabAll:SetScript("OnClick", function() UI.SelectTab("all") end)

    -- scrolling list
    scroll = CreateFrame("ScrollFrame", nil, panel)
    scroll:SetPoint("TOPLEFT", 10, -56)
    scroll:SetPoint("BOTTOMRIGHT", -24, 12)
    content = CreateFrame("Frame", nil, scroll)
    content:SetSize(Width(), 1)
    scroll:SetScrollChild(content)
    scroll:EnableMouseWheel(true)
    scroll:SetScript("OnMouseWheel", function(_, d) UI.Scroll(d) end)

    local bar = CreateFrame("Slider", nil, panel)
    bar:SetPoint("TOPRIGHT", -8, -58)
    bar:SetPoint("BOTTOMRIGHT", -8, 26)
    bar:SetWidth(10)
    bar:SetOrientation("VERTICAL")
    bar:SetMinMaxValues(0, 0)
    bar:SetValueStep(1)
    local track = bar:CreateTexture(nil, "BACKGROUND")
    track:SetAllPoints()
    track:SetColorTexture(0, 0, 0, 0.35)
    local thumb = bar:CreateTexture(nil, "OVERLAY")
    thumb:SetColorTexture(0.6, 0.55, 0.4, 0.8)
    thumb:SetSize(8, 36)
    bar:SetThumbTexture(thumb)
    bar:SetScript("OnValueChanged", function(_, v)
        scrollY = v
        scroll:SetVerticalScroll(v)
    end)
    UI.bar = bar

    empty = content:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    empty:SetPoint("TOPLEFT", 8, -12)
    empty:SetWidth(Width() - 16)
    empty:SetJustifyH("LEFT")

    -- resize grip
    local grip = CreateFrame("Button", nil, panel)
    grip:SetSize(16, 16)
    grip:SetPoint("BOTTOMRIGHT", -4, 4)
    grip:SetNormalTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Up")
    grip:SetHighlightTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Highlight")
    grip:SetPushedTexture("Interface\\ChatFrame\\UI-ChatIM-SizeGrabber-Down")
    grip:SetScript("OnMouseDown", function()
        SavePosition()
        ApplyPosition() -- pin the top-left so only the bottom-right moves
        panel:StartSizing("BOTTOMRIGHT")
    end)
    grip:SetScript("OnMouseUp", function()
        panel:StopMovingOrSizing()
        db.size = { math.floor(panel:GetWidth() + 0.5), math.floor(panel:GetHeight() + 0.5) }
        SavePosition()
        ApplyPosition()
        empty:SetWidth(Width() - 16)
        QSB.Refresh()
    end)

    local sizing = false
    panel:SetScript("OnSizeChanged", function(self, w, h)
        db.size = { math.floor(w + 0.5), math.floor(h + 0.5) }
        if sizing then return end
        sizing = true
        C_Timer.After(0.1, function() sizing = false; QSB.Refresh() end)
    end)

    panel:SetScript("OnShow", function()
        if db.hidden then
            db.hidden = nil
            UI.SelectTab("zone") -- Current Zone is where it opens
        end
        UI.ApplyTracker()
    end)
    panel:SetScript("OnHide", function(self)
        if self:IsShown() then return end -- the whole UI was hidden (Alt+Z), not us
        db.hidden = true
        UI.ApplyTracker(true)
    end)

    ApplyPosition()
    UI.ApplyScale()
    tabZone:Disable()
    if db.hidden then panel:Hide() else panel:Show() end
    UI.ApplyTracker()
end
