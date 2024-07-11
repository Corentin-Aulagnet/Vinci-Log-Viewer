import requests
import os,sys
import zipfile
from PyQt5.QtWidgets import QMessageBox
from utils import copy_and_replace,delete_folder,LoadingBar
import subprocess
def download_asset(url, file_name):
    response = requests.get(url, stream=True)
    dl_size = int(response.headers.get("content-length"))
    dld_size = 0
    bar = LoadingBar(dl_size,title="Download Progress")
    bar.open()
    with open(file_name, 'wb') as file:
        chunk_size = 1024
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                file.write(chunk)
                dld_size += chunk_size
                bar.update(chunk_size)
    bar.close()

def download_latest_release_asset(user, repo, asset_name,destination):
    url = f'https://api.github.com/repos/{user}/{repo}/releases/latest'
    response = requests.get(url)
    if response.status_code == 200:
        latest_release = response.json()
        for asset in latest_release['assets']:
            if asset['name'] == asset_name:
                extract_directory = destination+'\\tmp'
                try:
                    os.mkdir(extract_directory)
                except:
                    pass
                download_url = asset['browser_download_url']
                download_asset(download_url, extract_directory+'\\'+asset_name)
                print(f"{asset_name} downloaded successfully.")
                return True
    return False


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
        msgBox.setInformativeText("Do you want to download the latest version?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.Yes)
        ret = msgBox.exec()
        if ret == QMessageBox.Yes : download_update(latest_version,installation_folder,user,repo,asset_name)
    else:
        print("You are using the latest version.")

def download_update(version,installation_folder,user,repo,asset_name):
    print(f"Downloading version {version}...")
    # Example usage
    if download_latest_release_asset(user, repo, asset_name,installation_folder):
        print("Asset downloaded, proceed with installation.")
        install_update(asset_name,installation_folder)
    else:
        print("Failed to download the asset.")
        # Add your download and installation logic here

def install_update(asset_name,destination):
    updater_script_content = f"""
import os
import shutil
import time
import sys
from utils import copy_and_replace,delete_folder
import zipfile
time.sleep(5)

destination = sys.argv[1]
asset_name = sys.argv[2]

extract_directory = destination+'\\tmp'
asset_path = extract_directory+'\\'+asset_name
zip_file_path = asset_path
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(extract_directory)
    copy_and_replace(asset_path[:-4],destination)
    delete_folder(extract_directory)

# Restart the application
os.execv(sys.argv[0])
"""
    updater_script_path = 'updater.py'
    with open(updater_script_path, 'w') as updater_script:
        updater_script.write(updater_script_content)

    # Run updater script
    subprocess.Popen([sys.executable, updater_script_path, sys.argv[0], destination,asset_name])
    sys.exit(0)


    '''extract_directory = destination+'\\tmp'
    asset_path = extract_directory+'\\'+asset_name
    zip_file_path = asset_path
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_directory)
    copy_and_replace(asset_path[:-4],destination)
    delete_folder(extract_directory)'''

if __name__ == "__main__":
    # Example usage
    user = 'Corentin-Aulagnet'
    repo = 'Vinci-Log-Viewer'
    current_version = 'v0.1.0'
    installation_folder = "test"
    asset_name = 'VinciLogViewer_v0.5.1_python3.8.zip'
    check_for_update(user, repo, current_version,installation_folder,asset_name)