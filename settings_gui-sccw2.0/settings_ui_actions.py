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
    
    
    def updateUi(self, data):
        #Takes in the data format of loadSettings() and updates the UI with the data received
        #We will go through data{} and use the access method detailed in the uiElements dictionary.
        #The two's structure are identical and so make this task extremely simple.
        pass
    
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
    
    def updateCurrentAvoidListSelection(self, new_listwidget, previous_listwidget):
        self.updateCurrentListSelection(new_listwidget, previous_listwidget, self.context.avoidListElements)
    
    def updateCurrentWatchListSelection(self, new_listwidget, previous_listwidget):
        self.updateCurrentListSelection(new_listwidget, previous_listwidget, self.context.watchListElements)
    
    def updateCurrentListSelection(self, new_listwidget, previous_listwidget, listToUse):
        #This function implements a save-on-switch approach to managing the itemlist and its associated data
        #We will loop through each element and save the data for each one into a copy of the OorderedDict watchListElements,
        #but with the values replaced with actual data rather than locations to store data on file.
             
        ###########
        #SAVE DATA#
        ###########
        
        #Create our OrderedDict to be stored inside the element. This will contain all the data
        item_save_data = OD()
        
        #Loop through each item in listToUse
        for element in listToUse:
            live_element = eval("self.context." + str(element))
            if len(listToUse[element]) == 3:
                #Special case for size-limit selectors. We have to save the index of the dropdown list.
                #Get data for both elements.
                prefix, suffix = self.typeMatcher(live_element, "SLC_READ", listToUse[element][2], sc=True)
                item_save_data[element] = prefix
                item_save_data[listToUse[element][2]] = suffix
            else:
                #Get our access function to read the data from the live element into our save dict
                item_save_data[element] = self.typeMatcher(live_element, "READ")()
                #We may want to now get the write function to "zero out" the form. This may be better put in its own function however.
             
        #Now we have an OrderedDict with our data to save in it, we store it inside the element using the setData() function.
        #We will be saving the data in the Qt.UserRole role to the previous listwidget we were in.
        previous_listwidget.setData(Qt.UserRole, item_save_data)
        
        
        ###########
        #LOAD DATA#
        ###########
        
        #Now that we have saved our old data, lets load up the data from the new selection, if there is any
        new_data = new_listwidget.data(Qt.UserRole).toPyObject()
        if new_data is not None:
            #Ok we do have data, so lets set the form up with this data
            for element in new_data:
                live_element = eval("self.context." + str(element))
                write_function = self.typeMatcher(live_element, "WRITE")
                #Special case for dropdown selector
                if "SuffixSelector" in element: new_data[element] = int(new_data[element])
                #And now we update the element with the new data
                write_function(new_data[element])
     
     
    def updateCurrentWatchTitle(self, text):
        current_item = self.context.WLGwatchlistItemsList.currentItem()
        current_item.setText(text)
    
    def updateCurrentAvoidTitle(self, text):
        current_item = self.context.avoidlistItemsList.currentItem()
        current_item.setText(text)
    
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
        
        
        #We should now have a nice dictionary filled with the current state of our app. Lets send it to our save function and let it handle the rest
        self.context.SettingsManager.saveSettings(save_data)
            
    def typeMatcher(self, access_object, operation, alt_obj = None, sc = False):
        #This function will match the type of the access_object provided to a dictionary and return the data requested in operation.
        #operation can be READ, WRITE or a special case called SLC_READ.
        if operation == "SLC_READ":
            #SLC_READ is used when we need both the size and suffix of our sizelimit entries in one piece of data.
            #We need to concatenate the data returned from two objects
                prefix = self.typeMatcher(access_object, "READ")()
                suffix_index = int(self.typeMatcher(eval("self.context." + str(alt_obj)), "READ")())
                if suffix_index == 0: suffix = "KB"
                if suffix_index == 1: suffix = "MB"
                if suffix_index == 2: suffix = "GB"
                if sc is True: return [prefix, suffix_index]
                else: return str(prefix) + suffix
                
                
        #Convert operation into numbers to make index easier. Read is default.
        op = 0
        if operation == "WRITE": op = 1
        
        for type_name in self.context.elementAccessMethods.keys():
            if type_name in str(type(access_object)):
                access_function = self.context.elementAccessMethods[type_name][op]
                break
        #Now we have our access function, we use getattr to return the live function
        live_function = getattr(access_object, access_function)
        return live_function
