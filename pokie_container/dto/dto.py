from rick_db import fieldmapper


@fieldmapper(tablename="node_tree_type", pk="id_node_tree_type")
class TreeTypeRecord:
    id = "id_node_tree_type"
    label = "label"


@fieldmapper(tablename="node_type", pk="id_node_type")
class NodeTypeRecord:
    id = "id_node_type"
    tree_type = "fk_node_tree_type"
    label = "label"


@fieldmapper(tablename="node", pk="id_node")
class NodeRecord:
    id = "id_node"
    tenant = "fk_tenant"
    tree_type = "fk_node_tree_type"
    node_type = "fk_node_type"
    created = "created_at"
    updated = "updated_at"
    src = "src"
    label = "label"
    attributes = "attributes"


@fieldmapper(tablename="node_tree", pk="id_node_tree")
class NodeTreeRecord:
    id = "id_node_tree"
    tenant = "fk_tenant"
    tree_type = "fk_node_tree_type"
    parent = "parent"
    child = "child"
    is_child = "is_child"
    depth = "depth"
