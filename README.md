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
First, please ensure that the virtual environment has been **activated**.

Start the App. If it's the first time you launch the App, it will automatically start to download the offline models.
```sh
python app.py
```

Show help message
```sh
python app.py --help
```

Launch the App in TUI mode without displaying the servers' log; use [edge-tts](https://pypi.org/project/edge-tts/) Microsoft Edge's online text-to-speech service
```sh
python app.py --tui --noecho-server-log --tts.engine edge-tts
```
