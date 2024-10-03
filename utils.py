import os,shutil
from PyQt5.QtWidgets import QDialog,QProgressBar,QVBoxLayout,QSizePolicy
from PyQt5.QtCore import Qt
import re
def alphanum_key(s):
    # Split the string into list of strings and numbers
        return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
def copy_and_replace(src_dir, dst_dir):
    """
    Copy all files and subdirectories from src_dir to dst_dir, overwriting any existing files.
    """
    try:
        # Copy the entire directory tree from src_dir to dst_dir
        try:
            os.mkdir(dst_dir)
        except:
            pass
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        #print(f"Successfully copied and replaced files from {src_dir} to {dst_dir}")
        pass
    except Exception as e:
        print(f"Error: {e}")

def delete_folder(path):
    try:
        shutil.rmtree(path)
        #print(f"Folder '{folder_path}' and its contents have been successfully removed.")
    except Exception as e:
        print(f"Error while removing folder '{path}': {e}")

class LoadingBar(QDialog):
    def __init__(self,max,title,text=None,parent=None):
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
        self.setWindowTitle(title)
        if text != None:
            self.bar.setTextVisible(True)
            self.bar.setFormat(text)
            self.bar.setAlignment(Qt.AlignCenter)
        self.bar.setValue(self.value)
    def update(self,value=1):
        self.value +=value
        self.bar.setValue(self.value)
    def set_max(self,max):
        self.bar.setRange(0,max)