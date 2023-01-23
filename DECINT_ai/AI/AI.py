import ast
import node
import os
import json
import zipfile
import magic
#  import TF_kung_fu
#  import keras_kung_fu
import re


class DECIError(Exception):
    pass


class LibraryError(DECIError):
    """This Exception is raised when an invalid library is used"""
    pass


class OpenError(DECIError):
    """This Exception is raised when the script is trying to open a file it is not aloud to"""


class ScriptError(DECIError):
    """This Exception is raised when invalid function are trying to be used"""
    pass


class DependencyError(DECIError):
    """This Exception is raised when there is an issue with the dependencies"""
    pass


def write_script(script):
    open("model.py", "w").close()
    with open("model.py", "w") as file:
        file.read(script.replace("`", " "))


def write_dependencies(string):
    with open("depen.zip", "wb") as file:
        file.write(bytes(string))

    with zipfile.ZipFile("depen.zip", 'r') as zip_ref:
        zip_ref.extractall("./data/")


def no_read(lines):
    no_virus = True

    lines = lines.replace('\n', '')

    linux = ["/bin", "/boot", "/cdrom", "/dev", "/etc", "/home", "/lib", "/lost+found", "/media", "/mnt", "/opt",
             "/proc", "/root", "/run", "/sbin", "/selinux", "/srv", "/tmp", "/usr", "/var"]

    aloud = ["'r'", "'rb'", '"r"', '"rb"']
    for line in lines:
        line = line.lower()
        if "open" in line:
            if line.count(",") > 1:
                raise OpenError("There are multiple ',' in the open line")
            info = re.findall(r'\(.*?\)', line)[0]
            info = info.replace("(", "").replace(")", "").split(",")
            if "+" in info:
                raise OpenError("+ was found in open")

            if info[1] not in aloud:  # if second val in open("lol.txt","wb")
                raise OpenError("mode is invalid (No writing to files)")
                break

        banned_phrases = [
            "c:", "..", "raise", "compile", "eval", "exec",  # c: doesnt matter as
            "__import__", "cimport", "cdef", "cpdef", "cython", "load_op_library"  # stop malicious files being used
            "cpp_extension",
        ]
        for phrase in banned_phrases:
            if phrase in line:
                raise ScriptError(f"your not allowed to use the phrase {phrase}")

        for directory in linux:
            if directory in line:
                raise ScriptError("You are not allowed to access base directories")



def please_no_hack():
    libraries = [
        "tensorflow",
        "torch",
        "torchvision",
        "torchaudio",
        "keras",
        "glob",
        "cv2",
        "numpy",
        "time",
        "PIL",
        "pandas",
        "scipy",
        "jax"
    ]

    with open("../model.py", "r") as file:
        lines = file.readlines()
        no_read(lines)
        virus = False
        framework = ""
        for line in lines:
            if "import" in line:
                if "#" in line or "'" in line or '"' in line or "," in line:
                    raise LibraryError("no comments aloud in import line or multiple functions "
                                       "(from tensorflow.keras import layers, regularizers)")
                for library in libraries:
                    if library in line:
                        if "as" in line:
                            if library in line.split("as")[1]:
                                raise LibraryError("Library cannot be used as import name "
                                                   "(import os as numpy)")

                        if "from" in line:
                            if not library in line.split("import")[0]:
                                raise LibraryError("import invalid "
                                                   "(from os import pytorch)")

                        if not library in line.split(".")[0]:
                            raise LibraryError("import invalid "
                                               "(import os.time)")

                    if library in line:
                        if library == "tensorflow":
                            virus = False
                            framework = "tensorflow"
                        if library == "torch":
                            virus = False
                            framework = "torch"
                    else:
                        raise LibraryError("Invalid Import make sure to use only supported packages")

    return virus, framework


def file_please_no_hack():
    file_endings = [
        ".csv",  # CSV text
        ".json",  # JSON data
        ".txt",  # UTF-8 Unicode (with BOM) text, ASCII text
        ".h5", ".hdf5",  # Hierarchical Data Format (version 5) data
        ".jpg", ".jpeg", ".jpe",  # JPEG image data
        ".png",  # PNG image data
        ".npy",  # NumPy array
        ".xml",  # XML 1.0 document
        ".mp3",  # MPEG ADTS, layer III
        ".wav"  # RIFF (little-endian) data, WAVE audio
        ".mp4",  # ISO Media, MP4 Base Media
        ".mov",  # ISO Media, Apple QuickTime movie, Apple QuickTime
    ]
    magic_file_type = [
        "CSV text",
        "JSON data",
        "UTF-8 Unicode (with BOM) text", "ASCII text",
        "Hierarchical Data Format (version 5) data",
        "JPEG image data",
        "PNG image data",
        "NumPy array",
        "XML 1.0 document",
        "MPEG ADTS, layer III",
        "RIFF (little-endian) data, WAVE audio",
        "ISO Media, MP4 Base Media",
        "ISO Media, Apple QuickTime movie, Apple QuickTime"
    ]
    data_files = []
    for path, subdirs, files in os.walk("../info/"):
        for name in files:
            data_files.append(os.path.join(path, name))

    for file in data_files:
        file_format = magic.from_file(f"./data/{file[2:]}")
        for file_type in magic_file_type:
            if file_format in file_type:
                file_ending = os.path.splitext()[-1]
                if file_ending == file_endings[magic_file_type.index(file_type)]:
                    break
                else:
                    raise DependencyError("File is not stated format")
        else:
            raise DependencyError("File type is not allowed")


def tf_config(nodes, index):
    tf_config = {
        "cluster": {
            "worker": nodes
        },
        "task": {"type": "worker", "index": index}
    }
    os.environ['TF_CONFIG'] = json.dumps(tf_config)


def AI_REQ(message):
    """
    values in message are deleted to leave only the lines in the script
    """
    ip = message[0]

    script_identity = message[2]
    origin_ip = message[3]
    nodes = ast.literal_eval(message[4])

    write_script(message[5])
    dependencies = node.request_reader("DEP", script_identity=message[2])
    print("d: ", dependencies)
    dependencies = dependencies[0].split(" ")
    dep_identity = dependencies[2]

    if dep_identity == script_identity:
        print([dependencies[3]])
        if len(dependencies[3]) % 2 != 0:
            print(str(type(len(dependencies[3]) / 2)))
            write_dependencies(bytes.fromhex("0" + dependencies[
                3]))  # https://stackoverflow.com/questions/56742408/valueerror-non-hexadecimal-number-found-in-fromhex-arg-at-position/56742540

        else:
            print(str(type(len(dependencies[3]) / 2)))
            write_dependencies(bytes.fromhex(str(dependencies[3])))
    try:
        virus, framework = please_no_hack()
        file_please_no_hack()
    except Exception as e:
        if isinstance(e, LibraryError) or isinstance(e, DependencyError):
            node.send(ip, f"Error {str(e)}")
        return
    if not virus:
        import model
        node_str = ""
        for AI_node in nodes:
            node_str.append(f"{AI_node['ip']}:{AI_node['num_gpus']},")
        total_gpus = sum(x["num_gpus"] for x in nodes)

        if framework == "tensorflow":
            if model.METHOD == "HOROVOD":
                os.system(f"horovodrun -np {total_gpus} -H {node_str} python3 TF_horovod.py")
            elif model.METHOD == "KUNGFU":
                os.system(f"kungfu-run -np {total_gpus} -H {node_str} python TF_kung_fu.py")

        if framework == "keras":
            if model.METHOD == "HOROVOD":
                os.system(f"horovodrun -np {total_gpus} -H {node_str} python3 keras_horovod.py")
            elif model.METHOD == "KUNGFU":
                os.system(f"kungfu-run -np {total_gpus} -H {node_str} python keras_kung_fu.py")

        if framework == "torch":
            os.system(f"horovodrun -np {total_gpus} -H {node_str} python3 Torch_run.py")
