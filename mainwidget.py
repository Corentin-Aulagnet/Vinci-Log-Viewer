from PyQt5.QtCore import pyqtSignal
import os
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
           'RecipesInfos':'',
           'Seren1_ForwardedMes':'',
           'Seren1_ReflectedMes':'',
           'SubstrateTemperature':''}
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
            #trim date
            infos = file.name.split('/')[-1].split(' ')[2]
            #trim extension
            name = infos[:-4]
            MainWidget.files[name] = file


        
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)