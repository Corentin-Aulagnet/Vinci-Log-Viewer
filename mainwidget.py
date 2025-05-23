from PyQt5.QtWidgets import QWidget,QLayout
from PyQt5.QtCore import QThreadPool, QObject,  pyqtSignal,QRunnable
from PyQt5.QtCore import pyqtSignal
import os
from datetime import datetime
import matplotlib.dates as mdates
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
def ReadFiles(dir):
    files_={}
    files = os.scandir(dir)
    for file in files:
        if('.CSV' in file.name):
            #parse only csv files
            #trim date
            infos = file.name.split('/')[-1].split(' ')[2]
            #trim extension
            name = infos[:-4]
            files_[name] = file               
        elif('.txt' in file.name): 
            #parse only csv files
            #trim date
            infos = file.name.split('/')[-1].split(' ')[2]
            #trim extension
            name = infos[:-4]
            files_[name] = file
    return files_

def ParseData(fileName):
        #parse data from file
        with open(fileName,'r') as file:
            lines = file.readlines()
            timestamps=[]
            values=[]
            for line in lines:
                data = line.split(',')
                date,time = data[0].split(' ')
                d,m,Y = date.split('/')
                H,M,S = time.split(':')
                s,ms = S.split('.')
                timestamps.append("{}-{}-{} {}:{}:{}.{}".format(Y,m,d,H,M,s,ms))
                values.append(float(data[1]))
            timestamps=mdates.date2num(timestamps)
        return timestamps,values

class MainWidget():
    messageChanged = pyqtSignal(str)
    workingDir = '.'
    openedDir = '.'
    
    files={}
    displayName={}
    data={}
    
    @staticmethod
    def SetWorkingDir(newDir):
        MainWidget.workingDir = newDir
        with open("user.pref",'w') as file:
            file.write(MainWidget.workingDir)
        
    @staticmethod
    def OpenDir(newDir):
        MainWidget.openedDir = newDir
        MainWidget.files={}
        MainWidget.displayName = {}
        files = ReadFiles(newDir)
        MainWidget.files = files
            
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)



class WorkerSignals(QObject):
    done = pyqtSignal()
    progress = pyqtSignal(list)

class Worker(QRunnable):
    id = 0
    def __init__(self, files,names):
        super(Worker, self).__init__()

        self.files = files
        self.names = names
        self.signals = WorkerSignals()

    def run(self):
        Worker.id+=1
        print(f"Started Worker {Worker.id}")
        for i in range(len(self.files)):
            if(self.names[i] == 'RecipeInfos'):
                continue
            timestamps,values = ParseData(self.files[i])
            self.signals.progress.emit([self.names[i],timestamps,values])
        self.signals.done.emit()
        #self.thread().exit(0)

