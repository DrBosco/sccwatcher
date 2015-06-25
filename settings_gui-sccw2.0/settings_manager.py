from PyQt4 import QtCore
from collections import OrderedDict as OD

#Get ready for tons of lame code
#The use of OD(), OrderedDict, means that the dictionary we create will be in the exact order as its created.
#This is useful because we also don't wan't the options in our ini file being saved in any old way, we want an order.
#The order of options is therefore extremely important. All of the global options must come first before all others.

#Format for the database is this:
#uiElements[element_name] = [ini_file_section_name, ini_file_option_name]
#The access methods are provided by running a type comparison on an eval of the element_name. Eval'ing turns that name into a proper object which can be type()'d.
#The type database is kept in elementAccessMethods below elementsToOptions.

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

#These special options get processed for each entry in WLGwatchlistItemsList
elementsToOptions["WLSGwatchNameTextbox"] = ["WSPECIAL", "W_TITLE"]
elementsToOptions["WLSGwatchFilterTextbox"] = ["WSPECIAL", "watch_filter"]
elementsToOptions["WLSGwatchFilterRegexCheck"] = ["WSPECIAL", "watch_regex"]
elementsToOptions["WLSGavoidFilterListTextbox"] = ["WSPECIAL", "avoid_filter"]
elementsToOptions["WLSGavoidFilterListRegexCheck"] = ["WSPECIAL", "avoid_regex"]
elementsToOptions["WLSGwatchCatListTextbox"] = ["WSPECIAL", "watch_categories"]
elementsToOptions["WLSGsavepathTextbox"] = ["WSPECIAL", "savepath"]
elementsToOptions["WLSGdupecheckingCheckbox"] = ["WSPECIAL", "dupecheck"]
elementsToOptions["WLSGsizeLimitLowerTextbox"] = ["WSPECIAL", "lower_sizelimit", "WLSGsizeLimitLowerSuffixSelector"]
elementsToOptions["WLSGsizeLimitUpperTextbox"] = ["WSPECIAL", "upper_sizelimit", "WLSGsizeLimitUpperSuffixSelector"]
elementsToOptions["WLSGemailCheckbox"] = ["WSPECIAL", "use_emailer"]
elementsToOptions["WLSGftpUploadCheckbox"] = ["WSPECIAL", "use_ftp_upload"]
elementsToOptions["WLSGutWebUiCheckox"] = ["WSPECIAL", "use_utorrent_webui"]
elementsToOptions["WLSGenableExternalCmdCheckbox"] = ["WSPECIAL", "use_external_command"]
elementsToOptions["WLSGexternalCommandTextbox"] = ["WSPECIAL", "external_command"]
elementsToOptions["WLSGexternalCommandArgsTextbox"] = ["WSPECIAL", "external_command_args"]

#Same special thing here, all items in avoidlistItemsList are processed and saved.
#A_TITLE functions identically to W_TITLE, except the avoid name is prefixed by a minus sign, to mark it as an avoid.
elementsToOptions["avoidNameTextbox"] = ["ASPECIAL", "A_TITLE"]
elementsToOptions["avoidFilterTextbox"] = ["ASPECIAL", "avoid_filter"]
elementsToOptions["avoidFilterRegexCheck"] = ["ASPECIAL", "use_regex"]


#This small dict keeps track of the read and write methods of different Qt types
elementAccessMethods = {}
#                                    READ  ,    WRITE
elementAccessMethods["QLineEdit"] = ["text", "setText"]
elementAccessMethods["QTextEdit"] = ["toPlainText", "setPlainText"]
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
        
    def syncData(self):
        #Commit all settings to file
        self.appSettings.sync()
    
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