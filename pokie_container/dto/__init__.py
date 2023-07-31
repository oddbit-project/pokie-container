from rick_db import fieldmapper


@fieldmapper(tablename="container_tree_type", pk="id_container_tree_type")
class TreeTypeRecord:
    id = "id_container_tree_type"
    label = "label"


@fieldmapper(tablename="container_tree", pk=None)
class TreeRecord:
    tenant = "tentant"
    tree_type = "fk_container_tree_type"
    parent= "container_parent"
    child = "container_child"
    is_child = "is_child"
    depth = "depth"
