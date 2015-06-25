#!/usr/bin/env python
# wanted to move all the ui functions into their own file to make everything look nicer
# otherwise the settings_ui.py file is going to get really crowded.
from collections import OrderedDict as OD

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
    
    def addAviodListItem(self):
        #This function will add a new list item to the avoid list
        self.addListItem(self.context.avoidlistItemsList)
    
    def addListItem(self, access_object):
        pass
    
    def updateCurrentListSelection(self, current_listwidget, previous_listwidget):
        #This can also be used for both avoid and watch lists by tying their signals into this function. The function will then get the QListWidgetItem's 
        #parent QListWidget using the function QListWidgetItem::listWidget(). It can then compare to find whether its from the avoid list or watch list. 
        pass
    
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
            #If the subgroup name is WSPECIAL or ASPECIAL we need to iterate over the itemlist and save each item's settings one by one.
            if "SPECIAL" in subgroupName:
                #current_selection_title = current_selection.text()
                continue
                
            
            
            
            #Do what we need to get the dictionary ready for use
            if subgroupName not in save_data.keys(): save_data[subgroupName] = OD()
            #Here we make up a string with our element, eval it into life, then give it to the type checker
            access_string = "self.context." + str(element)
            live_access_string = eval(access_string)
            #And now we send it to the type checker and set our save_data to its output
            if len(data_list) == 3: read_data = self.typeMatcher(live_access_string, "SLC_READ", data_list[2])
            else: read_data = self.typeMatcher(live_access_string, "READ")
            save_data[subgroupName][optionName] = read_data
        
        #We should now have a nice dictionary filled with the current state of our app. Lets send it to our save function and let it handle the rest
        self.context.SettingsManager.saveSettings(save_data)
            
    def typeMatcher(self, access_object, operation, alt_obj = None):
        #This function will match the type of the access_object provided to a dictionary and return the data requested in operation.
        #operation can be READ, WRITE or a special case called SLC_READ.
        if operation == "SLC_READ":
            #We need to concatenate the data returned from two objects
                prefix = self.typeMatcher(access_object, "READ")
                suffix_index = int(self.typeMatcher(eval("self.context." + str(alt_obj)), "READ"))
                if suffix_index == 0: suffix = "KB"
                if suffix_index == 1: suffix = "MB"
                if suffix_index == 2: suffix = "GB"
                return str(prefix) + suffix
                
                
        #Convert operation into numbers to make index easier. Read is default.
        op = 0
        if operation == "WRITE": op = 1
        
        for type_name in self.context.elementAccessMethods.keys():
            if type_name in str(type(access_object)):
                access_function = self.context.elementAccessMethods[type_name][op]
                break
        #Now we have our access function, we use getattr to return the live function
        live_function = getattr(access_object, access_function)
        return live_function()
