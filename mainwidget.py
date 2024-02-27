from PyQt5.QtWidgets import QDialog,QProgressBar,QVBoxLayout,QSizePolicy,QLabel
from PyQt5.QtCore import QThreadPool, QObject, QRunnable, pyqtSignal
from PyQt5.QtCore import pyqtSignal,Qt
import os
from datetime import datetime
import matplotlib.dates as mdates
class MainWidget():
    messageChanged = pyqtSignal(str)
    workingDir = '.'
    openedDir = '.'
    files={'DepositChamberFullRangePressure':'',
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
    data ={'DepositChamberFullRangePressure':{'timestamps':[],'values':[]},
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
    
    pool = QThreadPool()
    pool.setMaxThreadCount(1)
    @staticmethod
    def SetWorkingDir(newDir):
        MainWidget.workingDir = newDir
        with open("user.pref",'w') as file:
            file.write(MainWidget.workingDir)
        
    @staticmethod
    def OpenDir(newDir):
        MainWidget.openedDir = newDir
        files = os.scandir(MainWidget.openedDir)
        for file in files:
            if('.CSV' in file.name):
                #parse only csv files
                #trim date
                infos = file.name.split('/')[-1].split(' ')[2]
                #trim extension
                name = infos[:-4]
                MainWidget.files[name] = file               
            elif('.txt' in file.name): 
                #parse only csv files
                #trim date
                infos = file.name.split('/')[-1].split(' ')[2]
                #trim extension
                name = infos[:-4]
                MainWidget.files[name] = file
            

    @staticmethod
    def parseData(fileName):
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
        return timestamps,values
        
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)



class WorkerSignals(QObject):
    done = pyqtSignal()
    progress = pyqtSignal(list)

class Worker(QObject):
    def __init__(self, files,names):
        super(Worker, self).__init__()

        self.files = files
        self.names = names
        self.signals = WorkerSignals()

    def run(self):
        for i in range(len(self.files)):
            if(self.names[i] == 'RecipeInfos'):
                continue
            timestamps,values = MainWidget.parseData(self.files[i])
            self.signals.progress.emit([self.names[i],timestamps,values])
        self.signals.done.emit()

class LoadingBar(QDialog):
    def __init__(self,max,parent=None):
        super().__init__(parent)
        self.value = 0
        self.bar = QProgressBar()
        self.bar.setRange(0,max-1)
        layout = QVBoxLayout()
        self.setModal(True)
        layout.addWidget(self.bar)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.setWindowTitle("Import Progress")
    def update(self):
        self.value +=1
        self.bar.setValue(self.value)