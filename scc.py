#!/usr/bin/python
############################################################################
#    Copyright (C) 2007 by realty                                          #
#             Currently maintained/updated by TRB                          #
#    exclusively written for scc                                           #
#    some code from cancel's bot                                           #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################
__module_name__ = "SCCwatcher"
__module_version__ = "1.52"
__module_description__ = "SCCwatcher"

import xchat, os, re, string, urllib, ftplib

print "\0034",__module_name__, __module_version__,"has been loaded\003"

#the globals go here
option = {}
xchatdir = xchat.get_info("xchatdir")
color = {"white":"\0030", "black":"\0031", "blue":"\0032", "green":"\0033", "red":"\0034",
"dred":"\0035", "purple":"\0036", "dyellow":"\0037", "yellow":"\0038", "bgreen":"\0039",
"dgreen":"\00310", "green":"\00311", "lblue":"\00312", "bpurple":"\00313", "dgrey":"\00314",
"lgrey":"\00315", "close":"\003"}
def reload_vars():
	inifile = open(os.path.join(xchatdir,"scc.ini"))
	line = inifile.readline()
	while line != "":
		par1, par2 = re.split("=", line)
		option[par1] = string.strip(par2)
		line = inifile.readline()
	inifile.close
	option["watchlist"] = re.split(' ', option["watchlist"])
	option["avoidlist"] = re.split(' ', option["avoidlist"])
	print color["dgreen"], "SCCwatcher scc.ini reload successfully"
	option["service"] = 'on'
	if option["ftpenable"] == 'on':
		detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if detailscheck is None:
			print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
			option["ftpenable"] = 'off'

def load_vars():
	global option, p, sccnet
	try:
		inifile = open(os.path.join(xchatdir,"scc.ini"))
		line = inifile.readline()
		while line != "":
			par1, par2 = re.split("=", line)
			option[par1] = string.strip(par2)
			line = inifile.readline()
		inifile.close
		option["watchlist"] = re.split(' ', option["watchlist"])
		option["avoidlist"] = re.split(' ', option["avoidlist"])
		if option["ftpenable"] == 'on':
			detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
			if detailscheck is None:
				print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
				option["ftpenable"] = 'off'
		
		print color["dgreen"], "SCCwatcher scc.ini Load Success, detecting the network details, the script will be ready in", option["startdelay"], "seconds "
		#compile the regexp, do this one time only
		p = re.compile(' NEW in (.*): -> ([^\s]*.) \((.*)\) - \(http:\/\/www.sceneaccess.org\/details.php\?id=(\d+)\)(.*)')

	except EnvironmentError:
		print color["red"], "Could not open scc.ini ! put it in your "+xchatdir+" !"

#detectet the network only 30seconds after the start
def starttimer(userdata):
	global sccnet, starttimerhook
	#automatically detect the networkname
	sccnet = xchat.find_context(channel='#scc-announce')
	if starttimerhook is not None:
		xchat.unhook(starttimerhook)
		starttimerhook = None
	if sccnet is not None:
		option["service"] = 'on'
		print color["dgreen"], "Network detected succesfully, script loaded and working properly";
	else:
		option["service"] = 'notdetected'
		print color["red"], "Could not detect the correct network! Autodownloading has been disabled. Make sure you have joined #scc-announce channel and then do /sccwatcher detectnetwork"
 
starttimerhook = None
def main():
	sdelay=int(option["startdelay"]+"000")
	starttimerhook = xchat.hook_timer(sdelay, starttimer)

def verbose(which,mtext,host,port,dir):
	currloc = xchat.find_context()
	# There isnt a context-orentiated command to print, so I had to work waaaaay around. Because context commands dont carry variables, I had to place all the into a var.
	print1 = "py exec print \""+color["bpurple"]+"SCCwatcher is downloading torrent for: "+color["dgrey"]+mtext+"\""
	print2 = "py exec print \""+color["bpurple"]+"SCCwatcher is uploading torrent "+color["dgrey"]+mtext+".torrent"+color["bpurple"]+" to "+color["dgrey"]+"ftp://"+color["dgrey"]+host+":"+port+"/"+dir+"\""
	which=int(which)
	if which == 1:
		currloc.command(print1)
	if which == 2:
		currloc.command(print2)
		
def on_text(word, word_eol, userdata):
	if option["service"] != 'on':
		return
	counter = 0
	#get the context where a new message was written
	destination = xchat.get_context()
	#did the message where sent to the right net, chan and by the right bot?
	if destination.get_info('network') == sccnet.get_info('network') and destination.get_info('channel') == sccnet.get_info('channel') and word[0] == "SCC":
		matchedtext = p.match(xchat.strip(word_eol[1]))
		#the bot wrote something we can understand, we can proceed with the parsing
		if matchedtext is not None:
			#matchedtext.group(1) = MP3
			#matchedtext.group(2) = VA-Stamina_Daddy_Riddim_Aka_Gold_Spoon_Riddim_(Promo_CD)-2006-VYM
			#matchedtext.group(4) = 37518

			#check if it's in watchlist
			#length checks to make sure theres something in the list first
			wlistcheck = string.join(option["watchlist"], '')
			if len(wlistcheck) is not 0:	
				for watchlist in option["watchlist"]:
					#replace * with (.*) will see in the future if the users want the full power of regexp or if they prefer a simple * as jolly and nothing else is needed
					watchlist = watchlist.replace('*','(.*)')
					watchlist = watchlist.replace('/','\/')
					watchlist_splitted = re.split(':', watchlist)
					watchlist_splitted[0] = '^' + watchlist_splitted[0] + '$'
					watchlist_splitted[1] = '^' + watchlist_splitted[1] + '$'
					#do the check for the section and the release name
					if re.search(watchlist_splitted[1], matchedtext.group(1), re.I) and re.search(watchlist_splitted[0], matchedtext.group(2), re.I):
						counter += 1
						break
			
			#check if it should be avoided
			#length checks to make sure theres something in the list first
			alistcheck = string.join(option["avoidlist"], '')
			if len(alistcheck) is not 0:	
				for avoidlist in option["avoidlist"]:
					avoidlist = avoidlist.replace('*','')
					avoidlist = avoidlist.replace('/','\/')
					avoidlist = '^(.*)' + avoidlist + '(.*)$'
					#do the check only on the release name
					if re.search(avoidlist, matchedtext.group(2), re.I):
						counter = 0
						break
			
			#got a match!! let's download
			if counter > 0:
				downloadurl = "https://www.sceneaccess.org/download2.php/" + matchedtext.group(4) + "/" + option["passkey"] + "/" + matchedtext.group(2) + ".torrent"
				urllib.urlretrieve(downloadurl,option["savepath"] + matchedtext.group(2) + ".torrent")
				if option["verbose"] == 'on':
					verbose(1,matchedtext.group(2),'', '', '')
				# Is ftp uploading enabled in scc.ini ?
				if option["ftpenable"] == 'on':
					#try to see if the ftp details are available, if the are: upload
					ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
					if ftpdetails is not None:
						if option["verbose"] == 'on':
							verbose(2,matchedtext.group(2),ftpdetails.group(3),ftpdetails.group(4),ftpdetails.group(5))
						# ftp://user:psw@host:port/directory/torrents/
						#ftpdetails.group(1) # user
						#ftpdetails.group(2) # psw
						#ftpdetails.group(3) # host
						#ftpdetails.group(4) # port
						#ftpdetails.group(5) # directory/torrents/
						s = ftplib.FTP() # Create the ftp object
						s.connect(ftpdetails.group(3), ftpdetails.group(4)) # Connect
						s.login(ftpdetails.group(1), ftpdetails.group(2)) # Login
						if option["ftppassive"] == 'on':
							s.set_pasv(True) # Set passive-mode
						s.cwd(ftpdetails.group(5)) # Change directory
						f = open(option["savepath"] + matchedtext.group(2) + ".torrent",'rb') # Open file to send
						s.storbinary('STOR ' + matchedtext.group(2) + ".torrent", f) # Send the file
						f.close() # Close file
						s.quit() # Close ftp
					else:
						print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
						option["ftpenable"] = 'off'
		else:
			print color["red"], "WTF!!! The bot wrote something I could'nt understand "			

def more_help(command):
	command = command.lower()
	if command == 'help':
		print color["bpurple"], "Help: " + color["blue"] + "Displays all of the currently accepted commands. Can also provide additional help on individual commands: "+color["dgrey"]+"/sccwatcher help <command>"
	elif command == 'loud':
		print color["bpurple"], "Loud: " + color["blue"] + "Turns verbose output on."
	elif command == 'quiet':
		print color["bpurple"], "Quiet: " + color["blue"] + "Turns verbose output off"
	elif command == 'rehash':
		print color["bpurple"], "Rehash : " + color["blue"] + "Reloads settings from scc.ini. "+color["red"]+"WARNING:"+color["blue"]+" All temporary adds will be lost upon doing this."
	elif command == 'addwatch':
		print color["bpurple"], "Addwatch: " + color["blue"] + "Temporarily adds an item to the watchlist. This add will be lost if the rehash command is used or scc.py is reloaded. Adds must be in the form of"+color["dgrey"]+" /sccwatcher addwatch name:category"
	elif command == 'status':
		print color["bpurple"], "Status: " + color["blue"] + "Displays important settings and their current values."
	elif command == 'watchlist':
		print color["bpurple"], "Watchlist: " + color["blue"] + "Displays the current watchlist (including adds)"
	elif command == 'avoidlist':
		print color["bpurple"], "Avoidlist: " + color["blue"] + "Displays the current avoidlist"
	elif command == 'on':
		print color["bpurple"], "On: " + color["blue"] + "Enables auto downloading."
	elif command == 'off':
		print color["bpurple"], "Off: " + color["blue"] + "Disables auto downloading."
	elif command == 'addavoid':
		print color["bpurple"], "Addavoid: " + color["blue"] + "Temporarily adds an item to the avoidlist. This add will be lost if the rehash command is used or scc.py is reloaded. Adds must be in the form of"+color["dgrey"]+" /sccwatcher addavoid <word>"
	elif command == 'remwatch':
		print color["bpurple"], "Remwatch: " + color["blue"] + "Temporarily remove a watch from watchlist. Must be in the form of : "+color["dgrey"]+" /sccwatcher remwatch name:category"
	elif command == 'remavoid':
		print color["bpurple"], "Remavoid: " + color["blue"] + "Temporarily remove an entry from avoidlist. Must be in the form of : "+color["dgrey"]+" /sccwatcher remavoid <word>"
	elif command == 'ftpon':
		print color["bpurple"], "Ftpon: " + color["blue"] + "Enables FTP uploading"
	elif command == 'ftpoff':
		print color["bpurple"], "Ftpoff: " + color["blue"] + "Disables FTP upload"
	elif command == 'updateftp':
		print color["bpurple"], "Updateftp: " + color["blue"] + "Allows you to update your ftpdetails, must be in the format of:"+color["dgrey"]+" /sccwatcher ftp://user:password@server:port/directory "
	elif command == 'detectnetwork':
		print color["bpurple"], "Detectnetwork: " + color["blue"] + "Re-detects the network settings, incase when SCCwatcher couldn't detect them when it first loaded."
	elif command == 'ftpdetails':
		print color["bpurple"], "ftpdetails: " + color["blue"] + "Displays your current FTPdetails"
	else:
		print color["red"], "Unknown command, "+color["black"]+command

def update_ftp(details):
	if details is not None:
		detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", details)
		if detailscheck is not None:
			print color["blue"] + "FTPdetails have been updated successfully. Please use 'ftpon' to reenable FTP uploading."
			option["ftpdetails"] = details
		else:
			print color["red"]+"There is a problem with your ftp details, the proper format is: ftp://username:password@server:port/directory"
	
def add_avoid(item):
	if item is not None:
		print "Temporarily adding", color["bpurple"]+item,color["black"]+"to the avoidlist"
		option["avoidlist"].append(item)
	else:
		print color["red"], "Invalid entry. Add cannot be empty"

def remove_avoid(delitem):
	if delitem is not None:
		#make sure its in the avoidlist to begin with
		try:
			option["avoidlist"].index(delitem)
			print "Temporarily removing", color["bpurple"]+delitem,color["black"]+"from the avoidlist"
			option["avoidlist"].remove(delitem)
		except:
			print color["bpurple"], delitem+color["red"], "was not found in the avoidlist"
	else:
		print color["red"], "Invalid entry. Are you sure you entered something?"

def add_watch(item):
	tmp_watch = re.match("(.*):(.*)", item)
	if tmp_watch is not None:
		print "Temporarily adding", color["bpurple"]+item,color["black"]+"to the watchlist"
		option["watchlist"].append(item)
	else:
		print color["red"], "Invalid entry. Adds must be in the form of:"+color["dgrey"]+" name:category"

def remove_watch(delitem):
	del_watch = re.match("(.*):(.*)", delitem)
	if del_watch is not None:
		#make sure its even in the watchlist
		try:
			option["watchlist"].index(delitem)
			print "Temporarily removing", color["bpurple"]+delitem,color["black"]+"from the watchlist"
			option["watchlist"].remove(delitem)
		except:
			print color["bpurple"], delitem+color["red"], "was not found in the watchlist"
	else:
		print color["red"], "Invalid entry. Must be in the form of:"+color["dgrey"]+" name:category"

		
# I had to split up the on_local and the ifs because using try on all of it was causing problems
def on_local(word, word_eol, userdata):
	global option
	ftrigger = re.split(' ',word_eol[0])
	try:
		ftrigger[0]
		#Before all text was being lower()'d but I removing items is case sensitive, so this only turns the first arg to lower, leaving the other args intact
		arg1 = ftrigger.pop(1).lower()
		ftrigger.insert(1, arg1)
		help(ftrigger)
	except:
		print "No argument given"
	return xchat.EAT_ALL

def help(trigger):
	if trigger[1] == 'help':
		try:
			trigger[2]
			more_help(trigger[2])
		except:
			print color["blue"], "Current accepted commands are: "
			print color["dgrey"], "Help, Loud, Quiet, Rehash, Addwatch, Addavoid, Remwatch, Remavoid, Status, Watchlist, Avoidlist, On, Off, ftpon, ftpoff, updateftp, ftpdetails, detectnetwork" 
			print color["blue"], "Too see info on individual commands use: "+color["bpurple"]+"/sccwatcher help <command>"
	elif trigger[1] == 'ftpon':
		ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if ftpdetails is not None:
			print color["blue"]+"FTP Uploading is now enabled, use 'ftpoff' to turn it back off"
			option["ftpenable"] = 'on'
		else:
			print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. You can also you 'updateftp' to update the FTP details"
	
	elif trigger[1] == 'ftpoff':
		print color["blue"]+"FTP Uploading is now disabled, use 'ftpon' to turn it back on"
		option["ftpenable"] = 'off'
	
	elif trigger[1] == 'updateftp':
		update_ftp(trigger[2])
	
	elif trigger[1] == 'ftpdetails':
		print color["bpurple"], "Current FTPdetails are: " + color["blue"] + option["ftpdetails"]
	
	elif trigger[1] == 'detectnetwork':
		starttimer(0)
	
	elif trigger[1] == 'loud':
		print color["blue"]+"Verbose output turned on, use 'quiet' to turn it back off"
		option["verbose"] = 'on'

	elif trigger[1] == 'quiet':
		print color["blue"]+"Verbose output turned off, use 'loud' to turn it back on"
		option["verbose"] = 'off'

	elif trigger[1] == 'rehash':
		print color["blue"], "Reloading scc.ini...."
		reload_vars()

	elif trigger[1] == 'addwatch':
		add_watch(trigger[2])
		
	elif trigger[1] == 'remwatch':
		remove_watch(trigger[2])

	elif trigger[1] == 'addavoid':
		add_avoid(trigger[2])
		
	elif trigger[1] == 'remavoid':
		remove_avoid(trigger[2])

	elif trigger[1] == 'del' or trigger[1] == 'delete':
		print color["red"],"Function not yet implemented"

	elif trigger[1] == 'status':
		print color["bpurple"], "Auto downloading is: " + color["blue"] + option["service"]
		print color["bpurple"], "Start delay is set to:" + color["blue"],option["startdelay"]+ " seconds"
		print color["bpurple"], "Verbose output is: " + color["blue"] + option["verbose"]
		print color["bpurple"], "Uploading to ftp is: " + color["blue"] + option["ftpenable"]
		print color["bpurple"], "Savepath is set to: " + color["blue"] + option["savepath"]
		print color["lblue"], "Current watchlist: " + color["dgreen"] + str(option["watchlist"])
		print color["lblue"], "Current avoidlist: " + color["dred"] + str(option["avoidlist"])
	
	elif trigger[1] == 'watchlist':
		print color["dgreen"], "Current watchlist: " + str(option["watchlist"])
		
	elif trigger[1] == 'avoidlist':
		print color["dred"], "Current avoidlist: " + str(option["avoidlist"])
	
	elif trigger[1] == 'off':
		option["service"] = 'off'
		print color["red"], "Autodownloading has been turned off"

	elif trigger[1] == 'on':
		if option["service"] == 'notdetected':
			print color["red"], " Didn't detected the correct network infos! Autodownloading is disabled. Make sure you have joined #scc-announce channel and reload the script!"      
		else:
			option["service"] = 'on'
			print color["dgreen"], "Autodownloading has been turned on"
			
	else:
		print color["red"], "Unknown command, "+color["black"]+trigger[1]
   
def unload_cb(userdata):
	print "\0034",__module_name__, __module_version__,"has been unloaded\003"

xchat.hook_unload(unload_cb)

load_vars()

#The hooks go here
xchat.hook_print('Channel Message', on_text)
xchat.hook_command('SCCwatcher', on_local, help="adjust the scc.ini as you wish ")

# This gets the script movin
if (__name__ == "__main__"):
		main()

#LICENSE GPL
#Last modified 12-24-08
