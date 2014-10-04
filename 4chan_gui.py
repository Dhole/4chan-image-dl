#!/usr/bin/python3

""" The Chandler: imageboard pictures downloader
This program will download all the images from various imageboards threads until 404'ed """

__author__ = "Dhole"
__license__ = "WTFPL - Do What The Fuck You Want To Public License "
__version__ = "0.6"
__email__ = "bankukur@gmail.com"
__status__ = "Beta"
__date__ = "10 May 2012"


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from urllib.request import urlopen, urlretrieve
from time import sleep
from contextlib import closing
import urllib.error
import sys, operator, pickle, os, threading, re, webbrowser, shutil, queue, urllib.request, platform, subprocess

import socket
socket.setdefaulttimeout(10)


class Glob(object):

  stop = False
  update = False
  my_array = []
  header = ['url', 'im board', 'section', 'thread', 'images', 'status']
  x = {}
  threadLock_mem = threading.RLock()
  threadLock_file = threading.RLock()
  db = ''
  q = {}

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
      my_array.append([])
      my_array[i].append(k)
      my_array[i].append(v['imboard'])
      my_array[i].append(v['section'])
      my_array[i].append(v['thread'])
      my_array[i].append(v['number_images'])

      if v['is404']:
        my_array[i].append('404')
      else:
        if v['isPaused']:
          my_array[i].append('Paused')
        else:
          my_array[i].append('Active')
      i = i + 1
    if len(Glob.x) == 0:
      my_array.append([[' '],[' '],[' '],[' '],[' '],[' ']])

    Glob.threadLock_mem.release()
    Glob.my_array = my_array

  def delete(url):
    Glob.threadLock_mem.acquire()
    del Glob.x[url]
    Glob.write()
    Glob.threadLock_mem.release()
    imboard = get_imageboard(url)
    section = get_section(url) #re.findall("4chan.org/[a-z0-9]*/res", url)[0].split("/")[1]
    number =  get_number_thread(url) #re.findall("res/[0-9]*", url)[0][4:]
    path = os.getcwd()
    path = os.path.join(path, imboard)
    path = os.path.join(path, section)
    path = os.path.join(path, number)
    if os.path.isdir(path):
      shutil.rmtree(path)
    else:
      print('Folder didn\'t exist')

class TheTable(QTableView):
  def __init__(self, parent = None):
    QTableView.__init__(self, parent)

    self.tablemodel = MyTableModel(Glob.my_array, Glob.header, self)

    self.setModel(self.tablemodel)
    self.resizeRowsToContents()
    self.resizeColumnsToContents()
    self.setSortingEnabled(True)
    self.verticalHeader().hide()
    for i in range(0,6):
      cur_size = self.horizontalHeader().sectionSize(i)
      self.horizontalHeader().resizeSection(i,cur_size + 20)
    self.horizontalHeader().setResizeMode(QHeaderView.Fixed)
    self.horizontalHeader().setStretchLastSection(True)
    self.current_row = -1

  def mousePressEvent(self, event):
    index = self.indexAt(event.pos())

    if (index.isValid()):
      self.current_row = row = index.row()
      self.selectRow(self.current_row)
    else:
      self.current_row = row = -1
      self.clearSelection()

  def contextMenuEvent(self, event):

    index = self.indexAt(event.pos())

    if (index.isValid() and len(Glob.x) != 0):
      row = index.row()
      self.current_row = row
      self.selectRow(self.current_row)
      column = index.column()
      value = self.model().index(row, 0).data()
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

    menu.addAction(browse_urlAction)
    menu.addAction(view_folderAction)
    menu.addAction(copyAction)
    menu.addSeparator()
    menu.addAction(pauseAction)
    menu.addAction(continueAction)
    menu.addSeparator()
    menu.addAction(clearAction)
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
    menu.popup(event.globalPos())

  def continue_slot(self, value):
    print("Continuing with " + value)
    Glob.q[value].put('continue')

  def pause_slot(self, value):
    print("Pausing " + value)
    Glob.q[value].put('pause')

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
      Glob.write()
    else:
      print(value + " is not 404, you should delete it instead")
    Glob.threadLock_mem.release()

  def view_folder_slot(self, value):
    print("Viewing folder" + value)
    imboard = get_imageboard(value)
    section = get_section(value) #re.findall("4chan.org/[a-z0-9]*/res", value)[0].split("/")[1]
    number =  get_number_thread(value) #re.findall("res/[0-9]*", value)[0][4:]
    path = os.getcwd()
    path = os.path.join(path, imboard)
    path = os.path.join(path, section)
    path = os.path.join(path, number)
    #This works fine on unix
    if platform.system() == 'Windows':
      subprocess.Popen('explorer \"'+path+'\"')
    else:
      os.system("xdg-open " + path)

  def delete_slot(self, value):
    print("Deleting " + value)
    Glob.threadLock_mem.acquire()
    is404 = Glob.x[value]['is404']
    Glob.threadLock_mem.release()
    if is404:
      Glob.delete(value)
    else:
      Glob.q[value].put('delete')


  #def updateGeometries(self):
    #super(TheTable, self).updateGeometries()
    #self.verticalScrollBar().setSingleStep(2)


class MyWindow(QMainWindow):
  def __init__(self, *args):
    QWidget.__init__(self, *args)

    self.centralwidget = QWidget(self)
    topBox = QHBoxLayout()
    box = QVBoxLayout(self.centralwidget)
    self.urlLine = QLineEdit(self)
    topBox.addWidget(self.urlLine)
    self.downloadButton = QPushButton('', self)
    self.downloadButton.setIcon(QIcon('icons/download.svg'))
    self.downloadButton.setEnabled(False)
    topBox.addWidget(self.downloadButton)
    #self.downloadMoreButton = QPushButton('Download more', self)
    #topBox.addWidget(self.downloadMoreButton)
    box.addLayout(topBox)
    self.tb = TheTable(self.centralwidget)
    box.addWidget(self.tb)
    self.setCentralWidget(self.centralwidget)

    self.url = ''
    self.downloadButton.clicked.connect(self.downloadUrl)
    self.urlLine.textChanged[str].connect(self.enteredUrl)
    self.urlLine.returnPressed.connect(self.downloadUrl)

    self.createActions()
    self.createMenus()
    self.createStatusBar()

    pauseAllAction = QAction(QIcon('icons/stop.svg'), 'Pause all', self)
    pauseAllAction.setShortcut('Ctrl+P')
    pauseAllAction.triggered.connect(self.pauseAllSlot)

    continueAllAction = QAction(QIcon('icons/continue.svg'), 'Continue all', self)
    continueAllAction.setShortcut('Ctrl+P')
    continueAllAction.triggered.connect(self.continueAllSlot)

    clear404Action = QAction(QIcon('icons/clear.svg'), 'Clear all 404', self)
    clear404Action.setShortcut('Ctrl+P')
    clear404Action.triggered.connect(self.clear404Slot)

    self.menu = QMenu()
    self.menu.addAction("un")
    self.menu.addAction("dos")

    self.toolbar = self.addToolBar('Pause all')
    self.toolbar.setFloatable(False)
    self.toolbar.setMovable(False)
    self.toolbar.addAction(pauseAllAction)
    self.toolbar = self.addToolBar('Continue all')
    self.toolbar.setFloatable(False)
    self.toolbar.setMovable(False)
    self.toolbar.addAction(continueAllAction)
    self.toolbar = self.addToolBar('Clear all 404 all')
    self.toolbar.setFloatable(False)
    self.toolbar.setMovable(False)
    self.toolbar.addAction(clear404Action)

    self.setWindowIcon(QIcon('icons/big_icon.png'))
    self.setGeometry(300, 50, 800, 400)
    self.update_dimensions()
    self.setWindowTitle('The Chandler')
    self.show()

  def update_dimensions(self):
    self.tb.resizeRowsToContents()
    self.tb.resizeColumnsToContents()
    width = 0

    for i in range(0,6):
      cur_size = self.tb.horizontalHeader().sectionSize(i)
      self.tb.horizontalHeader().resizeSection(i,cur_size)
      width = width + cur_size + 8

    if width < 600:
      width = 600

    self.setMaximumWidth(width)
    self.setMinimumWidth(width/2)
    self.setMinimumHeight(400)
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
      add_db(url_ok)
      Glob.update = True
      Glob.update_values()
      self.update_table()

  def update_table(self):
    Glob.update_values()

    self.tb.tablemodel.update(Glob.my_array) # = MyTableModel(Glob.my_array, Glob.header, self.tb)
    #self.tb.show()

    self.tb.setModel(self.tb.tablemodel)
    sort_column = self.tb.horizontalHeader().sortIndicatorSection()
    sort_order = self.tb.horizontalHeader().sortIndicatorOrder()
    self.tb.sortByColumn(sort_column, sort_order)
    self.update_dimensions()
    if self.tb.current_row != -1:
      self.tb.selectRow(self.tb.current_row)

  def pauseAllSlot(self):
    self.statusBar().showMessage(self.tr("Pausing all threads"))
    print("Pausing all threads")
    for k, v in Glob.q.items():
      Glob.q[k].put('pause')

  def continueAllSlot(self):
    self.statusBar().showMessage(self.tr("Continuing all threads"))
    print("Continuing all threads")
    for k, v in Glob.q.items():
      Glob.q[k].put('continue')

  def clear404Slot(self):
    self.statusBar().showMessage(self.tr("Clearing all 404 threads"))
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
    QMessageBox.about(self, self.tr("About The Chandler"),
    self.tr("The Chandler\n\n"
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

  def update(self, datain):
    self.arraydata = datain

  def rowCount(self, parent):
      return len(self.arraydata)

  def columnCount(self, parent):
    return len(self.arraydata[0])

  def data(self, index, role):
    if not index.isValid():
      return None
    elif role == Qt.BackgroundColorRole :
      if self.arraydata[index.row()][5] == "Active":
        return QColor(Qt.green)
      elif self.arraydata[index.row()][5] == "Paused":
        return QColor(Qt.yellow)
      elif self.arraydata[index.row()][5] == "404":
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
  url_parsed = re.findall("http(?:s)?://(?:boards.)?.*/*/res/[0-9]*(?:.php|.html)?", url)
  if len(url_parsed) < 1:
    return ""
  else:
    return url_parsed[0]

def get_section(url):
  result = re.findall(".*/[a-z0-9]*/res", url)[0].split("/")[-2]
  return result

def get_number_thread(url):
  result = re.findall("res/[0-9]*", url)[0][4:]
  return result

def get_imageboard(url):
  result = re.findall(".*/*/res/[0-9]*(?:.php|.html)?", url)[0].split("/")[-4].replace('boards.','').split(".")[0]
  return result

def get_image_urls(url):

  #print('LALALA ' + url)
  #fetch html from url
  with closing(urlopen(url)) as page:
    html_code = page.read()

  if Glob.stop:
    sys.exit(1)

  html_code = str(html_code)
  #Find urls to the images
  images = re.findall('\"[^\"]*/src/[0-9]*.(?:jpg|png|gif)\"', html_code)
  #Delete duplicate entries
  images = list(set(images))

  images_http = []

  for im in images:
    ima = im.replace('\"', '')
    if ima[:4] == 'http':
      images_http.append(ima)
    elif ima[:2] == '//':
      if url[:5] == 'https':
        images_http.append('https:'+ima)
      else:
        images_http.append('http:'+ima)
    else:
      if url[:5] == 'https':
        images_http.append('https://'+url.split('/')[2]+ima)
      else:
        images_http.append('http://'+url.split('/')[2]+ima)

  return images_http

def get_image(url):

  #Test if url is up
  while True:
    try:
      with closing(urlopen(url)) as connection:
        pass
    except urllib.error.HTTPError as e:
      if e.getcode() == 404:
        print("Url down or something wrong: " + str(e.getcode()))
        return '404'
      pass
    else:
      break

    print("Connection problems, trying again in 30 seconds...")
    try:
      order = Glob.q[url].get(block=True, timeout=30)
    except queue.Empty as e:
      pass
    else:
      if order == 'exit':
        return 'exit'
      else:
        break

  #del connection


  imboard = get_imageboard(url)
  section = get_section(url)#re.findall("4chan.org/[a-z0-9]*/res", url)[0].split("/")[1]
  number = get_number_thread(url) #re.findall("res/[0-9]*", url)[0][4:]
  path = os.getcwd()

  path = os.path.join(path, imboard)
  #Create imageboard directory
  if not os.path.isdir(path):
    os.mkdir(path)

  path = os.path.join(path, section)
  #Create section directory
  if not os.path.isdir(path):
    os.mkdir(path)

  path = os.path.join(path, number)
  #Create thread directory
  if not os.path.isdir(path):
    os.mkdir(path)

  #Download images
  down_images = []
  Glob.q[url].put('continue')
  while True:
    while True:
      try:
        order = Glob.q[url].get(block=True, timeout=30)
      except queue.Empty as e:
        break
      else:
        if order == 'pause':
          Glob.threadLock_mem.acquire()
          Glob.x[url]['isPaused'] = True
          Glob.threadLock_mem.release()
          continue
        elif order == 'continue':
          Glob.threadLock_mem.acquire()
          Glob.x[url]['isPaused'] = False
          Glob.threadLock_mem.release()
          break
        elif order == 'delete':
          return 'delete'
        elif order == 'exit':
          return 'exit'

    try:
      images = get_image_urls(url)
    except urllib.error.HTTPError as e:
      if e.getcode() == 404:
        print("Url down or something wrong: " + str(e.getcode()))
        return '404'
      continue
    except:
      print("Connection problems, trying again in 30 seconds!...")
      continue

    for im in images:
      if im not in down_images:
        if not Glob.q[url].empty(): break
        filename =  re.findall("[0-9]*.(?:jpg|gif|png)",im)[0]
        if not os.path.exists(os.path.join(path,filename)):
          try:
            urlretrieve(im, os.path.join(path,filename))
          except IOError as e:
            print('Network problem')
            break
          except:
            print('Other problem')
            break
        down_images.append(im)

        Glob.threadLock_mem.acquire()
        Glob.x[url]['number_images'] = str(len(down_images)) + "/" + str(len(images))
        Glob.threadLock_mem.release()


class Worker(threading.Thread):
  def __init__(self, url):
    threading.Thread.__init__(self)
    self.url = url

  def run(self):

    #Start function to download images
    status = get_image(self.url)

    Glob.threadLock_mem.acquire()
    if status == '404':
      Glob.x[self.url]["is404"] = True
      Glob.x[self.url]["isActive"] = False
    elif status == 'delete':
      Glob.x[self.url]['isPaused'] = True
    Glob.write()
    Glob.threadLock_mem.release()
    if status == 'delete':
      Glob.delete(self.url)


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
      Glob.q[k] = queue.Queue()

    Glob.write()
    Glob.threadLock_mem.release()

    while True:
      if Glob.stop:
        sys.exit(1)
      elif Glob.update:
        Glob.threadLock_mem.acquire()
        for k, v in Glob.x.items():
          if not Glob.x[k]["isActive"] and not Glob.x[k]["is404"]:
            w = Worker(k)
            w.start()
            Glob.x[k]["isActive"] = True
            Glob.q[k] = queue.Queue()
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
    Glob.x[url]["isPaused"] = False
    Glob.x[url]['imboard'] = get_imageboard(url)
    Glob.x[url]['section'] = get_section(url)#re.findall("4chan.org/[a-z0-9]*/res", url)[0].split("/")[1]
    Glob.x[url]['thread'] = get_number_thread(url)#re.findall("res/[0-9]*", url)[0][4:]
    Glob.x[url]['number_images'] = '*/*'
  else:
    print("Already downloading thread " + url)

  Glob.write()
  Glob.threadLock_mem.release()


def exit_all(app):
  app.exec_()
  Glob.stop = True
  for k, v in Glob.q.items():
    Glob.q[k].put('exit')
  Glob.threadLock_mem.acquire()
  Glob.write()
  Glob.threadLock_mem.release()
  print("Please, wait while the program is finishing")


def main():

  global db
  #Check input arguments
  if len(sys.argv) != 2:
    #print("usage: ./4chan.py urls_file")
    #sys.exit(1)
    db = 'urls_db'
  else:
    db = sys.argv[1]
    if sys.argv[1] == "s":
      db = "urls_db"
      Glob.initialize(db)
      print_db()
      sys.exit(1)

  Glob.initialize(db)

  reader = Reader()
  reader.start()

  app = QApplication(sys.argv)
  w = MyWindow()

  timer = QTimer()
  timer.timeout.connect(w.update_table)
  timer.start(1000)

  sys.exit(exit_all(app))

if __name__ == "__main__":
  main()
