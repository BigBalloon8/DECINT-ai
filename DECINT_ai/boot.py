import os
import concurrent.futures
import node
import multiprocessing
import threading
from DECINT_ai import reader


"""
update tensorflow
update Blockchain and nodes
"""
#open("recent_messages.txt", "w").close()#clear recent message file

local_ip = "127.0.0.1"#socket.gethostbyname(socket.gethostname())

os.system("pip3 install --upgrade tensorflow")
os.system("pip3 install --upgrade ecdsa")
def run():
    req_queue = multiprocessing.Queue()
    message_queue = multiprocessing.Queue()

    rec = multiprocessing.Process(target=node.receive, args=(req_queue, message_queue))
    rec.start()

    up = threading.Thread(target=node.get_nodes, args=([], req_queue))
    up.start()
    up.join()
    req_queue.close()

    read = multiprocessing.Process(target=reader.read, args=(message_queue,))
    read.start()


