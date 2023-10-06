import pytest
from pokie_container.constants import (
    SVC_CONTAINER,
    TREE_DEFAULT,
    TENANT_DEFAULT,
    NODE_DEFAULT,
)
from pokie_container.dto import TreeTypeRecord, NodeTypeRecord, NodeRecord
from pokie_container.service import ContainerService


@pytest.fixture
def svc_container(pokie_service_manager) -> ContainerService:
    return pokie_service_manager.get(SVC_CONTAINER)  # type: ContainerService


class TestPlatform:
    def test_tree_type(self, svc_container):
        records = svc_container.get_tree_type_list()
        assert len(records) == 1
        assert isinstance(records[0], TreeTypeRecord)

        # add a new tree type
        id_type = 100
        label = "my custom tree type"
        record = svc_container.add_tree_type(id_type, label)
        assert record is not None
        assert isinstance(record, TreeTypeRecord)

        records = svc_container.get_tree_type_list()
        assert len(records) == 2
        new_record = records[1]
        assert new_record.id == id_type
        assert new_record.label == label

    def test_node_type(self, svc_container):
        records = svc_container.get_node_type_list(TREE_DEFAULT)
        assert len(records) == 1
        assert isinstance(records[0], NodeTypeRecord) is True

        # add a custom node type
        id_type = 10
        label = "my custom node type"

        node_type = svc_container.add_node_type(TREE_DEFAULT, id_type, label)
        assert node_type is not None
        assert isinstance(node_type, NodeTypeRecord) is True

        records = svc_container.get_node_type_list(TREE_DEFAULT)
        assert len(records) == 2
        assert isinstance(records[0], NodeTypeRecord) is True

        node = records[0]
        assert node.id == id_type
        assert node.label == label

        result = svc_container.remove_node_type(id_type)
        assert result is True
        records = svc_container.get_node_type_list(TREE_DEFAULT)
        assert len(records) == 1

        # remove non-existing type
        result = svc_container.remove_node_type(id_type)
        assert result is False

    def test_node(self, svc_container: ContainerService):
        # custom node type
        id_node_type = 10
        node_type_label = "custom type"
        record = svc_container.add_node_type(
            TREE_DEFAULT, id_node_type, node_type_label
        )
        assert record is not None

        # create 10 nodes at root level, 5 nodes at second level
        nodes = {}
        for i in range(0, 10):
            record = svc_container.add_node(
                0, id_node_type, "root node {}".format(str(i))
            )
            nodes[record.id] = []
            for j in range(0, 2):
                child = svc_container.add_node(
                    0,
                    id_node_type,
                    "child node {} for node {}".format(str(j), str(i)),
                    id_parents=record.id,
                )
                nodes[record.id].append(child.id)

        for parent, children in nodes.items():
            record = svc_container.get_node(parent)
            node_record = svc_container.get_node_record(parent)
            assert isinstance(node_record, NodeRecord)
            assert node_record.id == parent

            # validate response
            for key in ["record", "parents", "children"]:
                assert key in record.keys()

            assert len(record["parents"]) == 0
            assert len(record["children"]) == 2
            for id_child in record["children"]:
                child = svc_container.get_node(id_child)
                # validate response
                for key in ["record", "parents", "children"]:
                    assert key in child.keys()

                assert len(child["parents"]) == 1
                assert child["parents"][0] == record["record"].id
                assert len(child["children"]) == 0

    def test_node_tree_multilevel(self, svc_container: ContainerService):
        # custom node type
        id_node_type = 10
        node_type_label = "custom type"
        record = svc_container.add_node_type(
            TREE_DEFAULT, id_node_type, node_type_label
        )
        assert record is not None

        # create a tree
        #       A
        #      / \
        #     B   C
        #    / \
        #   D   E
        node_a = svc_container.add_node(0, id_node_type, "node A")
        node_b = svc_container.add_node(0, id_node_type, "node B", id_parents=node_a.id)
        node_c = svc_container.add_node(0, id_node_type, "node C", id_parents=node_a.id)
        node_d = svc_container.add_node(0, id_node_type, "node D", id_parents=node_b.id)
        node_e = svc_container.add_node(0, id_node_type, "node E", id_parents=node_b.id)

        # validate node A
        read_a = svc_container.get_node(node_a.id)
        assert read_a["record"].label == "node A"
        assert len(read_a["parents"]) == 0
        assert len(read_a["children"]) == 2
        for node in [node_b, node_c]:
            assert node.id in read_a["children"]

        # validate node B
        read_b = svc_container.get_node(node_b.id)
        assert read_b["record"].label == "node B"
        assert len(read_b["parents"]) == 1
        assert read_b["parents"][0] == node_a.id
        assert len(read_b["children"]) == 2
        for node in [node_d, node_e]:
            assert node.id in read_b["children"]

        # validate node C
        read_c = svc_container.get_node(node_c.id)
        assert read_c["record"].label == "node C"
        assert len(read_c["parents"]) == 1
        assert read_c["parents"][0] == node_a.id
        assert len(read_c["children"]) == 0

        # validate node D
        read_d = svc_container.get_node(node_d.id)
        assert read_d["record"].label == "node D"
        assert len(read_d["parents"]) == 1
        assert read_d["parents"][0] == node_b.id
        assert len(read_d["children"]) == 0

        # validate node E
        read_e = svc_container.get_node(node_e.id)
        assert read_e["record"].label == "node E"
        assert len(read_e["parents"]) == 1
        assert read_e["parents"][0] == node_b.id
        assert len(read_e["children"]) == 0

        # extend the tree
        #     B
        #    / \
        #   D   E
        #    \ /
        #     F
        node_f = svc_container.add_node(
            0, id_node_type, "node F", id_parents=[node_d.id, node_e.id]
        )

        # validate node F
        read_f = svc_container.get_node(node_f.id)
        assert read_f["record"].label == "node F"
        assert len(read_f["parents"]) == 2
        for node in [node_d, node_e]:
            assert node.id in read_f["parents"]
        assert len(read_f["children"]) == 0

        # re-validate node E
        read_e = svc_container.get_node(node_e.id)
        assert read_e["record"].label == "node E"
        assert len(read_e["parents"]) == 1
        assert read_e["parents"][0] == node_b.id
        assert len(read_e["children"]) == 1
        assert read_e["children"][0] == node_f.id

    def test_node_tree_children_parent(self, svc_container: ContainerService):
        # create a tree
        #       A
        #      / \
        #     B   C
        #    / \
        #   D   E
        node_a = svc_container.add_node(0, NODE_DEFAULT, "node A")
        node_b = svc_container.add_node(0, NODE_DEFAULT, "node B", id_parents=node_a.id)
        node_c = svc_container.add_node(0, NODE_DEFAULT, "node C", id_parents=node_a.id)
        node_d = svc_container.add_node(0, NODE_DEFAULT, "node D", id_parents=node_b.id)
        node_e = svc_container.add_node(0, NODE_DEFAULT, "node E", id_parents=node_b.id)

        # check children
        children = svc_container.get_all_node_children_id(0, TREE_DEFAULT, node_b.id)
        assert len(children) == 2
        for i in [node_d.id, node_e.id]:
            assert i in children

        # check immediate children
        children = svc_container.get_children_id(0, TREE_DEFAULT, node_a.id)
        assert len(children) == 2
        for i in [node_b.id, node_c.id]:
            assert i in children

        # check parent
        parent = svc_container.get_all_node_parents_id(0, TREE_DEFAULT, node_e.id)
        assert len(parent) == 2
        for i in [node_a.id, node_b.id]:
            assert i in parent

        # check immediate parent
        parent = svc_container.get_parents_id(0, TREE_DEFAULT, node_e.id)
        assert len(parent) == 1
        for i in [node_b.id]:
            assert i in parent

        # check subtree
        parent = svc_container.get_node_subtree_id(0, TREE_DEFAULT, node_b.id)
        assert len(parent) == 3
        for i in [node_a.id, node_d.id, node_e.id]:
            assert i in parent

    def test_node_tree_multi_tree(self, svc_container: ContainerService):
        tree_1 = 10
        svc_container.add_tree_type(tree_1, "tree type 1")
        tree_2 = 20
        svc_container.add_tree_type(tree_2, "tree type 2")

        # custom node types
        tree1_id_node_type = 10
        tree1_node_type_label = "custom type for tree1"
        record = svc_container.add_node_type(
            tree_1, tree1_id_node_type, tree1_node_type_label
        )
        assert record is not None

        tree2_id_node_type = 11
        tree2_node_type_label = "custom type for tree2"
        record = svc_container.add_node_type(
            tree_2, tree2_id_node_type, tree2_node_type_label
        )
        assert record is not None

        # create first tree
        #       A
        #      / \
        #     B   C
        node_a1 = svc_container.add_node(0, tree1_id_node_type, "node A1")
        node_b1 = svc_container.add_node(
            0, tree1_id_node_type, "node B1", id_parents=node_a1.id
        )
        node_c1 = svc_container.add_node(
            0, tree1_id_node_type, "node C1", id_parents=node_a1.id
        )

        # create second tree
        #       A
        #      / \
        #     B   C
        node_a2 = svc_container.add_node(0, tree2_id_node_type, "node A2")
        node_b2 = svc_container.add_node(
            0, tree2_id_node_type, "node B2", id_parents=node_a2.id
        )
        node_c2 = svc_container.add_node(
            0, tree2_id_node_type, "node C2", id_parents=node_a2.id
        )

        # verify tree 1
        tree1 = svc_container.get_node_tree(0, tree_1)
        assert len(tree1) == 3
        for tid in [node_a1.id, node_b1.id, node_c1.id]:
            assert tid in tree1.keys()
        for tid in [node_a2.id, node_b2.id, node_c2.id]:
            assert tid not in tree1.keys()

        # verify tree 1 with records
        tree1 = svc_container.get_node_tree(0, tree_1, True)
        assert len(tree1) == 3
        tree1_ids = [k.id for k in tree1.keys()]
        for tid in [node_a1.id, node_b1.id, node_c1.id]:
            assert tid in tree1_ids
        for tid in [node_a2.id, node_b2.id, node_c2.id]:
            assert tid not in tree1_ids

        # verify tree 2
        tree2 = svc_container.get_node_tree(0, tree_2)
        assert len(tree2) == 3
        for tid in [node_a2.id, node_b2.id, node_c2.id]:
            assert tid in tree2.keys()
        for tid in [node_a1.id, node_b1.id, node_c1.id]:
            assert tid not in tree2.keys()

    def test_node_parent(self, svc_container: ContainerService):
        tree_1 = 10
        svc_container.add_tree_type(tree_1, "tree type 1")
        id_tree_2 = 20
        svc_container.add_tree_type(id_tree_2, "tree type 2")

        # custom node types
        tree1_id_node_type = 100
        tree1_node_type_label = "custom type for tree1"
        record = svc_container.add_node_type(
            tree_1, tree1_id_node_type, tree1_node_type_label
        )
        assert record is not None

        tree2_id_node_type = 110
        tree2_node_type_label = "custom type for tree2"
        record = svc_container.add_node_type(
            id_tree_2, tree2_id_node_type, tree2_node_type_label
        )
        assert record is not None

        # create first tree; used as fixture for multi-tree operation
        #       A  D
        #      / \
        #     B   C
        node_a1 = svc_container.add_node(0, tree1_id_node_type, "node A1")
        node_b1 = svc_container.add_node(
            0, tree1_id_node_type, "node B1", id_parents=node_a1.id
        )
        node_c1 = svc_container.add_node(
            0, tree1_id_node_type, "node C1", id_parents=node_a1.id
        )
        node_d1 = svc_container.add_node(0, tree1_id_node_type, "node D1")

        # create second tree
        #       A   D
        #      / \
        #     B   C
        node_a2 = svc_container.add_node(0, tree2_id_node_type, "node A2")
        node_b2 = svc_container.add_node(
            0, tree2_id_node_type, "node B2", id_parents=node_a2.id
        )
        node_c2 = svc_container.add_node(
            0, tree2_id_node_type, "node C2", id_parents=node_a2.id
        )
        node_d2 = svc_container.add_node(0, tree2_id_node_type, "node D2")

        # tree 2 parent manipulation
        # initial state: get node info
        node = svc_container.get_node(node_d2.id)
        assert isinstance(node, dict)
        assert isinstance(node["record"], NodeRecord)
        assert len(node["parents"]) == 0
        assert len(node["children"]) == 0

        # attempt to move node D to child of A
        # should fail, because they are on different levels
        result = svc_container.add_node_parent(node_d2.id, node_a2.id)
        assert result is False

        # attempt to remove node D
        result = svc_container.remove_node(node_d2.id)
        # and recreate as child of B
        node_d2 = svc_container.add_node(
            0, tree2_id_node_type, "node D2", id_parents=node_b2.id
        )
        node = svc_container.get_node(node_d2.id)
        assert isinstance(node, dict)
        assert isinstance(node["record"], NodeRecord)
        assert len(node["parents"]) == 1
        assert node_b2.id in node["parents"]
        assert len(node["children"]) == 0
        # add extra parent
        result = svc_container.add_node_parent(node_d2.id, node_c2.id)
        assert result is True
        node = svc_container.get_node(node_d2.id)
        assert len(node["parents"]) == 2
        assert node_b2.id in node["parents"]
        assert node_c2.id in node["parents"]
        # remove original parent
        result = svc_container.remove_node_parent(node_d2.id, node_b2.id)
        assert result is True
        node = svc_container.get_node(node_d2.id)
        assert len(node["parents"]) == 1
        assert node_c2.id in node["parents"]

        # get tree
        tree2 = svc_container.get_node_tree(0, id_tree_2)
        assert len(tree2) == 4
        assert len(tree2[node_d2.id]["children"]) == 0
        assert tree2[node_d2.id]["parents"] == [node_c2.id]

        # get tree nodes, no hierarchy
        tree2_nodes = svc_container.get_node_list(0, id_tree_2)
        assert len(tree2_nodes) == 4
        for r in tree2_nodes:
            assert r.id in [node_a2.id, node_b2.id, node_c2.id, node_d2.id]

    def test_node_src(self, svc_container: ContainerService):
        node_a = svc_container.add_node(0, NODE_DEFAULT, "node A1", src=100)
        node_b = svc_container.add_node(
            0, NODE_DEFAULT, "node B1", id_parents=node_a.id, src=101
        )
        node_c = svc_container.add_node(
            0, NODE_DEFAULT, "node C1", id_parents=node_a.id, src=102
        )
        node_d = svc_container.add_node(
            0, NODE_DEFAULT, "node D1", id_parents=node_b.id, src=103
        )

        node = svc_container.get_node_src(0, NODE_DEFAULT, 99)
        assert node is None
        node = svc_container.get_node_src(0, NODE_DEFAULT, 102)
        assert node is not None
        assert node.id == node_c.id
        node = svc_container.get_node_src(0, NODE_DEFAULT, 103)
        assert node is not None
        assert node.id == node_d.id
