import networkx as _nx
import environ as _environ
from pathlib import Path as _Path
# (corona/config/settings.py - 2 = corona/)
ROOT_DIR = (_environ.Path(__file__) - 2)

# load bot token from .env
path = _Path(ROOT_DIR) / 'graph/questions.gexf'

_G = _nx.readwrite.read_gexf(path)


def get_next_question(node_id):
    try:
        return _G.nodes[node_id]["label"]
    except KeyError:
        return False


def get_multichoice(node_id):
    return True if "multichoice" in _G.nodes[node_id] else False


def get_next_answer(node_id):
    return _G[node_id]
