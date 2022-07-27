import node
import time
from requests import get#
import AI
import distributor

def read():
    time.sleep(5)
    print("reader started")
    ip = get('https://api.ipify.org').text
    while True:
        NODE_Lines = node.request_reader("NODE")
        for message in NODE_Lines:
            message = message.split(" ")
            try:
                node.message_handler(message)
            except Exception as e:
                node.send(message[0], f"ERROR {e}")
                print(message[1], e)
                continue

            if message[1] == "GET_NODES":
                node.send_node(message[0])
                print(message)

            elif message[1] == "HELLO":
                node.new_node(message[2], message[0], message[3])
                print(message)

            elif message[1] == "ONLINE?":
                node.send_node(message[0], "yh")
                print(message)

            elif message[1] == "AI":
                AI.AI_REQ(message)

            elif message[1] == "AI_DIST":
                distributor.dist(message)

            else:
                pass



if __name__ == "__main__":
    read()

