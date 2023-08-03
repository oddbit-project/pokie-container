from typing import List, Optional, Union

from pokie.constants import DI_DB
from rick.mixin import Injectable
from rick.util.datetime import iso8601_now

from pokie_container.dto import TreeTypeRecord, NodeTypeRecord, NodeRecord, NodeTreeRecord
from pokie_container.errors import NodeTypeNotFoundError, NodeNotFoundError, NodeError
from pokie_container.repository.repository import NodeRepository, NodeTreeRepository, NodeTypeRepository, \
    TreeTypeRepository


class ContainerService(Injectable):

    def get_tree_type_list(self) -> List[TreeTypeRecord]:
        """
        Retrieve a list of tree types
        :return:
        """
        return self.repo_tree_type().get_all_ordered()

    def add_tree_type(self, id_tree_type: int, label: str) -> TreeTypeRecord:
        """
        Add a new tree type

        :param id_tree_type:
        :param label:
        :return:
        """
        record = TreeTypeRecord(
            id=id_tree_type,
            label=label,
        )
        self.repo_tree_type().insert(record)
        return record

    def get_node_type_list(self, id_tree_type: int) -> List[NodeTypeRecord]:
        """
        Retrieve list of node types
        :param id_tree_type:
        :return:
        """
        return self.repo_node_type().get_all_ordered(id_tree_type)

    def add_node_type(self, id_tree_type: int, id_node_type: int, label: str) -> NodeTypeRecord:
        """
        Create a node type

        :param id_tree_type:
        :param id_node_type:
        :param label:
        :return:
        """
        record = NodeTypeRecord(
            id=id_node_type,
            tree_type=id_tree_type,
            label=label
        )
        self.repo_node_type().insert(record)
        return record

    def remove_node_type(self, id_node_type: int) -> bool:
        """
        Remove a node type

        :param id_node_type:
        :return:
        """
        record = self.repo_node_type().fetch_pk(id_node_type)
        if record is None:
            return False
        try:
            self.repo_node_type().delete_pk(id_node_type)
            return True
        except Exception as e:
            return False

    def get_node_record(self, id_node: int) -> Optional[NodeRecord]:
        """
        Get just the node record

        :param id_node:
        :return:
        """
        return self.repo_node().fetch_pk(id_node)

    def get_node(self, id_node: int) -> Optional[dict]:
        """
        Get node details

        Return format:
        {
            "record": NodeRecord,
            "parents": [list of immediate parent ids],
            "children": [list of immediate children ids],
        }

        :param id_node:
        :return:
        """
        record = self.repo_node().fetch_pk(id_node)  # type: NodeRecord
        if record is None:
            return None
        return {
            'record': record,
            'parents': self.repo_tree().get_parents(record.tenant, record.tree_type, record.id),
            'children': self.repo_tree().get_children(record.tenant, record.tree_type, record.id),
        }

    def get_node_src(self, id_tenant: int, id_tree_type: int, src: int) -> Optional[NodeRecord]:
        """
        Find a node by src

        :param id_tenant:
        :param id_tree_type:
        :param src:
        :return:
        """
        return self.repo_node().find_by_src(id_tenant, id_tree_type, src)

    def get_all_node_children_id(self, id_tenant: int, id_tree_type: int, id_node: int) -> List[int]:
        """
        Get all node ids for the children subtree of id_node

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        return self.repo_tree().get_all_children(id_tenant, id_tree_type, id_node)

    def get_all_node_parents_id(self, id_tenant: int, id_tree_type: int, id_node: int) -> List[int]:
        """
        Get all node ids for the parents of the tree upto id_node

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        return self.repo_tree().get_all_parents(id_tenant, id_tree_type, id_node)

    def get_children_id(self, id_tenant: int, id_tree_type: int, id_node: int) -> List[int]:
        """
        Get immediate children node ids

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        return self.repo_tree().get_children(id_tenant, id_tree_type, id_node)

    def get_parents_id(self, id_tenant: int, id_tree_type: int, id_node: int) -> List[int]:
        """
        Get immediate parent node ids

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        return self.repo_tree().get_parents(id_tenant, id_tree_type, id_node)

    def get_node_subtree_id(self, id_tenant: int, id_tree_type: int, id_node: int) -> List[int]:
        """
        Return all node ids in path above and below id_node

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        return self.repo_tree().get_all_children_parents(id_tenant, id_tree_type, id_node)

    def add_node(self, id_tenant: int, id_node_type: int, label: str, id_parents: Union[int, List] = None,
                 src: int = None,
                 attributes: dict = None) -> NodeRecord:
        """
        Creates a new node and adds it to the tree

        :param id_tenant:
        :param id_node_type:
        :param label:
        :param id_parents:
        :param src:
        :param attributes:
        :return:
        """
        node_type = self.repo_node_type().fetch_pk(id_node_type)  # type: NodeTypeRecord
        if not node_type:
            raise NodeTypeNotFoundError("invalid node type: {}".format(str(id_node_type)))

        if not attributes:
            attributes = {}

        if id_parents is None:
            id_parents = []
        elif isinstance(id_parents, int):
            id_parents = [id_parents]

        now = iso8601_now()
        record = NodeRecord(
            tenant=id_tenant,
            tree_type=node_type.tree_type,
            node_type=node_type.id,
            created=now,
            updated=now,
            src=src,
            label=label,
            attributes=attributes
        )
        record.id = self.repo_node().insert_pk(record)
        self.repo_tree().add_node(id_tenant, record.tree_type, record.id, id_parents)

        return record

    def add_node_parent(self, id_node: int, id_parent: int) -> bool:
        """
        Add an extra parent to a node
        Note: this cannot be used to move nodes around the tree, only to bind them to multiple parents

        :param id_node:
        :param id_parent:
        :return:
        """
        node = self.repo_node().fetch_pk(id_node)  # type: NodeRecord
        if node is None:
            return False
        return self.repo_tree().add_parent(node.tenant, node.tree_type, id_node, id_parent)

    def remove_node_parent(self, id_node: int, id_parent: int) -> bool:
        """
        Remove a parent from a node

        :param id_node:
        :param id_parent:
        :return:
        """
        node = self.repo_node().fetch_pk(id_node)  # type: NodeRecord
        if node is None:
            return False
        return self.repo_tree().delete_parent(node.tenant, node.tree_type, id_node, id_parent)

    def update_node(self, record: NodeRecord):
        """
        Updates a node record
        :param record:
        :return:
        """
        record.updated = iso8601_now()
        return self.repo_node().update(record)

    def remove_node(self, id_node: int):
        """
        Removes a node from the node table and the tree

        :param id_node:
        :return:
        """
        repo_node = self.repo_node()
        node = repo_node.fetch_pk(id_node)  # type: NodeRecord
        if not node:
            raise NodeNotFoundError("invalid node id {}".format(str(id_node)))

        if not self.repo_tree().delete_node(node.tenant, node.tree_type, id_node):
            raise NodeError("cannot remove node id {}".format(str(id_node)))

        self.repo_node().delete_pk(id_node)

    def get_node_tree(self, id_tenant: int, id_tree_type: int, fetch_records=False) -> dict:
        """
        Fetches a tree

        the result has the following structure when fetch_records == False:
        {
          node_id: {
            'children': [list of node id's],
            'parents': [list of node id's],
            'nodes': [list of node id's],
            'depth': int
            }
          (...)
        }

        the result has the following structure when fetch_records == True:
        {
          node object: {
            'children': [list of node id's],
            'parents': [list of node id's],
            'nodes': [list of node id's],
            'depth': int
            }
          (...)
        }

        :param id_tenant:
        :param id_tree_type:
        :param fetch_records:
        :return: dict
        """
        result = self.repo_tree().get_tree(id_tenant, id_tree_type)
        if not fetch_records:
            return result

        record_result = {}
        repo = self.repo_node()
        for k, v in result.items():
            record_result[repo.fetch_pk(k)] = v
        return record_result

    def get_node_list(self, id_tenant: int, id_tree_type: int) -> List[NodeRecord]:
        """
        Retrieve a list of nodes sorted by label for a given tree
        :param id_tenant:
        :param id_tree_type:
        :return:
        """
        return self.repo_node().get_all_ordered(id_tenant, id_tree_type)

    def repo_node(self) -> NodeRepository:
        return NodeRepository(self.get_di().get(DI_DB))

    def repo_node_type(self) -> NodeTypeRepository:
        return NodeTypeRepository(self.get_di().get(DI_DB))

    def repo_tree_type(self) -> TreeTypeRepository:
        return TreeTypeRepository(self.get_di().get(DI_DB))

    def repo_tree(self) -> NodeTreeRepository:
        return NodeTreeRepository(self.get_di().get(DI_DB))
