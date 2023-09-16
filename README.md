# TalkyTalky
A simple offline chatbot running on your computer using [Faster Whisper](https://github.com/guillaumekln/faster-whisper) and [GPT4All](https://github.com/nomic-ai/gpt4all). 

## Prerequisite
- A normal computer
- Windows or Unix-like OS
- Python 3.8 or newer
- Internet access during the installation and the first run

## Installation
It is recommended to run this Python3 program in a virtual environment, so let's install the `virtualenv` package first
```sh
pip install virtualenv
```

Clone this repository and make a virtual environment for it
```sh
git clone https://github.com/NewComer00/TalkyTalky
cd TalkyTalky
virtualenv .
```

Activate the virtual environment
```sh
# for windows
.\Scripts\activate

# for linux
source bin/activate
```

Install the required Python packages
```sh
pip install -r requirements.txt
```

## Usage
First, please open **two different terminals**, and ensure that the virtual environment has been **activated** in both of them.

In one of the terminal, start the GPT4All backend. If it's the first time the backend is started, it will automatically start to download the offline chatting model.
```sh
python backend_gpt4all.py
```

After the GPT4All backend is started, switch to the other terminal and launch the main script. If it's the first time the main script is started, it will automatically start to download the offline speech-to-text model.
```sh
python main.py
```

**Hold the SPACE KEY** to say whatever you want, and **release the SPACE KEY** after you finished. Enjoy the chatting!
