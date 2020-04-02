import json
import environ as _environ
from pathlib import Path as _Path
# (corona/config/settings.py - 2 = corona/)
ROOT_DIR = (_environ.Path(__file__) - 2)

# get the actual file path
path = _Path(ROOT_DIR) / 'Questions'


class Questions:

    def __init__(self):
        self.languages = {}
        self.reload_strings()

    def reload_strings(self):
        for filename in path:
            if filename.endswitch(".json"):
                language = filename[:-5]
                self.languages[language] = json.load(open(path + filename))

    def get_question(self, language, question_id):
        return self.languages[language][question_id]
