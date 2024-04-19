from PyQt5.QtCore import Qt,QVariant,QPersistentModelIndex,QStringListModel,QModelIndex


class CustomListModel(QStringListModel):

    def __init__(self):
        self.checkedItems = set()
        self.partiallyCheckedItems = set()
        super().__init__()
        
    def flags(self,index:QModelIndex):
        defaultFlags = super().flags(index)
        if index.isValid():
            return defaultFlags | Qt.ItemIsUserCheckable | Qt.ItemIsUserTristate ^ Qt.ItemIsEditable
        else:
            return defaultFlags
        
    def setData(self,index:QModelIndex, value:QVariant, role:int):
        if not index.isValid() or role!= Qt.CheckStateRole:
            return False
        if value == Qt.Checked:
            if index in self.partiallyCheckedItems: self.partiallyCheckedItems.remove(index)
            self.checkedItems.add(index)
        elif value == Qt.PartiallyChecked:
            if index in self.checkedItems: self.checkedItems.remove(index)
            self.partiallyCheckedItems.add(index)
        else:
            if index in self.checkedItems: self.checkedItems.remove(index)
            if index in self.partiallyCheckedItems: self.partiallyCheckedItems.remove(index)
        self.dataChanged.emit(index,index)
        return True
    
    def data(self,index:QModelIndex,role:int):
        if not index.isValid():
            return QVariant()
        if role == Qt.CheckStateRole:
             if index in self.checkedItems:
                 return Qt.Checked
             elif index in self.partiallyCheckedItems:
                 return Qt.PartiallyChecked
             else:
                 return Qt.Unchecked
        return super().data(index,role)
        
        

