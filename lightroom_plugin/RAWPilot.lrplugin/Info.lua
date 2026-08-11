return {
    LrSdkVersion = 14.0,
    LrSdkMinimumVersion = 12.0,
    LrToolkitIdentifier = "com.rawpilot.lightroom.bridge",
    LrPluginName = "原光 RAWPilot Bridge",
    LrPluginInfoUrl = "https://developer.adobe.com/lightroom-classic",
    LrInitPlugin = "InitPlugin.lua",
    LrForceInitPlugin = true,
    LrExportMenuItems = {
        {
            title = "启动原光 RAWPilot Bridge",
            file = "InitPlugin.lua",
        },
    },
    VERSION = { major = 0, minor = 3, revision = 0, build = 1 },
}
