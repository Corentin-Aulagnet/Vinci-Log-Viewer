import os
class LogModel():
    files={}
    displayName={}
    data={}

    def ReadFiles(self,dir):
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

    def OpenDir(self,dir):

        self.files={}
        self.displayName = {}
        self.files = self.ReadFiles(dir)