DROP TABLE IF EXISTS entity CASCADE; 
DROP TABLE IF EXISTS source_entity CASCADE; 
DROP TABLE IF EXISTS entity_type CASCADE; 
DROP TABLE IF EXISTS field_occurrence CASCADE; 
DROP TABLE IF EXISTS field_type CASCADE; 
DROP TABLE IF EXISTS relation CASCADE;
DROP TABLE IF EXISTS source_relation CASCADE; 
DROP TABLE IF EXISTS relation_type CASCADE;
DROP TABLE IF EXISTS relation_entity CASCADE;
DROP TABLE IF EXISTS semantic_identifier CASCADE;
DROP TABLE IF EXISTS entity_semantic_identifier CASCADE;
DROP TABLE IF EXISTS source_entity_semantic_identifier CASCADE;
DROP TABLE IF EXISTS entity_provenance CASCADE;
DROP TABLE IF EXISTS provenance CASCADE;
DROP TABLE IF EXISTS relation_type_member CASCADE;

DROP SEQUENCE IF EXISTS entity_relation_type_seq CASCADE;
DROP SEQUENCE IF EXISTS field_occr_type_seq CASCADE;
DROP SEQUENCE IF EXISTS sematic_id_type_seq CASCADE;

DROP TABLE IF EXISTS entity_relation_type CASCADE; 
DROP TABLE IF EXISTS field_occurrence_container CASCADE;
DROP SEQUENCE IF EXISTS hibernate_SEQUENCE CASCADE;

DROP TABLE IF EXISTS source_entity_fieldoccr CASCADE; 
DROP TABLE IF EXISTS entity_fieldoccr CASCADE; 
DROP TABLE IF EXISTS source_relation_fieldoccr CASCADE; 
DROP TABLE IF EXISTS relation_fieldoccr CASCADE; 




--
-- Name: entity; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE entity (
    uuid uuid NOT NULL,
    entity_type_id bigint,
    dirty boolean
);


--
-- Name: entity_fieldoccr; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE entity_fieldoccr (
    entity_id uuid NOT NULL,
    fieldoccr_id bigint NOT NULL
);

--
-- Name: entity_relation_type_seq; Type: SEQUENCE; Schema: public; Owner: lrharvester
--

CREATE SEQUENCE entity_relation_type_seq
    START WITH 1
    INCREMENT BY 100
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: entity_semantic_identifier; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE entity_semantic_identifier (
    entity_id uuid NOT NULL,
    semantic_id bigint NOT NULL
);


--
-- Name: entity_type; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE entity_type (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255)
);

--
-- Name: field_occurrence; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE field_occurrence (
    kind character varying(31) NOT NULL,
    id bigint NOT NULL,
    field_type_id bigint,
    lang character varying(255),
    content text
);

--
-- Name: field_type; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE field_type (
    id bigint NOT NULL,
    description character varying(255),
    kind integer,
    maxoccurs integer,
    name character varying(255),
    entity_relation_type_id bigint,
    parent_field_type_id bigint
);


--
-- Name: field_type_id_seq; Type: SEQUENCE; Schema: public; Owner: lrharvester
--

CREATE SEQUENCE field_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: field_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: lrharvester
--

ALTER SEQUENCE field_type_id_seq OWNED BY field_type.id;

--
-- Name: provenance; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE provenance (
    id bigint NOT NULL,
    last_update timestamp without time zone,
    record_id character varying(255),
    source_id character varying(255)
);


--
-- Name: relation; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE relation (
    from_entity_id uuid NOT NULL,
    relation_type_id bigint NOT NULL,
    to_entity_id uuid NOT NULL,
    dirty boolean
);


--
-- Name: relation_fieldoccr; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE relation_fieldoccr (
    from_entity_id uuid NOT NULL,
    relation_type_id bigint NOT NULL,
    to_entity_id uuid NOT NULL,
    fieldoccr_id bigint NOT NULL
);


--
-- Name: relation_type; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE relation_type (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255),
    from_entity_id bigint,
    to_entity_id bigint
);


--
-- Name: semantic_identifier; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE semantic_identifier (
    id bigint NOT NULL,
    semantic_id character varying(255)
);


--
-- Name: source_entity; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE source_entity (
    uuid uuid NOT NULL,
    entity_type_id bigint,
    deleted boolean,
    final_entity_id uuid,
    provenance_id bigint
);


--
-- Name: source_entity_fieldoccr; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE source_entity_fieldoccr (
    entity_id uuid NOT NULL,
    fieldoccr_id bigint NOT NULL
);


--
-- Name: source_entity_semantic_identifier; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE source_entity_semantic_identifier (
    entity_id uuid NOT NULL,
    semantic_id bigint NOT NULL
);


--
-- Name: source_relation; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE source_relation (
    from_entity_id uuid NOT NULL,
    relation_type_id bigint NOT NULL,
    to_entity_id uuid NOT NULL,
    confidence double precision NOT NULL,
    enddate timestamp without time zone,
    startdate timestamp without time zone
);


--
-- Name: source_relation_fieldoccr; Type: TABLE; Schema: public; Owner: lrharvester
--

CREATE TABLE source_relation_fieldoccr (
    from_entity_id uuid NOT NULL,
    relation_type_id bigint NOT NULL,
    to_entity_id uuid NOT NULL,
    fieldoccr_id bigint NOT NULL
);


--
-- Name: field_type id; Type: DEFAULT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY field_type ALTER COLUMN id SET DEFAULT nextval('field_type_id_seq'::regclass);

--
-- Name: entity_relation_type_seq; Type: SEQUENCE SET; Schema: public; Owner: lrharvester
--

SELECT pg_catalog.setval('entity_relation_type_seq', 1, false);


--
-- Name: field_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: lrharvester
--

SELECT pg_catalog.setval('field_type_id_seq', 1, false);


--
-- Name: entity_fieldoccr entity_fieldoccr_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_fieldoccr
    ADD CONSTRAINT entity_fieldoccr_pkey PRIMARY KEY (entity_id, fieldoccr_id);


--
-- Name: entity entity_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity
    ADD CONSTRAINT entity_pkey PRIMARY KEY (uuid);


--
-- Name: entity_semantic_identifier entity_semantic_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_semantic_identifier
    ADD CONSTRAINT entity_semantic_identifier_pkey PRIMARY KEY (entity_id, semantic_id);


--
-- Name: entity_type entity_type_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_type
    ADD CONSTRAINT entity_type_pkey PRIMARY KEY (id);


--
-- Name: field_occurrence field_occurrence_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY field_occurrence
    ADD CONSTRAINT field_occurrence_pkey PRIMARY KEY (id);


--
-- Name: field_type field_type_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY field_type
    ADD CONSTRAINT field_type_pkey PRIMARY KEY (id);


--
-- Name: provenance provenance_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY provenance
    ADD CONSTRAINT provenance_pkey PRIMARY KEY (id);


--
-- Name: relation_fieldoccr relation_fieldoccr_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation_fieldoccr
    ADD CONSTRAINT relation_fieldoccr_pkey PRIMARY KEY (from_entity_id, relation_type_id, to_entity_id, fieldoccr_id);


--
-- Name: relation relation_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation
    ADD CONSTRAINT relation_pkey PRIMARY KEY (from_entity_id, relation_type_id, to_entity_id);


--
-- Name: relation_type relation_type_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation_type
    ADD CONSTRAINT relation_type_pkey PRIMARY KEY (id);


--
-- Name: semantic_identifier semantic_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY semantic_identifier
    ADD CONSTRAINT semantic_identifier_pkey PRIMARY KEY (id);


--
-- Name: source_entity_fieldoccr source_entity_fieldoccr_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity_fieldoccr
    ADD CONSTRAINT source_entity_fieldoccr_pkey PRIMARY KEY (entity_id, fieldoccr_id);


--
-- Name: source_entity source_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity
    ADD CONSTRAINT source_entity_pkey PRIMARY KEY (uuid);


--
-- Name: source_entity_semantic_identifier source_entity_semantic_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity_semantic_identifier
    ADD CONSTRAINT source_entity_semantic_identifier_pkey PRIMARY KEY (entity_id, semantic_id);


--
-- Name: source_relation_fieldoccr source_relation_fieldoccr_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_relation_fieldoccr
    ADD CONSTRAINT source_relation_fieldoccr_pkey PRIMARY KEY (from_entity_id, relation_type_id, to_entity_id, fieldoccr_id);


--
-- Name: source_relation source_relation_pkey; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_relation
    ADD CONSTRAINT source_relation_pkey PRIMARY KEY (from_entity_id, relation_type_id, to_entity_id);


--
-- Name: relation_type uk_dqprukb42qt2xmwu1vgg1oqsv; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation_type
    ADD CONSTRAINT uk_dqprukb42qt2xmwu1vgg1oqsv UNIQUE (name);


--
-- Name: entity_type uk_kg3s1d935edaf7me4vq9vv15v; Type: CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_type
    ADD CONSTRAINT uk_kg3s1d935edaf7me4vq9vv15v UNIQUE (name);


--
-- Name: efo_entity_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX efo_entity_id ON entity_fieldoccr USING btree (entity_id);


--
-- Name: efo_fieldoccr_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX efo_fieldoccr_id ON entity_fieldoccr USING btree (fieldoccr_id);


--
-- Name: esi_entity_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX esi_entity_id ON entity_semantic_identifier USING btree (entity_id);


--
-- Name: esi_semantic_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX esi_semantic_id ON entity_semantic_identifier USING btree (semantic_id);


--
-- Name: idx_final_entity_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX idx_final_entity_id ON source_entity USING btree (final_entity_id);


--
-- Name: relation_type_members; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX relation_type_members ON relation USING btree (relation_type_id, from_entity_id, to_entity_id);


--
-- Name: sfo_entity_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX sfo_entity_id ON source_entity_fieldoccr USING btree (entity_id);


--
-- Name: sfo_fieldoccr_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX sfo_fieldoccr_id ON source_entity_fieldoccr USING btree (fieldoccr_id);


--
-- Name: source_relation_type_members; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX source_relation_type_members ON source_relation USING btree (relation_type_id, from_entity_id, to_entity_id);


--
-- Name: ssi_entity_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX ssi_entity_id ON source_entity_semantic_identifier USING btree (entity_id);


--
-- Name: ssi_semantic_id; Type: INDEX; Schema: public; Owner: lrharvester
--

CREATE INDEX ssi_semantic_id ON source_entity_semantic_identifier USING btree (semantic_id);


CREATE INDEX se_provenance_id ON source_entity USING btree (provenance_id);


--
-- Name: source_relation_fieldoccr fk10s6vmwa91jkhcc3m14debj7k; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_relation_fieldoccr
    ADD CONSTRAINT fk10s6vmwa91jkhcc3m14debj7k FOREIGN KEY (fieldoccr_id) REFERENCES field_occurrence(id);


--
-- Name: source_entity fk1cg02lhoal5xq86jpj1a7qokg; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity
    ADD CONSTRAINT fk1cg02lhoal5xq86jpj1a7qokg FOREIGN KEY (entity_type_id) REFERENCES entity_type(id);


--
-- Name: entity fk21ec1ub943occfcpm2jaovtsa; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity
    ADD CONSTRAINT fk21ec1ub943occfcpm2jaovtsa FOREIGN KEY (entity_type_id) REFERENCES entity_type(id);


--
-- Name: source_entity_fieldoccr fk2f3wc4b3huh74134hloikiou7; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity_fieldoccr
    ADD CONSTRAINT fk2f3wc4b3huh74134hloikiou7 FOREIGN KEY (entity_id) REFERENCES source_entity(uuid);


--
-- Name: source_relation fk2tug80it3it1d7315h2x04fig; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_relation
    ADD CONSTRAINT fk2tug80it3it1d7315h2x04fig FOREIGN KEY (to_entity_id) REFERENCES source_entity(uuid);


--
-- Name: relation_type fk3is6dski9xnfyk1mo8cv14led; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation_type
    ADD CONSTRAINT fk3is6dski9xnfyk1mo8cv14led FOREIGN KEY (from_entity_id) REFERENCES entity_type(id);


--
-- Name: source_entity fk3obeh2naev2b3gyswvpvw433e; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity
    ADD CONSTRAINT fk3obeh2naev2b3gyswvpvw433e FOREIGN KEY (final_entity_id) REFERENCES entity(uuid);


--
-- Name: source_entity_semantic_identifier fk8u7995l8qeh56i34ij4jfm7ny; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity_semantic_identifier
    ADD CONSTRAINT fk8u7995l8qeh56i34ij4jfm7ny FOREIGN KEY (entity_id) REFERENCES source_entity(uuid);


--
-- Name: source_entity_semantic_identifier fk9bf1gs0tx86f4eewbws4hkytp; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity_semantic_identifier
    ADD CONSTRAINT fk9bf1gs0tx86f4eewbws4hkytp FOREIGN KEY (semantic_id) REFERENCES semantic_identifier(id);


--
-- Name: relation_fieldoccr fk9fdsesc6ey8c831brij4u1rob; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation_fieldoccr
    ADD CONSTRAINT fk9fdsesc6ey8c831brij4u1rob FOREIGN KEY (fieldoccr_id) REFERENCES field_occurrence(id);


--
-- Name: relation fk9kavjxgi0tpvju15iab7petiw; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation
    ADD CONSTRAINT fk9kavjxgi0tpvju15iab7petiw FOREIGN KEY (from_entity_id) REFERENCES entity(uuid);


--
-- Name: relation fk9wvqikvahl1a0x1xkcfdw42n; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation
    ADD CONSTRAINT fk9wvqikvahl1a0x1xkcfdw42n FOREIGN KEY (to_entity_id) REFERENCES entity(uuid);


--
-- Name: source_relation fka85ljpk6ps09u8nya2pvpfgvk; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_relation
    ADD CONSTRAINT fka85ljpk6ps09u8nya2pvpfgvk FOREIGN KEY (from_entity_id) REFERENCES source_entity(uuid);


--
-- Name: entity_fieldoccr fkcnvu6hyt4mihaxjsejgmhu15r; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_fieldoccr
    ADD CONSTRAINT fkcnvu6hyt4mihaxjsejgmhu15r FOREIGN KEY (fieldoccr_id) REFERENCES field_occurrence(id);


--
-- Name: field_type fkf1e4wfupyw60nca04lvdpchs0; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY field_type
    ADD CONSTRAINT fkf1e4wfupyw60nca04lvdpchs0 FOREIGN KEY (parent_field_type_id) REFERENCES field_type(id);


--
-- Name: entity_fieldoccr fkg85y6bnncn3q9y762wvrwj08u; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_fieldoccr
    ADD CONSTRAINT fkg85y6bnncn3q9y762wvrwj08u FOREIGN KEY (entity_id) REFERENCES entity(uuid);


--
-- Name: source_relation fkhr0udguiwn7dos2o77lwt0abj; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_relation
    ADD CONSTRAINT fkhr0udguiwn7dos2o77lwt0abj FOREIGN KEY (relation_type_id) REFERENCES relation_type(id);


--
-- Name: entity_semantic_identifier fkinjr1aqio6tuon2ypi6ixd4ao; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_semantic_identifier
    ADD CONSTRAINT fkinjr1aqio6tuon2ypi6ixd4ao FOREIGN KEY (entity_id) REFERENCES entity(uuid);


--
-- Name: source_entity_fieldoccr fkitn5f8xb60m8w8t5ppsu4wgff; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity_fieldoccr
    ADD CONSTRAINT fkitn5f8xb60m8w8t5ppsu4wgff FOREIGN KEY (fieldoccr_id) REFERENCES field_occurrence(id);


--
-- Name: relation_fieldoccr fkjottc07w9a00w4ta9u48br53m; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation_fieldoccr
    ADD CONSTRAINT fkjottc07w9a00w4ta9u48br53m FOREIGN KEY (from_entity_id, relation_type_id, to_entity_id) REFERENCES relation(from_entity_id, relation_type_id, to_entity_id);


--
-- Name: field_occurrence fklygjgmk42bw7il8p85svic8hg; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY field_occurrence
    ADD CONSTRAINT fklygjgmk42bw7il8p85svic8hg FOREIGN KEY (field_type_id) REFERENCES field_type(id);


--
-- Name: relation_type fkndcced7wia4vkdvhydsvi7rld; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation_type
    ADD CONSTRAINT fkndcced7wia4vkdvhydsvi7rld FOREIGN KEY (to_entity_id) REFERENCES entity_type(id);


--
-- Name: source_relation_fieldoccr fkntrxgvqcjsy3w7nb8xxcauh84; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_relation_fieldoccr
    ADD CONSTRAINT fkntrxgvqcjsy3w7nb8xxcauh84 FOREIGN KEY (from_entity_id, relation_type_id, to_entity_id) REFERENCES source_relation(from_entity_id, relation_type_id, to_entity_id);


--
-- Name: source_entity fknwk1uql6xtcgjny8k6nq8ja8j; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY source_entity
    ADD CONSTRAINT fknwk1uql6xtcgjny8k6nq8ja8j FOREIGN KEY (provenance_id) REFERENCES provenance(id);


--
-- Name: relation fks2nk3th0n2lygksxkloek4gd1; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY relation
    ADD CONSTRAINT fks2nk3th0n2lygksxkloek4gd1 FOREIGN KEY (relation_type_id) REFERENCES relation_type(id);


--
-- Name: entity_semantic_identifier fkstp4rub2i3fywyrbsebuwjosa; Type: FK CONSTRAINT; Schema: public; Owner: lrharvester
--

ALTER TABLE ONLY entity_semantic_identifier
    ADD CONSTRAINT fkstp4rub2i3fywyrbsebuwjosa FOREIGN KEY (semantic_id) REFERENCES semantic_identifier(id);

DROP PROCEDURE IF EXISTS merge_entity_relation_data(integer);

-- Procedure

CREATE PROCEDURE merge_entity_relation_data(INOUT ret integer)
    LANGUAGE sql
    AS $$	

	DELETE FROM entity_fieldoccr efo
	USING entity e
	WHERE efo.entity_id = e.uuid AND e.dirty = true;
	
	INSERT INTO entity_fieldoccr
	SELECT DISTINCT e.uuid, sef.fieldoccr_id
	FROM source_entity_fieldoccr sef, source_entity se, entity e
	WHERE e.dirty = TRUE AND se.deleted = FALSE AND sef.entity_id = se.uuid AND e.uuid = se.final_entity_id;
	
	INSERT INTO relation (relation_type_id, from_entity_id, to_entity_id, dirty)
	SELECT DISTINCT sr.relation_type_id, e1.uuid AS from_entity_id, e2.uuid AS to_entity_id, TRUE 
	FROM source_relation sr, source_entity se1, source_entity se2, entity e1, entity e2
	WHERE (e1.dirty = TRUE OR e2.dirty = TRUE) AND se1.deleted = FALSE AND se2.deleted = FALSE 
	AND sr.from_entity_id = se1.uuid AND sr.to_entity_id = se2.uuid 
	AND se1.final_entity_id = e1.uuid AND se2.final_entity_id = e2.uuid 
	AND NOT EXISTS (SELECT * FROM relation x WHERE x.relation_type_id = sr.relation_type_id AND x.from_entity_id = e1.uuid AND x.to_entity_id = e2.uuid );
	
	DELETE FROM relation_fieldoccr rfo
	USING relation r
	WHERE r.dirty = TRUE AND r.relation_type_id = rfo.relation_type_id AND r.from_entity_id = rfo.from_entity_id AND r.to_entity_id = rfo.to_entity_id;
	
	INSERT INTO relation_fieldoccr (from_entity_id, relation_type_id, to_entity_id, fieldoccr_id)
	SELECT DISTINCT r.from_entity_id, r.relation_type_id, r.to_entity_id,  sro.fieldoccr_id
	FROM relation r, source_entity se1, source_entity se2, source_relation_fieldoccr sro
	WHERE r.dirty = TRUE AND r.from_entity_id = se1.final_entity_id AND r.to_entity_id = se2.final_entity_id AND sro.from_entity_id = se1.uuid AND sro.to_entity_id = se2.uuid AND sro.relation_type_id = r.relation_type_id;
	
	UPDATE entity 
	SET dirty = FALSE
	WHERE dirty = TRUE;
	
	UPDATE relation 
	SET dirty = FALSE
	WHERE dirty = TRUE;
	
	SELECT 1;
	
$$;