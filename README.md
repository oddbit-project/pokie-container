# pokie-container

[![Tests](https://github.com/oddbit-project/pokie-container/workflows/Tests/badge.svg?branch=master)](https://github.com/oddbit-project/pokie-container/actions)
[![pypi](https://img.shields.io/pypi/v/pokie-container.svg)](https://pypi.org/project/pokie-container/)
[![license](https://img.shields.io/pypi/l/pokie-container.svg)](https://git.oddbit.org/OddBit/pokie-container/src/branch/master/LICENSE)


pokie-container is a Pokie module to manage multiple tree data structures, using the database. It features a multi-tenant,
multi-tree, multi-type node closure table implementation. 

## Adding to a Pokie project

Just add the module name to the module list in your *main.py*:

```python
(...)

def build_pokie():
    # load configuration from ENV
    cfg = Config().build()

    # modules to load & initialize
    modules = ['pokie_container', ]

    # factories to run
    factories = [PgSqlFactory]

    # build app
    pokie_app = FlaskApplication(cfg)
    flask_app = pokie_app.build(modules, factories)
    return pokie_app, flask_app


main, app = build_pokie()

(...)
```

## Usage: basic concepts

**Tree Type**

A tree type works as a distinct tree identifier. A given application may have e.g. a user group tree, and an unrelated attribute
tree - these would be distinct tree types within the same application. Each tree has its own node types and its own nodes; there
is no underlying relationship between different tree types, their purpose is to compartmentalize different trees.

The best practice to create custom tree types is to add them to the sql migrations of a given project module, and define
the appropriate constants for ID, as their numeric identifier is assigned manually by the programmer. Regardless,
the pokie-container service also provides some methods to add tree types in runtime. The module also provides a default
tree, conveniently using the numeric id 1.

**Node Type**

A node type is a node identifier that can be used for specific application logic. As an example, a LMS application may
use a tree to map a virtual campus, with classrooms with different subjects. These different types of objects could be
mapped as node types.
The module provides a base node type, using the numeric id 1.

**Node**

A node is a container object that is inserted somewhere in the tree. This container object has a specific position in the
tree, a node type, and an underlying tree type. It can also have a custom attribute dictionary, and external numeric reference
for applicational purpose, and a string label.

## Usage: populating a tree

```python
from pokie_container.service import ContainerService
from rick.mixin import Injectable
from pokie.constants import DI_SERVICES
from pokie_container.constants import  SVC_CONTAINER, NODE_DEFAULT, TREE_DEFAULT

class SampleService(Injectable):
    
    def svc_container(self) -> ContainerService:
        return self.get_di().get(DI_SERVICES).get(SVC_CONTAINER)

    
    def create_tree_dump(self, id_tenant:int=0):
        # create a tree with the following structure
        #       A
        #      / \
        #     B   C
        #    / \
        #   D   E
        svc_container = self.svc_container()
        
        # create nodes with type NODE_DEFAULT
        # the node type is internally associated with a tree type - in this case, TREE_DEFAULT
        
        node_a = svc_container.add_node(id_tenant, NODE_DEFAULT, "node A")
        node_b = svc_container.add_node(id_tenant, NODE_DEFAULT, "node B", id_parents=node_a.id)
        node_c = svc_container.add_node(id_tenant, NODE_DEFAULT, "node C", id_parents=node_a.id)
        node_d = svc_container.add_node(id_tenant, NODE_DEFAULT, "node D", id_parents=node_b.id)
        node_e = svc_container.add_node(id_tenant, NODE_DEFAULT, "node E", id_parents=node_b.id)

        tree = svc_container.get_node_tree(id_tenant, TREE_DEFAULT)
        # dump tree
        print(tree)
```

