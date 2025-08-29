# backend/ds_plugins.py (Version 4 - Final, Context-Aware)
from collections import deque
from typing import Dict, Any, List, Set, Optional

# --- Dummy classes are now ONLY for type hinting, they are never used by logic ---
class ListNode: pass
class TreeNode: pass
class BinarySearchTree: pass
class Graph: pass
class Stack: pass
class Queue: pass

# --- HELPER FUNCTIONS NOW ACCEPT A `context` ARGUMENT ---

def ll_create(items: List[int], context: dict) -> Optional[ListNode]:
    ListNodeClass = context['ListNode'] # Get the REAL class from the context
    if not items: return None
    head = ListNodeClass(val=items[0])
    curr = head
    for val in items[1:]:
        curr.next = ListNodeClass(val=val)
        curr = curr.next
    return head

def ll_serialize(head: Optional[ListNode], context: dict) -> List[int]:
    items = []; curr = head
    while curr:
        items.append(curr.val)
        curr = curr.next
    return items

def tree_create(items: List[Optional[int]], context: dict) -> Optional[TreeNode]:
    TreeNodeClass = context['TreeNode']
    # ... (similar logic for all other helpers)
    if not items or items[0] is None: return None
    root = TreeNodeClass(val=items[0])
    q = deque([root])
    i = 1
    while q and i < len(items):
        node = q.popleft()
        if i < len(items) and items[i] is not None:
            node.left = TreeNodeClass(val=items[i]); q.append(node.left)
        i += 1
        if i < len(items) and items[i] is not None:
            node.right = TreeNodeClass(val=items[i]); q.append(node.right)
        i += 1
    return root
    
def tree_serialize(root: Optional[TreeNode], context: dict) -> List[Optional[int]]:
    if not root: return []
    res, q = [], deque([root])
    while q:
        node = q.popleft()
        if node: res.append(node.val); q.append(node.left); q.append(node.right)
        else: res.append(None)
    while res and res[-1] is None: res.pop()
    return res

GraphRepr = Dict[str, Set[Any]]
def graph_create(data: GraphRepr, context: dict) -> 'Graph':
    GraphClass = context['Graph']
    g = GraphClass()
    for v in data.get('V', set()): g.add_vertex(v)
    for u, v_ in data.get('E', set()): g.add_edge(u, v_)
    return g
def graph_serialize(g: 'Graph', context: dict) -> GraphRepr:
    edges = set()
    for u, neighbors in g.adj.items():
        for v in neighbors: edges.add((u, v))
    return {'V': set(g.adj.keys()), 'E': edges}

def stack_create(items: List[int], context: dict) -> 'Stack':
    StackClass = context['Stack']
    s = StackClass()
    for i in items: s.push(i)
    return s
def stack_serialize(s: 'Stack', context: dict) -> List[int]:
    return getattr(s, 'items', [])

def queue_create(items: List[int], context: dict) -> 'Queue':
    QueueClass = context['Queue']
    q = QueueClass()
    for i in items: q.enqueue(i)
    return q
def queue_serialize(q: 'Queue', context: dict) -> List[int]:
    return list(getattr(q, 'items', []))

# --- Plugin Registries (Unchanged) ---
INPUT_STRATEGIES = { 'ListNode': lambda: [[1, 2, 3], [5], []], 'list': lambda: [[1, 1, 2, 3, 3], [], [5]], 'Stack': lambda: [[1, 2], []], 'Queue': lambda: [[10, 20], []], 'BinarySearchTree': lambda: [[10, 5, 15, 12, 20], []], 'Graph': lambda: [{'V': {'A', 'B', 'C'}, 'E': {('A', 'B'), ('B', 'C')}}, {'V': set(), 'E': set()}], 'int': lambda: [3, 99], }
INPUT_CONVERTERS = { 'ListNode': ll_create, 'list': lambda x, ctx: x[:], 'Stack': stack_create, 'Queue': queue_create, 'BinarySearchTree': lambda items, ctx: (bst := ctx['BinarySearchTree'](), [bst.insert(i) for i in items], bst)[-1], 'Graph': graph_create, 'int': lambda x, ctx: x, }
STATE_SERIALIZERS = { 'ListNode': ll_serialize, 'list': lambda x, ctx: x, 'Stack': stack_serialize, 'Queue': queue_serialize, 'BinarySearchTree': lambda bst, ctx: tree_serialize(bst.root, ctx), 'Graph': graph_serialize, 'int': lambda x, ctx: x, }