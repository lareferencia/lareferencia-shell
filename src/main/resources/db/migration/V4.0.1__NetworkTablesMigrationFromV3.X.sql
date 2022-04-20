/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES  */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- CREATE TABLE IF NOT EXISTS broker_event (
-- 	id BIGINT NOT NULL DEFAULT nextval('broker_event_id_seq'::regclass),
-- 	identifier CHARACTER VARYING(255) NOT NULL,
-- 	message TEXT NULL DEFAULT NULL,
-- 	network_id BIGINT NULL DEFAULT NULL,
-- 	topic CHARACTER VARYING(255) NULL DEFAULT NULL,
-- 	PRIMARY KEY ("id"),
-- 	KEY ("identifier"),
-- 	KEY ("network_id"),
-- 	KEY ("topic")
-- );

DROP TABLE IF EXISTS oairecord;
DROP SEQUENCE IF EXISTS oai_record_id_seq;

CREATE SEQUENCE IF NOT EXISTS oai_record_id_seq
    START WITH 1
    INCREMENT BY 1000
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


CREATE TABLE IF NOT EXISTS oairecord (
	id BIGINT NOT NULL,
	datestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	identifier CHARACTER VARYING(255) NOT NULL,
	originalxml TEXT NULL DEFAULT NULL,
	publishedxml TEXT NULL DEFAULT NULL,
	status INTEGER NOT NULL,
	transformed BOOLEAN NOT NULL,
	snapshot_id BIGINT NULL DEFAULT NULL,
	PRIMARY KEY ("id")
);

ALTER TABLE oairecord ALTER COLUMN id SET DEFAULT nextval('oai_record_id_seq'::regclass);
ALTER TABLE oairecord ADD CONSTRAINT fk_snapshot FOREIGN KEY (snapshot_id) REFERENCES networksnapshot(id);


-- update network table

ALTER TABLE network
ADD COLUMN IF NOT EXISTS attributes TEXT NULL DEFAULT '{}',
ADD COLUMN IF NOT EXISTS metadataprefix CHARACTER VARYING(255) NULL DEFAULT 'oai_dc',
ADD COLUMN IF NOT EXISTS metadatastoreschema CHARACTER VARYING(255) NULL DEFAULT 'xoai' ,
ADD COLUMN IF NOT EXISTS originurl CHARACTER VARYING(255) NULL DEFAULT NULL,
ADD COLUMN IF NOT EXISTS properties TEXT NULL DEFAULT '{}',
ADD COLUMN IF NOT EXISTS sets TEXT NULL DEFAULT '[]',
ADD COLUMN IF NOT EXISTS pre_validator_id BIGINT NULL DEFAULT NULL;

ALTER TABLE network DROP CONSTRAINT IF EXISTS fk_prevalidator;
ALTER TABLE network ADD CONSTRAINT fk_prevalidator FOREIGN KEY (pre_validator_id) REFERENCES validator(id);

-- migrate network data from v3 to v4

UPDATE network
SET attributes = attributesjsonserialization;

UPDATE network 
SET  metadataprefix = o.metadataprefix, originurl = o.uri 
FROM oaiorigin o
WHERE network.id = o.network_id;

UPDATE network 
SET sets = j.sets_json
FROM 
(SELECT o.network_id, concat('[',string_agg(format('"%s"', spec), ', '),']') AS sets_json FROM oaiset s, oaiorigin o WHERE s.origin_id = o.id GROUP BY o.network_id) AS j 
WHERE id = j.network_id;

UPDATE network
SET properties = j.properties_json
FROM 
( SELECT n.network_id, concat('{',string_agg(format('"%s":%s', n.name,n.value::text), ', '),'}') AS properties_json FROM networkproperty n GROUP BY n.network_id ) AS j
WHERE id = j.network_id;

-- networksnapshot

ALTER TABLE networksnapshot ADD COLUMN IF NOT EXISTS lastincrementaltime TIMESTAMP WITHOUT TIME ZONE;

-- Truncate snapshots logs
TRUNCATE networksnapshotlog;

-- Set all snapshots as deleted
UPDATE networksnapshot
SET deleted = true;

/*
DROP TABLE IF EXISTS networkproperty;
DROP TABLE IF EXISTS oaiset;
DROP TABLE IF EXISTS oaiorigin;
*/

-- La exportación de datos fue deseleccionada.
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
