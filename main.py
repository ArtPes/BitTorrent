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
from GUI import main_window
from GUI import download

#sys.path.insert(1, '/Users/stefano/Desktop/P2PBitTorrent')


class Main(QtCore.QThread):
    download_trigger = QtCore.pyqtSignal(str, str, int)  # n parte, sorgente, progresso
    download_progress_trigger = QtCore.pyqtSignal(int, str)  # n parti scaricate, n parti totale, nome file
    print_trigger = QtCore.pyqtSignal(str, str)

    def __init__(self,parent=None):
        super(Main, self).__init__(parent)

    def run(self):
        tracker = False

        out_lck = threading.Lock()
        db = MongoConnection(out_lck)

        output(out_lck, "\nAre you a tracker?")
        output(out_lck, "1: YES")
        output(out_lck, "2: NO")

        int_choice = None
        while int_choice is None:
            try:
                option = raw_input()  # Input da tastiera
            except SyntaxError:
                option = None

            if option is None:
                output(out_lck, "Please select an option")
            else:
                try:
                    int_choice = int(option)
                except ValueError:
                    output(out_lck, "A choice is required")

        if int_choice == 1:
            output(out_lck, "YOU ARE A TRACKER")
            tracker = True
        else:
            output(out_lck, "YOU ARE A PEER!")

        # Avvio il server in ascolto sulle porte 3000 e 6000
        server = multithread_server.Server(tracker)
        server.print_trigger.connect(mainwindow.print_on_main_panel)
        server.start()

        if not tracker:
            client = Client(config.my_ipv4, config.my_ipv6, int(config.my_port), config.track_ipv4, config.track_ipv6,
                            config.track_port, db, out_lck, self.print_trigger, self.download_trigger,
                            self.download_progress_trigger)

            while client.session_id is None:
                # print_menu_top(out_lck)
                output(out_lck, "\nSelect one of the following options ('e' to exit): ")
                output(out_lck, "1: Log in                                          ")
                output(out_lck, "2: Set parallel downloads                          ")
                output(out_lck, "3: Set part length                                 ")

                int_option = None
                try:
                    option = raw_input()
                except SyntaxError:
                    option = None

                if option is None:
                    output(out_lck, "Please select an option")
                elif option == 'e':
                    output(out_lck, "Bye bye")
                    server.stop()
                    sys.exit()  # Interrompo l'esecuzione
                else:
                    try:
                        int_option = int(option)
                    except ValueError:
                        output(out_lck, "A number is required")
                    else:
                        if int_option == 1:

                            client.login()

                            while client.session_id is not None:
                                output(out_lck, "\nSelect one of the following options ('e' to exit): ")
                                output(out_lck, "1: Add file                                        ")
                                output(out_lck, "2: Search file                                     ")
                                output(out_lck, "3: Log out                                         ")

                                int_option = None
                                try:
                                    option = raw_input()
                                except SyntaxError:
                                    option = None

                                if option is None:
                                    output(out_lck, "Please select an option")
                                else:
                                    try:
                                        int_option = int(option)
                                    except ValueError:
                                        output(out_lck, "A number is required")
                                    else:
                                        if int_option == 1:
                                            # scelgo un file dalla cartella e lo aggiungo al tracker
                                            client.share()
                                        elif int_option == 2:
                                            # creo una query e la invio al tracker
                                            client.look()
                                        elif int_option == 3:
                                            client.logout()
                                            #output(out_lck, 'Logout completed')
                                        else:
                                            output(out_lck, "Option " + str(int_option) + " not available")
                        elif int_option == 2:
                            output(out_lck, "Insert the number of parallel downloads: ")

                            try:
                                option = raw_input()
                            except SyntaxError:
                                option = None

                            if option is None:
                                output(out_lck, "Please insert a number")
                            else:
                                try:
                                    int_option = int(option)
                                except ValueError:
                                    output(out_lck, "A number is required")
                                else:
                                    client.parallel_downloads = int_option
                                    output(out_lck, "Parallel downloads set to: " + str(int_option))

                        elif int_option == 3:
                            output(out_lck, "Insert the new part size: ")

                            try:
                                option = raw_input()
                            except SyntaxError:
                                option = None

                            if option is None:
                                output(out_lck, "Please insert a number")
                            else:
                                try:
                                    int_option = int(option)
                                except ValueError:
                                    output(out_lck, "A number is required")
                                else:
                                    client.part_size = int_option
                                    output(out_lck, "Parts size set to: " + str(int_option))
                        else:
                            output(out_lck, "Option " + str(int_option) + " not available")


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)

    mainwindow = main_window.Ui_MainWindow()
    mainwindow.show()

    # download_window = download.Ui_MainWindow()
    # download_window.show()

    main = Main()
    main.print_trigger.connect(mainwindow.print_on_main_panel)
    main.download_trigger.connect(mainwindow.update_progress)
    main.download_progress_trigger.connect(mainwindow.download_progress)
    main.start()

    sys.exit(app.exec_())
