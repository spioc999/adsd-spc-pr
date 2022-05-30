from threading import Lock
from constants import *
from enums.son_status import Status
from datetime import datetime


__tree = dict()
__treeLock = Lock()
__last_broker = 0


def get_tree() -> dict:
    """
    Get tree
    :return: a copy of the tree in order to avoid changing values outside of this manager
    """
    __treeLock.acquire()
    copy = __tree.copy()
    __treeLock.release()
    return copy


def get_father_id_of(node_id) -> str:
    __treeLock.acquire()
    if node_id in __tree:
        father_id = __tree[node_id][FATHER]
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found", 404)
    __treeLock.release()
    return father_id


def is_node_in_tree(node_id) -> bool:
    __treeLock.acquire()
    is_present = node_id in __tree
    __treeLock.release()
    return is_present


def is_son_of(father_id, son_id) -> bool:
    __treeLock.acquire()
    is_son = father_id in __tree and son_id in __tree[father_id][SONS]
    __treeLock.release()
    return is_son


def is_father_for_node(node_id, father_id) -> bool:
    __treeLock.acquire()
    if node_id in __tree:
        is_father = __tree[node_id][FATHER] == father_id
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found", 404)
    __treeLock.release()
    return is_father


def get_node_status(father_id, node_id) -> Status:
    __treeLock.acquire()
    if father_id in __tree and node_id in __tree[father_id][SONS]:
        status = __tree[father_id][SONS][node_id][STATUS]
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {father_id} not found or son with id: {node_id} not found", 404)
    __treeLock.release()
    return status


def remove_node_from_father_if_present(node_id) -> str:
    __treeLock.acquire()
    if node_id in __tree:
        father_id = __tree[node_id][FATHER]
        if father_id in __tree:
            del __tree[father_id][SONS][node_id]
            __tree[father_id][IS_FULL] = len(__tree[father_id][SONS]) >= TREE_BRANCH_SIZE
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found", 404)
    __treeLock.release()
    return father_id


def is_full(node_id) -> bool:
    __treeLock.acquire()
    if node_id in __tree:
        full = __tree[node_id][IS_FULL]
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found", 404)
    __treeLock.release()
    return full


def has_father(node_id) -> bool:
    __treeLock.acquire()
    if node_id in __tree:
        is_father_present = __tree[node_id][FATHER] is not None
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found", 404)
    __treeLock.release()
    return is_father_present


def add_son(father_id, son_id, unlimited_branch_size=False) -> None:
    __treeLock.acquire()
    if father_id in __tree:
        father = __tree[father_id]
        if unlimited_branch_size or not father[IS_FULL]:
            father[SONS][son_id] = dict()
            father[SONS][son_id][STATUS] = Status.PENDING
            father[SONS][son_id][TIME] = datetime.now()
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {father_id} not found", 404)
    __treeLock.release()


def confirm_son_and_add_as_node(father_id, son_id) -> None:
    __treeLock.acquire()
    if father_id in __tree and son_id in __tree[father_id][SONS]:
        son = __tree[father_id][SONS]
        son[STATUS] = Status.CONFIRMED
        son[TIME] = datetime.now()
        if son_id in __tree:
            __tree[son_id][FATHER] = father_id
        else:
            __tree.update(create_node(son_id, father_id))
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {father_id} not found or son with id: {son_id} not found", 404)
    __treeLock.release()


def remove_sons_if_needed(node_id) -> None:
    confirmed_sons = dict()
    __treeLock.acquire()
    if node_id in __tree:
        sons = __tree[node_id][SONS]
        for son in sons:
            if sons[son][STATUS] == Status.CONFIRMED:
                confirmed_sons[son] = sons[son]

        if len(confirmed_sons) > TREE_BRANCH_SIZE:
            __treeLock.release()
            raise RuntimeError("Too much sons for node", 403)  # forbidden

        if len(confirmed_sons) == TREE_BRANCH_SIZE:
            __tree[FATHER][SONS] = confirmed_sons
            __tree[FATHER][IS_FULL] = True
            print(f"Dropping exceeded sons for node {node_id}")
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found", 404)
    __treeLock.release()


def remove_son(node_id, son_id) -> None:
    __treeLock.acquire()
    if node_id in __tree:
        if son_id in __tree[node_id][SONS]:
            del __tree[node_id][SONS][son_id]
            __tree[node_id][IS_FULL] = len(__tree[node_id][SONS]) >= TREE_BRANCH_SIZE
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found.", 404)
    __treeLock.release()


def remove_father(node_id) -> None:
    __treeLock.acquire()
    if node_id in __tree:
        __tree[node_id][FATHER] = None
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found.", 404)
    __treeLock.release()


def remove_node(node_id) -> None:
    __treeLock.acquire()
    if node_id in __tree:
        del __tree[node_id]
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found.", 404)
    __treeLock.release()


def is_alone(node_id) -> bool:
    __treeLock.acquire()
    if node_id in __tree:
        alone = __tree[node_id][FATHER] is None and len(__tree[node_id][SONS]) == 0
    else:
        __treeLock.release()
        raise RuntimeError(f"Node with id: {node_id} not found.", 404)
    __treeLock.release()
    return alone


def create_node(node_id, father_id) -> dict:
    return {
            node_id: {
                FATHER: father_id,
                SONS: dict(),
                IS_FULL: False
            }
        }

