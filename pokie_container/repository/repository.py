from typing import Union, List, Optional

from rick.util.datetime import iso8601_now
from rick_db import Repository
from rick_db.sql import Literal

from pokie_container.dto import (
    TreeTypeRecord,
    ContainerTypeRecord,
    ContainerRecord,
    ContainerTreeRecord,
)


class TreeTypeRepository(Repository):
    def __init__(self, db):
        super().__init__(db, TreeTypeRecord)


class ContainerTypeRepository(Repository):
    def __init__(self, db):
        super().__init__(db, ContainerTypeRecord)


class ContainerRepository(Repository):
    def __init__(self, db):
        super().__init__(db, ContainerRecord)


class ContainerTreeRepository(Repository):
    def __init__(self, db):
        super().__init__(db, ContainerTreeRecord)

    def add_node(
        self,
        id_tenant: int,
        id_tree_type: int,
        id_container: int,
        id_parent_container: Union[List, int],
    ) -> bool:
        if isinstance(id_parent_container, int):
            id_parent_container = [id_parent_container]

        depth = 0
        self._db.begin()
        for id_parent in id_parent_container:
            qry = (
                self.select()
                .where(ContainerTreeRecord.tenant, "=", id_tenant)
                .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
                .where(ContainerTreeRecord.child, "=", id_parent)
            )
            for row in self.fetch(qry):  # type: ContainerTreeRecord
                if row.depth >= depth:
                    depth = row.depth + 1
                record = ContainerRecord(
                    tenant=id_tenant,
                    tree_type=id_tree_type,
                    parent=row.parent,
                    child=id_container,
                    is_child=True if (row.parent == row.child) else False,
                    depth=row.depth,
                )
                self.insert(record)

        record = ContainerRecord(
            tenant=id_tenant,
            tree_type=id_tree_type,
            parent=id_container,
            child=id_container,
            is_child=False,
            depth=depth,
        )
        self.insert(record)
        self._db.commit()
        return True

    def get_by_container(
        self, id_tenant: int, id_tree_type: int, id_container: int
    ) -> Optional[ContainerTreeRecord]:
        qry = (
            self.select()
            .where(ContainerTreeRecord.tenant, "=", id_tenant)
            .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
            .where(ContainerTreeRecord.child, "=", id_container)
            .where(ContainerTreeRecord.parent, "=", id_container)
        )
        return self.fetch_one(qry)

    def get_parents(self, id_tenant: int, id_tree_type: int, id_container: int):
        qry = (
            self.select(cols=[ContainerTreeRecord.parent])
            .where(ContainerTreeRecord.tenant, "=", id_tenant)
            .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
            .where(ContainerTreeRecord.child, "=", id_container)
            .where(ContainerTreeRecord.is_child, "=", True)
        )
        result = []
        for row in self.fetch(qry):
            result.append(row.parent)
        return result

    def get_children(self, id_tenant: int, id_tree_type: int, id_container: int):
        qry = (
            self.select(cols=[ContainerTreeRecord.child])
            .where(ContainerTreeRecord.tenant, "=", id_tenant)
            .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
            .where(ContainerTreeRecord.parent, "=", id_container)
            .where(ContainerTreeRecord.is_child, "=", True)
        )
        result = []
        for row in self.fetch(qry):
            result.append(row.child)
        return result

    def add_parent(
        self, id_tenant: int, id_tree_type: int, id_container: int, id_parent: int
    ) -> bool:
        if id_parent in self.get_parents(id_tenant, id_tree_type, id_container):
            return False

        node = self.get_by_container(id_tenant, id_tree_type, id_container)
        parent = self.get_by_container(id_tenant, id_tree_type, id_parent)
        if node is None or parent is None:
            return False

        if node.depth != parent.depth + 1:
            return False

        self._db.begin()
        subqry = (
            self.select(cols=ContainerTreeRecord.parent)
            .where(ContainerTreeRecord.tenant, "=", id_tenant)
            .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
            .where(ContainerTreeRecord.child, "=", id_container)
        )

        qry = (
            self.select()
            .where(ContainerTreeRecord.tenant, "=", id_tenant)
            .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
            .where(ContainerTreeRecord.child, "=", id_parent)
            .where(ContainerTreeRecord.parent, "not in", subqry)
        )
        for row in self.fetch(qry):
            record = ContainerTreeRecord(
                tenant=id_tenant,
                tree_type=id_tree_type,
                parent=row.parent,
                child=id_container,
                is_child=True if (row.parent == row.child) else False,
                depth=row.depth,
            )
            self.insert(record)
        self._db.commit()
        return True

    def delete_parent(
        self, id_tenant: int, id_tree_type: int, id_container: int, id_parent: int
    ) -> bool:
        parents = self.get_parents(id_tenant, id_tree_type, id_container)
        if id_parent not in parents:
            return False
        parents.remove(id_parent)

        # cannot remove last parent
        if len(parents) == 0:
            return False

        parents = ",".join(parents)

        subqry = (
            self.select(cols=ContainerTreeRecord.parent)
            .where(ContainerTreeRecord.tenant, "=", id_tenant)
            .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
            .where(ContainerTreeRecord.child, "in", Literal("({})".format(parents)))
        )

        qry = (
            self.select()
            .where(ContainerTreeRecord.tenant, "=", id_tenant)
            .where(ContainerTreeRecord.tree_type, "=", id_tree_type)
            .where(ContainerTreeRecord.child, "=", id_container)
            .where(ContainerTreeRecord.parent, "<>", id_container)
            .where(ContainerTreeRecord.parent, "not in ", subqry)
        )

        self._db.begin()
        for row in self.fetch(qry):
            self.delete_where(
                [
                    (ContainerTreeRecord.tenant, "=", id_tenant),
                    (ContainerTreeRecord.tree_type, "=", id_tree_type),
                    (ContainerTreeRecord.parent, "=", row.parent),
                    (ContainerTreeRecord.child, "=", row.child),
                    (ContainerTreeRecord.depth, "=", row.depth),
                ]
            )
        self._db.commit()
        return True


"""
"""
