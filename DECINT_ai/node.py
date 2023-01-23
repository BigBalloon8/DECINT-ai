"""
node 
"""

import socket
import random
import pickle
import time
import ast
import concurrent.futures
from ecdsa import SigningKey, VerifyingKey, SECP112r2
import multiprocessing
import json
import hashlib
import traceback
import os
import asyncio
import textwrap

#recieve from nodes

class NotCompleteError(Exception):
    """
    Raised when problem with line but the line is needed to be kept in recent messages
    """
    pass

def message_hash(message):
    return hashlib.sha256(message.encode()).hexdigest()

class TimeOutList(): #TODO test in working simulation
    def __init__(self):
        self.t_list = []
        self.times = []

    def timeout(self):
        removed = 0
        if len(self.t_list) == 0:
            return
        for i in range(len(self.t_list)):
            if time.time()-self.times[i-removed] > 5.0:
                self.t_list.pop(i-removed)
                self.times.pop(i-removed)
                removed +=1

    def __len__(self):
        return len(self.t_list)

    def append(self, value):
        self.t_list.append(value)
        self.times.append(time.time())

    def __setitem__(self,index, value):
        return self.t_list.__setitem__(index,value)

    def __getitem__(self, index):
        self.timeout()
        return self.t_list.__getitem__(index)

    def remove(self, value):
        self.times.pop(self.t_list.index(value))
        self.t_list.remove(value)

    def __iter__(self):
        self.timeout()
        for i in self.t_list:
            yield i

    def __delitem__(self, index):
        self.t_list.__delitem__(index)
        self.times.__delitem__(index)

    def insert(self, index, value):
        self.t_list.insert(index, value)
        self.times.insert(index, time.time())



class MessageManager:
    def __init__(self, req_queue, message_queue):
        self.long_messages = TimeOutList()
        self.req_queue = req_queue
        self.message_queue = message_queue

    def write(self, address, message):

        if (" " not in message and "ONLINE?" not in message and "GET_NODES" not in message) or "NREQ" in message:  # TODO clean this up
            self.long_messages.append((address[0], message))

        else:
            message = f"{address[0]} {message}".split(" ")

            try:
                message_handler(message)
            except NodeError as e:
                print([message], e)
                send(message[0], f"ERROR {e}")
            except NotCompleteError:
                return

            self.message_queue.put(" ".join(message))
            #print("added to relay")

            # with open(f"{os.path.dirname(__file__)}/recent_messages.txt", "a+") as file:
                # file.write(f"{address[0]} {message}\n")
            # with open(f"{os.path.dirname(__file__)}/relay_messages.txt", "a+") as file:
                # file.write(f"{address[0]} {message}\n")

        for i in self.long_messages:
            if i[1][-67:-64] == "END":
                complete_message = [k for k in self.long_messages.t_list if i[0] == k[0]]
                if message_hash(" ".join([k[1] for k in complete_message])[:-67]) == i[1][-64:]:
                    long_write_lines = ''.join([j[1] for j in complete_message])
                else:
                    continue
                message = f"{i[0]} {long_write_lines[:-67]}".split(" ")

                try:
                    message_handler(message)
                except NodeError as e:
                    print([message], e)
                    send(message[0], f"ERROR {e}")
                except NotCompleteError:
                    return

                if "NREQ" in message:
                    self.req_queue.put(" ".join(message))

                for m in complete_message:
                    self.long_messages.remove(m)


def message_manager_process(message_manager: MessageManager, message_pipeline):  # works as thread as well
    while True:
        message_manager.write(*message_pipeline.recv())


# recieve from nodes
def receive(req_queue, message_queue):
    """
    message is split into array the first value the type of message the second value is the message
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", 1379))
    server.listen()
    message_handle = MessageManager(req_queue, message_queue)
    receive_pipe, send_pipe = multiprocessing.Pipe()
    p = multiprocessing.Process(target=message_manager_process, args=(message_handle, receive_pipe))
    p.start()
    while True:
        try:
            client, address = server.accept()
            message = client.recv(2 ** 16).decode("utf-8")  # .split(" ")
            send_pipe.send((address, message))
        except Exception as e:
            traceback.print_exc()



# send to node
def send(host, message, port=1379, send_all=False):
    """
    sends a message to the given host
    tries the default port and if it doesn't work search for actual port
    this process is skipped if send to all for speed
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((host, port))
        client.sendall(message.encode("utf-8"))
        print(f"Message to {host} {message}\n")
    except ConnectionRefusedError:
        if send_all:
            return
        try:
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                nodes = json.load(file)
            for node in nodes:
                if node["ip"] == host:
                    if not int(node["port"]) == 1379:
                        client.connect((host, int(node["port"])))
                        client.sendall(message.encode("utf-8"))
                        print(f"Message to {host} {message}\n")
        except ConnectionRefusedError:
            return "node offline"
        client.close()

async def async_send(host, message, port=1379, send_all=False):
    """
    sends a message to the given host
    tries the default port and if it doesn't work search for actual port
    this process is skipped if send to all for speed
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((host, port))
        client.sendall(message.encode("utf-8"))
        print(f"Message to {host} {message}\n")
    except ConnectionError:
        if not send_all:
            try:
                with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                    nodes = json.load(file)
                for node in nodes:
                    if node[1] == host:
                        if not int(node["port"]) == 1379:
                            client.connect((host, int(node["port"])))
                            client.sendall(message.encode("utf-8"))
                            print(f"Message to {host} {message}\n")
            except ConnectionError:
                return "node offline"

    client.close()

# check if nodes online
def online(address):
    try:
        send(address, "ONLINE?") #TODO add a way to timeout
        return True
    except TimeoutError:
        return False

def rand_act_node(num_nodes=1, type_=None):
    """
    returns a list of random active nodes which is x length
    """
    with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "r") as file:
        key = file.read()
    nodes = []
    i = 0
    while i != num_nodes:  # turn into for loop
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
            all_nodes = json.load(file)
        if type_:
            all_nodes = [node for node in all_nodes if node["node_type"] == type_]
        me = socket.gethostbyname(socket.gethostname())
        node_index = random.randint(0, len(all_nodes) - 1)
        node = all_nodes[node_index]
        # print(node)
        if node["pub_key"] == key or node["ip"] == me:
            continue
        alive = online(node["ip"])
        if alive:
            nodes.append(node)
            i += 1

    if len(nodes) == 1:
        return nodes[0]
    return nodes

def line_remover(del_lines, file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()
    new_lines = [line for line in lines if line.strip("\n") not in del_lines]
    open(file_path, "w").close()
    with open(file_path, "a") as file:
        for line in new_lines:
            file.write(line)

async def send_to_all(message, no_dist=False):
    """
    sends to all nodes
    """
    while True:
        try:
            with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                all_nodes = json.load(file)
                break
        except json.decoder.JSONDecodeError:
            pass
        if no_dist:
            all_nodes = [i for i in all_nodes if i["node_type"] != "dist"]
    for _ in asyncio.as_completed(
        [async_send(node["ip"], message, port=node["port"], send_all=True) for node in all_nodes]):
        result = await _

async def send_to_all_no_dist(message):
    """
    sends to all nodes
    """
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        all_nodes = json.load(file)
    for f in asyncio.as_completed([async_send(node_["ip"], message, port=node_["port"], send_all=True) for node_ in all_nodes if node_["node_type"]!="dist"]):
        result = await f

def announce(pub_key, port, version, node_type, priv_key):
    announcement_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(announcement_time.encode()).hex())
    print(f"HELLO {announcement_time} {pub_key} {port} {version} {node_type} {sig}")
    asyncio.run(send_to_all(f"HELLO {announcement_time} {pub_key} {port} {version} {node_type} {sig}"))


def update(old_key, port, version, priv_key, new_key=None):
    if not new_key:
        new_key = old_key
    update_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(update_time.encode()).hex())
    asyncio.run(send_to_all(f"UPDATE {update_time} {old_key} {new_key} {port} {version} {sig}"))
    with open(f"{os.path.dirname(__file__)}/info/Public_key.txt", "w") as file:
        file.write(new_key)


def delete(pub_key, priv_key):
    update_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(update_time.encode()).hex())
    asyncio.run(send_to_all(f"DELETE {update_time} {pub_key} {sig}"))

def get_nodes(nodes, queue):
    print("---GETTING NODES---")
    pre_nodes = copy.copy(nodes)
    while True:
        node = rand_act_node()
        if node in nodes:
            break
            continue
        else:
            break
    time.sleep(0.1)
    send(node["ip"], "GET_NODES")
    tries = 0
    while True:
        if tries == 10:
            return get_nodes(pre_nodes, queue)
        time.sleep(1)
        line = queue.get()
        if line:
            line = line.split(" ")
            if line[0] == node["ip"]:
                nodes_1 = json.loads(line[2])
                print("---NODES 1 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    while True:
        node = rand_act_node()
        if node in nodes:
            break
            continue
        else:
            break
    time.sleep(0.1)
    send(node["ip"], "GET_NODES")
    tries = 0
    while True:
        if tries == 10:
            return get_nodes(pre_nodes, queue)
        time.sleep(1)
        line = queue.get()
        if line:
            line = line.split(" ")
            if line[0] == node["ip"]:
                nodes_2 = json.loads(line[2])
                print("---NODES 2 RECEIVED---")
                break
        else:
            tries += 1
    nodes.append(node)
    if nodes_1 == nodes_2:
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
            json.dump(nodes_1, file)
        print("---NODES UPDATED---")
        return nodes
    return get_nodes(pre_nodes, queue)

def send_node(host):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    str_node = json.dumps(nodes)
    str_node = str_node.replace(" ", "")
    messages = textwrap.wrap("NREQ " + str_node, 5000)
    for message_ in messages:
        send(host, message_)


def new_node(initiation_time, ip, pub_key, port, node_version, node_type, sig):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(pub_key), curve=SECP112r2)
    if public_key.verify(bytes.fromhex(sig), str(initiation_time).encode()):
        new_node = {"time": initiation_time, "ip": ip, "pub_key": pub_key, "port": port, "version": node_version,
                    "node_type": node_type}
        for node in nodes:
            if node["pub_key"] == pub_key:
                return
            if node["ip"] == ip:
                return
        nodes.append(new_node)
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
            json.dump(nodes, file)
        print("---NODE ADDED---")
    else:
        return "node invalid"


def update_node(ip, update_time, old_key, new_key, port, node_version, sig):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(old_key), curve=SECP112r2)
    try:
        assert public_key.verify(bytes.fromhex(sig), str(update_time).encode())
        for node in nodes:
            if node["ip"] == ip:
                node["pub_key"] = new_key
                node["port"] = port
                node["version"] = node_version
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
            json.dump(nodes, file)
            print("NODE UPDATED")
    except:
        return "update invalid"


def delete_node(deletion_time, ip, pub_key, sig):
    with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
        nodes = json.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(pub_key), curve=SECP112r2)
    try:
        assert public_key.verify(bytes.fromhex(sig), str(deletion_time).encode())
        for node in nodes:
            if node["ip"] == ip and node["pub_key"] == pub_key:
                nodes.remove(node)
        with open(f"{os.path.dirname(__file__)}/info/nodes.json", "w") as file:
            json.dump(nodes, file)
    except:
        return "cancel invalid"


def send_node(host):
    with open("info/Nodes.pickle", "rb") as file:
        Nodes = pickle.load(file)
    str_node = str(Nodes)
    str_node = str_node.replace(" ", "")
    send(host, "NREQ " + str_node)

def new_node(time, ip, pub_key, port, version, node_type):
    with open("info/Nodes.pickle", "rb") as file:
        nodes = pickle.load(file)
    new_node = [time, ip, pub_key, port, version, node_type]
    for node in nodes:
        if node[2] == pub_key:
            return
    nodes.append(new_node)
    with open("info/Nodes.pickle", "wb") as file:
        pickle.dump(nodes, file)


def version(ver):
    send_to_all(f"VERSION {ver}")


def version_update(ip, ver):
    with open("info/Nodes.pickle", "rb") as file:
        nodes = pickle.load(file)
    for nod in nodes:
        if nod[1] == ip:
            nod[4] = ver
            break

class NodeError(Exception):
    pass


class UnrecognisedCommand(NodeError):
    pass


class ValueTypeError(NodeError):
    pass


class UnrecognisedArg(NodeError):
    pass


def message_handler(message):
    try:
        protocol = message[1]
    except:
        raise UnrecognisedArg("No Protocol Found")

    node_types = ["Lite", "Blockchain", "AI"]

    if protocol == "GET_NODES":
        # host, GET_NODES
        if len(message) != 2:
            raise UnrecognisedArg("number of args given incorrect")

    elif protocol == "HELLO":
        # host, HELLO, announcement_time, public key, port, version, node type, sig
        if len(message) != 8:
            raise UnrecognisedArg("number of args given incorrect")

        try:
            float(message[2])
            if "." not in message[2]:
                Exception()
        except:
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Public Key is the wrong size")

        try:
            port = int(message[4])
        except:
            raise ValueTypeError("port not given as int")

        if not port > 0 and port < 65535:
            raise ValueTypeError("TCP port out of range")

        try:
            float(message[5])
            if "." not in message[5]:
                Exception()
        except:
            raise ValueTypeError("version not given as float")

        if message[6] not in node_types:
            raise UnrecognisedArg("Node Type Unknown")

    elif protocol == "ONLINE?":
        # host, ONLINE?
        if len(message) != 2:
            raise UnrecognisedArg("number of args given incorrect")


    elif protocol == "UPDATE":
        # host, UPDATE, update time, public key, port, version, sig
        if len(message) != 7:
            raise UnrecognisedArg("number of args given incorrect")

        try:
            float(message[2])
            if "." not in message[2]:
                Exception()
        except:
            raise ValueTypeError("time not given as float")

        if len(message[3]) != 56:
            raise UnrecognisedArg("Public Key is the wrong size")

        try:
            port = int(message[4])
        except:
            raise ValueTypeError("port not given as int")

        if not port >= 0 and port < 65535:
            raise ValueTypeError("TCP port out of range")

        try:
            float(message[5])
            if "." not in message[5]:
                Exception()
        except:
            raise ValueTypeError("version not given as float")

    elif protocol == "DELETE":
        # host, DELETE, public key, sig
        if len(message) != 4:
            raise UnrecognisedArg("number of args given incorrect")

        if len(message[2]) != 56:
            raise UnrecognisedArg("Public Key is the wrong size")


    elif protocol == "NREQ":
        # host, NREQ, Nodes
        try:
            ast.literal_eval(message[2])
        except:
            raise ValueTypeError("Blockchain not given as Node List")

    
    elif protocol == "ERROR":
        pass

    elif protocol == "DIST":
        if len(message) != 4:
            raise UnrecognisedArg("number of args given ")
        
    elif protocol == "DEP":
        if len(message) != 4:
            raise UnrecognisedArg("number of args given ")
    
    elif protocol == "AI":
        if len(message) != 6:
            raise UnrecognisedArg("number of args given")
        if len(ast.literal_eval(message[4])) > 10:
            raise ValueTypeError("Too many nodes given")
    else:
        raise UnrecognisedCommand("protocol unrecognised")

if __name__ == "__main__":
    receive()
