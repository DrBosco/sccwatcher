from PyQt4 import QtCore
from collections import OrderedDict as OD

#Get ready for tons of lame code
#The use of OD(), OrderedDict, means that the dictionary we create will be in the exact order as its created.
#This is useful because we also don't wan't the options in our ini file being saved in any old way, we want an order.
#The order of options is therefore extremely important. All of the global options must come first before all others.

#Format for the dictionary is this:
#uiElements[element_name] = [ini_file_section_name, ini_file_option_name]
#The access methods are provided by running a type comparison on an eval of the element_name. Eval'ing turns that name into a proper object which can be type()'d.
#The type dictionary is kept in elementAccessMethods below elementsToOptions.

#This dictionary defines the translation between UI Elements and ini options. Without this, things would get much more complicated.
#The structure is the same as all the other elements databases. The main keys are the tab names, and each subkey of the tab is the UI element. Each value is the Group and the INI option name in a list.
elementsToOptions = OD()
#basic download and operational options first
elementsToOptions["ggMasterAutodlCheck"] = ["GlobalSettings", "service"]
elementsToOptions["ggEnableVerboseCheck"] = ["GlobalSettings", "verbose"]
elementsToOptions["ggVerboseTabTextbox"] = ["GlobalSettings", "verbose_tab"]
elementsToOptions["ggBeepCheckbox"] = ["GlobalSettings", "printalert"]
elementsToOptions["ggEnableLoggingCheck"] = ["GlobalSettings", "logenabled"]
elementsToOptions["ggLogpathTextbox"] = ["GlobalSettings", "logpath"]
elementsToOptions["ggNetworkDelaySpinbox"] = ["GlobalSettings", "startdelay"]
elementsToOptions["ggPasskeyTextbox"] = ["GlobalSettings", "passkey"]
elementsToOptions["globalDupecheckCheck"] = ["GlobalSettings", "dupecheck"]
elementsToOptions["globalSSLDownloadCheck"] = ["GlobalSettings", "download_ssl"]
elementsToOptions["ggSavepathTextbox"] = ["GlobalSettings", "savepath"]
#These Size Limit UI elements need some special treatment. Both when loading and saving.
#These hold another object name in index 3 that will signal the function to operate on the third data item, the element name that holds the suffix data.
elementsToOptions["globalSizeLimitLowerTextbox"] = ["GlobalSettings", "sizelimit_lower", "globalSizeLimitLowerSuffixSelector"]
elementsToOptions["globalSizeLimitUpperTextbox"] = ["GlobalSettings", "sizelimit_upper", "globalSizeLimitUpperSuffixSelector"]
elementsToOptions["globalCFBypassUseragentTextbox"] = ["GlobalSettings", "cfbypass_useragent"]
elementsToOptions["globalCFBypassCookiefilePathTextbox"] = ["GlobalSettings", "cfbypass_cookiefile"]
#ftp settings
elementsToOptions["ftpMasterEnableCheck"] = ["GlobalSettings", "ftpEnable"]
elementsToOptions["ftpHostnameTextbox"] = ["GlobalSettings", "ftpServerHostname"]
elementsToOptions["ftpPortTextbox"] = ["GlobalSettings", "ftpPort"]
elementsToOptions["ftpRemoteFolderTextbox"] = ["GlobalSettings", "ftpRemoteFolder"]
elementsToOptions["ftpUsernameTextbox"] = ["GlobalSettings", "ftpUsername"]
elementsToOptions["ftpPasswordTextbox"] = ["GlobalSettings", "ftpPassword"]
elementsToOptions["ftpPasvModeCheck"] = ["GlobalSettings", "ftpPassive"]
elementsToOptions["ftpTLSModeCheck"] = ["GlobalSettings", "ftpSecureMode"]
#ut web ui options
elementsToOptions["utwuiMasterEnableTriCheck"] = ["GlobalSettings", "utorrent_mode"]
elementsToOptions["utwuiUsernameTextbox"] = ["GlobalSettings", "utorrent_username"]
elementsToOptions["utwuiPasswordTextbox"] = ["GlobalSettings", "utorrent_password"]
elementsToOptions["utwuiHostnameTextbox"] = ["GlobalSettings", "utorrent_hostname"]
elementsToOptions["utwuiPortTextbox"] = ["GlobalSettings", "utorrent_port"]
#Email options
elementsToOptions["emailMasterEnableCheck"] = ["GlobalSettings", "smtp_emailer"]
elementsToOptions["hostnameIPTextbox"] = ["GlobalSettings", "smtp_server"]
elementsToOptions["portTextbox"] = ["GlobalSettings", "smtp_port"]
elementsToOptions["emailUseTLSCheck"] = ["GlobalSettings", "smtp_tls"]
elementsToOptions["usernameTextbox"] = ["GlobalSettings", "smtp_username"]
elementsToOptions["passwordTextbox"] = ["GlobalSettings", "smtp_password"]
elementsToOptions["emailFromTextbox"] = ["GlobalSettings", "smtp_from"]
elementsToOptions["emailToTextbox"] = ["GlobalSettings", "smtp_to"]
elementsToOptions["emailSubjectTextbox"] = ["GlobalSettings", "smtp_subject"]
elementsToOptions["emailMessageTextbox"] = ["GlobalSettings", "smtp_message"]
#External command
elementsToOptions["extCmdMasterEnableCheck"] = ["GlobalSettings", "use_external_command"]
elementsToOptions["extCmdExeLocation"] = ["GlobalSettings", "external_command"]
elementsToOptions["extCmdExeArguments"] = ["GlobalSettings", "external_command_args"]
#Debug is always last
elementsToOptions["ggEnableDebugCheck"] = ["GlobalSettings", "DEBUG"] 


#These two OrderedDict's are for the watch and avoid lists, respectively. 

watchListElements = OD()
#These special options get processed for each entry in WLGwatchlistItemsList
watchListElements["WLSGwatchNameTextbox"] = ["WSPECIAL", "W_TITLE"]
watchListElements["WLSGwatchFilterTextbox"] = ["WSPECIAL", "watch_filter"]
watchListElements["WLSGwatchFilterRegexCheck"] = ["WSPECIAL", "watch_regex"]
watchListElements["WLSGavoidFilterListTextbox"] = ["WSPECIAL", "avoid_filter"]
watchListElements["WLSGavoidFilterListRegexCheck"] = ["WSPECIAL", "avoid_regex"]
watchListElements["WLSGwatchCatListTextbox"] = ["WSPECIAL", "watch_categories"]
watchListElements["WLSGsavepathTextbox"] = ["WSPECIAL", "savepath"]
watchListElements["WLSGdupecheckingCheckbox"] = ["WSPECIAL", "dupecheck"]
watchListElements["WLSGsizeLimitLowerTextbox"] = ["WSPECIAL", "lower_sizelimit", "WLSGsizeLimitLowerSuffixSelector"]
watchListElements["WLSGsizeLimitUpperTextbox"] = ["WSPECIAL", "upper_sizelimit", "WLSGsizeLimitUpperSuffixSelector"]
watchListElements["WLSGemailCheckbox"] = ["WSPECIAL", "use_emailer"]
watchListElements["WLSGftpUploadCheckbox"] = ["WSPECIAL", "use_ftp_upload"]
watchListElements["WLSGutWebUiCheckox"] = ["WSPECIAL", "use_utorrent_webui"]
watchListElements["WLSGenableExternalCmdCheckbox"] = ["WSPECIAL", "use_external_command"]
watchListElements["WLSGexternalCommandTextbox"] = ["WSPECIAL", "external_command"]
watchListElements["WLSGexternalCommandArgsTextbox"] = ["WSPECIAL", "external_command_args"]


avoidListElements = OD()
#Same special thing here, all items in avoidlistItemsList are processed and saved.
#A_TITLE functions identically to W_TITLE, except the avoid name is prefixed by a minus sign, to mark it as an avoid.
avoidListElements["avoidNameTextbox"] = ["ASPECIAL", "A_TITLE"]
avoidListElements["avoidFilterTextbox"] = ["ASPECIAL", "avoid_filter"]
avoidListElements["avoidFilterRegexCheck"] = ["ASPECIAL", "use_regex"]


#This small dict keeps track of the read and write methods of different Qt types as well as the expected data type
elementAccessMethods = {}
#                                    READ  ,    WRITE   ,   type
elementAccessMethods["QLineEdit"] = ["text", "setText", "str"]
elementAccessMethods["QTextEdit"] = ["toPlainText", "setPlainText", "str"]
elementAccessMethods["QSpinBox"] = ["value", "setValue", "int"]
elementAccessMethods["QCheckBox"] = ["checkState", "setCheckState", "int"]
elementAccessMethods["QComboBox"] = ["currentIndex", "setCurrentIndex", "int"]
elementAccessMethods["QListWidget"] = ["currentItem", "addItem", "QListWidgetItem"]
elementAccessMethods["QListWidgetItem"] = ["text", "setText", "str"]

#Create a reverse dicts for the options>elements conversion.
globalReverse = OD()
watchReverse = OD()
avoidReverse = OD()
for key, val in elementsToOptions.iteritems(): globalReverse[val[1]] = key
for key, val in watchListElements.iteritems(): watchReverse[val[1]] = key
for key, val in avoidListElements.iteritems(): avoidReverse[val[1]] = key

#GUI Defaults
#These three dicts contain the default state of our application.
guiDefaults = {}
guiDefaults["watchlistDefaults"] = OD([('WLSGwatchNameTextbox', QtCore.QString(u'')), ('WLSGwatchFilterTextbox', QtCore.QString(u'')), ('WLSGwatchFilterRegexCheck', 0), ('WLSGavoidFilterListTextbox', QtCore.QString(u'')), ('WLSGavoidFilterListRegexCheck', 0), ('WLSGwatchCatListTextbox', QtCore.QString(u'')), ('WLSGsavepathTextbox', QtCore.QString(u'')), ('WLSGdupecheckingCheckbox', 0), ('WLSGsizeLimitLowerTextbox', QtCore.QString(u'')), ('WLSGsizeLimitLowerSuffixSelector', 0), ('WLSGsizeLimitUpperTextbox', QtCore.QString(u'')), ('WLSGsizeLimitUpperSuffixSelector', 0), ('WLSGemailCheckbox', 0), ('WLSGftpUploadCheckbox', 0), ('WLSGutWebUiCheckox', 0), ('WLSGenableExternalCmdCheckbox', 0), ('WLSGexternalCommandTextbox', QtCore.QString(u'')), ('WLSGexternalCommandArgsTextbox', QtCore.QString(u''))])
guiDefaults["avoidlistDefaults"] = OD([('avoidNameTextbox', QtCore.QString(u'')), ('avoidFilterTextbox', QtCore.QString(u'')), ('avoidFilterRegexCheck', 0)])
guiDefaults["allOtherDefaults"] = OD([('ggMasterAutodlCheck', 0), ('ggEnableVerboseCheck', 0), ('ggVerboseTabTextbox', QtCore.QString(u'')), ('ggBeepCheckbox', 0), ('ggEnableLoggingCheck', 0), ('ggLogpathTextbox', QtCore.QString(u'')), ('ggNetworkDelaySpinbox', 0), ('ggPasskeyTextbox', QtCore.QString(u'')), ('globalDupecheckCheck', 0), ('globalSSLDownloadCheck', 0), ('ggSavepathTextbox', QtCore.QString(u'')), ('globalSizeLimitLowerTextbox', ''), ('globalSizeLimitUpperTextbox', ''), ('globalSizeLimitLowerSuffixSelector', 0), ('globalSizeLimitUpperSuffixSelector', 0), ('globalCFBypassUseragentTextbox', QtCore.QString(u'')), ('globalCFBypassCookiefilePathTextbox', QtCore.QString(u'')), ('ftpMasterEnableCheck', 0), ('ftpHostnameTextbox', QtCore.QString(u'')), ('ftpPortTextbox', QtCore.QString(u'')), ('ftpRemoteFolderTextbox', QtCore.QString(u'')), ('ftpUsernameTextbox', QtCore.QString(u'')), ('ftpPasswordTextbox', QtCore.QString(u'')), ('ftpPasvModeCheck', 0), ('ftpTLSModeCheck', 0), ('utwuiMasterEnableTriCheck', 0), ('utwuiUsernameTextbox', QtCore.QString(u'')), ('utwuiPasswordTextbox', QtCore.QString(u'')), ('utwuiHostnameTextbox', QtCore.QString(u'')), ('utwuiPortTextbox', QtCore.QString(u'')), ('emailMasterEnableCheck', 0), ('hostnameIPTextbox', QtCore.QString(u'')), ('portTextbox', QtCore.QString(u'')), ('emailUseTLSCheck', 0), ('usernameTextbox', QtCore.QString(u'')), ('passwordTextbox', QtCore.QString(u'')), ('emailFromTextbox', QtCore.QString(u'')), ('emailToTextbox', QtCore.QString(u'')), ('emailSubjectTextbox', QtCore.QString(u'')), ('emailMessageTextbox', QtCore.QString(u'')), ('extCmdMasterEnableCheck', 0), ('extCmdExeLocation', QtCore.QString(u'')), ('extCmdExeArguments', QtCore.QString(u'')), ('ggEnableDebugCheck', 0)])


class sccwSettingsManager:
    def __init__(self, settingsfile, MWloc):
        self.appSettings = None
        self.elementsToOptions = elementsToOptions
        self.elementAccessMethods = elementAccessMethods
        self.watchListElements = watchListElements
        self.avoidListElements = avoidListElements
        self.REVelementsToOptions = globalReverse
        self.REVwatchListElements = watchReverse
        self.REVavoidListElements = avoidReverse
        self.guiDefaults = guiDefaults
        self.windowPos = MWloc[0]
        self.windowSize = MWloc[1]
        self.isLoaded = False
        
    def resetSettings(self):
        self.appSettings.clear()   
        
    def syncData(self):
        #Commit all settings to file
        self.appSettings.sync()
    
    def openSettingsFile(self, filename):
        self.appSettings = QtCore.QSettings(filename, QtCore.QSettings.IniFormat)
        self.appSettings.setIniCodec("UTF-8")
        self.isLoaded = True
        
    def closeSettingsFile(self):
        self.appSettings = None
        self.isLoaded = False
    
    def saveSettings(self, data):
        #Clear out the data currently in our QSetting object to make sure no old stale data is saved
        self.resetSettings()
        
        #data{} is similar in structure to loadSettings()'s data
        #Each key is the subgroup name, below that is another dictionary containing a list of keys and values for that group.
        #You can feed back the data from loadSettings to saveSettings to give you an idea of the structure.
        #The actual subgroups are the tabs of the GUI.
        for group in data:
            #Each key is our group name
            if data[group] is None:
                continue
            self.appSettings.beginGroup(group)
            for key, value in data[group].iteritems():
                #Save eack value to respective key
                self.appSettings.setValue(key, value)
            #close the group and move on to the next one
            self.appSettings.endGroup()
            
        #We also save window state data at the end
        #Begin group for window state (size and position)
        #Consider moving this to a different QSettings object, one that saves to the registry instead.
        #This WILL be moved to registery before we use it. Until then its commented out and the settings arent ever used if loaded.
        #self.appSettings.beginGroup("WindowState")
        #Screen size and position
        #self.appSettings.setValue("windowSize", self.windowSize())
        #self.appSettings.setValue("windowPos", self.windowPos())
        #self.appSettings.endGroup()
        
        #Sync data. It works without this because sync() is automatically called on the destruction of the QSettings object, which happens at close.
        #Id rather do it now though.
        self.syncData()

    def loadSettings(self):
        returnData = OD()
        #We have no idea what subgroups we need to load so we have to get the list
        #We'll loop through each subgroup and get the data for each.
        
        for subgroup in self.appSettings.childGroups():
            subgroup = str(subgroup)
            returnData[subgroup] = OD()
            self.appSettings.beginGroup(subgroup)
            #loop through the keys in this subgroup and save their values
            for value in self.appSettings.childKeys():
                value = str(value)
                #Need to handle QStringLists differently
                item = self.appSettings.value(value).toPyObject()
                if type(item) is QtCore.QStringList:
                    returnData[subgroup][value] = []
                    for x in xrange(len(item)):
                        returnData[subgroup][value].append(str(item[x]))
                else:
                    returnData[subgroup][value] = str(item)
            self.appSettings.endGroup()
        
        #We should have a nice dictionary with all the requested data in it so just return
        return returnData