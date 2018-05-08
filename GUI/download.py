# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'download.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Ui_MainWindow, self).__init__(parent)
        self.setObjectName(_fromUtf8("MainWindow"))
        self.resize(511, 450)
        self.centralwidget = QtGui.QWidget(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(7, 10, 501, 431))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.widget)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.tableWidget = QtGui.QTableWidget(self.widget)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.verticalLayout.addWidget(self.tableWidget)
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.label.setText(_translate("MainWindow", "Donwloading file <filename>", None))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Part n°", None))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Source", None))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Progress", None))

    def update_progress(self, part_n, source, progress, file_name):

        self.label.setText(_translate("MainWindow", "Donwloading file " + file_name, None))

        part_doesnt_exists = True

        allRows = self.tableWidget.rowCount()
        for row in xrange(0, allRows):
            part_number = self.tableWidget.item(row, 0).text()

            if int(part_n) == int(part_number):
                part_doesnt_exists = False

                self.tableWidget.removeCellWidget(row, 2)
                progressbar = QtGui.QProgressBar()
                progressbar.setRange(0, 100)
                progressbar.setValue(progress)
                self.tableWidget.setCellWidget(row, 2, progressbar)

        if part_doesnt_exists:
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            row = self.tableWidget.rowCount() - 1

            item = QtGui.QTableWidgetItem(QtCore.QString(part_n))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(row, 0, item)

            item = QtGui.QTableWidgetItem(QtCore.QString(source))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(row, 1, item)

            progressbar = QtGui.QProgressBar()
            progressbar.setRange(0, 100)
            progressbar.setValue(progress)
            self.tableWidget.setCellWidget(row, 2, progressbar)

