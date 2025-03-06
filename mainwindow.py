from PyQt5.QtWidgets import QApplication,QAbstractItemView,QListView,QMainWindow,QWidget,QGridLayout,QFileSystemModel,QTreeView,QAction,QMessageBox,QFileDialog,QTextEdit,QPushButton,QVBoxLayout,QHBoxLayout,QComboBox
from PyQt5.QtCore import pyqtSlot,QModelIndex,Qt,QThread,QThreadPool
from PyQt5.QtGui import QIcon
from mainwidget import MainWidget,Worker,clearLayout
from utils import LoadingBar
from customListModel import CustomListModel
from comparepopup import ComparePopUp
import re
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.dates as mdates
from mplcanvas import MplCanvas
import utils
import py7zr,zipfile
import sys,os,shutil
from updateCheck import start_update,UpdateCheckThread,get_latest_release
class MainWindow(QMainWindow):
    version = "v0.8.0"
    date= "06th of March, 2025"
    github_user = 'Corentin-Aulagnet'
    github_repo = 'Vinci-Log-Viewer'
    asset_name= lambda s : f'VinciLogViewer_{s}_python3.8.zip'
    def __init__(self,width=1400,height=800):
        super().__init__()
        self.height = height
        self.width = width
        self.left = 100
        self.top = 100

        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowTitle("Vinci Logs Viewer")
        self.setWindowIcon(QIcon("res\\VinciLogViewer.ico"))
        
        self.initWorkingDir()
        self.initLayout()
        
        self.initMenus()
        self.checkForUpdates()
        self.show()
        
        
    def start(self):
        self.checkForUpdates()

    def checkForUpdates(self):
        #Check for updates
        # Start the update check thread
        self.update_thread = UpdateCheckThread(MainWindow.github_user,MainWindow.github_repo,MainWindow.version,MainWindow.asset_name)
        self.update_thread.update_available.connect(self.on_update_check_finished)
        self.update_thread.start()

        
        
    @pyqtSlot(str)
    def on_update_check_finished(self,latest_version):
        #Get the folder where the app is running from
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app 
            # path into variable _MEIPASS'.
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        installation_folder = application_path
        if latest_version != '':
            msgBox = QMessageBox()
            msgBox.setText(f"A newer version ({latest_version}) is available. You are currently using version {MainWindow.version}.");
            msgBox.setInformativeText("Do you want to download the latest version? VinciLogViewer will be closed")
            msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgBox.setDefaultButton(QMessageBox.Yes)
            ret = msgBox.exec()
            if ret == QMessageBox.Yes : 
                start_update(latest_version,installation_folder,MainWindow.github_user,MainWindow.github_repo,MainWindow.asset_name(latest_version))
                QApplication.instance().quit()
    
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
        self.tree.setColumnWidth(0, self.tree.width() // 4)
        
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
        rightScale = list(self.model.checkedItems)
        for i,index in enumerate(leftScale):
            displayName = index.data(Qt.DisplayRole)
            name = MainWidget.displayName[displayName]
            fileName = MainWidget.files[name]
            timestamps, values = MainWidget.data[name]['timestamps'],MainWidget.data[name]['values']
            self.sc.axes.plot(timestamps, values,label = name,color=cmap[i%len(cmap)])
            self.sc.axes.set_title(name)
        if(len(rightScale)>0):
            self.sc.twin.set_visible(True)
            for i,index in enumerate(rightScale):
                displayName = index.data(Qt.DisplayRole)
                name = MainWidget.displayName[displayName]
                fileName = MainWidget.files[name]
                timestamps, values = MainWidget.data[name]['timestamps'],MainWidget.data[name]['values']
                self.sc.twin.plot(timestamps, values,linestyle='dashed',label = name,color=cmap[i%len(cmap)])
                self.sc.twin.set_title(name)
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
        displayName = index.data(Qt.DisplayRole)
        name = MainWidget.displayName[displayName]
        fileName = MainWidget.files[name]
        timestamps, values = MainWidget.data[name]['timestamps'],MainWidget.data[name]['values']
        self.sc.axes.cla()
        self.sc.axes.plot(timestamps, values, color='r')
        xfmt = mdates.DateFormatter('%H:%M:%S')
        self.sc.axes.xaxis.set_major_formatter(xfmt)
        self.sc.draw()

    def setup_graph_layout(self,_3D=False):
        clearLayout(self.graph_layout)
        self.sc = MplCanvas(self, width=7, height=4, dpi=100,_3D=_3D)
        self.toolbar = NavigationToolbar(self.sc, self)
        self.hx = QHBoxLayout()
        
        self.yScaleComboBox = QComboBox()
        self.yScaleComboBox.addItems(["linear","log"])
        self.yScaleComboBox.currentTextChanged.connect(self.redrawScales)
        self.yScaleComboBox.setToolTip("y-scale of 1st axis")

        self.hx.addWidget(self.toolbar)
        self.hx.addWidget(self.yScaleComboBox)
        self.hx.addStretch()

        self.graph_layout.addWidget(self.sc)
        self.graph_layout.addLayout(self.hx)
    
    @pyqtSlot(str)
    def redrawScales(self,text):
        self.sc.axes.set_yscale(text)
        self.sc.draw()
        

    @pyqtSlot()
    def loadFolder(self):
        path = self.tree.model().filePath(self.tree.selectedIndexes()[0])
        if(not os.path.isdir(path)):
            file = path
            path = "tmp"
            if(file[-3:]=="zip"):
                #Extract to a tmp folder first
                os.mkdir("tmp")
                with zipfile.ZipFile(file, mode='r') as zip_ref:
                    zip_ref.extractall("tmp")
            elif(file[-3:]==".7z"):
                os.mkdir("tmp")
                with py7zr.SevenZipFile(file, mode='r') as z:
                    z.extractall("tmp")
            else:
                return
        MainWidget.OpenDir(path)
        self.LoadData()
        self.updateInfos()
        
        
    
    def LoadData(self):
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
        val = list(MainWidget.files.values())
        keys = list(MainWidget.files.keys())
        self.bar = LoadingBar(len(val),title="Import Progress",parent=self)
        self.bar.open()
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
        if(self.threadDone >=self.maxThreads):
            self.bar.close()
            self.model.setStringList(sorted(MainWidget.displayName.keys(),key=utils.alphanum_key))
            self.list.setEnabled(True)
            self.plotAll()
            self.cleanTempDir()

    def cleanTempDir(self):
        try:
                shutil.rmtree("tmp")
        except (FileNotFoundError,PermissionError) as e:
            if type(e) == PermissionError:
                msg = QMessageBox.critical(self,"Error cleaning the temp directory",f"{e.strerror}: {e.filename}. Free the file and click Ok")
                if msg == QMessageBox.Ok:
                    #ok was clicked
                    #Try cleaning the dir again
                    self.cleanTempDir()
    
    
    def show_progress(self,data):
        MainWidget.data[data[0]] = {'timestamps':data[1],'values':data[2]}
        displayName = re.sub(r'(_)', r'', re.sub(r'([A-Z])', r' \1', data[0])).strip() #insert a space before each capital letters
        MainWidget.displayName[displayName] = data[0]
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
        msgBox = QMessageBox(self)
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setWindowTitle('About')
        msgBox.setText("""Version: {}\r\n
Date of publication: {}\r\n
Details: Developped and maintained by Corentin Aulagnet.\r\n
You can publish new issues on <a href=\'https://github.com/Corentin-Aulagnet/Vinci-Log-Viewer/issues'>GitHub</a>""".format(MainWindow.version,MainWindow.date))
        msgBox.exec()
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

