import os,sys
import zipfile
import requests
from utils import copy_and_replace,delete_folder,LoadingBar
import subprocess

from PyQt5.QtWidgets import QApplication,QWidget,QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal,pyqtSlot

class DownloadThread(QThread):
    download_finished = pyqtSignal()
    update_download = pyqtSignal()
    read_download_size = pyqtSignal(int)
    def __init__(self,url,dl_path):
        super().__init__()
        self.url = url
        self.dl_path = dl_path
        
    def run(self):
        self.download_asset(self.url,self.dl_path)
        self.download_finished.emit()
        
    def download_asset(self,url, file_name):
        response = requests.get(url, stream=True)
        if response != None:
            dl_size = int(response.headers.get("content-length"))
            dld_size = 0
            self.read_download_size.emit(dl_size//1024)
            with open(file_name, 'wb') as file:
                chunk_size = 1024
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        file.write(chunk)
                        dld_size += 1 #kb
                        #print("{}/{}kbytes downloaded".format(dld_size,dl_size//1024))
                        self.update_download.emit()


class Updater(QWidget):
    def __init__(self,version,destination,user,repo,asset_name,parent=None):
        super().__init__()
        self.version = version
        self.destination = destination
        self.user = user
        self.repo = repo
        self.asset_name = asset_name
        self.bar = LoadingBar(1,title="Download Progress")
        layout = QVBoxLayout()
        layout.addWidget(self.bar)
        self.setLayout(layout)
        self.download_update(self.version)
        
        
        

    def download_latest_release_asset(self):
        url = f'https://api.github.com/repos/{self.user}/{self.repo}/releases/latest'
        response = requests.get(url)
        if response.status_code == 200:
            latest_release = response.json()
            for asset in latest_release['assets']:
                if asset['name'] == self.asset_name:
                    extract_directory = self.destination+'\\tmp'
                    try:
                        os.mkdir(extract_directory)
                    except:
                        pass
                    download_url = asset['browser_download_url']
                    self.dl_thread = DownloadThread(download_url, extract_directory+'\\'+asset_name)
                    self.dl_thread.download_finished.connect(self.on_download_finished)
                    self.dl_thread.update_download.connect(self.on_update_download)
                    self.dl_thread.read_download_size.connect(self.on_read_download_size)
                    self.dl_thread.start()
                    
                    return True
        return False
    
    def download_update(self,version):
        print(f"Downloading version {version}...")
        # Example usage
        if self.download_latest_release_asset():
            # Add your download and installation logic here
            print("Asset downloading...")
            
        else:
            print("Failed to download the asset.")
            

    def install_update(self,asset_name,destination):
        extract_directory = destination+'\\tmp'
        asset_path = extract_directory+'\\'+asset_name
        zip_file_path = asset_path
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_directory)
            copy_and_replace(asset_path[:-4],destination)
        delete_folder(extract_directory)
        exe_path = "{}\\VinciLogViewer.exe".format(destination)
        subprocess.Popen([exe_path])

    @pyqtSlot()
    def on_download_finished(self):
        print(f"{self.asset_name} downloaded successfully.")
        self.install_update(self.asset_name,self.destination)
        QApplication.instance().quit()

    @pyqtSlot()
    def on_update_download(self):
        self.bar.update()
    @pyqtSlot(int)
    def on_read_download_size(self,size):
        self.bar.set_max(size)
if __name__ == "__main__":
    destination = sys.argv[1]
    asset_name = sys.argv[2]
    repo = sys.argv[3]
    user = sys.argv[4]
    version = sys.argv[5]
    app = QApplication([])
    widget = Updater(version,destination,user,repo,asset_name)
    widget.show()
    sys.exit(app.exec_())