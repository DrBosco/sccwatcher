#!/usr/bin/python
##############################################################################
#    SCCwatcher                                                              #
#                                                                            #
#    exclusively written for scc                                             #
#    some code from reality and cancel's bot                                 #
#                                                                            #
#    Copyright (C) 2008-2015  TRB                                            #
#                                                                            #
#    This program is free software; you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation; either version 2 of the License, or       #
#    (at your option) any later version.                                     #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU General Public License for more details.                            #
#    You should have received a copy of the GNU General Public License along #
#    with this program; if not, write to the Free Software Foundation, Inc., #
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.             #
#                                                                            #
##############################################################################
__module_name__ = "SCCwatcher"
__module_version__ = "1.86"
__module_description__ = "SCCwatcher"

import xchat, os, re, string, urllib, ftplib, time, threading, base64, urllib2, smtplib, subprocess, platform, socket, cookielib

#Set the timeout for all network operations here. This value is in seconds. Default is 20 seconds.
socket.setdefaulttimeout(20)

loadmsg = "\0034 "+__module_name__+" "+__module_version__+" has been loaded\003"
print loadmsg

#the globals go here
xchat.command('menu DEL SCCwatcher')
extra_paths = "no"
recent_list = ""
last5recent_list = {}
dupelist = ""
full_xpath = ""
option = {}
has_tab_data = False
sccnet = None
announce_regex = None
downloaderHeaders = None
xchatdir = xchat.get_info("xchatdir")
color = {"white":"\00300", "black":"\00301", "blue":"\00302", "green":"\00303", "red":"\00304",
"dred":"\00305", "purple":"\00306", "dyellow":"\00307", "yellow":"\00308", "bgreen":"\00309",
"dgreen":"\00310", "green":"\00311", "lblue":"\00312", "bpurple":"\00313", "dgrey":"\00314",
"lgrey":"\00315", "close":"\003"}


class sccwDownloader(urllib.FancyURLopener):
        #This is where we adjust the useragent.
        version = "Mozilla/5.0 (compatible; Python urllib; SCCwatcher; v%s)" % (__module_version__)

def reload_vars():
	global option, has_tab_data, downloaderHeaders
	#backup some values we want to keep, if they exist
	try:
		cc = option["_current_context_"]
		ec = option["_extra_context_"]
	except:
		cc = None
		ec = "off"
	#removing debug key from the options dict.
	try:
		option.pop("DEBUG")
	except:
		pass
	inifile = open(os.path.join(xchatdir,"scc.ini"))
	line = inifile.readline()
	while line != "":
		# Skip over lines with comments in them
		if line[0] != "#":
			try:
				par1, par2 = line.split("=", 1)
				option[par1] = string.strip(par2)
			except:
				#Line that doesnt conform to standards, tell the user which line fucked up (think about trying to add line numbers to the output as well to aid in finding the error)
				LOADERROR = color["bpurple"]+"SCCwatcher encountered an error in your scc.ini file. The following line caused the error: " + color["dgrey"] + str(line)
				verbose(LOADERROR)
				logging(xchat.strip(LOADERROR), "RELOAD_ERROR-INI")
		line = inifile.readline()
		
	inifile.close()
	option["watchlist"] = re.split(' ', option["watchlist"])
	option["avoidlist"] = re.split(' ', option["avoidlist"])
	print color["dgreen"], "SCCwatcher scc.ini reload successfully"
	
	#check the savepath and logpath to make sure they have the trailing slash
	if len(option["savepath"]) > 0 and option["savepath"][-1] != os.sep:
		option["savepath"] = str(option["savepath"]) + os.sep
		
	if len(option["logpath"]) > 0 and option["logpath"][-1] != os.sep:
		option["logpath"] = str(option["logpath"]) + os.sep
	
	# Before we turn on services, make sure SCC IRC server is still connected to and the announce channel exists
	if xchat.find_context(channel='#announce') is not None:
		option["service"] = 'on'
		xchat.command('menu -t1 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
	else:
		option["service"] = 'off'
		xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
		
	if option["ftpenable"] == 'on':
		detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if detailscheck is None:
			print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
			option["ftpenable"] = 'off'
			xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
	try:
		option["external_command"]
	except:
		option["external_command"] = ""
	
	#Set up debug var. If it exists use it, if not set it to off
	try:
		option["DEBUG"]
	except:
		option["DEBUG"] = "off"
	
	#convert sizelimit to bytes
	try:
		option["sizelimit"]
	except:
		option["sizelimit"] = ""
	if len(option["sizelimit"]) > 0:
		sizelim = re.match("^([0-9]{1,10})(K|k|M|m|G|g)$", option["sizelimit"])
		if sizelim is not None:
			if sizelim.group(2).lower() == "k":
				mult=int(1024)
			if sizelim.group(2).lower() == "m":
				mult=int(1048576)
			if sizelim.group(2).lower() == "g":
				mult=int(1073741824)
			sizebytes = float(sizelim.group(1)) * mult
			option["sizelimit2"] = int(sizebytes)
		else:
			print color["dgrey"]+option["sizelimit"]+color["red"]+" is not a valid entry for sizelimit. Valid examples: 150K, 150M, 150G"
	
	option["_current_context_"] = cc
	option["_extra_context_"] = ec
	
	#Check if 
	
	#Set the needed headers if the user wants to bypass cloudflare
	#Headers for our downloader. Most of them I just copied from a normal browser to ensure compatibility with browser-checkers
	if option.has_key("cookiefile") and option.has_key("useragent"):
		downloaderHeaders = {
		"User-Agent": option["useragent"],
		"Accept": "application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
		"Accept-Language": "en-US,en;q=0.8",
		"Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3"
		}
	
	
	if option["download_ssl"] == "on":
		xchat.command('menu -t1 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
	else:
		xchat.command('menu -t0 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
	
	
	if option["smtp_emailer"] == "on":
		xchat.command('menu -t1 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')
	else:
		xchat.command('menu -t0 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')

		
	if option["ftpenable"] == "on":
		xchat.command('menu -t1 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
	else:
		xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')

	if option["use_external_command"] == "on":
		xchat.command('menu -t1 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
	else:
		xchat.command('menu -t0 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
	
	if option["verbose"] == "on":
		xchat.command('menu -t1 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')
	else:
		xchat.command('menu -t0 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')

		
	if option["logenabled"] == "on":
		xchat.command('menu -t1 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')
	else:
		xchat.command('menu -t0 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')

	if option["DEBUG"] == "on":
		xchat.command('menu -p9 -t1 add "SCCwatcher/Debug output" "sccwatcher _guidebugon" "sccwatcher _guidebugoff"')
	

	if option["_extra_context_"] == "on":
		xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
	else:
		xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
		
	#Rebuild the watch/avoid lists
	xchat.command('menu DEL "SCCwatcher/Avoidlist/Temporarily Remove Avoid"')
	xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid"')
	for x in option["avoidlist"]:
		xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s"' % str(x))
		xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s/Confirm Remove" "sccwatcher remavoid %s"' % (str(x), str(x)))
	xchat.command('menu DEL "SCCwatcher/Watchlist/Temporarily Remove Watch"')
	xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch"')
	for x in option["watchlist"]:
		xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s"' % str(x))
		xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s/Confirm Remove" "sccwatcher remwatch %s"' % (str(x), str(x)))
	
	# here we check for an option that specifies what tab we should be sending the verbose output to.
	# If its blank or nonexistant then we assume the user doesnt have any preference they want to set ahead of time.
	# If it does have something, we assume its the name of the tab they want the output to go to. I'm not sure of what characters are safe to put into a tab name but the user wont be doing anything weird
	has_tab_data = False
	try:
		option["verbose_tab"]
		#Ok so the option exists, now does it have anything in it?
		if len(option["verbose_tab"]) > 0:
			#Ok there is a tab preference here, lets keep going
			has_tab_data = True
		else:
			# The option is there but its blank so the user doesn't want a tab set ahead of time
			has_tab_data = False
	except:
		#The option doesnt exist so we can assume they dont want any tab ahead of time
		has_tab_data = False
	
	#Because we are reloading the settings here, we cannot count on the delay in enabling downloading to also create the tabs for us so we do it now.
	#Ok now that we have tested the option, we can go ahead and set up the output settings if thats what is needed
	if has_tab_data == True:
		sop_outtext = color["red"] + "SCCwatcher will now use this tab for all verbose output. Use /sccwatcher anytab to go back to the original way sccwatcher outputs."
		# We have to make sure SCCwatcher knows we need extra tabs.
		option["_extra_context_"] = "on"
		option["_current_context_type_"] = "SCCTAB"
		#First we need to get a context object for SCCnet so we can be sure the new tab opens in the SCC server branch.
		# I'm not 100% sure whether this will mess up on BNC users who may not be connected straight to irc.sceneaccess.org
		# I am running through a ZNC server myself and it didn't seem to effect things. But just in case this DOES fail on someone the backup will be just looking for #sceneaccess
		scc_context = xchat.find_context(server="irc.sceneaccess.org")
		if scc_context is None:
			# If it's None we know either the connection hasnt been made to the server yet or there is a difference in someone's BNC config that obscures the actual server address.
			scc_context = xchat.find_context(channel="#sceneaccess")
		if scc_context is None:
			# If it's STILL None then this user is also only joined to one channnel. Since this is an autodownloader we will assume this channel is the scc announce channel.
			# This could possibly come back as a different server if they share the same channel names. This is just our last ditch maneuver to still use the designated output tab.
			scc_context = xchat.find_context(channel="#announce")
		#Create the new tab if we have the right context object, if not we will report the error and not create the new tab
		if scc_context:
			scc_context.command("QUERY %s" % option["verbose_tab"])
			#Set the new tab as the context to use
			option["_current_context_"] = xchat.find_context(channel="%s" % option["verbose_tab"])
			#set the context name
			option["_current_context_name_"] = option["_current_context_"].get_info("channel")
			option["_current_context_"].prnt(sop_outtext)
			xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
		else:
			OHNOEZ = color["bpurple"]+"SCCwatcher failed to create your verbose output tab because it could not find the SCC IRC server. Please make sure you are connected to the SCC IRC server and you have joined the announce channel."
			verbose(OHNOEZ)
			logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
	
def load_vars():
	global option, announce_regex, sccnet, has_tab_data, downloaderHeaders
	try:
		inifile = open(os.path.join(xchatdir,"scc.ini"))
		line = inifile.readline()
		while line != "":
			if line[0] != "#":
				try:
					par1, par2 = line.split("=", 1)
					option[par1] = string.strip(par2)
				except:
					#Line that doesnt conform to standards, tell the user which line fucked up
					LOADERROR = color["bpurple"]+"SCCwatcher encountered an error in your scc.ini file. The following line caused the error: " + color["dgrey"] + str(line)
					verbose(LOADERROR)
					logging(xchat.strip(LOADERROR), "LOAD_ERROR-INI")

			line = inifile.readline()
			
			
			
		inifile.close()
		option["watchlist"] = re.split(' ', option["watchlist"])
		option["avoidlist"] = re.split(' ', option["avoidlist"])
		if option["ftpenable"] == 'on':
			detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
			if detailscheck is None:
				print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
				option["ftpenable"] = 'off'
				xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
		#check the savepath and logpath to make sure they have the trailing slash
		if len(option["savepath"]) > 0 and option["savepath"][-1] != os.sep:
			option["savepath"] = str(option["savepath"]) + os.sep
		
		if len(option["logpath"]) > 0 and option["logpath"][-1] != os.sep:
			option["logpath"] = str(option["logpath"]) + os.sep
			
		try:
			option["external_command"]
		except:
			option["external_command"] = ""
		
		#Set up debug var. If it exists use it, if not set it to false
		try:
			option["DEBUG"]
		except:
			option["DEBUG"] = "off"
		
		#convert sizelimit to bytes
		try:
			option["sizelimit"]
		except:
			option["sizelimit"] = ""
		if len(option["sizelimit"]) > 0:
			sizelim = re.match("^([0-9]{1,5})(K|k|M|m|G|g)$", option["sizelimit"])
			if sizelim is not None:
				if sizelim.group(2).lower() == "k":
					mult=int(1024)
				if sizelim.group(2).lower() == "m":
					mult=int(1048576)
				if sizelim.group(2).lower() == "g":
					mult=int(1073741824)
				sizebytes = float(sizelim.group(1)) * mult
				option["sizelimit2"] = int(sizebytes)
			else:
				print color["dgrey"]+option["sizelimit"]+color["red"]+" is not a valid entry for sizelimit. Valid examples: 150K, 150M, 150G"
		
		# here we check for an option that specifies what tab we should be sending the verbose output to.
		# If its blank or nonexistant then we assume the user doesnt have any preference they want to set ahead of time.
		# If it does have something, we assume its the name of the tab they want the output to go to. I'm not sure of what characters are safe to put into a tab name but the user wont be doing anything weird
		has_tab_data = False
		try:
			option["verbose_tab"]
			#Ok so the option exists, now does it have anything in it?
			if len(option["verbose_tab"]) > 0:
				#Ok there is a tab preference here, lets keep going
				has_tab_data = True
			else:
				# The option is there but its blank so the user doesn't want a tab set ahead of time
				has_tab_data = False
		except:
			#The option doesnt exist so we can assume they dont want any tab ahead of time
			has_tab_data = False
			
		#Set the needed headers if the user wants to bypass cloudflare
		#Headers for our downloader. Most of them I just copied from a normal browser to ensure compatibility with browser-checkers
		if option.has_key("cookiefile") and option.has_key("useragent"):
			downloaderHeaders = {
			"User-Agent": option["useragent"],
			"Accept": "application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
			"Accept-Language": "en-US,en;q=0.8",
			"Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3"
			}
		
		
		print color["dgreen"], "SCCwatcher scc.ini Load Success, detecting the network details, the script will be ready in", option["startdelay"], "seconds "
		#compile the regexp, do this one time only
		announce_regex = re.compile('(.*)NEW in (.*): -> ([^\s]*.) \((.*)\) - \(https?:\/\/(?:www\.)?sceneaccess\.(?:org|eu)\/details(?:\.php)?\?id=(\d+)\)(.*)')
		
		#Create the menus
		#lots of ifs because we have to make sure the default values reflect whats in scc.ini
		xchat.command('menu -p-1 add SCCwatcher')
		xchat.command('menu add "SCCwatcher/Status" "sccwatcher status"')
		xchat.command('menu add "SCCwatcher/-"')
		
		if option["service"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
		
		
		if option["download_ssl"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
		
		
		if option["smtp_emailer"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')

			
		if option["ftpenable"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')

		if option["use_external_command"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
			
		if option["verbose"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')

			
		if option["logenabled"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')
		
		if option["DEBUG"] == "on":
			xchat.command('menu -t1 add "SCCwatcher/Debug output" "sccwatcher _guidebugon" "sccwatcher _guidebugoff"')
		
			
		xchat.command('menu add SCCwatcher/-')
		xchat.command('menu add SCCwatcher/Help "sccwatcher help"')
		xchat.command('menu add "SCCwatcher/Reload scc.ini" "sccwatcher rehash"')
		xchat.command('menu add "SCCwatcher/Re-Detect Network" "sccwatcher detectnetwork"')
		xchat.command('menu add SCCwatcher/-')
		xchat.command('menu add "SCCwatcher/Watchlist"')
		xchat.command('menu add "SCCwatcher/Watchlist/Print Watchlist" "sccwatcher watchlist"')
		xchat.command('menu add "SCCwatcher/Watchlist/-"')
		xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Add Watch" "sccwatcher _guiaddwatch"')
		
		xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch"')
		for x in option["watchlist"]:
			xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s"' % str(x))
			xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s/Confirm Remove" "sccwatcher remwatch %s"' % (str(x), str(x)))
		
		
		
		xchat.command('menu add "SCCwatcher/Avoidlist"')
		xchat.command('menu add "SCCwatcher/Avoidlist/Print Avoidlist" "sccwatcher avoidlist"')
		xchat.command('menu add "SCCwatcher/Avoidlist/-"')
		xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Add Avoid" "sccwatcher _guiaddavoid"')
		
		xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid"')
		for x in option["avoidlist"]:
			xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s"' % str(x))
			xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s/Confirm Remove" "sccwatcher remavoid %s"' % (str(x), str(x)))
		
		
		xchat.command('menu add "SCCwatcher/Recent Grab List"')
		xchat.command('menu add "SCCwatcher/Recent Grab List/Print Recent List" "sccwatcher recent"')
		xchat.command('menu add "SCCwatcher/Recent Grab List/Recent List"')
		xchat.command('menu -e0 add "SCCwatcher/Recent Grab List/Recent List/Last 5 Grabs" "echo"')
		xchat.command('menu add "SCCwatcher/Recent Grab List/Recent List/-')
		xchat.command('menu -e0 add "SCCwatcher/Recent Grab List/Recent List/(none)" "echo"')
		xchat.command('menu add "SCCwatcher/Recent Grab List/-"')
		xchat.command('menu add "SCCwatcher/Recent Grab List/Clear Recent List" "sccwatcher recentclear"')
		xchat.command('menu add "SCCwatcher/Verbose Output Settings"')
		xchat.command('menu add "SCCwatcher/Verbose Output Settings/Default" "sccwatcher anytab"')
		xchat.command('menu add "SCCwatcher/Verbose Output Settings/This Tab" "sccwatcher thistab"')
		xchat.command('menu add "SCCwatcher/Verbose Output Settings/SCCwatcher Tab" "sccwatcher scctab"')
		xchat.command('menu add "SCCwatcher/Verbose Output Settings/-"')
		option["_extra_context_"] = "off"
		xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
		
		about_box = '"SCCwatcher Version ' + __module_version__ + ' by TRB.'
		xchat.command('menu add SCCwatcher/-')
		xchat.command('menu add SCCwatcher/About "GUI MSGBOX "' + about_box + '""')
		#Only log script load if logging is enabled
		if option["logenabled"] == "on":
			loadmsg = "\0034 "+__module_name__+" "+__module_version__+" has been loaded\003"
			logging(xchat.strip(loadmsg), "LOAD")
	
	
	except EnvironmentError:
		print color["red"], "Could not open scc.ini! Put it in "+xchatdir+" !"
	
#detectet the network only 30seconds after the start
def starttimer(userdata):
	global sccnet, starttimerhook
	#automatically detect the networkname
	sccnet = xchat.find_context(channel='#announce')
	if starttimerhook is not None:
		xchat.unhook(starttimerhook)
		starttimerhook = None
	if sccnet is not None:
		#Now here is where we specifically check for verbose tabs and create them. It is safer doing it here because we are already sure the user has SCC open and the announce chan
		
		#Ok now that we have tested the option, we can go ahead and set up the output settings if thats what is needed
		if has_tab_data == True:
			sop_outtext = color["red"] + "SCCwatcher will now use this tab for all verbose output. Use /sccwatcher anytab to go back to the original way sccwatcher outputs."
			# We have to make sure SCCwatcher knows we need extra tabs.
			option["_extra_context_"] = "on"
			option["_current_context_type_"] = "SCCTAB"
			
			#First we need to get a context object for SCCnet so we can be sure the new tab opens in the SCC server branch.
			# I'm not 100% sure whether this will mess up on BNC users who may not be connected straight to irc.sceneaccess.org
			# I am running through a ZNC server myself and it didn't seem to effect things. But just in case this DOES fail on someone the backup will be just looking for #sceneaccess
			scc_context = xchat.find_context(server="irc.sceneaccess.org")
			if scc_context is None:
				# If it's None we know either the connection hasnt been made to the server yet or there is a difference in someone's BNC config that obscures the actual server address.
				scc_context = xchat.find_context(channel="#sceneaccess")
			if scc_context is None:
				# If it's STILL None then this user is also only joined to one channnel. Since this is an autodownloader we will assume this channel is the scc announce channel.
				# This could possibly come back as a different server if they share the same channel names. This is just our last ditch maneuver to still use the designated output tab.
				scc_context = xchat.find_context(channel="#announce")
			#Create the new tab if we have the right context object, if not we will report the error and not create the new tab
			if scc_context:
				scc_context.command("QUERY %s" % option["verbose_tab"])
				#Set the new tab as the context to use
				option["_current_context_"] = xchat.find_context(channel="%s" % option["verbose_tab"])
				#set the context name
				option["_current_context_name_"] = option["_current_context_"].get_info("channel")
				option["_current_context_"].prnt(sop_outtext)
				xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
			else:
				OHNOEZ = color["bpurple"]+"SCCwatcher failed to create your verbose output tab because it could not find the SCC IRC server. Please make sure you are connected to the SCC IRC server and you have joined the announce channel."
				verbose(OHNOEZ)
				logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
		
		#And lastly we turn on the service, update the checkbox in the menu to reflect the new status, and send a message to the user about this.
		option["service"] = 'on'
		xchat.command('menu -t1 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
		verbose(color["dgreen"] + "Network detected succesfully, script loaded and working properly")
		
	else:
		option["service"] = 'notdetected'
		xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
		print color["red"], "Could not detect the correct network! Autodownloading has been disabled. Make sure you have joined #announce channel and then do /sccwatcher detectnetwork"


starttimerhook = None
def main():
	global starttimerhook
	sdelay=int(option["startdelay"]+"000")
	starttimerhook = xchat.hook_timer(sdelay, starttimer)
	
def verbose(text):
	global option
	#Make sure verbose is enabled:
	if option["verbose"] == 'on':
		#Check if the user wants the script to beep when it prints
		if option.has_key("printalert") and option["printalert"] == "on":
			text = "\007" + text
		
		try:
			option["_extra_context_"]
		except:
			option["_extra_context_"] = "off"
			
		if option["_extra_context_"] == "on":
			if option["_current_context_"] is not None:
				context_name = option["_current_context_"].get_info("channel")
				if context_name == option["_current_context_name_"]:
					option["_current_context_"].prnt(text)
					option["_current_context_"].command("GUI COLOR 3")
					option["_current_context_"].command("GUI FLASH")
				else:
					errortext = "\00304There was an error using your set output tab, please redefine the output tab with setoutput. Reseting output to normal."
					currloc = xchat.find_context()
					currloc.prnt(errortext)
					currloc.prnt(text)
					option["_extra_context_"] = "off"
					xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
			else:
				option["_extra_context_"] = "off"
				xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
				currloc = xchat.find_context()
				currloc.prnt(text)
		else:
			currloc = xchat.find_context()
			currloc.prnt(text)
	
def logging(text, operation):
	#Check if logging has been enabled
	if option["logenabled"] == 'on':
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
	
#This class checks to make sure the directory given actually exists and creates it if not.
#It can also create directories in varius styles, e.g. SCCDATE, SCCGRP, SCCGRPTREE
class dir_check:
	def __init__(self, dldir, cat):
		self.dldir = dldir
		self.cat = cat
		#This is the base dir that the extra paths will be appended to
		self.full_path = option["savepath"]
		#This is the stuff thats going to get appended to the savepath
		self.npath = ""
		
	def check(self):
		global extra_paths
		extra_paths = "yes"
		#This will seperate all the download dir options into a list
		dir_list = re.split(";", self.dldir)
		#Now we can easily loop through all the options
		for x in dir_list:
			#Get the dir's name-to-be
			dirname = self.categorize(x)
			#Append the new dir to the eventual path:
			self.npath = os.path.join(self.npath, dirname)
		#Ok now we should have a nice list of extra dirs in self.npath, so lets split em up and start making dirs
		dir_split = self.npath.split(os.sep)
		
		#We use another list similar to npath to keep track of our current dir.
		#This list also contains the savepath
		cur_dir = option["savepath"]
		for x in dir_split:
			cur_dir = os.path.join(cur_dir, x)
			self.create_dir(cur_dir)
		
		#And finally, return the entire new savepath
		self.full_path = os.path.join(self.full_path, self.npath)
		#DONT FORGET THE TRAILING SLASH!!!!
		self.full_path = self.full_path + os.sep
		return self.full_path
			
	def categorize(self, xpath):
		if xpath == "SCCDATE":
			# Create a dir in the DDMM format
			xpath = time.strftime("%m%d", time.localtime())
			
		if xpath == "SCCGRP":
			xpath = self.cat
			xpath = xpath.replace('/','.')
			xpath = xpath.replace('-','.')
			
		if xpath == "SCCGRPTREE":
			xpath = self.cat
			# Replace that pesky - in TV-X264 with a slash so its like the other groups
			xpath = xpath.replace('-', os.sep)
			#Replace any forward slashes with the correct versions for the current OS
			xpath = xpath.replace('/', os.sep)
			
		return xpath
	
	def create_dir(self, xpath):
		global extra_paths
		#Check if the dir exists
		checkF_xpath = os.access(xpath, os.F_OK)
		#If it doesn't, create it and notify the user whats going on
		if checkF_xpath is False:
			OHNOEZ = color["bpurple"]+"SCCwatcher is creating the following dir: " + color["dgrey"] + xpath
			verbose(OHNOEZ)
			logging(xchat.strip(OHNOEZ), "CREATE_DIR")
			os.makedirs(xpath)
			
		#Check if the DIR is writeable
		checkW_xpath = os.access(xpath, os.W_OK)
		if checkW_xpath is False:
			OHNOEZ = color["bpurple"]+"SCCwatcher cannot write to the save dir: "+color["dgrey"]+xpath+color["bpurple"]+". Please make sure the user running xchat has the proper permissions."
			verbose(OHNOEZ)
			logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
			#disable extra paths
			extra_paths = "no"


def update_recent(file, dldir, size, dduration):
	global recent_list, last5recent_list
	entry_number = str(int(len(recent_list)) + 1)
	time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
	
	formatted = color["bpurple"] + entry_number + color["black"] + " - " + color["dgrey"] + time_now + color["black"] + " - " + color["bpurple"] + file + color["black"] + " - " + color["dgrey"] + size + color["black"] + " - " + color["dgrey"] + dduration+" Seconds" + color["black"] + " - " + color["dgrey"] + os.path.normcase(dldir)
	#recent list update or initial creation
	if len(string.join(recent_list, ' ')) > 0:
		recent_list.append(formatted)
	else:
		recent_list = [formatted]
	
	#And heres where we update the menu items
	#Check the size of the menu so far
	menu_size = len(last5recent_list)
	if menu_size == 0:
		xchat.command('menu DEL "SCCwatcher/Recent Grab List/Recent List/(none)')
		last5recent_list["1"] = file
	
	elif menu_size < 5:
		entry = str(menu_size + 1)
		last5recent_list[entry] = file
	else:
		#Cut the first one, and move all others down. Then add the new one to the end.
		xchat.command('menu DEL "SCCwatcher/Recent Grab List/Recent List/%s' % last5recent_list["1"])
		del(last5recent_list["1"])
		n = 1
		while n < 5:
			cnum = str(n+1)
			enum = str(n)
			last5recent_list[enum] = last5recent_list[cnum]
			n += 1
		last5recent_list["5"] = file
	xchat.command('menu -e0 add "SCCwatcher/Recent Grab List/Recent List/%s" "echo"' % file)
	


def update_dupe(file):
	global dupelist
	#Dupe list update or initial creation
	if len(string.join(dupelist, ' ')) > 0:
		dupelist.append(file)
	else:
		dupelist = [file]
		
	

def on_text(word, word_eol, userdata):
	# word[0] = The username of the person who sent the message
	# word[1] = The text of the message
	# word[2] = The channel rank of the user, i.e. + % @ & or ~
	# word_eol[0] = Username + message text + user rank all on a single line.
	# word_eol[1] = Message text + user rank all on a single line
	# word_eol[2] = User rank (None, +, %, ~, and others)
	#
	# Userdata contains any special flags for bypassing and testing
	
	can_continue = False
	
	# Make sure sccnet is valid if this isn't a manual download request
	if userdata == "BYPASS" or userdata == "TESTING":
		pass
	elif option["service"] == "on":
		# We use try/except as a safe way to test whether or not a variable exists and has what we want
		try:
			#Test for a specific method we will need
			sccnet.get_info('network')
		except:
			# Somehow sccnet is no longer an active context object so we need to disable autodownloading to prevent any errors
			option["service"] = "off"
			# And update the menu item's checkbox
			xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
			# Report the error
			net_error = [color["red"] + "SCCwatcher had a problem using the detected network settings. Please redetect the network settings through the SCCwatcher menu or with the command: " + color["dgrey"] + "/sccwatcher detectnetwork"]
			net_error.append(color["red"] + "Autodownloading has been disabled, please redetect your network settings to enable again.")
			for x in net_error:
				verbose(x)
			# Finally we return and stop execution. Next time we get here the service will be disabled or the user will have reenabled it already.
			return
	
	#If we are manually downloading, we don't care if the service is enabled. The user requested specifically to download.
	if userdata == "BYPASS" or userdata == "TESTING":
		pass
	elif option["service"] != 'on':
		return
	
	counter = 0
	# Just temp setting incase the shit hits the fan it will still sorta be correct. Shouldn't go wrong tho :D
	zxfpath = option["savepath"]
	#get the context where a new message was written
	#If this is a manual add then we just bypass this
	if userdata == "BYPASS" or userdata == "TESTING":
		pass
	else:
		destination = xchat.get_context()
	#did the message where sent to the right net, chan and by the right bot?
	#If your wondering what the hell xchat.strip does, it removes all color and extra trash from text. I wish the xchat python plugin devs would have documented this function, it sure would have made my job easier.
	#If this is a manual add then we just bypass this
	if userdata == "BYPASS" or userdata == "TESTING":
		pass
	else:
		stnick = xchat.strip(word[0])
	if userdata == "BYPASS" or userdata == "TESTING":
		can_continue = True
	elif destination.get_info('network') == sccnet.get_info('network') and destination.get_info('channel') == sccnet.get_info('channel') and stnick == "SCC":
		can_continue = True
	
	
	if can_continue == True:
		if userdata == "BYPASS" or userdata == "TESTING":
			#If we are manually adding then use word as the regex object.
			matchedtext = word
			word = ['MANUAL_TEST', matchedtext.group(0), '']
		else:
			matchedtext = announce_regex.match(xchat.strip(word[1]))
		#the bot wrote something we can understand, we can proceed with the parsing
		if matchedtext is not None:
			if option["DEBUG"] == "on":
				DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Got good announce line, starting download. LINE: " + color["dgrey"] + str(word[1])
				verbose(DEBUG_MESSAGE)
				logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				
			
			#matchedtext.group(2) = MP3
			#matchedtext.group(3) = VA-Stamina_Daddy_Riddim_Aka_Gold_Spoon_Riddim_(Promo_CD)-2006-VYM
			#matchedtext.group(5) = 37518

			#check if it's in watchlist
			#length checks to make sure theres something in the list first
			wlistcheck = string.join(option["watchlist"], '')
			
			if len(wlistcheck) is not 0:	
				for watchlist in option["watchlist"]:
					#replace * with (.*) will see in the future if the users want the full power of regexp or if they prefer a simple * as jolly and nothing else is needed
					watchlist = watchlist.replace('.','\.')
					watchlist = watchlist.replace('*','(.*)')
					watchlist = watchlist.replace('/','\/')
					watchlist_splitted = re.split(':', watchlist)
					#Here we're going to search the watch for anything extra like a tag or a download dir
					#Using a try incase someone entered a watch with no colon at all (no watchlist_splitted[1]
					dldir_extra = None
					tag_extra = None
					nice_tag_extra = None
					download_dir = None
					try:
						watchlist_splitted[1]
						dldir_extra = re.search(";(.*)", watchlist_splitted[1])
						tag_extra = re.search("\[(.*)\]", watchlist_splitted[1])
					except:
						pass
					#Now lets see if we found anything
					if dldir_extra is not None:
						#we got a dl dir for sure, lets make sure theres no tag in it too.
						if tag_extra is not None:
							#ok so we have a tag stuck in there too, lets cut the tag out and set the downloaddir var.
							download_dir =  dldir_extra.group(1).replace(tag_extra.group(0), "")
							nice_tag_extra = tag_extra.group(1)
						else:
							#ok so we don't have a tag, so just set the var to dldir_extra
							download_dir = dldir_extra.group(1)
						#Now we clean up watchlist_splitted[1]
						watchlist_splitted[1] = watchlist_splitted[1].replace(dldir_extra.group(0), "")
					#No extra download dir so check if there is a tag
					elif tag_extra is not None:
						#Ok we gots a tag at least, so set the tag var and clean up watchlist_splitted[1]
						nice_tag_extra = tag_extra.group(1)
						watchlist_splitted[1] = watchlist_splitted[1].replace(tag_extra.group(0), "")
					#Now after the above we should have 2 vars with nicely formatted data inside. 
					# download_dir is either None if no dldir, or is a string containing the extra dir(s)
					# nice_tag_extra is either None if no tag, or is a string of the tag
					
					#Add some stuff for the regex searches
					watchlist_splitted[0] = '^' + watchlist_splitted[0] + '$'
					watchlist_splitted[1] = '^' + watchlist_splitted[1] + '$'
					#do the check for the section and the release name. re.I means the search is case insensitive
					if re.search(watchlist_splitted[1], matchedtext.group(2), re.I) and re.search(watchlist_splitted[0], matchedtext.group(3), re.I):
						counter += 1
						if option["DEBUG"] == "on":
							DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Matched release to watch. Matched watchlist entry: " + color["dgrey"] + str(watchlist)
							verbose(DEBUG_MESSAGE)
							logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
						break
					else:
						#This 'else' is only really here for debug purposes.
						if option["DEBUG"] == "on":
							DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Failed to match watchlist entry. Failed watchlist entry: " + color["dgrey"] + str(watchlist)
							verbose(DEBUG_MESSAGE)
							logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				
					
			#check if it should be avoided
			#length checks to make sure theres something in the list first
			alistcheck = string.join(option["avoidlist"], '')
			if len(alistcheck) != 0 and userdata != "BYPASS" and counter > 0:	
				for avoidlist in option["avoidlist"]:
					avoidlist = avoidlist.replace('.','\.')
					avoidlist = avoidlist.replace('*','')
					avoidlist = avoidlist.replace('/','\/')
					avoidlist = '^(.*)' + avoidlist + '(.*)$'
					#do the check only on the release name
					if re.search(avoidlist, matchedtext.group(3), re.I):
						counter = 0
						if option["DEBUG"] == "on":
							DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Matched rls to entry in avoidlist. Download operation stopped. Matched avoidlist entry: " + color["dgrey"] + str(avoidlist)
							verbose(DEBUG_MESSAGE)
							logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
						break
					else:
						if option["DEBUG"] == "on":
							DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Failed to match avoidlist entry with rls. Avoidlist entry: " + color["dgrey"] + str(avoidlist)
							verbose(DEBUG_MESSAGE)
							logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
			
			#Size details
			sizedetail = matchedtext.group(4).replace(')', '')
			sizedetail = sizedetail.replace('(', '')
			sizedetail = re.search("([0-9]{1,6}\.[0-9]{1,2})(.*)(M|m|K|k|G|g)B?(.*)", sizedetail)
			#sizedetail.group(1) = 541.34
			#sizedetail.group(3) = M
			nicesize = sizedetail.group(1)+sizedetail.group(3)
			# Only if we're about to download should we check size
			if counter > 0 and userdata != "BYPASS":
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
						sizeavoid = color["bpurple"]+"SCCwatcher has avoided "+color["dgrey"]+matchedtext.group(3)+color["bpurple"]+" due to size constraints. "+color["blue"]+"Torrent size: "+color["dgrey"]+nicesize+color["blue"]+", Limit: "+color["dgrey"]+option["sizelimit"]
						verbose(sizeavoid)
						logging(xchat.strip(sizeavoid), "AVOID")
						counter = 0
			
			#And here's the dupe check
			#only if we're about to download should we do a dupe check
			if counter > 0:
				if option["dupecheck"] == "on" and userdata != "BYPASS":
					#Check for the release name in the dupe list
					try:
						dupelist.index(matchedtext.group(3))
						counter = 0
						dupeavoid = color["bpurple"]+"SCCwatcher has determined that "+color["dgrey"]+matchedtext.group(3)+color["bpurple"]+" is a dupe. Torrent not downloaded."
						verbose(dupeavoid)
						logging(xchat.strip(dupeavoid), "DUPE")
					#if its not a dupe, rabblerabblerabble do nothing.
					except:
						if option["DEBUG"] == "on":
							DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Release was not found in dupe list."
							verbose(DEBUG_MESSAGE)
							logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
							
			#got a match!! let's download
			if (counter > 0 or userdata == "BYPASS") and userdata != "TESTING":
				#Now that we're downloading for sure, add the release name to the dupecheck list.
				update_dupe(matchedtext.group(3))
				if option["DEBUG"] == "on":
					DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Added the following release to dupe list: " + color["dgrey"] + str(matchedtext.group(3))
					verbose(DEBUG_MESSAGE)
					logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
						
				#And set the download url. If download_ssl is on, generate an ssl url instead.
				if option["download_ssl"] == "on":
					#downloadurl = "https://www.sceneaccess.org/downloadbig2.php/" + matchedtext.group(5) + "/" + option["passkey"] + "/" + matchedtext.group(3) + ".torrent"
					downloadurl = "https://www.sceneaccess.eu/download/" + matchedtext.group(5) + "/" + option["passkey"] + "/" + matchedtext.group(3) + ".torrent"
					
					if option["DEBUG"] == "on":
						DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Using the following SSL download url: " + color["dgrey"] + str(downloadurl)
						verbose(DEBUG_MESSAGE)
						logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
					
				else:
					#downloadurl = "http://www.sceneaccess.org/downloadbig2.php/" + matchedtext.group(5) + "/" + option["passkey"] + "/" + matchedtext.group(3) + ".torrent"
					downloadurl = "http://www.sceneaccess.eu/download/" + matchedtext.group(5) + "/" + option["passkey"] + "/" + matchedtext.group(3) + ".torrent"
					
					if option["DEBUG"] == "on":
						DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Using the following non-SSL download url: " + color["dgrey"] + str(downloadurl)
						verbose(DEBUG_MESSAGE)
						logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
					
				#And make the nice_tag_extra a string, since later it will be needed in string format, and we wont be needing its boolean type anymore anyway.
				nice_tag_extra = str(nice_tag_extra)
				#Utorrent is either disabled or is working in tandom with normal download.
				if option["utorrent_mode"] == "0" or option["utorrent_mode"] == "1":
					# If theres a specified directory, run through the directory checker to make sure the dir exists and is accessable
					if download_dir is not None:
						# Because full_xpath is no longer global, we assign zxfpath to dir_checks return value (full_xpath)
						dircheck_obj = dir_check(download_dir, matchedtext.group(2))
						zxfpath = dircheck_obj.check()
					
					if extra_paths == "yes":
						disp_path = zxfpath
						filename = zxfpath + matchedtext.group(3) + ".torrent"
					else:
						disp_path = option["savepath"]
						filename = option["savepath"] + matchedtext.group(3) + ".torrent"
					
					verbtext = color["bpurple"]+"SCCwatcher is downloading torrent for: "+color["dgrey"]+matchedtext.group(3)
					verbose(verbtext)
					verbtext = xchat.strip(verbtext) +" - "+ os.path.normcase(disp_path)
					logging(verbtext, "GRAB")
					#Set the tray text
					xchat.command('TRAY -t "SCCwatcher has grabbed a new torrent"')
					#The number of passed vars has gone up in an effort to alleviate var overwrites under high load.
					download(downloadurl, filename, zxfpath, matchedtext, disp_path, nicesize, extra_paths, nice_tag_extra).start()
					# The upload will be cascaded from the download thread to prevent a train wreck.
					
				# If utorrent adding is enabled, perform those operations
				if option["utorrent_mode"] == "1" or option["utorrent_mode"] == "2":
					verbtext = color["bpurple"]+"SCCwatcher is adding torrent for " + color["dgrey"] + matchedtext.group(3) + color["bpurple"] + " to the uTorrent WebUI at " + color["dgrey"] + option["utorrent_hostname"]
					verbose(verbtext)
					verbtext3 = xchat.strip(verbtext)
					logging(verbtext3, "START_UTOR_ADD")
					webui_upload(downloadurl, matchedtext, nicesize, nice_tag_extra).start()
				if option["utorrent_mode"] != "0" and option["utorrent_mode"] != "1" and option["utorrent_mode"] != "2":
					verbtext = color["bpurple"]+"SCCwatcher cannot download because you have set utorrent_mode to an invalid number. Please check your scc.ini and fix this error. utorrent_mode is currently set to: " + color["dgrey"] + option["utorrent_mode"]
					verbose(verbtext)
			
			elif userdata == "TESTING" and counter > 0:
				verbose_text = color["bpurple"] + "SCCwatcher would have downloaded that release."
				verbose(verbose_text)
					
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
		print color["bpurple"], "setoutput: " + color["blue"] + "This command has been depreciated. You can now use anytab, thistab, or scctab."
	elif command == 'deloutput':
		print color["bpurple"], "deloutput: " + color["blue"] + "This command has been depreciated. You can now use anytab to reset the verbose output back to default."
	elif command == 'anytab':
		print color["bpurple"], "anytab: " + color["blue"] + "Changes the verbose output to be any currently active tab at the time of printing."
	elif command == 'thistab':
		print color["bpurple"], "thistab: " + color["blue"] + "Changes the verbose output to be the tab this command was used in. This will not change unless you use the anytab command."
	elif command == 'scctab':
		print color["bpurple"], "scctab: " + color["blue"] + "Creates a tab named SCCwatcher and directs all verbose output to it. This will not change unless you use the anytab command, or close the SCCwatcher tab."
	elif command == 'sslon':
		print color["bpurple"], "sslon: " + color["blue"] + "This command will enable SSL downloading, which will download all torrents over an encrypted HTTPS connection. This may increase the amount of time it takes to grab a torrent."
	elif command == 'ssloff':
		print color["bpurple"], "ssloff: " + color["blue"] + "This command disables the SSL downloading feature, forcing SCCwatcher to download all torrents using an unencrypted HTTP connection."
	elif command == 'cmdon':
		print color["bpurple"], "cmdon: " + color["blue"] + "This will enable the execution of a specified external command, as configured in scc.ini."
	elif command == 'cmdoff':
		print color["bpurple"], "cmdoff: " + color["blue"] + "This will disable the execution of a specified external command."
	elif command == 'manualadd':
		print color["bpurple"], "manualadd: " + color["blue"] + "This command allows you to manually download a torrent by pasting its announcement text (the entire line, start to finish) from #announce. SCCwatcher will then download and upload/save the torrent according to the way your configuration is set."
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
		#Add to the menu
		xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s"' % str(item))
		xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s/Confirm Remove" "sccwatcher remavoid %s"' % (str(item), str(item)))
	else:
		print color["red"], "Invalid entry. Add cannot be empty"

def remove_avoid(delitem):
	if delitem is not None:
		#make sure its in the avoidlist to begin with
		try:
			option["avoidlist"].index(delitem)
			print "Temporarily removing", color["bpurple"]+delitem,color["black"]+"from the avoidlist"
			option["avoidlist"].remove(delitem)
			#remove the menu item
			xchat.command('menu DEL "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s/Confirm Remove"' % str(delitem))
			xchat.command('menu DEL "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s"' % str(delitem))
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
		#Add to the menu
		xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s"' % str(item))
		xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s/Confirm Remove" "sccwatcher remwatch %s"' % (str(item), str(item)))
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
			
			xchat.command('menu DEL "SCCwatcher/Watchlist/Temporarily Remove Watch/%s"' % str(delitem))
			xchat.command('menu DEL "SCCwatcher/Watchlist/Temporarily Remove Watch/%s/Confirm Remove"' % str(delitem))
		except:
			print color["bpurple"], delitem+color["red"], "was not found in the watchlist"
	else:
		print color["red"], "Invalid entry. Must be in the form of:"+color["dgrey"]+" name:category"


#This decoder class was borrowed from:
# http://buffis.com/2007/07/28/bittorrent-bencode-decoder-in-python-using-30-lines-of-code/
#I take absolutely no credit for anything but copy and pasting that code here and adding the part in __init__ where it reads the provided file into self.data.
class Decoder:
	def __init__(self, file):
		self.readme = open(file, 'rb')
		self.data = self.readme.read()
		self.readme.close()
		self.ptr = 0
	def _cur(self): return self.data[self.ptr]
	def _get(self, x):
		self.ptr += x
		return self.data[self.ptr-x:self.ptr]
	def _get_int_until(self, c):
		num = int(self._get(self.data.index(c, self.ptr)-self.ptr))
		self._get(1) # kill extra char
		return num
	def _get_str(self): return self._get(self._get_int_until(":"))
	def _get_int(self): return self._get_int_until("e")
	def decode(self):
		i = self._get(1)
		if i == "d":
			r = {}
			while self._cur() != "e":
				key = self._get_str()
				val = self.decode()
				r[key] = val
			self._get(1)
		elif i == "l":
			r = []
			while self._cur() != "e": r.append(self.decode())
			self._get(1)
		elif i == "i": r = self._get_int()
		elif i.isdigit():
			self._get(-1) # reeeeewind
			r = self._get_str()
		return r

#Threaded download class.
class download(threading.Thread):
	def __init__(self, dlurl, flname, zxfpath, matchedtext, disp_path, nicesize, extra_paths, nice_tag_extra):
		self.dlurl = dlurl
		self.flname = flname
		self.zxfpath = zxfpath
		self.matchedtext = matchedtext
		self.disp_path = disp_path
		self.nicesize = nicesize
		self.extra_paths = extra_paths
		self.nice_tag_extra = nice_tag_extra
		threading.Thread.__init__(self)
	def run(self):
		#create thread-local data to further prevent var overwrites under high load
		thread_data = threading.local()
		# I'm adding in some timer things just for the hell of it
		thread_data.start_time = time.time()
		#self.count keeps track of how many tries sccwatcher has made to grab the file.
		self.count = 0
		# Goto the download function
		self.download(thread_data.start_time)
		
	def check_valid(self, tfile, stime):
		#Add to the count since we just tried to download.
		self.count += 1
		thread_data = threading.local()
		thread_data.need_cf_bypass = False
		
		#Set to false first as a precaution incase something fails.
		thread_data.torrent_is_valid = False
		
		thread_data.filesize = int(os.path.getsize(tfile))
		#Check if the file is less than 100 bytes (shouldn't be).
		#Using 100 bytes as a size just to weed out empty files and other small-size type corruptions.
		#This is only the first stage of corrupt download detection
		if thread_data.filesize < 100:
			thread_data.torrent_is_valid = False
			
			if option["DEBUG"] == "on":
				DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Downloaded torrent is smaller than 100 bytes. Actual file size: " + color["dgrey"] + str(thread_data.filesize)
				verbose(DEBUG_MESSAGE)
				logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
					
		# Second stage in corruption detection, bencode check
		else:
			#To use the bencode checking class we just have to pass it a variable containing the full path to the .torrent file to be checked.
			thread_data.torrent_file_validation = Decoder(tfile)
			#Now we decode it to test its validity
			try:
				thread_data.torrent_file_validation.decode()  # We do this in a try/except because the bencode class just throws an exception when the torrent is invalid. 
				thread_data.torrent_is_valid = True           # So if we get this far it means the bencoder class was able to validate the torrent.
				
			except:
				thread_data.torrent_is_valid = False  # A thown exception means this .torrent isn't valid for one reason or another.
				
				if option["DEBUG"] == "on":
					DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Torrent file failed bencode check. Checking for cloudflare interference..."
					verbose(DEBUG_MESSAGE)
					logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				cfcheck = open(tfile, 'r')
				tcheck = cfcheck.read()
				cfcheck.close()
				#Look for cloudflare
				cf_req_reg = re.search("cloudflare", tcheck, re.IGNORECASE)
				if cf_req_reg is not None:
					#We got some cloudflare business so we need to do the bypass to get it working.
					thread_data.need_cf_bypass = True
					if option["DEBUG"] == "on":
						DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Cloudflare interference verified. Using cloudflare workaround next try..."
						verbose(DEBUG_MESSAGE)
						logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
		
		
		if thread_data.torrent_is_valid == False:
		#Delete the bad file
			os.remove(tfile)
			# Have we reached the retry limit?
			if self.count < int(option["max_dl_tries"]):
				#Sleep a second to give the server some breathing room.
				time.sleep(int(option["retry_wait"]))
				#Then download again
				self.download(stime, thread_data.need_cf_bypass)
			#We have reached the limit, verbose/log event and discontinue download operations.
			else:
				self.final_output(False, stime)
		else:
			self.final_output(True, stime)
		
	def download(self, stime, req=False):
		thread_data = threading.local()
		
		if option["DEBUG"] == "on":
			DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Starting download process."
			verbose(DEBUG_MESSAGE)
			logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				
		
		# And here we download. This wont hold up the main thread because this class is in a subthread,
		#Using a try-except here incase urlretrieve has problems
		try:
			#If we have the option, use the cookiefile and bypass the cloudflare protection.
			if option.has_key("cookiefile") and len(option["cookiefile"]) > 2 and option.has_key("useragent") and len(option["useragent"]) > 5 and req is True:
				
				#DBG
				if option["DEBUG"] == "on":
					DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Found cookiefile and useragent option, length checks good."
					verbose(DEBUG_MESSAGE)
					logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				#END DBG
				
				
				thread_data.cookie_path = option["savepath"] + option["cookiefile"]
				thread_data.cookie_jar = cookielib.MozillaCookieJar()
				thread_data.cookie_jar.load(thread_data.cookie_path)
				thread_data.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(thread_data.cookie_jar))
				urllib2.install_opener(thread_data.opener)
				thread_data.request = urllib2.Request(self.dlurl, None, downloaderHeaders)
				thread_data.connection = urllib2.urlopen(thread_data.request)
				with open(self.flname, 'wb') as thread_data.savefile:
					thread_data.savefile.write(thread_data.connection.read())
				thread_data.savefile.close()
				thread_data.connection.close()
				
				#DBG
				if option["DEBUG"] == "on":
					DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Finished downloading and saved to file."
					verbose(DEBUG_MESSAGE)
					logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				#END DBG
				
			else:
				
				#DBG
				if option["DEBUG"] == "on":
					DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: No cookiefile or useragent option or length checks failed."
					verbose(DEBUG_MESSAGE)
					logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				#END DBG	
					
				#Download normally
				thread_data.opener = sccwDownloader()
				thread_data.dl = thread_data.opener.retrieve(self.dlurl, self.flname)			
				#thread_data.dl = urllib.urlretrieve(self.dlurl, self.flname)
				
				
				#DBG
				if option["DEBUG"] == "on":
					DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: finished normal download"
					verbose(DEBUG_MESSAGE)
					logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				#END DBG	
			
			#thread_data.dl = urllib.urlretrieve(self.dlurl, self.flname)
		#Problem with urllib, so we create a blank file and send it to the size check. It will fail the check and redownload
		except:
			blankfile = open(self.flname, 'w')
			blankfile.write("")
			blankfile.close()
		#Now that we have either downloaded the torrent, or we have made a blank file because the download failed, we can continue to the checking routine:
		self.check_valid(self.flname, stime)
		
	def final_output(self, status, stime):
		thread_data = threading.local()
		thread_data.start_time = stime
		if status == True:
			# Calculating download duration
			thread_data.end_time = time.time()
			thread_data.duration = thread_data.end_time - thread_data.start_time
			#round off extra crap from duration to 3 digits
			thread_data.duration = str(round(thread_data.duration, 3))
			#Update Recent list
			update_recent(self.matchedtext.group(3), self.disp_path, self.nicesize, thread_data.duration)
			#Print/log the confirmation of download completed and duration
			# Its annoying to see the download try number after each grab, so only put the number of retry's if there was more than 1.
			if self.count == 1:
				thread_data.verbtext3 = color["bpurple"] + "SCCwatcher successfully downloaded torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds."
			else:
				thread_data.verbtext3 = color["bpurple"] + "SCCwatcher successfully downloaded torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds. Total retry's: " + color["dgrey"] + str(self.count)
			verbose(thread_data.verbtext3)
			thread_data.verbtext3 = xchat.strip(thread_data.verbtext3) +" - "+ os.path.normcase(self.disp_path)
			logging(thread_data.verbtext3, "END_GRAB")
			
			#Ok now that we have the file, we can do the upload if necessary:
			#If we're doing an upload, then dont do an email or external command, as that will be handled by the upload class.
			if option["ftpenable"] == 'on':
				upload(self.flname, self.zxfpath, self.matchedtext, self.disp_path, self.extra_paths, self.nicesize, self.nice_tag_extra).start()
			else:
				#If emailing is enabled, dont do external command as that will be handled by the email class.
				if option["smtp_emailer"] == "on":
					email(self.matchedtext, self.disp_path, self.nicesize, self.nice_tag_extra).start()
				else:
					if option["use_external_command"] == "on":
						do_cmd(self.matchedtext, self.disp_path, self.nicesize, self.nice_tag_extra).start()
		else:
			thread_data.verbtext3 = color["bpurple"]+"SCCwatcher failed to downloaded torrent for "+color["dgrey"] + self.matchedtext.group(3) + color["bpurple"]+" after " +color["dgrey"]+ option["max_dl_tries"] + color["bpurple"]+" tries. Manually download at: " +color["dgrey"]+ self.dlurl
			verbose(thread_data.verbtext3)
			thread_data.verbtext3 = xchat.strip(thread_data.verbtext3) +" - "+ os.path.normcase(self.disp_path)
			logging(thread_data.verbtext3, "END_GRAB_FAILED")
	
#threaded upload class
class upload(threading.Thread):
	def __init__(self, torrentname, zxfpath, matchedtext, disp_path, extra_paths, nicesize, nice_tag_extra):
		self.torrentname = torrentname
		self.zxfpath = zxfpath
		self.matchedtext = matchedtext		
		self.disp_path = disp_path
		self.extra_paths = extra_paths
		self.nicesize = nicesize
		self.nice_tag_extra = nice_tag_extra
		threading.Thread.__init__(self)
	#Uploading tiem nao!!!!
	def run(self):
		if option["DEBUG"] == "on":
			DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: FTP Upload operation has started."
			verbose(DEBUG_MESSAGE)
			logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				
		#create thread-local data to further prevent var overwrites under high load
		thread_data = threading.local()
		#try to see if the ftp details are available, if the are: upload
		thread_data.ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if thread_data.ftpdetails is not None:
			thread_data.verbtext2 = color["bpurple"] + "SCCwatcher is uploading file " + color["dgrey"] + self.matchedtext.group(3) + ".torrent" + color["bpurple"] + " to " + color["dgrey"] + "ftp://" + color["dgrey"] + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5)
			verbose(thread_data.verbtext2)
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
			
			thread_data.uc = 0
			thread_data.uploaded = False
			#  Eliminate errors while uploading by using try-except protection. Uses the max_dl_tries variable to know how many tries to 
			while thread_data.uploaded is False:
				if thread_data.uc < int(option["max_dl_tries"]):
					try:
						thread_data.s.storbinary('STOR ' + self.matchedtext.group(3) + ".torrent", thread_data.f) # Send the file
						thread_data.uploaded = True
						break
					except:
						thread_data.vtext1 = color["bpurple"] + "SCCwatcher encountered an error while uploading " + color["dgrey"] + self.matchedtext.group(3) + ".torrent." + color["bpurple"] + " Retrying...."
						verbose(thread_data.vtext1)
						logging(xchat.strip(thread_data.vtext1), "UPLOAD_FAIL-RETRYING")
						thread_data.uc += 1
						time.sleep(int(option["retry_wait"]))
				else:
					thread_data.vtext2 = color["bpurple"] + "SCCwatcher cannot upload " + color["dgrey"] + self.matchedtext.group(3) + ".torrent" + color["bpurple"] + " to the specified FTP server. Please make sure the server is functioning properly."
					verbose(thread_data.vtext2)
					logging(xchat.strip(thread_data.vtext2), "UPLOAD_FAIL_FINAL")
					break
				
			thread_data.f.close() # Close file
			thread_data.s.quit() # Close ftp
			
			if thread_data.uploaded == True:
				self.upload_finish(thread_data.start_time2, thread_data.ftpdetails)
			
		else:
			print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
			option["ftpenable"] = 'off'
			xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
		if option["smtp_emailer"] == "on":
			email(self.matchedtext, self.disp_path, self.nicesize, self.nice_tag_extra).start()
		else:
			if option["use_external_command"] == "on":
				do_cmd(self.matchedtext, self.disp_path, self.nicesize, self.nice_tag_extra).start()
		
	def upload_finish(self, stime, ftpdetails):
		thread_data = threading.local()
		thread_data.start_time2 = stime
		thread_data.ftpdetails = ftpdetails
		thread_data.end_time2 = time.time()
		thread_data.duration2 = thread_data.end_time2 - thread_data.start_time2
		#round off extra crap from duration to 3 digits
		thread_data.duration2 = str(float(round(thread_data.duration2, 3)))
		thread_data.verbtext4 = color["bpurple"] + "SCCwatcher successfully uploaded file " + color["dgrey"] + self.matchedtext.group(3) + ".torrent" + color["bpurple"] + " to " + color["dgrey"] + "ftp://" + color["dgrey"] + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5) + color["bpurple"]+" in " + color["dgrey"]+thread_data.duration2 + color["bpurple"]+" seconds."
		verbose(thread_data.verbtext4)
		thread_data.verbtext4 = xchat.strip(thread_data.verbtext4)
		logging(thread_data.verbtext4, "END_UPLOAD")
		
#Threaded upload class. Thanks to backdraft for providing most of the code. Sure made my life easier. :)
class webui_upload(threading.Thread):
	def __init__(self, turl, matchedtext, nicesize, nice_tag_extra):
		self.turl = turl
		self.matchedtext = matchedtext
		self.nicesize = nicesize
		self.nice_tag_extra = nice_tag_extra
		threading.Thread.__init__(self)	
		
	def run(self):
		if option["DEBUG"] == "on":
			DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: uTorrent WebUI upload operation has started."
			verbose(DEBUG_MESSAGE)
			logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
				
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
			thread_data.error = color["bpurple"]+"SCCwatcher encountered an HTTP error while connecting to the uTorrent WebUI at " + color["dgrey"] + option["utorrent_hostname"] + color["bpurple"] + ". Please double check the uTorrent WebUI settings in scc.ini are correct."
			verbose(thread_data.error)
			thread_data.good = 0
		if thread_data.good == 1:
			#end timer
			thread_data.end_time = time.time()
			thread_data.duration = thread_data.end_time - thread_data.start_time
			thread_data.duration = str(round(thread_data.duration, 3))
			# If only uTorrent uploading is active, update the recent using WEBUI as the disp_path
			if option["utorrent_mode"] == "2":
				thread_data.webuiloc = "WEBUI-" + option["utorrent_hostname"]
				update_recent(self.matchedtext.group(3), thread_data.webuiloc, self.nicesize, thread_data.duration)
				if option["smtp_emailer"] == "on":
					email(self.matchedtext, "NONE", self.nicesize, self.nice_tag_extra).start()
				else:
					if option["use_external_command"] == "on":
						do_cmd(self.matchedtext, "NONE", self.nicesize, self.nice_tag_extra).start()
				
			thread_data.verbtext = color["bpurple"]+"SCCwatcher successfully added torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " to the uTorrent WebUI at " + color["dgrey"] + option["utorrent_hostname"] + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds."
			verbose(thread_data.verbtext)
			thread_data.verbtext3 = xchat.strip(thread_data.verbtext)
			logging(thread_data.verbtext3, "END_UTOR_ADD")
		if thread_data.good == 0:
			thread_data.verbtext3 = xchat.strip(thread_data.error)
			logging(thread_data.verbtext3, "END_UTOR_ADD")
		
class email(threading.Thread):
	def __init__(self, matchedtext, disp_path, nicesize, nice_tag_extra):
		self.matchedtext = matchedtext
		self.disp_path = disp_path
		self.nicesize = nicesize
		self.nice_tag_extra = nice_tag_extra
		threading.Thread.__init__(self)	
	#Send tiem nao
	def run(self):
		if option["DEBUG"] == "on":
			DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Email operation has started."
			verbose(DEBUG_MESSAGE)
			logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
		#create thread-local data to further prevent var overwrites under high load
		thread_data = threading.local()
		#connect to the server
		try:
			thread_data.smtpconn = smtplib.SMTP(option["smtp_server"], option["smtp_port"])
			#Uncomment the line below to be dazzled with all the crazy server chatter. Very spammy.
			#thread_data.smtpconn.set_debuglevel(1)
			thread_data.smtpconn.ehlo()
			thread_data.is_connected = True
			
		#If theres an error while connecting, verbose/log it
		except:
			thread_data.verbtext=color["bpurple"]+"SCCwatcher encountered an error while connecting to SMTP server, no email was sent"
			verbose(thread_data.verbtext)
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
					thread_data.verbtext=color["bpurple"]+"SCCwatcher encountered an error while authenticating with the SMTP server, no email was sent"
					verbose(thread_data.verbtext)
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
					thread_data.verbtext=color["bpurple"]+"SCCwatcher successfully emailed " + color["dgrey"] + option["smtp_to"]
					verbose(thread_data.verbtext)
					thread_data.verbtext = xchat.strip(thread_data.verbtext)
					logging(xchat.strip(thread_data.verbtext), "SMTP_SUCCESS")
				except:
					thread_data.verbtext=color["bpurple"]+"SCCwatcher encountered an error while talking to the SMTP server, no email was sent"
					verbose(thread_data.verbtext)
					thread_data.verbtext = xchat.strip(thread_data.verbtext)
					logging(xchat.strip(thread_data.verbtext), "SMTP_FAIL")
		if option["use_external_command"] == "on":
			do_cmd(self.matchedtext, self.disp_path, self.nicesize, self.nice_tag_extra).start()

	#Here we build our email message
	def message_builder(self):
		thread_data = threading.local()
		thread_data.current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		#Here we replace all the special strings with actual data
		# Acceptable special strings are:
		# %torrent% %category% %size% %time% %dlpath% %ulpath% %utserver% %tag %torrentpath% %sccgrptree% %sccgrp% %sccdate%
		# To see what they mean, just see below.
		thread_data.sccgrp = self.matchedtext.group(2)
		thread_data.sccgrp = thread_data.sccgrp.replace('/','.')
		thread_data.sccgrp = thread_data.sccgrp.replace('-','.')
		thread_data.sccgrptree = self.matchedtext.group(2)
		thread_data.sccgrptree = thread_data.sccgrptree.replace('-', os.sep)
		thread_data.sccgrptree = thread_data.sccgrptree.replace('/', os.sep)
		thread_data.sccdate = time.strftime("%m%d", time.localtime())
		
		thread_data.fulltpath = self.disp_path + self.matchedtext.group(3) + ".torrent"
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
		thread_data.email_body = thread_data.email_body.replace('%tag%', self.nice_tag_extra)
		thread_data.email_body = thread_data.email_body.replace('%torrentpath%', thread_data.fulltpath)
		thread_data.email_body = thread_data.email_body.replace('%sccgrptree%', thread_data.sccgrptree)
		thread_data.email_body = thread_data.email_body.replace('%sccgrp%', thread_data.sccgrp)
		thread_data.email_body = thread_data.email_body.replace('%sccdate%', thread_data.sccdate)
		
		thread_data.email_subject = option["smtp_subject"].replace('%torrent%', self.matchedtext.group(3))
		thread_data.email_subject = thread_data.email_subject.replace('%category%', self.matchedtext.group(2))
		thread_data.email_subject = thread_data.email_subject.replace('%size%', self.nicesize)
		thread_data.email_subject = thread_data.email_subject.replace('%time%', thread_data.current_time)
		thread_data.email_subject = thread_data.email_subject.replace('%dlpath%', self.disp_path)
		thread_data.email_subject = thread_data.email_subject.replace('%ulpath%', thread_data.ftpstring)
		thread_data.email_subject = thread_data.email_subject.replace('%utserver%', thread_data.utstring)
		thread_data.email_subject = thread_data.email_subject.replace('%tag%', self.nice_tag_extra)
		thread_data.email_subject = thread_data.email_subject.replace('%torrentpath%', thread_data.fulltpath)
		thread_data.email_subject = thread_data.email_subject.replace('%sccgrptree%', thread_data.sccgrptree)
		thread_data.email_subject = thread_data.email_subject.replace('%sccgrp%', thread_data.sccgrp)
		thread_data.email_subject = thread_data.email_subject.replace('%sccdate%', thread_data.sccdate)
		
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
	def __init__(self, matchedtext, disp_path, nicesize, nice_tag_extra):
		self.matchedtext = matchedtext
		self.disp_path = disp_path
		self.nicesize = nicesize
		self.nice_tag_extra = nice_tag_extra
		threading.Thread.__init__(self)	
	#Send tiem nao
	def run(self):
		if option["DEBUG"] == "on":
			DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: External command operation has started."
			verbose(DEBUG_MESSAGE)
			logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
		thread_data = threading.local()
		thread_data.current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		#Here we replace all the special strings with actual data
		# Acceptable special strings are:
		# %torrent% %category% %size% %time% %dlpath% %ulpath% %utserver% %sccdate%
		# To see what they mean, just see below.
		thread_data.sccgrp = self.matchedtext.group(2)
		thread_data.sccgrp = thread_data.sccgrp.replace('/','.')
		thread_data.sccgrp = thread_data.sccgrp.replace('-','.')
		thread_data.sccgrptree = self.matchedtext.group(2)
		thread_data.sccgrptree = thread_data.sccgrptree.replace('-', os.sep)
		thread_data.sccgrptree = thread_data.sccgrptree.replace('/', os.sep)
		thread_data.sccdate = time.strftime("%m%d", time.localtime())
			
		thread_data.fulltpath = self.disp_path + self.matchedtext.group(3) + ".torrent"
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
		thread_data.command_string = thread_data.command_string.replace('%tag%', self.nice_tag_extra)
		thread_data.command_string = thread_data.command_string.replace('%torrentpath%', thread_data.fulltpath)
		thread_data.command_string = thread_data.command_string.replace('%sccgrptree%', thread_data.sccgrptree)
		thread_data.command_string = thread_data.command_string.replace('%sccgrp%', thread_data.sccgrp)
		thread_data.command_string = thread_data.command_string.replace('%sccdate%', thread_data.sccdate)
		
		#Check what OS we are on so we know if we need to use 'shell=True' with subprocess.Popen
		thread_data.osver = platform.system()
		
		# If for some reason you are having trouble with this new script, specifically external commands, it could be because of the new execution method (subprocess.Popen). 
		# To fix this, you need to replace the do_cmd class in this script with the one from version 1.72.
		# If you have problems doing that then PM TRB and he will give you a pastebin link to a fully modified version.
		
		try:
			if thread_data.osver == "Windows":
				subprocess.Popen(thread_data.command_string)
			else:
				subprocess.Popen(thread_data.command_string, shell=True)
			
			thread_data.verbtext=color["bpurple"]+"SCCwatcher successfully ran the external command " + color["dgrey"] + thread_data.command_string
			verbose(thread_data.verbtext)
			thread_data.verbtext = xchat.strip(thread_data.verbtext)
			logging(xchat.strip(thread_data.verbtext), "EXT_CMD_SUCCESS")
		except:
			thread_data.verbtext=color["bpurple"]+"SCCwatcher encountered an error running: " + color["dgrey"] + thread_data.command_string
			verbose(thread_data.verbtext)
			thread_data.verbtext = xchat.strip(thread_data.verbtext)
			logging(xchat.strip(thread_data.verbtext), "EXT_CMD_FAIL")


# I had to split up the on_local and the ifs because using try on all of it was causing problems
def on_local(word, word_eol, userdata):
	global option
	ftrigger = re.split(' ',word_eol[0])
	try:
		ftrigger[1] #make sure we have an argument
		ftrigger[1][0] #Make sure that argument isnt just blank
		#Before all text was being lower()'d but remwatch and remavoid are case sensitive, so this only turns the first arg to lower, leaving the other args intact
		arg1 = ftrigger.pop(1).lower()
		ftrigger.insert(1, arg1)
		help(ftrigger)
	except:
		print "No argument given, for help type: /sccwatcher help"
	#help(ftrigger)
	return xchat.EAT_ALL

def help(trigger):
	global recent_list, option, last5recent_list
	#For use with custom tabs.
	sop_outtext = color["red"] + "SCCwatcher will now use this tab for all verbose output. Use /sccwatcher anytab to go back to the original way sccwatcher outputs."
	
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
			print color["dgrey"], "Help, Loud, Quiet, Rehash, Addwatch, Addavoid, Remwatch, Remavoid, Status, Watchlist, Avoidlist, On, Off, ftpon, ftpoff, updateftp, ftpdetails, logon, logoff, recent, recentclear, detectnetwork, emailon, emailoff, anytab, thistab, sccab, sslon, ssloff, cmdon, cmdoff, manualadd" 
			print color["blue"], "To see info on individual commands use: "+color["bpurple"]+"/sccwatcher help <command>"
			
	elif trigger[1] == 'ftpon':
		ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["ftpdetails"])
		if ftpdetails is not None:
			print color["blue"]+"FTP Uploading is now enabled, use 'ftpoff' to turn it back off"
			option["ftpenable"] = 'on'
			xchat.command('menu -t1 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
		else:
			xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
			print color["red"]+"There is a problem with your ftp details, please double check scc.ini and make sure you have entered them properly. You can also you 'updateftp' to update the FTP details"
	
	elif trigger[1] == 'ftpoff':
		print color["blue"]+"FTP Uploading is now disabled, use 'ftpon' to turn it back on"
		xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
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
		xchat.command('menu -t1 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')

	elif trigger[1] == 'quiet':
		print color["blue"]+"Verbose output turned off, use 'loud' to turn it back on"
		option["verbose"] = 'off'
		xchat.command('menu -t0 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')

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
		#Clear the recent list menu
		for x in last5recent_list:
			xchat.command('menu DEL "SCCwatcher/Recent Grab List/Recent List/%s' % last5recent_list[x])
		xchat.command('menu -e0 add "SCCwatcher/Recent Grab List/Recent List/(none)" "echo"')
		last5recent_list = {}
		recent_list = []
		
		print color["red"] + "Recent list cleared."
	
	elif trigger[1] == 'logon':
		print color["blue"]+"Logging to file is now turned on, use 'logoff' to turn it back off"
		option["logenabled"] = 'on'
		xchat.command('menu -t1 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')
	
	elif trigger[1] == 'logoff':
		print color["blue"]+"Logging to file is now turned off, use 'logon' to turn it back on"
		option["logenabled"] = 'off'
		xchat.command('menu -t0 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')

	elif trigger[1] == 'status':
		print color["bpurple"], "SCCwatcher version " +color["blue"] + __module_version__
		if option["DEBUG"] == "on":
			print color["bpurple"], "Debug output is: " + color["blue"] + option["DEBUG"]
		print color["bpurple"], "Auto downloading is: " + color["blue"] + option["service"]
		print color["bpurple"], "SSL downloading is: " + color["blue"] + option["download_ssl"]
		if option.has_key("cookiefile") and len(option["cookiefile"]) > 2 and option.has_key("useragent") and len(option["useragent"]) > 5:
			print color["bpurple"], "Cloudflare workaround is " + color["blue"] + "Enabled"
		else:
			print color["bpurple"], "Cloudflare workaround is " + color["blue"] + "Disabled"
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
		print color["lblue"] + "Current watchlist: " + color["dgreen"] + str(option["watchlist"])
		
	elif trigger[1] == 'avoidlist':
		print color["lblue"] + "Current avoidlist: " + color["dred"] + str(option["avoidlist"])
	
	elif trigger[1] == 'off':
		option["service"] = 'off'
		xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
		print color["red"], "Autodownloading has been turned off"

	elif trigger[1] == 'on':
		if option["service"] == 'notdetected':
			xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
			print color["red"], " Didn't detected the correct network infos! Autodownloading is disabled. Make sure you have joined #announce channel and then redetect the network through the SCCwatcher toolbar menu."      
		else:
			if xchat.find_context(channel='#announce') is not None:
				option["service"] = 'on'
				xchat.command('menu -t1 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
				print color["dgreen"], "Autodownloading has been turned on"
			else:
				option["service"] = 'off'
				print color["red"], " Didn't detected the correct network infos! Autodownloading is disabled. Make sure you have joined #announce channel and then redetect the network through the SCCwatcher toolbar menu."      
				xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
	
	elif trigger[1] == 'emailoff':
		option["smtp_emailer"] = 'off'
		xchat.command('menu -t0 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')
		print color["red"], "Emailing has been turned off, use 'emailon' to turn it back on"
	
	elif trigger[1] == 'emailon':
		option["smtp_emailer"] = 'on'
		xchat.command('menu -t1 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')
		print color["red"], "Emailing has been turned on, use 'emailoff' to turn it back off"
	
	elif trigger[1] == 'sslon':
		option["download_ssl"] = 'on'
		xchat.command('menu -t1 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
		print color["red"], "SSL downloading is now enabled, use 'ssloff' to disable it."
		
	elif trigger[1] == 'ssloff':
		option["download_ssl"] = 'off'
		xchat.command('menu -t0 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
		print color["red"], "SSL downloading is now disabled, use 'sslon' to enable it."
	
	elif trigger[1] == "setoutput":
		print color["red"] + "This command has been depreciated. You can now use anytab, thistab, or scctab. The deloutput command has also been removed in favor of anytab."
	
	elif trigger[1] == "thistab":
		#Use extra context
		option["_extra_context_"] = "on"
		option["_current_context_type_"] = "THISTAB"
		#Set the tab as the context to use
		option["_current_context_"] = xchat.find_context()
		#set the context name
		option["_current_context_name_"] = option["_current_context_"].get_info("channel")
		option["_current_context_"].prnt(sop_outtext)
		xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
		
	elif trigger[1] == "scctab":
		#Use extra context
		option["_extra_context_"] = "on"
		option["_current_context_type_"] = "SCCTAB"
		#Create the new tab
		xchat.command("QUERY SCCwatcher")
		#Set the new tab as the context to use
		option["_current_context_"] = xchat.find_context(channel="SCCwatcher")
		#set the context name
		option["_current_context_name_"] = option["_current_context_"].get_info("channel")
		option["_current_context_"].prnt(sop_outtext)
		xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
	
	elif trigger[1] == "anytab":
		option["_extra_context_"] = "off"
		option["_current_context_type_"] = "ANYTAB"
		print color["red"] + "SCCwatcher will now output all text to whichever tab is active at the time of printing."
		xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
	
	elif trigger[1] == 'deloutput':
		print color["red"] + "This command has been depreciated. You can now use anytab to reset the verbose output to default."
	
	#These commands below are internal commands the menu uses.
	elif trigger[1] == "_guiaddwatch":
		xchat.command('GETSTR Name:Group "sccwatcher addwatch" "Temporarily Add Watch"')
		
	elif trigger[1] == "_guiaddavoid":
		xchat.command('GETSTR word-to-avoid "sccwatcher addavoid" "Temporarily Add Watch"')
	
	elif trigger[1] == "_guidebugon":
		pass
		
	elif trigger[1] == "_guidebugoff":
		option["DEBUG"] = "off"
		xchat.command('menu DEL "SCCwatcher/Debug output"')
		
		
	elif trigger[1] == "cmdon":
		option["use_external_command"] = "on"
		print color["red"], "External Command Execution has been enabled, use cmdoff to turn it off."
		xchat.command('menu -t1 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
	
	elif trigger[1] == "cmdoff":
		option["use_external_command"] = "off"
		print color["red"], "External Command Execution has been disabled, use cmdoff to turn it on."
		xchat.command('menu -t0 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
	
	else:
		print color["red"], "Unknown command, " + color["black"] + trigger[1]
		print color["red"], "For help type: /sccwatcher help"

def manual_torrent_add(word, word_eol, userdata):
	#All we are doing is sending the input data directly to on_text. The only thing we do first is make sure the entered data actually works, that way we can inform the user if it's incorrect.
	#If it checks out, we send the data over to on_text with special userdata flag to bypass some of the checks that happen for channel messages.
	
	#This is just incase someone uses the command and doesnt enter anything
	try:
		word_eol[1]
	except:
		word_eol = ['Nothing', 'Nothing', 'Nothing']
		
	manual_matchedtext = announce_regex.match(xchat.strip(word_eol[1]))
	if manual_matchedtext is not None:
		#group(1) = Garbage at the beginning of the line
		#group(2) = Torrent's section (TV/XviD, TV-X264, etc)
		#group(3) = Release name
		#group(4) = Pretime and size
		#group(5) = Torrent's site ID
		#group(6) = Garbage at the end of the line
		# Sending the data like this:
		# on_text(regex_object, blank, bypass_checks_flag)
		on_text(manual_matchedtext, None, "BYPASS")
		
	else:
		verbose("\00305The line you entered was incorrect somehow. Please double check that the line you copied was actually from #announce and was complete and try again\003")
		verbose("\00305If you continue to have problems please post the problem in the SCCwatcher forum topic.\003")
	
	return xchat.EAT_ALL

def announce_line_tester(word, word_eol, userdata):
	global option
	#basically using manual_torrent_add's checking code and then using some of the option checking code in on_text.
	
	#This is just incase someone uses the command and doesnt enter anything
	try:
		word_eol[1]
	except:
		word_eol = ['Nothing', 'Nothing', 'Nothing']
		
	manual_matchedtext = announce_regex.match(xchat.strip(word_eol[1]))
	if manual_matchedtext is not None:
		#group(1) = Garbage at the beginning of the line
		#group(2) = Torrent's section (TV/XviD, TV-X264, etc)
		#group(3) = Release name
		#group(4) = Pretime and size
		#group(5) = Torrent's site ID
		#group(6) = Garbage at the end of the line
		# Sending the data like this:
		# on_text(regex_object, blank, bypass_checks_flag)
		
		#Ok now the thing is, we don't want to actuall *do* anything when we send this to on_text.
		#So we are going to disable logging if its enabled but leave verbose output on so you can see (should it be forced on if its off? yes for now)
		if option["logenabled"] == "on":
			option["logenabled"] = "off"
			option["__logenabled"] = "on"
		
		if option["verbose"] == "off":
			option["verbose"] = "on"
			option["__verbose"] = "off"
		
		#We are also going to turn debugging output on just because when testing you might want extra info
		option["DEBUG"] = "on"
		
		on_text(manual_matchedtext, None, "TESTING")
		
		#now turn debug output off
		option["DEBUG"] = "off"
		
		#Now reset settings back to what they were.
		try:
			option["__verbose"]
			option["verbose"] = option["__verbose"]
		except:
			option["verbose"] = "on"
		
		try:
			option["__logenabled"]
			option["logenabled"] = option["__logenabled"]
		except:
			option["logenabled"] = "off"		
	else:
		verbose("\00305The line you entered was incorrect somehow. Please double check that the line you copied was actually from #announce and try again\003")
		verbose("\00305If you continue to have problems please post the problem in the SCCwatcher forum topic.\003")
	
	return xchat.EAT_ALL

def unload_cb(userdata):
	quitmsg = "\0034 "+__module_name__+" "+__module_version__+" has been unloaded\003"
	print quitmsg
	xchat.command('menu DEL SCCwatcher')
	#Only log script unload if logging is enabled
	if option["logenabled"] == "on":
		logging(xchat.strip(quitmsg), "UNLOAD")



#The hooks go here
xchat.hook_print('Channel Message', on_text)
xchat.hook_command('SCCwatcher', on_local, help="Edit main setting in scc.ini. use \002/sccwatcher help\002 for usage information.")
xchat.hook_command('manualadd', manual_torrent_add, help="Manually grab torrents by pasting lines from #announce")
xchat.hook_command('test_line', announce_line_tester, help="This will test a line to see if it would be downloaded by your current settings in scc.ini")
xchat.hook_unload(unload_cb)
#load scc.ini
load_vars()

# This gets the script movin
if (__name__ == "__main__"):
		main()

#LICENSE GPL
#Last modified 10-15-15 (MM/DD/YY)

