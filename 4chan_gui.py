#!/usr/bin/python3.2

""" 4chan downloader
This program will download all the images from 4chan threads until 404'ed """

__author__ = "Dhole"
__license__ = "GPL"
__version__ = "0.3"
__email__ = "bankukur@gmail.com"
__status__ = "Development"
__date__ = "27 Apr 2012"


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from urllib.request import urlopen, urlretrieve
from time import sleep
import urllib.error
import sys, operator, pickle, os, threading, re, webbrowser

class Glob(object):

  stop = False
  update = False
  my_array = []
  header = ['url', 'section', 'thread', 'images', 'status']
  x = {}
  threadLock_mem = threading.RLock()
  threadLock_file = threading.RLock()
  db = ''
  
  def initialize(db):
    
    #Check db
    Glob.threadLock_mem.acquire()
    if not os.path.exists(db):
      print("Creating new urls_file")
      x = {}
      with open(db, 'wb') as f:
        pickle.dump(x, f)
    else:	
      with open(db, 'rb') as f:
        try:
          x = pickle.load(f)
        except EOFError:
          print("Error opening file " + db + ". Exiting...")
          sys.exit(1)
    Glob.x = x
    print("initializing..." +  db)
    Glob.update_values()
    Glob.threadLock_mem.release()
    Glob.db = db
  
  def write():
    Glob.threadLock_mem.acquire()
    Glob.threadLock_file.acquire()
    with open(Glob.db, 'wb') as f:
        pickle.dump(Glob.x, f)
    Glob.threadLock_file.release()
    Glob.threadLock_mem.release()
  
  def update_values():
    Glob.threadLock_mem.acquire()
    i = 0
    my_array = []
    for k,v in Glob.x.items():
      #print(k)
      my_array.append([])
      my_array[i].append(k)
      my_array[i].append(v['section'])
      my_array[i].append(v['thread'])
      my_array[i].append(v['number_images'])
      if v['is404']:
        my_array[i].append('404')
      else:
        my_array[i].append('Active')
      i = i + 1
    if len(Glob.x) == 0:
      my_array.append([[' '],[' '],[' '],[' '],[' ']])
      
    Glob.threadLock_mem.release()
    Glob.my_array = my_array

class TheTable(QTableView):
  def __init__(self, parent = None):
    QTableView.__init__(self, parent)
    
    #print(my_array)
    #print("Ayayayayay")
    #print(Glob.my_array)
    self.tablemodel = MyTableModel(Glob.my_array, Glob.header, self)
    
    #rowColor = Qt.blue
    #self.model().setData(Qt.BackgroundRole, rowColor)

    self.setModel(self.tablemodel)
    #self.resizeColumnsToContents()
    self.resizeRowsToContents()
    self.resizeColumnsToContents() 
    self.setSortingEnabled(True)
    self.verticalHeader().hide()
    #self.clicked.connect(self.right_click_table)
    #self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
    for i in range(0,5):
      cur_size = self.horizontalHeader().sectionSize(i)
      self.horizontalHeader().resizeSection(i,cur_size + 20)
    self.horizontalHeader().setResizeMode(QHeaderView.Fixed)
    self.horizontalHeader().setStretchLastSection(True)
    self.current_row = -1
      
    
      
    #self.show()
  def mousePressEvent(self, event):
    index = self.indexAt(event.pos())
  	
    if (index.isValid()):
      #if 	event.button() == Qt.RightButton:
      self.current_row = row = index.row()
      self.selectRow(self.current_row)
    else:
      self.current_row = row = -1
      self.clearSelection()
    
  def contextMenuEvent(self, event):
  
    index = self.indexAt(event.pos())
  	
    if (index.isValid()):
      row = index.row()
      self.current_row = row
      self.selectRow(self.current_row)
      column = index.column()
      #print("Row " + str(row) + " - Column " + str(column) + " was clicked")
      value = self.model().index(row, 0).data()
      #print(value)
    else:
      self.current_row = -1
      return
      
    # The menu
    menu = QMenu(self)
    # Add your actions
    continueAction = QAction("Continue", self)
    pauseAction = QAction("Pause", self)
    browse_urlAction = QAction("Open in broswer", self)
    copyAction = QAction("Copy url", self)
    clearAction = QAction("Clear", self)   
    view_folderAction = QAction("View folder", self)
    deleteAction = QAction("Delete", self)
    menu.addAction(continueAction)
    menu.addAction(pauseAction)
    menu.addAction(browse_urlAction)
    menu.addAction(copyAction)
    menu.addAction(clearAction)
    menu.addAction(view_folderAction)
    menu.addSeparator()
    menu.addAction(deleteAction)
    continueAction.triggered.connect(lambda: self.continue_slot(value))
    pauseAction.triggered.connect(lambda: self.pause_slot(value))
    browse_urlAction.triggered.connect(lambda: self.browse_url_slot(value))    
    copyAction.triggered.connect(lambda: self.copy_slot(value))
    clearAction.triggered.connect(lambda: self.clear_slot(value))
    deleteAction.triggered.connect(lambda: self.delete_slot(value))
    view_folderAction.triggered.connect(lambda: self.view_folder_slot(value))
    
    #menu.addAction(pauseAction)
    #menu.addAction(clearAction)
    #menu.addAction(delete_filesAction)
    #menu.addAction(view_folderAction)
    self.clipboard = QApplication.clipboard()

    #print(.row())
    # Add some check here for event.globalPos() to see if it's in your widget
    # Open the menu
    menu.popup(event.globalPos())
       
    
  def continue_slot(self, value):
  	print("Continuing with " + value)
  	
  def pause_slot(self, value):
  	print("Pausing " + value)
  	
  def browse_url_slot(self, value):
  	print("Browsing url " + value) 
  	webbrowser.open(value)
  	
  def copy_slot(self, value):
  	print("Copying " + value) 
  	self.clipboard.setText(value)
  
  def clear_slot(self, value):
  	print("Clearing " + value)
  	Glob.threadLock_mem.acquire()
  	if Glob.x[value]['is404']:
  	  del Glob.x[value]
  	else:
  	  print(value + " is not 404, you should delete it instead")
  	Glob.threadLock_mem.release()
      
  def view_folder_slot(self, value):
    print("Viewing folder" + value)
    section = re.findall("4chan.org/[a-z0-9]*/res", value)[0].split("/")[1]
    number =  re.findall("res/[0-9]*", value)[0][4:]
    path = os.getcwd()
    path = os.path.join(path, section)     
    path = os.path.join(path, number) 
    #This works fine on unix
    os.system("xdg-open " + path)
  	
  def delete_slot(self, value):
  	print("Deleting " + value)
  	
  def updateGeometries(self):
    super(TheTable, self).updateGeometries()
    self.verticalScrollBar().setSingleStep(2)
  
  #def data(self):
  # super(TheTable, self).data()
  #return QVariant(QColor(Qt.red))
    


class MyWindow(QMainWindow):
  def __init__(self, *args):
    QWidget.__init__(self, *args)

    #print(my_array)
    #exit(1)
    #self.resize(470, 616)
    self.centralwidget = QWidget(self)
    topBox = QHBoxLayout()
    box = QVBoxLayout(self.centralwidget)
    #lowBox = QHBoxLayout(self.centralwidget)    
    self.urlLine = QLineEdit(self)
    topBox.addWidget(self.urlLine)
    self.downloadButton = QPushButton('', self)
    self.downloadButton.setIcon(QIcon('download.svg'))
    self.downloadButton.setEnabled(False)
    topBox.addWidget(self.downloadButton)
    self.downloadMoreButton = QPushButton('Download more', self)
    topBox.addWidget(self.downloadMoreButton)
    box.addLayout(topBox)
    self.tb = TheTable(self.centralwidget)
    box.addWidget(self.tb)
    #lowBox.addLayout(box)
    self.setCentralWidget(self.centralwidget)
    
    self.url = ''
    self.downloadButton.clicked.connect(self.downloadUrl)
    self.urlLine.textChanged[str].connect(self.enteredUrl)
    self.urlLine.returnPressed.connect(self.downloadUrl)
    #self.mainWidget=QWidget(self)
    #self.mainLayout=QVBoxLayout(self.mainWidget, 5, 5, "main")
   

    #self.setCentralWidget(self.tb)
    
    
    self.createActions()
    self.createMenus()
    self.createStatusBar()
    
    pauseAllAction = QAction(QIcon('stop.svg'), 'Pause all', self)
    pauseAllAction.setShortcut('Ctrl+P')
    pauseAllAction.triggered.connect(self.pauseAllSlot)
    
    continueAllAction = QAction(QIcon('continue.svg'), 'Pause all', self)
    continueAllAction.setShortcut('Ctrl+P')
    continueAllAction.triggered.connect(self.continueAllSlot)
    
    clear404Action = QAction(QIcon('clear.svg'), 'Clear all 404', self)
    clear404Action.setShortcut('Ctrl+P')
    clear404Action.triggered.connect(self.clear404Slot)
    
    self.menu = QMenu()
    self.menu.addAction("un")
    self.menu.addAction("dos")

    
    self.toolbar = self.addToolBar('Pause all')
    self.toolbar.addAction(pauseAllAction)
    self.toolbar = self.addToolBar('Continue all')
    self.toolbar.addAction(continueAllAction)
    self.toolbar = self.addToolBar('Clear all 404 all')
    self.toolbar.addAction(clear404Action)

    self.setWindowIcon(QIcon('big_icon.png'))
    self.setGeometry(300, 50, 600, 600)
    self.update_dimensions()
    self.setWindowTitle('4CHONDL')
    self.show()
    
    
  def update_dimensions(self):
    self.tb.resizeRowsToContents()
    self.tb.resizeColumnsToContents() 
    width = 0
    for i in range(0,5):
      cur_size = self.tb.horizontalHeader().sectionSize(i) + 8
      width = width + cur_size
    if width < 300:
      width = 600
      
    self.setMaximumWidth(width)
    self.setMinimumWidth(width)
    self.setMinimumHeight(600)
    self.tb.horizontalHeader().setStretchLastSection(True)
       
  def enteredUrl(self, line):
    if line == '':
      self.downloadButton.setEnabled(False)
    else:
      self.downloadButton.setEnabled(True)
      self.url = line
  
  def downloadUrl(self):
    url_ok = check_url(self.url)
    if url_ok == "":
      print("Bad url!")
    else:
      print("Downloading url " +  url_ok)
      self.urlLine.clear()
      #self.urlLine.setText(QString(''))
      add_db(url_ok)
      Glob.update = True  
      Glob.update_values()
      self.update_table()
      
      
  def update_table(self):
    #s = self.tb.selectionModel()
    Glob.update_values()
    self.tb.tablemodel = MyTableModel(Glob.my_array, Glob.header, self.tb)
    self.tb.setModel(self.tb.tablemodel)
    #		self.tb.setSelectionModel(s)
    sort_column = self.tb.horizontalHeader().sortIndicatorSection()
    sort_order = self.tb.horizontalHeader().sortIndicatorOrder()
    self.tb.sortByColumn(sort_column, sort_order)    
    self.update_dimensions()
    if self.tb.current_row != -1:
      self.tb.selectRow(self.tb.current_row)
        
       
  def pauseAllSlot(self):
    print("Pausing all threads")
    
  def continueAllSlot(self):
    print("Continuing all threads")
  
  def clear404Slot(self):
    print("Clearing all 404 threads")   
    Glob.threadLock_mem.acquire()
    to_delete = []
    for k, v in Glob.x.items():
      if v['is404']:
        to_delete.append(k)
    for k in to_delete:
      del Glob.x[k]
    Glob.write()
    Glob.threadLock_mem.release()

  def about(self):
    QMessageBox.about(self, self.tr("About 4CHONDL"),
      self.tr("4chan dl\n\n"
              "by %s\n"
              "version %s\n"
              "%s" % (__author__, __version__, __date__)))
  
  def createActions(self):
    self.exitAct = QAction(self.tr("E&xit"), self)
    self.exitAct.setShortcut(self.tr("Ctrl+Q"))
    self.exitAct.setStatusTip(self.tr("Exit the application"))
    self.connect(self.exitAct, SIGNAL("triggered()"), self, SLOT("close()"))

    self.aboutAct = QAction(self.tr("&About"), self)
    self.aboutAct.setStatusTip(self.tr("Show the application's About box"))
    self.connect(self.aboutAct, SIGNAL("triggered()"), self.about)

    self.aboutQtAct = QAction(self.tr("About &Qt"), self)
    self.aboutQtAct.setStatusTip(self.tr("Show the Qt library's About box"))
    self.connect(self.aboutQtAct, SIGNAL("triggered()"), qApp, SLOT("aboutQt()"))

  def createMenus(self):
    self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
    self.fileMenu.addAction(self.exitAct)

    self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
    self.helpMenu.addAction(self.aboutAct)
    self.helpMenu.addAction(self.aboutQtAct)

  def createStatusBar(self):
    sb = QStatusBar()
    sb.setFixedHeight(18)
    self.setStatusBar(sb)
    self.statusBar().showMessage(self.tr("Ready"))
    


class MyTableModel(QAbstractTableModel):
  def __init__(self, datain, headerdata, parent=None, *args):
    QAbstractTableModel.__init__(self, parent, *args)
    self.arraydata = datain
    self.headerdata = headerdata
    #print("Hola que tal>>>>>>>>>>>>>>>>>>")
    #print(self.arraydata)

  def rowCount(self, parent):
      return len(self.arraydata)

  def columnCount(self, parent):
    return len(self.arraydata[0])

  def data(self, index, role):
    if not index.isValid():
      return None
    elif role == Qt.BackgroundColorRole :
      if self.arraydata[index.row()][4] == "Active":
        return QColor(Qt.green)
      elif self.arraydata[index.row()][4] == "Paused":
        return QColor(Qt.yellow)
      elif self.arraydata[index.row()][4] == "404":
        return QColor(Qt.gray)
    elif role == Qt.DisplayRole:
      return self.arraydata[index.row()][index.column()]
    return None
        
  def headerData(self, col, orientation, role):
    if orientation == Qt.Horizontal and role == Qt.DisplayRole:
      return self.headerdata[col]
    return None
        
  def sort(self, Ncol, order):
    """Sort table by given column number.
    """
    self.emit(SIGNAL("layoutAboutToBeChanged()"))
    self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))        
    if order == Qt.DescendingOrder:
      self.arraydata.reverse()
    self.emit(SIGNAL("layoutChanged()"))
    
def check_url(url):
  #Test if url is ok
  url_parsed = re.findall("http.*4chan.org/[a-z0-9]*/res/[0-9]*", url)
  if len(url_parsed) < 1:
    #print("Malformed url")
    return ""
  else:
    return url_parsed[0]

def wait(seconds):
  for i in range(0,seconds):
    if Glob.stop:
      sys.exit(1)
    else:
      sleep(1)

def get_image_urls(url):

  #fetch html from url
  f = urlopen(url)
  html_code = f.read()
  html_code = str(html_code)
  #Find urls to the images
  images =re.findall("(?:img|cgi|images).4chan.org/[a-z0-9]+/src/(?:cb-nws/)?(?:[0-9]*).(?:jpg|png|gif)", html_code)
  
  images = list(set(images))
  images_http = []
  for im in images:
    images_http.append("http://"+im)
  #Remove duplicate entries
  
  return images_http
  
def get_image(url): 
  
  #Test if url is up
  try:
    connection = urlopen(url)
  except urllib.error.HTTPError as e:
    print("Url down or something wrong: " + str(e.getcode()))
    return
  del connection
  
  #Parse section and thread number
  section = re.findall("4chan.org/[a-z0-9]*/res", url)[0].split("/")[1]
  number =  re.findall("res/[0-9]*", url)[0][4:]
  
  path = os.getcwd()
  path = os.path.join(path, section)
  #Create section directory
  if not os.path.isdir(path):
    os.mkdir(path)
    
  path = os.path.join(path, number)  
  #Create thread directory
  if not os.path.isdir(path):
    os.mkdir(path)
  #else:
    #print("Folder thread already exists")
    #sys.exit(1)
  
  #Download images
  down_images = []
  while True:
    #Get image urls
    try:
      images = get_image_urls(url)
    except urllib.error.HTTPError as e:
      print("Thread went 404, exiting...")
      #Glob.update_values()
      return
    
    for im in images:
      if Glob.stop:
        sys.exit(1)
      else:
        if im not in down_images:
          filename =  re.findall("[0-9]*.(?:jpg|gif|png)",im)[0]
          #print("Downloading "+im)
          if not os.path.exists(os.path.join(path,filename)):
            urlretrieve(im, os.path.join(path,filename))
          down_images.append(im)
          Glob.threadLock_mem.acquire()
          Glob.x[url]['number_images'] = str(len(down_images)) + "/" + str(len(images))          
          Glob.threadLock_mem.release()
          #Glob.update_values()
      
    #Wait 30 seconds until next check
    wait(30)
   
#class TableUpdater(threading.Thread):
#  def __init__(self, t): 
#    threading.Thread.__init__(self)
#    self.t = t
#    self.setDaemon(True)
#    
#  def run(self):
#    while True:
#      try: 
#        w   
#        w.update_table()
#      except: 
#        sleep(1)
#      sleep(self.t)
    
class Worker(threading.Thread):
  def __init__(self, url):
    threading.Thread.__init__(self)
    self.url = url
    #self.setDaemon(True)
    
  def run(self):
    
    #Start function to download images
    get_image(self.url)
    
    Glob.threadLock_mem.acquire()
    Glob.x[self.url]["is404"] = True
    Glob.x[self.url]["isActive"] = False
    Glob.write()
    Glob.threadLock_mem.release()
    
class Reader(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    
  def run(self):
    print("Starting reader...")
    Glob.threadLock_mem.acquire()
    for k, v in Glob.x.items():
      if Glob.x[k]['is404'] == False:
        w = Worker(k)
        w.start()
        Glob.x[k]["isActive"] = True
      
    Glob.write()
    Glob.threadLock_mem.release()
    
    while True:
      if Glob.stop:
        sys.exit(1)
      elif Glob.update:
        Glob.threadLock_mem.acquire()
        #print(Glob.x)
        for k, v in Glob.x.items():
          if not Glob.x[k]["isActive"] and not Glob.x[k]["is404"]:
            w = Worker(k)
            w.start()
            Glob.x[k]["isActive"] = True
        Glob.write()
        Glob.update = False
        Glob.threadLock_mem.release()
      else:
        sleep(1)
  
  
def print_db():
  print("Database " + Glob.db)
  Glob.threadLock_mem.acquire()  
  print(Glob.x)
  Glob.threadLock_mem.release()
  
def add_db(url):
  Glob.threadLock_mem.acquire()
  if not url in Glob.x:
    print("Adding url... " + url)
    Glob.x[url] = {}	
    Glob.x[url]["is404"] = False
    Glob.x[url]["isActive"] = False
    Glob.x[url]['section'] = re.findall("4chan.org/[a-z0-9]*/res", url)[0].split("/")[1]
    Glob.x[url]['thread'] = re.findall("res/[0-9]*", url)[0][4:]
    Glob.x[url]['number_images'] = '*/*'
  else:
    print("Already downloading thread " + url)
    
  Glob.write()
  Glob.threadLock_mem.release()
  
def get_db():
  return Glob.x
        
def exit_all(app):
  app.exec_()
  Glob.stop = True
  print("Please, wait while the program is finishing")
        
def main():
  
  #Check input arguments
  if len(sys.argv) != 2:
    print("usage: ./4chan.py urls_file")
    sys.exit(1)
  
  global db
  db = sys.argv[1]  
  
  if sys.argv[1] == "s":
    db = "urls_db"
    Glob.initialize(db)
    print_db()
    sys.exit(1)
    
  Glob.initialize(db)
  
  reader = Reader()
  reader.start()
  

#  updater = TableUpdater(1)
#  updater.start()
  
  app = QApplication(sys.argv)
  w = MyWindow()
  
  timer = QTimer()
  timer.timeout.connect(w.update_table)
  timer.start(1000)
  
  sys.exit(exit_all(app))

if __name__ == "__main__":
  main()
