import sys
from random import randrange
from threading import Thread
from multiprocessing import Process, Lock, Value
from hashlib import sha512
from time import sleep

PROCESS_LIMIT = 12
REFRESH_RATE = 1

class Counter(object):
  def __init__(self, initval=0):
    self.val = Value('i', initval)
    self.lock = Lock()

  def increment(self, buff):
    with self.lock:
      self.val.value += buff

  def getAndReset(self):
    with self.lock:
      result = self.val.value
      self.val.value = 0
      return result

class BaseThread(Process):
  def __init__(self, counter):
    Process.__init__(self)
    self.counter = counter

  def stop(self):
    self.running = False

class hashNum(BaseThread):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.currentValue = 0

  def hashIt(self):
    try:
      while True:
        num = randrange(100000000)
        m = sha512()
        m.update(num.to_bytes(8, byteorder='big'))
        m.digest()
        self.currentValue += 1
    except KeyboardInterrupt:
      return

  def getValue(self):
    try:
      while True:
        sleep(REFRESH_RATE)
        self.counter.increment(self.currentValue)
        self.currentValue = 0
    except KeyboardInterrupt:
      return

  def run(self):
    hashThread = Thread(target=self.hashIt)
    bufferThread = Thread(target=self.getValue)
    hashThread.daemon = True
    bufferThread.daemon = True  
    try:
      hashThread.start()
      bufferThread.start()
      while 1:
        pass
    except KeyboardInterrupt:
      hashThread.join()
      bufferThread.join()
      return

class hashPerSecond(BaseThread):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def run(self):
    try:
      while True:
        sleep(REFRESH_RATE)
        value = self.counter.getAndReset()
        sys.stdout.write('\r{count} HASH/S'.format(count=value))
        sys.stdout.flush()
    except KeyboardInterrupt:
      return

def main():
  print('STARTING FURNACE')
  pool = []
  c = Counter()
  p = hashPerSecond(c)
  p.daemon = True
  pool.append(p)
  for _ in range(PROCESS_LIMIT):
    t = hashNum(c)
    t.daemon = True
    pool.append(t)
  print('STARTING {} PROCESSES'.format(len(pool)))
  for t in pool:
      t.start()
  try:
    while 1:
      pass
  except KeyboardInterrupt:
    print('\nExiting...')
    for t in pool:
      t.terminate()
      t.join()
    exit()
    

if __name__ == '__main__':
  main()
