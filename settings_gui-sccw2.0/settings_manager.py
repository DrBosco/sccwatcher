from PyQt4 import QtCore
from collections import OrderedDict as OD

#Get ready for tons of lame code

#And here we set up our UI elements database. This will simplify the way we store and retrieve settings.
#I thought about simplifying this and just going by the element's type. This cut the dictionary down to only 7 entries but I found
#that writing back to the elements became significantly more difficult when I didn't have the exact name of the element. So either
#way I was going to end up listing out the elements name by name, I figured Id just do it in one place rather than multiple (possibly)
uiElements = {}
#Format for the database is this:
#uiElements[element_type] = [read_access_method, write_acecss_method]
#The access methods are just whatever function is required to retrieve/modify the current value of that element.

#This dictionary defines the translation between UI Elements and ini options. Without this, things would get much more complicated.
#The structure is the same as all the other elements databases. The main keys are the tab names, and each subkey of the tab is the UI element. Each value is the Group and the INI option name in a list.
elementsToOptions = OD()
elementsToOptions["downloadUploadTab"] = OD()
elementsToOptions["watchlistTab"] = OD()
elementsToOptions["mainTab"] = OD()
elementsToOptions["emailSettingsTab"] = OD()
elementsToOptions["globalAvoidlistTab"] = OD()

elementsToOptions["mainTab"]["ggEnableVerboseCheck"] = ["GlobalSettings", "verbose"]
elementsToOptions["mainTab"]["ggEnableDebugCheck"] = ["GlobalSettings", "DEBUG"]
elementsToOptions["mainTab"]["ggLogpathTextbox"] = ["GlobalSettings", "logpath"]
elementsToOptions["mainTab"]["ggSavepathTextbox"] = ["GlobalSettings", "savepath"]
elementsToOptions["mainTab"]["ggMasterAutodlCheck"] = ["GlobalSettings", "service"]
elementsToOptions["mainTab"]["ggNetworkDelaySpinbox"] = ["GlobalSettings", "startdelay"]
elementsToOptions["mainTab"]["ggBeepCheckbox"] = ["GlobalSettings", "printalert"]
elementsToOptions["mainTab"]["ggEnableLoggingCheck"] = ["GlobalSettings", "logenabled"]
elementsToOptions["mainTab"]["ggVerboseTabTextbox"] = ["GlobalSettings", "verbose_tab"]
elementsToOptions["mainTab"]["ggPasskeyTextbox"] = ["GlobalSettings", "passkey"]

elementsToOptions["downloadUploadTab"]["globalDupecheckCheck"] = ["GlobalSettings", "dupecheck"]
elementsToOptions["downloadUploadTab"]["globalSSLDownloadCheck"] = ["GlobalSettings", "download_ssl"]
elementsToOptions["downloadUploadTab"]["utwuiMasterEnableTriCheck"] = ["GlobalSettings", "utorrent_mode"]
elementsToOptions["downloadUploadTab"]["utwuiUsernameTextbox"] = ["GlobalSettings", "utorrent_username"]
elementsToOptions["downloadUploadTab"]["utwuiPasswordTextbox"] = ["GlobalSettings", "utorrent_password"]
elementsToOptions["downloadUploadTab"]["utwuiHostnameTextbox"] = ["GlobalSettings", "utorrent_hostname"]
elementsToOptions["downloadUploadTab"]["utwuiPortTextbox"] = ["GlobalSettings", "utorrent_port"]
#These Size Limit UI elements need some special treatment. Both when loading and saving.
#These hold a function in index 3 that will return data instead of getting it straight from the element's access function.
#This function takes one argument, the element name that holds the suffix data.
elementsToOptions["downloadUploadTab"]["globalSizeLimitLowerTextbox"] = ["GlobalSettings", "sizelimit_lower", "SLcombiner('globalSizeLimitLowerSuffixSelector')"]
elementsToOptions["downloadUploadTab"]["globalSizeLimitUpperTextbox"] = ["GlobalSettings", "sizelimit_upper", "SLcombiner('globalSizeLimitUpperSuffixSelector')"]
elementsToOptions["downloadUploadTab"]["ftpHostnameTextbox"] = ["GlobalSettings", "ftpServerHostname"]
elementsToOptions["downloadUploadTab"]["ftpPortTextbox"] = ["GlobalSettings", "ftpPort"]
elementsToOptions["downloadUploadTab"]["ftpPasvModeCheck"] = ["GlobalSettings", "ftpPassive"]
elementsToOptions["downloadUploadTab"]["ftpUsernameTextbox"] = ["GlobalSettings", "ftpUsername"]
elementsToOptions["downloadUploadTab"]["ftpPasswordTextbox"] = ["GlobalSettings", "ftpPassword"]
elementsToOptions["downloadUploadTab"]["ftpMasterEnableCheck"] = ["GlobalSettings", "ftpEnable"]
elementsToOptions["downloadUploadTab"]["ftpTLSModeCheck"] = ["GlobalSettings", "ftpSecureMode"]
elementsToOptions["downloadUploadTab"]["ftpRemoteFolderTextbox"] = ["GlobalSettings", "ftpRemoteFolder"]
elementsToOptions["downloadUploadTab"]["globalCFBypassUseragentTextbox"] = ["GlobalSettings", "cfbypass_useragent"]
elementsToOptions["downloadUploadTab"]["globalCFBypassCookiefilePathTextbox"] = ["GlobalSettings", "cfbypass_cookiefile"]
elementsToOptions["downloadUploadTab"]["extCmdMasterEnableCheck"] = ["GlobalSettings", "use_external_command"]
elementsToOptions["downloadUploadTab"]["extCmdExeArguments"] = ["GlobalSettings", "external_command_args"]
elementsToOptions["downloadUploadTab"]["extCmdExeLocation"] = ["GlobalSettings", "external_command"]


elementsToOptions["emailSettingsTab"]["emailMasterEnableCheck"] = ["GlobalSettings", "smtp_emailer"]
elementsToOptions["emailSettingsTab"]["hostnameIPTextbox"] = ["GlobalSettings", "smtp_server"]
elementsToOptions["emailSettingsTab"]["portTextbox"] = ["GlobalSettings", "smtp_port"]
elementsToOptions["emailSettingsTab"]["emailUseTLSCheck"] = ["GlobalSettings", "smtp_tls"]
elementsToOptions["emailSettingsTab"]["usernameTextbox"] = ["GlobalSettings", "smtp_username"]
elementsToOptions["emailSettingsTab"]["passwordTextbox"] = ["GlobalSettings", "smtp_password"]
elementsToOptions["emailSettingsTab"]["emailToTextbox"] = ["GlobalSettings", "smtp_to"]
elementsToOptions["emailSettingsTab"]["emailFromTextbox"] = ["GlobalSettings", "smtp_from"]
elementsToOptions["emailSettingsTab"]["emailSubjectTextbox"] = ["GlobalSettings", "smtp_subject"]
elementsToOptions["emailSettingsTab"]["emailMessageTextbox"] = ["GlobalSettings", "smtp_message"]


elementsToOptions["watchlistTab"]["WLSGwatchNameTextbox"] = ["WSPECIAL", "W_TITLE"]
elementsToOptions["watchlistTab"]["WLSGwatchFilterTextbox"] = ["WSPECIAL", "watch_filter"]
elementsToOptions["watchlistTab"]["WLSGwatchFilterRegexCheck"] = ["WSPECIAL", "watch_regex"]
elementsToOptions["watchlistTab"]["WLSGavoidFilterListTextbox"] = ["WSPECIAL", "avoid_filter"]
elementsToOptions["watchlistTab"]["WLSGavoidFilterListRegexCheck"] = ["WSPECIAL", "avoid_regex"]
elementsToOptions["watchlistTab"]["WLSGwatchCatListTextbox"] = ["WSPECIAL", "watch_categories"]
elementsToOptions["watchlistTab"]["WLSGsavepathTextbox"] = ["WSPECIAL", "savepath"]
elementsToOptions["watchlistTab"]["WLSGdupecheckingCheckbox"] = ["WSPECIAL", "dupecheck"]
elementsToOptions["watchlistTab"]["WLSGsizeLimitLowerTextbox"] = ["WSPECIAL", "lower_sizelimit", "SLcombiner('WLSGsizeLimitLowerSuffixSelector')"]
elementsToOptions["watchlistTab"]["WLSGsizeLimitUpperTextbox"] = ["WSPECIAL", "upper_sizelimit", "SLcombiner('WLSGsizeLimitUpperSuffixSelector')"]
elementsToOptions["watchlistTab"]["WLSGemailCheckbox"] = ["WSPECIAL", "use_emailer"]
elementsToOptions["watchlistTab"]["WLSGftpUploadCheckbox"] = ["WSPECIAL", "use_ftp_upload"]
elementsToOptions["watchlistTab"]["WLSGutWebUiCheckox"] = ["WSPECIAL", "use_utorrent_webui"]
elementsToOptions["watchlistTab"]["WLSGenableExternalCmdCheckbox"] = ["WSPECIAL", "use_external_command"]
elementsToOptions["watchlistTab"]["WLSGexternalCommandTextbox"] = ["WSPECIAL", "external_command"]
elementsToOptions["watchlistTab"]["WLSGexternalCommandArgsTextbox"] = ["WSPECIAL", "external_command_args"]


elementsToOptions["globalAvoidlistTab"]["avoidNameTextbox"] = ["ASPECIAL", "A_TITLE"]
elementsToOptions["globalAvoidlistTab"]["avoidFilterTextbox"] = ["ASPECIAL", "avoid_filter"]
elementsToOptions["globalAvoidlistTab"]["avoidFilterRegexCheck"] = ["ASPECIAL", "use_regex"]


#This small dict keeps track of the read and write methods of different Qt types
elementAccessMethods = {}
#                                    READ  ,    WRITE
elementAccessMethods["QLineEdit"] = ["text", "setText"]
elementAccessMethods["QTextEdit"] = ["toHtml", "setHtml"]
elementAccessMethods["QSpinBox"] = ["value", "setValue"]
elementAccessMethods["QCheckBox"] = ["checkState", "setCheckState"]
elementAccessMethods["QComboBox"] = ["currentIndex", "setCurrentIndex"]
elementAccessMethods["QListWidget"] = ["currentItem", "addItem"]
elementAccessMethods["QListWidgetItem"] = ["text", "setText"]


class sccwSettingsManager:
    def __init__(self, settingsfile):
        self.appSettings = QtCore.QSettings(settingsfile, QtCore.QSettings.IniFormat)
        self.elementsToOptions = elementsToOptions
        self.elementAccessMethods = elementAccessMethods
    
    
    def resetSettings(self):
        self.appSettings.clear()
        
    def saveSettings(self, data):
        #data{} is similar in structure to loadSettings()'s data
        #Each key is the subgroup name, below that is another dictionary containing a list of keys and values for that group.
        #You can feed back the data from loadSettings to saveSettings to give you an idea of the structure.
        #The actual subgroups are the tabs of the GUI.
        for group in data:
            #Each key is our group name
            self.appSettings.beginGroup(group)
            for key, value in data[group].iteritems():
                #Save eack value to respective key
                self.appSettings.setValue(key, value)
            #close the group and move on to the next one
            self.appSettings.endGroup()
            
        #We also save window state data at the end
        #Begin group for basic app settings
#        self.appSettings.beginGroup("WindowState")
#        #Screen size and position
#        self.appSettings.setValue("windowSize", data["MainWindow"].size())
#        self.appSettings.setValue("windowPos", data["MainWindow"].pos())
#        self.appSettings.endGroup()
        
        #Almost done, we sync the settings to the file
        self.appSettings.sync()
        
        #Lastly we update the Ui
        #optionsdict = OD()
        #This is where the optionsdict is set up with values from data
        #This is then passed to setupUiOptions() to update the UI with the new settings.
        #self.setupUiOptions(optionsdict)

    def loadSettings(self, data):
        returnData = OD()
        #loop through data{} and get the values requested. Each key is the subgroup name.
        for key in data:
            returnData[key] = OD()
            self.appSettings.beginGroup(key)
            #loop through the list of values to return and get the data
            for value in data[key]:
                #Need to handle QStringLists differently
                item = self.appSettings.value(value).toPyObject()
                if type(item) is QtCore.QStringList:
                    returnData[key][value] = []
                    for x in xrange(len(item)):
                        returnData[key][value].append(str(item[x]))
                else:
                    returnData[key][value] = str(item)
            self.appSettings.endGroup()
        
        #We should have a nice dictionary with all the requested data in it so just return
        return returnData