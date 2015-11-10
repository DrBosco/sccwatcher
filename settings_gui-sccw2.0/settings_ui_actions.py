#!/usr/bin/env python
# wanted to move all the ui functions into their own file to make everything look nicer
# otherwise the settings_ui.py file is going to get really crowded.
from collections import OrderedDict as OD
#from collections import namedtuple as NT
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QDir
from copy import deepcopy as DC
from ntpath import basename as ntpath_basename
from urllib import urlopen as ulibOpen
from ast import literal_eval as safe_eval
import re


try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class guiActions(object):
    def __init__(self, context):
        #If anyone can think of a better way to do this I'm all ears. I think python handles this as a pointer and doesn't copy the entire object, but I could be wrong.
        self.context = context
        #this is different from self.context.SettingsManager.isLoaded.
        #This just flags during the load operation itself and gives no indication as to whether or not something is currently loaded.
        self.__is_loading = False
    
    
    def updateUiTitle(self, text):
        text = "SCCwatcher - %s" % (text)
        self.context.MainWindow.setWindowTitle(_translate("MainWindow", text, None))
    
    def newSettingsFile(self):
        #Start fresh, make sure the user is ok with that
        has_changed, rtn = self.checkUiStateChange()
        #If there were changes, check how the user wanted us to proceed
        if has_changed is True:
            if rtn == QtGui.QMessageBox.Save:
                self.saveUiToFile() #Should we move this to checkUiStateChange too? We have to do this every time.
            elif rtn == QtGui.QMessageBox.Discard:
                pass
            elif rtn == QtGui.QMessageBox.Cancel:
                return
        
        #Now we clear the UI
        self.clearUiData(self.context.SettingsManager.guiDefaults["allOtherDefaults"])
        self.clearUiData(self.context.SettingsManager.guiDefaults["watchlistDefaults"])
        self.clearUiData(self.context.SettingsManager.guiDefaults["avoidlistDefaults"])
        #Remove any watches or avoids
        self.clearList(self.context.WLGwatchlistItemsList)
        self.clearList(self.context.avoidlistItemsList)
        #Reset internal state tracking
        self.context.SettingsManager.guiState["globalOptionsState"] = DC(self.context.SettingsManager.guiDefaults["allOtherDefaults"])
        self.context.SettingsManager.guiState["watchlistState"] = OD()
        self.context.SettingsManager.guiState["avoidlistState"] = OD()
        #Close the current file completely
        self.context.SettingsManager.closeSettingsFile()
        
        #Now set the title
        self.updateUiTitle("New Settings File")
        #and finally set the UI state to fresh
        self.updateUiStateInfo()
        
    def checkListChanges(self, list_object, check_dict):
        #This function will take a watchlist object as list_object and compare its items against the data stored in check_dict
        if len(check_dict) == list_object.count():
            #Ok well at least the size matches, now onto the rest
            #Now loop over the items in the list_object and check for differences one by one. (is there a better way?)
            for cur_index in xrange(0, list_object.count()):
                cur_item = list_object.item(cur_index)
                if cur_item == 0:
                    continue
                cur_item_title = str(cur_item.text())
                cur_item_title = cur_item_title.replace(" ", "_")
                #Do a check to see if the title is in our saved data.
                #If not, we know something has changed and we can quit right now
                if cur_item_title not in check_dict.keys():
                    return True
                #So this name exists in the check_dict dict, we have to check every option now.
                cur_item_data = cur_item.data(Qt.UserRole).toPyObject()
                for cid_option, cid_value in cur_item_data.iteritems():
                    if str(cid_value) != str(check_dict[cur_item_title][cid_option]):
                        return True
        else:
            return True
    
    def checkUiStateChange(self):
        #This function checks to see if the GUI's current state matches the last saved state. If it matches, it returns true. If it doesnt match it returns false.
        is_changed = False
        globalOptions = self.context.SettingsManager.guiState["globalOptionsState"]
        wlOptions = self.context.SettingsManager.guiState["watchlistState"]
        alOptions = self.context.SettingsManager.guiState["avoidlistState"]
        watchlist = self.context.WLGwatchlistItemsList
        avoidlist = self.context.avoidlistItemsList
        
        
        #First we do the easy stuff, all the global options
        for element, old_data in globalOptions.iteritems():
            live_element = eval("self.context." + str(element))
            element_data = self.typeMatcher(live_element, "READ")()
            if old_data != element_data:
                is_changed = True
                break
            
        #Now the more complex bits, we check the watchlist and avoidlist here.
        if is_changed is False:
            if self.checkListChanges(avoidlist, alOptions) is True or self.checkListChanges(watchlist, wlOptions) is True:
                is_changed = True
                    
        if is_changed is True:
            msgBox = QtGui.QMessageBox()
            msgBox.setInformativeText("Do you want to save any changes to the current settings file?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Save)
            rtn = msgBox.exec_()
            return [True, rtn]
        else:
            return [False, None]
        
    def updateUiStateInfo(self):
        #This function will loop through all the GUI options, saving the state of all objects.
        #This will allow us to detect whether or not a user has changed anything in the program since the last save/load operation
        
        globalOptions = self.context.SettingsManager.guiState["globalOptionsState"]
        wlOptions = self.context.SettingsManager.guiState["watchlistState"]
        alOptions = self.context.SettingsManager.guiState["avoidlistState"]
        watchlist = self.context.WLGwatchlistItemsList
        avoidlist = self.context.avoidlistItemsList
        
        #Global options
        for element, old_data in globalOptions.iteritems():
            #First turn the element live so we can check it
            live_element = eval("self.context." + str(element))
            #Now get the elements current state
            element_data = self.typeMatcher(live_element, "READ")()
            globalOptions[element] = element_data
            
        #Watchlist
        for cur_index in xrange(0, watchlist.count()):
            cur_WL_item = watchlist.item(cur_index)
            if cur_WL_item == 0:
                continue
            cur_WL_title = str(cur_WL_item.text())
            cur_WL_title = cur_WL_title.replace(" ", "_")
            cur_WL_data = cur_WL_item.data(Qt.UserRole).toPyObject()
            #Save it
            wlOptions[cur_WL_title] = cur_WL_data
        
        #Avoidlist
        for cur_index in xrange(0, avoidlist.count()):
            cur_AL_item = avoidlist.item(cur_index)
            if cur_AL_item == 0:
                continue
            cur_AL_title = str(cur_AL_item.text())
            cur_AL_title = cur_AL_title.replace(" ", "_")
            cur_AL_data = cur_AL_item.data(Qt.UserRole).toPyObject()
            #Save it
            alOptions[cur_AL_title] = cur_AL_data
    
    def removeWatchListItem(self):
        #This function will remove the currently selected item in the watch list
        self.removeListItem(self.context.WLGwatchlistItemsList)
    
    def removeAvoidListItem(self):
        #This function will remove the currently selected item in the avoid list
        self.removeListItem(self.context.avoidlistItemsList)
    
    #I really don't like repeating myself so I've made a third function here with all the actual code for removing items from watchlists.
    def removeListItem(self, access_object):
        #Get the currently selected item
        current_selection = access_object.currentItem()
        #Get the index of the current item
        current_selection_index = access_object.row(current_selection)
        #And now we remove our watch item from the QListWidget. This also removes any temporary data associated with this item at the same time.
        removed_item = access_object.takeItem(current_selection_index)
        del(removed_item) #Sometimes I don't trust the GC, and it can't hurt to be sure.
        
    def addWatchListItem(self):
        #This function will add a new list item to the watch list
        #First thing we do is make a copy of the defaults for the watchlist, then populate it with values from the general options
        #I am wondering now whether or not making a new deep copy each time we add a list item is a good idea or not. Might lead to a memory leak.
        #We should instead create the structure once and then update the values as needed.
        updated_wl_defaults = DC(self.context.SettingsManager.guiDefaults["watchlistDefaults"])
        updated_wl_defaults["WLSGsavepathTextbox"] = self.context.ggSavepathTextbox.text()
        updated_wl_defaults["WLSGexternalCommandTextbox"] = self.context.extCmdExeLocation.text()
        updated_wl_defaults["WLSGexternalCommandArgsTextbox"] = self.context.extCmdExeArguments.text()
        updated_wl_defaults["WLSGsizeLimitLowerTextbox"] = self.context.globalSizeLimitLowerTextbox.text()
        updated_wl_defaults["WLSGsizeLimitLowerSuffixSelector"] = self.context.globalSizeLimitLowerSuffixSelector.currentIndex()
        updated_wl_defaults["WLSGsizeLimitUpperTextbox"] = self.context.globalSizeLimitUpperTextbox.text()
        updated_wl_defaults["WLSGsizeLimitUpperSuffixSelector"] = self.context.globalSizeLimitUpperSuffixSelector.currentIndex()
        updated_wl_defaults["WLSGenableExternalCmdCheckbox"] = self.context.extCmdMasterEnableCheck.checkState()
        updated_wl_defaults["WLSGdupecheckingCheckbox"] = self.context.globalDupecheckCheck.checkState()
        updated_wl_defaults["WLSGutWebUiCheckox"] = self.context.utwuiMasterEnableTriCheck.checkState()
        updated_wl_defaults["WLSGftpUploadCheckbox"] = self.context.ftpMasterEnableCheck.checkState()
        updated_wl_defaults["WLSGemailCheckbox"] = self.context.emailMasterEnableCheck.checkState()
        
        self.addNewListItem(self.context.WLGwatchlistItemsList, updated_wl_defaults)
    
    def addAvoidListItem(self):
        #This function will add a new list item to the avoid list
        self.addNewListItem(self.context.avoidlistItemsList)
    
    def addNewListItem(self, access_object, wl_defaults=None):
        #Temporarily disable sorting
        __sortingEnabled = access_object.isSortingEnabled()
        access_object.setSortingEnabled(False)
        #Create our QListWidgetItem
        item = QtGui.QListWidgetItem()
        #Make sure our untitled entry isnt going to be a duplicate
        item_title = self.checkForDuplicates(access_object, "Untitled Entry")
        #Set its text
        item.setText(_translate("sccw_SettingsUI", item_title, None))
        #Set the default data items if we are a new watchlist item:
        if wl_defaults is not None:
            item.setData(Qt.UserRole, wl_defaults)  
        #And add the item to the list
        access_object.addItem(item)
        #Finally we reenable sorting, if it was enabled before
        access_object.setSortingEnabled(__sortingEnabled)
    
    def checkForDuplicates(self, access_object, item_text, alt_match=None): #I hate doing this, adding params as needed
        #This function will look for duplicate entries in the QWidgetList supplied as access_object
        #If any duplicates are detected the item_text has a number appended to it (or has its appended number incremented) and is returned
        
        #First we loop through each entry and see if its item_text matches anything in the watchlist.
        for cur_index in xrange(0, access_object.count()):
            cur_item = access_object.item(cur_index)
            cur_item_text = cur_item.text()
            
            if alt_match is not None:
                    #We make sure the current item isnt the one supplied by alt_match
                    if cur_item == alt_match: continue
            
            #Check if the titles match
            if cur_item_text == item_text:
                #Ok we got a duplicate. Lets see if this dupe has a number appended or not
                num_reg = re.match("^(.*?)\s\(([0-9]{1,3})\)$", cur_item_text)
                if num_reg is not None:
                    #This dupe does have a number already. We'll get the number, increment it by one, and put it back.
                    num_end = int(num_reg.group(2)) + 1
                    new_title = "%s (%s)" % (num_reg.group(1), num_end)
                else:
                    #Ok there is no number ending, now we just append a number.
                    new_title = "%s (1)" % (item_text)
                #Finally, we recurse to be sure this new title isnt also a dupe.
                final_return = self.checkForDuplicates(access_object, new_title)
                return final_return
        #No titles matched so we don't have a dupe. We return the correct item_text to confirm this.
        return item_text
    
    #Update functions for when anything is changed for a watchlist or avoidlist item.
    #These two functions save all the data for the item, not just the piece of data that has changed.
    def saveAllAvoidlistItems(self):
        self.saveAllListItems(self.context.avoidlistItemsList, self.context.avoidNameTextbox, self.context.avoidListElements)
    
    def saveAllWatchlistItems(self):
        self.saveAllListItems(self.context.WLGwatchlistItemsList, self.context.WLSGwatchNameTextbox, self.context.watchListElements)
        
    def saveAllListItems(self, access_object, item_title_object, elements_list):
        #Don't operate during a load operation
        if self.__is_loading is True:
            return
        
        #Get the current avoidlist item
        current_list_item = access_object.currentItem()
        
        #First thing we do is make sure the title isnt a dupe.
        #We run the title through a dupe checker and return a new title if necessary
        cur_title = current_list_item.text() #I thought about using the item_title_object to get the title, but this is nicer.
        cur_title = self.checkForDuplicates(access_object, cur_title, current_list_item)
        #Now we set the returned title. If it wasnt a dupe it should be the same as before.
        current_list_item.setText(cur_title)
        #And update the textbox with the title in it
        item_title_object.setText(cur_title)
        
        #Now call the saveListData() function with the avoidlist elements and objects passed
        if "Untitled Entry" not in str(current_list_item.text()):
            self.saveListData(elements_list, current_list_item)

    #These Three functions save the data associated with each watch or avoid item whenever the user switches watch items.
    #The third is the master function while the other two just provide unique data tot he master.
    def updateCurrentAvoidListSelection(self, new_listwidget_item, previous_listwidget_item):
        self.updateCurrentListSelection(new_listwidget_item, previous_listwidget_item, self.context.avoidListElements, self.context.SettingsManager.guiDefaults["avoidlistDefaults"], self.context.avoidlistSettingsGroup)
        
    def updateCurrentWatchListSelection(self, new_listwidget_item, previous_listwidget_item):
        self.updateCurrentListSelection(new_listwidget_item, previous_listwidget_item, self.context.watchListElements, self.context.SettingsManager.guiDefaults["watchlistDefaults"], self.context.watchlistSettingsGroup)
    
    def updateCurrentListSelection(self, new_listwidget_item, previous_listwidget_item, listwidget_elements, reset_data, opgrp_access_object):
        #Set the load var so nothing crappy happens
        self.__is_loading = True
        
        #Save data
        #If things go south here, its probably because its an Untitled entry or theres no entry at all.
        #We still want to reset though so we allow it to pass even if it fails
        if previous_listwidget_item is not None:
            self.saveListData(listwidget_elements, previous_listwidget_item)

        #reset listwidget
        self.clearUiData(reset_data)
        
        #Finally, load new data if necessary
        if new_listwidget_item is not None:
            new_data = new_listwidget_item.data(Qt.UserRole).toPyObject()
            if new_data is not None:
                self.loadListData(new_data)       
            #Set the current selection to this item to be sure
            new_listwidget_item.listWidget().setCurrentItem(new_listwidget_item)
            #Now that we have loaded up our data, we enable the watch/avoid list's option groups if necessary
            if opgrp_access_object.isEnabled() is False:
                opgrp_access_object.setEnabled(True)
            
        else:
            #Ok so we know new_listwidget_item is NoneType, this means the user has no item selected.
            #We will disable the group of options adjacent to the listwidget object
            opgrp_access_object.setDisabled(True)
        #And set the load var again to its normal state
        self.__is_loading = False
        
        
    #These three functions deal with saving, clearing, and loading from watchlists.
    def saveListData(self, listwidget_elements, listwidget_item):
        item_save_data = OD()
        
        #Loop through each item in listwidget_elements
        for element in listwidget_elements:
            live_element = eval("self.context." + str(element))
            if len(listwidget_elements[element]) == 3:
                #Special case for size-limit selectors. We have to save the index of the dropdown list.
                #Get data for both elements.
                prefix, suffix = self.typeMatcher(live_element, "SLC_READ", listwidget_elements[element][2], sc=True)
                #Save the data for the textbox
                item_save_data[element] = prefix
                #And store the data for the dropdown box
                item_save_data[listwidget_elements[element][2]] = suffix
            else:
                #Get our access function to read the data from the live element into our save dict
                item_save_data[element] = self.typeMatcher(live_element, "READ")()
                #We may want to now get the write function to "zero out" the form. This may be better put in its own function however. (why?)
             
        #Now we have an OrderedDict with our data to save in it, we store it inside the element using the setData() function.
        #We will be saving the data in the Qt.UserRole role to the previous qlistwidgetitem we just had selected.
        if hasattr(listwidget_item, "setData"): listwidget_item.setData(Qt.UserRole, item_save_data)
    
    def clearUiData(self, reset_data):
        for element, data in reset_data.iteritems():
            live_element = eval("self.context." + str(element))
            write_function, dtype = self.typeMatcher(live_element, "WRITE")
            if dtype == "str": data = str(data)
            if dtype == "int": data = int(data)
            write_function(data)
    
    def loadListData(self, new_data):
        #Ok we do have data, so lets set the form up with this data
        for element, data in new_data.iteritems():
            live_element = eval("self.context." + str(element))
            write_function, datatype = self.typeMatcher(live_element, "WRITE")
            if datatype == "str": data = str(data)
            if datatype == "int": data = int(data)
            #And now we update the element with the new data
            write_function(data)


    def updateCurrentWatchTitle(self, text):
        current_item = self.context.WLGwatchlistItemsList.currentItem()
        current_item.setText(text)
    
    def updateCurrentAvoidTitle(self, text):
        current_item = self.context.avoidlistItemsList.currentItem()
        current_item.setText(text)
    
    def clearList(self, access_object):
        #This function will remove all items from the QListWidget supplied as access_object
        while access_object.count() > 0:
            removed_item = access_object.takeItem(0)
            del(removed_item) #Sometimes I don't trust the GC, and it can't hurt to be sure.
    
    
    def loadUiState(self):
        #Takes in the data format of loadSettings() and updates the UI with the data received
        #We will go through data{} and use the access method detailed in the uiElements dictionary.
        #The two's structure are identical, making this task extremely simple.
        
        #If we already have a file loaded, prompt the user if they want to save or not
        #This code is going to be changed to detect changes from the last saved internal state.
        if self.context.SettingsManager.isLoaded == True:
            #Check if we need to ask the user to save changes
            has_changed, rtn = self.checkUiStateChange()
            #If there were changes, check how the user wanted us to proceed
            if has_changed is True:
                if rtn == QtGui.QMessageBox.Save:
                    self.saveUiToFile() #Should we move this to checkUiStateChange too? We have to do this every time.
                elif rtn == QtGui.QMessageBox.Discard:
                    pass
                elif rtn == QtGui.QMessageBox.Cancel:
                    return
        
        #Now that we have either saved or discared any changes made, we prompt the user to open up a new file
        #Get the new file name and tell the SettingsManager to update its QSettings object to use the new file location
        filename = self.browse_button_loadFile()
        #Discontinue if the user canceled selection of a file
        if len(filename) < 1:
            return
        else:
            #close the old file first
            self.context.SettingsManager.closeSettingsFile()
            self.context.SettingsManager.openSettingsFile(filename)
        
        #Clear UI state
        self.clearUiData(self.context.SettingsManager.guiDefaults["allOtherDefaults"])
        self.clearUiData(self.context.SettingsManager.guiDefaults["watchlistDefaults"])
        self.clearUiData(self.context.SettingsManager.guiDefaults["avoidlistDefaults"])
        #Remove any watches or avoids
        self.clearList(self.context.WLGwatchlistItemsList)
        self.clearList(self.context.avoidlistItemsList)
        
        #Load up the data
        loaded_data = self.context.SettingsManager.loadSettings()
        #We have to convert the ini option names back into the element object's name.
        converted_data = OD()
        
        #Check if we have the correct settings, if not notify the user and discontinue current operation
        if loaded_data.has_key("GlobalSettings") is False:
            #The settings ini we are trying to load doesnt have our main settings section
            #We will assume this is not a correct file and give an error to the user
            errorbox = QtGui.QMessageBox()
            errorbox.setText("There was an error while trying to load the provided settings file. This file doesn't look like a valid SCCwatcher 2.0 settings file.")
            errorbox.exec_()
            self.context.SettingsManager.closeSettingsFile()
            #Set the title because by now we've already closed the old file so we are effectively at a New File state.
            self.updateUiTitle("New Settings File")
            return
        
        #First we do the general options
        converted_data["GlobalSettings"] = OD()
        for key, value in loaded_data["GlobalSettings"].iteritems():
            objectname = self.context.SettingsManager.REVelementsToOptions[key]
            converted_data["GlobalSettings"][objectname] = value
        
        
        #Clean up loaded_data so we are left with just watches and avoids.
        del(loaded_data["GlobalSettings"])
        
        converted_data["watch"] = OD()
        converted_data["avoid"] = OD()
        
        for key, val in loaded_data.iteritems():
            if key[0] == "-": converted_data["avoid"][key] = val
            else: converted_data["watch"][key] = val
            

        #Ok now converted_data has three subdicts called: GlobalSettings, watch, and avoid.
        #We now go about the business of setting the GUI up with the loaded data.
        #First we do the GlobalSettings.
        #We look through our elementsToOptions dict and set each options as we come upon it.
        for element, einfos in self.context.SettingsManager.elementsToOptions.iteritems():
            data = converted_data["GlobalSettings"][element]
            
            #Make a live access object from element and then use its type to get our access function
            access_string = "self.context." + str(element)
            live_element_obj = eval(access_string)
            #we use typeMatcher() to return our write function
            access_function, datatype = self.typeMatcher(live_element_obj, "WRITE")
            
            #special case for size limit selector
            if len(einfos) > 2:
                #Check if we have any data, if not we just move along
                if len(data) < 1:
                    continue
                #Split up the data into two part, prefix and suffix
                prefix, suffix = re.match("([0-9]{1,9})([A-Za-z]{2})", data).groups()
                suffix = self.convertIndex(suffix)
                #Get the live function for the suffix
                suffix_access_string = "self.context." + str(einfos[2])
                live_suffix_obj = eval(suffix_access_string)
                suffix_access_function = self.typeMatcher(live_suffix_obj, "WRITE")[0]
                #Now we set the data for the prefix
                access_function(prefix)
                suffix_access_function(suffix)
                
            else:
                #Get and set the needed type for the data we plan to set
                if datatype == "str": data = str(data)
                if datatype == "int": data = int(data)
                #update the element with the data
                access_function(data)
        
        #Now we do the watchlist. We do this a little differently.
        #We loop through each key in converted_data["watch"] and create new watchlist items for each one
        #Then we set the data for that item and move onto the next one. We shouldn't have to actually update the GUI since that happens automatically when you click an item.
        for item_name, item_data in converted_data["watch"].iteritems():
            __sortingEnabled = self.context.WLGwatchlistItemsList.isSortingEnabled()
            self.context.WLGwatchlistItemsList.setSortingEnabled(False)
            #Replace any underscores with spaces in the title
            item_name = item_name.replace("_", " ")
            #Create a new QListWidgetItem with the name item_name
            new_item = QtGui.QListWidgetItem()
            #Make sure the item_name isnt a duplicate
            item_name = self.checkForDuplicates(self.context.WLGwatchlistItemsList, item_name)
            new_item.setText(_translate("sccw_SettingsUI", item_name, None))
            #Add the item to the list
            self.context.WLGwatchlistItemsList.addItem(new_item)
            self.context.WLGwatchlistItemsList.setSortingEnabled(__sortingEnabled)
            #Fix the data's options name so they are element names
            item_data = self.fixElementsToOptionsLoad(item_data, self.context.SettingsManager.watchListElements, ["WLSGwatchNameTextbox", item_name])
            #Add the data to the item for the user role. We're using a new item to be sure
            actual_item = self.context.WLGwatchlistItemsList.findItems(item_name, Qt.MatchFixedString)[0]
            actual_item.setData(Qt.UserRole, item_data)
        
        #Same thing for the avoidlist
        for item_name, item_data in converted_data["avoid"].iteritems():
            __sortingEnabled = self.context.avoidlistItemsList.isSortingEnabled()
            self.context.avoidlistItemsList.setSortingEnabled(False)
            #Create our QListWidgetItem
            new_item = QtGui.QListWidgetItem()
            #Remove the minus sign from the beginning of the watch title
            if item_name[0] == "-": item_name = self.removeMinusSignPrefix(item_name)
            #Replace any underscores with spaces in the title
            item_name = item_name.replace("_", " ")
            #Make sure the title isnt a dupe
            item_name = self.checkForDuplicates(self.context.avoidlistItemsList, item_name)
            #Set its text
            new_item.setText(_translate("sccw_SettingsUI", item_name, None))
            #Add to the list
            self.context.avoidlistItemsList.addItem(new_item)
            #Finally we reenable sorting, if it was enabled before
            self.context.avoidlistItemsList.setSortingEnabled(__sortingEnabled)
            #Fix the data
            item_data = self.fixElementsToOptionsLoad(item_data, self.context.SettingsManager.avoidListElements, ["avoidNameTextbox", item_name])
            #Set the data using a new item from the qlistwidget to be sure its the right one
            actual_item = self.context.avoidlistItemsList.findItems(item_name, Qt.MatchFixedString)[0]
            actual_item.setData(Qt.UserRole, item_data)
        
        #Now that a new file has been loaded, we need to update the current internal state
        self.updateUiStateInfo()
        #And finally set the title to the new file's name
        nameonly = str(filename)
        nameonly = nameonly.replace("\\", "/")
        nameonly = ntpath_basename(nameonly)
        title = "%s (%s)" % (nameonly, filename)
        self.updateUiTitle(title)
        
    def removeMinusSignPrefix(self, text):
        #Silly to have this as its own function but recursing has its benefits
        if text[0] == "-":
            text = text[1:]
            text = self.removeMinusSignPrefix(text)
        return text
    
    
    def saveAsDialog(self, recurse=False):
        #Since this is a save-as dialog, we just change the file location and save
        newfilename = self.saveAsAction()
        if len(newfilename) < 1:
            return False
        #Close the old file first
        self.context.SettingsManager.closeSettingsFile()
        #Then set the new file
        self.context.SettingsManager.openSettingsFile(newfilename)
        #Update the title of the window to reflect the new file name
        nameonly = str(newfilename)
        nameonly = nameonly.replace("\\", "/")
        nameonly = ntpath_basename(nameonly)
        title = "%s (%s)" % (nameonly, newfilename)
        self.updateUiTitle(title)
        #Finally we pass onto saveUiToFile to finish things off
        if recurse == False: self.saveUiToFile()
        else: return True
    
    def saveUiToFile(self):
        #Takes the current state of the UI in an OrderedDict and sends it to the saveSettings() function.
        #This is only a temp save, to write the changes to disk you must call syncData() to really get it written.
        #Our return dictionary
        save_data = OD()
        #Our return dictionary will be in the form:
        #save_data[subgroupName][optionName] = data
        
        #If there isnt a file currently loaded to save to, we turn this into a save-as dialog
        if self.context.SettingsManager.isLoaded == False:
            if not self.saveAsDialog(recurse=True):
                return
        
        #Similar to updateUi(), we are going to loop through the uiElements dict and use its access methods to save the Ui state.
        #Now we loop through each element and eval it into life. Then we send each element through a type checking function that will access its data depending on its type.
        for element, data_list in self.context.elementsToOptions.iteritems():
            #Lets separate out some info from data_list first
            #These two options map our data to ini option sections and names
            subgroupName = data_list[0]
            optionName = data_list[1]
            #Do what we need to get the dictionary ready for use
            if subgroupName not in save_data.keys(): save_data[subgroupName] = OD()
            #Here we make up a string with our element, eval it into life, then give it to the type checker
            access_string = "self.context." + str(element)
            live_access_string = eval(access_string)
            #And now we send it to the type checker and set our save_data to its output
            if len(data_list) == 3: read_data = self.typeMatcher(live_access_string, "SLC_READ", data_list[2])
            else: read_data = self.typeMatcher(live_access_string, "READ")()
            save_data[subgroupName][optionName] = read_data
        
        #Now we get the data associated with each watchlist item and save it in our save_data dict
        #This part will get the number of items in the QListWidget and then loop through each QListWidgetItem
        #It will get the QListWidgetItem's text() as the option group name and the data() contains an OrderedDict with our data
        
        #We are going to shorten the variable name a little to make it easier on the eyes.
        watchlist = self.context.WLGwatchlistItemsList
        
        #We're going to grab the data associated with each item in the watchlist and save it to our save_data
        for cur_index in xrange(0, watchlist.count()):
            #Get our watchlist item
            cur_WL_item = watchlist.item(cur_index)
            #If we get a 0 it means this index has no item, so we go onto the next iteration.
            #We should really just break here since returning no item usually means end of list, but I cant be sure.
            if cur_WL_item == 0:
                continue
            
            #Get the watch title
            cur_WL_title = str(cur_WL_item.text())
            #Spaces get encoded as %20 with Qt and there doesn't seem to be any way to change that besides writing my own saving system
            #Much easier to just change them to underscores for now. We can even change them back to spaces later if necessary
            cur_WL_title = cur_WL_title.replace(" ", "_")
            
            #Return our data and use toPyObject() to turn it from a QVariant to an OrderedDict.
            cur_WL_data = cur_WL_item.data(Qt.UserRole).toPyObject()
            
            #Before we can save the data we have to go through it and convert raw element names into human-readable option names.
            fixed_WL_data = self.fixElementsToOptionsSave(cur_WL_data, self.context.watchListElements)
            
            #Should have a nice OrderedDict full of our options with proper, human-readable names.
            save_data[cur_WL_title] = fixed_WL_data
        
        #Ok now we do the same for the avoidlist, except we prepend the title with a minus.
        avoidlist = self.context.avoidlistItemsList
        for cur_index in xrange(0, avoidlist.count()):
            #Get the avoidlist item
            cur_AL_item = avoidlist.item(cur_index)
            if cur_AL_item == 0:
                continue
            
            #Set the title, a minus denotes it is an avoidlist item. REMEMBER TO REMOVE ON LOAD!
            cur_AL_title = str(cur_AL_item.text())
            cur_AL_title = cur_AL_title.replace(" ", "_")
            cur_AL_title = "-" + cur_AL_title
            
            #Get the data
            cur_AL_data = cur_AL_item.data(Qt.UserRole).toPyObject()
            
            #Change the keys from the element name to the option name for saving
            fixed_AL_data = self.fixElementsToOptionsSave(cur_AL_data, self.context.avoidListElements)
            
            #save the data
            save_data[cur_AL_title] = fixed_AL_data
        
        #We should now have a nice dictionary filled with the current state of our app. Lets send it to our save function and let it handle the rest
        self.context.SettingsManager.saveSettings(save_data)
        
        #We lastly need to update the internal GUI state since things could have changed since the last load/save operation
        self.updateUiStateInfo()
    
    
    def fixElementsToOptionsSave(self, cur_L_data, listElements):
        fixed_L_data = OD()
        for element, data_list in listElements.iteritems():
            if "TITLE" in data_list[1]:
                continue
            #data_list[1] is our option name
            if len(data_list) == 3:
                #special case for size-limit selectors
                #Remember, we have to undo this on load
                suffix = self.convertIndex(cur_L_data[data_list[2]])
                nice_size_limit = str(cur_L_data[element]) + str(suffix)
                fixed_L_data[data_list[1]] = nice_size_limit
            else:    
                fixed_L_data[data_list[1]] = cur_L_data[element]
        return fixed_L_data
    
    def fixElementsToOptionsLoad(self, loaded_data, listElements, nametextbox):
        fixed_loaded_data = OD()
        for element, data_list in listElements.iteritems():
            if "TITLE" in data_list[1]:
                fixed_loaded_data[nametextbox[0]] = nametextbox[1]
                continue
            
            option_name = data_list[1]
            data = loaded_data[option_name]
            
            if len(data_list) == 3:
                #special case for size-limit selectors
                #Split the data into two different items
                try:
                    prefix, suffix = re.match("([0-9]{1,9})([A-Za-z]{2})", data).groups()
                    suffix = self.convertIndex(suffix)
                except:
                    #This option was probably not set by the user so we ignore it too by setting the prefix and suffix to default
                    prefix = ""
                    suffix = 0
                    
                suffix_element_name = data_list[2]
                #Set the data for both the prefix and suffix
                fixed_loaded_data[element] = prefix
                fixed_loaded_data[suffix_element_name] = suffix
            else:    
                fixed_loaded_data[element] = loaded_data[option_name]
        return fixed_loaded_data
    
    def convertIndex(self, index):
        if type(index) == str:
            if index == "": suffix = 0
            if index == "KB": suffix = 1
            if index == "MB": suffix = 2
            if index == "GB": suffix = 3
        if type(index) == int:
            if index == 0: suffix = ""
            if index == 1: suffix = "KB"
            if index == 2: suffix = "MB"
            if index == 3: suffix = "GB"
        return suffix
        
    def typeMatcher(self, access_object, operation, alt_obj = None, sc = False):
        #This function will match the type of the access_object provided to a dictionary and return the data requested in operation.
        #operation can be READ, WRITE or a special case called SLC_READ.
        if operation == "SLC_READ":
            #SLC_READ is used when we need both the size and suffix of our sizelimit entries in one piece of data.
            #We need to concatenate the data returned from two objects
                prefix = self.typeMatcher(access_object, "READ")()
                suffix_index = int(self.typeMatcher(eval("self.context." + str(alt_obj)), "READ")())
                suffix = self.convertIndex(suffix_index)
                if sc is True: return [prefix, suffix_index]
                else: return str(prefix) + suffix
                    
        #Convert operation into numbers to make matching to index easier. Read is default.
        op = 0
        if operation == "WRITE": op = 1
        
        for type_name in self.context.elementAccessMethods.keys():
            if type_name in str(type(access_object)):
                access_function = self.context.elementAccessMethods[type_name][op]
                if op == 1: dtype = self.context.elementAccessMethods[type_name][2]
                break
        #Now we have our access function, we use getattr to return the live function
        live_function = getattr(access_object, access_function)
        if op == 1:
            return (live_function, dtype)
        else:
            return live_function
    
    
    
    #Here are the 6 browse buttons. I would have to mess around with the QPushButton class, changing the way it emits, if I wanted to cut these down.
    #start_dir is a list because im lazy and didn't want to rewrite it the correct way. Nobody but me is going to be messing around this part of the code anyway.
    #The extra digit controls whether the start_dir should be returned if the user cancels the dialog instead of making a selection.
    
    def browse_button_mainSavepath(self):
        caption = "Choose location to save .torrent files..."
        if len(self.context.ggSavepathTextbox.text()) > 1:
            start_dir = [self.context.ggSavepathTextbox.text(), 1]
        elif len(self.context.ggLogpathTextbox.text()) > 1:
            start_dir = [self.context.ggLogpathTextbox.text(), 0]
        elif len(self.context.SettingsManager.currentFile) > 1:
            start_dir = [self.context.SettingsManager.currentFile, 0]
        else:
            start_dir = [QDir.currentPath(), 0]
        
        self.browse_button_master(self.context.ggSavepathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption, start_dir=start_dir)
    
    def browse_button_mainLogpath(self):
        if len(self.context.ggLogpathTextbox.text()) > 1:
            start_dir = [self.context.ggLogpathTextbox.text(), 1]
        elif len(self.context.ggSavepathTextbox.text()) > 1:
            start_dir = [self.context.ggSavepathTextbox.text(), 0]
        elif len(self.context.SettingsManager.currentFile) > 1:
            start_dir = [self.context.SettingsManager.currentFile, 0]
        else:
            start_dir = [QDir.currentPath(), 0]
        
        caption = "Choose location to save logs..."
        self.browse_button_master(self.context.ggLogpathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption, start_dir=start_dir)
        
    
    def browse_button_cookieFile(self):
        start_dir = [self.context.globalCFBypassCookiefilePathTextbox.text(), 1]
        caption = "Location of cookie file..."
        self.browse_button_master(self.context.globalCFBypassCookiefilePathTextbox, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, start_dir=start_dir)
        
        
    def browse_button_mainExtProgram(self):
        start_dir = [self.context.extCmdExeLocation.text(), 1]
        caption = "Choose Program..."
        self.browse_button_master(self.context.extCmdExeLocation, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, start_dir=start_dir)
        
        
    def browse_button_WLsavepath(self):
        start_dir = [self.context.WLSGsavepathTextbox.text(), 1]
        caption = "Choose location to save .torrent files to..."
        self.browse_button_master(self.context.WLSGsavepathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption, start_dir=start_dir)
        #Update the data for the watch item manually
        self.saveAllWatchlistItems()
        
        
    def browse_button_WLextProgram(self):
        start_dir = [self.context.WLSGexternalCommandTextbox.text(), 1]
        caption = "Choose Program..."
        self.browse_button_master(self.context.WLSGexternalCommandTextbox, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, start_dir=start_dir)
        #Update the data for the watch item manually
        self.saveAllWatchlistItems()
    
    def browse_button_loadFile(self):
        start_dir = [self.context.SettingsManager.currentFile, 0]
        caption = "Location of scc.ini..."
        filename = self.browse_button_master(None, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption, alt_mode=True, start_dir=start_dir)
        return filename
    
    def saveAsAction(self):
        start_dir = [self.context.SettingsManager.currentFile, 0]
        caption = "Choose location to save settings file..."
        filename = self.browse_button_master(None, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.AnyFile, caption, alt_mode=True, save_mode=True, start_dir=start_dir)
        return filename
    
    
    def browse_button_master(self, access_object, main_mode, file_mode, dialog_caption, alt_mode=False, save_mode=False, start_dir=["", 0]):
        rtnstat = start_dir[1]
        start_dir = start_dir[0]
        
        fileDialog = QtGui.QFileDialog()
        fileDialog.AcceptMode = main_mode
        fileDialog.setFileMode(file_mode)
        fileDialog.setDirectory(start_dir)
        if save_mode == True:
            fd_access = fileDialog.getSaveFileName
        else:
            fd_access = fileDialog.getOpenFileName
        
        if file_mode == QtGui.QFileDialog.Directory:
            chosenFile = fileDialog.getExistingDirectory(caption=dialog_caption)
        elif file_mode == QtGui.QFileDialog.ExistingFile or file_mode == QtGui.QFileDialog.AnyFile:
            chosenFile = fd_access(caption=dialog_caption)
        
        if len(chosenFile) < 1:
            if rtnstat == 1:
                chosenFile = start_dir
        
        if alt_mode is True:
            #We are going to return the filename instead
            return chosenFile
        else:
            access_object.setText(_translate("sccw_SettingsUI", chosenFile, None))
    
    
    #These EDsection_ functions enable/disable the option sections that correspond to certain checkboxes.
    #checkboxes will have thier toggled(bool) slots tied into these functions.
    #It was only possible to directly connect one checkbox, the others needed these helper functions.
    def EDsection_ftpupload(self, state):
        #FTP upload section of Upload/Download tab
        #These functions are pretty simple, we just pass state, which is a bool, to the setEnabled functions of the objects we need to turn off/on.
        self.context.ftpHostnameTextbox.setEnabled(state)
        self.context.ftpPortTextbox.setEnabled(state)
        self.context.ftpUsernameTextbox.setEnabled(state)
        self.context.ftpPasswordTextbox.setEnabled(state)
        self.context.ftpRemoteFolderTextbox.setEnabled(state)
        self.context.ftpPasvModeCheck.setEnabled(state)
        self.context.ftpTLSModeCheck.setEnabled(state)
        
    def EDsection_utwebui(self, state):
        #uTorrent WebUI of the Ul/Dl tab
        #Because this is a tri-state checkbox we cant use toggled(bool). Instead of have to use stateChanged(int) and compare the int.
        #We also update the QLabel here with the appropriate text and color change to indicate the different modes of operation for the utorrent module
        
        #QLabel first
        if state == 0:
            color = "#ff0000"
            text = "Disabled"
        elif state == 1:
            color = "#00aa00"
            text = "Normal DL and WebUI UL"
        elif state == 2:
            color = "#ff8700"
            text = "WebUI Uploading Only"
            
        self.context.utwuiStateLabel.setText(_translate("sccw_SettingsUI", "<html><head/><body><p><span style=\" font-weight:600; color:%s;\">%s</span></p></body></html>" % (color, text), None))
        
        if state > 0: state = True
        else: state = False
        self.context.utwuiHostnameTextbox.setEnabled(state)
        self.context.utwuiPortTextbox.setEnabled(state)
        self.context.utwuiUsernameTextbox.setEnabled(state)
        self.context.utwuiPasswordTextbox.setEnabled(state)
        
    def EDsection_externalcmd(self, state):
        #External command section of the ul/dl tab
        self.context.extCmdExeLocation.setEnabled(state)
        self.context.extCmdBrowseButton.setEnabled(state)
        self.context.extCmdExeArguments.setEnabled(state)
        
    def EDsection_emailer(self, state):
        #Emailer section of the Emailer tab
        self.context.hostnameIPTextbox.setEnabled(state)
        self.context.portTextbox.setEnabled(state)
        self.context.usernameTextbox.setEnabled(state)
        self.context.passwordTextbox.setEnabled(state)
        self.context.emailUseTLSCheck.setEnabled(state)
        self.context.emailFromTextbox.setEnabled(state)
        self.context.emailToTextbox.setEnabled(state)
        self.context.emailSubjectTextbox.setEnabled(state)
        self.context.emailMessageTextbox.setEnabled(state)
    
    def checkForUpdates(self):
        #version_regex = "(?P<major>[0-9])\.(?P<minor>[0-9]{1,3})(?P<extra>[a-zA-Z][0-9]{1,2})?"
        text_color = "#ff0000"
        comment = "Error!"
        c = ulibOpen(self.context.SettingsManager._GITHUB_VER_URL_)
        version_txt = c.read()
        c.close()
        #Fix some minor stuffs
        version_txt = version_txt.replace("true", "True")
        version_txt = version_txt.replace("false", "False")
        try:
            version_dict = safe_eval(version_txt) #might still be a bad idea
        except Exception as e:
            print e
            return
        latest_version = version_dict["tag_name"]
        #Now we separate out the components of the version and compare against our own
        #This is a more exact way to test and is incomplete, will work on this further if necessary
        #ourver_re = re.match(version_regex, self.context.SettingsManager._CURRENT_GUI_VERSION_)
        #latestver_re = re.match(version_regex, latest_version)
        
        #This seemed like a good idea at the time, but now I dunno
        #It seems to work most of the time, as long as I dont do anything crazy with the version string.
        if self.context.SettingsManager._CURRENT_GUI_VERSION_ < latest_version:
            text_color = "#ff0000"
            comment = "Old"
        else:
            comment = "Latest"
            text_color = "#0055ff"
        
        #Set the latest version number in the GUI
        self.context.ugServVerActual.setText(_translate("sccw_SettingsUI", "<html><head/><body><p><span style=\" font-weight:600; color:#0055ff;\">%s</span></p></body></html>" % (latest_version), None))
        self.context.ugCliVerActual.setText(_translate("sccw_SettingsUI", "<html><head/><body><p><span style=\" font-weight:600; color:%s;\">%s (%s)</span></p></body></html>" % (text_color, self.context.SettingsManager._CURRENT_GUI_VERSION_, comment), None))
        

    #Undo/Redo system.
    #Temporarily removed to restore my sanity
    