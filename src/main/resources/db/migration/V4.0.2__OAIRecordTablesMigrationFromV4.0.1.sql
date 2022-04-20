/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES  */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


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
	identifier VARCHAR(255) NOT NULL,
	originalmetadatahash VARCHAR(32) NULL DEFAULT NULL,
	publishedmetadatahash VARCHAR(32) NULL DEFAULT NULL,
	snapshot_id BIGINT NULL DEFAULT NULL,
	status INTEGER NOT NULL,
	transformed BOOLEAN NOT NULL,
	PRIMARY KEY ("id")
);

ALTER TABLE oairecord ALTER COLUMN id SET DEFAULT nextval('oai_record_id_seq'::regclass);
ALTER TABLE oairecord ADD CONSTRAINT fk_snapshot FOREIGN KEY (snapshot_id) REFERENCES networksnapshot(id);

DROP INDEX IF EXISTS oairecord_snapid_index;
CREATE INDEX oairecord_snapid_index ON oairecord USING btree (snapshot_id);	

DROP INDEX IF EXISTS oairecord_snapid_status_id_index;
CREATE INDEX oairecord_snapid_status_id_index ON oairecord USING btree (snapshot_id, status, id);

DROP TABLE IF EXISTS oaimetadata;
CREATE TABLE IF NOT EXISTS oaimetadata (
	hash VARCHAR(32) NOT NULL,
	metadata TEXT NOT NULL,
	PRIMARY KEY ("hash")
);

-- Truncate snapshots logs
TRUNCATE networksnapshotlog;

-- Set all snapshots as deleted
UPDATE networksnapshot
SET deleted = true;

-- La exportación de datos fue deseleccionada.
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
