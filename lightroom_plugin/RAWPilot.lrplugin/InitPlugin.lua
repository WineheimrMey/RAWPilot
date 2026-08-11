local LrApplication = import "LrApplication"
local LrApplicationView = import "LrApplicationView"
local LrDevelopController = import "LrDevelopController"
local LrExportSession = import "LrExportSession"
local LrFileUtils = import "LrFileUtils"
local LrLogger = import "LrLogger"
local LrPathUtils = import "LrPathUtils"
local LrTasks = import "LrTasks"

local sdkLogger = LrLogger("RAWPilotBridge")
local BRIDGE_VERSION = "0.5"
sdkLogger:enable("logfile")
sdkLogger:trace("InitPlugin.lua entered")

if _G.RAWPilotBridgeStarted then
    sdkLogger:trace("Bridge already running; duplicate start ignored")
    return
end

local function readText(path)
    local file = io.open(path, "r")
    if not file then return nil end
    local value = file:read("*a")
    file:close()
    if value then
        value = string.gsub(value, "^%s+", "")
        value = string.gsub(value, "%s+$", "")
    end
    return value
end

local configuredPath = LrPathUtils.child(_PLUGIN.path, "queue_path.txt")
local queueDir = readText(configuredPath)
if not queueDir or queueDir == "" then
    local home = LrPathUtils.getStandardFilePath("home")
    queueDir = LrPathUtils.child(home, "AppData")
    queueDir = LrPathUtils.child(queueDir, "Roaming")
    queueDir = LrPathUtils.child(queueDir, "RAWPilot")
    queueDir = LrPathUtils.child(queueDir, "lightroom_queue")
end
LrFileUtils.createAllDirectories(queueDir)

local logPath = LrPathUtils.child(queueDir, "bridge.log")
local readyPath = LrPathUtils.child(queueDir, "bridge.ready")

local function appendLog(message)
    local file = io.open(logPath, "a")
    if file then
        file:write(os.date("%Y-%m-%d %H:%M:%S") .. "  " .. tostring(message) .. "\n")
        file:close()
    end
end

local function writeStatus(path, state, detail)
    local file = io.open(path, "w")
    if file then
        file:write(state .. "|" .. tostring(detail or ""))
        file:close()
    end
end

local function heartbeat()
    writeStatus(readyPath, "ready", BRIDGE_VERSION .. "|" .. os.time())
end

local function readJob(path)
    local file = assert(io.open(path, "r"))
    local source = file:read("*l")
    local output = file:read("*l")
    local stem = file:read("*l")
    local settings = { ProcessVersion = "15.4" }
    local masks = {}
    local stateKey = nil
    for line in file:lines() do
        local parsedState = string.match(line, "^STATE|(.+)$")
        local target, controls = string.match(line, "^MASK|([^|]+)|(.+)$")
        if parsedState then
            stateKey = parsedState
        elseif target and controls then
            local mask = { target = target, settings = {} }
            for item in string.gmatch(controls, "[^;]+") do
                local key, value = string.match(item, "^([^:]+):(.*)$")
                if key and value then mask.settings[key] = tonumber(value) end
            end
            table.insert(masks, mask)
        else
            local key, value = string.match(line, "^([^=]+)=(.*)$")
            if key and value then
                local numeric = tonumber(value)
                settings[key] = numeric ~= nil and numeric or value
            end
        end
    end
    file:close()
    return source, output, stem, settings, masks, stateKey
end

local function applyLocalAdjustments(catalog, photo, masks, stateKey)
    if #masks == 0 then return end

    catalog:setSelectedPhotos(photo, {})
    LrApplicationView.switchToModule("develop")
    LrTasks.yield()
    LrTasks.sleep(1)
    if LrDevelopController.getSelectedTool() ~= "masking" then
        LrDevelopController.selectTool("masking")
    end

    local stateDir = LrPathUtils.child(queueDir, "mask_state")
    LrFileUtils.createAllDirectories(stateDir)
    local statePath = stateKey and LrPathUtils.child(stateDir, stateKey .. ".txt") or nil
    if statePath and LrFileUtils.exists(statePath) then
        local stateFile = io.open(statePath, "r")
        if stateFile then
            for oldId in stateFile:lines() do
                if oldId and oldId ~= "" then
                    local ok, message = LrTasks.pcall(function()
                        LrDevelopController.deleteMask(oldId, oldId)
                    end)
                    appendLog(
                        "previous RAWPilot mask delete: " .. oldId ..
                        "; ok=" .. tostring(ok) ..
                        (ok and "" or "; " .. tostring(message))
                    )
                end
            end
            stateFile:close()
        end
    end

    local createdMaskIds = {}
    for _, mask in ipairs(masks) do
        do
            local aiTarget = mask.target
            if aiTarget == "people" then
                aiTarget = "subject"
                appendLog("people mask mapped to subject selection for non-interactive execution")
            end
            local beforeMasks = LrDevelopController.getAllMasks() or {}
            local beforeCount = #beforeMasks
            local beforeSelected = LrDevelopController.getSelectedMask()
            LrDevelopController.createNewMask("aiSelection", aiTarget)
            local deadline = os.time() + 30
            local maskId = LrDevelopController.getSelectedMask()
            local allMasks = LrDevelopController.getAllMasks() or {}
            while os.time() < deadline and #allMasks <= beforeCount and (not maskId or maskId == beforeSelected) do
                LrTasks.sleep(0.5)
                maskId = LrDevelopController.getSelectedMask()
                allMasks = LrDevelopController.getAllMasks() or {}
            end

            if #allMasks <= beforeCount and (not maskId or maskId == beforeSelected) then
                appendLog("AI mask failed or timed out: " .. aiTarget)
            else
                appendLog(
                    "AI mask ready: " .. mask.target ..
                    "; id=" .. tostring(maskId) ..
                    "; count=" .. tostring(#allMasks)
                )
                if maskId then LrDevelopController.selectMask(maskId) end
                if maskId then table.insert(createdMaskIds, maskId) end
                for parameter, value in pairs(mask.settings) do
                    LrDevelopController.setValue(parameter, value)
                    LrTasks.yield()
                    local actual = LrDevelopController.getValue(parameter)
                    appendLog("  " .. parameter .. "=" .. tostring(value) .. "; actual=" .. tostring(actual))
                end
                appendLog("AI mask applied: " .. aiTarget)
            end
        end
        LrTasks.sleep(1)
    end
    if statePath then
        local stateFile = io.open(statePath, "w")
        if stateFile then
            for _, maskId in ipairs(createdMaskIds) do
                stateFile:write(maskId .. "\n")
            end
            stateFile:close()
        end
    end
    appendLog("local adjustments applied: " .. tostring(#masks))
end

local function processJob(jobPath)
    local base = LrPathUtils.removeExtension(jobPath)
    local statusPath = base .. ".status"
    local source, output, stem, settings, masks, stateKey = readJob(jobPath)
    appendLog("received " .. source)
    local catalog = LrApplication.activeCatalog()
    local photo = catalog:findPhotoByPath(source)

    if not photo then
        catalog:withWriteAccessDo("RAWPilot 导入底片", function()
            photo = catalog:addPhoto(source)
        end, { timeout = 30 })
        appendLog("imported " .. source)
    else
        appendLog("found in catalog " .. source)
    end
    if not photo then error("无法把底片加入 Lightroom 目录：" .. source) end

    catalog:withWriteAccessDo("RAWPilot AI 调色", function()
        photo:applyDevelopSettings(settings, "RAWPilot AI 调色")
    end, { timeout = 30 })
    appendLog("develop settings applied")
    applyLocalAdjustments(catalog, photo, masks, stateKey)

    LrFileUtils.createAllDirectories(output)
    local exportSettings = {
        LR_exportServiceProvider = "com.adobe.ag.export.file",
        LR_export_destinationType = "specificFolder",
        LR_export_destinationPathPrefix = output,
        LR_export_useSubfolder = false,
        LR_collisionHandling = "overwrite",
        LR_format = "JPEG",
        LR_jpeg_quality = 0.9,
        LR_export_colorSpace = "sRGB",
        LR_extensionCase = "lowercase",
        LR_export_postProcessing = "doNothing",
        LR_outputSharpeningOn = true,
        LR_outputSharpeningLevel = 2,
        LR_outputSharpeningMedia = "screen",
        LR_size_doConstrain = false,
        LR_renamingTokensOn = false,
        LR_useWatermark = false,
        LR_removeLocationMetadata = false,
    }
    local session = LrExportSession {
        photosToExport = { photo },
        exportSettings = exportSettings,
    }
    session:doExportOnCurrentTask()
    local rendered = LrPathUtils.child(output, stem .. ".jpg")
    if not LrFileUtils.exists(rendered) then
        error("Lightroom 未生成预期 JPEG：" .. rendered)
    end
    appendLog("exported " .. rendered)
    writeStatus(statusPath, "done", rendered)
end

_G.RAWPilotBridgeStarted = true
appendLog("Bridge " .. BRIDGE_VERSION .. " initialized; queue=" .. queueDir)
sdkLogger:trace("Bridge initialized; queue=" .. queueDir)
heartbeat()
LrTasks.startAsyncTask(function()
    while true do
        local ok, message = LrTasks.pcall(function()
            heartbeat()
            for path in LrFileUtils.directoryEntries(queueDir) do
                if string.lower(LrPathUtils.extension(path) or "") == "job" then
                    local jobOk, jobMessage = LrTasks.pcall(processJob, path)
                    if not jobOk then
                        appendLog("ERROR " .. tostring(jobMessage))
                        writeStatus(
                            LrPathUtils.removeExtension(path) .. ".status",
                            "error",
                            jobMessage
                        )
                    end
                    LrFileUtils.delete(path)
                end
            end
        end)
        if not ok then appendLog("LOOP ERROR " .. tostring(message)) end
        LrTasks.sleep(1)
    end
end)
