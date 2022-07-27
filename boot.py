import os
import concurrent.futures
import node
import reciever

"""
update tensorflow
update Blockchain and nodes
"""
#open("recent_messages.txt", "w").close()#clear recent message file

local_ip = "127.0.0.1"#socket.gethostbyname(socket.gethostname())

os.system("pip3 install --upgrade tensorflow")
os.system("pip3 install --upgrade ecdsa")


"""
try:
    os.remove("install_decint.py")
    os.remove("instal   l.exe")
except:
    pass#wont work after first time ill come up with better way later
"""

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.submit(reciever.rec, local_ip)#start recieving
    executor.submit(node.get_nodes)#update nodes













