from PyQt5.QtWidgets import QStatusBar,QAbstractItemView,QListView,QLayout,QMainWindow,QWidget,QGridLayout,QHBoxLayout,QFileSystemModel,QTreeView,QAction,QMessageBox,QFileDialog,QTextEdit,QPushButton,QVBoxLayout
from PyQt5.QtCore import pyqtSlot,QModelIndex,Qt,QThreadPool
from mainwidget import ReadFiles,ParseData,Worker,MainWidget,clearLayout,clearWidget
from logLoader import LogLoader
from logModel import LogModel
from customListModel import CustomListModel
import numpy as np
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from mplcanvas import MplCanvas
import matplotlib.dates as mdates
import py7zr,zipfile
import sys,os,shutil
from utils import LoadingBar,alphanum_key
import re
class ComparePopUp(QWidget):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.loaded = {"A":False,"B":False}
        self.setWindowTitle("Compare Logs")
        self.logModelA = LogModel()
        self.logModelB = LogModel()
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

        self.layoutA = QVBoxLayout()
        self.openButtonA = QPushButton("Open Logs A")
        self.openButtonA.clicked.connect(self.OpenLogsA)
        self.layoutA.addWidget(self.openButtonA)
        #Display textlogs
        self.textDisplayA = QTextEdit()
        self.textDisplayA.setReadOnly(True)
        self.layoutA.addWidget(self.textDisplayA)

        self.layoutB = QVBoxLayout()
        self.openButtonB = QPushButton("Open Logs B")
        self.openButtonB.clicked.connect(self.OpenLogsB)
        self.layoutB.addWidget(self.openButtonB)
        #Display textlogs
        self.textDisplayB = QTextEdit()
        self.textDisplayB.setReadOnly(True)
        self.layoutB.addWidget(self.textDisplayB)

        self.layoutAB.addLayout(self.layoutA)
        self.layoutAB.addLayout(self.layoutB)

        self.layout.addLayout(self.layoutAB,0,0,2,1)

        #Plotter
        self.graph_layout = QVBoxLayout()
        self.setup_graph_layout()
        
        #Plot Selection
        self.list = QListView()
        self.model = CustomListModel()
        self.list.setModel(self.model)

        self.model.dataChanged.connect(self.plotAll)

        self.layout.addLayout(self.graph_layout,0,1)
        self.layout.addWidget(self.list,1,1)
        self.list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list.setEnabled(False)

        self.layout.addWidget(self.statusbar,2,0,1,2)
        
        self.setLayout(self.layout)

    def OpenLogsA(self):
        fileDialog = QFileDialog(self,caption="Open Logs A",directory = MainWidget.workingDir)
        fileDialog.setViewMode(QFileDialog.Detail)
        pathA = ""
        if (fileDialog.exec()):
            pathA = fileDialog.selectedFiles()[0]
        if(not os.path.isdir(pathA)):
            file = pathA
            pathA = "tmpA"
            if(file[-3:]=="zip"):
                #Extract to a tmp folder first
                os.mkdir("tmpA")
                with zipfile.ZipFile(file, mode='r') as zip_ref:
                    zip_ref.extractall("tmpA")
            elif(file[-3:]==".7z"):
                os.mkdir("tmpA")
                with py7zr.SevenZipFile(file, mode='r') as z:
                    z.extractall("tmpA")
            else:
                return
        self.logModelA.OpenDir(pathA)
        self.LoadDataA()
        self.updateInfosA()

    def OpenLogsB(self):
        fileDialog = QFileDialog(self,caption="Open Logs",directory = MainWidget.workingDir)
        fileDialog.setViewMode(QFileDialog.Detail)
        pathB = ""
        if (fileDialog.exec()):
            pathB = fileDialog.selectedFiles()[0]
        if(not os.path.isdir(pathB)):
            file = pathB
            pathB = "tmpB"
            if(file[-3:]=="zip"):
                #Extract to a tmp folder first
                os.mkdir("tmpB")
                with zipfile.ZipFile(file, mode='r') as zip_ref:
                    zip_ref.extractall("tmpB")
            elif(file[-3:]==".7z"):
                os.mkdir("tmpB")
                with py7zr.SevenZipFile(file, mode='r') as z:
                    z.extractall("tmpB")
            else:
                return
        self.logModelB.OpenDir(pathB)
        self.LoadDataB()
        self.updateInfosB()
    def LoadDataA(self):
        self.threadDoneA = 0
        self.maxThreadsA = QThreadPool.globalInstance().maxThreadCount()//2
        self.barA = LoadingBar(18,text="Loading Logs A",title="ImportProgress")
        self.statusbar.addWidget(self.barA)
        logLoader = LogLoader(self.logModelA.files,self.show_progressA,self.closeLoadingBarA)
        logLoader.LoadData()
    def LoadDataB(self):
        self.threadDoneB = 0
        self.maxThreadsB = QThreadPool.globalInstance().maxThreadCount()//2
        self.barB = LoadingBar(18,text="Loading Logs B",title="ImportProgress")
        self.statusbar.addWidget(self.barB)
        logLoader = LogLoader(self.logModelB.files,self.show_progressB,self.closeLoadingBarB)
        logLoader.LoadData()
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
        rightScale = list(self.model.checkedItems)
        for i,index in enumerate(leftScale):
            name = index.data(Qt.DisplayRole)
            displayName = self.logModelA.displayName[name] 
            timestampsA, valuesA = self.logModelA.data[displayName]['timestamps'],self.logModelA.data[displayName]['values']
            timestampsB, valuesB = self.logModelB.data[displayName]['timestamps'],self.logModelB.data[displayName]['values']
            self.sc.axes.plot((np.array(timestampsA)-np.min(timestampsA))/(np.max(timestampsA)-np.min(timestampsA))*(np.max([np.max(timestampsA),np.max(timestampsB)])), valuesA,label = name+"A",color=cmapA[i%len(cmapA)])
            self.sc.axes.plot((np.array(timestampsB)-np.min(timestampsB))/(np.max(timestampsB)-np.min(timestampsB))*(np.max([np.max(timestampsA),np.max(timestampsB)])), valuesB,label = name+"B",color=cmapB[i%len(cmapB)])
        if(len(rightScale)>0):
            self.sc.twin.set_visible(True)
            for i,index in enumerate(rightScale):
                name = index.data(Qt.DisplayRole)
                displayName = self.logModelA.displayName[name] 
                timestampsA, valuesA = self.logModelA.data[displayName]['timestamps'],self.logModelA.data[displayName]['values']
                timestampsB, valuesB = self.logModelB.data[displayName]['timestamps'],self.logModelB.data[displayName]['values']
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
        displayName = self.logModelA.displayName[name] 
        timestampsA, valuesA = self.logModelA.data[displayName]['timestamps'],self.logModelA.data[displayName]['values']
        timestampsB, valuesB = self.logModelB.data[displayName]['timestamps'],self.logModelB.data[displayName]['values']
        self.sc.axes.cla()
        self.sc.axes.plot(timestampsA, valuesA, color='r')
        xfmt = mdates.DateFormatter('%H:%M:%S')
        self.sc.axes.xaxis.set_major_formatter(xfmt)
        self.sc.draw()



    def closeLoadingBarA(self):
        self.threadDoneA+=1
        if(self.threadDoneA >=self.maxThreadsA):
            self.statusbar.removeWidget(self.barA)
            self.model.setStringList(sorted(self.logModelA.displayName.keys(),key=alphanum_key))
            self.list.setEnabled(True)
            self.cleanTempDirA()
            pass

    def show_progressA(self,data):
        self.logModelA.data[data[0]]={'timestamps':data[1],'values':data[2]}
        displayName = re.sub(r'(_)', r'', re.sub(r'([A-Z])', r' \1', data[0])).strip() #insert a space before each capital letters
        self.logModelA.displayName[displayName] = data[0]
        self.barA.update()

    def updateInfosA(self):
        self.textDisplayA.setText(open(self.logModelA.files['RecipeInfos']).read())

    def closeLoadingBarB(self):
        self.threadDoneB+=1
        if(self.threadDoneB >=self.maxThreadsB):
            self.statusbar.removeWidget(self.barB)
            self.model.setStringList(sorted(self.logModelB.displayName.keys(),key=alphanum_key))
            self.list.setEnabled(True)
            self.cleanTempDirB()
            pass
    def cleanTempDirA(self):
        try:
                shutil.rmtree("tmpA")
        except (FileNotFoundError,PermissionError) as e:
            if type(e) == PermissionError:
                msg = QMessageBox.critical(self,"Error cleaning the temp directory",f"{e.strerror}: {e.filename}. Free the file and click Ok")
                if msg == QMessageBox.Ok:
                    #ok was clicked
                    #Try cleaning the dir again
                    self.cleanTempDirA()
    def cleanTempDirB(self):
        try:
                shutil.rmtree("tmpB")
        except (FileNotFoundError,PermissionError) as e:
            if type(e) == PermissionError:
                msg = QMessageBox.critical(self,"Error cleaning the temp directory",f"{e.strerror}: {e.filename}. Free the file and click Ok")
                if msg == QMessageBox.Ok:
                    #ok was clicked
                    #Try cleaning the dir again
                    self.cleanTempDirB()
    def show_progressB(self,data):
        self.logModelB.data[data[0]]={'timestamps':data[1],'values':data[2]}
        displayName = re.sub(r'(_)', r'', re.sub(r'([A-Z])', r' \1', data[0])).strip() #insert a space before each capital letters
        self.logModelB.displayName[displayName] = data[0]
        self.barB.update()

    def updateInfosB(self):
        self.textDisplayB.setText(open(self.logModelB.files['RecipeInfos']).read())