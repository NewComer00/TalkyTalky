import os
import sys
from multiprocessing import Process


# self-defined modules to be added to PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_root, 'backends/')
sys.path.append(backend_path)
from backends.action_server import ActionServer
from backends.language_model_server import LanguageModelServer
from backends.speech2text_server import Speech2TextServer
# end of self-defined module list

def run_action_server():
    acts = ActionServer()
    acts.connect()
    acts.run()

def run_language_server():
    lms = LanguageModelServer()
    lms.connect()
    lms.run()

def run_speech2text_server():
    s2ts = Speech2TextServer()
    s2ts.connect()
    s2ts.run()

if __name__ == "__main__":

    p1 = Process(target=run_action_server)
    p1.daemon=True
    p1.start()

    p2 = Process(target=run_language_server)
    p2.daemon=True
    p2.start()

    p3 = Process(target=run_speech2text_server)
    p3.daemon=True
    p3.start()

    while True:
        pass
    # import main
    # main.main()
