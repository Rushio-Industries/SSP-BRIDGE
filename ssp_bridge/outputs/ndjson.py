import json

class NdjsonWriter:
    def __init__(self, path):
        self.f = open(path, "a", encoding="utf-8")

    def write(self, frame: dict):
        self.f.write(json.dumps(frame, ensure_ascii=False) + "\n")
        self.f.flush()

    def close(self):
        self.f.close()
