from rick_db import fieldmapper


@fieldmapper(tablename="container_tree_type", pk="id_container_tree_type")
class TreeTypeRecord:
    id = "id_container_tree_type"
    label = "label"


@fieldmapper(tablename="container_type", pk="id_container_type")
class ContainerTypeRecord:
    id = "id_container_type"
    label = "label"


@fieldmapper(tablename="container", pk="id_container")
class ContainerRecord:
    id = "id_container"
    tenant = "fk_tenant"
    tree_type = "fk_container_tree_type"
    container_type = "fk_container_type"
    src = "src"
    label = "label"
    attributes = "attributes"


@fieldmapper(tablename="container_tree", pk="id_container_tree")
class ContainerTreeRecord:
    id = "id_container_tree"
    tenant = "fk_tenant"
    tree_type = "fk_container_tree_type"
    parent = "parent"
    child = "child"
    is_child = "is_child"
    depth = "depth"
