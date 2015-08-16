## SCCwatcher 2.0         ##
##                        ##
## sccwatcher.py          ##
##                        ##
## Everything starts here ##
############################

import sys
from settings_ui import *
from PyQt4 import QtGui




def main():
    app = QtGui.QApplication(sys.argv)
    Window = QtGui.QMainWindow()
    ui = Ui_sccw_SettingsUI()
    ui.setupUi(Window)
    Window.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
