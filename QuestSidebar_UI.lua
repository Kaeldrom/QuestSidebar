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
local MIN_W, MIN_H, MAX_W, MAX_H = 250, 180, 700, 1200
local HEADER_H = 24
local SHARE_H = 22
local SEARCH_H = 20
local PARTY = "|cff66ddff"
local ORANGE = "|cffff9933"
local CHECK = "|TInterface\\RaidFrame\\ReadyCheck-Ready:13:13|t"
local SECTION_H = 18
local XPC = "|cffc8a2ff" -- XP purple, like the XP bar
local PAD = 6

local GREY = "|cff9a9a9a"
local GREEN = "|cff40c040"
local RED = "|cffff4040"
local TAG = "|cff4fd24f"

local ICON_INCOMPLETE = "Interface\\GossipFrame\\IncompleteQuestIcon"
local ICON_COMPLETE = "Interface\\GossipFrame\\ActiveQuestIcon"
local ICON_OPEN = "Interface\\Buttons\\UI-SpellbookIcon-NextPage-Up"
local ICON_ROUTE = "Interface\\Icons\\INV_Misc_Map_01"

local db
local panel, scroll, content, tabZone, tabAll, tabTurnIn, empty
local headers, quests, sections = {}, {}, {}
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

-- Grey = so far below your level it gives almost no XP (same rule as the game).
local function GreyLevel(lvl)
    if lvl <= 5 then return 0 end
    if lvl <= 39 then return lvl - 5 - math.floor(lvl / 10) end
    if lvl <= 59 then return lvl - 1 - math.floor(lvl / 5) end
    return lvl - 9
end

function UI.IsGrey(q)
    if q.complete or not q.level or q.level <= 0 then return false end
    local me = UnitLevel and UnitLevel("player")
    if not me or me <= 0 then return false end
    if GetQuestGreenRange then
        local ok, range = pcall(GetQuestGreenRange)
        if ok and type(range) == "number" then return me - q.level > range end
    end
    return q.level <= GreyLevel(me)
end

-- The right-click menu: { text, func, disabled } rows (also used by the tests)
function UI.MenuItems(q)
    local items = {}
    local function Add(text, func, disabled) items[#items + 1] = { text = text, func = func, disabled = disabled } end
    if QSB.IsRouted(q) then
        Add("|cffffd100Stop the route|r", function() QSB.RouteTo(q) end)
    else
        Add(QSB.HasRouter() and "|cffffd100Fastest route there|r" or "Point me there (quest arrow)", function() QSB.RouteTo(q) end)
    end
    Add(q.tracked and "Stop tracking" or "Track", function() QSB.ToggleTrack(q) end)
    local canShare = QSB.CanPush(q)
    Add(canShare and "Share with party" or (QSB.InGroup() and "Can't be shared" or "Share with party (not in a party)"),
        function() QSB.ShareQuest(q) end, not canShare)
    Add("Link in chat", function()
        if ChatFrame_OpenChat and ChatEdit_GetActiveWindow and not ChatEdit_GetActiveWindow() then ChatFrame_OpenChat("") end
        QSB.LinkQuest(q)
    end)
    Add("Show in quest log", function() QSB.OpenQuest(q) end)
    Add("|cffff5050Abandon quest|r", function() QSB.Abandon(q) end)
    return items
end

local function ShowMenu(owner, q)
    if not (MenuUtil and MenuUtil.CreateContextMenu) then
        QSB.ToggleTrack(q) -- old clients: right-click just tracks
        return
    end
    MenuUtil.CreateContextMenu(owner, function(_, root)
        root:CreateTitle(q.title)
        for _, it in ipairs(UI.MenuItems(q)) do
            local b = root:CreateButton(it.text, it.func)
            if it.disabled and b and b.SetEnabled then b:SetEnabled(false) end
        end
    end)
end

local function SetGradient(tex, orient, r1, g1, b1, a1, r2, g2, b2, a2)
    tex:SetColorTexture(1, 1, 1, 1)
    local ok = CreateColor and pcall(tex.SetGradient, tex, orient, CreateColor(r1, g1, b1, a1), CreateColor(r2, g2, b2, a2))
    if not ok then tex:SetColorTexture(r1, g1, b1, a1) end
end

---------------------------------------------------------------------------
-- pooled rows
---------------------------------------------------------------------------
-- Zone bar, after the world-map quest log: a dark brown bar with a thin bronze
-- frame, the zone name in large off-white text, and a flat yellow - / + on the right.
local BRONZE = { 0.58, 0.45, 0.25, 1 }

local function NewHeader()
    local h = CreateFrame("Button", nil, content)
    h:SetHeight(HEADER_H)
    h.bar = h:CreateTexture(nil, "BACKGROUND")
    h.bar:SetPoint("TOPLEFT", 1, -1)
    h.bar:SetPoint("BOTTOMRIGHT", -1, 1)
    -- warm brown at the top fading to near-black
    SetGradient(h.bar, "VERTICAL", 0.06, 0.04, 0.02, 0.96, 0.21, 0.15, 0.08, 0.96)
    h.border = {}
    for _, side in ipairs({ "TOP", "BOTTOM", "LEFT", "RIGHT" }) do
        local t = h:CreateTexture(nil, "BORDER")
        t:SetColorTexture(BRONZE[1], BRONZE[2], BRONZE[3], BRONZE[4])
        if side == "TOP" or side == "BOTTOM" then
            t:SetPoint(side .. "LEFT", 1, 0)
            t:SetPoint(side .. "RIGHT", -1, 0)
            t:SetHeight(1)
        else
            t:SetPoint("TOP" .. side, 0, -1)
            t:SetPoint("BOTTOM" .. side, 0, 1)
            t:SetWidth(1)
        end
        h.border[#h.border + 1] = t
    end
    local hl = h:CreateTexture(nil, "HIGHLIGHT")
    hl:SetPoint("TOPLEFT", 1, -1)
    hl:SetPoint("BOTTOMRIGHT", -1, 1)
    hl:SetColorTexture(1, 0.85, 0.5, 0.07)
    h.text = h:CreateFontString(nil, "ARTWORK", "GameFontHighlightLarge")
    h.text:SetPoint("LEFT", 7, 0)
    h.text:SetPoint("RIGHT", -52, 0)
    h.text:SetJustifyH("LEFT")
    h.text:SetWordWrap(false)
    h.text:SetTextColor(0.93, 0.91, 0.86)
    h.count = h:CreateFontString(nil, "ARTWORK", "GameFontDisableSmall")
    h.count:SetPoint("RIGHT", -26, 0)
    -- flat yellow dash; a second bar turns it into a plus when closed
    h.dash = h:CreateTexture(nil, "ARTWORK")
    h.dash:SetSize(11, 3)
    h.dash:SetPoint("RIGHT", -9, 0)
    h.dash:SetColorTexture(1, 0.82, 0, 1)
    h.plus = h:CreateTexture(nil, "ARTWORK")
    h.plus:SetSize(3, 11)
    h.plus:SetPoint("CENTER", h.dash, "CENTER")
    h.plus:SetColorTexture(1, 0.82, 0, 1)
    -- Turn in tab: route to every hand-in at this place, nearest first
    h.chain = CreateFrame("Button", nil, h)
    h.chain:SetSize(18, 18)
    h.chain:SetPoint("RIGHT", h.count, "LEFT", -6, 0)
    h.chain.icon = h.chain:CreateTexture(nil, "ARTWORK")
    h.chain.icon:SetAllPoints()
    h.chain.icon:SetTexture(ICON_ROUTE)
    h.chain.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    h.chain:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    h.chain.on = h.chain:CreateTexture(nil, "OVERLAY")
    h.chain.on:SetPoint("TOPLEFT", -3, 3)
    h.chain.on:SetPoint("BOTTOMRIGHT", 3, -3)
    h.chain.on:SetTexture("Interface\\Buttons\\CheckButtonHilight")
    h.chain.on:SetBlendMode("ADD")
    h.chain.on:SetVertexColor(1, 0.82, 0)
    h.chain.on:Hide()
    h.chain:SetScript("OnClick", function(self)
        local hd = self:GetParent()
        QSB.ChainTurnIns(hd.zone, hd.quests)
    end)
    h.chain:SetScript("OnEnter", function(self)
        local hd = self:GetParent()
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        if QSB.ChainZone() == hd.zone then
            GameTooltip:AddLine("Stop the turn-in route")
        else
            GameTooltip:AddLine("Route to every turn-in here")
            GameTooltip:AddLine("Takes you to each hand-in at " .. hd.zone .. ", nearest first, and moves on to the next one each time you hand a quest in."
                .. (QSB.HasRouter() and "" or " Install Shortest Path Forever for full routes; without it the quest arrow points the way."), 0.8, 0.8, 0.8, true)
        end
        GameTooltip:Show()
    end)
    h.chain:SetScript("OnLeave", function() GameTooltip:Hide() end)
    h.chain:Hide()
    h:RegisterForClicks("LeftButtonUp")
    h:SetScript("OnClick", function(self)
        if UI.tab == "turnin" then return end -- turn-in places don't fold
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
    -- soft gold wash behind quests that are ready to hand in
    r.ready = r:CreateTexture(nil, "BACKGROUND")
    r.ready:SetAllPoints()
    r.ready:SetColorTexture(1, 0.82, 0, 0.08)
    r.ready:Hide()
    -- gold edge down the left of a finished quest
    r.readyEdge = r:CreateTexture(nil, "BORDER")
    r.readyEdge:SetPoint("TOPLEFT", 0, 0)
    r.readyEdge:SetPoint("BOTTOMLEFT", 0, 0)
    r.readyEdge:SetWidth(3)
    r.readyEdge:SetColorTexture(1, 0.82, 0, 0.9)
    r.readyEdge:Hide()

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

    -- fastest route (Shortest Path Forever) / quest arrow
    r.route = CreateFrame("Button", nil, r)
    r.route:SetSize(16, 16)
    r.route:SetPoint("RIGHT", r.open, "LEFT", -2, 0)
    r.route.icon = r.route:CreateTexture(nil, "ARTWORK")
    r.route.icon:SetAllPoints()
    r.route.icon:SetTexture(ICON_ROUTE)
    r.route.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    r.route:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    -- gold glow while this quest is being routed to
    r.route.on = r.route:CreateTexture(nil, "OVERLAY")
    r.route.on:SetPoint("TOPLEFT", -3, 3)
    r.route.on:SetPoint("BOTTOMRIGHT", 3, -3)
    r.route.on:SetTexture("Interface\\Buttons\\CheckButtonHilight")
    r.route.on:SetBlendMode("ADD")
    r.route.on:SetVertexColor(1, 0.82, 0)
    r.route.on:Hide()
    r.route:SetScript("OnClick", function(self) QSB.RouteTo(self:GetParent().quest) end)
    r.route:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        if QSB.IsRouted(self:GetParent().quest) then
            GameTooltip:AddLine("Stop the route")
            GameTooltip:AddLine("Click again to stop being guided to this quest.", 0.8, 0.8, 0.8, true)
        elseif QSB.HasRouter() then
            GameTooltip:AddLine("Fastest route there")
            GameTooltip:AddLine("Plans the quickest way: walking, flight paths, boats, zeppelins and portals (Shortest Path Forever).", 0.8, 0.8, 0.8, true)
        else
            GameTooltip:AddLine("Point me there")
            GameTooltip:AddLine("Uses the game's quest arrow. Install Shortest Path Forever for full routes with flights, boats and portals.", 0.8, 0.8, 0.8, true)
        end
        GameTooltip:Show()
    end)
    r.route:SetScript("OnLeave", function() GameTooltip:Hide() end)

    r.tag = r:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    r.tag:SetPoint("RIGHT", r.route, "LEFT", -2, 0)
    r.tag:SetJustifyH("RIGHT")

    r:SetScript("OnClick", function(self, button)
        local q = self.quest
        if IsModifiedClick and IsModifiedClick("CHATLINK") then QSB.LinkQuest(q)
        elseif IsControlKeyDown and IsControlKeyDown() and button == "LeftButton" then QSB.RouteTo(q)
        elseif button == "RightButton" then ShowMenu(self, q)
        else QSB.ToggleQuest(q) end
    end)
    r:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        local q = self.quest
        GameTooltip:AddLine(q.title)
        if q.party then
            if #q.party.have > 0 then GameTooltip:AddLine("Party on this quest: " .. table.concat(q.party.have, ", "), 0.4, 0.87, 1, true) end
            if #q.party.missing > 0 then GameTooltip:AddLine("Doesn't have it: " .. table.concat(q.party.missing, ", "), 0.6, 0.6, 0.6, true) end
        end
        GameTooltip:AddLine("Click: show/hide objectives   Ctrl-click: fastest route (again to stop)   Shift-click: link in chat   Right-click: menu", 0.8, 0.8, 0.8, true)
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
    -- party marker: how many of your party have this quest
    q.party = QSB.PartyOn(q)
    if q.party then
        local n, total = #q.party.have, #q.party.have + #q.party.missing
        tag = tag .. (tag ~= "" and " " or "") .. (n > 0 and PARTY or GREY) .. n .. "/" .. total .. "|r"
    end
    r.tag:SetText(tag)
    local tagW = tag ~= "" and ((r.tag:GetStringWidth() or 0) + 4) or 0
    r.title:SetWidth(width - 30 - 64 - tagW)
    r.title:SetText(LevelColor(q.level) .. "[" .. (q.level or "?") .. "] " .. q.title .. "|r")
    r.track:SetChecked(q.tracked)
    if QSB.IsRouted(q) then r.route.on:Show(); r.route.icon:SetDesaturated(false); r.route:SetAlpha(1)
    else r.route.on:Hide(); r.route:SetAlpha(0.8) end
    -- finished: stronger wash + gold edge in Current Zone, a lighter wash in All
    if q.complete then
        r.ready:SetColorTexture(1, 0.82, 0, showDetails and 0.16 or 0.08)
        r.ready:Show()
        if showDetails then r.readyEdge:Show() else r.readyEdge:Hide() end
    else
        r.ready:Hide()
        r.readyEdge:Hide()
    end

    local h = math.max(22, (r.title:GetStringHeight() or 14) + 6)

    local folded = QSB.questFolded[q.questID]
    local objText
    if not folded then
        local parts = {}
        if q.complete then
            local xp = QSB.RewardXP(q)
            parts[#parts + 1] = GREEN .. CHECK .. " Ready to turn in|r" .. (xp and ("  " .. XPC .. "+" .. QSB.FormatXP(xp) .. "|r") or "")
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

    -- for a finished quest, say who to hand it to when the game tells us
    local details
    if showDetails and not folded then
        if q.complete then
            local place = QSB.TurnInPlace(q)
            details = QSB.TurnIn(q)
                or (place and place.npc and ("Hand in to " .. place.npc .. (place.zone and (" in " .. place.zone) or "") .. "."))
                or QSB.Details(q)
        else
            details = QSB.Details(q)
        end
    end
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
    local max = (C_QuestLog and C_QuestLog.GetMaxNumQuestsCanAccept and C_QuestLog.GetMaxNumQuestsCanAccept()) or 25
    if type(max) ~= "number" or max <= 0 then max = 25 end
    -- the count warns you before a quest giver turns you away
    local countColor = (total >= max and RED) or (total >= max - 3 and ORANGE) or GREY
    if UI.SetTitle then UI.SetTitle("Quests  " .. countColor .. total .. "/" .. max .. "|r") end
    UI.logFull = total >= max

    -- the Turn in tab shows how many are ready
    local readyCount = 0
    for _, g in ipairs(groups) do readyCount = readyCount + (g.done or 0) end
    UI.readyCount = readyCount
    if tabTurnIn then
        tabTurnIn:SetText(readyCount > 0 and ("Turn in |cff40ff40" .. readyCount .. "|r") or "Turn in")
    end

    -- hide grey quests (setting); ones ready to hand in always stay
    local hideGrey = db.settings.hideGrey
    local function Visible(list)
        if not hideGrey then return list end
        local out = {}
        for _, q in ipairs(list) do if not UI.IsGrey(q) then out[#out + 1] = q end end
        return out
    end
    if db.minimized then return end

    local function Header(g, open)
        nh = nh + 1
        local h = headers[nh] or NewHeader()
        headers[nh] = h
        h.zone = g.zone
        h:SetWidth(width)
        h:ClearAllPoints()
        h:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
        -- in All, the zone you're in reads gold; pinned zones say so
        local name = (g.zone == here and UI.tab ~= "zone") and ("|cffffd100" .. g.zone .. "|r") or g.zone
        h.text:SetText(name .. (db.pinned[g.zone] and "|cff66ddff  (pinned)|r" or ""))
        h.count:SetText((g.done > 0 and (GREEN .. g.done .. "|r/") or "") .. #g.quests)
        h.open = open
        h.quests = g.quests
        if open then h.plus:Hide() else h.plus:Show() end
        if UI.tab == "turnin" then
            h.chain:Show()
            if QSB.ChainZone() == g.zone then h.chain.on:Show() else h.chain.on:Hide() end
            h.text:SetPoint("RIGHT", -76, 0)
        else
            h.chain:Hide()
            h.text:SetPoint("RIGHT", -52, 0)
        end
        h.bar:SetAlpha(math.max(0.35, db.settings.opacity or 1))
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

    -- small section labels inside the Current Zone list
    local ns = 0
    local function Section(text, gold)
        ns = ns + 1
        local l = sections[ns]
        if not l then
            l = CreateFrame("Frame", nil, content)
            l:SetHeight(SECTION_H)
            l.text = l:CreateFontString(nil, "ARTWORK", "GameFontNormal")
            l.text:SetPoint("LEFT", 4, 0)
            l.line = l:CreateTexture(nil, "ARTWORK")
            l.line:SetHeight(1)
            l.line:SetPoint("LEFT", l.text, "RIGHT", 6, 0)
            l.line:SetPoint("RIGHT", -2, 0)
            sections[ns] = l
        end
        l:ClearAllPoints()
        l:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y - 2)
        l:SetWidth(width)
        l.text:SetText(text)
        if gold then l.line:SetColorTexture(1, 0.82, 0, 0.5) else l.line:SetColorTexture(0.6, 0.55, 0.45, 0.35) end
        l:Show()
        y = y + SECTION_H + 4
    end

    empty:Hide()
    local share = UI.shareBtn
    if share then share:Hide() end
    local search = UI.search
    if search then search:Hide() end
    if UI.tab == "zone" then
        local g = QSB.HereGroup(groups)
        if g then
            Header(g, true)
            if share then
                share:ClearAllPoints()
                share:SetPoint("TOPLEFT", content, "TOPLEFT", 0, -y)
                share:SetWidth(width)
                if QSB.Sharing() then
                    share:SetText("Sharing...")
                    share:Disable()
                else
                    share:SetText("Share all quests")
                    if QSB.InGroup() then share:Enable() else share:Disable() end
                end
                share:Show()
                y = y + SHARE_H + 4
            end
            local shown = Visible(g.quests)
            -- finished quests get their own section at the top
            local ready, rest = {}, {}
            for _, q in ipairs(shown) do
                if q.complete then ready[#ready + 1] = q else rest[#rest + 1] = q end
            end
            if #ready > 0 then
                local xpSum = 0
                for _, q in ipairs(ready) do xpSum = xpSum + (QSB.RewardXP(q) or 0) end
                Section(CHECK .. " |cffffd100Ready to turn in|r  " .. GREEN .. #ready .. "|r"
                    .. (xpSum > 0 and ("   " .. XPC .. QSB.FormatXP(xpSum) .. "|r") or ""), true)
                for _, q in ipairs(ready) do Quest(q, true) end
                if #rest > 0 then Section("|cffd8d0bcIn progress|r  " .. GREY .. #rest .. "|r", false) end
            end
            for _, q in ipairs(rest) do Quest(q, true) end
            if #shown < #g.quests then
                empty:ClearAllPoints()
                empty:SetPoint("TOPLEFT", content, "TOPLEFT", 8, -y - 4)
                empty:SetText(GREY .. (#g.quests - #shown) .. " grey quest" .. (#g.quests - #shown == 1 and "" or "s") .. " hidden.|r")
                empty:Show()
                y = y + 22
            end
        else
            empty:ClearAllPoints()
            empty:SetPoint("TOPLEFT", 8, -12)
            empty:SetText(GREY .. "No quests for " .. (here or "this zone") .. ".|r\n\n" .. "Open the |cffffd100All|r tab to see your other quests.")
            empty:Show()
        end
    elseif UI.tab == "turnin" then
        -- every finished quest, grouped by where it's handed in (not where you got it);
        -- the place you're in first, the rest A-Z, quests nearest first
        local byPlace, list = {}, {}
        for _, g in ipairs(groups) do
            for _, q in ipairs(g.quests) do
                if q.complete then
                    local place = QSB.TurnInPlace(q)
                    local zone = (place and place.zone) or g.zone
                    local entry = byPlace[zone]
                    if not entry then
                        entry = { zone = zone, quests = {}, done = 0 }
                        byPlace[zone] = entry
                        list[#list + 1] = entry
                    end
                    entry.quests[#entry.quests + 1] = q
                end
            end
        end
        table.sort(list, function(a, b)
            if (a.zone == here) ~= (b.zone == here) then return a.zone == here end
            return QSB.SortKey(a.zone) < QSB.SortKey(b.zone)
        end)
        for _, e in ipairs(list) do e.quests = QSB.NearestOrder(e.quests) end
        -- what handing everything in is worth
        local xpSum = 0
        for _, g in ipairs(list) do
            for _, q in ipairs(g.quests) do xpSum = xpSum + (QSB.RewardXP(q) or 0) end
        end
        UI.turnInXP = xpSum
        if xpSum > 0 then
            local share = QSB.LevelShare(xpSum)
            Section(XPC .. "Total " .. QSB.FormatXP(xpSum) .. "|r"
                .. (share and (GREY .. "  (" .. share .. "% of a level)|r") or ""), false)
        end
        for _, g in ipairs(list) do
            Header(g, true)
            for _, q in ipairs(g.quests) do Quest(q, true) end
        end
        if #list == 0 then
            empty:ClearAllPoints()
            empty:SetPoint("TOPLEFT", 8, -12)
            empty:SetText(GREY .. "Nothing to turn in yet.|r\n\n" .. "Finished quests show up here, wherever they are.")
            empty:Show()
        end
    else
        if search then
            search:ClearAllPoints()
            search:SetPoint("TOPLEFT", content, "TOPLEFT", 6, -y - 2)
            search:SetWidth(width - 10)
            search:Show()
            y = y + SEARCH_H + 6
        end
        local filter = UI.filter
        local matched = 0
        for _, g in ipairs(groups) do
            local list = Visible(g.quests)
            if filter then
                -- a zone name match shows the whole zone; otherwise only matching quests
                if not g.zone:lower():find(filter, 1, true) then
                    local hits = {}
                    for _, q in ipairs(list) do
                        local hay = q.title:lower()
                        for _, o in ipairs(q.objectives or {}) do hay = hay .. "\n" .. o.text:lower() end
                        if hay:find(filter, 1, true) then hits[#hits + 1] = q end
                    end
                    list = hits
                end
                if #list > 0 then
                    matched = matched + #list
                    Header(g, true)
                    for _, q in ipairs(list) do Quest(q, false) end
                end
            elseif #list > 0 then
                local open = QSB.IsOpen(g.zone)
                Header(g, open)
                if open then
                    for _, q in ipairs(list) do Quest(q, false) end
                end
            end
        end
        empty:ClearAllPoints()
        empty:SetPoint("TOPLEFT", content, "TOPLEFT", 8, -y - 8)
        if total == 0 then
            empty:SetText(GREY .. "Your quest log is empty.|r")
            empty:Show()
        elseif filter and matched == 0 then
            empty:SetText(GREY .. "No quests match \"" .. filter .. "\".|r")
            empty:Show()
        end
    end
    for i = nh + 1, #headers do headers[i]:Hide() end
    for i = nq + 1, #quests do quests[i]:Hide() end
    for i = ns + 1, #sections do sections[i]:Hide() end

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
    tabZone:Enable(); tabAll:Enable(); tabTurnIn:Enable()
    if tab == "zone" then tabZone:Disable() elseif tab == "turnin" then tabTurnIn:Disable() else tabAll:Disable() end
    QSB.Refresh()
end

-- tests
function UI.Headers() return headers end
function UI.Quests() return quests end
function UI.Sections() return sections end
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
    db.point, db.size, db.minimized = nil, nil, nil
    panel:SetSize(DEFAULT_W, DEFAULT_H)
    ApplyPosition()
    if UI.minBtn then UI.ApplyMinimized() end
end

function UI.ApplyScale()
    if panel then panel:SetScale(db.settings.scale or 1) end
end

-- Opacity fades the window's background and zone bars; text, icons and buttons stay solid.
local function FadeTextures(frame, a)
    if not frame or not frame.GetRegions then return end
    for _, r in ipairs({ frame:GetRegions() }) do
        if r.GetObjectType and r:GetObjectType() == "Texture" then r:SetAlpha(a) end
    end
end

function UI.ApplyOpacity()
    if not panel then return end
    local a = db.settings.opacity or 1
    FadeTextures(panel, a)
    if type(panel.Inset) == "table" then FadeTextures(panel.Inset, a) end
    if UI.bar then FadeTextures(UI.bar, math.max(0.35, a)) end
    for _, h in ipairs(headers) do h.bar:SetAlpha(math.max(0.35, a)) end
end

---------------------------------------------------------------------------
-- Settings: a small panel that opens beside the window from the cog
---------------------------------------------------------------------------
local settings

local function Slider(parent, label, minV, maxV, step, get, set, fmt)
    local holder = CreateFrame("Frame", nil, parent)
    holder:SetSize(196, 36)
    holder.label = holder:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    holder.label:SetPoint("TOPLEFT", 0, 0)
    local s = CreateFrame("Slider", nil, holder)
    s:SetPoint("TOPLEFT", 2, -16)
    s:SetSize(190, 12)
    s:SetOrientation("HORIZONTAL")
    s:SetMinMaxValues(minV, maxV)
    s:SetValueStep(step)
    if s.SetObeyStepOnDrag then s:SetObeyStepOnDrag(true) end
    s:EnableMouseWheel(true)
    local track = s:CreateTexture(nil, "BACKGROUND")
    track:SetPoint("LEFT")
    track:SetPoint("RIGHT")
    track:SetHeight(4)
    track:SetColorTexture(0.25, 0.2, 0.12, 1)
    local thumb = s:CreateTexture(nil, "OVERLAY")
    thumb:SetSize(10, 14)
    thumb:SetColorTexture(1, 0.82, 0, 1)
    s:SetThumbTexture(thumb)
    local function Show(v) holder.label:SetText(label .. ":  |cffffd100" .. fmt(v) .. "|r") end
    s:SetScript("OnValueChanged", function(_, v)
        v = math.floor(v / step + 0.5) * step
        Show(v)
        set(v)
    end)
    s:SetScript("OnMouseWheel", function(self, d)
        local lo, hi = self:GetMinMaxValues()
        self:SetValue(math.max(lo, math.min(hi, (self:GetValue() or lo) + d * step)))
    end)
    holder.slider = s
    holder.Sync = function()
        local v = get()
        s:SetValue(v)
        Show(v)
    end
    return holder
end

local function Check(parent, label, key, after)
    local c = CreateFrame("CheckButton", nil, parent, "UICheckButtonTemplate")
    c:SetSize(22, 22)
    c.label = c:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    c.label:SetPoint("LEFT", c, "RIGHT", 2, 0)
    c.label:SetText(label)
    c:SetScript("OnClick", function(self)
        db.settings[key] = self:GetChecked() and true or false
        if after then after() end
        QSB.Refresh()
    end)
    c.Sync = function() c:SetChecked(db.settings[key]) end
    return c
end

local function BuildSettings()
    settings = CreateFrame("Frame", "QuestSidebarSettings", panel, "BackdropTemplate")
    settings:SetSize(236, 324)
    settings:SetPoint("TOPRIGHT", panel, "TOPLEFT", -2, 0)
    settings:SetFrameStrata("HIGH")
    settings:EnableMouse(true)
    if settings.SetBackdrop then
        settings:SetBackdrop({ bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
            edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", tile = true, tileSize = 16, edgeSize = 14,
            insets = { left = 4, right = 4, top = 4, bottom = 4 } })
        settings:SetBackdropColor(0.06, 0.04, 0.02, 0.95)
        settings:SetBackdropBorderColor(BRONZE[1], BRONZE[2], BRONZE[3], 1)
    end
    local t = settings:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    t:SetPoint("TOPLEFT", 12, -10)
    t:SetText("Quest Sidebar settings")

    -- X in the corner closes the settings (no need to click the cog again)
    local okX, close = pcall(CreateFrame, "Button", nil, settings, "UIPanelCloseButton")
    if not okX or not close then
        close = CreateFrame("Button", nil, settings)
        close:SetNormalTexture("Interface\\Buttons\\UI-Panel-MinimizeButton-Up")
        close:SetPushedTexture("Interface\\Buttons\\UI-Panel-MinimizeButton-Down")
        close:SetHighlightTexture("Interface\\Buttons\\UI-Panel-MinimizeButton-Highlight", "ADD")
    end
    close:SetSize(24, 24)
    close:SetPoint("TOPRIGHT", -2, -2)
    close:SetScript("OnClick", function() settings:Hide() end)
    settings.close = close

    local items = {}
    items[#items + 1] = Slider(settings, "Opacity", 0.1, 1, 0.05,
        function() return db.settings.opacity or 1 end,
        function(v) db.settings.opacity = v; UI.ApplyOpacity() end,
        function(v) return math.floor(v * 100 + 0.5) .. "%" end)
    items[#items + 1] = Slider(settings, "Size", 0.6, 1.5, 0.05,
        function() return db.settings.scale or 1 end,
        function(v) db.settings.scale = v; UI.ApplyScale() end,
        function(v) return math.floor(v * 100 + 0.5) .. "%" end)
    items[#items + 1] = Check(settings, "Open the zone I'm in", "autoZone")
    items[#items + 1] = Check(settings, "Show objectives", "showObjectives")
    items[#items + 1] = Check(settings, "Hide Blizzard's tracker", "hideTracker", function() UI.ApplyTracker(true) end)
    items[#items + 1] = Check(settings, "Lock position", "locked")
    items[#items + 1] = Check(settings, "Minimap button", "minimap", function() UI.ApplyMinimap() end)
    items[#items + 1] = Check(settings, "Auto-share new quests with party", "autoShare")
    items[#items + 1] = Check(settings, "Hide grey (low level) quests", "hideGrey")

    local y = -32
    for _, it in ipairs(items) do
        it:SetPoint("TOPLEFT", it.slider and 12 or 8, y)
        y = y - (it.slider and 40 or 24)
    end
    local reset = CreateFrame("Button", nil, settings, "UIPanelButtonTemplate")
    reset:SetSize(212, 20)
    reset:SetPoint("TOPLEFT", 12, y - 6)
    reset:SetText("Reset size & position")
    reset:SetScript("OnClick", function() UI.ResetPosition(); QSB.Refresh() end)
    settings:SetHeight(-y + 40)

    settings.items = items
    settings:SetScript("OnShow", function() for _, it in ipairs(items) do it.Sync() end end)
    settings:Hide()
    tinsert(UISpecialFrames, "QuestSidebarSettings")
end

function UI.ToggleSettings()
    if not settings then BuildSettings() end
    if settings:IsShown() then settings:Hide() else settings:Show() end
end
function UI.Settings() return settings end -- tests

function UI.IsShown() return panel ~= nil and panel:IsShown() and true or false end

function UI.ToggleShown()
    if panel:IsShown() then panel:Hide() else panel:Show() end
end

---------------------------------------------------------------------------
-- Minimize: shrink to the title bar and back
---------------------------------------------------------------------------
local SHRUNK_H = 30

local function HasAtlas(name)
    return C_Texture and C_Texture.GetAtlasInfo and C_Texture.GetAtlasInfo(name) ~= nil
end

local function StyleMinButton(b, minimized)
    -- modern clients: the red square buttons; older: the world map's smaller/bigger buttons
    local up = minimized and "RedButton-Expand" or "RedButton-Condense"
    if HasAtlas(up) and b.SetNormalAtlas then
        b:SetNormalAtlas(up)
        b:SetPushedAtlas(up .. "-Pressed")
        if HasAtlas("RedButton-Highlight") then b:SetHighlightAtlas("RedButton-Highlight", "ADD") end
    else
        local base = minimized and "Interface\\Buttons\\UI-Panel-BiggerButton" or "Interface\\Buttons\\UI-Panel-SmallerButton"
        b:SetNormalTexture(base .. "-Up")
        b:SetPushedTexture(base .. "-Down")
        b:SetHighlightTexture("Interface\\Buttons\\UI-Panel-MinimizeButton-Highlight", "ADD")
    end
end

function UI.ApplyMinimized()
    if not panel then return end
    local m = db.minimized and true or false
    for _, f in ipairs({ tabZone, tabAll, tabTurnIn, scroll, UI.grip }) do
        if f then if m then f:Hide() else f:Show() end end
    end
    if type(panel.Inset) == "table" and panel.Inset.Hide then
        if m then panel.Inset:Hide() else panel.Inset:Show() end
    end
    if m and UI.bar then UI.bar:Hide() end
    local size = db.size or { DEFAULT_W, DEFAULT_H }
    panel:SetHeight(m and SHRUNK_H or size[2])
    if UI.minBtn then StyleMinButton(UI.minBtn, m) end
    if not m then QSB.Refresh() end
end

function UI.ToggleMinimized()
    db.minimized = not db.minimized or nil
    UI.ApplyMinimized()
end

---------------------------------------------------------------------------
-- Minimap button: left-click shows/hides, right-click settings, drag to move
---------------------------------------------------------------------------
local mapBtn

local function PlaceMinimap()
    local angle = math.rad(db.minimapAngle or 200)
    local radius = (Minimap:GetWidth() / 2) + 5
    mapBtn:ClearAllPoints()
    mapBtn:SetPoint("CENTER", Minimap, "CENTER", math.cos(angle) * radius, math.sin(angle) * radius)
end

function UI.BuildMinimap()
    if mapBtn or not Minimap then return end
    local b = CreateFrame("Button", "QuestSidebarMinimapButton", Minimap)
    b:SetSize(31, 31)
    b:SetFrameStrata("MEDIUM")
    b:SetFrameLevel(8)
    b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
    b:RegisterForDrag("LeftButton")
    b:SetHighlightTexture("Interface\\Minimap\\UI-Minimap-ZoomButton-Highlight")
    local bg = b:CreateTexture(nil, "BACKGROUND")
    bg:SetSize(20, 20)
    bg:SetPoint("TOPLEFT", 7, -5)
    bg:SetTexture("Interface\\Minimap\\UI-Minimap-Background")
    local icon = b:CreateTexture(nil, "ARTWORK")
    icon:SetSize(18, 18)
    icon:SetPoint("TOPLEFT", 7, -6)
    icon:SetTexture("Interface\\Icons\\INV_Misc_Note_01")
    icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    b.icon = icon
    local border = b:CreateTexture(nil, "OVERLAY")
    border:SetSize(53, 53)
    border:SetPoint("TOPLEFT")
    border:SetTexture("Interface\\Minimap\\MiniMap-TrackingBorder")

    b:SetScript("OnMouseDown", function() icon:SetPoint("TOPLEFT", 8, -7) end)
    b:SetScript("OnMouseUp", function() icon:SetPoint("TOPLEFT", 7, -6) end)
    b:SetScript("OnClick", function(_, button)
        if button == "RightButton" then
            if not panel:IsShown() then panel:Show() end
            UI.ToggleSettings()
        else
            UI.ToggleShown()
        end
    end)
    b:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine("Quest Sidebar", 0.4, 0.87, 1)
        GameTooltip:AddLine("Click: show or hide", 1, 1, 1)
        GameTooltip:AddLine("Right-click: settings", 1, 1, 1)
        GameTooltip:AddLine("Drag: move this button", 0.6, 0.6, 0.6)
        GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:SetScript("OnDragStart", function(self)
        GameTooltip:Hide()
        self:SetScript("OnUpdate", function()
            local mx, my = Minimap:GetCenter()
            local cx, cy = GetCursorPosition()
            local scale = Minimap:GetEffectiveScale()
            db.minimapAngle = math.deg(math.atan2(cy / scale - my, cx / scale - mx))
            PlaceMinimap()
        end)
    end)
    b:SetScript("OnDragStop", function(self) self:SetScript("OnUpdate", nil) end)
    mapBtn = b
    UI.mapBtn = b
    PlaceMinimap()
    UI.ApplyMinimap()
end

function UI.ApplyMinimap()
    if not mapBtn then return end
    if db.settings.minimap then mapBtn:Show() else mapBtn:Hide() end
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
    if size[1] < MIN_W then size[1] = MIN_W end
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
    tabZone:SetSize(100, 22)
    tabZone:SetPoint("TOPLEFT", 10, -28)
    tabZone:SetText("Current Zone")
    tabZone:SetScript("OnClick", function() UI.SelectTab("zone") end)
    tabAll = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    tabAll:SetSize(44, 22)
    tabAll:SetPoint("LEFT", tabZone, "RIGHT", 3, 0)
    tabAll:SetText("All")
    tabAll:SetScript("OnClick", function() UI.SelectTab("all") end)
    tabTurnIn = CreateFrame("Button", nil, panel, "UIPanelButtonTemplate")
    tabTurnIn:SetSize(84, 22)
    tabTurnIn:SetPoint("LEFT", tabAll, "RIGHT", 3, 0)
    tabTurnIn:SetText("Turn in")
    tabTurnIn:SetScript("OnClick", function() UI.SelectTab("turnin") end)
    tabTurnIn:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_TOP")
        GameTooltip:AddLine("Turn in")
        GameTooltip:AddLine("Every finished quest, wherever it is, with who to hand it to.", 0.8, 0.8, 0.8, true)
        GameTooltip:Show()
    end)
    tabTurnIn:SetScript("OnLeave", function() GameTooltip:Hide() end)
    UI.tabTurnIn = tabTurnIn

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

    -- Current Zone: share every quest here with your party
    local share = CreateFrame("Button", nil, content, "UIPanelButtonTemplate")
    share:SetHeight(SHARE_H)
    share:SetText("Share all quests")
    share:SetMotionScriptsWhileDisabled(true)
    share:SetScript("OnClick", function() QSB.ShareZone() end)
    share:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine("Share all quests")
        if QSB.InGroup() then
            GameTooltip:AddLine("Shares every quest for this zone with your party, one after another.", 0.8, 0.8, 0.8, true)
        else
            GameTooltip:AddLine("Join a party to share your quests.", 1, 0.4, 0.4, true)
        end
        GameTooltip:Show()
    end)
    share:SetScript("OnLeave", function() GameTooltip:Hide() end)
    share:Hide()
    UI.shareBtn = share

    -- All tab: search box (title, objectives or zone)
    local okS, box = pcall(CreateFrame, "EditBox", "QuestSidebarSearch", content, "SearchBoxTemplate")
    if not okS or not box then box = CreateFrame("EditBox", "QuestSidebarSearch", content, "InputBoxTemplate") end
    box:SetHeight(SEARCH_H)
    box:SetAutoFocus(false)
    if type(box.Instructions) == "table" and box.Instructions.SetText then box.Instructions:SetText("Search quests") end
    box:HookScript("OnTextChanged", function(self)
        local t = (self:GetText() or ""):lower():gsub("^%s+", ""):gsub("%s+$", "")
        local f = t ~= "" and t or nil
        if f ~= UI.filter then
            UI.filter = f
            scrollY = 0
            QSB.QueueRefresh()
        end
    end)
    box:HookScript("OnEscapePressed", function(self) self:ClearFocus() end)
    box:HookScript("OnEnterPressed", function(self) self:ClearFocus() end)
    box:Hide()
    UI.search = box

    empty = content:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
    empty:SetPoint("TOPLEFT", 8, -12)
    empty:SetWidth(Width() - 16)
    empty:SetJustifyH("LEFT")

    -- resize grip
    local grip = CreateFrame("Button", nil, panel)
    UI.grip = grip
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
        if db.minimized then return end -- the shrunk height isn't the size you chose
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

    -- discreet cog in the title bar for the settings
    local cog = CreateFrame("Button", nil, panel)
    cog:SetSize(15, 15)
    cog:SetPoint("TOPRIGHT", -28, -4)
    cog.icon = cog:CreateTexture(nil, "ARTWORK")
    cog.icon:SetAllPoints()
    -- our own white cog (Media\Cog.tga), tinted to match the title text
    cog.icon:SetTexture("Interface\\AddOns\\QuestSidebar\\Media\\Cog")
    cog.icon:SetVertexColor(0.85, 0.82, 0.74)
    cog:SetAlpha(0.6)
    cog:SetScript("OnEnter", function(self)
        self:SetAlpha(1)
        self.icon:SetVertexColor(1, 0.82, 0)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine("Settings")
        GameTooltip:Show()
    end)
    cog:SetScript("OnLeave", function(self)
        self:SetAlpha(0.6)
        self.icon:SetVertexColor(0.85, 0.82, 0.74)
        GameTooltip:Hide()
    end)
    cog:SetScript("OnClick", function() UI.ToggleSettings() end)
    UI.cog = cog

    -- minimize, where the close X used to be
    local closeBtn = (type(panel.CloseButton) == "table" and panel.CloseButton) or _G["QuestSidebarFrameCloseButton"]
    local minBtn = CreateFrame("Button", nil, panel)
    minBtn:SetSize(24, 24)
    if closeBtn and closeBtn.Hide then
        minBtn:SetPoint("CENTER", closeBtn, "CENTER")
        closeBtn:Hide()
        closeBtn:SetScript("OnShow", closeBtn.Hide)
    else
        minBtn:SetPoint("TOPRIGHT", 2, 1)
    end
    minBtn:SetScript("OnClick", function() UI.ToggleMinimized() end)
    minBtn:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_LEFT")
        GameTooltip:AddLine(db.minimized and "Restore" or "Minimize")
        GameTooltip:Show()
    end)
    minBtn:SetScript("OnLeave", function() GameTooltip:Hide() end)
    UI.minBtn = minBtn

    UI.BuildMinimap()
    UI.ApplyMinimized()

    UI.ApplyOpacity()
    tabZone:Disable()
    if db.hidden then panel:Hide() else panel:Show() end
    UI.ApplyTracker()
end
