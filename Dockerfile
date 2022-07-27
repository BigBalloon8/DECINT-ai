FROM nvidia/cuda:11.6.0-runtime-ubuntu20.04

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get -y install software-properties-common

ADD . .

RUN apt-get -y install python3 python3-pip

CMD pip3 --no-input install --upgrade tensorflow-gpu torch torchvision torchaudio numpy ecdsa pillow opencv-python
CMD python3 boot.py