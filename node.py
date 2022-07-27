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

#recieve from nodes
def receive(local_ip):
    """
    message is split into array the first value the type of message the second value is the message
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((local_ip, 1379))
    server.listen()
    while True:
        try:
            client, address = server.accept()
            message = client.recv(2048).decode("utf-8").split(" ")
            server.close()
            return message, address
        except Exception as e:
            print(e)


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
        client.send(message.encode("utf-8"))
        print(f"Message to {host} {message}\n")
        return
    except Exception as e:
        if not send_all:
            if isinstance(e, ConnectionRefusedError):
                try:
                    with open("info/Nodes.pickle", "rb") as file:
                        nodes = pickle.load(file)
                    for node in nodes:
                        if node[1] == host:
                            if not int(node["port"]) == 1379:
                                client.connect((host, int(node["port"])))
                                client.send(message.encode("utf-8"))
                                print(f"Message to {host} {message}\n")
                                return
                except Exception as e:
                    return "node offline"




# check if nodes online
def online(address):
    """
    asks if a node is online and if it is it returns yh
    """
    print(address)
    try:
        send(address, "ONLINE?")
    except:
        return False
    time.sleep(5)
    message = request_reader("YH", ip=address)
    if message:
        message = message[0].split(" ")
        if message[1] == "yh":
            return True
    else:
        return False


def rand_act_node(num_nodes=1):
    """
    returns a list of random active nodes which is x length
    """
    with open("./info/Public_key.txt", "r") as file:
        key = file.read()
    nodes = []
    i = 0
    while i != num_nodes:  # turn into for loop
        with open("info/Nodes.pickle", "rb") as file:
            all_nodes = pickle.load(file)
        node_index = random.randint(0, len(all_nodes) - 1)
        node = all_nodes[node_index]
        print(node)
        if node["pub_key"] == key:
            continue
        alive = online(node["ip"])
        if alive:
            nodes.append(node)
            i += 1

    if len(nodes) == 1:
        return nodes[0]
    else:
        return nodes


def request_reader(type, script_identity = 0.0, ip="192.168.68.1"):
    with open("recent_messages.txt", "r") as file:
        lines = file.read().splitlines()
    NREQ_protocol = ["NREQ"]#node request
    DEP_protocol = ["DEP"]
    yh_protocol = ["yh"]
    NODE_Lines = []
    NREQ_Lines = []
    DEP_Lines = []
    yh_Lines = []
    if str(lines) != "[]":
        for line in lines:
            line = line.split(" ")

            if line[0] == "" or line[0] == "\n":
                del line # delete blank lines

            elif line[1] in NREQ_protocol:
                NREQ_Lines.append(" ".join(line))

            elif line[1] in DEP_protocol and line[2] == script_identity:
                DEP_Lines.append(" ".join(line))
                
            elif line[1] in yh_protocol:
                yh_Lines.append(" ".join(line))



        if type == "YH":
            if len(yh_Lines) != 0:
                new_lines = []
                with open("recent_messages.txt", "r") as file:
                    file_lines = file.readlines()
                for f_line in file_lines:
                    f_line.split(" ")
                    if not yh_Lines[0] in f_line:
                        if not f_line.strip("\n") == "":
                            new_lines.append(f_line)
                open("recent_messages.txt", "w").close()
                with open("recent_messages.txt", "a") as file:
                    for n_line in new_lines:
                        file.write(n_line)
            return yh_Lines

        if type == "NODE":
            if len(NODE_Lines) != 0:
                new_lines = []
                with open("recent_messages.txt", "r") as file:
                    file_lines = file.readlines()
                for f_line in file_lines:
                    f_line.split(" ")
                    if not NODE_Lines[0] in f_line:
                        if not f_line.strip("\n") == "":
                            new_lines.append(f_line)
                open("recent_messages.txt", "w").close()
                with open("recent_messages.txt", "a") as file:
                    for n_line in new_lines:
                        file.write(n_line)
            return NODE_Lines

        if type == "NREQ":
            if len(NREQ_Lines) != 0:
                new_lines = []
                with open("recent_messages.txt", "r+") as file:
                    file_lines = file.readlines()
                for f_line in file_lines:
                    f_line.split(" ")
                    if not NREQ_Lines[0] in f_line:
                        if not f_line.strip("\n") == "":
                            new_lines.append(f_line)
                open("recent_messages.txt", "w").close()
                with open("recent_messages.txt", "a") as file:
                    for n_line in new_lines:
                        file.write(n_line)
            return NREQ_Lines

        if type == "DEP":
            if len(DEP_Lines) != 0:
                new_lines = []
                with open("recent_messages.txt", "r") as file:
                    file_lines = file.readlines()
                for f_line in file_lines:
                    f_line.split(" ")
                    if not DEP_Lines[0] in f_line:
                        if not f_line.strip("\n") == "":
                            new_lines.append(f_line)
                open("recent_messages.txt", "w").close()
                with open("recent_messages.txt", "a") as file:
                    for n_line in new_lines:
                        file.write(n_line)
            return DEP_Lines





def send_to_all(message):
    """
    sends to all nodes
    """
    with open("./info/Nodes.pickle", "rb") as file:
        all_nodes = pickle.load(file)
    for node in all_nodes:
        print(message)
        print(node["ip"], node["port"])
        send(node["ip"], message, port=node["port"], send_all=True)

    
def announce(pub_key, port, version, num_gpus, benchmark, priv_key):
    announcement_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(announcement_time.encode()).hex())
    send_to_all(f'HELLO {str(time.time())} {pub_key} {port} {version} {num_gpus} {benchmark} {sig.hex()}')
    print("Announcement sent")
    return announcement_time

def update(pub_key, port, version, num_gpus, benchmark, priv_key):
    update_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(update_time.encode()).hex())
    send_to_all(f"UPDATE {update_time} {pub_key} {str(port)} {version} {num_gpus} {benchmark} {sig}")

def delete(pub_key, priv_key):
    update_time = str(time.time())
    if not isinstance(priv_key, bytes):
        priv_key = SigningKey.from_string(bytes.fromhex(priv_key), curve=SECP112r2)
    sig = str(priv_key.sign(update_time.encode()).hex())
    send_to_all(f"DELETE {update_time} {pub_key} {sig}")


def new_node(initiation_time, ip, pub_key, port, node_version, num_gpus, benchmark, sig):
    with open("info/Nodes.pickle", "rb") as file:
        nodes = pickle.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(pub_key), curve=SECP112r2)
    try:
        assert public_key.verify(bytes.fromhex(sig), str(initiation_time).encode())
        new_node = {"time": initiation_time, "ip": ip, "pub_key": pub_key, "port": port, "version": node_version,
                    "num_gpus": num_gpus, "benchmark": benchmark}
        for node in nodes:
            if node["pub_key"] == pub_key:
                return
            if node["ip"] == ip:
                return
        nodes.append(new_node)
        with open("info/Nodes.pickle", "wb") as file:
            pickle.dump(nodes, file)
    except Exception as e:
        print(e)
        return "node invalid"

def update_node(ip, update_time, pub_key, port, node_version,num_gpus,benchmark ,sig):
    with open("info/Nodes.pickle", "rb") as file:
        nodes = pickle.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(pub_key), curve=SECP112r2)
    try:
        assert public_key.verify(bytes.fromhex(sig), str(update_time).encode())
        for node in nodes:
            if node["ip"] == ip:
                node["pub_key"] = pub_key
                node["port"] = port
                node["version"] = node_version
                node["num_gpus"] = num_gpus
                node["benchmark"] = benchmark
        with open("info/Nodes.pickle", "wb") as file:
            pickle.dump(nodes, file)
            print("NODE UPDATED")
    except:
        return "update invalid"

def delete_node(deletion_time, ip, pub_key, sig):
    with open("info/Nodes.pickle", "rb") as file:
        nodes = pickle.load(file)
    public_key = VerifyingKey.from_string(bytes.fromhex(pub_key), curve=SECP112r2)
    try:
        assert public_key.verify(bytes.fromhex(sig), str(deletion_time).encode())
        for node in nodes:
            if node["ip"] == ip and node["pub_key"] == pub_key:
                del node
        with open("info/Nodes.pickle", "wb") as file:
            pickle.dump(nodes, file)
    except:
        return "cancel invalid"

def get_nodes():
    node = rand_act_node()
    send(node[1],"GET_NODES")
    while True:
        time.sleep(1)
        line = request_reader("NREQ")
        line = line.split(" ")
        nodes = line[2]
        nodes = ast.literal_eval(nodes)
        with open("./info/Nodes.pickle", "wb") as file:
            pickle.dump(nodes, file)

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
    with open("info/Nodes.pickle","wb") as file:
        pickle.dump(nodes, file)


def version(ver):
    send_to_all(f"VERSION {ver}")


def version_update(ip, ver):
    with open("./info/Nodes.pickle", "rb") as file:
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
