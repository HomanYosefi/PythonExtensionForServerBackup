import os
import paramiko
from datetime import datetime
import schedule
import time


timeBackup = "13:00"
processTime = timeBackup.split(":")
timePlus = f"{int(processTime[0]) + 1}:{processTime[1]}"
timeMines = f"{int(processTime[0]) - 1}:{processTime[1]}"

# max save database 
max_databases = 30

# information servers
source_ssh_host = 'source_host'
source_ssh_port = 22
source_ssh_username = 'source_username'
source_ssh_private_key_path = '/path/to/source/private_key'
source_file_path = '/path/to/source/file.txt'

dest_ssh_host = 'destination_host'
dest_ssh_port = 22
dest_ssh_username = 'destination_username'
dest_ssh_private_key_path = '/path/to/destination/private_key'
dest_file_path = '/path/to/destination/'


def connect_to_servers():
      # connect server limo
      source_ssh_client = paramiko.SSHClient()
      source_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      source_ssh_private_key = paramiko.RSAKey.from_private_key_file(source_ssh_private_key_path)
      source_ssh_client.connect(hostname=source_ssh_host, port=source_ssh_port, username=source_ssh_username, pkey=source_ssh_private_key)
      
      # connect server hetzener
      dest_ssh_client = paramiko.SSHClient()
      dest_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      dest_ssh_private_key = paramiko.RSAKey.from_private_key_file(dest_ssh_private_key_path)
      dest_ssh_client.connect(hostname=dest_ssh_host, port=dest_ssh_port, username=dest_ssh_username, pkey=dest_ssh_private_key)

      return source_ssh_client, dest_ssh_client


def send_database():
    source_ssh_client, dest_ssh_client = connect_to_servers()

    # Get list of existing zip files
    existing_files = [f for f in os.listdir(dest_file_path) if f.endswith('.zip')]
    if existing_files:
        max_index = max([int(f.split('.')[0]) for f in existing_files])
        next_index = max_index + 1
    else:
        next_index = 1

    # Zip the database file
    zip_file_name = f"{next_index}.zip"
    zip_file_path = os.path.join(dest_file_path, zip_file_name)
    os.system(f"zip -r {zip_file_path} {source_file_path}")

    # Send the zipped database file
    sftp = dest_ssh_client.open_sftp()
    sftp.put(zip_file_path, zip_file_path)
    sftp.close()

    # Delete the zipped database file
    os.remove(zip_file_path)

    # Disconnect servers
    source_ssh_client.close()
    dest_ssh_client.close()


# in 24h start
def job():
      send_database()
      delete_old_database()


def delete_old_database():
    files = [f for f in os.listdir(dest_file_path) if f.endswith('.zip')]
    
    # if number data > max database => delete old database 
    if len(files) >= max_databases:
        files.sort()
        os.remove(os.path.join(dest_file_path, files[0]))
        for i in range(1, len(files)):
            os.rename(os.path.join(dest_file_path, files[i]), os.path.join(dest_file_path, f"{i}.zip"))

 


schedule.every().day.at(timeBackup).do(job)  

# start app 
# In order to make the extension work optimally in unwanted hours,
# I changed the sleep time of the application to half an hour, and with one hour floating time,
# the requested time duration is one minute each time the clock is checked.
while True:
      schedule.run_pending()
      current_time = datetime.now().time()
      if datetime.strptime(timePlus, '%H:%M').time() <= current_time <= datetime.strptime(timeMines, '%H:%M').time():
            time.sleep(60)
      else:
            time.sleep(1800)   



