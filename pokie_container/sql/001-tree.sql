CREATE TABLE container_tree_type (
  id_container_tree_type INT NOT NULL PRIMARY KEY,
  label       TEXT NOT NULL
);

CREATE TABLE container_type (
  id_container_type INT NOT NULL PRIMARY KEY,
  fk_container_tree_type INT NOT NULL REFERENCES container_tree,
  label TEXT NOT NULL
);

CREATE TABLE container (
  id_container BIGSERIAL PRIMARY KEY,
  fk_tenant BIGINT NOT NULL,
  fk_container_tree_type INT NOT NULL REFERENCES container_tree,
  fk_container_type INT NOT NULL REFERENCES container_type,
  src BIGINT DEFAULT NULL,
  label TEXT NOT NULL,
  attributes JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX container_idx01 ON container (fk_tenant, fk_container_tree_type);
CREATE INDEX container_idx02 ON container (fk_container_type);
CREATE INDEX container_idx03 ON container (src);

CREATE TABLE container_tree (
  id_container_tree BIGSERIAL NOT NULL PRIMARY KEY,
  fk_tenant BIGINT NOT NULL,
  fk_container_tree_type INT NOT NULL REFERENCES container_tree_type,
  parent BIGINT NOT NULL  REFERENCES container,
  child BIGINT NOT NULL REFERENCES container,
  is_child  BOOL   NOT NULL DEFAULT FALSE,
  depth     INT    NOT NULL DEFAULT 0
);

CREATE INDEX container_tree_idx01 ON container_tree (fk_tenant);
CREATE UNIQUE INDEX container_tree_idx02 ON container_tree (parent, child);

CREATE OR REPLACE RULE container_tree_insert_unique AS
ON INSERT TO container_tree
  WHERE (
    EXISTS(
        SELECT 1
        FROM container_tree
        WHERE
            container_tree.fk_tenant = NEW.fk_tenant AND
            container_tree.fk_container_tree_type = NEW.fk_container_tree_type AND
            container_tree.parent = NEW.parent AND
            container_tree.child = NEW.child
            )
  ) DO INSTEAD NOTHING;
