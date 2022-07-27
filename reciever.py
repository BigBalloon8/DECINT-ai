import node


def rec(my_ip):
    while True:
        message,address = node.receive(my_ip)

        print(message)
        print(address)

        with open("recent_messages.txt", "a") as file:
            if " ".join(message) != " " or " ".join(message) != "":
                file.write("\n" + address[0] + " " + " ".join(message))

if __name__ == "__main__":
    rec("127.0.0.1")
