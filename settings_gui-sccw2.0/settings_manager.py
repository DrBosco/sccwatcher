from PyQt4 import QtCore

class sccwSettingsManager:
	def __init__(self, settingsfile):
		self.appSettings = QtCore.QSettings(settingsfile, QtCore.QSettings.IniFormat)



	def loadSettings(self, data):
		returnData = {}
		#loop through data{} and get the values requested. Each key is the subgroup name.
		for key in data:
			returnData[key] = []
			self.appSettings.beginGroup(key)
			#loop through the list of values to return and get the data
			for value in data[key]:
				#Need to handle QStringLists differently
				item = self.appSettings.value(value).toPyObject()
				if type(item) is QtCore.QStringList:
					niceVal = []
					for x in xrange(len(item)):
						niceVal.append(str(item[x]))
				else:
					niceVal = str(item)
				returnData[key].append(niceVal)
			self.appSettings.endGroup()
		
		#We should have a nice dictionary with all the requested data in it so just return
		return returnData