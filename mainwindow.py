from PyQt5.QtWidgets import QListWidget,QLayout,QMainWindow,QWidget,QGridLayout,QFileSystemModel,QTreeView,QAction,QMessageBox,QFileDialog,QTextEdit,QPushButton,QVBoxLayout
from PyQt5.QtCore import QSize,pyqtSlot,QModelIndex,Qt
from mainwidget import MainWidget

from time import mktime
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm

def clearLayout(layout):
        if layout != None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    clearLayout(child)

def clearWidget(widget):
    children = widget.findChildren(QWidget)
    for child in children:
        child.deleteLater()
    children = widget.findChildren(QLayout)
    for child in children:        
        clearLayout(child)

class MainWindow(QMainWindow):
    version = "v0.1.0"
    date= "20th of February, 2024"
    def __init__(self,width=1400,height=800):
        super().__init__()
        self.height = height
        self.width = width
        self.left = 100
        self.top = 100

        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowTitle("Vinci Logs Viewer")
        
        
        self.initWorkingDir()
        self.initLayout()
        
        self.initMenus()

        self.show()

    def initLayout(self):
        self.centralWidget = QWidget()
        self.layout = QGridLayout()
        self.centralWidget.setLayout(self.layout)


        #File explorer
        sublayout = QVBoxLayout()

        model = QFileSystemModel()
        model.setRootPath(MainWidget.workingDir)
        self.tree = QTreeView()
        self.tree.setModel(model)
        self.tree.setRootIndex(self.tree.model().index(MainWidget.workingDir))
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        availableSize = self.tree.screen().availableGeometry().size()
        self.tree.resize(availableSize / 2)
        self.tree.setColumnWidth(0, self.tree.width() / 3)
        
        openButton = QPushButton("Open")
        openButton.clicked.connect(self.loadFolder)

        sublayout.addWidget(self.tree)
        sublayout.addWidget(openButton)
        #Display textlogs
        self.textDisplay = QTextEdit()
        self.textDisplay.setReadOnly(True)


        #Plotter
        self.graph_layout = QVBoxLayout()
        self.setup_graph_layout()
        
        #Plot Selection
        self.list = QListWidget()
        self.list.addItems(['Chamber Pressure',
           'Massflow1',
           'Massflow2',
           'Massflow3',
           'Massflow4',
           'Maxim1 Current',
           'Maxim1 Voltage',
           'Maxim1 Power',
           'Maxim2 Current',
           'Maxim2 Voltage',
           'Maxim2 Power',
           'Maxim3 Current',
           'Maxim3 Voltage',
           'Maxim3 Power',
           'Seren1 ForwardedMes',
           'Seren1 ReflectedMes',
           'Substrate Temperature'])
        self.list.doubleClicked.connect(self.plotThis)

        self.layout.addLayout(sublayout,0,0)
        self.layout.addLayout(self.graph_layout,0,1)
        self.layout.addWidget(self.list,1,1)
        self.layout.addWidget(self.textDisplay,1,0)


        
        
        self.setCentralWidget(self.centralWidget)


    @pyqtSlot(QModelIndex)
    def plotThis(self,index:QModelIndex):
        name = index.data(Qt.DisplayRole)
        dic = {'Chamber Pressure':'DepositChamberFullRangePressure',
           'Massflow1':'Massflow1',
           'Massflow2':'Massflow2',
           'Massflow3':'Massflow3',
           'Massflow4':'Massflow4',
           'Maxim1 Current':'Maxim1_Current',
           'Maxim1 Voltage':'Maxim1_Voltage',
           'Maxim1 Power':'Maxim1_Power',
           'Maxim2 Current':'Maxim2_Current',
           'Maxim2 Voltage':'Maxim2_Voltage',
           'Maxim2 Power':'Maxim2_Power',
           'Maxim3 Current':'Maxim3_Current',
           'Maxim3 Voltage':'Maxim3_Voltage',
           'Maxim3 Power':'Maxim3_Power',
           'Seren1 ForwardedMes':'Seren1_ForwardedMes',
           'Seren1 ReflectedMes':'Seren1_ReflectedMes',
           'Substrate Temperature':'SubstrateTemperature'
           }
        fileName = MainWidget.files[dic[name]]
        #parse data from file
        with open(fileName,'r') as file:
            lines = file.readlines()
            timestamps=[]
            values=[]
            for line in lines:
                data = line.split(',')
                timestamps.append(datetime.strptime(data[0],"%d/%m/%Y %H:%M:%S.%f"))
                values.append(float(data[1]))
            timestamps=mdates.date2num(timestamps)
            self.sc.axes.cla()
            self.sc.axes.plot(timestamps, values, color='r')
            xfmt = mdates.DateFormatter('%H:%M:%S')
            self.sc.axes.xaxis.set_major_formatter(xfmt)
            self.sc.draw()
    def setup_graph_layout(self,_3D=False):
        clearLayout(self.graph_layout)
        self.sc = MplCanvas(self, width=7, height=4, dpi=100,_3D=_3D)
        self.toolbar = NavigationToolbar(self.sc, self)
        self.graph_layout.addWidget(self.sc)
        self.graph_layout.addWidget(self.toolbar)
    @pyqtSlot()
    def loadFolder(self):
        path = self.tree.model().data(self.tree.selectedIndexes()[0])
        MainWidget.OpenDir(MainWidget.workingDir+'/'+path)
        self.updateInfos()
    def updateInfos(self):
        self.textDisplay.setText(open(MainWidget.files['RecipeInfos']).read())
    def initMenus(self):

        ##Preferences
        self.prefMenu = self.menuBar().addMenu("&Preferences")
        ###Editor
        self.editWorkingPath_action = QAction("Set Working Directory...",self)
        self.editWorkingPath_action.triggered.connect(self.SetWorkingDir)
        self.prefMenu.addAction(self.editWorkingPath_action)
        ##About
        self.aboutMenu = self.menuBar().addMenu("&About")
        self.version_action = QAction("Version",self)
        self.version_action.triggered.connect(self.DisplayVersion)
        self.aboutMenu.addAction(self.version_action)

    def DisplayVersion(self):
        QMessageBox.information(self,'Version',"""Version: {}\n
Date of publication: {}\n
Details: To be published""".format(MainWindow.version,MainWindow.date))
    def SetWorkingDir(self):
        dir = QFileDialog.getExistingDirectory(self,caption="Set Working Directory",directory = MainWidget.workingDir)
        if dir != "":
            MainWidget.SetWorkingDir(dir)
            #self.PrintNormalMessage("Changed working directory to {}".format(MainWidget.workingDir))
    def initWorkingDir(self):
        try:
            with open("user.pref",'r') as f:
                MainWidget.SetWorkingDir(f.readline())
        except FileNotFoundError:
            pass


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=6, height=4, dpi=100,_3D=False):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        if(_3D):self.axes = self.fig.add_subplot(projection='3d')
        else: self.axes = self.fig.add_subplot()
        
        super(MplCanvas, self).__init__(self.fig)