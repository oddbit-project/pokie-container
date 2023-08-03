# Version
POKIE_CONTAINER_VERSION = ["0", "9", "0"]


def get_version():
    return ".".join(POKIE_CONTAINER_VERSION)


SVC_CONTAINER = "pokie_container.container"

TENANT_DEFAULT = 0  # default tenant
TREE_DEFAULT = 1    # default tree type
NODE_DEFAULT = 1   # default node type
