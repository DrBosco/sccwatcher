#!/usr/bin/python
############################################################################
#    Copyright (C) 2009 by TRB                                             #
#                                                                          #
#    exclusively written for scc                                           #
#    some code from reality and cancel's bot                               #
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
__module_version__ = "1.69"
__module_description__ = "SCCwatcher"

import xchat, os, re, string, urllib, ftplib, time, math, threading, base64, urllib2, smtplib

#the globals go here
extra_paths = "no"
recent_list = ""
dupelist = ""
full_xpath = ""
option = {}
xchatdir = xchat.get_info("xchatdir")
color = {"white":"\00300", "black":"\00301", "blue":"\00302", "green":"\00303", "red":"\00304",
"dred":"\00305", "purple":"\00306", "dyellow":"\00307", "yellow":"\00308", "bgreen":"\00309",
"dgreen":"\00310", "green":"\00311", "lblue":"\00312", "bpurple":"\00313", "dgrey":"\00314",
"lgrey":"\00315", "close":"\003"}
def reload_vars():
	global option
	inifile = open(os.path.join(xchatdir,"scc.ini"))
	line = inifile.readline()
	while line != "":
		par1, par2 = line.split("=", 1)
		option[par1] = string.strip(par2)
		line = inifile.readline()
	inifile.close()
	option["watchlist"] = re.split(' ', option["watchlist"])
	option["avoidlist"] = re.split(' ', option["avoidlist"])
	print color["dgreen"], "SCCwatcher scc.ini reload successfully"
	option["service"] = 'on'
	if option["ftpenable"] == 'on':
		detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if detailscheck is None:
			print color["red"]+"\007There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
			option["ftpenable"] = 'off'
	try:
		option["external_command"]
	except:
		option["external_command"] = ""
	
	#convert sizelimit to bytes
	try:
		option["sizelimit"]
	except:
		option["sizelimit"] = ""
	if len(option["sizelimit"]) > 0:
		sizelim = re.match("^([0-9]{1,10})(K|k|M|m|G|g)$", option["sizelimit"])
		if sizelim is not None:
			if sizelim.group(2) == "K" or sizelim.group(2) == "k":
				mult=int(1024)
			if sizelim.group(2) == "M" or sizelim.group(2) == "m":
				mult=int(1048576)
			if sizelim.group(2) == "G" or sizelim.group(2) == "g":
				mult=int(1073741824)
			sizebytes = float(sizelim.group(1)) * mult
			option["sizelimit2"] = int(sizebytes)
		else:
			print "\007"+color["dgrey"]+option["sizelimit"]+color["red"]+" is not a valid entry for sizelimit. Valid examples: 150K, 150M, 150G"
	option["_extra_context_"] = "off"

def load_vars():
	global option, p, sccnet
	try:
		inifile = open(os.path.join(xchatdir,"scc.ini"))
		line = inifile.readline()
		while line != "":
			par1, par2 = line.split("=", 1)
			option[par1] = string.strip(par2)
			line = inifile.readline()
		inifile.close()
		option["watchlist"] = re.split(' ', option["watchlist"])
		option["avoidlist"] = re.split(' ', option["avoidlist"])
		if option["ftpenable"] == 'on':
			detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
			if detailscheck is None:
				print color["red"]+"\007There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
				option["ftpenable"] = 'off'
		#Make sure theres a trailing slash on the end of logdir and savepath
		logdir_check = re.match(r"(.*)(\\|/)$", option["logpath"])
		savepath_check = re.match(r"(.*)(\\|/)$", option["savepath"])
		if len(option["logpath"]) > 0:
			if logdir_check is None:
				warning = "\007"+color["red"]+"\007You forgot the trailing slash at the end of logdir"
				warnloc1 = xchat.find_context()
				warnloc1.prnt(warning)
		if savepath_check is None:
			warning = "\007"+color["red"]+"\007You forgot the trailing slash at the end of savepath"
			warnloc2 = xchat.find_context()
			warnloc2.prnt(warning)
		try:
			option["external_command"]
		except:
			option["external_command"] = ""
		#convert sizelimit to bytes
		try:
			option["sizelimit"]
		except:
			option["sizelimit"] = ""
		if len(option["sizelimit"]) > 0:
			sizelim = re.match("^([0-9]{1,5})(K|k|M|m|G|g)$", option["sizelimit"])
			if sizelim is not None:
				if sizelim.group(2) == "K" or sizelim.group(2) == "k":
					mult=int(1024)
				if sizelim.group(2) == "M" or sizelim.group(2) == "m":
					mult=int(1048576)
				if sizelim.group(2) == "G" or sizelim.group(2) == "g":
					mult=int(1073741824)
				sizebytes = float(sizelim.group(1)) * mult
				option["sizelimit2"] = int(sizebytes)
			else:
				print "\007"+color["dgrey"]+option["sizelimit"]+color["red"]+" is not a valid entry for sizelimit. Valid examples: 150K, 150M, 150G"
		
		print color["dgreen"], "SCCwatcher scc.ini Load Success, detecting the network details, the script will be ready in", option["startdelay"], "seconds "
		#compile the regexp, do this one time only
		p = re.compile('(.*)NEW in (.*): -> ([^\s]*.) \((.*)\) - \(http:\/\/www.sceneaccess.org\/details.php\?id=(\d+)\)(.*)')

		#Only log script load if logging is enabled
		if option["logenabled"] == "on":
			loadmsg = "\0034 "+__module_name__+" "+__module_version__+" has been loaded\003"
			logging(xchat.strip(loadmsg), "LOAD")
		
		option["_extra_context_"] = "off"
		
	except EnvironmentError:
		print color["red"], "\007Could not open scc.ini! Put it in "+xchatdir+" !"
	
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
		print color["red"], "\007Could not detect the correct network! Autodownloading has been disabled. Make sure you have joined #scc-announce channel and then do /sccwatcher detectnetwork"
 
starttimerhook = None
def main():
	sdelay=int(option["startdelay"]+"000")
	starttimerhook = xchat.hook_timer(sdelay, starttimer)

def verbose(text):
	if option["_extra_context_"] == "on":
		if option["_current_context_"] is not None:
			try:
				option["_current_context_"].prnt(text)
			except:
				errortext = "\007\00304There was an error using your set output tab, please redefine the output tab with /sccwatcher setoutput. Reseting output to normal."
				currloc = xchat.find_context()
				currloc.prnt(errortext)
				option["_extra_context_"] = "off"
		else:
			option["_extra_context_"] = "off"
			currloc = xchat.find_context()
			currloc.prnt(text)
	else:
		currloc = xchat.find_context()
		currloc.prnt(text)
	
def logging(text, operation):
	#Make sure logpath exists first, if not create it.
	logdir_is_available = os.access(option["logpath"], os.W_OK)
	if logdir_is_available is False:
		os.mkdir(option["logpath"])
	
	fullpath = option["logpath"] + "sccwatcher.log"
	current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
	text = current_time+" - "+operation+":"+text+"\n"
	scclog = open(fullpath, 'a')
	scclog.write(text)
	scclog.close()


def dir_check(xpath, cat):
	global extra_paths
	extra_paths = "yes"
	if xpath == "SCCDATE":
		# Create a dir in the DDMM format
		xpath = time.strftime("%m%d", time.localtime())
		tree = "no"
	elif xpath == "SCCGRP":
		xpath = cat
		xpath = xpath.replace('/','.')
		path = xpath.replace('-','.')
		tree = "no"
	elif xpath == "SCCGRPTREE":
		xpath = cat
		# Replace that pesky - in TV-X264 with a slash so its like the other groups
		xpath = xpath.replace('-','/')
		xpath_split = re.split('/', xpath)
		try:
			xpath_split[1]
			tree = "yes"
		except:
			tree = "no"
	else:
		tree = "no"
	
	if tree == "no":
		full_xpath = option["savepath"] + xpath + "/"
		#Check if the dir exists
		checkF_xpath = os.access(full_xpath, os.F_OK)
		#If not create it and notify the user whats going on
		if checkF_xpath is False:
			OHNOEZ = "\007"+color["bpurple"]+"SCCwatcher is creating the following dir: "+color["dgrey"]+option["savepath"]+xpath
			if option["verbose"] == 'on':
				verbose(OHNOEZ)
			if option["logenabled"] == 'on':
				logging(xchat.strip(OHNOEZ), "CREATE_DIR")
			
			os.mkdir(full_xpath)
		#Check if the DIR is writeable
		checkW_xpath = os.access(full_xpath, os.W_OK)
		if checkW_xpath is False:
			OHNOEZ = "\007"+color["bpurple"]+"SCCwatcher cannot write to the save dir: "+color["dgrey"]+option["savepath"]+xpath+". Please make sure the user running xchat has the proper permissions."
			if option["verbose"] == 'on':
				verbose(OHNOEZ)
			if option["logenabled"] == 'on':
				logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
			#disable extra paths
			extra_paths = "no"
	
	else:
		# It's too bad I cant tell python to create one dir, and extra above it if needed. I have to do it one by one.
		full_xpath1 = option["savepath"] + xpath_split[0] + "/"
		full_xpath2 = option["savepath"] + xpath_split[0] + "/" + xpath_split[1] + "/"
		#Check if the first dir exists
		checkF_xpath1 = os.access(full_xpath1, os.F_OK)
		#If not create it and notify the user whats going on
		if checkF_xpath1 is False:
			OHNOEZ = "\007"+color["bpurple"]+"SCCwatcher is creating the following dir: "+color["dgrey"]+option["savepath"]+xpath_split[0]
			if option["verbose"] == 'on':
				verbose(OHNOEZ)
			if option["logenabled"] == 'on':
				logging(xchat.strip(OHNOEZ), "CREATE_DIR")
			os.mkdir(full_xpath1)
		#Check if the first DIR is writeable
		checkW_xpath1 = os.access(full_xpath1, os.W_OK)
		if checkW_xpath1 is False:
			OHNOEZ = "\007"+color["bpurple"]+"SCCwatcher cannot write to the save dir: "+color["dgrey"]+option["savepath"]+xpath_split[0]+". Please make sure the user running xchat has the proper permissions."
			if option["verbose"] == 'on':
				verbose(OHNOEZ)
			if option["logenabled"] == 'on':
				logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
			#disable extra paths
			extra_paths = "no"
		#Check if the second dir exists
		checkF_xpath2 = os.access(full_xpath2, os.F_OK)
		#If not create it and notify the user whats going on
		if checkF_xpath2 is False:
			OHNOEZ = "\007"+color["bpurple"]+"SCCwatcher is creating the following dir: "+color["dgrey"]+ os.path.normcase(full_xpath2)
			if option["verbose"] == 'on':
				verbose(OHNOEZ)
			if option["logenabled"] == 'on':
				logging(xchat.strip(OHNOEZ), "CREATE_DIR")
			os.mkdir(full_xpath2)
		#Check if the second DIR is writeable
		checkW_xpath2 = os.access(full_xpath2, os.W_OK)
		if checkW_xpath2 is False:
			OHNOEZ = "\007"+color["bpurple"]+"SCCwatcher cannot write to the save dir: "+color["dgrey"] + os.path.normcase(full_xpath2) + ". Please make sure the user running xchat has the proper permissions."
			if option["verbose"] == 'on':
				verbose(OHNOEZ)
			if option["logenabled"] == 'on':
				logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
			#disable extra paths
			extra_paths = "no"
		full_xpath = full_xpath2
	# Return the var instead of globalizing it.
	return full_xpath

#This function also tracks individual release names for dupe protection since v1.63
def update_recent(file, dldir, size, dduration):
	global recent_list
	entry_number = str(int(len(recent_list)) + 1)
	time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
	
	formatted = color["bpurple"] + entry_number + color["black"] + " - " + color["dgrey"] + time_now + color["black"] + " - " + color["bpurple"] + file + color["black"] + " - " + color["dgrey"] + size + color["black"] + " - " + color["dgrey"] + dduration+" Seconds" + color["black"] + " - " + color["dgrey"] + os.path.normcase(dldir)
	#recent list update or initial creation
	if len(string.join(recent_list, ' ')) > 0:
		recent_list.append(formatted)
	else:
		recent_list = [formatted]
	
def update_dupe(file):
	global dupelist
	#Dupe list update or initial creation
	if len(string.join(dupelist, ' ')) > 0:
		dupelist.append(file)
	else:
		dupelist = [file]
		
	

def on_text(word, word_eol, userdata):
	#what the hell why didnt I do this before???? Enough sending vars, GLOBAL FTW!
	global matchedtext, disp_path, nicesize
	if option["service"] != 'on':
		return
	counter = 0
	# Just temp setting incase the shit hits the fan it will still sorta be correct. Shouldn't go wrong tho :D
	zxfpath = option["savepath"]
	#get the context where a new message was written
	destination = xchat.get_context()
	#did the message where sent to the right net, chan and by the right bot?
	#If your wondering what the hell xchat.strip does, it removes all color and extra trash from text. I wish the xchat python plugin devs would have documented this function, it sure would have made my job easier.
	stnick = xchat.strip(word[0])
	if destination.get_info('network') == sccnet.get_info('network') and destination.get_info('channel') == sccnet.get_info('channel') and stnick == "SCC":
		matchedtext = p.match(xchat.strip(word_eol[1]))
		#the bot wrote something we can understand, we can proceed with the parsing
		if matchedtext is not None:
			#matchedtext.group(2) = MP3
			#matchedtext.group(3) = VA-Stamina_Daddy_Riddim_Aka_Gold_Spoon_Riddim_(Promo_CD)-2006-VYM
			#matchedtext.group(5) = 37518

			#check if it's in watchlist
			#length checks to make sure theres something in the list first
			wlistcheck = string.join(option["watchlist"], '')
			if len(wlistcheck) is not 0:	
				for watchlist in option["watchlist"]:
					#replace * with (.*) will see in the future if the users want the full power of regexp or if they prefer a simple * as jolly and nothing else is needed
					watchlist = watchlist.replace('*','(.*)')
					watchlist = watchlist.replace('/','\/')
					watchlist_splitted = re.split(':', watchlist)
					#here we split off anything extra for a download dir
					#Using a try incase someone entered a watch with no colon at all (no watchlist_splitted[1]
					try:
						watchlist_splitted[1]
						download_dir = re.split(';', watchlist_splitted[1])
					except:
						this="isavar"
					# and then make sure watchlist_splitted[1] has the correct data, sans download dir
					watchlist_splitted[1] = download_dir[0]
					watchlist_splitted[0] = '^' + watchlist_splitted[0] + '$'
					watchlist_splitted[1] = '^' + watchlist_splitted[1] + '$'
					#do the check for the section and the release name
					if re.search(watchlist_splitted[1], matchedtext.group(2), re.I) and re.search(watchlist_splitted[0], matchedtext.group(3), re.I):
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
					if re.search(avoidlist, matchedtext.group(3), re.I):
						counter = 0
						break
			
			#Size details
			sizedetail = matchedtext.group(4).replace(')', '')
			sizedetail = matchedtext.group(4).replace('(', '')
			sizedetail = re.search("([0-9]{1,6}\.[0-9]{2})(.*)(M|m|K|k|G|g)(.*)", sizedetail)
			#sizedetail.group(1) = 541.34
			#sizedetail.group(3) = M
			nicesize = sizedetail.group(1)+sizedetail.group(3)
			
			# Only if we're about to download should we check size
			if counter > 0:
				if len(option["sizelimit"]) > 0:
					#Check if it's too big
					if sizedetail.group(3) == "K" or sizedetail.group(3) == "k":
						multi=int(1024)
					if sizedetail.group(3) == "M" or sizedetail.group(3) == "m":
						multi=int(1048576)
					if sizedetail.group(3) == "G" or sizedetail.group(3) == "g":
						multi=int(1073741824)
					torrent_size = float(sizedetail.group(1)) * multi
					torrent_size = int(torrent_size)
					if torrent_size > int(option["sizelimit2"]):
						# Print/Log this if needed
						sizeavoid = "\007"+color["bpurple"]+"SCCwatcher has avoided "+color["dgrey"]+matchedtext.group(3)+color["bpurple"]+" due to size constraints. "+color["blue"]+"Torrent size: "+color["dgrey"]+nicesize+color["blue"]+", Limit: "+color["dgrey"]+option["sizelimit"]
						if option["verbose"] == 'on':
							verbose(sizeavoid)
						if option["logenabled"] == 'on':
							logging(xchat.strip(sizeavoid), "AVOID")
						counter = 0
			
			#And here's the dupe check
			#only if we're about to download should we do a dupe check
			if counter > 0:
				if option["dupecheck"] == "on":
					#Check for the release name in the dupe list
					try:
						dupelist.index(matchedtext.group(3))
						counter = 0
						dupeavoid = "\007"+color["bpurple"]+"SCCwatcher has determined that "+color["dgrey"]+matchedtext.group(3)+color["bpurple"]+" is a dupe. Torrent not downloaded."
						if option["verbose"] == 'on':
							verbose(dupeavoid)
						if option["logenabled"] == 'on':
							logging(xchat.strip(dupeavoid), "DUPE")
					#if its not a dupe, rabblerabblerabble do nothing.
					except:
						notadupe="RABBLERABBLERABBLE!"
							
			#got a match!! let's download
			if counter > 0:
				#Now that we're downloading for sure, add the release name to the dupecheck list.
				update_dupe(matchedtext.group(3))
				
				downloadurl = "http://www.sceneaccess.org/downloadbig2.php/" + matchedtext.group(5) + "/" + option["passkey"] + "/" + matchedtext.group(3) + ".torrent"
				
				#Utorrent is either disabled or is working in tandom with normal download.
				if option["utorrent_mode"] == "0" or option["utorrent_mode"] == "1":
					# If theres a specified directory, run through the directory checker to make sure the dir exists and is accessable
					try:
						download_dir[1]
						# Because full_xpath is no longer global, we assign zxfpath to dir_checks return value (full_xpath)
						zxfpath = dir_check(download_dir[1], matchedtext.group(2))
					except:
						chicken = "lol" # Had to put something here :D
		
					if extra_paths == "yes":
						disp_path = zxfpath
						filename = zxfpath + matchedtext.group(3) + ".torrent"
					else:
						disp_path = option["savepath"]
						filename = option["savepath"] + matchedtext.group(3) + ".torrent"
					
					verbtext = "\007"+color["bpurple"]+"SCCwatcher is downloading torrent for: "+color["dgrey"]+matchedtext.group(3)
					if option["verbose"] == 'on':
						verbose(verbtext)
					if option["logenabled"] == 'on':
						verbtext = xchat.strip(verbtext) +" - "+ os.path.normcase(disp_path)
						logging(verbtext, "GRAB")
					#The number of passed vars has gone up in an effort to alleviate var overwrites under high load.
					download(downloadurl, filename, zxfpath, matchedtext, disp_path, nicesize, extra_paths).start()
					# The upload will be cascaded from the download thread to prevent a train wreck.
					
				# If utorrent adding is enabled, perform those operations
				if option["utorrent_mode"] == "1" or option["utorrent_mode"] == "2":
					verbtext = "\007"+color["bpurple"]+"SCCwatcher is adding torrent for " + color["dgrey"] + matchedtext.group(3) + color["bpurple"] + " to the uTorrent WebUI at " + color["dgrey"] + option["utorrent_hostname"]
					if option["verbose"] == 'on':
						verbose(verbtext)
					if option["logenabled"] == 'on':
						verbtext3 = xchat.strip(verbtext)
						logging(verbtext3, "START_UTOR_ADD")
					webui_upload(downloadurl, matchedtext, nicesize).start()
				if option["utorrent_mode"] is not "0" and option["utorrent_mode"] is not "1" and option["utorrent_mode"] is not "2":
					verbtext = "\007"+color["bpurple"]+"SCCwatcher cannot download because you have set utorrent_mode to an invalid number. Please check your scc.ini and fix this error. utorrent_mode is currently set to: " + color["dgrey"] + option["utorrent_mode"]
					verbose(verbtext)
				
	
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
	elif command == 'logon':
		print color["bpurple"], "logon: " + color["blue"] + "Enables logging to file."
	elif command == 'logoff':
		print color["bpurple"], "logoff: " + color["blue"] + "Disables logging to file."
	elif command == 'recent':
		print color["bpurple"], "recent: " + color["blue"] + "Shows a list of recently grabbed torrents. The list can be cleared with"+color["dgrey"]+" recentclear"
	elif command == 'recentclear':
		print color["bpurple"], "recentclear: " + color["blue"] + "Clears the list of recent torrent downloads"
	elif command == 'emailon':
		print color["bpurple"], "emailon: " + color["blue"] + "Turns the emailing function on. Use 'emailoff' to turn it off"
	elif command == 'emailoff':
		print color["bpurple"], "emailoff: " + color["blue"] + "Turns the emailing function off. Use 'emailon' to turn it on"
	elif command == 'setoutput':
		print color["bpurple"], "setoutput: " + color["blue"] + "Sets the currently active tab as the place for all verbose output. You can reset back to the default output by using /sccwatcher deloutput"
	elif command == 'deloutput':
		print color["bpurple"], "deloutput: " + color["blue"] + "Returns the verbose output to default (Currently active tab at the time of output). You can set a tab for output by using /sccwatcher setoutput"
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
		#Check if the list is empty
		if len(string.join(option["avoidlist"], ' ')) > 0:
			option["avoidlist"].append(item)
		else:
			option["avoidlist"] = [item]
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
		#Check if the list is empty
		if len(string.join(option["watchlist"], ' ')) > 0:
			option["watchlist"].append(item)
		else:
			option["watchlist"] = [item]
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

#Threaded download class.
class download(threading.Thread):
	def __init__(self, dlurl, flname, zxfpath, matchedtext, disp_path, nicesize, extra_paths):
		self.dlurl = dlurl
		self.flname = flname
		self.zxfpath = zxfpath
		self.matchedtext = matchedtext
		self.disp_path = disp_path
		self.nicesize = nicesize
		self.extra_paths = extra_paths
		threading.Thread.__init__(self)
	def run(self):
		#create thread-local data to further prevent var overwrites under high load
		thread_data = threading.local()
		# I'm adding in some timer things just for the hell of it
		thread_data.start_time = time.time()
		self.count = 0
		# Goto the download function
		self.download(thread_data.start_time)
		
	def check_size(self, file, stime):
		self.count += 1
		thread_data = threading.local()
		thread_data.filesize = int(os.path.getsize(file))
		#Check if the file is less than 50 bytes (shouldn't be)
		if thread_data.filesize < 50:
			#Delete the bad file
			os.remove(file)
			# Have we reached the retry limit?
			if self.count < int(option["max_dl_tries"]):
				#Sleep a second to give the server some breathing room.
				time.sleep(int(option["retry_wait"]))
				#Then download again
				self.download(stime)
			#We have reached the limit, verbose/log event and discontinue download operations.
			else:
				self.final_output(False, stime)
		# Yay we downloaded a good file, verbose/log event.
		else:
			self.final_output(True, stime)
	
	def download(self, stime):
		thread_data = threading.local()
		# And here we download, but instead of halting the main thread (and xchat), this is in its own thread.
		thread_data.dl = urllib.urlretrieve(self.dlurl, self.flname)
		# See if it grabbed it correctly
		self.check_size(self.flname, stime)
		
	def final_output(self, status, stime):
		thread_data = threading.local()
		thread_data.start_time = stime
		if status == True:
			# Calculating download duration
			thread_data.end_time = time.time()
			thread_data.duration = thread_data.end_time - thread_data.start_time
			#round off extra crap from duration to 3 digits
			thread_data.duration = str(float(round(thread_data.duration, 3)))
			#Update Recent list
			update_recent(self.matchedtext.group(3), self.disp_path, self.nicesize, thread_data.duration)
			#Print/log the confirmation of download completed and duration
			# Its annoying to see the download try number after each grab, so only put the number of retry's if there was more than 1.
			if self.count == 1:
				thread_data.verbtext3 = "\007" + color["bpurple"] + "SCCwatcher successfully downloaded torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds."
			else:
				thread_data.verbtext3 = "\007" + color["bpurple"] + "SCCwatcher successfully downloaded torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds. Total retry's: " + color["dgrey"] + str(self.count)
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext3)
			if option["logenabled"] == 'on':
				thread_data.verbtext3 = xchat.strip(thread_data.verbtext3) +" - "+ os.path.normcase(self.disp_path)
				logging(thread_data.verbtext3, "END_GRAB")
			
			#Ok now that we have the file, we can do the upload if necessary:
			#If we're doing an upload, then dont do an email or external command, as that will be handled by the upload class.
			if option["ftpenable"] == 'on':
				upload(self.flname, self.zxfpath, self.matchedtext, self.disp_path, self.extra_paths, self.nicesize).start()
			else:
				#If emailing is enabled, dont do external command as that will be handled by the email class.
				if option["smtp_emailer"] == "on":
					email(self.matchedtext, self.disp_path, self.nicesize).start()
				else:
					if option["use_external_command"] == "on":
						do_cmd(self.matchedtext, self.disp_path, self.nicesize).start()
		else:
			thread_data.verbtext3 = "\007"+color["bpurple"]+"SCCwatcher failed to downloaded torrent for "+color["dgrey"] + self.matchedtext.group(3) + color["bpurple"]+" after " +color["dgrey"]+ option["max_dl_tries"] + color["bpurple"]+" tries. Manually download at: " +color["dgrey"]+ self.dlurl
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext3)
			if option["logenabled"] == 'on':
				thread_data.verbtext3 = xchat.strip(thread_data.verbtext3) +" - "+ os.path.normcase(self.disp_path)
				logging(thread_data.verbtext3, "END_GRAB")
	
#threaded upload class
class upload(threading.Thread):
	def __init__(self, torrentname, zxfpath, matchedtext, disp_path, extra_paths, nicesize):
		self.torrentname = torrentname
		self.zxfpath = zxfpath
		self.matchedtext = matchedtext		
		self.disp_path = disp_path
		self.extra_paths = extra_paths
		self.nicesize = nicesize
		threading.Thread.__init__(self)
	#Uploading tiem nao!!!!
	def run(self):
		#create thread-local data to further prevent var overwrites under high load
		thread_data = threading.local()
		#try to see if the ftp details are available, if the are: upload
		thread_data.ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if thread_data.ftpdetails is not None:
			thread_data.verbtext2 = "\007" + color["bpurple"] + "SCCwatcher is uploading file " + color["dgrey"] + self.matchedtext.group(3) + ".torrent" + color["bpurple"] + " to " + color["dgrey"] + "ftp://" + color["dgrey"] + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5)
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext2)
			if option["logenabled"] == 'on':
				logging(xchat.strip(thread_data.verbtext2), "UPLOAD")
			# I'm adding in some timer things just for the hell of it
			thread_data.start_time2 = time.time()
			# ftp://user:psw@host:port/directory/torrents/
			#thread_data.ftpdetails.group(1) # user
			#thread_data.ftpdetails.group(2) # psw
			#thread_data.ftpdetails.group(3) # host
			#thread_data.ftpdetails.group(4) # port
			#thread_data.ftpdetails.group(5) # directory/torrents/
			thread_data.s = ftplib.FTP() # Create the ftp object
			thread_data.s.connect(thread_data.ftpdetails.group(3), thread_data.ftpdetails.group(4)) # Connect
			thread_data.s.login(thread_data.ftpdetails.group(1), thread_data.ftpdetails.group(2)) # Login
			if option["ftppassive"] == 'on':
				thread_data.s.set_pasv(True) # Set passive-mode 
			thread_data.s.cwd(thread_data.ftpdetails.group(5)) # Change directory
			if self.extra_paths == "yes":
				thread_data.f = open(self.zxfpath + self.matchedtext.group(3) + ".torrent",'rb') # Open file to send
			else:
				thread_data.f = open(option["savepath"] + self.matchedtext.group(3) + ".torrent",'rb') # Open file to send
			thread_data.s.storbinary('STOR ' + self.matchedtext.group(3) + ".torrent", thread_data.f) # Send the file
			thread_data.f.close() # Close file
			thread_data.s.quit() # Close ftp
			thread_data.end_time2 = time.time()
			thread_data.duration2 = thread_data.end_time2 - thread_data.start_time2
			#round off extra crap from duration to 3 digits
			thread_data.duration2 = str(float(round(thread_data.duration2, 3)))
			thread_data.verbtext4 = "\007" + color["bpurple"] + "SCCwatcher successfully uploaded file " + color["dgrey"] + self.matchedtext.group(3) + ".torrent" + color["bpurple"] + " to " + color["dgrey"] + "ftp://" + color["dgrey"] + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5) + color["bpurple"]+" in " + color["dgrey"]+thread_data.duration2 + color["bpurple"]+" seconds."
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext4)
			if option["logenabled"] == 'on':
				thread_data.verbtext4 = xchat.strip(thread_data.verbtext4)
				logging(thread_data.verbtext4, "END_UPLOAD")
			
		else:
			print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
			option["ftpenable"] = 'off'
		if option["smtp_emailer"] == "on":
			email(self.matchedtext, self.disp_path, self.nicesize).start()
		else:
			if option["use_external_command"] == "on":
				do_cmd(self.matchedtext, self.disp_path, self.nicesize).start()

#Threaded upload class. Thanks to backdraft for providing most of the code. Sure made my life easier. :)
class webui_upload(threading.Thread):
	def __init__(self, turl, matchedtext, nicesize):
		self.turl = turl
		self.matchedtext = matchedtext
		self.nicesize = nicesize
		threading.Thread.__init__(self)	
		
	def run(self):
		#create thread-local data to further prevent var overwrites under high load
		thread_data = threading.local()
		thread_data.torrent_url = urllib.quote(self.turl) # Escape the url
		thread_data.http_url = 'http://' + option["utorrent_hostname"] +':'+ option["utorrent_port"] + '/gui/?action=add-url&s=' + thread_data.torrent_url # Make the url
		thread_data.base64string = base64.encodestring('%s:%s' % (option["utorrent_username"], option["utorrent_password"]))[:-1] 
		thread_data.authheader =  "Basic %s" % thread_data.base64string
		# Basic Auth using base64
		#start timer
		thread_data.start_time = time.time()
		thread_data.http_data = urllib2.Request(thread_data.http_url)
		thread_data.http_data.add_header("Authorization", thread_data.authheader)
		thread_data.http_data.add_header('User-Agent','Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.0)') # Pretend we are Internet Explorer
		thread_data.opener_web = urllib2.build_opener()
		thread_data.good = 0
		try:
			thread_data.text = thread_data.opener_web.open(thread_data.http_data).read() # get the data
			thread_data.good = 1
		except:
			thread_data.error = "\007" +color["bpurple"]+"SCCwatcher encountered an HTTP error while connecting to the uTorrent WebUI at " + color["dgrey"] + option["utorrent_hostname"] + color["bpurple"] + ". Please double check the uTorrent WebUI settings in scc.ini are correct."
			verbose(thread_data.error)
			thread_data.good = 0
		if thread_data.good == 1:
			#end timer
			thread_data.end_time = time.time()
			thread_data.duration = thread_data.end_time - thread_data.start_time
			thread_data.duration = str(float(round(thread_data.duration, 3)))
			# If only uTorrent uploading is active, update the recent using WEBUI as the disp_path
			if option["utorrent_mode"] == "2":
				thread_data.webuiloc = "WEBUI-" + option["utorrent_hostname"]
				update_recent(self.matchedtext.group(3), thread_data.webuiloc, self.nicesize, thread_data.duration)
				if option["smtp_emailer"] == "on":
					email(self.matchedtext, "NONE", self.nicesize).start()
				else:
					if option["use_external_command"] == "on":
						do_cmd(self.matchedtext, "NONE", self.nicesize).start()
				
			thread_data.verbtext = "\007"+color["bpurple"]+"SCCwatcher successfully added torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " to the uTorrent WebUI at " + color["dgrey"] + option["utorrent_hostname"] + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds."
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext)
			if option["logenabled"] == 'on':
				thread_data.verbtext3 = xchat.strip(thread_data.verbtext)
				logging(thread_data.verbtext3, "END_UTOR_ADD")
		if thread_data.good == 0:
			if option["logenabled"] == 'on':
				thread_data.verbtext3 = xchat.strip(thread_data.error)
				logging(thread_data.verbtext3, "END_UTOR_ADD")
		
class email(threading.Thread):
	def __init__(self, matchedtext, disp_path, nicesize):
		self.matchedtext = matchedtext
		self.disp_path = disp_path
		self.nicesize = nicesize
		threading.Thread.__init__(self)	
	#Send tiem nao
	def run(self):
		#create thread-local data to further prevent var overwrites under high load
		thread_data = threading.local()
		#connect to the server
		try:
			thread_data.smtpconn = smtplib.SMTP(option["smtp_server"])
			#Uncomment the line below to be dazzled with all the crazy server chatter. Very spammy.
			#thread_data.smtpconn.set_debuglevel(1)
			thread_data.smtpconn.ehlo()
			thread_data.is_connected = True
			
		#If theres an error while connecting, verbose/log it
		except:
			thread_data.verbtext="\007"+color["bpurple"]+"SCCwatcher encountered an error while connecting to SMTP server, no email was sent"
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext)
			if option["logenabled"] == 'on':
				thread_data.verbtext = xchat.strip(thread_data.verbtext)
				logging(xchat.strip(thread_data.verbtext), "SMTP_FAIL")
			thread_data.is_connected = False
		#If we've gotten this far, then we should have some type of connection to the server. Now we can send our message
		#Still using try incase something else fails
		if thread_data.is_connected == True:
			#Should we start a tls session?
			if option["smtp_tls"] == "on":
				thread_data.smtpconn.starttls()
				thread_data.smtpconn.ehlo()
			#If the user gave a username/password, log in with it.
			if len(option["smtp_username"]) > 0:
				try:
					thread_data.smtpconn.login(option["smtp_username"], option["smtp_password"])
					thread_data.is_auth = True
				except:
					thread_data.verbtext="\007"+color["bpurple"]+"SCCwatcher encountered an error while authenticating with the SMTP server, no email was sent"
					if option["verbose"] == 'on':
						verbose(thread_data.verbtext)
					if option["logenabled"] == 'on':
						thread_data.verbtext = xchat.strip(thread_data.verbtext)
						logging(xchat.strip(thread_data.verbtext), "SMTP_FAIL")
					thread_data.is_auth = False
			#Otherwise just continue on without authenticating
			else:
				thread_data.is_auth = True
				
			if thread_data.is_auth == True:
				try:
					#The actual message we will be sending needs to be created with the function message_builder()
					thread_data.smtpconn.sendmail(option["smtp_from"], option["smtp_to"], self.message_builder())
					thread_data.smtpconn.close()
					thread_data.verbtext="\007"+color["bpurple"]+"SCCwatcher successfully emailed " + color["dgrey"] + option["smtp_to"]
					if option["verbose"] == 'on':
						verbose(thread_data.verbtext)
					if option["logenabled"] == 'on':
						thread_data.verbtext = xchat.strip(thread_data.verbtext)
						logging(xchat.strip(thread_data.verbtext), "SMTP_SUCCESS")
				except:
					thread_data.verbtext="\007"+color["bpurple"]+"SCCwatcher encountered an error while talking to the SMTP server, no email was sent"
					if option["verbose"] == 'on':
						verbose(thread_data.verbtext)
					if option["logenabled"] == 'on':
						thread_data.verbtext = xchat.strip(thread_data.verbtext)
						logging(xchat.strip(thread_data.verbtext), "SMTP_FAIL")
		if option["use_external_command"] == "on":
			do_cmd(self.matchedtext, self.disp_path, self.nicesize).start()

	#Here we build our email message
	def message_builder(self):
		thread_data = threading.local()
		thread_data.current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		#Here we replace all the special strings with actual data
		# Acceptable special strings are:
		# %torrent% %category% %size% %time% %dlpath% %ulpath% %utserver%
		# To see what they mean, just see below.
		thread_data.ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if thread_data.ftpdetails is not None:
			thread_data.ftpstring = "ftp://" + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5)
		else:
			thread_data.ftpstring = "BAD_FTP_DETAILS"
		thread_data.utstring = option["utorrent_hostname"] + ":" + option["utorrent_port"]
		
		thread_data.email_body = option["smtp_message"].replace('%torrent%', self.matchedtext.group(3))
		thread_data.email_body = thread_data.email_body.replace('%category%', self.matchedtext.group(2))
		thread_data.email_body = thread_data.email_body.replace('%size%', self.nicesize)
		thread_data.email_body = thread_data.email_body.replace('%time%', thread_data.current_time)
		thread_data.email_body = thread_data.email_body.replace('%dlpath%', self.disp_path)
		thread_data.email_body = thread_data.email_body.replace('%ulpath%', thread_data.ftpstring)
		thread_data.email_body = thread_data.email_body.replace('%utserver%', thread_data.utstring)
		
		thread_data.email_subject = option["smtp_subject"].replace('%torrent%', self.matchedtext.group(3))
		thread_data.email_subject = thread_data.email_subject.replace('%category%', self.matchedtext.group(2))
		thread_data.email_subject = thread_data.email_subject.replace('%size%', self.nicesize)
		thread_data.email_subject = thread_data.email_subject.replace('%time%', thread_data.current_time)
		thread_data.email_subject = thread_data.email_subject.replace('%dlpath%', self.disp_path)
		thread_data.email_subject = thread_data.email_subject.replace('%ulpath%', thread_data.ftpstring)
		thread_data.email_subject = thread_data.email_subject.replace('%utserver%', thread_data.utstring)
		
		thread_data.message = """
Subject: %s
Content-Type: text/html; charset=ISO-8859-1

<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">
<html>
<head></head>
<body>
%s
</body>
</html>		
		""" % (thread_data.email_subject, thread_data.email_body)
		thread_data.message = thread_data.message.strip()
		return thread_data.message

class do_cmd(threading.Thread):
	def __init__(self, matchedtext, disp_path, nicesize):
		self.matchedtext = matchedtext
		self.disp_path = disp_path
		self.nicesize = nicesize
		threading.Thread.__init__(self)	
	#Send tiem nao
	def run(self):
		thread_data = threading.local()
		thread_data.current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		#Here we replace all the special strings with actual data
		# Acceptable special strings are:
		# %torrent% %category% %size% %time% %dlpath% %ulpath% %utserver%
		# To see what they mean, just see below.
		thread_data.ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if thread_data.ftpdetails is not None:
			thread_data.ftpstring = "ftp://" + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5)
		else:
			thread_data.ftpstring = "BAD_FTP_DETAILS"
		thread_data.utstring = option["utorrent_hostname"] + ":" + option["utorrent_port"]
		thread_data.nice_cat = self.matchedtext.group(2).replace('/','-')
		thread_data.command_string = option["external_command"].replace('%torrent%', self.matchedtext.group(3))
		thread_data.command_string = thread_data.command_string.replace('%category%', thread_data.nice_cat)
		thread_data.command_string = thread_data.command_string.replace('%size%', self.nicesize)
		thread_data.command_string = thread_data.command_string.replace('%time%', thread_data.current_time)
		thread_data.command_string = thread_data.command_string.replace('%dlpath%', self.disp_path)
		thread_data.command_string = thread_data.command_string.replace('%ulpath%', thread_data.ftpstring)
		thread_data.command_string = thread_data.command_string.replace('%utserver%', thread_data.utstring)
		
		try:
			os.system(thread_data.command_string)
			thread_data.verbtext="\007"+color["bpurple"]+"SCCwatcher successfully ran the external command " + color["dgrey"] + thread_data.command_string
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext)
			if option["logenabled"] == 'on':
				thread_data.verbtext = xchat.strip(thread_data.verbtext)
				logging(xchat.strip(thread_data.verbtext), "EXT_CMD_SUCCESS")
		except:
			thread_data.verbtext="\007"+color["bpurple"]+"SCCwatcher encountered an error running: " + color["dgrey"] + thread_data.command_string
			if option["verbose"] == 'on':
				verbose(thread_data.verbtext)
			if option["logenabled"] == 'on':
				thread_data.verbtext = xchat.strip(thread_data.verbtext)
				logging(xchat.strip(thread_data.verbtext), "EXT_CMD_FAIL")
		
# I had to split up the on_local and the ifs because using try on all of it was causing problems
def on_local(word, word_eol, userdata):
	global option
	ftrigger = re.split(' ',word_eol[0])
	try:
		ftrigger[0]
		#Before all text was being lower()'d but remwatch and remavoid are case sensitive, so this only turns the first arg to lower, leaving the other args intact
		arg1 = ftrigger.pop(1).lower()
		ftrigger.insert(1, arg1)
		help(ftrigger)
	except:
		print "No argument given, for help type: /sccwatcher help"
	return xchat.EAT_ALL

def help(trigger):
	global recent_list, option
	try:
		option["sizelimit"]
	except:
		option["sizelimit"] = ""
		
	if len(option["sizelimit"]) > 0:
		tmp_limit_text = str(option["sizelimit"])
	else:
		tmp_limit_text = "No Limit"
	if trigger[1] == 'help':
		try:
			trigger[2]
			more_help(trigger[2])
		except:
			print color["blue"], "Current accepted commands are: "
			print color["dgrey"], "Help, Loud, Quiet, Rehash, Addwatch, Addavoid, Remwatch, Remavoid, Status, Watchlist, Avoidlist, On, Off, ftpon, ftpoff, updateftp, ftpdetails, logon, logoff, recent, recentclear, detectnetwork, emailon, emailoff, setoutput, deloutput" 
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
	
	elif trigger[1] == 'recent':
		if len(recent_list) > 0:
			for item in recent_list:
				print item
		else:
			print color["red"] + "No items in recent list."
		
	elif trigger[1] == 'recentclear':
		recent_list = []
		print color["red"] + "Recent list cleared."
	
	elif trigger[1] == 'logon':
		print color["blue"]+"Logging to file is now turned on, use 'logoff' to turn it back off"
		option["logenabled"] = 'on'
	
	elif trigger[1] == 'logoff':
		print color["blue"]+"Logging to file is now turned off, use 'logon' to turn it back on"
		option["logenabled"] = 'off'

	elif trigger[1] == 'status':
		print color["bpurple"], "SCCwatcher version " +color["blue"] + __module_version__
		print color["bpurple"], "Auto downloading is: " + color["blue"] + option["service"]
		print color["bpurple"], "Maximum redownload tries is : " + color["blue"] + option["max_dl_tries"]
		print color["bpurple"], "Delay (in seconds) between download retry is: " + color["blue"] + option["retry_wait"]
		print color["bpurple"], "Dupechecking is: " + color["blue"] + option["dupecheck"]
		print color["bpurple"], "Torrent size limit: " + color["blue"] + tmp_limit_text
		print color["bpurple"], "Recent list size: " + color["blue"] + str(len(recent_list)) + color["bpurple"] + " items."
		print color["bpurple"], "Start delay is set to:" + color["blue"],option["startdelay"]+ " seconds"
		print color["bpurple"], "Verbose output is: " + color["blue"] + option["verbose"]
		print color["bpurple"], "Using custom tab for verbose output is: " + color["blue"] + option["_extra_context_"]
		print color["bpurple"], "Logging to file is: " + color["blue"] + option["logenabled"]
		print color["bpurple"], "Uploading to ftp is: " + color["blue"] + option["ftpenable"]
		print color["bpurple"], "uTorrent WebUI Mode is: " + color["blue"] + option["utorrent_mode"]
		print color["bpurple"], "Savepath is set to: " + color["blue"] + option["savepath"]
		print color["bpurple"], "Logpath is set to: " + color["blue"] + option["logpath"]
		print color["bpurple"], "Emailing is set to: " + color["blue"] + option["smtp_emailer"]
		if option["smtp_emailer"] == "on":
			print color["bpurple"], "Email server is: " + color["blue"] + str(option["smtp_server"]) + ":" + option["smtp_port"]
			print color["bpurple"], "Email TLS is set to: " + color["blue"] + str(option["smtp_tls"])
		if option["use_external_command"] == "on":
			print color["bpurple"], "External command is: " + color["blue"] + option["external_command"].strip()
		else:
			print color["bpurple"], "External command is: " + color["blue"] + "Off"
			
		
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
	
	elif trigger[1] == 'emailoff':
		option["smtp_emailer"] = 'off'
		print color["red"], "Emailing has been turned off, use 'emailon' to turn it back on"
	
	elif trigger[1] == 'emailon':
		option["smtp_emailer"] = 'on'
		print color["red"], "Emailing has been turned on, use 'emailoff' to turn it back off"
	
	elif trigger[1] == 'setoutput':
		option["_extra_context_"] = "on"
		option["_current_context_"] = xchat.find_context()
		print color["red"] + "SCCwatcher will now use this tab for all verbose output. To change the tab, use /sccwatcher setout again in a different tab, or use /sccwatcher deloutput to go back to the original way sccwatcher outputs."
		
	elif trigger[1] == 'deloutput':
		option["_extra_context_"] = "off"
		option["_current_context_"] = None
		print color["red"], "SCCwatcher will now output to whichever tab is currently active. Use /sccwatcher setoutput to change this."
		
	else:
		print color["red"], "Unknown command, " + color["black"] + trigger[1]
		print color["red"], "For help type: /sccwatcher help"
   
def unload_cb(userdata):
	quitmsg = "\0034 "+__module_name__+" "+__module_version__+" has been unloaded\003"
	print quitmsg
	#Only log script unload if logging is enabled
	if option["logenabled"] == "on":
		logging(xchat.strip(quitmsg), "UNLOAD")



#The hooks go here
xchat.hook_print('Channel Message', on_text)
xchat.hook_command('SCCwatcher', on_local, help="adjust the scc.ini as you wish ")
xchat.hook_unload(unload_cb)

#load scc.ini
load_vars()

# This gets the script movin
if (__name__ == "__main__"):
		main()

loadmsg = "\0034 "+__module_name__+" "+__module_version__+" has been loaded\003"
print loadmsg
#LICENSE GPL
#Last modified 4-11-09
