CREATE TABLE node_tree_type (
  id_node_tree_type INT NOT NULL PRIMARY KEY,
  label       TEXT NOT NULL
);

CREATE TABLE node_type (
  id_node_type INT NOT NULL PRIMARY KEY,
  fk_node_tree_type INT NOT NULL REFERENCES node_tree_type,
  label TEXT NOT NULL
);

CREATE TABLE node (
  id_node BIGSERIAL PRIMARY KEY,
  fk_tenant BIGINT NOT NULL,
  fk_node_tree_type INT NOT NULL REFERENCES node_tree_type,
  fk_node_type INT NOT NULL REFERENCES node_type,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
  src BIGINT DEFAULT NULL,
  label TEXT NOT NULL,
  attributes JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX node_idx01 ON node (fk_tenant, fk_node_tree_type);
CREATE INDEX node_idx02 ON node (fk_node_type);
CREATE INDEX node_idx03 ON node (src);

CREATE TABLE node_tree (
  id_node_tree BIGSERIAL NOT NULL PRIMARY KEY,
  fk_tenant BIGINT NOT NULL,
  fk_node_tree_type INT NOT NULL REFERENCES node_tree_type,
  parent BIGINT NOT NULL  REFERENCES node,
  child BIGINT NOT NULL REFERENCES node,
  is_child  BOOL   NOT NULL DEFAULT FALSE,
  depth     INT    NOT NULL DEFAULT 0
);

CREATE INDEX node_tree_idx01 ON node_tree (fk_tenant);
CREATE UNIQUE INDEX node_tree_idx02 ON node_tree (parent, child);

CREATE OR REPLACE RULE node_tree_insert_unique AS
ON INSERT TO node_tree
  WHERE (
    EXISTS(
        SELECT 1
        FROM node_tree
        WHERE
            node_tree.fk_tenant = NEW.fk_tenant AND
            node_tree.fk_node_tree_type = NEW.fk_node_tree_type AND
            node_tree.parent = NEW.parent AND
            node_tree.child = NEW.child
            )
  ) DO INSTEAD NOTHING;

INSERT INTO node_tree_type(id_node_tree_type,label) VALUES(1, 'Default');
INSERT INTO node_type(id_node_type, fk_node_tree_type, label) VALUES(1, 1, 'Node');
