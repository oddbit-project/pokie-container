from typing import Union, List, Optional

from rick.util.datetime import iso8601_now
from rick_db import Repository
from rick_db.sql import Literal, Select

from pokie_container.dto import (
    TreeTypeRecord,
    NodeTypeRecord,
    NodeRecord,
    NodeTreeRecord,
)


class TreeTypeRepository(Repository):
    def __init__(self, db):
        super().__init__(db, TreeTypeRecord)

    def get_all_ordered(self) -> List[TreeTypeRecord]:
        qry = self.select().order(TreeTypeRecord.label)
        return self.fetch(qry)


class NodeTypeRepository(Repository):
    def __init__(self, db):
        super().__init__(db, NodeTypeRecord)

    def get_all_ordered(self, id_tree_type: int) -> List[NodeTypeRecord]:
        qry = (
            self.select()
            .where(NodeTypeRecord.tree_type, '=', id_tree_type)
            .order(NodeTypeRecord.label)
        )
        return self.fetch(qry)


class NodeRepository(Repository):
    def __init__(self, db):
        super().__init__(db, NodeRecord)

    def get_all_ordered(self, id_tenant: int, id_tree_type: int) -> List[NodeRecord]:
        qry = (
            self.select()
            .where(NodeRecord.tenant, "=", id_tenant)
            .where(NodeRecord.tree_type, "=", id_tree_type)
            .order(NodeRecord.label)
        )
        return self.fetch(qry)

    def find_by_src(self, id_tenant: int, id_tree_type: int, src: int) -> Optional[NodeRecord]:
        qry = (
            self.select()
            .where(NodeRecord.tenant, "=", id_tenant)
            .where(NodeRecord.tree_type, "=", id_tree_type)
            .where(NodeRecord.src, "=", src)
        )
        return self.fetch_one(qry)


class NodeTreeRepository(Repository):
    def __init__(self, db):
        super().__init__(db, NodeTreeRecord)

    def add_node(
            self,
            id_tenant: int,
            id_tree_type: int,
            id_node: int,
            id_parent_node: Union[List, int] = 0,
    ) -> bool:
        if isinstance(id_parent_node, int):
            id_parent_node = [id_parent_node]

        depth = 0
        self._db.begin()
        for id_parent in id_parent_node:
            qry = (
                self.select()
                .where(NodeTreeRecord.tenant, "=", id_tenant)
                .where(NodeTreeRecord.tree_type, "=", id_tree_type)
                .where(NodeTreeRecord.child, "=", id_parent)
            )
            for row in self.fetch(qry):  # type: NodeTreeRecord
                if row.depth >= depth:
                    depth = row.depth + 1
                record = NodeTreeRecord(
                    tenant=id_tenant,
                    tree_type=id_tree_type,
                    parent=row.parent,
                    child=id_node,
                    is_child=True if (row.parent == row.child) else False,
                    depth=row.depth,
                )
                self.insert(record)

        record = NodeTreeRecord(
            tenant=id_tenant,
            tree_type=id_tree_type,
            parent=id_node,
            child=id_node,
            is_child=False,
            depth=depth,
        )
        self.insert(record)
        self._db.commit()
        return True

    def get_by_node(
            self, id_tenant: int, id_tree_type:int, id_node: int
    ) -> Optional[NodeTreeRecord]:
        qry = (
            self.select()
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.child, "=", id_node)
            .where(NodeTreeRecord.parent, "=", id_node)
        )
        return self.fetch_one(qry)

    def get_parents(self, id_tenant: int, id_tree_type:int, id_node: int) -> List:
        """
        Get immediate parent node ids
        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        qry = (
            self.select(cols=[NodeTreeRecord.parent])
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.child, "=", id_node)
            .where(NodeTreeRecord.is_child, "=", True)
        )
        result = []
        for row in self.fetch(qry):
            result.append(row.parent)
        return result

    def get_children(self, id_tenant: int, id_tree_type:int, id_node: int) -> List:
        """
        Get immediate children node ids
        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        qry = (
            self.select(cols=[NodeTreeRecord.child])
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.parent, "=", id_node)
            .where(NodeTreeRecord.is_child, "=", True)
        )
        result = []
        for row in self.fetch(qry):
            result.append(row.child)
        return result

    def add_parent(
            self, id_tenant: int, id_tree_type:int, id_node: int, id_parent: int
    ) -> bool:
        """
        Add a parent to a node
        Note: this cannot be used to move nodes between levels; parent must be at depth-1 from the current node

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :param id_parent:
        :return:
        """
        if id_parent in self.get_parents(id_tenant, id_tree_type, id_node):
            return False

        node = self.get_by_node(id_tenant,id_tree_type, id_node)
        parent = self.get_by_node(id_tenant,id_tree_type, id_parent)
        if node is None or parent is None:
            return False

        if node.depth != parent.depth + 1:
            return False

        self._db.begin()
        subqry = (
            self.select(cols=NodeTreeRecord.parent)
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.child, "=", id_node)
        )

        qry = (
            self.select()
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.child, "=", id_parent)
            .where(NodeTreeRecord.parent, "not in", subqry)
        )
        for row in self.fetch(qry):
            record = NodeTreeRecord(
                tenant=id_tenant,
                tree_type=id_tree_type,
                parent=row.parent,
                child=id_node,
                is_child=True if (row.parent == row.child) else False,
                depth=row.depth,
            )
            self.insert(record)
        self._db.commit()
        return True

    def delete_parent(
            self, id_tenant: int, id_tree_type:int, id_node: int, id_parent: int
    ) -> bool:
        """
        Remove a parent from a node

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :param id_parent:
        :return:
        """
        parents = self.get_parents(id_tenant, id_tree_type, id_node)
        if id_parent not in parents:
            return False
        parents.remove(id_parent)

        # cannot remove last parent
        if len(parents) == 0:
            return False

        toks = [str(p) for p in parents]
        parents = ",".join(toks)

        subqry = (
            self.select(cols=NodeTreeRecord.parent)
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.child, "in", Literal("({})".format(parents)))
        )

        qry = (
            self.select()
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.child, "=", id_node)
            .where(NodeTreeRecord.parent, "<>", id_node)
            .where(NodeTreeRecord.parent, "not in ", subqry)
        )

        self._db.begin()
        for row in self.fetch(qry):
            self.delete_where(
                [
                    (NodeTreeRecord.tenant, "=", id_tenant),
                    (NodeTreeRecord.tree_type, "=", id_tree_type),
                    (NodeTreeRecord.parent, "=", row.parent),
                    (NodeTreeRecord.child, "=", row.child),
                    (NodeTreeRecord.depth, "=", row.depth),
                ]
            )
        self._db.commit()
        return True

    def get_all_children(self, id_tenant: int, id_tree_type:int, id_node: int) -> List:
        """
        Get all node ids for the children subtree of id_node
        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        qry = (
            self.select(cols=[NodeTreeRecord.child])
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.parent, "=", id_node)
            .where(NodeTreeRecord.child, "<>", id_node)
        )
        result = []
        for row in self.fetch(qry):
            result.append(row.child)
        return result

    def get_all_parents(self, id_tenant: int, id_tree_type:int, id_node: int) -> List:
        """
        Get all node ids for the parents of the tree upto id_node

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        qry = (
            self.select(cols=[NodeTreeRecord.parent])
            .where(NodeTreeRecord.tenant, "=", id_tenant)
            .where(NodeTreeRecord.tree_type, "=", id_tree_type)
            .where(NodeTreeRecord.child, "=", id_node)
            .where(NodeTreeRecord.parent, "<>", id_node)
        )
        result = []
        for row in self.fetch(qry):
            result.append(row.parent)
        return result

    def get_all_children_parents(self, id_tenant: int, id_tree_type:int, id_node: int) -> List:
        """
        Return all node ids in path above and below id_node

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        result = self.get_children(id_tenant, id_tree_type, id_node)
        result.extend(self.get_parents(id_tenant, id_tree_type, id_node))
        return result

    def delete_node(self, id_tenant: int, id_tree_type:int, id_node: int) -> bool:
        """
        Removes a node from the tree
        The node must not have children

        :param id_tenant:
        :param id_tree_type:
        :param id_node:
        :return:
        """
        children = self.get_children(id_tenant, id_tree_type, id_node)
        if len(children) > 0:
            return False

        self.delete_where([
            (NodeTreeRecord.tenant, "=", id_tenant),
            (NodeTreeRecord.tree_type, "=", id_tree_type),
            (NodeTreeRecord.child, "=", id_node),
        ])
        return True

    def get_tree(self, id_tenant:int, id_tree_type:int):
        """
        Get complete tree in iterable format

        the result has the following structure:
        {
          node_id: {
            'children': [list of node id's],
            'parents': [list of node id's],
            'nodes': [list of node id's],
            'depth': int
            }
          (...)
        }

        :param id_tenant:
        :param id_tree_type:
        :return:
        """
        tn = self._tablename
        qry = (
                Select(self._dialect).from_(
                    {tn:"a"},
                    cols={
                        NodeTreeRecord.parent:None,
                        NodeTreeRecord.depth: None,
                        Literal("array(SELECT child FROM {tn} as sub WHERE sub.parent = a.parent AND is_child )".format(tn=tn)):"children",
                        Literal("array(SELECT parent FROM {tn} as sub WHERE sub.child = a.parent AND is_child )".format(tn=tn)): "parents",
                        Literal("array(SELECT child FROM {tn} as sub WHERE sub.parent = a.parent )".format(tn=tn)):"nodes"
                    },
                    schema=self._schema
                )
                .where(NodeTreeRecord.tenant, '=', id_tenant)
                .where(NodeTreeRecord.tree_type, '=', id_tree_type)
                .where(NodeTreeRecord.parent, '=', Literal("a.child"))
                .order(NodeTreeRecord.depth)
        )
        result = {}
        with self._db.cursor() as c:
            sql, values = qry.assemble()
            for row in c.fetchall(sql, values):
                result[row['parent']] = {
                    'children': row['children'],
                    'parents': row['parents'],
                    'nodes': row['nodes'],
                    'depth': row['depth']
                }
        return result
