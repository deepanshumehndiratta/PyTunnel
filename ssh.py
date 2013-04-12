'''
  @Title: Python script to Re-connect SSH Tunnels on Broken pipe
  @Author: Deepanshu Mehndiratta
  @URL: http://www.deepanshumehndiratta.com
'''

import subprocess,string,time,signal,sys,socket,os

class SSH:

  def __init__(self, port, username, host, sudo_username):
    self.port = port
    self.username = username
    self.host = host
    self.sudo_username = sudo_username
    self.attempt = False

  def isOpen(self,ip,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
     s.connect((ip, int(port)))
     s.shutdown(2)
     return True
    except:
     return False

  def connect(self):
    print "Connecting."
    command = "su - " + self.sudo_username + " -c 'ssh -D " + self.port + " " + self.username + "@" + self.host + "'"
    if self.attempt != True:
      self.p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    self.attempt = True

  def disconnect(self):
    print "Disconnecting."
    self.attempt = False
    #self.p.kill()

  def establish(self):
    if self.isOpen('127.0.0.1',self.port):
      print "Port already in use. Killing processes on port " + self.port + "."
      process = subprocess.Popen("netstat -ntlp | awk '$4~/:*" + self.port + """$/{gsub(/\/.*/,"",$NF);cmd="kill -9 "$NF;system(cmd)}'""", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      process.kill()
    self.connect()
    connect = False
    while True:
      out = self.p.stdout.readline()
      if out == '':
        if self.p.wait() != None:
          print "Process terminated."
          break
      if out != '':
        print out
        if connect != True:
          if self.isOpen('127.0.0.1',self.port):
            connect = True
            print "SSH Tunnel open on Port " + self.port + ". Press Ctrl+C to exit."
        if string.lower(out).find('broken pipe') != -1:
          self.disconnect()
          connect = False
          time.sleep(1)
          break
    if connect != True:
      self.establish()

if os.getuid() != 0:
  print "Exiting.\nPlease run this program as Super-User."
  exit(0)

port, username, host = sys.argv[1], sys.argv[2], sys.argv[3]

sudo_username = os.getenv("SUDO_USER")

print "Script Initialized. Trying to establish SSH connection."

ssh = SSH(port, username, host, sudo_username)

pid = os.fork()
if pid == 0:
  # Ensure that process is detached from TTY
  os.setsid()
  p = ssh.establish()
else:
  print "Waiting for ssh (pid %d)" % pid
  os.waitpid(pid, 0)    
  print "Done"

def signal_handler(signal, frame):
  print "You pressed Ctrl+C!\nExiting Program."
  p.disconnect()
  subprocess.Popen("netstat -ntlp | awk '$4~/:*" + sys.argv[1] + """$/{gsub(/\/.*/,"",$NF);cmd="kill -9 "$NF;system(cmd)}'""", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

signal.pause()