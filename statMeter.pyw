import os
import sys
import time
import psutil
import tkinter
import threading
import pyqtgraph
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# enable highdpi scaling and icons
QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True) 
QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
iconFile = 'statMeter.ico'

# get path and set icon file
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
elif __file__:
    application_path = os.path.dirname(__file__)

# create application
application = QApplication([])
windowWidth = 55 * 16 # *  1
windowHeight = 55 * 9 # * 2
# size modifier, base ratio, ratio modifier
# 800, 450 / 960, 540

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    def run(self):
        while appWindow.runningBool:
            time.sleep(appWindow.collectionInterval)
            self.progress.emit(1)
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        #self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        # set vars for data collection interval of window
        self.precisionCoeff = 1
        self.collectionInterval = 1 / self.precisionCoeff
        
        # set background color, window size and title
        self.setStyleSheet("""
        QMainWindow{background: rgb(30,30,30)} \n QLabel{color:white} \n QPushButton{background-color: rgb(77,77,77); color: white}""")
        self.setFixedSize(QSize(windowWidth, windowHeight))
        #self.setFixedSize(QSize(500, 300))
        #self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.setWindowTitle("statMeter")
        self.setWindowIcon(QtGui.QIcon(os.path.join(application_path, iconFile)))

        # create a custom widget layout for the main window and set geometry
        self.layout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)
        self.layout.setAlignment(Qt.AlignCenter)
        self.buttonLayout.setAlignment(Qt.AlignCenter)
        
        # create widgets
        self.label_cpu = QLabel(self)
        self.label_cpu_abs = QLabel(self)
        self.label_ram = QLabel(self)
        self.label_ram_abs = QLabel(self)
        self.label_cpu.setText("Used CPU: 0%")
        self.label_cpu_abs.setText(" ")
        self.label_ram.setText("Used RAM: 0%")
        self.label_ram_abs.setText(" ")
        
        self.label_cpu.setAlignment(Qt.AlignCenter)
        self.label_ram.setAlignment(Qt.AlignCenter)
        self.label_cpu_abs.setAlignment(Qt.AlignCenter)
        self.label_ram_abs.setAlignment(Qt.AlignCenter)
        
        self.cpu_values=[0] * (30 * self.precisionCoeff)
        self.ram_values=[0] * (30 * self.precisionCoeff)
        self.graphWindow_cpu = pyqtgraph.plot(self.cpu_values)
        self.graphWindow_ram = pyqtgraph.plot(self.ram_values)
        self.graphWindow_cpu.setYRange(0, 100)
        self.graphWindow_ram.setYRange(0, 100)
        self.graphWindow_cpu.setBackground((30,30,30))
        self.graphWindow_ram.setBackground((30,30,30))
        self.graphWindow_cpu.setMouseEnabled(x=False, y=False)
        self.graphWindow_ram.setMouseEnabled(x=False, y=False)
        self.graphWindow_cpu.setMenuEnabled(False)
        self.graphWindow_ram.setMenuEnabled(False)
        self.graphWindow_cpu.hideButtons()
        self.graphWindow_ram.hideButtons()
        
        self.buttonTop = QPushButton('Refresh')
        self.buttonExit = QPushButton('Exit')
        self.buttonTop.setFixedSize(QSize(int(windowWidth/4), int(windowHeight/20)))
        self.buttonExit.setFixedSize(QSize(int(windowWidth/4), int(windowHeight/20)))
        
        # add widgets to main layout
        self.layout.addWidget(self.graphWindow_cpu)
        self.layout.addWidget(self.label_cpu)
        self.layout.addWidget(self.label_cpu_abs)
        self.layout.addWidget(self.graphWindow_ram)
        self.layout.addWidget(self.label_ram)
        self.layout.addWidget(self.label_ram_abs)
        self.layout.addStretch()
        
        # nested horizontal layout for bottom row
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.buttonTop)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.buttonExit)
        self.buttonLayout.addStretch()
        self.layout.addLayout(self.buttonLayout)

        # linking actions
        self.buttonExit.clicked.connect(self.buttonExitFunc)
        self.buttonTop.clicked.connect(self.clearValues)
        
        # get static stats
        self.cpuCoresPhys = psutil.cpu_count(logical=False)
        self.cpuCoresLog = psutil.cpu_count(logical=True)
        
        # set running bool
        self.runningBool = True
        
        # set up QThread and Worker
        self.graphThread = QThread()
        self.graphWorker = Worker()
        self.graphWorker.moveToThread(self.graphThread)
        self.graphThread.started.connect(self.graphWorker.run)
        self.graphWorker.progress.connect(self.updateGraphs)
        self.graphWorker.finished.connect(self.graphThread.quit)
        self.graphWorker.finished.connect(self.graphWorker.deleteLater)
        self.graphThread.finished.connect(self.graphThread.deleteLater)
        self.graphThread.start()
   
    # defining actions
    def clearValues(self):
        self.cpu_values=[0] * (30 * self.precisionCoeff)
        self.ram_values=[0] * (30 * self.precisionCoeff)
        
    def updateGraphs(self):
        self.graphWindow_cpu.clear()
        self.graphWindow_ram.clear()
        self.graphWindow_cpu.plot(self.cpu_values)
        self.graphWindow_ram.plot(self.ram_values)
    
    def updateStatsCycle(self):
        self.iter = 0
        while self.runningBool==True:
            # collecting values
            self.currCpu = psutil.cpu_percent()
            self.currCpuFreq = psutil.cpu_freq().current / 1000
            self.maxCpuFreq = psutil.cpu_freq().max / 1000
            self.currRam = psutil.virtual_memory()[2]
            self.currRamAbs = psutil.virtual_memory()[3] / 1000000000
            self.maxRamAbs = psutil.virtual_memory()[0] / 1000000000
            # storing values
            self.cpu_values.append(self.currCpu)
            self.cpu_values.pop(0)
            self.ram_values.append(self.currRam)
            self.ram_values.pop(0)
            # GUI update skipper
            if self.iter == self.precisionCoeff:
                self.updateStatsGUI()
                self.iter = 0
            self.iter = self.iter + 1
            time.sleep(self.collectionInterval)
   
    def updateStatsGUI(self):
            self.currCpuDisplay = self.currCpu
            self.currRamDisplay = self.currRam
            self.label_cpu.setText("Used CPU: " + str(self.currCpuDisplay) + "%")
            self.label_cpu_abs.setText(format(self.currCpuFreq, ".2f") + " / " + format(self.maxCpuFreq, ".2f") + " GHz" + " (" + str(self.cpuCoresPhys) + " physical cores, " +  str(self.cpuCoresLog) + " logical cores)")
            self.label_ram.setText("Used RAM: " + str(self.currRamDisplay) + "%")
            self.label_ram_abs.setText(str(format(self.currRamAbs, ".2f")) + " / " + str(format(self.maxRamAbs, ".2f")) + " GB")

    def buttonExitFunc(self):
        self.runningBool = False
        QApplication.quit()
        
    def closeEvent(self, event):
            self.runningBool=False
            event.accept()

# create and show window
appWindow = MainWindow()
appWindow.show()  

# spawn collection thread
collectionThread = threading.Thread(target=appWindow.updateStatsCycle)
collectionThread.start()

# start event loop
application.exec()