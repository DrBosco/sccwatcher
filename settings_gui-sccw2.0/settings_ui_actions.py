#!/usr/bin/env python
# wanted to move all the ui functions into their own file to make everything look nicer
# otherwise the settings_ui.py file is going to get really crowded.
from collections import OrderedDict as OD
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
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
        self.__is_loading = False
    
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
        self.addListItem(self.context.WLGwatchlistItemsList)
    
    def addAvoidListItem(self):
        #This function will add a new list item to the avoid list
        self.addListItem(self.context.avoidlistItemsList)
    
    def addListItem(self, access_object):
        #Temporarily disable sorting
        __sortingEnabled = access_object.isSortingEnabled()
        access_object.setSortingEnabled(False)
        #Create our QListWidgetItem
        item = QtGui.QListWidgetItem()
        #Set its text
        item.setText(_translate("sccw_SettingsUI", "Untitled Entry", None))
        #And add the item to the list
        access_object.addItem(item)
        #Finally we reenable sorting, if it was enabled before
        access_object.setSortingEnabled(__sortingEnabled)
    
    #Update functions for when anything is changed for a watchlist or avoidlist item.
    #These two functions save all the data for the item, not just the piece of data that has changed.
    def saveAllAvoidlistItems(self):
        #Don't operate during a load operation
        if self.__is_loading is True:
            return
        #Get the current avoidlist item
        current_avoidlist_item = self.context.avoidlistItemsList.currentItem()
        
        #Now call the saveListData() function with the avoidlist elements and objects passed
        self.saveListData(self.context.avoidListElements, current_avoidlist_item)
    
    def saveAllWatchlistItems(self):
        #Don't operate during a load operation
        if self.__is_loading is True:
            return
        current_watchlist_item = self.context.WLGwatchlistItemsList.currentItem()
        #Don't save if this is an 'Untitled Entry'
        if str(current_watchlist_item.text()) != "Untitled Entry":
            self.saveListData(self.context.watchListElements, current_watchlist_item)
        

    #These Three functions save the data associated with each watch or avoid item whenever the user switches watch items.
    #The third is the master function while the other two just provide unique data tot he master.
    def updateCurrentAvoidListSelection(self, new_listwidget_item, previous_listwidget_item):
        
        self.updateCurrentListSelection(new_listwidget_item, previous_listwidget_item, self.context.avoidListElements, self.context.SettingsManager.guiDefaults["avoidlistDefaults"])
        
    def updateCurrentWatchListSelection(self, new_listwidget_item, previous_listwidget_item):
        self.updateCurrentListSelection(new_listwidget_item, previous_listwidget_item, self.context.watchListElements, self.context.SettingsManager.guiDefaults["watchlistDefaults"])
    
    def updateCurrentListSelection(self, new_listwidget_item, previous_listwidget_item, listwidget_elements, reset_data):
        #Set the load var so nothing crappy happens
        self.__is_loading = True
        
        #Save data
        #If things go south here, its probably because its an Untitled entry or theres no entry at all.
        #We still want to reset though so we allow it to pass even if it fails
        if previous_listwidget_item is not None:
            self.saveListData(listwidget_elements, previous_listwidget_item)

        #reset listwidget
        self.clearListData(reset_data)
        
        #Finally, load new data if necessary
        if new_listwidget_item is not None:
            new_data = new_listwidget_item.data(Qt.UserRole).toPyObject()
            if new_data is not None:
                self.loadListData(new_data)
        #And set the load var again to its normal state
        
        #Set the current selection to this item to be sure
        new_listwidget_item.listWidget().setCurrentItem(new_listwidget_item)
        
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
                #We may want to now get the write function to "zero out" the form. This may be better put in its own function however.
             
        #Now we have an OrderedDict with our data to save in it, we store it inside the element using the setData() function.
        #We will be saving the data in the Qt.UserRole role to the previous qlistwidgetitem we just had selected.
        if hasattr(listwidget_item, "setData"): listwidget_item.setData(Qt.UserRole, item_save_data)
    
    def clearListData(self, reset_data):
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
    
    def loadUiState(self):
        #Takes in the data format of loadSettings() and updates the UI with the data received
        #We will go through data{} and use the access method detailed in the uiElements dictionary.
        #The two's structure are identical and so make this task extremely simple.
        
        #Load up the data
        loaded_data = self.context.SettingsManager.loadSettings()
        #We have to convert the ini option names back into the element object's name.
        converted_data = OD()
        
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
            
            #Create a new QListWidgetItem with the name item_name
            new_item = QtGui.QListWidgetItem()
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
            
    
    
    
    def saveUiState(self):
        #Takes the current state of the UI in an OrderedDict and sends it to the saveSettings() function.
        #This is only a temp save, to write the changes to disk you must call syncData() to really get it written.
        #Our return dictionary
        save_data = OD()
        #Our return dictionary will be in the form:
        #save_data[subgroupName][optionName] = data
        
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
        for cIndex in xrange(0, watchlist.count()):
            #Get our watchlist item
            cur_WL_item = watchlist.item(cIndex)
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
        for cIndex in xrange(0, avoidlist.count()):
            #Get the avoidlist item
            cur_AL_item = avoidlist.item(cIndex)
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
            if index == "KB": suffix = 0
            if index == "MB": suffix = 1
            if index == "GB": suffix = 2
        if type(index) == int:
            if index == 0: suffix = "KB"
            if index == 1: suffix = "MB"
            if index == 2: suffix = "GB"
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
    
    def browse_button_mainSavepath(self):
        caption = "Choose location to save .torrent files..."
        self.browse_button_master(self.context.ggSavepathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption)
    
    def browse_button_mainLogpath(self):
        caption = "Choose location to save logs..."
        self.browse_button_master(self.context.ggLogpathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption)
        
    
    def browse_button_cookieFile(self):
        caption = "Location of cookie file..."
        self.browse_button_master(self.context.globalCFBypassCookiefilePathTextbox, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption)
        
        
    def browse_button_mainExtProgram(self):
        caption = "Choose Program..."
        self.browse_button_master(self.context.extCmdExeLocation, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption)
        
        
    def browse_button_WLsavepath(self):
        caption = "Choose location to save .torrent files to..."
        self.browse_button_master(self.context.WLSGsavepathTextbox, QtGui.QFileDialog.AcceptSave, QtGui.QFileDialog.Directory, caption)
        
        
    def browse_button_WLextProgram(self):
        caption = "Choose Program..."
        self.browse_button_master(self.context.WLSGexternalCommandTextbox, QtGui.QFileDialog.AcceptOpen, QtGui.QFileDialog.ExistingFile, caption)
        
    
    def browse_button_master(self, access_object, main_mode, file_mode, caption):
        #Infos has extra data, like the caption
        fileDialog = QtGui.QFileDialog()
        fileDialog.AcceptMode = main_mode
        fileDialog.setFileMode(file_mode)
        if file_mode == QtGui.QFileDialog.Directory:
            chosenFile = fileDialog.getExistingDirectory(caption=caption)
        elif file_mode == QtGui.QFileDialog.ExistingFile:
            chosenFile = fileDialog.getOpenFileName(caption=caption)
        
        access_object.setText(_translate("OptionsDialog", chosenFile, None))
        
