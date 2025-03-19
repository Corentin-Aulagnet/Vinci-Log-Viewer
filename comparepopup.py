from PyQt5.QtWidgets import QStatusBar,QAbstractItemView,QListView,QLayout,QMainWindow,QWidget,QGridLayout,QHBoxLayout,QFileSystemModel,QTreeView,QAction,QMessageBox,QFileDialog,QTextEdit,QPushButton,QVBoxLayout
from PyQt5.QtCore import pyqtSlot,QModelIndex,Qt,QThreadPool
from mainwidget import ReadFiles,ParseData,Worker,MainWidget,clearLayout,clearWidget
from utils import LoadingBar
from customListModel import CustomListModel
import numpy as np
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from mplcanvas import MplCanvas
import matplotlib.dates as mdates
class LogLoader(QWidget):
    def __init__(self,index,parent = None):
        super().__init__(parent)
        self.dir = ""
        self.index = index
        self.files={'DepositChamberFullRangePressure':'',
           'Massflow1':'',
           'Massflow2':'',
           'Massflow3':'',
           'Massflow4':'',
           'Maxim1_Current':'',
           'Maxim1_Voltage':'',
           'Maxim1_Power':'',
           'Maxim2_Current':'',
           'Maxim2_Voltage':'',
           'Maxim2_Power':'',
           'Maxim3_Current':'',
           'Maxim3_Voltage':'',
           'Maxim3_Power':'',
           'RecipeInfos':'',
           'Seren1_ForwardedMes':'',
           'Seren1_ReflectedMes':'',
           'SubstrateTemperature':''}
        self.data ={'DepositChamberFullRangePressure':{'timestamps':[],'values':[]},
           'Massflow1':{'timestamps':[],'values':[]},
           'Massflow2':{'timestamps':[],'values':[]},
           'Massflow3':{'timestamps':[],'values':[]},
           'Massflow4':{'timestamps':[],'values':[]},
           'Maxim1_Current':{'timestamps':[],'values':[]},
           'Maxim1_Voltage':{'timestamps':[],'values':[]},
           'Maxim1_Power':{'timestamps':[],'values':[]},
           'Maxim2_Current':{'timestamps':[],'values':[]},
           'Maxim2_Voltage':{'timestamps':[],'values':[]},
           'Maxim2_Power':{'timestamps':[],'values':[]},
           'Maxim3_Current':{'timestamps':[],'values':[]},
           'Maxim3_Voltage':{'timestamps':[],'values':[]},
           'Maxim3_Power':{'timestamps':[],'values':[]},
           #'RecipeInfos':{'timestamps':[],'values':[]},
           'Seren1_ForwardedMes':{'timestamps':[],'values':[]},
           'Seren1_ReflectedMes':{'timestamps':[],'values':[]},
           'SubstrateTemperature':{'timestamps':[],'values':[]}}
        self.layout = QVBoxLayout()
        self.thrd1 = None
        self.thrd2 = None
        self.openButton = QPushButton("Open Logs {}".format(index))
        self.openButton.clicked.connect(self.SetDirectory)
        self.layout.addWidget(self.openButton)

        #Display textlogs
        self.textDisplay = QTextEdit()
        self.textDisplay.setReadOnly(True)
        self.layout.addWidget(self.textDisplay)


        
        self.setLayout(self.layout)

    def LoadData(self,index):
        def divide_task(N:int, n:int)->'list[tuple[int,int]]':
            """
            Divide a task of length N into n jobs as evenly as possible.
            Returns a list of (start, end) index ranges for each job.
            """
            jobs = []
            base = N // n  # Base workload per job
            extra = N % n   # Remaining extra workload to distribute
            start = 0
            
            for i in range(n):
                # Distribute the extra workload among the first 'extra' jobs
                end = start + base + (1 if i < extra else 0) - 1
                jobs.append((start, end))
                start = end + 1
            
            return jobs

        self.threadDone = 0
        self.maxThreads = QThreadPool.globalInstance().maxThreadCount()//2
        self.workers = []
        val = list(self.files.values())
        keys = list(self.files.keys())
        self.bar = LoadingBar(18,text="Loading Logs {}".format(self.index),title="ImportProgress",parent=self)
        self.parent().notifyLoading(self.index)
        self.parent().statusbar.addWidget(self.bar)
        job_sizes = divide_task(len(val),self.maxThreads)
        print(f"Using {self.maxThreads} threads")
        for i in range(self.maxThreads):
            job_size = job_sizes[i]
            v = val[job_size[0]:job_size[1]+1]
            k= keys[job_size[0]:job_size[1]+1]
            w = Worker(v,k)
            w.signals.progress.connect(self.show_progress)
            w.signals.done.connect(self.closeLoadingBar)
            self.workers.append(w)
            QThreadPool.globalInstance().start(w)
        

    @pyqtSlot()
    def closeLoadingBar(self):
        self.threadDone+=1
        if(self.threadDone >=2):
            self.parent().statusbar.removeWidget(self.bar)
            self.parent().notifyLoaded(self.index)
            pass

    def show_progress(self,data):
        self.data[data[0]]['timestamps']=data[1]
        self.data[data[0]]['values']=data[2]
        self.bar.update()

    def updateInfos(self):
        self.textDisplay.setText(open(self.files['RecipeInfos']).read())

    def SetDirectory(self):
        self.dir = QFileDialog.getExistingDirectory(self,caption="Open logs",directory = MainWidget.workingDir)
        if dir != "":
            self.files = ReadFiles(self.dir)
            self.LoadData(self.index)
            self.updateInfos()

class ComparePopUp(QWidget):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.loaded = {"A":False,"B":False}
        self.setWindowTitle("Compare Logs")
        self.statusbar = QStatusBar()
        self.initLayouts()
        self.show()
    def notifyLoading(self,who):
        self.loaded[who] = False
        self.list.setEnabled(False)
    def notifyLoaded(self,who):
        self.loaded[who] = True
        if self.loaded["A"] and self.loaded["B"]:
            self.list.setEnabled(True)
            self.plotAll()
    def initLayouts(self):
        self.layout = QGridLayout()

        self.layoutAB = QHBoxLayout()
        self.logLoaderA = LogLoader("A",self)
        self.logLoaderB = LogLoader("B",self)
        self.layoutAB.addWidget(self.logLoaderA)
        self.layoutAB.addWidget(self.logLoaderB)

        self.layout.addLayout(self.layoutAB,0,0,2,1)

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

        self.layout.addLayout(self.graph_layout,0,1)
        self.layout.addWidget(self.list,1,1)
        self.list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list.setEnabled(False)

        self.layout.addWidget(self.statusbar,2,0,1,2)
        
        self.setLayout(self.layout)

    def setup_graph_layout(self,_3D=False):
        clearLayout(self.graph_layout)
        self.sc = MplCanvas(self, width=7, height=4, dpi=100,_3D=_3D)
        self.toolbar = NavigationToolbar(self.sc, self)
        self.graph_layout.addWidget(self.sc)
        self.graph_layout.addWidget(self.toolbar)



    @pyqtSlot(QModelIndex,QModelIndex)
    def plotAll(self,topLeft:QModelIndex = None,topRight:QModelIndex=None):
        self.sc.axes.cla()
        self.sc.twin.cla()
        cmapA = ["#fd7f6f", "#7eb0d5", "#b2e061", "#bd7ebe", "#ffb55a", "#ffee65", "#beb9db", "#fdcce5"]
        cmapB = ["#7fc97f", "#beaed4", "#fdc086", "#ffff99", "#386cb0", "#f0027f", "#bf5b16", "#666666"]
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
            fileNameA = self.logLoaderA.files[dic[name]]
            fileNameB = self.logLoaderB.files[dic[name]]
            timestampsA, valuesA = self.logLoaderA.data[dic[name]]['timestamps'],self.logLoaderA.data[dic[name]]['values']
            timestampsB, valuesB = self.logLoaderB.data[dic[name]]['timestamps'],self.logLoaderB.data[dic[name]]['values']
            self.sc.axes.plot((np.array(timestampsA)-np.min(timestampsA))/(np.max(timestampsA)-np.min(timestampsA))*(np.max([np.max(timestampsA),np.max(timestampsB)])), valuesA,label = name+"A",color=cmapA[i%len(cmapA)])
            self.sc.axes.plot((np.array(timestampsB)-np.min(timestampsB))/(np.max(timestampsB)-np.min(timestampsB))*(np.max([np.max(timestampsA),np.max(timestampsB)])), valuesB,label = name+"B",color=cmapB[i%len(cmapB)])
        if(len(rightScale)>0):
            self.sc.twin.set_visible(True)
            for i,index in enumerate(rightScale):
                name = index.data(Qt.DisplayRole)
                fileNameA = self.logLoaderA.files[dic[name]]
                fileNameB = self.logLoaderB.files[dic[name]]
                timestampsA, valuesA = self.logLoaderA.data[dic[name]]['timestamps'],self.logLoaderA.data[dic[name]]['values']
                timestampsB, valuesB = self.logLoaderB.data[dic[name]]['timestamps'],self.logLoaderB.data[dic[name]]['values']
                self.sc.twin.plot((np.array(timestampsA)-np.min(timestampsA))/(np.max(timestampsA)-np.min(timestampsA))*(np.max([np.max(timestampsA),np.max(timestampsB)])), valuesA,linestyle='dashed',label = name+"A",color=cmapA[i%len(cmapA)])
                self.sc.twin.plot((np.array(timestampsB)-np.min(timestampsB))/(np.max(timestampsB)-np.min(timestampsB))*(np.max([np.max(timestampsA),np.max(timestampsB)])), valuesB,linestyle='dashed',label = name+"B",color=cmapB[i%len(cmapB)])
        else:
            self.sc.twin.set_visible(False)
        #if len(leftScale)+len(rightScale)>1:
        lines, labels = self.sc.axes.get_legend_handles_labels()
        lines2, labels2 = self.sc.twin.get_legend_handles_labels()
        self.legend = self.sc.axes.legend(lines + lines2, labels + labels2)
        #self.legend.draggable()
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
        fileNameA = self.logLoaderA.files[dic[name]]
        fileNameB = self.logLoaderB.files[dic[name]]
        timestampsA, valuesA = self.logLoaderA.data[dic[name]]['timestamps'],self.logLoaderA.data[dic[name]]['values']
        timestampsB, valuesB = self.logLoaderB.data[dic[name]]['timestamps'],self.logLoaderB.data[dic[name]]['values']
        self.sc.axes.cla()
        self.sc.axes.plot(timestampsA, valuesA, color='r')
        xfmt = mdates.DateFormatter('%H:%M:%S')
        self.sc.axes.xaxis.set_major_formatter(xfmt)
        self.sc.draw()
