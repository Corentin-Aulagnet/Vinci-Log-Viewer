from PyQt5.QtWidgets import QAbstractItemView,QListView,QLayout,QMainWindow,QWidget,QGridLayout,QFileSystemModel,QTreeView,QAction,QMessageBox,QFileDialog,QTextEdit,QPushButton,QVBoxLayout
from PyQt5.QtCore import pyqtSlot,QModelIndex,Qt,QThread
from mainwidget import MainWidget,LoadingBar,Worker,clearLayout,clearWidget
from customListModel import CustomListModel
from comparepopup import ComparePopUp

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.dates as mdates
from mplcanvas import MplCanvas


class MainWindow(QMainWindow):
    version = "v0.5.1"
    date= "10th of July, 2024"
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
        self.list = QListView()
        self.model = CustomListModel()
        self.list.setModel(self.model)

        strList = ['Chamber Pressure',
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
           'Substrate Temperature']
        self.model.setStringList(strList)

        self.model.dataChanged.connect(self.plotAll)

        self.layout.addLayout(sublayout,0,0)
        self.layout.addLayout(self.graph_layout,0,1)
        self.layout.addWidget(self.list,1,1)
        self.list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list.setEnabled(False)
        self.layout.addWidget(self.textDisplay,1,0)


        
        
        self.setCentralWidget(self.centralWidget)

    @pyqtSlot(QModelIndex,QModelIndex)
    def plotAll(self,topLeft:QModelIndex=None,topRight:QModelIndex=None):
        self.sc.axes.cla()
        self.sc.twin.cla()
        cmap = ["#fd7f6f", "#7eb0d5", "#b2e061", "#bd7ebe", "#ffb55a", "#ffee65", "#beb9db", "#fdcce5", "#8bd3c7"]
        leftScale = list(self.model.partiallyCheckedItems)
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
        rightScale = list(self.model.checkedItems)
        for i,index in enumerate(leftScale):
            name = index.data(Qt.DisplayRole)
            fileName = MainWidget.files[dic[name]]
            timestamps, values = MainWidget.data[dic[name]]['timestamps'],MainWidget.data[dic[name]]['values']
            self.sc.axes.plot(timestamps, values,label = name,color=cmap[i%len(cmap)])
        if(len(rightScale)>0):
            self.sc.twin.set_visible(True)
            for i,index in enumerate(rightScale):
                name = index.data(Qt.DisplayRole)
                fileName = MainWidget.files[dic[name]]
                timestamps, values = MainWidget.data[dic[name]]['timestamps'],MainWidget.data[dic[name]]['values']
                self.sc.twin.plot(timestamps, values,linestyle='dashed',label = name,color=cmap[i%len(cmap)])
        else:
            self.sc.twin.set_visible(False)
        if len(leftScale)+len(rightScale)>1:
            lines, labels = self.sc.axes.get_legend_handles_labels()
            lines2, labels2 = self.sc.twin.get_legend_handles_labels()
            self.sc.axes.legend(lines + lines2, labels + labels2)
            #if(len(leftScale)>0):self.sc.axes.legend()
            #if(len(rightScale)>0):self.sc.twin.legend()
        xfmt = mdates.DateFormatter('%H:%M:%S')
        self.sc.axes.xaxis.set_major_formatter(xfmt)
        self.sc.draw()

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
        timestamps, values = MainWidget.data[dic[name]]['timestamps'],MainWidget.data[dic[name]]['values']
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
        path = self.tree.model().filePath(self.tree.selectedIndexes()[0])
        MainWidget.OpenDir(path)
        self.LoadData()
        self.updateInfos()
        self.list.setEnabled(True)
        

    def LoadData(self):
        self.threadDone = 0
        self.bar = LoadingBar(18,parent=self)
        self.bar.open()
        self.thrd1 = QThread()
        self.thrd2 = QThread()
        val = list(MainWidget.files.values())
        keys = list(MainWidget.files.keys())
        self.worker1 = Worker(val[:len(val)//2],keys[:len(keys)//2])
        self.worker2 = Worker(val[len(val)//2:],keys[len(keys)//2:])
        self.worker1.moveToThread(self.thrd1)
        self.worker2.moveToThread(self.thrd2)

        self.thrd1.start()
        self.thrd1.started.connect(self.worker1.run)
        self.worker1.signals.progress.connect(self.show_progress)
        self.worker1.signals.done.connect(self.closeLoadingBar)
        self.thrd2.start()
        self.thrd2.started.connect(self.worker2.run)
        self.worker2.signals.progress.connect(self.show_progress)
        self.worker2.signals.done.connect(self.closeLoadingBar)
    
    @pyqtSlot()
    def closeLoadingBar(self):
        self.threadDone+=1
        if(self.threadDone >=2):
            self.bar.close()
            self.plotAll()

    def show_progress(self,data):
        MainWidget.data[data[0]]['timestamps']=data[1]
        MainWidget.data[data[0]]['values']=data[2]
        self.bar.update()

    def updateInfos(self):
        self.textDisplay.setText(open(MainWidget.files['RecipeInfos']).read())
    def initMenus(self):
        ##Tools
        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.compareLogs_action = QAction("Compare logs",self)
        self.compareLogs_action.triggered.connect(self.OpenCompare)
        self.toolsMenu.addAction(self.compareLogs_action)
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

    def OpenCompare(self):
        self.popup = ComparePopUp()
        

    def DisplayVersion(self):
        QMessageBox.information(self,'Version',"""Version: {}\n
Date of publication: {}\n
Details: Developped and maintained by Corentin Aulagnet.\r
You can publish new issues on <a href=\'https://github.com/Corentin-Aulagnet/Vinci-Log-Viewer/issues'>GitHub</a>""".format(MainWindow.version,MainWindow.date))
    def SetWorkingDir(self):
        dir = QFileDialog.getExistingDirectory(self,caption="Set Working Directory",directory = MainWidget.workingDir)
        if dir != "":
            MainWidget.SetWorkingDir(dir)
            self.tree.model().setRootPath(MainWidget.workingDir)
            self.tree.setRootIndex(self.tree.model().index(MainWidget.workingDir))
            #self.PrintNormalMessage("Changed working directory to {}".format(MainWidget.workingDir))
        
    def initWorkingDir(self):
        try:
            with open("user.pref",'r') as f:
                MainWidget.SetWorkingDir(f.readline())
        except FileNotFoundError:
            pass

