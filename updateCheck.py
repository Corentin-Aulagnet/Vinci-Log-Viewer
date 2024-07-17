from PyQt5.QtWidgets import QMessageBox
import requests
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal

class UpdateCheckThread(QThread):
    update_available = pyqtSignal(str)
    def __init__(self,user,repo,current_version,asset_name):
        super().__init__()
        self.user = user
        self.repo = repo
        self.current_version = current_version
        self.asset_name = asset_name

    def run(self):
        latest_version = get_latest_release(self.user, self.repo)
        update_available = False
        if latest_version and compare_versions(self.current_version, latest_version):
            update_available = latest_version
        else:
            print("You are using the latest version.")
            update_available = None
        self.update_available.emit(update_available)

def get_latest_release(user, repo):
    url = f'https://api.github.com/repos/{user}/{repo}/releases/latest'
    response = requests.get(url)
    if response.status_code == 200:
        latest_release = response.json()
        return latest_release['tag_name']
    else:
        return None

def compare_versions(current_version, latest_version):
    from packaging import version
    return version.parse(latest_version) > version.parse(current_version)

def check_for_update(user, repo, current_version,installation_folder,asset_name):
    latest_version = get_latest_release(user, repo)
    if latest_version and compare_versions(current_version, latest_version):
        asset_name = asset_name(latest_version)
        msgBox = QMessageBox()
        msgBox.setText(f"A newer version ({latest_version}) is available. You are currently using version {current_version}.");
        msgBox.setInformativeText("Do you want to download the latest version? VinciLogViewer will be closed")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.Yes)
        ret = msgBox.exec()
        if ret == QMessageBox.Yes : 
            start_update(latest_version,installation_folder,user,repo,asset_name)
            return True
        else: return False
    else:
        print("You are using the latest version.")
        return False

def start_update(latest_version,installation_folder,user,repo,asset_name):
    exe_path = "{}\\VinciLogViewerInstaller.exe".format(installation_folder)
    subprocess.Popen(['runas', '/user:Administrator',exe_path, installation_folder,asset_name,repo,user,latest_version])
