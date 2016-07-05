#!/usr/bin/python
##############################################################################
#    SCCwatcher                                                              #
#                                                                            #
#    exclusively written for scc                                             #
#    some code from reality and cancel's bot                                 #
#                                                                            #
#    Copyright (C) 2008-2016  TRB                                            #
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
__module_version__ = "2.1a4"
__module_description__ = "SCCwatcher"

import xchat
import os
import re
import string
import urllib
import ftplib
import time
import threading
import base64
import urllib2
import smtplib
import subprocess
import platform
import socket
import cookielib
import cPickle
from copy import deepcopy as DC
from time import sleep
from tempfile import gettempdir
#from copy import deepcopy as DC


#Set the timeout for all network operations here. This value is in seconds. Default is 20 seconds.
socket.setdefaulttimeout(20)

loadmsg = "\0034 "+__module_name__+" "+__module_version__+" has been loaded\003"
print loadmsg
#Remove our port file
try:
    os.remove(gettempdir() + os.sep + "sccw_port.txt")
except:
    pass

    

#the globals go here
xchat.command('menu DEL SCCwatcher')
extra_paths = "no"
recent_list = []
last5recent_list = {}
dupelist = []
full_xpath = ""
option = {}
has_tab_data = False
sccnet = None
announce_regex = None
downloaderHeaders = None
server_thread = None
xchatdir = xchat.get_info("xchatdir")
color = {"white":"\00300", "black":"\00301", "blue":"\00302", "green":"\00303", "red":"\00304",
"dred":"\00305", "purple":"\00306", "dyellow":"\00307", "yellow":"\00308", "bgreen":"\00309",
"dgreen":"\00310", "green":"\00311", "lblue":"\00312", "bpurple":"\00313", "dgrey":"\00314",
"lgrey":"\00315", "close":"\003"}


class sccwDownloader(urllib.FancyURLopener):
        #This is where we adjust the useragent.
        version = "Mozilla/5.0 (compatible; Python urllib; SCCwatcher; v%s)" % (__module_version__)
    

#Simple way to communicate our random port number to the GUI
def writePortNum(portnum):
    tmpname = gettempdir() + os.sep + "sccw_port.txt"
    tempfile = open(tmpname, 'w')
    tempfile.write(str(portnum))
    tempfile.close()

def getCurrentStatus():
        data = {}
        data["version"] = __module_version__
        data["autodlstatus"] = option["global"]["service"]
        data["ssl"] = option["global"]["download_ssl"]
        data["max_dl_tries"] = option["global"]["max_dl_tries"]
        data["retry_wait"] = option["global"]["retry_wait"]
        if option["global"].has_key("cfbypass_cookiefile") and len(option["global"]["cfbypass_cookiefile"]) > 2 and option["global"].has_key("cfbypass_useragent") and len(option["global"]["cfbypass_useragent"]) > 5:
                data["cf_workaround"] = "on"
        else:
                data["cf_workaround"] = "off"
        data["dupecheck"] = option["global"]["dupecheck"]
        data["logging"] = option["global"]["logenabled"]
        data["verbose"] = option["global"]["verbose"]
        data["recent_list_size"] = str(len(recent_list))
        data["wl_al_size"] = "%s/%s" % (str(len(option["global"]["watchlist"])), str(len(option["global"]["avoidlist"])))
        data["ini_path"] = xchatdir + os.sep + "scc2.ini"
        return data

class server(threading.Thread):
    def __init__(self):
        self.quitting = False
        self.port = None
        self.connected = False
        self.connection = None
        self.address = ("127.0.0.1", 0)
        self.wait_time_recv = int(time.time()) - 5
        self.wait_time_accept = int(time.time()) - 5
        self.recv_tries = 0
        super(server, self).__init__()
    
    
    def quit_thread(self):
        #First set our quitting var se we die asap
        self.quitting = True
        if self.connected is False:
            #Waiting for a self.connection, lets give it one
            quit_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            quit_socket.connect((self.address[0], self.port))
            #Reset quitting since it will be set true now
            self.quitting = True
            quit_socket.close()
        elif self.connected is True:
            self.connection.send("CONNECTION_CLOSING")
    
    def get_connection(self):
        #Connect loop
        while self.connected is False and self.quitting is False:
            if int(time.time()) - self.wait_time_accept > 5:
                self.wait_time_accept = int(time.time())
                try:
                    self.main_socket.settimeout(2)
                    self.connection, addy = self.main_socket.accept()
                    self.connected = True
                    self.connection.setblocking(0) #Non-blocking so we can quit fast if necessary
                except:
                    continue
            sleep(0.5)
            
    def run(self):
        if len(self.address) != 2:
            return
        
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.main_socket.bind(self.address)
            portnum = self.main_socket.getsockname()[1]
            self.port = portnum
            writePortNum(portnum)
            self.main_socket.listen(1)
        except:
            return
        
        while self.quitting is False:
            if self.connected is False:
                self.get_connection()
                continue
            
            while self.connected is True and self.quitting is False:
                rawdata = None
                sleep(0.5) #500ms sleep time to give everyone some breathing room
                if int(time.time()) - self.wait_time_recv > 0.5:
                    if self.recv_tries > 20: #Consider our connection closed if after 10 seconds we still have no data
                        self.connection.close()
                        self.connected = False
                        self.recv_tries = 0
                        continue
                    try:
                        rawdata = self.connection.recv(4096) #Receive at most 4096 bytes.
                        self.recv_tries = 0
                    except:
                        self.recv_tries += 1 #Prevents runaways where the client has closed but we don't know and keep-alives dont figure it out (rare)
                        #send keep-alive
                        try:
                            self.connection.send("KEEP-ALIVE")
                        except:
                            self.connection.close()
                            self.connected = False
                            continue
                        self.wait_time_recv = int(time.time())
                        continue
                
                if rawdata is None:
                    continue
                
                #Got some data, do what was requested:
                if len(rawdata) > 0:
                    returndata = None
                    
                    data_split = re.split(";;;", rawdata)
                    for data in data_split:
                        if len(data) == 0:
                            continue
                            
                        #Execute cmds from GUI
                        elif data == "RELOAD_SCRIPT_SETTINGS":
                            reload_vars()
                            returndata = getCurrentStatus()
                        
                        #Toggle autodl status
                        elif data == "TOGGLE_AUTODL":
                            if option["global"]["service"] == "off":
                                sccwhelp(["", "on"])
                            else:
                                sccwhelp(["", "off"])
                            returndata = getCurrentStatus()
                        
                        #Closing    
                        elif data == "CONNECTION_CLOSING":
                            self.connection.close()
                            self.connected = False
                            continue
                        
                        #Return script status to GUI
                        if data == "GET_SCRIPT_STATUS":
                            returndata = getCurrentStatus()
                        
                        if returndata is not None:
                            preturndata = cPickle.dumps(returndata)
                            #We surround our data with special chars to make it easier to pick out of the jumble of keep-alives we will find in our recv buffer
                            preturndata = ":::" + str(preturndata) + ";;;"
                            self.connection.send(preturndata)
                        
                else:
                    self.connection.close()
                    self.connected = False
                
                sleep(0.2)
                
        try:
            self.connection.send("CONNECTION_CLOSING")
        except:
            pass
        try:
            self.connection.close()
        except:
            pass
        try:
            self.main_socket.close()
        except:
            pass
        
        return


#This function takes the ini file as an argument, and returns the loaded options dict
def loadSettingsFile(file_location):
    global option
    
    #This makes it easier to track the current location within the option dict
    cur_dict = None
    option = {}
    option["watchlist"] = {}
    option["avoidlist"] = {}
    option["global"] = {}
    #Simple lists just for tracking watches and avoids
    option["global"]["watchlist"] = []
    option["global"]["avoidlist"] = []
    
    #These are the defaults here. I thought laying them out flat, while taking up more lines, would make it easier to understand the defaults.
    #Compared to a one-liner that is, and nobody wants those. So here are all of the default general settings. Some are blank while some are set.
    #Zeros are off, Two's are on, and One's are half-ticked boxes (only uTorrent mode does this)
    #We set service by default here to off because we by default don't have a passkey. This just prevents any weird problems associated with running
    #without customizing the config. Really the program should detect no passkey and not do anything.
    option["global"]["service"] = "0"
    option["global"]["verbose"] = "2"
    option["global"]["verbose_tab"] = ""
    option["global"]["printalert"] = "0"
    option["global"]["logenabled"] = "0"
    option["global"]["logpath"] = ""
    option["global"]["startdelay"] = "20"
    option["global"]["passkey"] = ""
    option["global"]["dupecheck"] = "2"
    option["global"]["download_ssl"] = "2"
    option["global"]["savepath"] = ""
    option["global"]["lower_sizelimit"] = ""
    option["global"]["upper_sizelimit"] = ""
    option["global"]["max_dl_tries"] = "15"
    option["global"]["retry_wait"] = "1"
    option["global"]["cfbypass_useragent"] = ""
    option["global"]["cfbypass_cookiefile"] = ""
    option["global"]["ftpenable"] = "0"
    option["global"]["ftpserverhostname"] = ""
    option["global"]["ftpport"] = ""
    option["global"]["ftpremotefolder"] = ""
    option["global"]["ftpusername"] = ""
    option["global"]["ftppassword"] = ""
    option["global"]["ftppassive"] = "0"
    option["global"]["ftpsecuremode"] = "0"
    option["global"]["ftpdetails"] = ""
    option["global"]["utorrent_mode"] = "0"
    option["global"]["utorrent_username"] = ""
    option["global"]["utorrent_password"] = ""
    option["global"]["utorrent_hostname"] = ""
    option["global"]["utorrent_port"] = ""
    option["global"]["smtp_emailer"] = "0"
    option["global"]["smtp_server"] = ""
    option["global"]["smtp_port"] = ""
    option["global"]["smtp_tls"] = "0"
    option["global"]["smtp_username"] = ""
    option["global"]["smtp_password"] = ""
    option["global"]["smtp_from"] = ""
    option["global"]["smtp_to"] = ""
    option["global"]["smtp_subject"] = ""
    option["global"]["smtp_message"] = ""
    option["global"]["use_external_command"] = "0"
    option["global"]["external_command"] = ""
    option["global"]["external_command_args"] = ""
    option["global"]["debug"] = "0"
    
    
    #Easy way to see if we loaded up a good config or not
    good_config_check = False
    
    try:
        inifile = open(file_location, 'r')
    except:
        
        LOADERROR = color["bpurple"] + "Could not open scc2.ini! Put it in "+xchatdir+" !"
        verbose(LOADERROR)
        logging(xchat.strip(LOADERROR), "LOAD_FAIL-INI")
        return False
    
    #Here's the business end of the function
    for line in inifile:
        #Ignore any commented out lines
        if line[0] == "#":
            continue
        
        #New group
        if line[0] == "[":
            groupreg = re.match("\[(-)?(.*?)\]", line)
            grpname = groupreg.group(2)
            #Fix any escaped sequences
            grpname = urllib.unquote(grpname)
            
            #If we don't have a minus sign then its a watch, otherwise its an avoid
            if groupreg.group(1) is None:
                if groupreg.group(2) == "GlobalSettings":
                    good_config_check = True #If we have a GlobalSettings group we definitely have a good config, so we update the check
                    clist = "global"
                    grpname = clist
                else:
                    clist = "watchlist"
            else:
                clist = "avoidlist"
            
            #have to set up differently for global options
            if clist == "global":
                cur_dict = option[clist]
            else:
                #Set up the dict for this entry
                option[clist][grpname] = {}
                #This makes it easier to work with later
                cur_dict = option[clist][grpname]
                #finally append the watch or avoid to our tracking list
                option["global"][clist].append(grpname)
        
        #Options
        elif re.match("(.*?)(?:\s+)?=(?:\s+)?(.*)", line) is not None:
            if cur_dict is not None:
                option_line = re.match("(.*?)(?:\s+)?=(?:\s+)?(.*)", line)
                cur_dict[str(option_line.group(1)).lower()] = str(option_line.group(2))
            else:
                dbgerror = color["bpurple"]+"SCCwatcher found a weird line in your ini: " + str(line)
                verbose(dbgerror)
                logging(dbgerror)
        
        #Some other line, who knows what
        else:
            if option["global"]["debug"] == "on":
                dbgerror = color["bpurple"]+"SCCwatcher found a weird line in your ini: " + str(line)
                verbose(dbgerror)
                logging(dbgerror)
    
    
    #Gotta close it before we quit
    inifile.close()
    
    #Build ftpdetails from the various ftp options
    if option["global"]["ftpenable"] > 0:
        option["global"]["ftpdetails"] = "ftp://%s:%s@%s:%s%s" % (option["global"]["ftpusername"], option["global"]["ftppassword"], option["global"]["ftpserverhostname"], option["global"]["ftpport"], option["global"]["ftpremotefolder"])
        #option["global"]["ftppassive"] = "0"
        #option["global"]["ftpsecuremode"] = "0"
        
    
    #Fix some stuff
    fixdict = {"0": "off", "1": "on", "2": "on"}
    fixdict2 = {"0": "off", "1": "on", "2": "autodetect"}
    if len(str(option["global"]["service"])) > 0: option["global"]["service"] = fixdict2[str(option["global"]["service"])]
    if len(str(option["global"]["dupecheck"])) > 0: option["global"]["dupecheck"] = fixdict[str(option["global"]["dupecheck"])]
    if len(str(option["global"]["verbose"])) > 0: option["global"]["verbose"] = fixdict[str(option["global"]["verbose"])]
    if len(str(option["global"]["logenabled"])) > 0: option["global"]["logenabled"] = fixdict[str(option["global"]["logenabled"])]
    if len(str(option["global"]["ftpenable"])) > 0: option["global"]["ftpenable"] = fixdict[str(option["global"]["ftpenable"])]
    if len(str(option["global"]["smtp_emailer"])) > 0: option["global"]["smtp_emailer"] = fixdict[str(option["global"]["smtp_emailer"])]
    if len(str(option["global"]["use_external_command"])) > 0: option["global"]["use_external_command"] = fixdict[str(option["global"]["use_external_command"])]
    if len(str(option["global"]["download_ssl"])) > 0: option["global"]["download_ssl"] = fixdict[str(option["global"]["download_ssl"])]
    if len(str(option["global"]["printalert"])) > 0: option["global"]["printalert"] = fixdict[str(option["global"]["printalert"])]
    if len(str(option["global"]["ftppassive"])) > 0: option["global"]["ftppassive"] = fixdict[str(option["global"]["ftppassive"])]
    if len(str(option["global"]["ftpsecuremode"])) > 0: option["global"]["ftpsecuremode"] = fixdict[str(option["global"]["ftpsecuremode"])]
    if len(str(option["global"]["smtp_tls"])) > 0: option["global"]["smtp_tls"] = fixdict[str(option["global"]["smtp_tls"])]
    if len(str(option["global"]["debug"])) > 0: option["global"]["debug"] = fixdict[str(option["global"]["debug"])]
    
    if good_config_check is True:
        return option
    else:
        return False


def reload_vars():
    load_vars(rld=True)
    
    
def setupMenus(global_option, rld=False):
    #Simple function to set up the menus.
    #If rld is True it won't erase some stuff.
    
    #Clear out any remnents of the previous menu.
    xchat.command('menu DEL "SCCwatcher"')
    
    #lots of ifs because we have to make sure the default values reflect whats in scc2.ini
    xchat.command('menu -p-1 add SCCwatcher')
    xchat.command('menu add "SCCwatcher/Status" "sccwatcher status"')
    xchat.command('menu add "SCCwatcher/-"')
    
    if global_option["service"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
    else:
        xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
    
    
    if global_option["download_ssl"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
    else:
        xchat.command('menu -t0 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
    
    
    if global_option["smtp_emailer"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')
    else:
        xchat.command('menu -t0 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')

        
    if global_option["ftpenable"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
    else:
        xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')

    if global_option["use_external_command"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
    else:
        xchat.command('menu -t0 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
        
    if global_option["verbose"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')
    else:
        xchat.command('menu -t0 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')

        
    if global_option["logenabled"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')
    else:
        xchat.command('menu -t0 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')
    
    if global_option["debug"] == "on":
        xchat.command('menu -t1 add "SCCwatcher/Debug output" "sccwatcher _guidebugon" "sccwatcher _guidebugoff"')
    
        
    xchat.command('menu add SCCwatcher/-')
    xchat.command('menu add SCCwatcher/Help "sccwatcher help"')
    xchat.command('menu add "SCCwatcher/Reload scc2.ini" "sccwatcher rehash"')
    xchat.command('menu add "SCCwatcher/Re-Detect Network" "sccwatcher detectnetwork"')
    xchat.command('menu add SCCwatcher/-')
    xchat.command('menu add "SCCwatcher/Watchlist"')
    xchat.command('menu add "SCCwatcher/Watchlist/Print Watchlist" "sccwatcher watchlist"')
    xchat.command('menu add "SCCwatcher/Watchlist/-"')
    xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Add Watch" "sccwatcher _guiaddwatch"')
    
    xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch"')
    for x in global_option["watchlist"]:
        xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s"' % str(x))
        xchat.command('menu add "SCCwatcher/Watchlist/Temporarily Remove Watch/%s/Confirm Remove" "sccwatcher remwatch %s"' % (str(x), str(x)))
    
    
    
    xchat.command('menu add "SCCwatcher/Avoidlist"')
    xchat.command('menu add "SCCwatcher/Avoidlist/Print Avoidlist" "sccwatcher avoidlist"')
    xchat.command('menu add "SCCwatcher/Avoidlist/-"')
    xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Add Avoid" "sccwatcher _guiaddavoid"')
    
    xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid"')
    for x in global_option["avoidlist"]:
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
    
    
    
    
    about_box = '"SCCwatcher Version ' + __module_version__ + ' by TRB.'
    xchat.command('menu add SCCwatcher/-')
    xchat.command('menu add SCCwatcher/About "GUI MSGBOX "' + about_box + '""')
    
    if rld is True:
        #This is just a few things that we need to take care of during a reload
        #Custom tab stuff
        if global_option["_extra_context_"] == "on":
            xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
        else:
            xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
    
    else:
        #Some stuff that only happens on first load.
        global_option["_extra_context_"] = "off"
        xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')



def load_vars(rld=False):
    global option, announce_regex, sccnet, has_tab_data, downloaderHeaders, starttimerhook, server_thread
    
    #compile the regexp, do this one time only
    announce_regex = re.compile('(.*)NEW in (.*): -> ([^\s]*.) \((.*)\) - \(https?:\/\/(?:www\.)?sceneaccess\.(?:org|eu)\/details(?:\.php)?\?id=(\d+)\)(.*)')
    
    if rld is True:
        #backup some values we want to keep, if they exist
        _saved_service = option["global"]["service"]
        try:
            cc = option["global"]["_current_context_"]
            ec = option["global"]["_extra_context_"]
        except:
            cc = None
            ec = "off"
            
    if loadSettingsFile(os.path.join(xchatdir,"scc2.ini")) is not False:
        
        if len(option["global"]["passkey"]) < 32: #Passkeys are 32 chars long
            print color["red"]+"There is a problem with your passkey, it seems to be invalid. Please double check your the passkey you entered is correct and try again. Disabling autodownloading..."
            print color["red"]+"If this problem persists, it may be a bug. Please contact TRB about the issue for a fix."
            option["global"]["service"] = "off"
            return False
        
        if option["global"]["ftpenable"] == 'on' and option["global"].has_key("ftpdetails") is True:
            detailscheck = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["global"]["ftpdetails"])
            if detailscheck is None:
                print color["red"]+"There is a problem with your ftp details, please double check scc2.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
                option["global"]["ftpenable"] = 'off'
                xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
        
        #check the savepath and logpath to make sure they have the trailing slash
        if len(option["global"]["savepath"]) > 0 and option["global"]["savepath"][-1] != os.sep:
            option["global"]["savepath"] = str(option["global"]["savepath"]) + os.sep
        
        if len(option["global"]["logpath"]) > 0 and option["global"]["logpath"][-1] != os.sep:
            option["global"]["logpath"] = str(option["global"]["logpath"]) + os.sep
        
        
        try:
            option["global"]["external_command"]
        except:
            option["global"]["external_command"] = ""
        
        #Set up debug var. If it exists use it, if not set it to false
        try:
            option["global"]["debug"]
        except:
            option["global"]["debug"] = "off"
        
        #convert upper and lower sizelimits to bytes
        try:
            option["global"]["lower_sizelimit"]
        except:
            option["global"]["lower_sizelimit"] = ""
        try:
            option["global"]["upper_sizelimit"]
        except:
            option["global"]["upper_sizelimit"] = ""
        #Ok so now we can convert our sizelimits to bytes and store them in similarly named variables, just with _bytes suffix.
        option["global"]["lower_sizelimit_bytes"] = return_bytes_from_sizedetail(option["global"]["lower_sizelimit"])
        option["global"]["upper_sizelimit_bytes"] = return_bytes_from_sizedetail(option["global"]["upper_sizelimit"])
        
        
        # here we check for an option that specifies what tab we should be sending the verbose output to.
        # If its blank or nonexistant then we assume the user doesnt have any preference they want to set ahead of time.
        # If it does have something, we assume its the name of the tab they want the output to go to. I'm not sure of what characters are safe to put into a tab name but the user wont be doing anything weird
        has_tab_data = False
        try:
            option["global"]["verbose_tab"]
            #Ok so the option exists, now does it have anything in it?
            if len(option["global"]["verbose_tab"]) > 0:
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
        if option["global"].has_key("cfbypass_cookiefile") and option["global"].has_key("cfbypass_useragent"):
            downloaderHeaders = {
            "User-Agent": option["global"]["cfbypass_useragent"],
            "Accept": "application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3"
            }
        
        if rld is True:
            #Set autodownloading back to whatever it was
            option["global"]["service"] = _saved_service
            option["global"]["_current_context_"] = cc
            option["global"]["_extra_context_"] = ec
            
            scc_context = xchat.find_context(server="irc.sceneaccess.org")
            if scc_context is None:
                # If it's None we know either the connection hasnt been made to the server yet or there is a difference in someone's BNC config that obscures the actual server address.
                scc_context = xchat.find_context(channel="#sceneaccess")
            if scc_context is None:
                # If it's STILL None then this user is also only joined to one channnel. Since this is an autodownloader we will assume this channel is the scc announce channel.
                # This could possibly come back as a different server if they share the same channel names. This is just our last ditch maneuver to still use the designated output tab.
                scc_context = xchat.find_context(channel="#announce")
            
            #Because we are reloading the settings here, we cannot count on the delay in enabling downloading to also create the tabs for us so we do it now.
            #Ok now that we have tested the option, we can go ahead and set up the output settings if thats what is needed
            if has_tab_data == True:
                sop_outtext = color["red"] + "SCCwatcher will now use this tab for all verbose output. Use /sccwatcher anytab to go back to the original way sccwatcher outputs."
                # We have to make sure SCCwatcher knows we need extra tabs.
                option["global"]["_extra_context_"] = "on"
                option["global"]["_current_context_type_"] = "SCCTAB"
                #First we need to get a context object for SCCnet so we can be sure the new tab opens in the SCC server branch.
                # I'm not 100% sure whether this will mess up on BNC users who may not be connected straight to irc.sceneaccess.org
                # I am running through a ZNC server myself and it didn't seem to effect things. But just in case this DOES fail on someone the backup will be just looking for #sceneaccess
                
                #Create the new tab if we have the right context object, if not we will report the error and not create the new tab
                if scc_context:
                    scc_context.command("QUERY %s" % option["global"]["verbose_tab"])
                    #Set the new tab as the context to use
                    option["global"]["_current_context_"] = xchat.find_context(channel="%s" % option["global"]["verbose_tab"])
                    #set the context name
                    option["global"]["_current_context_name_"] = option["global"]["_current_context_"].get_info("channel")
                    option["global"]["_current_context_"].prnt(sop_outtext)
                    xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
                else:
                    OHNOEZ = color["bpurple"]+"SCCwatcher failed to create your verbose output tab because it could not find the SCC IRC server. Please make sure you are connected to the SCC IRC server and you have joined the announce channel."
                    verbose(OHNOEZ)
                    logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
            
            print color["dgreen"], "SCCwatcher scc2.ini reloaded successfully!"
            
        else:
            print color["dgreen"], "SCCwatcher scc2.ini Load Success, detecting the network details, the script will be ready in", option["global"]["startdelay"], "seconds "
            #Only log script load if logging is enabled
            if option["global"]["logenabled"] == "on":
                loadmsg = "\0034 "+__module_name__+" "+__module_version__+" has been loaded\003"
                logging(xchat.strip(loadmsg), "LOAD")
            
        #Build the menus
        setupMenus(option["global"], rld)
        
        #Start up coms server on first boot
        if rld is False:
            server_thread = server()
            server_thread.start()
        
        return True
    else:
        print color["red"], "There was an error while reading your config. The GlobalSettings group couldn't be located within your scc2.ini. Please recheck your config. Autodownloading is disabled."
        return False
    
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
            option["global"]["_extra_context_"] = "on"
            option["global"]["_current_context_type_"] = "SCCTAB"
            
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
                scc_context.command("QUERY %s" % option["global"]["verbose_tab"])
                #Set the new tab as the context to use
                option["global"]["_current_context_"] = xchat.find_context(channel="%s" % option["global"]["verbose_tab"])
                #set the context name
                option["global"]["_current_context_name_"] = option["global"]["_current_context_"].get_info("channel")
                option["global"]["_current_context_"].prnt(sop_outtext)
                xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
            else:
                OHNOEZ = color["bpurple"]+"SCCwatcher failed to create your verbose output tab because it could not find the SCC IRC server. Please make sure you are connected to the SCC IRC server and you have joined the announce channel."
                verbose(OHNOEZ)
                logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
        
        #And lastly we turn on the service, update the checkbox in the menu to reflect the new status, and send a message to the user about this.
        option["global"]["service"] = 'on'
        xchat.command('menu -t1 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
        verbose(color["dgreen"] + "Network detected succesfully, script loaded and working properly")
        
    else:
        option["global"]["service"] = 'notdetected'
        xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
        print color["red"], "Could not detect the correct network! Autodownloading has been disabled. Make sure you have joined #announce channel and then do /sccwatcher detectnetwork"


starttimerhook = None
def main():
    global starttimerhook
    if load_vars() is True:
        sdelay=int(option["global"]["startdelay"]+"000")
        starttimerhook = xchat.hook_timer(sdelay, starttimer)
    else:
        #Still build the menus just to make it look good, and so the user can load a good config when ready
        print color["red"] + "SCCwatcher encountered an error while loading your scc2.ini. Please double check your ini and then do /sccwatcher reload"
        setupMenus(option["global"], False)
    
    
def verbose(text):
    global option
    #Make sure verbose is enabled:
    if option["global"]["verbose"] == 'on':
        #Check if the user wants the script to beep when it prints
        if option["global"].has_key("printalert") and option["global"]["printalert"] == "on":
            text = "\007" + text
        
        try:
            option["global"]["_extra_context_"]
        except:
            option["global"]["_extra_context_"] = "off"
            
        if option["global"]["_extra_context_"] == "on":
            if option["global"]["_current_context_"] is not None:
                context_name = option["global"]["_current_context_"].get_info("channel")
                if context_name == option["global"]["_current_context_name_"]:
                    option["global"]["_current_context_"].prnt(text)
                    option["global"]["_current_context_"].command("GUI COLOR 3")
                    option["global"]["_current_context_"].command("GUI FLASH")
                else:
                    errortext = "\00304There was an error using your set output tab, please redefine the output tab with setoutput. Reseting output to normal."
                    currloc = xchat.find_context()
                    currloc.prnt(errortext)
                    currloc.prnt(text)
                    option["global"]["_extra_context_"] = "off"
                    xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
            else:
                option["global"]["_extra_context_"] = "off"
                xchat.command('menu -e0 -t0 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
                currloc = xchat.find_context()
                currloc.prnt(text)
        else:
            currloc = xchat.find_context()
            currloc.prnt(text)
    
def logging(text, operation):
    #Check if logging has been enabled
    if option["global"]["logenabled"] == 'on':
        #Make sure logpath exists first, if not create it.
        logdir_is_available = os.access(option["global"]["logpath"], os.W_OK)
        if logdir_is_available is False:
            os.mkdir(option["global"]["logpath"])
        
        fullpath = option["global"]["logpath"] + os.sep +  "sccwatcher.log"
        current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        text = current_time+" - "+operation+":"+text+"\n"
        scclog = open(fullpath, 'a')
        scclog.write(text)
        scclog.close()
    

def detect_sep(fullpath):
    DETECTED_SEP = os.sep #Default fallback
    try:
        fullpath.index("/")
        DETECTED_SEP = "/"
    except:
        try:
            fullpath.index("\\")
            DETECTED_SEP = "\\"
        except:
            pass
    return DETECTED_SEP

#This class checks to make sure the directory given actually exists and creates it if not.
#It can also create directories in varius styles, e.g. SCCDATE, SCCGRP, SCCGRPTREE
class dir_check:
    def __init__(self, dldir, cat):
        
        self.dldir = ""
        self.cat = cat
        #This is the base dir that the extra paths will be appended to
        self.full_path = dldir
        #This is the stuff thats going to get appended to the savepath
        self.npath = ""
        
    def check(self):
        global extra_paths
        extra_paths = "yes"
        #Detect dir separator
        DETECTED_SEP = detect_sep(self.full_path) #Default fallback
        
        #Remove any trailing slash for now
        while self.full_path[-1] == "\\" or self.full_path[-1] == "/":
                self.full_path = self.full_path[:len(self.full_path)-1]
        
        #Fix double slashes
        if DETECTED_SEP == "\\":
                self.full_path.replace("\\\\", "\\")
        #Split the dirs and test each one to see if its a special dir path.
        dir_split = self.full_path.split(DETECTED_SEP)
        #We're going to live dangerously and assume that index 0 of our split path is not a special dir name.
        self.npath = dir_split.pop(0)
        #Fix the path to use os.sep to make things easier as well as convert special dir names.
        for x in dir_split:
            if len(x) > 0:
                #Get the dir's name-to-be
                dirname = self.categorize(x)
                #Append the new dir to the eventual path:
                self.npath = self.npath + os.sep + dirname
        #split it again now that we have converted to special dir names and corrected the separator.
        dir_split = self.npath.split(os.sep)
        
        #Could probably combine the above and below loops into one
        #now create the directory structure
        cur_dir = dir_split.pop(0)
        for x in dir_split:
            cur_dir = cur_dir + os.sep + x
            self.create_dir(cur_dir)
            #Check if we failed
            if extra_paths == "no": break
        
        #See if we failed during path creation:
        if extra_paths == "yes":
            self.full_path = os.path.join(self.full_path, self.npath)
            #DONT FORGET THE TRAILING SLASH!!!!
            self.full_path = self.full_path + os.sep
        else:
            self.full_path = option["global"]["savepath"]
        return self.full_path
            
    def categorize(self, xpath):
        if xpath == "SCCDATE":
            # Create a dir in the DDMM format
            xpath = time.strftime("%m%d", time.localtime())
            
        if xpath == "SCCGRP":
            xpath = self.cat
            xpath = xpath.replace('/','.')
            
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
            try:
                os.makedirs(xpath)
            except:
                OHNOEZ = color["bpurple"]+"SCCwatcher cannot create dir: "+color["dgrey"]+xpath+color["bpurple"]+". Please make sure the user running xchat has the proper permissions."
                verbose(OHNOEZ)
                logging(xchat.strip(OHNOEZ), "WRITE_ERROR")
                #disable extra paths
                extra_paths = "no"
            


def update_recent(file, dldir, size, dduration):
    global recent_list, last5recent_list
    entry_number = str(int(len(recent_list)) + 1)
    time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    
    sep = color["black"] + " - "
    
    formatted = color["bpurple"] + entry_number + sep + color["dgrey"] + time_now + sep + color["bpurple"] + file + sep + color["dgrey"] + size + sep + color["bpurple"] + dduration+" Seconds" + sep + color["dgrey"] + os.path.normcase(dldir)
    #recent list update
    recent_list.append(formatted)

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
    


def update_dupe(release_name):
    global dupelist
    #Dupe list update
    dupelist.append(release_name)

#Simple function that converts ints to their corresponding words
def convert_int_opts_to_word(options_dict):
    change_items = []
    change_items.append("service")
    change_items.append("dupecheck")
    change_items.append("verbose")
    change_items.append("logenabled")
    change_items.append("ftpenable")
    change_items.append("use_ftp_upload")
    change_items.append("smtp_emailer")
    change_items.append("use_emailer")
    change_items.append("download_ssl")
    change_items.append("printalert")
    change_items.append("ftppassive")
    change_items.append("ftpsecuremode")
    change_items.append("smtp_tls")
    change_items.append("debug")
    change_items.append("watch_regex")
    change_items.append("avoid_regex")
    change_items.append("use_utorrent_webui")
    change_items.append("use_external_command")
    change_items.append("utorrent_mode")
    for item in change_items:
        if options_dict.has_key(item):
            try:
                int(options_dict[item])
                if int(options_dict[item]) == 0: options_dict[item] = "off"
                elif item == "utorrent_mode":
                        if int(options_dict[item]) == 0:
                                options_dict[item] = "off"
                        elif int(options_dict[item]) == 1:
                                options_dict[item] = "_MIDWAY_"
                        elif int(options_dict[item]) == 2:
                                options_dict[item] = "on"
                elif int(options_dict[item]) > 0: options_dict[item] = "on"
            except:
                pass
    #Prolly dont need to return actually since python passes dicts as pointers, but meh it wont hurt.
    return options_dict

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
    if userdata == "BYPASS" or userdata == "TESTING" or userdata == "SPECIAL":
        pass
    elif option["global"]["service"] == "on":
        # We use try/except as a safe way to test whether or not a variable exists and has what we want
        try:
            #Test for a specific method we will need
            sccnet.get_info('network')
        except:
            # Somehow sccnet is no longer an active context object so we need to disable autodownloading to prevent any errors
            option["global"]["service"] = "off"
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
    if userdata == "BYPASS" or userdata == "TESTING" or userdata == "SPECIAL":
        pass
    elif option["global"]["service"] != 'on':
        return
    
    counter = 0
    # Just temp setting incase the shit hits the fan it will still sorta be correct. Shouldn't go wrong tho :D
    zxfpath = option["global"]["savepath"]
    #get the context where a new message was written
    #If this is a manual add then we just bypass this
    if userdata == "BYPASS" or userdata == "TESTING" or userdata == "SPECIAL":
        pass
    else:
        destination = xchat.get_context()
    #did the message where sent to the right net, chan and by the right bot?
    #If your wondering what the hell xchat.strip does, it removes all color and extra trash from text. I wish the xchat python plugin devs would have documented this function, it sure would have made my job easier.
    #If this is a manual add then we just bypass this
    if userdata == "BYPASS" or userdata == "TESTING" or userdata == "SPECIAL":
        pass
    else:
        stnick = xchat.strip(word[0])
    if userdata == "BYPASS" or userdata == "TESTING" or userdata == "SPECIAL":
        can_continue = True
    elif destination.get_info('network') == sccnet.get_info('network') and destination.get_info('channel') == sccnet.get_info('channel') and stnick == "SCC":
        can_continue = True
    
    
    if can_continue == True:
        if userdata == "BYPASS" or userdata == "TESTING" or userdata == "SPECIAL":
            #If we are manually adding then use word as the regex object.
            matchedtext = word
            word = ['MANUAL_TEST', matchedtext.group(0), '']
        else:
            matchedtext = announce_regex.match(xchat.strip(word[1]))
        #the bot wrote something we can understand, we can proceed with the parsing
        if matchedtext is not None:
            if option["global"]["debug"] == "on":
                DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Got good announce line! Testing line against watchlist... LINE: " + color["dgrey"] + str(word[1])
                verbose(DEBUG_MESSAGE)
                logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
            
            #
            #matchedtext.group(1) = crap before line
            #matchedtext.group(2) = Release Category
            #matchedtext.group(3) = Release Name
            #matchedtext.group(4) = Pretime and Size information
            #matchedtext.group(5) = Torrent ID
            #
            #Example matches:    
            #matchedtext.group(1) = <SCC> 
            #matchedtext.group(2) = TV/HD-x264
            #matchedtext.group(3) = Dr.Dee.Alaska.Vet.S01E01.720p.HDTV.x264-CBFM
            #matchedtext.group(4) = Uploaded 1 minute and 52 seconds after pre) - (1.06 GB
            #matchedtext.group(5) = 1292421

            #check if it's in watchlist
            #length checks to make sure theres something in the list first
            wlistcheck = string.join(option["watchlist"].keys(), '')
            
            if len(wlistcheck) is not 0:    
                for watch_entry, watch_data in option["watchlist"].iteritems():
                    
                    #Now the fun part, we have to match against the new scc2.ini
                    check_filter = watch_data["watch_filter"]

#Remove these for super debug mode. Too annoying even for normal users.                    
#                    if watch_specific_options["debug"] == "on":
#                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Checking watchlist entry: " + color["dgrey"] + str(watch_entry)
#                            verbose(DEBUG_MESSAGE)
#                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                    
                    
                    #Generate an up-to-date representation of the default settings. These will then be overriden by watch-specific options.
                    #We do this so that if a watch entry has no options but the basics it won't fail.
                    watch_specific_defaults = {}
                    watch_specific_defaults["savepath"] = option["global"]["savepath"]
                    watch_specific_defaults["avoid_filter"] = ""
                    watch_specific_defaults["watch_categories"] = ""
                    watch_specific_defaults["watch_regex"] = "0"
                    watch_specific_defaults["avoid_regex"] = "0"
                    watch_specific_defaults["use_utorrent_webui"] = "0"
                    watch_specific_defaults["use_external_command"] = "0"
                    watch_specific_defaults["use_ftp_upload"] = option["global"]["ftpenable"]
                    watch_specific_defaults["use_emailer"] = option["global"]["smtp_emailer"]
                    watch_specific_options = DC(watch_data)
                    #Fill in any options the watch was missing using defaults, then global options
                    for key, value in watch_specific_defaults.iteritems():
                        if watch_specific_options.has_key(key) is False:
                                watch_specific_options[key] = value
                    for key, value in option["global"].iteritems():
                        if watch_specific_options.has_key(key) is False:
                                watch_specific_options[key] = value
                    
                    #Fix external command stuff
                    if len(watch_specific_options["external_command"].strip()) < 2: watch_specific_options["external_command"] = option["global"]["external_command"]
                    if len(watch_specific_options["external_command_args"].strip()) == 0: watch_specific_options["external_command_args"] = option["global"]["external_command_args"]
                    
                    
                    #now convert certain items to on and off if needed
                    watch_specific_options = convert_int_opts_to_word(watch_specific_options)
                    
                    #Yeah, I could just program this thing correctly in the first place, but fuck it! I'm in a band-aid kinda mood today.
                    watch_specific_options["utorrent_mode"] = watch_specific_options["use_utorrent_webui"]
                    watch_specific_options["ftpenable"] = watch_specific_options["use_ftp_upload"]
                    watch_specific_options["smtp_emailer"] = watch_specific_options["use_emailer"]
                    
                    #We only do this replacement when the user doesn't want regexes enabled.
                    if watch_specific_options["watch_regex"] == "off":
                        check_filter = check_filter.replace('.','\.')
                        check_filter = check_filter.replace('*','(.*)')
                        check_filter = check_filter.replace('/','\/')
                        check_filter = '^' + check_filter + '$'
                    else:
                        #Our GUI app likes to escape back slashes so we have to undo some of the damage
                        check_filter = check_filter.replace("\\\\", "\\")
                        if watch_specific_options["debug"] == "on":
                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Enabling Regex support for watch entry: %s%s" % (color["dgrey"], watch_entry)
                            verbose(DEBUG_MESSAGE)
                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                            
                    #No regex stuff in the category list...... for now
                    categories = watch_specific_options["watch_categories"].replace("/", "\/")
                    categories = categories.replace(".", "\.")
                    categories = categories.replace("*", "(.*)")
                    categories = categories.lower()
                    categories = categories.split(" ")
                    watchlist_splitted = [check_filter, categories]
                    
                    download_dir = option["global"]["savepath"]
                    
                    #do the check for release name. re.I means the search is case insensitive
                        
                    if re.search(watchlist_splitted[0], matchedtext.group(3), re.I):
                        if watch_specific_options["debug"] == "on":
                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Matched release name to watch entry: " + color["dgrey"] + str(watch_entry)
                            verbose(DEBUG_MESSAGE)
                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                        
                        for cat in watchlist_splitted[1]:
                            if re.search(cat, matchedtext.group(2).lower(), re.I):
                                counter += 1
                                #We got a good match!
                                if watch_specific_options["debug"] == "on":
                                    DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Matched category and release name for watch entry: " + color["dgrey"] + str(watch_entry)
                                    verbose(DEBUG_MESSAGE)
                                    logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                                
                                
                                #Fist we check the watch-specific avoidlist to be sure we want this watch
                                for avoid_entry in watch_specific_options["avoid_filter"].split(" "):
                                    if len(avoid_entry) < 1:
                                        continue
                                    if watch_specific_options["avoid_regex"] == "off":
                                        avoid_entry = avoid_entry.replace('.','\.')
                                        avoid_entry = avoid_entry.replace('*','')
                                        avoid_entry = avoid_entry.replace('/','\/')
                                        avoid_entry = '^(.*)' + avoid_entry + '(.*)$'
                                    else:
                                        #Unmangling escaped backslashes.
                                        avoid_entry = avoid_entry.replace("\\\\", "\\")
                                        if watch_specific_options["debug"] == "on":
                                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Enabling Regex support for avoid entry: %s%s" % (color["dgrey"], avoid_entry)
                                            verbose(DEBUG_MESSAGE)
                                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                                        
                                    if re.search(avoid_entry, matchedtext.group(3), re.I):
                                        counter = 0
                                        if watch_specific_options["debug"] == "on":
                                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Ignoring match. Matched rls to entry in watch-specific avoidlist. Matched avoidlist entry: " + color["dgrey"] + str(avoid_entry)
                                            verbose(DEBUG_MESSAGE)
                                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                                        break
                                
                                #Let's copy over our watch-specific options before we do anything else
                                #First the savepath
                                if len(watch_specific_options["savepath"]) > 2:
                                    download_dir = watch_specific_options["savepath"]
                                else:
                                    download_dir = option["global"]["savepath"]
                                
                                if download_dir is not None and len(download_dir) > 0 and download_dir[-1] != os.sep:
                                        download_dir = str(download_dir) + os.sep
                                
                                #Quickly clean up any weirdness with the sizelimits
                                #convert upper and lower sizelimits to bytes
                                try:
                                    watch_specific_options["lower_sizelimit"]
                                except:
                                    watch_specific_options["lower_sizelimit"] = ""
                                try:
                                    watch_specific_options["upper_sizelimit"]
                                except:
                                    watch_specific_options["upper_sizelimit"] = ""
                                #Ok so now we can convert our sizelimits to bytes and store them in similarly named variables, just with _bytes suffix.
                                watch_specific_options["lower_sizelimit_bytes"] = return_bytes_from_sizedetail(watch_specific_options["lower_sizelimit"])
                                watch_specific_options["upper_sizelimit_bytes"] = return_bytes_from_sizedetail(watch_specific_options["upper_sizelimit"])
                                
                                if counter > 0: break #Breaking out of cat search
                            else:
                                if watch_specific_options["debug"] == "on":
                                    DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Category match failed. Release category: " + color["dgrey"] + str(matchedtext.group(2).lower())
                                    verbose(DEBUG_MESSAGE)
                                    logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                        if counter > 0:
                            break #break out of watchlist search
                    if counter == 0:
                        #This is only really here for debug purposes, to notify when a watchlist entry doesnt match. 
                        if watch_specific_options["debug"] == "on":
                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Failed to match watchlist entry. Failed watchlist entry: " + color["dgrey"] + str(watch_entry)
                            verbose(DEBUG_MESSAGE)
                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
            
            #check if it should be avoided
            #length checks to make sure theres something in the list first
            #We check both the global avoidlist and the watch-specific avoidlist
            alistcheck = string.join(option["global"]["avoidlist"], '')
            if len(alistcheck) != 0 and userdata != "BYPASS" and counter > 0:
                #Check the global avoidlist
                for avoid_entry, avoid_data in option["avoidlist"].iteritems():
                    avoid_filter = avoid_data["avoid_filter"]
                    if len(avoid_filter) < 1:
                        continue
                    
                    #This is the ONLY place in the whole script where off is actually 0. Programmer, more like lolgrammer! AMIRITE?!
                    if int(avoid_data["avoid_regex"]) == 0:
                        avoid_filter = avoid_filter.replace('.','\.')
                        avoid_filter = avoid_filter.replace('*','')
                        avoid_filter = avoid_filter.replace('/','\/')
                        avoid_filter = '^(.*)' + avoid_filter + '(.*)$'
                    else:
                        #Unmangling escaped backslashes.
                        avoid_entry = avoid_entry.replace("\\\\", "\\")
                        if watch_specific_options["debug"] == "on":
                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Enabling Regex support for avoid entry: %s%s" % (color["dgrey"], avoid_entry)
                            verbose(DEBUG_MESSAGE)
                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                        
                    #do the check only on the release name
                    if re.search(avoid_filter, matchedtext.group(3), re.I):
                        counter = 0
                        if watch_specific_options["debug"] == "on":
                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Matched rls to entry in avoidlist. Download operation stopped. Matched avoidlist entry: " + color["dgrey"] + str(avoid_entry)
                            verbose(DEBUG_MESSAGE)
                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                        break
                    else:
                        if watch_specific_options["debug"] == "on":
                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Failed to match avoidlist entry with rls. Avoidlist entry: " + color["dgrey"] + str(avoid_entry)
                            verbose(DEBUG_MESSAGE)
                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                
            
            #Size details
            sizedetail = matchedtext.group(4).replace(')', '')
            sizedetail = sizedetail.replace('(', '')
            sizedetail = re.search("(?:([0-9]{1,6}\.[0-9]{1,2}|[0-9]{1,6})(?:\s+)?(M|m|K|k|G|g)B?)$", sizedetail) #I hate this regex
            #sizedetail.group(1) = 541.34
            #sizedetail.group(2) = M
            nicesize = sizedetail.group(1)+sizedetail.group(2)
            # Only if we're about to download should we check size
            if counter > 0 and userdata != "BYPASS":
                #Convert lower and upper size limits to raw bytes if we have them
                over_size_limit = False
                if watch_specific_options["lower_sizelimit_bytes"] > 0 or watch_specific_options["upper_sizelimit_bytes"] > 0:
                    torrent_size = int(return_bytes_from_sizedetail(nicesize))
                    #Check if it's too big or small
                    if (watch_specific_options["upper_sizelimit_bytes"] == 0) or (watch_specific_options["upper_sizelimit_bytes"] > watch_specific_options["lower_sizelimit_bytes"]): #zero means no limit. Also make sure upper is larger than lower. If upper is bigger than lower, we know its at least not 0.
                        if watch_specific_options["upper_sizelimit_bytes"] != 0 and torrent_size > watch_specific_options["upper_sizelimit_bytes"]:
                                over_size_limit = True
                        if watch_specific_options["lower_sizelimit_bytes"] != 0 and torrent_size < watch_specific_options["lower_sizelimit_bytes"]:
                                over_size_limit = True
                        
                        if over_size_limit is True:
                            # Print/Log this if needed
                            sizeavoid = color["bpurple"]+"SCCwatcher has avoided "+color["dgrey"]+matchedtext.group(3)+color["bpurple"]+" due to size constraints. "+color["blue"]+"Torrent size: "+color["dgrey"]+nicesize+color["blue"]+", Limit (lower/upper): " + color["dgrey"] + "%s/%s" % (str(watch_specific_options["lower_sizelimit"]), str(watch_specific_options["upper_sizelimit"]))
                            verbose(sizeavoid)
                            logging(xchat.strip(sizeavoid), "AVOID")
                            counter = 0
            
            #And here's the dupe check
            #only if we're about to download should we do a dupe check
            if counter > 0:
                if watch_specific_options["dupecheck"] == "on" and userdata != "BYPASS":
                    #Check for the release name in the dupe list
                    try:
                        dupelist.index(matchedtext.group(3))
                        counter = 0
                        dupeavoid = color["bpurple"]+"SCCwatcher has determined that "+color["dgrey"]+matchedtext.group(3)+color["bpurple"]+" is a dupe. Torrent not downloaded."
                        verbose(dupeavoid)
                        logging(xchat.strip(dupeavoid), "DUPE")
                    #if its not a dupe, rabblerabblerabble do nothing.
                    except:
                        if watch_specific_options["debug"] == "on":
                            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Release was not found in dupe list."
                            verbose(DEBUG_MESSAGE)
                            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                            
            #got a match!! let's download
            if (counter > 0 or userdata == "BYPASS") and userdata != "TESTING":
                if counter == 0 and userdata == "BYPASS":
                    #Manual add, don't use any of the watch-specific settings we just set up
                    del(watch_specific_options)
                    watch_specific_options = DC(option["global"])
                    for key, value in watch_specific_defaults.iteritems():
                        if watch_specific_options.has_key(key) is False:
                            watch_specific_options[key] = value
                    watch_specific_options = convert_int_opts_to_word(watch_specific_options)
                        
                #And set the download url. If download_ssl is on, generate an ssl url instead.
                if watch_specific_options["download_ssl"] == "on":
                    #downloadurl = "https://www.sceneaccess.org/downloadbig2.php/" + matchedtext.group(5) + "/" + watch_specific_options["passkey"] + "/" + matchedtext.group(3) + ".torrent"
                    downloadurl = "https://www.sceneaccess.eu/download/" + matchedtext.group(5) + "/" + watch_specific_options["passkey"] + "/" + matchedtext.group(3) + ".torrent"
                    
                    if watch_specific_options["debug"] == "on":
                        DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Using the following SSL download url: " + color["dgrey"] + str(downloadurl)
                        verbose(DEBUG_MESSAGE)
                        logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                    
                else:
                    #downloadurl = "http://www.sceneaccess.org/downloadbig2.php/" + matchedtext.group(5) + "/" + watch_specific_options["passkey"] + "/" + matchedtext.group(3) + ".torrent"
                    downloadurl = "http://www.sceneaccess.eu/download/" + matchedtext.group(5) + "/" + watch_specific_options["passkey"] + "/" + matchedtext.group(3) + ".torrent"
                    
                    if watch_specific_options["debug"] == "on":
                        DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Using the following non-SSL download url: " + color["dgrey"] + str(downloadurl)
                        verbose(DEBUG_MESSAGE)
                        logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                    
                #And make the nice_watch_entry_name a string, since later it will be needed in string format, and we wont be needing its boolean type anymore anyway.
                if userdata != "BYPASS" and userdata != "TESTING":
                        nice_watch_entry_name = str(watch_entry)
                else:
                        nice_watch_entry_name = "Manual Add"
                #Utorrent is either disabled or is working in tandom with normal download.
                if watch_specific_options["utorrent_mode"] == "off" or watch_specific_options["utorrent_mode"] == "_MIDWAY_":
                    # If theres a specified directory, run through the directory checker to make sure the dir exists and is accessable
                    if download_dir is not None:
                        # Because full_xpath is no longer global, we assign zxfpath to dir_checks return value (full_xpath)
                        dircheck_obj = dir_check(download_dir, matchedtext.group(2))
                        zxfpath = dircheck_obj.check()
                    
                    if extra_paths == "yes":
                        disp_path = zxfpath
                        filename = zxfpath + matchedtext.group(3) + ".torrent"
                    else:
                        disp_path = download_dir
                        filename = download_dir + matchedtext.group(3) + ".torrent"
                    
                    verbtext = color["bpurple"]+"SCCwatcher is downloading torrent for: "+color["dgrey"]+matchedtext.group(3)
                    verbose(verbtext)
                    verbtext = xchat.strip(verbtext) +" - "+ os.path.normcase(disp_path)
                    logging(verbtext, "GRAB")
                    #The number of passed vars has gone up in an effort to alleviate var overwrites under high load.
                    download(downloadurl, filename, zxfpath, matchedtext, disp_path, nicesize, extra_paths, nice_watch_entry_name, watch_specific_options).start()
                    # The upload will be cascaded from the download thread to prevent a train wreck.   
                # If utorrent adding is enabled, perform those operations
                if watch_specific_options["use_utorrent_webui"] == "on":
                    if watch_specific_options["utorrent_mode"] == "_MIDWAY_" or watch_specific_options["utorrent_mode"] == "on":
                        verbtext = color["bpurple"]+"SCCwatcher is adding torrent for " + color["dgrey"] + matchedtext.group(3) + color["bpurple"] + " to the uTorrent WebUI at " + color["dgrey"] + watch_specific_options["utorrent_hostname"]
                        verbose(verbtext)
                        verbtext3 = xchat.strip(verbtext)
                        logging(verbtext3, "START_UTOR_ADD")
                        webui_upload(downloadurl, matchedtext, nicesize, nice_watch_entry_name, watch_specific_options).start()
                    if watch_specific_options["utorrent_mode"] != "off" and watch_specific_options["utorrent_mode"] != "_MIDWAY_" and watch_specific_options["utorrent_mode"] != "on":
                        verbtext = color["bpurple"]+"SCCwatcher cannot download because you have set utorrent_mode to an invalid number. Please check your scc2.ini and fix this error. utorrent_mode is currently set to: " + color["dgrey"] + watch_specific_options["utorrent_mode"]
                        verbose(verbtext)
            
            elif userdata == "TESTING" and counter > 0:
                verbose_text = color["bpurple"] + "SCCwatcher would have downloaded that release."
                verbose(verbose_text)
            elif userdata == "TESTING" and counter == 0:
                verbose_text = color["bpurple"] + "SCCwatcher would NOT have downloaded that release."
                verbose(verbose_text)

def return_bytes_from_sizedetail(sizedetail):
    multi = 1
    if sizedetail == "" or sizedetail is None or len(sizedetail) < 2:
        return (0)
    sizedetail_reg = re.search("([0-9]{1,6}(?:\.[0-9]{1,2})?)(?:(.*)(M|m|K|k|G|g)B?)?(.*)", sizedetail)
    if sizedetail_reg is None:
        print color["dgrey"] + str(sizedetail) + color["red"] + " is not a valid entry for sizelimit. Valid examples: 150K, 150M, 150G. Ignoring set size limit."
        return(0)
    nicesize = str(sizedetail_reg.group(3)).lower()
    
    if nicesize == "":
        multi=1
    elif nicesize == "k":
        multi=1024
    elif nicesize == "m":
        multi=(1024**2)
    elif nicesize == "g":
        multi=(1024**3)
    elif nicesize == "t":
        multi=(1024**4)

    return_size = float(sizedetail_reg.group(1)) * multi
    return int(return_size)
        

def more_help(command):
    command = command.lower()
    if command == 'help':
        print color["bpurple"], "Help: " + color["blue"] + "Displays all of the currently accepted commands. Can also provide additional help on individual commands: "+color["dgrey"]+"/sccwatcher help <command>"
    elif command == 'loud':
        print color["bpurple"], "Loud: " + color["blue"] + "Turns verbose output on."
    elif command == 'quiet':
        print color["bpurple"], "Quiet: " + color["blue"] + "Turns verbose output off"
    elif command == 'rehash':
        print color["bpurple"], "Rehash : " + color["blue"] + "Reloads settings from scc2.ini. "+color["red"]+"WARNING:"+color["blue"]+" All temporary adds will be lost upon doing this."
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
        print color["bpurple"], "Updateftp: " + color["blue"] + "Allows you to update your ftpdetails, must be in the format of:"+color["dgrey"]+" ftp://user:password@server:port/directory "
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
        print color["bpurple"], "cmdon: " + color["blue"] + "This will enable the execution of a specified external command, as configured in scc2.ini."
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
            option["global"]["ftpdetails"] = details
        else:
            print color["red"]+"There is a problem with your ftp details, the proper format is: ftp://username:password@server:port/directory"
    
def add_avoid(item):
    if item is not None:
        print "Temporarily adding", color["bpurple"]+item,color["black"]+"to the avoidlist"
        #Check if the list is empty
        if len(string.join(option["global"]["avoidlist"], ' ')) > 0:
            option["global"]["avoidlist"].append(item)
        else:
            option["global"]["avoidlist"] = [item]
        #Add to the menu
        xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s"' % str(item))
        xchat.command('menu add "SCCwatcher/Avoidlist/Temporarily Remove Avoid/%s/Confirm Remove" "sccwatcher remavoid %s"' % (str(item), str(item)))
    else:
        print color["red"], "Invalid entry. Add cannot be empty"

def remove_avoid(delitem):
    if delitem is not None:
        #make sure its in the avoidlist to begin with
        try:
            option["global"]["avoidlist"].index(delitem)
            print "Temporarily removing", color["bpurple"]+delitem,color["black"]+"from the avoidlist"
            option["global"]["avoidlist"].remove(delitem)
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
        if len(string.join(option["global"]["watchlist"], ' ')) > 0:
            option["global"]["watchlist"].append(item)
        else:
            option["global"]["watchlist"] = [item]
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
            option["global"]["watchlist"].index(delitem)
            print "Temporarily removing", color["bpurple"]+delitem,color["black"]+"from the watchlist"
            option["global"]["watchlist"].remove(delitem)
            
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
    def __init__(self, dlurl, flname, zxfpath, matchedtext, disp_path, nicesize, extra_paths, nice_watch_entry_name, specific_options):
        self.dlurl = dlurl
        self.flname = flname
        self.zxfpath = zxfpath
        self.matchedtext = matchedtext
        self.disp_path = disp_path
        self.nicesize = nicesize
        self.extra_paths = extra_paths
        self.nice_watch_entry_name = nice_watch_entry_name
        self.specific_options = specific_options
        threading.Thread.__init__(self)
    def run(self):
        if self.specific_options["debug"] == "on":
                DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Entered download thread."
                verbose(DEBUG_MESSAGE)
                logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
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
            
            if option["global"]["debug"] == "on":
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
                
                if option["global"]["debug"] == "on":
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
                    if option["global"]["debug"] == "on":
                        DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Cloudflare interference verified. Using cloudflare workaround next try..."
                        verbose(DEBUG_MESSAGE)
                        logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
        
        
        if thread_data.torrent_is_valid == False:
        #Delete the bad file
            os.remove(tfile)
            # Have we reached the retry limit?
            if self.count <= int(option["global"]["max_dl_tries"]):
                #Sleep a second to give the server some breathing room.
                time.sleep(int(option["global"]["retry_wait"]))
                #Then download again
                self.download(stime, thread_data.need_cf_bypass)
            #We have reached the limit, verbose/log event and discontinue download operations.
            else:
                self.final_output(False, stime)
        else:
            self.final_output(True, stime)
        
    def download(self, stime, req=False):
        thread_data = threading.local()
        
        if self.specific_options["debug"] == "on":
            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Starting download process."
            verbose(DEBUG_MESSAGE)
            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                
        
        # And here we download. This wont hold up the main thread because this class is in a subthread,
        #Using a try-except here incase urlretrieve has problems
        try:
            #If we have the option, use the cookiefile and bypass the cloudflare protection.
            if option["global"].has_key("cfbypass_cookiefile") and len(option["global"]["cfbypass_cookiefile"]) > 2 and option["global"].has_key("cfbypass_useragent") and len(option["global"]["cfbypass_useragent"]) > 5 and req is True:
                
                #DBG
                if self.specific_options["debug"] == "on":
                    DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Found cookiefile and useragent option, length checks good."
                    verbose(DEBUG_MESSAGE)
                    logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                #END DBG
                
                
                thread_data.cookie_path = option["global"]["savepath"] + option["global"]["cfbypass_cookiefile"]
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
                if self.specific_options["debug"] == "on":
                    DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Finished downloading and saved to file."
                    verbose(DEBUG_MESSAGE)
                    logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                #END DBG
                
            else:
                
                #DBG
                if self.specific_options["debug"] == "on" and req is True:
                    DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: No cookiefile or useragent option or length checks failed."
                    verbose(DEBUG_MESSAGE)
                    logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                #END DBG    
                    
                #Download normally
                thread_data.opener = sccwDownloader()
                thread_data.dl = thread_data.opener.retrieve(self.dlurl, self.flname)            
                #thread_data.dl = urllib.urlretrieve(self.dlurl, self.flname)
                
                
                #DBG
                if self.specific_options["debug"] == "on":
                    DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: finished normal download"
                    verbose(DEBUG_MESSAGE)
                    logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                #END DBG    
            
            #thread_data.dl = urllib.urlretrieve(self.dlurl, self.flname)
        #Problem with urllib, so we create a blank file and send it to the size check. It will fail the check and redownload
        except:
            try:
                blankfile = open(self.flname, 'w')
                blankfile.write("")
                blankfile.close()
            except:
                thread_data.dlerror = color["bpurple"] + "SCCwatcher encountered an error while writing the torrent file. Torrent was NOT downloaded. Please check the following path is writable: " + color["dgrey"] + self.flname
                verbose(thread_data.dlerror)
                thread_data.dlerror = xchat.strip(thread_data.dlerror)
                logging(thread_data.dlerror, "GRAB_WRITE_FAIL")
                return False
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
            
            thread_data.dldir = os.path.dirname(self.flname)
            thread_data.verbtext3 = color["bpurple"] + "SCCwatcher successfully downloaded torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " to " + color["dgrey"] + thread_data.dldir + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds."
            if self.count > 1:
                thread_data.verbtext3 += " Total retry's: " + color["dgrey"] + str(self.count)
            verbose(thread_data.verbtext3)
            thread_data.verbtext3 = xchat.strip(thread_data.verbtext3) +" - "+ os.path.normcase(self.disp_path)
            logging(thread_data.verbtext3, "END_GRAB")
            
            #Download definitely succeeded, now we can add to the dupe list
            if self.specific_options["debug"] == "on" and self.specific_options["dupecheck"] == "on":
                DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Added the following release to dupe list: " + color["dgrey"] + str(self.matchedtext.group(3))
                verbose(DEBUG_MESSAGE)
                logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
            update_dupe(self.matchedtext.group(3))
            
            #Ok now that we have the file, we can do the upload if necessary:
            #If we're doing an upload, then dont do an email or external command, as that will be handled by the upload class.
            if self.specific_options["ftpenable"] == 'on':
                upload(self.flname, self.zxfpath, self.matchedtext, self.disp_path, self.extra_paths, self.nicesize, self.nice_watch_entry_name, self.specific_options).start()
            else:
                #If emailing is enabled, dont do external command as that will be handled by the email class.
                if self.specific_options["smtp_emailer"] == "on":
                    email(self.matchedtext, self.disp_path, self.nicesize, self.nice_watch_entry_name, self.specific_options).start()
                else:
                    if self.specific_options["use_external_command"] == "on":
                        do_cmd(self.matchedtext, self.disp_path, self.nicesize, self.nice_watch_entry_name, self.specific_options).start()
        else:
            thread_data.verbtext3 = color["bpurple"]+"SCCwatcher failed to downloaded torrent for "+color["dgrey"] + self.matchedtext.group(3) + color["bpurple"]+" after " +color["dgrey"]+ option["global"]["max_dl_tries"] + color["bpurple"]+" tries. Manually download at: " +color["dgrey"]+ self.dlurl
            verbose(thread_data.verbtext3)
            thread_data.verbtext3 = xchat.strip(thread_data.verbtext3) +" - "+ os.path.normcase(self.disp_path)
            logging(thread_data.verbtext3, "END_GRAB_FAILED")
    
#threaded upload class
class upload(threading.Thread):
    def __init__(self, torrentname, zxfpath, matchedtext, disp_path, extra_paths, nicesize, nice_watch_entry_name, specific_options):
        self.torrentname = torrentname
        self.zxfpath = zxfpath
        self.matchedtext = matchedtext        
        self.disp_path = disp_path
        self.extra_paths = extra_paths
        self.nicesize = nicesize
        self.nice_watch_entry_name = nice_watch_entry_name
        self.specific_options = specific_options
        threading.Thread.__init__(self)
    #Uploading tiem nao!!!!
    def run(self):
        if self.specific_options["debug"] == "on":
            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: FTP Upload operation has started."
            verbose(DEBUG_MESSAGE)
            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                
        #create thread-local data to further prevent var overwrites under high load
        thread_data = threading.local()
        #try to see if the ftp details are available, if the are: upload
        thread_data.ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["global"]["ftpdetails"])
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
            try:
                thread_data.s.connect(thread_data.ftpdetails.group(3), thread_data.ftpdetails.group(4)) # Connect
            except:
                thread_data.vtext = color["bpurple"] + "SCCwatcher encountered an error while attempting to connect to the ftp server at " + color["dgrey"] + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + ". " + color["bpurple"] + "Skipping FTP Upload. Please check your configuration and be sure your user has access to the directory on the remote server."
                verbose(thread_data.vtext)
                logging(xchat.strip(thread_data.vtext), "UPLOAD_FAIL-CONNECT_FAIL")
                return False
            thread_data.s.login(thread_data.ftpdetails.group(1), thread_data.ftpdetails.group(2)) # Login
            if option["global"]["ftppassive"] == 'on':
                thread_data.s.set_pasv(True) # Set passive-mode 
            try:
                thread_data.s.cwd("/" + thread_data.ftpdetails.group(5)) # Change directory
            except:
                thread_data.vtext = color["bpurple"] + "SCCwatcher encountered an error while changing the directory to " + color["dgrey"] + "/" + thread_data.ftpdetails.group(5) + ". " + color["bpurple"] + "Skipping FTP Upload. Please check your configuration and be sure your user has access to the directory on the remote server."
                verbose(thread_data.vtext)
                logging(xchat.strip(thread_data.vtext), "UPLOAD_FAIL-CHDIR_FAIL")
                return False
            if self.extra_paths == "yes":
                thread_data.f = open(self.zxfpath + self.matchedtext.group(3) + ".torrent",'rb') # Open file to send
            else:
                thread_data.f = open(option["global"]["savepath"] + self.matchedtext.group(3) + ".torrent",'rb') # Open file to send
            
            thread_data.uc = 0
            thread_data.uploaded = False
            #  Eliminate errors while uploading by using try-except protection. Uses the max_dl_tries variable to know how many tries to 
            while thread_data.uploaded is False:
                if thread_data.uc < int(option["global"]["max_dl_tries"]):
                    try:
                        thread_data.s.storbinary('STOR ' + self.matchedtext.group(3) + ".torrent", thread_data.f) # Send the file
                        thread_data.uploaded = True
                        break
                    except:
                        thread_data.vtext = color["bpurple"] + "SCCwatcher encountered an error while uploading " + color["dgrey"] + self.matchedtext.group(3) + ".torrent." + color["bpurple"] + " Retrying...."
                        verbose(thread_data.vtext)
                        logging(xchat.strip(thread_data.vtext), "UPLOAD_FAIL-RETRYING")
                        thread_data.uc += 1
                        time.sleep(int(option["global"]["retry_wait"]))
                else:
                    thread_data.vtext = color["bpurple"] + "SCCwatcher cannot upload " + color["dgrey"] + self.matchedtext.group(3) + ".torrent" + color["bpurple"] + " to the specified FTP server. Please make sure the server is functioning properly."
                    verbose(thread_data.vtext)
                    logging(xchat.strip(thread_data.vtext), "UPLOAD_FAIL_FINAL")
                    break
                
            thread_data.f.close() # Close file
            thread_data.s.quit() # Close ftp
            
            if thread_data.uploaded == True:
                self.upload_finish(thread_data.start_time2, thread_data.ftpdetails)
            
        else:
            print color["red"]+"There is a problem with your ftp details, please double check scc2.ini and make sure you have entered them properly. Temporarily disabling FTP uploading, you can reenable it by using /sccwatcher ftpon"
            option["global"]["ftpenable"] = 'off'
            xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
        if option["global"]["smtp_emailer"] == "on":
            email(self.matchedtext, self.disp_path, self.nicesize, self.nice_watch_entry_name).start()
        else:
            if option["global"]["use_external_command"] == "on":
                do_cmd(self.matchedtext, self.disp_path, self.nicesize, self.nice_watch_entry_name).start()
        
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
#Had to update a lot of this code in June 2016 due to not using token auth. 
class webui_upload(threading.Thread):
    def __init__(self, turl, matchedtext, nicesize, nice_watch_entry_name, specific_options):
        self.turl = turl
        self.matchedtext = matchedtext
        self.nicesize = nicesize
        self.nice_watch_entry_name = nice_watch_entry_name
        self.specific_options = specific_options
        threading.Thread.__init__(self)    
        
    def run(self):
        print self.specific_options["debug"]
        if self.specific_options["debug"] == "on":
            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: uTorrent WebUI upload operation has started."
            verbose(DEBUG_MESSAGE)
            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
                
        #create thread-local data to further prevent var overwrites under high load
        thread_data = threading.local()
        thread_data.torrent_url = urllib.quote(self.turl) # Escape the url
        #Generate our authentication details
        thread_data.base64string = base64.encodestring('%s:%s' % (option["global"]["utorrent_username"], option["global"]["utorrent_password"])).strip() 
        thread_data.authheader =  "Basic %s" % thread_data.base64string
        #Before we can add a torrent we need to generate a token
        thread_data.token_url = 'http://' + option["global"]["utorrent_hostname"] +':'+ option["global"]["utorrent_port"] + "/gui/token.html"
        thread_data.token_req = urllib2.Request(thread_data.token_url)
        thread_data.token_req.add_header("Authorization", thread_data.authheader)
        try:
            thread_data.token_html = urllib2.urlopen(thread_data.token_req).read()
        except Exception as e:
            if "401" in e:
                thread_data.error = color["bpurple"]+"DEBUG_OUTPUT: Failed to authenticate with the remote uTorrent WebUI. Please check your username/password combination."
            else:
                thread_data.error = color["bpurple"]+"SCCwatcher encountered an HTTP error while connecting to the uTorrent WebUI at " + color["dgrey"] + option["global"]["utorrent_hostname"] + ":" + option["global"]["utorrent_port"] + color["bpurple"] + ". Please double check the uTorrent WebUI settings in scc2.ini are correct."
            verbose(thread_data.error)
            logging(xchat.strip(thread_data.error), "END_UTOR_ADD_FAIL")
            return False
        thread_data.auth_token = re.search("'>(.*?)</div>", thread_data.token_html).group(1)
        #Ok now that we have our token, we can add the torrent to the WebUI
        thread_data.http_url = 'http://' + option["global"]["utorrent_hostname"] +':'+ option["global"]["utorrent_port"] + '/gui/?token=%s&action=add-url&s=%s' % (thread_data.auth_token, thread_data.torrent_url) # Make the url
        # Basic Auth using base64
        #start timer
        thread_data.start_time = time.time()
        thread_data.http_data = urllib2.Request(thread_data.http_url)
        thread_data.http_data.add_header("Authorization", thread_data.authheader)
        thread_data.http_data.add_header('User-Agent','Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.0)') # Pretend we are Internet Explorer
        thread_data.good = 0
        try:
            thread_data.text = urllib2.urlopen(thread_data.http_data).read() # get the data
            thread_data.good = 1
        except:
            thread_data.error = color["bpurple"]+"SCCwatcher encountered an HTTP error while connecting to the uTorrent WebUI at " + color["dgrey"] + option["global"]["utorrent_hostname"] + color["bpurple"] + ". Please double check the uTorrent WebUI settings in scc2.ini are correct."
            verbose(thread_data.error)
            thread_data.good = 0
        if thread_data.good == 1:
            #end timer
            thread_data.end_time = time.time()
            thread_data.duration = thread_data.end_time - thread_data.start_time
            thread_data.duration = str(round(thread_data.duration, 3))
            # If only uTorrent uploading is active, update the recent using WEBUI as the disp_path
            if option["global"]["utorrent_mode"] == "on":
                thread_data.webuiloc = "WEBUI-" + option["global"]["utorrent_hostname"]
                update_recent(self.matchedtext.group(3), thread_data.webuiloc, self.nicesize, thread_data.duration)
                if option["global"]["smtp_emailer"] == "on":
                    email(self.matchedtext, "NONE", self.nicesize, self.nice_watch_entry_name).start()
                else:
                    if option["global"]["use_external_command"] == "on":
                        do_cmd(self.matchedtext, "NONE", self.nicesize, self.nice_watch_entry_name).start()
                
            thread_data.verbtext = color["bpurple"]+"SCCwatcher successfully added torrent for " + color["dgrey"] + self.matchedtext.group(3) + color["bpurple"] + " to the uTorrent WebUI at " + color["dgrey"] + option["global"]["utorrent_hostname"] + ":" + option["global"]["utorrent_port"] + color["bpurple"] + " in " + color["dgrey"] + thread_data.duration + color["bpurple"] + " seconds."
            verbose(thread_data.verbtext)
            thread_data.verbtext3 = xchat.strip(thread_data.verbtext)
            logging(thread_data.verbtext3, "END_UTOR_ADD")
        if thread_data.good == 0:
            thread_data.verbtext3 = xchat.strip(thread_data.error)
            logging(thread_data.verbtext3, "END_UTOR_ADD")
        
class email(threading.Thread):
    def __init__(self, matchedtext, disp_path, nicesize, nice_watch_entry_name, specific_options):
        self.matchedtext = matchedtext
        self.disp_path = disp_path
        self.nicesize = nicesize
        self.nice_watch_entry_name = nice_watch_entry_name
        self.specific_options = specific_options
        threading.Thread.__init__(self)    
    #Send tiem nao
    def run(self):
        if self.specific_options["debug"] == "on":
            DEBUG_MESSAGE = color["bpurple"]+"DEBUG_OUTPUT: Email operation has started."
            verbose(DEBUG_MESSAGE)
            logging(xchat.strip(DEBUG_MESSAGE), "DEBUG_OUTPUT")
        #create thread-local data to further prevent var overwrites under high load
        thread_data = threading.local()
        #connect to the server
        try:
            thread_data.smtpconn = smtplib.SMTP(option["global"]["smtp_server"], option["global"]["smtp_port"])
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
            if option["global"]["smtp_tls"] == "on":
                thread_data.smtpconn.starttls()
                thread_data.smtpconn.ehlo()
            #If the user gave a username/password, log in with it.
            if len(option["global"]["smtp_username"]) > 0:
                try:
                    thread_data.smtpconn.login(option["global"]["smtp_username"], option["global"]["smtp_password"])
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
                    thread_data.smtpconn.sendmail(option["global"]["smtp_from"], option["global"]["smtp_to"], self.message_builder())
                    thread_data.smtpconn.close()
                    thread_data.verbtext=color["bpurple"]+"SCCwatcher successfully emailed " + color["dgrey"] + option["global"]["smtp_to"]
                    verbose(thread_data.verbtext)
                    thread_data.verbtext = xchat.strip(thread_data.verbtext)
                    logging(xchat.strip(thread_data.verbtext), "SMTP_SUCCESS")
                except:
                    thread_data.verbtext=color["bpurple"]+"SCCwatcher encountered an error while talking to the SMTP server, no email was sent"
                    verbose(thread_data.verbtext)
                    thread_data.verbtext = xchat.strip(thread_data.verbtext)
                    logging(xchat.strip(thread_data.verbtext), "SMTP_FAIL")
        if option["global"]["use_external_command"] == "on":
            do_cmd(self.matchedtext, self.disp_path, self.nicesize, self.nice_watch_entry_name, self.specific_options).start()

    #Here we build our email message
    def message_builder(self):
        thread_data = threading.local()
        thread_data.current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        #Here we replace all the special strings with actual data
        # Acceptable special strings are:
        # %torrent% %category% %size% %time% %dlpath% %ulpath% %utserver% %watchname% %torrentpath% %sccgrptree% %sccgrp% %sccdate%
        # To see what they mean, just see below.
        thread_data.sccgrp = self.matchedtext.group(2)
        thread_data.sccgrp = thread_data.sccgrp.replace('/','.')
        thread_data.sccgrp = thread_data.sccgrp.replace('-','.')
        thread_data.sccgrptree = self.matchedtext.group(2)
        thread_data.sccgrptree = thread_data.sccgrptree.replace('-', os.sep)
        thread_data.sccgrptree = thread_data.sccgrptree.replace('/', os.sep)
        thread_data.sccdate = time.strftime("%m%d", time.localtime())
        
        thread_data.fulltpath = self.disp_path + self.matchedtext.group(3) + ".torrent"
        thread_data.ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["global"]["ftpdetails"])
        if thread_data.ftpdetails is not None:
            thread_data.ftpstring = "ftp://" + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5)
        else:
            thread_data.ftpstring = "BAD_FTP_DETAILS"
        thread_data.utstring = option["global"]["utorrent_hostname"] + ":" + option["global"]["utorrent_port"]
        
        
        thread_data.email_body = option["global"]["smtp_message"].replace('%torrent%', self.matchedtext.group(3))
        thread_data.email_body = thread_data.email_body.replace('%category%', self.matchedtext.group(2))
        thread_data.email_body = thread_data.email_body.replace('%size%', self.nicesize)
        thread_data.email_body = thread_data.email_body.replace('%time%', thread_data.current_time)
        thread_data.email_body = thread_data.email_body.replace('%dlpath%', self.disp_path)
        thread_data.email_body = thread_data.email_body.replace('%ulpath%', thread_data.ftpstring)
        thread_data.email_body = thread_data.email_body.replace('%utserver%', thread_data.utstring)
        thread_data.email_body = thread_data.email_body.replace('%watchname%', self.nice_watch_entry_name)
        thread_data.email_body = thread_data.email_body.replace('%torrentpath%', thread_data.fulltpath)
        thread_data.email_body = thread_data.email_body.replace('%sccgrptree%', thread_data.sccgrptree)
        thread_data.email_body = thread_data.email_body.replace('%sccgrp%', thread_data.sccgrp)
        thread_data.email_body = thread_data.email_body.replace('%sccdate%', thread_data.sccdate)
        
        thread_data.email_subject = option["global"]["smtp_subject"].replace('%torrent%', self.matchedtext.group(3))
        thread_data.email_subject = thread_data.email_subject.replace('%category%', self.matchedtext.group(2))
        thread_data.email_subject = thread_data.email_subject.replace('%size%', self.nicesize)
        thread_data.email_subject = thread_data.email_subject.replace('%time%', thread_data.current_time)
        thread_data.email_subject = thread_data.email_subject.replace('%dlpath%', self.disp_path)
        thread_data.email_subject = thread_data.email_subject.replace('%ulpath%', thread_data.ftpstring)
        thread_data.email_subject = thread_data.email_subject.replace('%utserver%', thread_data.utstring)
        thread_data.email_subject = thread_data.email_subject.replace('%watchname%', self.nice_watch_entry_name)
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
    def __init__(self, matchedtext, disp_path, nicesize, nice_watch_entry_name, specific_options):
        self.matchedtext = matchedtext
        self.disp_path = disp_path
        self.nicesize = nicesize
        self.nice_watch_entry_name = nice_watch_entry_name
        self.specific_options = specific_options
        threading.Thread.__init__(self)    
    #Send tiem nao
    def run(self):
        if self.specific_options["debug"] == "on":
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
        thread_data.ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["global"]["ftpdetails"])
        if thread_data.ftpdetails is not None:
            thread_data.ftpstring = "ftp://" + thread_data.ftpdetails.group(3) + ":" + thread_data.ftpdetails.group(4) + "/" + thread_data.ftpdetails.group(5)
        else:
            thread_data.ftpstring = "BAD_FTP_DETAILS"
        thread_data.utstring = option["global"]["utorrent_hostname"] + ":" + option["global"]["utorrent_port"]
        thread_data.nice_cat = self.matchedtext.group(2).replace('/','-')
        thread_data.command_args =  self.specific_options["external_command_args"].replace('%torrent%', self.matchedtext.group(3))
        thread_data.command_args = thread_data.command_args.replace('%category%', thread_data.nice_cat)
        thread_data.command_args = thread_data.command_args.replace('%size%', self.nicesize)
        thread_data.command_args = thread_data.command_args.replace('%time%', thread_data.current_time)
        thread_data.command_args = thread_data.command_args.replace('%dlpath%', self.disp_path)
        thread_data.command_args = thread_data.command_args.replace('%ulpath%', thread_data.ftpstring)
        thread_data.command_args = thread_data.command_args.replace('%utserver%', thread_data.utstring)
        thread_data.command_args = thread_data.command_args.replace('%watchname%', self.nice_watch_entry_name)
        thread_data.command_args = thread_data.command_args.replace('%torrentpath%', thread_data.fulltpath)
        thread_data.command_args = thread_data.command_args.replace('%sccgrptree%', thread_data.sccgrptree)
        thread_data.command_args = thread_data.command_args.replace('%sccgrp%', thread_data.sccgrp)
        thread_data.command_args = thread_data.command_args.replace('%sccdate%', thread_data.sccdate)
        
        thread_data.command_string =  self.specific_options["external_command"] + " " + thread_data.command_args
        
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
        except Exception as e:
            thread_data.verbtext=color["bpurple"]+"SCCwatcher encountered an error running: " + color["dgrey"] + thread_data.command_string
            verbose(thread_data.verbtext)
            thread_data.verbtext = xchat.strip(thread_data.verbtext)
            logging(xchat.strip(thread_data.verbtext), "EXT_CMD_FAIL")
            if self.specific_options["debug"] == "on":
                verbose("The specific error was: ")
                verbose(str(e))
                e = "The specific error was: %s" % str(e)
                logging(xchat.strip(e), "EXT_CMD_FAIL-DEBUG")
            


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
        sccwhelp(ftrigger)
    except:
        print "No argument given, for help type: /sccwatcher help"
    return xchat.EAT_ALL

def sccwhelp(trigger):
    global recent_list, option, last5recent_list
    #For use with custom tabs.
    sop_outtext = color["red"] + "SCCwatcher will now use this tab for all verbose output. Use /sccwatcher anytab to go back to the original way sccwatcher outputs."
    
    try:
        option["global"]["sizelimit"]
    except:
        option["global"]["sizelimit"] = ""
        
    if trigger[1] == 'help':
        try:
            trigger[2]
            more_help(trigger[2])
        except:
            print color["blue"], "Current accepted commands are: "
            print color["dgrey"], "Help, Loud, Quiet, Rehash, Addwatch, Addavoid, Remwatch, Remavoid, Status, Watchlist, Avoidlist, On, Off, ftpon, ftpoff, updateftp, ftpdetails, logon, logoff, recent, recentclear, detectnetwork, emailon, emailoff, anytab, thistab, sccab, sslon, ssloff, cmdon, cmdoff, manualadd" 
            print color["blue"], "To see info on individual commands use: "+color["bpurple"]+"/sccwatcher help <command>"
            
    elif trigger[1] == 'ftpon':
        ftpdetails = re.match("ftp:\/\/(.*):(.*)@(.*):([^\/]*.)/(.*)", option["global"]["ftpdetails"])
        if ftpdetails is not None:
            print color["blue"]+"FTP Uploading is now enabled, use 'ftpoff' to turn it back off"
            option["global"]["ftpenable"] = 'on'
            xchat.command('menu -t1 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
        else:
            xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
            print color["red"]+"There is a problem with your ftp details, please double check scc2.ini and make sure you have entered them properly. You can also you 'updateftp' to update the FTP details"
    
    elif trigger[1] == 'ftpoff':
        print color["blue"]+"FTP Uploading is now disabled, use 'ftpon' to turn it back on"
        xchat.command('menu -t0 add "SCCwatcher/FTP Uploading" "sccwatcher ftpon" "sccwatcher ftpoff"')
        option["global"]["ftpenable"] = 'off'
    
    elif trigger[1] == 'updateftp':
        update_ftp(trigger[2])
    
    elif trigger[1] == 'ftpdetails':
        print color["bpurple"], "Current FTPdetails are: " + color["blue"] + option["global"]["ftpdetails"]
    
    elif trigger[1] == 'detectnetwork':
        starttimer(0)
    
    elif trigger[1] == 'loud':
        print color["blue"]+"Verbose output turned on, use 'quiet' to turn it back off"
        option["global"]["verbose"] = 'on'
        xchat.command('menu -t1 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')

    elif trigger[1] == 'quiet':
        print color["blue"]+"Verbose output turned off, use 'loud' to turn it back on"
        option["global"]["verbose"] = 'off'
        xchat.command('menu -t0 add "SCCwatcher/Verbose Output" "sccwatcher loud" "sccwatcher quiet"')

    elif trigger[1] == 'rehash' or trigger[1] == "reload":
        print color["blue"], "Reloading scc2.ini...."
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
        option["global"]["logenabled"] = 'on'
        xchat.command('menu -t1 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')
    
    elif trigger[1] == 'logoff':
        print color["blue"]+"Logging to file is now turned off, use 'logon' to turn it back on"
        option["global"]["logenabled"] = 'off'
        xchat.command('menu -t0 add "SCCwatcher/Logging to File" "sccwatcher logon" "sccwatcher logoff"')

    elif trigger[1] == 'status':
        print color["bpurple"], "SCCwatcher version " +color["blue"] + __module_version__
        if option["global"]["debug"] == "on":
            print color["bpurple"], "Debug output is: " + color["blue"] + option["global"]["debug"]
        print color["bpurple"], "Auto downloading is: " + color["blue"] + option["global"]["service"]
        print color["bpurple"], "SSL downloading is: " + color["blue"] + option["global"]["download_ssl"]
        if option["global"].has_key("cfbypass_cookiefile") and len(option["global"]["cfbypass_cookiefile"]) > 2 and option["global"].has_key("cfbypass_useragent") and len(option["global"]["cfbypass_useragent"]) > 5:
            print color["bpurple"], "Cloudflare workaround is " + color["blue"] + "Enabled"
        else:
            print color["bpurple"], "Cloudflare workaround is " + color["blue"] + "Disabled"
        
        print color["bpurple"], "Maximum redownload tries is : " + color["blue"] + option["global"]["max_dl_tries"]
        print color["bpurple"], "Delay (in seconds) between download retry is: " + color["blue"] + option["global"]["retry_wait"]
        print color["bpurple"], "Dupechecking is: " + color["blue"] + option["global"]["dupecheck"]
        
        #Shorthand to make the code cleaner
        ul = option["global"]["upper_sizelimit"] # Upper Limit
        ll = option["global"]["lower_sizelimit"] # Lower Limit
        if ul is None or ul == "" or ul == 0 or len(ul) < 2:
                ul = "No Upper Limit"
        if ll is None or ll == "" or ll == 0 or len(ll) < 2:
                ll = "No Lower Limit"
        
        print color["bpurple"], "Torrent size limit (lower): " + color["blue"] + ll
        print color["bpurple"], "Torrent size limit (upper): " + color["blue"] + ul
        
        print color["bpurple"], "Recent list size: " + color["blue"] + str(len(recent_list)) + color["bpurple"] + " items."
        print color["bpurple"], "Start delay is set to:" + color["blue"],option["global"]["startdelay"]+ " seconds"
        print color["bpurple"], "Verbose output is: " + color["blue"] + option["global"]["verbose"]
        print color["bpurple"], "Using custom tab for verbose output is: " + color["blue"] + option["global"]["_extra_context_"]
        print color["bpurple"], "Logging to file is: " + color["blue"] + option["global"]["logenabled"]
        print color["bpurple"], "Uploading to ftp is: " + color["blue"] + option["global"]["ftpenable"]
        
        if int(option["global"]["utorrent_mode"]) == 0: ut_mode = "Disabled"
        elif int(option["global"]["utorrent_mode"]) == 1: ut_mode = "Normal DL and WebUI Upload"
        elif int(option["global"]["utorrent_mode"]) == 2: ut_mode = "WebUI Uploading Only"
        else: ut_mode = "Disabled"
        print color["bpurple"], "uTorrent WebUI Mode: " + color["blue"] + ut_mode
        print color["bpurple"], "Savepath is set to: " + color["blue"] + option["global"]["savepath"]
        print color["bpurple"], "Logpath is set to: " + color["blue"] + option["global"]["logpath"]
        print color["bpurple"], "Emailing is set to: " + color["blue"] + option["global"]["smtp_emailer"]
        if option["global"]["smtp_emailer"] == "on":
            print color["bpurple"], "Email server is: " + color["blue"] + str(option["global"]["smtp_server"]) + ":" + option["global"]["smtp_port"]
            print color["bpurple"], "Email TLS is set to: " + color["blue"] + str(option["global"]["smtp_tls"])
        if option["global"]["use_external_command"] == "on":
            print color["bpurple"], "External command is: " + color["blue"] + option["global"]["use_external_command"].strip()
        else:
            print color["bpurple"], "External command is: " + color["blue"] + "Off"
            
        
        print color["lblue"], "Current watchlist: " + color["dgreen"] + str(option["global"]["watchlist"])
        print color["lblue"], "Current avoidlist: " + color["dred"] + str(option["global"]["avoidlist"])
        
        
    elif trigger[1] == 'watchlist':
        print color["lblue"] + "Current watchlist: " + color["dgreen"] + str(option["global"]["watchlist"])
        
    elif trigger[1] == 'avoidlist':
        print color["lblue"] + "Current avoidlist: " + color["dred"] + str(option["global"]["avoidlist"])
    
    elif trigger[1] == 'off':
        option["global"]["service"] = 'off'
        xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
        print color["red"], "Autodownloading has been turned off"

    elif trigger[1] == 'on':
        if option["global"]["service"] == 'notdetected':
            xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
            print color["red"] + "Didn't detected the correct network infos! Autodownloading is disabled. Make sure you have joined #announce channel and then redetect the network through the SCCwatcher toolbar menu."      
        else:
            if len(option["global"]["passkey"]) == 32:
                if xchat.find_context(channel='#announce') is not None:
                        option["global"]["service"] = 'on'
                        xchat.command('menu -t1 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
                        print color["dgreen"] + "Autodownloading has been turned on"
                else:
                        option["global"]["service"] = 'off'
                        print color["red"] + "Didn't detected the correct network infos! Autodownloading is disabled. Make sure you have joined #announce channel and then redetect the network through the SCCwatcher toolbar menu."      
                        xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
            else:
                option["global"]["service"] = 'off'
                print color["red"] + "Your passkey is incomplete, please double check it and try again."
                xchat.command('menu -t0 add "SCCwatcher/Enable Autograbbing" "sccwatcher on" "sccwatcher off"')
    
    elif trigger[1] == 'emailoff':
        option["global"]["smtp_emailer"] = 'off'
        xchat.command('menu -t0 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')
        print color["red"], "Emailing has been turned off, use 'emailon' to turn it back on"
    
    elif trigger[1] == 'emailon':
        option["global"]["smtp_emailer"] = 'on'
        xchat.command('menu -t1 add "SCCwatcher/E-Mail On Grab" "sccwatcher emailon" "sccwatcher emailoff"')
        print color["red"], "Emailing has been turned on, use 'emailoff' to turn it back off"
    
    elif trigger[1] == 'sslon':
        option["global"]["download_ssl"] = 'on'
        xchat.command('menu -t1 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
        print color["red"], "SSL downloading is now enabled, use 'ssloff' to disable it."
        
    elif trigger[1] == 'ssloff':
        option["global"]["download_ssl"] = 'off'
        xchat.command('menu -t0 add "SCCwatcher/SSL Downloading" "sccwatcher sslon" "sccwatcher ssloff"')
        print color["red"], "SSL downloading is now disabled, use 'sslon' to enable it."
    
    elif trigger[1] == "setoutput":
        print color["red"] + "This command has been depreciated. You can now use anytab, thistab, or scctab. The deloutput command has also been removed in favor of anytab."
    
    elif trigger[1] == "thistab":
        #Use extra context
        option["global"]["_extra_context_"] = "on"
        option["global"]["_current_context_type_"] = "THISTAB"
        #Set the tab as the context to use
        option["global"]["_current_context_"] = xchat.find_context()
        #set the context name
        option["global"]["_current_context_name_"] = option["global"]["_current_context_"].get_info("channel")
        option["global"]["_current_context_"].prnt(sop_outtext)
        xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
        
    elif trigger[1] == "scctab":
        #Use extra context
        option["global"]["_extra_context_"] = "on"
        option["global"]["_current_context_type_"] = "SCCTAB"
        #Create the new tab
        xchat.command("QUERY SCCwatcher")
        #Set the new tab as the context to use
        option["global"]["_current_context_"] = xchat.find_context(channel="SCCwatcher")
        #set the context name
        option["global"]["_current_context_name_"] = option["global"]["_current_context_"].get_info("channel")
        option["global"]["_current_context_"].prnt(sop_outtext)
        xchat.command('menu -e0 -t1 add "SCCwatcher/Verbose Output Settings/Using Non-Default Output?" "echo"')
    
    elif trigger[1] == "anytab":
        option["global"]["_extra_context_"] = "off"
        option["global"]["_current_context_type_"] = "ANYTAB"
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
        option["global"]["debug"] = "off"
        xchat.command('menu DEL "SCCwatcher/Debug output"')
        
        
    elif trigger[1] == "cmdon":
        option["global"]["use_external_command"] = "on"
        print color["red"], "External Command Execution has been enabled, use cmdoff to turn it off."
        xchat.command('menu -t1 add "SCCwatcher/Use External Command" "sccwatcher cmdon" "sccwatcher cmdoff"')
    
    elif trigger[1] == "cmdoff":
        option["global"]["use_external_command"] = "off"
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

def manual_torrent_add_special(word, word_eol, userdata):
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
        on_text(manual_matchedtext, None, "SPECIAL")
        
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
        if option["global"]["logenabled"] == "on":
            option["global"]["logenabled"] = "off"
            option["global"]["__logenabled"] = "on"
        
        if option["global"]["verbose"] == "off":
            option["global"]["verbose"] = "on"
            option["global"]["__verbose"] = "off"
        
        #We are also going to turn debugging output on just because when testing you might want extra info
        option["global"]["debug"] = "on"
        
        on_text(manual_matchedtext, None, "TESTING")
        
        #now turn debug output off
        option["global"]["debug"] = "off"
        
        #Now reset settings back to what they were.
        try:
            option["global"]["__verbose"]
            option["global"]["verbose"] = option["global"]["__verbose"]
        except:
            option["global"]["verbose"] = "on"
        
        try:
            option["global"]["__logenabled"]
            option["global"]["logenabled"] = option["global"]["__logenabled"]
        except:
            option["global"]["logenabled"] = "off"        
    else:
        verbose("\00305The line you entered was incorrect somehow. Please double check that the line you copied was actually from #announce and try again\003")
        verbose("\00305If you continue to have problems please post the problem in the SCCwatcher forum topic.\003")
    
    return xchat.EAT_ALL

def unload_cb(userdata):
    global server_thread
    quitmsg = "\0034 "+__module_name__+" "+__module_version__+" has been unloaded\003"
    #Remove our status file
    try:
        os.remove(gettempdir() + os.sep + "sccw_port.txt")
    except:
        pass
    print quitmsg
    
    try:
        server_thread.quit_thread()
    except:
        pass
    try:
        server_thread.join()
    except:
        pass
    
    xchat.command('menu DEL SCCwatcher')
    #Only log script unload if logging is enabled
    if option["global"]["logenabled"] == "on":
        logging(xchat.strip(quitmsg), "UNLOAD")


#The hooks go here
xchat.hook_print('Channel Message', on_text)
xchat.hook_command('SCCwatcher', on_local, help="Edit main setting in scc2.ini. use \002/sccwatcher help\002 for usage information.")
xchat.hook_command('manualadd', manual_torrent_add, help="Manually grab torrents by pasting lines from #announce")
xchat.hook_command('manualadd_special', manual_torrent_add_special, help="Manually grab torrents by pasting lines from #announce")
xchat.hook_command('test_line', announce_line_tester, help="This will test a line to see if it would be downloaded by your current settings in scc2.ini")
xchat.hook_unload(unload_cb)
#Now that we have everything loaded, start up our status updater thread
#xchat.hook_timer(1000, scriptStatusUpdater)
#load scc2.ini


# This gets the script movin
if (__name__ == "__main__"):
    main()

#LICENSE GPL
#Last modified 07-04-16 (MM/DD/YY)

