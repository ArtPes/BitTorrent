# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bittorrent.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
#from PyQt4.QtGui import QApplication

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class Ui_MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Ui_MainWindow, self).__init__(parent)
        self.setObjectName(_fromUtf8("BitTorrent"))
        self.resize(800, 600)
        self.setMinimumSize(QtCore.QSize(600, 350))
        self.setMaximumSize(QtCore.QSize(1200, 650))
        self.centralwidget = QtWidgets.QWidget(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setMinimumSize(QtCore.QSize(600, 300))
        self.centralwidget.setMaximumSize(QtCore.QSize(1200, 600))
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(9, 9, 781, 581))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setMaximumSize(QtCore.QSize(40, 20))
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_1 = QtWidgets.QLabel(self.widget)
        self.label_1.setMinimumSize(QtCore.QSize(0, 0))
        self.label_1.setMaximumSize(QtCore.QSize(45, 20))
        self.label_1.setObjectName(_fromUtf8("label_1"))
        self.gridLayout.addWidget(self.label_1, 0, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.client = QtWidgets.QTextBrowser(self.widget)
        self.client.setMinimumSize(QtCore.QSize(300, 200))
        self.client.setMaximumSize(QtCore.QSize(600, 600))
        self.client.setObjectName(_fromUtf8("client"))
        self.gridLayout_2.addWidget(self.client, 0, 0, 1, 1)
        self.server = QtWidgets.QTextBrowser(self.widget)
        self.server.setMinimumSize(QtCore.QSize(300, 200))
        self.server.setMaximumSize(QtCore.QSize(600, 600))
        self.server.setObjectName(_fromUtf8("server"))
        self.gridLayout_2.addWidget(self.server, 0, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout_2, 1, 0, 1, 1)
        self.verticalLayout_3.addLayout(self.gridLayout_3)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.download_label = QtWidgets.QLabel(self.widget)
        self.download_label.setObjectName(_fromUtf8("download_label"))
        self.verticalLayout_2.addWidget(self.download_label)
        self.progressBar = QtWidgets.QProgressBar(self.widget)
        self.progressBar.setRange(0, 100)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout_2.addWidget(self.progressBar)
        self.tableWidget = QtWidgets.QTableWidget(self.widget)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_2.addWidget(self.tableWidget)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.label.setText(_translate("MainWindow", "Client", None))
        self.label_1.setText(_translate("MainWindow", "Server", None))
        self.download_label.setText(_translate("MainWindow", "Download idle", None))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Part n°", None))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Source", None))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Progress", None))

    def print_on_main_panel(self, message, color):
        """
            00 stampa sul terminale Client in nero
            01 stampa sul terminale Client in rosso
            02 stampa sul terminale Client in verde

            10 stampa sul terminale Server in nero
            11 stampa sul terminale Server in rosso
            12 stampa sul terminale Server in verde
        """
        if color == "10":
            self.server.setTextColor(QtGui.QColor('black'))
            self.server.append(message)
        elif color == "11":
            self.server.setTextColor(QtGui.QColor('red'))
            self.server.append(message)
        elif color == "12":
            self.server.setTextColor(QtGui.QColor('green'))
            self.server.append(message)
        elif color == "00":
            self.client.setTextColor(QtGui.QColor('black'))
            self.client.append(message)
        elif color == "01":
            self.client.setTextColor(QtGui.QColor('red'))
            self.client.append(message)
        elif color == "02":
            self.client.setTextColor(QtGui.QColor('green'))
            self.client.append(message)

    def update_progress(self, part_n, source, progress):
        part_doesnt_exists = True

        allRows = self.tableWidget.rowCount()
        for row in xrange(0, allRows):
            part_number = self.tableWidget.item(row, 0).text()

            if int(part_n) == int(part_number):
                part_doesnt_exists = False

                self.tableWidget.removeCellWidget(row, 2)
                progressbar = QtWidgets.QProgressBar()
                progressbar.setRange(0, 100)
                progressbar.setValue(progress)
                self.tableWidget.setCellWidget(row, 2, progressbar)

        if part_doesnt_exists:
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            row = self.tableWidget.rowCount() - 1

            item = QtWidgets.QTableWidgetItem(QtCore.QString(part_n))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(row, 0, item)

            item = QtWidgets.QTableWidgetItem(QtCore.QString(source))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(row, 1, item)

            progressbar = QtWidgets.QProgressBar()
            progressbar.setRange(0, 100)
            progressbar.setValue(progress)
            self.tableWidget.setCellWidget(row, 2, progressbar)

    def download_progress(self, down_progress, file_name):
        if down_progress == 100:
            self.download_label.setText(_translate("MainWindow", "File " + file_name + " successfully downloaded.", None))
        else:
            self.download_label.setText(_translate("MainWindow", "Downloading file " + file_name, None))

        self.progressBar.setValue(down_progress)

        #QApplication.processEvents()
        # self.widget.repaint()