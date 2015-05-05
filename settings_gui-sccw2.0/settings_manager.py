from PyQt4 import QtCore

class sccwSettingsManager:
	def __init__(self, settingsfile):
		self.appSettings = QtCore.QSettings(settingsfile, QtCore.QSettings.IniFormat)

	def resetSettings(self):
		self.appSettings.clear()
		
	def saveSettings(self, data):
		#data{} is similar in structure to loadSettings()'s data
		#Each key is the subgroup name, below that is another dictionary containing a list of keys and values for that group.
		#You can feed back the data from loadSettings to saveSettings to give you an idea of the structure.
		for group in data:
			#Each key is our group name
			self.appSettings.beginGroup(group)
			for key, value in data[group]:
				#Save eack value to respective key
				self.appSettings.setValue(key, value)
			#close the group and move on to the next one
			self.appSettings.endGroup()
			
		#We also save window state data at the end
		#Begin group for basic app settings
		self.appSettings.beginGroup("WindowState")
		#Screen size and position
		self.appSettings.setValue("windowSize", data["MainWindow"].size())
		self.appSettings.setValue("windowPos", data["MainWindow"].pos())
		self.appSettings.endGroup()
		
		#Almost done, we sync the settings to the file
		self.appSettings.sync()
		
		#Lastly we update the Ui
		optionsdict = {}
		#This is where the optionsdict is set up with values from data
		#This is then passed to setupUiOptions() to update the UI with the new settings.
		#self.setupUiOptions(optionsdict)

	def loadSettings(self, data):
		returnData = {}
		#loop through data{} and get the values requested. Each key is the subgroup name.
		for key in data:
			returnData[key] = {}
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