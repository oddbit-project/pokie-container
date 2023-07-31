CREATE TABLE container_tree_type (
  id_container_tree_type INT NOT NULL PRIMARY KEY,
  label       TEXT NOT NULL
);

CREATE TABLE container_tree (
  tenant BIGINT NOT NULL,
  fk_container_tree_type INT NOT NULL REFERENCES container_tree_type,
  container_parent BIGINT NOT NULL,
  container_child  BIGINT NOT NULL,
  is_child  BOOL   NOT NULL DEFAULT FALSE,
  depth     INT    NOT NULL DEFAULT 0
);

CREATE INDEX container_tree_idx01 ON container_tree (tenant);
CREATE UNIQUE INDEX container_tree_idx02 ON container_tree (container_parent, container_child);

CREATE OR REPLACE RULE container_tree_insert_unique AS
ON INSERT TO container_tree
  WHERE (
    EXISTS(
        SELECT 1
        FROM container_tree
        WHERE
            container_tree.tenant = NEW.tenant AND
            container_tree.fk_tree_type = NEW.fk_tree_type AND
            container_tree.container_parent = NEW.container_parent AND
            container_tree.container_child = NEW.container_child
            )
  ) DO INSTEAD NOTHING;
