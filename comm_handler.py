import paramiko
import time
from getpass import getpass
import random
 
# paramiko functions -- START
def establish_ssh_connection(hostname,username,password):
  delay=round(random.uniform(0.1,0.5),1)
  time.sleep(delay)
  ssh=paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  def connect(ssh):
    try:
      ssh.connect(hostname, port=22, username=username,password=password, timeout=50, banner_timeout=600, auth_timeout=30)
      return ssh
    except paramiko.AuthenticationException as _:
      print(f'{hostname} Authentication error occured.')
      return None
    except Exception as _:
      ssh.close()
      return None
  retry_counter=1
  while ssh.get_transport() is None and retry_counter <= 15:
    connect(ssh)
    time.sleep(2)
    if ssh.get_transport() is None:
      r_delay=round(random.uniform(4.5,5.5),1)
      #
      time.sleep(r_delay)
    retry_counter+=1
  if ssh.get_transport() is None:
    print(f'connecting to {hostname} failed after {retry_counter} attempts')
    return None
  else:
    return ssh
def create_channel(client):
  try:
    channel=client.invoke_shell()
    send_command('PS1=\'$ \'', channel)
    retry_counter=1
    while not channel.recv_ready():
      if retry_counter > 10:
        break
      retry_counter+=1
      time.sleep(0.3)
    if channel.recv_ready():
      channel.recv(2048).decode(encoding='UTF-8')
    return channel
  except Exception as e:
    print(f'an error occured while creating channel: {e}')
    return None
def send_command(cmd,channel):
  while not channel.send_ready():
    time.sleep(0.1)
  channel.send(f'{cmd}\n')
  time.sleep(0.1)
  return receive_data(channel)
def receive_data(channel):
  result=''
  repeat_counter=0
  while (not result.endswith(('> ','$ '))) and (not (result.find('[sudo] password for') > -1)):
    if not channel:
      print('Channel closed unexpectedly.')
      break
    while not channel.recv_ready():
      if any((result.endswith(('> ','$ ')),channel.send_ready())):
        break
      repeat_counter+=1
      print(f'repeat_counter={repeat_counter} on {channel}')
      time.sleep(0.1)
    while channel.recv_ready():
      result+=channel.recv(2048).decode(encoding='UTF-8')
      if not channel.recv_ready():
        time.sleep(0.2)
  return list(result.split('\r\n'))[1:][:-1]
def sudo(user,pwd,channel):
  while not channel.send_ready():
    time.sleep(0.1)
  try:
    if send_command('whoami',channel)[0]==user:
      return True
  except Exception as e:
    print(f'error occured while executing "whoami": {e}')
 
  def sudo_with_retry(user,pwd,channel):
    send_command(f'sudo -su {user}', channel)
    while not channel.send_ready():
      time.sleep(0.1)
    send_command(pwd,channel)
    while not channel.send_ready():
      time.sleep(0.1)
    try:
      return str(send_command('whoami',channel)[0])==user
    except Exception as _:
      return False
  retry_counter=1
  while sudo_with_retry(user,pwd,channel) is False and retry_counter <=5:
    time.sleep(0.5)
    retry_counter+=1
  
  if retry_counter > 5:
    return False
  else:
    return True
def get_PID(is_running,instance,fwk_ctr,channel):
  is_running=is_running.replace('{instance}',instance).replace('{fwk_ctr}',fwk_ctr)
  try:
    if 'brkctl' in is_running:
      tmp=send_command(f"{is_running} | awk '{{print $5}}'",channel)
      status=int(tmp[0].lstrip('(').rstrip('.)'))
    elif 'fwctl' in is_running:
      tmp=send_command(f"{is_running} | grep Framework | awk '{{print $7}}'",channel)
      status=int(tmp[0].lstrip('(').rstrip('.)'))
    elif 'zookeeper' in is_running:
      tmp=send_command(f"{is_running} | awk '{{print $1}}'",channel)
      status=int(tmp[0])
    else:
      tmp=send_command(f"{is_running} | awk '{{print $2}}'",channel)
      status=int(tmp[0])
  except:
    status=0
  return status
 
 
if __name__ == '__main__':
  import sys
 
  servers=['attraktor.mooo.com']
  uname=input('Please enter your username: ')
  pwd=getpass('Please enter your password: ')
  commands=['uname','date']
 
  for server in servers:
    client=establish_ssh_connection(server,uname,pwd)
    channel=create_channel(client)
    if channel:
      for command in commands:
        for line in send_command(command,channel):
          print(line)
 
      channel.shutdown(2)
      channel.close()
      client.close()
    else:
      print(f'I could not connect to {server}')
 
'''
import paramiko
ssh=paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<server>', port=22, username='',password='', timeout=50, banner_timeout=600, auth_timeout=30)
channel=ssh.invoke_shell()
channel.send(f'date\n')
channel.shutdown(2)
channel.close()
ssh.close()
'''