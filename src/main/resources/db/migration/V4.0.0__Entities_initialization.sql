--
-- Create entities structure
--


DROP TABLE IF EXISTS relation_entity CASCADE;
ALTER TABLE IF EXISTS ONLY semantic_identifier DROP CONSTRAINT IF EXISTS fksgaqudetb9hymxmqolar0xwob;
ALTER TABLE IF EXISTS ONLY relation DROP CONSTRAINT IF EXISTS fks2nk3th0n2lygksxkloek4gd1;
ALTER TABLE IF EXISTS ONLY relation_type_member DROP CONSTRAINT IF EXISTS fkrme38lsngm3ggdmnymwc5w3ag;
ALTER TABLE IF EXISTS ONLY entity DROP CONSTRAINT IF EXISTS fkq4lvyy5hnj9vjvs9iiyv1tsu1;
ALTER TABLE IF EXISTS ONLY field_occurrence DROP CONSTRAINT IF EXISTS fklygjgmk42bw7il8p85svic8hg;
ALTER TABLE IF EXISTS ONLY entity_provenance DROP CONSTRAINT IF EXISTS fkj8h1dh05dt4fprpuh9wnx2gur;
ALTER TABLE IF EXISTS ONLY field_type DROP CONSTRAINT IF EXISTS fkf1e4wfupyw60nca04lvdpchs0;
ALTER TABLE IF EXISTS ONLY relation_type_member DROP CONSTRAINT IF EXISTS fke5s5jt69jomv84eu6ysx8yhms;
ALTER TABLE IF EXISTS ONLY relation DROP CONSTRAINT IF EXISTS fk9wvqikvahl1a0x1xkcfdw42n;
ALTER TABLE IF EXISTS ONLY relation DROP CONSTRAINT IF EXISTS fk9kavjxgi0tpvju15iab7petiw;
ALTER TABLE IF EXISTS ONLY entity_provenance DROP CONSTRAINT IF EXISTS fk5hmip8mfrm9tt5bflf09c3f5j;
ALTER TABLE IF EXISTS ONLY entity DROP CONSTRAINT IF EXISTS fk21ec1ub943occfcpm2jaovtsa;
DROP INDEX IF EXISTS relation_type_members;
DROP INDEX IF EXISTS field_occr_by_type_and_container;
ALTER TABLE IF EXISTS ONLY relation DROP CONSTRAINT IF EXISTS uk_sggxdjblk96dhmtor2rfcjbnc;
ALTER TABLE IF EXISTS ONLY entity_type DROP CONSTRAINT IF EXISTS uk_kg3s1d935edaf7me4vq9vv15v;
ALTER TABLE IF EXISTS ONLY relation_type DROP CONSTRAINT IF EXISTS uk_dqprukb42qt2xmwu1vgg1oqsv;
ALTER TABLE IF EXISTS ONLY entity DROP CONSTRAINT IF EXISTS uk_ckkkpbd1ayrdgjc77w54r8qp5;
ALTER TABLE IF EXISTS ONLY semantic_identifier DROP CONSTRAINT IF EXISTS semantic_identifier_pkey;
ALTER TABLE IF EXISTS ONLY relation_type DROP CONSTRAINT IF EXISTS relation_type_pkey;
ALTER TABLE IF EXISTS ONLY relation_type_member DROP CONSTRAINT IF EXISTS relation_type_member_pkey;
ALTER TABLE IF EXISTS ONLY relation DROP CONSTRAINT IF EXISTS relation_pkey;
ALTER TABLE IF EXISTS ONLY provenance DROP CONSTRAINT IF EXISTS provenance_str;
ALTER TABLE IF EXISTS ONLY provenance DROP CONSTRAINT IF EXISTS provenance_pkey;
ALTER TABLE IF EXISTS ONLY field_type DROP CONSTRAINT IF EXISTS field_type_pkey;
ALTER TABLE IF EXISTS ONLY field_occurrence DROP CONSTRAINT IF EXISTS field_occurrence_pkey;
ALTER TABLE IF EXISTS ONLY entity_type DROP CONSTRAINT IF EXISTS entity_type_pkey;
ALTER TABLE IF EXISTS ONLY entity_provenance DROP CONSTRAINT IF EXISTS entity_provenance_pkey;
ALTER TABLE IF EXISTS ONLY entity DROP CONSTRAINT IF EXISTS entity_pkey;
ALTER TABLE IF EXISTS field_type ALTER COLUMN id DROP DEFAULT;
DROP TABLE IF EXISTS semantic_identifier;
DROP TABLE IF EXISTS relation_type_member;
DROP TABLE IF EXISTS relation_type;
DROP TABLE IF EXISTS relation;
DROP SEQUENCE IF EXISTS provenance_seq;
DROP TABLE IF EXISTS provenance;
DROP SEQUENCE IF EXISTS field_type_id_seq;
DROP TABLE IF EXISTS field_type;
DROP TABLE IF EXISTS field_occurrence;
DROP SEQUENCE IF EXISTS field_occr_type_seq;
DROP TABLE IF EXISTS entity_type;
DROP SEQUENCE IF EXISTS entity_relation_type_seq;
DROP TABLE IF EXISTS entity_provenance;
DROP TABLE IF EXISTS entity;


--
-- Name: entity_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS entity_type (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255),
    CONSTRAINT entity_type_pkey PRIMARY KEY (id),
    CONSTRAINT uk_kg3s1d935edaf7me4vq9vv15v UNIQUE (name)
);

--
-- Name: entity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS entity (
    uuid uuid NOT NULL,
    duplicate_type integer,
    entity_type_id bigint,
    deduplicated_entity_id uuid,
    CONSTRAINT entity_pkey PRIMARY KEY (uuid),
    CONSTRAINT uk_ckkkpbd1ayrdgjc77w54r8qp5 UNIQUE (uuid),
    CONSTRAINT fk21ec1ub943occfcpm2jaovtsa FOREIGN KEY (entity_type_id) REFERENCES entity_type(id),
    CONSTRAINT fkq4lvyy5hnj9vjvs9iiyv1tsu1 FOREIGN KEY (deduplicated_entity_id) REFERENCES entity(uuid)
);


--
-- Name: provenance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS provenance (
    id bigint NOT NULL,
    last_update timestamp without time zone,
    provenance_str character varying(255),
    CONSTRAINT provenance_pkey PRIMARY KEY (id),
    CONSTRAINT provenance_str UNIQUE (provenance_str)
);


--
-- Name: provenance_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS provenance_seq
    START WITH 1
    INCREMENT BY 100
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: entity_provenance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS entity_provenance (
    entity_id uuid NOT NULL,
    provenance_id bigint NOT NULL,
    CONSTRAINT entity_provenance_pkey PRIMARY KEY (entity_id, provenance_id),
    CONSTRAINT fk5hmip8mfrm9tt5bflf09c3f5j FOREIGN KEY (entity_id) REFERENCES entity(uuid),
    CONSTRAINT fkj8h1dh05dt4fprpuh9wnx2gur FOREIGN KEY (provenance_id) REFERENCES provenance(id)
);


--
-- Name: entity_relation_type_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS entity_relation_type_seq
    START WITH 1
    INCREMENT BY 100
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: field_occr_type_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS field_occr_type_seq
    START WITH 1
    INCREMENT BY 100
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

--
-- Name: field_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS field_type (
    id bigint NOT NULL,
    description character varying(255),
    kind integer,
    maxoccurs integer,
    name character varying(255),
    entity_relation_type_id bigint,
    parent_field_type_id bigint,
    CONSTRAINT field_type_pkey PRIMARY KEY (id),
    CONSTRAINT fkf1e4wfupyw60nca04lvdpchs0 FOREIGN KEY (parent_field_type_id) REFERENCES field_type(id)
);


--
-- Name: field_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE IF NOT EXISTS field_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: field_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE field_type_id_seq OWNED BY field_type.id;

--
-- Name: field_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE IF EXISTS ONLY field_type ALTER COLUMN id SET DEFAULT nextval('field_type_id_seq'::regclass);

--
-- Name: field_occurrence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS field_occurrence (
    kind character varying(31) NOT NULL,
    id bigint NOT NULL,
    field_container_id uuid,
    field_type_id bigint,
    lang character varying(255),
    content text,
    CONSTRAINT field_occurrence_pkey PRIMARY KEY (id),
    CONSTRAINT fklygjgmk42bw7il8p85svic8hg FOREIGN KEY (field_type_id) REFERENCES field_type(id)
);


--
-- Name: relation_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS relation_type (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255),
    CONSTRAINT relation_type_pkey PRIMARY KEY (id),
    CONSTRAINT uk_dqprukb42qt2xmwu1vgg1oqsv UNIQUE (name)
);


--
-- Name: relation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS relation (
    uuid uuid NOT NULL,
    confidence double precision NOT NULL,
    enddate timestamp without time zone,
    from_entity_id uuid,
    relation_type_id bigint,
    startdate timestamp without time zone,
    to_entity_id uuid,
    CONSTRAINT relation_pkey PRIMARY KEY (uuid),
    CONSTRAINT uk_sggxdjblk96dhmtor2rfcjbnc UNIQUE (uuid),
    CONSTRAINT fk9kavjxgi0tpvju15iab7petiw FOREIGN KEY (from_entity_id) REFERENCES entity(uuid),
    CONSTRAINT fk9wvqikvahl1a0x1xkcfdw42n FOREIGN KEY (to_entity_id) REFERENCES entity(uuid),
    CONSTRAINT fks2nk3th0n2lygksxkloek4gd1 FOREIGN KEY (relation_type_id) REFERENCES relation_type(id)
);


--
-- Name: relation_type_member; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS relation_type_member (
    relation_type_id bigint NOT NULL,
    member_id bigint NOT NULL,
    name character varying(255) NOT NULL,
    CONSTRAINT relation_type_member_pkey PRIMARY KEY (relation_type_id, name),
    CONSTRAINT fke5s5jt69jomv84eu6ysx8yhms FOREIGN KEY (member_id) REFERENCES entity_type(id),
    CONSTRAINT fkrme38lsngm3ggdmnymwc5w3ag FOREIGN KEY (relation_type_id) REFERENCES relation_type(id)
);


--
-- Name: semantic_identifier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE IF NOT EXISTS semantic_identifier (
    entity_id uuid NOT NULL,
    semantic_id character varying(255) NOT NULL,
    CONSTRAINT semantic_identifier_pkey PRIMARY KEY (entity_id, semantic_id),
    CONSTRAINT fksgaqudetb9hymxmqolar0xwob FOREIGN KEY (entity_id) REFERENCES entity(uuid)
);




--
-- Name: field_occr_by_type_and_container; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS field_occr_by_type_and_container ON field_occurrence USING btree (field_type_id, field_container_id);


--
-- Name: relation_type_members; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX IF NOT EXISTS relation_type_members ON relation USING btree (relation_type_id, from_entity_id, to_entity_id);



