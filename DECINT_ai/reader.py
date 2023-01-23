import node
import time
from requests import get#
import AI
from DECINT_ai import AI
import json
import textwrap
import os

def read(queue):
    print("---READER STARTED---")
    while True:
        # NODE_Lines = node.request_reader("NODE")
        if not queue.empty():
            # print(f"NODE LINES: {NODE_Lines}\n")
            message = queue.get()
            message = message.split(" ")

            if message[1] == "HELLO":
                node.new_node(float(message[2]), message[0], message[3], int(message[4]), float(message[5]), message[6],
                              message[7])

            elif message[1] == "UPDATE":
                node.update_node(message[0], float(message[2]), message[3], int(message[4]), float(message[5]),
                                 message[6])

            elif message[1] == "DELETE":
                node.delete_node(float(message[2]), message[0], message[3], message[4])

            elif message[1] == "ERROR":  # TODO add raise error with type
                print("ERROR")
                print(message[2])
                continue


            elif message[1] == "GET_NODES":
                with open(f"{os.path.dirname(__file__)}/info/nodes.json", "r") as file:
                    nodes = json.load(file)
                str_node = json.dumps(nodes).replace(" ", "")
                message_hash = node.message_hash("NREQ " + str_node)
                messages = textwrap.wrap("NREQ " + str_node, 5000)
                for message_ in messages[:-1]:
                    node.send(message[0], message_)
                node.send(message[0], messages[-1] + "END" + message_hash)

            elif message[1] == "AI":
                AI.AI_REQ(message)

            elif message[1] == "AI_DIST":
                AI.distributor.dist(message)

            else:
                pass



if __name__ == "__main__":
    read()

