import docker

def environment_init():
    client = docker.from_env()
    