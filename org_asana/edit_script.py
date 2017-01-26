if __name__ == "__main__" and __package__ is None:
    import os
    import sys
    sys.path.insert(0, os.path.abspath(".."))
__package__ = "org_asana"

import copy

from org_asana.node import Node, breadth_first_order

def lcs2(X, Y, equal):
    """
    apply the greedy lcs/ses algorithm between X and Y sequence
    (should be any Python's sequence)
    equal is a function to compare X and Y which must return 0 if
    X and Y are different, 1 if they are identical
    return a list of matched pairs in tuplesthe greedy lcs/ses algorithm
    """
    N, M = len(X), len(Y)
    if not X or not Y :
        return []
    max = N + M
    v = [0 for i in range(2*max+1)]
    common = [[] for i in range(2*max+1)]
    for D in range(max+1):
        for k in range(-D, D+1, 2):
            if k == -D or k != D and v[k-1] < v[k+1]:
                x = v[k+1]
                common[k] = common[k+1][:]
            else:
                x = v[k-1] + 1
                common[k] = common[k-1][:]

            y = x - k
            while x < N and y < M and equal(X[x], Y[y]):
                common[k].append((x, y))
                x += 1 ; y += 1

            v[k] = x
            if x >= N and y >= M:
                return [ (X[x],Y[y]) for x,y in common[k] ]

def edit_script(source_tree, target_tree,
                s_maps_to_t_p, s_equals_t_p, make_s_from_t,
                s_script_class=Node):
    """Generate an edit script to go from S_TREE to T_TREE.
    """
    if not hasattr(source_tree, 'root'):
        raise Exception("Source tree is not rooted.")
    if not hasattr(target_tree, 'root'):
        raise Exception("Target tree is not rooted.")
    s_tree = copy.deepcopy(source_tree)
    t_tree = copy.deepcopy(target_tree)

    # initialize mapping dictionaries
    s_from_t, t_from_s = {}, {}
    s_from_t[t_tree] = s_tree
    t_from_s[s_tree] = t_tree
    s_list = breadth_first_order(s_tree)
    t_list = breadth_first_order(t_tree)
    for s_node in s_list:
        for t_node in t_list:
            if s_maps_to_t_p(s_node, t_node):
                s_from_t[t_node] = s_node
                t_from_s[s_node] = t_node
                t_list.remove(t_node)
                break

    # define helper functions
    def mapped_nodes_p(s_node, t_node):
        return s_node is s_from_t.get(t_node)

    def s_pos_from_t(target_node):
        target_parent = target_node.parent
        target_index = target_parent.children.index(target_node)
        target_ordered_nodes = [t_node for t_node
                                in target_parent.children[:target_index]
                                if t_node.in_order]
        result = 0
        if target_ordered_nodes:
            if target_node is target_ordered_nodes[0]:
                result = 0
            else:
                source_node = s_from_t.get(target_ordered_nodes[-1])
                source_parent = source_node.parent
                source_ordered_nodes = [s_node
                                        for s_node
                                        in source_parent.children
                                        if s_node.in_order]
                source_ordered_index = source_ordered_nodes.index(
                    source_node)
                result = source_ordered_index + 1
        return result

    edit_sequence = []
    for t_node in breadth_first_order(t_tree):
        s_node = s_from_t.get(t_node)
        t_parent = t_node.parent
        s_parent = s_from_t.get(t_parent)
        # insert
        if not s_node:
            t_node.in_order = True
            s_position = s_pos_from_t(t_node)
            s_node = make_s_from_t(t_node)
            edit_sequence.append((s_script_class.insert_child,
                                  s_parent, s_position, s_node))
            s_from_t[t_node] = s_node
            t_from_s[s_node] = t_node
            s_parent.insert_child(s_position, s_node)
            s_node.in_order = True
        elif t_parent:
            s_node = s_from_t.get(t_node)
            s_parent = s_node.parent
            # update
            if not s_equals_t_p(s_node, t_node):
                model_s_node = make_s_from_t(t_node)
                edit_sequence.append((s_script_class.update,
                                      s_node, model_s_node))
                s_node.update(model_s_node)
            # move
            elif not mapped_nodes_p(s_parent, t_node.parent):
                t_node.in_order = True
                s_parent = s_from_t.get(t_node.parent)
                s_position = s_pos_from_t(t_node)
                edit_sequence.append((s_script_class.move_to,
                                      s_node, s_position, s_parent))
                s_node.move_to(s_position, s_parent)
                s_node.in_order = True
        # align
        s_list, t_list = [], []
        for s_child in s_node.children:
            s_child.in_order = False
            t_child = t_from_s.get(s_child)
            if t_child and t_child.parent is t_node:
                s_list.append(s_child)
        for t_child in t_node.children:
            t_child.in_order = False
            s_child = s_from_t.get(t_child)
            if s_child and s_child.parent is s_node:
                t_list.append(t_child)
        s = lcs2(s_list, t_list, mapped_nodes_p)
        for s_child, t_child in s:
            s_child.in_order = t_child.in_order = True
        for s_child in s_list:
            t_child = t_from_s.get(s_child)
            if (t_child not in t_list) or ((s_child, t_child) in s):
                continue
            s_position = s_pos_from_t(t_child)
            edit_sequence.append((s_script_class.move_to, s_child,
                                  s_position, s_node))
            s_child.move_to(s_position, s_node)
            s_child.in_order = t_child.in_order = True

    # delete
    s_list = breadth_first_order(s_tree)
    s_list.reverse()
    for s_node in s_list:
        if not t_from_s.get(s_node):
            edit_sequence.append((s_script_class.delete, s_node))
            s_node.delete()
    # results
    return edit_sequence