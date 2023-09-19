import datetime


class ServerBase:
    def __init__(self):
        pass

    def __del__(self):
        pass

    def _server_print(self, msg):
        class_name = self.__class__.__name__
        obj_id = id(self)
        time_stamp = datetime.datetime.now(datetime.timezone.utc)
        print(f"[{time_stamp}][{class_name}@{obj_id}] {msg}")
