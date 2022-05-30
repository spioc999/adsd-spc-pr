from threading import Lock
from constants import *
from enums.son_status import Status
from datetime import datetime




__tree = dict()
__treeLock = Lock()


def get_tree():
    """
    Get tree
    :return: a copy of the tree in order to avoid changing values outside of this manager
    """
    __treeLock.acquire()
    copy = __tree.copy()
    __treeLock.release()
    return copy


def get_father_id_of(node_id):
    father = None
    __treeLock.acquire()
    if node_id in __tree:
        father = __tree[node_id][FATHER]
    __treeLock.release()
    return father


def is_node_in_tree(node_id):
    __treeLock.acquire()
    is_present = node_id in __tree
    __treeLock.release()
    return is_present


def remove_father_from_node_if_present(node_id):
    father = None
    __treeLock.acquire()
    if node_id in __tree:
        father = __tree[node_id][FATHER]
        if father in __tree:
            del __tree[father][SONS][node_id]
            __tree[FATHER][IS_FULL] = len(__tree[FATHER][SONS]) >= TREE_BRANCH_SIZE
    __treeLock.release()
    return father


def is_full(node_id):
    full = True
    __treeLock.acquire()
    if node_id in __tree:
        full = __tree[node_id][IS_FULL]
    __treeLock.release()
    return full


def has_father(node_id):
    is_father_present = False
    __treeLock.acquire()
    if node_id in __tree and __tree[node_id][FATHER]:
        is_father_present = True
    __treeLock.release()
    return is_father_present


def add_son(father_id, son_id, unlimited_branch_size=False):
    __treeLock.acquire()
    if father_id in __tree:
        father = __tree[father_id]
        if unlimited_branch_size or not father[IS_FULL]:
            father[SONS][son_id] = dict()
            father[SONS][son_id][STATUS] = Status.PENDING
            father[SONS][son_id][TIME] = datetime.now()
        __treeLock.release()
    else:
        __treeLock.release()
        raise RuntimeError(f"Error adding son to node: {father_id}")



if __name__ == '__main__':
    __treeLock.acquire()
    __treeLock.release()

