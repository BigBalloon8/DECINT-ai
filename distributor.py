import AI
import node
import pickle
import time
import random
import requests

def smart_node_picker(available_nodes, script):
    job_nodes = []
    AI.write_script(script)
    if "torch" in script:
        framework = "torch"
    elif "keras" in script and "tensorflow" in script:
        framework = "keras"
    elif "keras" not in script and "tensorflow" in script:
        framework = "tensorflow"
    else:
        raise
    import model
    epochs = model.EPOCHS
    if framework == "torch":
        num_parameters =  sum(p.numel() for p in model.model().parameters() if p.requires_grad)
    elif framework == "keras":
        num_parameters = model.model().count_params()
    elif framework == "tensorflow":
        num_parameters = 0
        for variable in model.model().trainable_variables():
            # shape is an array of tf.Dimension
            shape = variable.get_shape()
            print(shape)
            print(len(shape))
            variable_parameters = 1
            for dim in shape:
                print(dim)
                variable_parameters *= dim.value
            print(variable_parameters)
            num_parameters += variable_parameters
    else:
        return
    if num_parameters < 50000000:
        return
    if epochs < 25:
        return
    total_params = num_parameters*epochs
    scale_time_for_model = total_params/23719498 #num parameters in benchmark
    average_time = sum(float(x["benchmark"]) for x in available_nodes)/len(available_nodes)
    scale_time_for_model *= average_time
    for i in range(10):
        if scale_time_for_model > 1:
            node = random.choice(available_nodes)
            job_nodes.append(node)
            scale_time_for_model -= node["benchmark"]
            available_nodes.remove(node)
    open("model.py","w").close()
    return job_nodes

class AI_upload_error(Exception):
    pass

class Param_wrong_size(AI_upload_error):
    pass

class Import_error(AI_upload_error):
    pass

def error_handler():
    pass

def dist(message):
    #total_size = data_size*epochs
    with open("./info/Nodes.pickle", "rb") as file:
        nodes = pickle.load(file) #node attributes: time_init, IP,port, pub_key,version, num_gpus, benchmark_epoch_per_second
    node.send_to_all("ONLINE?")
    time.sleep(5)
    online_lines = node.request_reader("YH")
    available_nodes = []
    for line in online_lines:
        line = line.split(" ")
        for AI_node in nodes:
            if line[0] == AI_node["ip"]:
                available_nodes.append(AI_node)
                continue
    job_nodes = smart_node_picker(available_nodes, message[3])
    dep = node.request_reader("DEP", script_identity=message[2])#add method to not get wrong dep
    dep = dep.split(" ")

    for job_node in job_nodes:
        node.send(job_node["ip"], f"AI {message[2]} {message[0]} {str(job_nodes).replace(' ','')} {message[3]}")
        node.send(job_node["ip"], f"DEP {dep[2]} {dep[3]}")

    dist_node = requests.get()
    
    node.send(dist_node["ip"],f"DIST AI_JOB_ANNOUNCE {time.time()} {str(job_nodes)} {message[2]}")



