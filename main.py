# coding=utf-8
import threading

from Client.Client import Client
from servers import multithread_server
from dbmodules.dbconnection import *
from helpers.helpers import *
import config
from PyQt5 import QtCore, QtWidgets
from GUI.ui import *
from GUI import main_window
from GUI import download


class Main(QtCore.QThread):
    download_trigger = QtCore.pyqtSignal(str, str, int)  # n parte, sorgente, progresso
    download_progress_trigger = QtCore.pyqtSignal(int, str)  # n parti scaricate, n parti totale, nome file
    print_trigger = QtCore.pyqtSignal(str, str)

    def __init__(self,parent=None):
        super(Main, self).__init__(parent)

    def run(self):
        tracker = False

        out_lck = threading.Lock()
        # connessione al database
        db = MongoConnection(out_lck)

        int_choice = loop_menu(out_lck, "Are you a tracker?", ["Yes", "No"])

        if int_choice == 1:
            output(out_lck, "YOU ARE A TRACKER")
            tracker = True
        else:
            output(out_lck, "YOU ARE A PEER")

        # Avvio il server in ascolto sulle porte 3000 e 6000
        server = multithread_server.Server(tracker)
        server.print_trigger.connect(mainwindow.print_on_main_panel)
        server.start()

        # se sono un tracker
        if not tracker:
            client = Client(config.my_ipv4, config.my_ipv6, int(config.my_port), config.track_ipv4, config.track_ipv6,
                            config.track_port, db, out_lck, self.print_trigger, self.download_trigger,
                            self.download_progress_trigger)

            while client.session_id is None:
                int_option = loop_menu(out_lck, "Select one of the following options ('e' to exit)", ["Login",
                                                                                                      "Set parallel downloads",
                                                                                                      "Set part length"])
                if int_option == 1:
                    client.login()
                    while int_option != 3:
                        int_option = loop_menu(out_lck, "Select one of the following options ('e' to exit): ", ["Add file",
                                                                                                                "Search file",
                                                                                                                "Logout"])
                        if int_option == 1:
                            # scelgo un file dalla cartella e lo aggiungo al tracker
                            client.share()
                        elif int_option == 2:
                            # creo una query e la invio al tracker
                            client.look()
                        elif int_option == 3:
                            client.logout()
                            output(out_lck, 'Logout completed.')
                        else:
                            output(out_lck, "Option " + str(int_option) + " not available")

                elif int_option == 2:
                    client.parallel_downloads = loop_int_input(out_lck, "Insert the number of parallel downloads: ")

                elif int_option == 3:

                    client.part_size = loop_int_input(out_lck, "Insert the new part size: ")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

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
