# coding=utf-8
import threading
from Client.Client import Client
from servers import multithread_server
from dbmodules.dbconnection import *
from helpers.helpers import *
import config
from PyQt4 import QtCore, QtGui
from GUI.ui import *
#from GUI.main_window import Ui_MainWindow
from GUI import download

class Main(QtCore.QThread):
    download_trigger = QtCore.pyqtSignal(str, str, int)

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

    def run(self):

        for i in range(0, 10):
            progress = round(random.uniform(0.0, 100.0), 0)
            print str(i) + " source " + str(i) + " " + str(progress)
            self.download_trigger.emit(str(i), "source " + str(i), progress)

        time.sleep(3)
        print "\n\n update"


        for i in range(0, 10):
            progress = round(random.uniform(0.0, 100.0), 0)
            #print str(i) + " source " + str(i) + " "  + str(progress)
            self.update_trigger.emit(str(i), "source " + str(i), progress)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    download_window = download.Ui_MainWindow()
    download_window.show()

    main = Main()
    main.download_trigger.connect(download_window.add_progress)
    main.start()

    sys.exit(app.exec_())