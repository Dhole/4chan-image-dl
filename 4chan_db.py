#!/usr/bin/python3.2
""" 4chan downloader
This program will download all the images from a 4chan thread until 404'ed """

from urllib.request import urlopen, urlretrieve
import urllib.error
from time import sleep
import os, sys, re, threading
import pickle


class Glob(object):
  stop = False
  update = False
  threadLock = threading.RLock()

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
  else:
    print("Folder thread already exists" + path)
    #sys.exit(1)
  
  #Download images
  down_images = []
  while True:
    #Get image urls
    try:
      images = get_image_urls(url)
    except urllib.error.HTTPError as e:
      print("Thread went 404, exiting...")
      return
    
    for im in images:
      if Glob.stop:
        sys.exit(1)
      else:
        if im not in down_images:
          filename =  re.findall("[0-9]*.(?:jpg|gif|png)",im)[0]
          #print("Downloading "+im)
          urlretrieve(im, os.path.join(path,filename))
          down_images.append(im)
      
    #Wait 30 seconds until next check
    wait(30)
    
class Worker(threading.Thread):
  def __init__(self, url):
    threading.Thread.__init__(self)
    self.url = url
    #self.setDaemon(True)
    
  def run(self):
    
    #Start function to download images
    get_image(self.url)
    
    Glob.threadLock.acquire()
    x = get_db()
    x[self.url]["is404"] = True
    x[self.url]["isActive"] = False
    write_db(x)
    Glob.threadLock.release()
    
class Reader(threading.Thread):
  def __init__(self, db):
    threading.Thread.__init__(self)
    self.db = 	db
    
  def run(self):
    print("Starting reader...")
    Glob.threadLock.acquire()
    x = get_db()
    for k, v in x.items():
      w = Worker(k)
      w.start()
      x[k]["isActive"] = True
    write_db(x)
    Glob.threadLock.release()
    
    print("Continuing old urls finished")
    
    while True:
      if Glob.stop:
        sys.exit(1)
      elif Glob.update:
        print("Waking up reader!")
        Glob.threadLock.acquire()
        x = get_db()
        for k, v in x.items():
          if not x[k]["isActive"] and not x[k]["is404"]:
            w = Worker(k)
            w.start()
            x[k]["isActive"] = True
        write_db(x)
        Glob.update = False
        Glob.threadLock.release()
      else:
        sleep(1)
  
  
def print_db():
  print("Database " + db)
  Glob.threadLock.acquire()  
  with open(db, 'rb') as f:
    print(pickle.load(f))
  Glob.threadLock.release()
  
def add_db(url):
  print("Adding url... " + url)
  Glob.threadLock.acquire()
  with open(db, 'rb') as f:
    x = pickle.load(f)
    if not url in x:
      x[url] = {}	
      x[url]["is404"] = False
      x[url]["isActive"] = False   
  with open(db, 'wb') as f:
    pickle.dump(x, f)
  Glob.threadLock.release()
  
def get_db():
  Glob.threadLock.acquire()  
  with open(db, 'rb') as f:
    x = pickle.load(f)
  Glob.threadLock.release()
  return x
  
def write_db(x):
  Glob.threadLock.acquire()
  with open(db, 'wb') as f:
    pickle.dump(x, f)
  Glob.threadLock.release()
    
def main():
  
  #Check input arguments
  if len(sys.argv) != 2:
    print("usage: ./4chan.py urls_file")
    sys.exit(1)
  
  global db
  db = sys.argv[1]  
  
  if sys.argv[1] == "s":
    db = "urls_db"
    print_db()
    sys.exit(1)
    
  cur_dir = os.getcwd()
  
  #Check db
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
  del x
  
  reader = Reader(db)
  reader.start()
  
  while True:
    url=input('Input the url of the 4chan tread: ')
    if url == "exit":
      Glob.stop = True
      sys.exit(1)
    else:
      url = check_url(url)
      if url == "":
        print("Bad url!")
      else:
        add_db(url)
        Glob.update = True
      #wake up


if __name__ == '__main__':
  main()
