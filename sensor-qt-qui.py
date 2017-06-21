# -*- coding: utf-8 -*-
"""
Sensor estimate voltage to distance application with GUI
GUI Framework : PyQt5
Author : Thatchakon Jom-ud
"""

import sys
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5 import QtCore, uic
from core import Core

ui = "ThinPot Estimator.ui"
alert_dialog = "alert dialog.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(ui)
dialog_mainwindow, QtBaseClass1 = uic.loadUiType(alert_dialog)

class distanceTask(QtCore.QObject):

    __start = bool
    finished = QtCore.pyqtSignal()
    stringChanged = QtCore.pyqtSignal(str)
    valueChanged = QtCore.pyqtSignal(int)

    def start_core(self):
        self.__start = True
        num = 0
        while self.__start:
            """
            values = core.get_volt_and_distance()
            if values[1] >= 0 and values[0] < 4.900000:
                self.stringChanged.emit(str(values[1]) + " cm")
                self.valueChanged.emit(values[0])
            """
            self.stringChanged.emit(str(num)+" cm")
            self.valueChanged.emit(num)
            num += 1
            if (num >= 100):
                num = 0
            time.sleep(0.05)
        self.finished.emit()

    def stop(self):
        self.__start = False

class deviceTask(QtCore.QObject):
    finished_set_device = QtCore.pyqtSignal()
    finished_disconnect = QtCore.pyqtSignal()

    def set_device(self):
        while core.set_device():
            pass
        self.finished_set_device.emit()

    def disconnect(self):
        while core.disconnect_ad2():
            pass
        self.finished_disconnect.emit()

class alertDialog(QDialog, dialog_mainwindow):
    def __init__(self):
        QDialog.__init__(self)
        dialog_mainwindow.__init__(self)
        self.setupUi(self)

    def setMessage(self, text):
        self.messageLabel.setText(text)

class application(QMainWindow, Ui_MainWindow):

    status = QtCore.pyqtSignal(str)

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.statusBar().showMessage('AD2 : Not Connect')
        self.status.connect(self.statusBar().showMessage)

        self.setFixedSize(500, 250)

        self.thread = QtCore.QThread()
        self.task = distanceTask()
        self.task.moveToThread(self.thread)
        self.task.finished.connect(self.thread.quit)
        self.task.stringChanged.connect(self.distance.setText)
        self.task.valueChanged.connect(self.distanceBar.setValue)
        self.thread.started.connect(self.task.start_core)

        self.connect_thread = QtCore.QThread()
        self.disconnect_thread = QtCore.QThread()
        self.device_task = deviceTask()
        self.device_task2 = deviceTask()
        self.device_task.moveToThread(self.connect_thread)
        self.device_task2.moveToThread(self.disconnect_thread)
        self.device_task.finished_set_device.connect(self.connect_thread.quit)
        self.device_task.finished_set_device.connect(self.callback_device_task)
        self.device_task2.finished_disconnect.connect(self.disconnect_thread.quit)
        self.device_task2.finished_disconnect.connect(self.callback_disconnect_task)
        self.connect_thread.started.connect(self.device_task.set_device)
        self.disconnect_thread.started.connect(self.device_task2.disconnect)

        self.setup_event()

    def setup_event(self):
        self.start.clicked.connect(self.start_event)
        self.stop.clicked.connect(self.stop_event)

        self.actionConnect.triggered.connect(self.connect_ad2)
        self.actionDisconnect.triggered.connect(self.disconnect_ad2)

        self.actionDisconnect.setEnabled(False)

    def start_event(self):
        if(core.get_device_status() != "Not Connect"):
            self.thread.start()
        else:
            dialog = alertDialog()
            dialog.setWindowTitle("Alert")
            dialog.setMessage("Please Connect AD2 To The Computer")
            dialog.exec_()

    def stop_event(self):
        self.task.stop()

    def connect_ad2(self):
        self.connect_thread.start()

    def disconnect_ad2(self):
        self.disconnect_thread.start()

    def callback_device_task(self):
        if (core.get_device_status() == "Not Connect"):
            dialog = alertDialog()
            dialog.setWindowTitle("Alert")
            dialog.setMessage("failed to open device..")
            dialog.exec_()
        else:
            self.actionConnect.setEnabled(False)
            self.actionDisconnect.setEnabled(True)

    def callback_disconnect_task(self):
        self.actionConnect.setEnabled(True)
        self.actionDisconnect.setEnabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = application()
    window.show()
    core = Core(window)
    sys.exit(app.exec_())
