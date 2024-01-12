-- Create indices for optimizing queries on OAIRecord table

BEGIN;

-- DROP ALL TABLES AND SEQUENCES
DROP TABLE IF EXISTS public.entity CASCADE;
DROP TABLE IF EXISTS public.entity_semantic_identifier CASCADE;
DROP TABLE IF EXISTS public.entity_type CASCADE;
DROP TABLE IF EXISTS public.field_type CASCADE;
DROP TABLE IF EXISTS public.provenance CASCADE;
DROP TABLE IF EXISTS public.relation_type CASCADE;
DROP TABLE IF EXISTS public.semantic_identifier CASCADE;
DROP TABLE IF EXISTS public.source_entity CASCADE;
DROP TABLE IF EXISTS public.source_entity_semantic_identifier CASCADE;
DROP SEQUENCE IF EXISTS public.field_type_id_seq CASCADE;


--
-- TOC entry 211 (class 1259 OID 306435)
-- Name: entity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity (
    uuid uuid NOT NULL,
    fieldvalues text,
    entity_type_id bigint,
    dirty boolean,
    relations text
);


--
-- TOC entry 212 (class 1259 OID 306442)
-- Name: entity_semantic_identifier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_semantic_identifier (
    entity_id uuid NOT NULL,
    semantic_id character varying(255) NOT NULL
);


--
-- TOC entry 213 (class 1259 OID 306447)
-- Name: entity_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_type (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255)
);


--
-- TOC entry 215 (class 1259 OID 306455)
-- Name: field_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.field_type (
    id bigint NOT NULL,
    description character varying(255),
    kind integer,
    maxoccurs integer,
    name character varying(255),
    subfields text,
    entity_relation_type_id bigint
);


--
-- TOC entry 214 (class 1259 OID 306454)
-- Name: field_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.field_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3421 (class 0 OID 0)
-- Dependencies: 214
-- Name: field_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.field_type_id_seq OWNED BY public.field_type.id;


--
-- TOC entry 225 (class 1259 OID 306507)
-- Name: provenance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provenance (
    record character varying(255) NOT NULL,
    source character varying(255) NOT NULL,
    last_update timestamp without time zone
);


--
-- TOC entry 226 (class 1259 OID 306514)
-- Name: relation_type; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.relation_type (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255),
    from_entity_id bigint,
    to_entity_id bigint
);


--
-- TOC entry 227 (class 1259 OID 306521)
-- Name: semantic_identifier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.semantic_identifier (
    semantic_id character varying(255) NOT NULL
);


--
-- TOC entry 228 (class 1259 OID 306526)
-- Name: source_entity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.source_entity (
    uuid uuid NOT NULL,
    fieldvalues text,
    entity_type_id bigint,
    final_entity_id uuid,
    record character varying(255),
    source character varying(255)
);


--
-- TOC entry 229 (class 1259 OID 306533)
-- Name: source_entity_semantic_identifier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.source_entity_semantic_identifier (
    entity_id uuid NOT NULL,
    semantic_id character varying(255) NOT NULL
);


--
-- TOC entry 3229 (class 2604 OID 306458)
-- Name: field_type id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_type ALTER COLUMN id SET DEFAULT nextval('public.field_type_id_seq'::regclass);


SELECT pg_catalog.setval('public.field_type_id_seq', 1, false);


--
-- TOC entry 3231 (class 2606 OID 306441)
-- Name: entity entity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity
    ADD CONSTRAINT entity_pkey PRIMARY KEY (uuid);


--
-- TOC entry 3233 (class 2606 OID 306446)
-- Name: entity_semantic_identifier entity_semantic_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_semantic_identifier
    ADD CONSTRAINT entity_semantic_identifier_pkey PRIMARY KEY (entity_id, semantic_id);


--
-- TOC entry 3237 (class 2606 OID 306453)
-- Name: entity_type entity_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_type
    ADD CONSTRAINT entity_type_pkey PRIMARY KEY (id);


--
-- TOC entry 3241 (class 2606 OID 306462)
-- Name: field_type field_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.field_type
    ADD CONSTRAINT field_type_pkey PRIMARY KEY (id);


--
-- TOC entry 3243 (class 2606 OID 306513)
-- Name: provenance provenance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provenance
    ADD CONSTRAINT provenance_pkey PRIMARY KEY (record, source);


--
-- TOC entry 3245 (class 2606 OID 306520)
-- Name: relation_type relation_type_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relation_type
    ADD CONSTRAINT relation_type_pkey PRIMARY KEY (id);


--
-- TOC entry 3249 (class 2606 OID 306525)
-- Name: semantic_identifier semantic_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_identifier
    ADD CONSTRAINT semantic_identifier_pkey PRIMARY KEY (semantic_id);


--
-- TOC entry 3252 (class 2606 OID 306532)
-- Name: source_entity source_entity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_entity
    ADD CONSTRAINT source_entity_pkey PRIMARY KEY (uuid);


--
-- TOC entry 3254 (class 2606 OID 306537)
-- Name: source_entity_semantic_identifier source_entity_semantic_identifier_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_entity_semantic_identifier
    ADD CONSTRAINT source_entity_semantic_identifier_pkey PRIMARY KEY (entity_id, semantic_id);


--
-- TOC entry 3247 (class 2606 OID 306581)
-- Name: relation_type uk_dqprukb42qt2xmwu1vgg1oqsv; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relation_type
    ADD CONSTRAINT uk_dqprukb42qt2xmwu1vgg1oqsv UNIQUE (name);


--
-- TOC entry 3239 (class 2606 OID 306577)
-- Name: entity_type uk_kg3s1d935edaf7me4vq9vv15v; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_type
    ADD CONSTRAINT uk_kg3s1d935edaf7me4vq9vv15v UNIQUE (name);


--
-- TOC entry 3234 (class 1259 OID 306574)
-- Name: esi_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX esi_entity_id ON public.entity_semantic_identifier USING btree (entity_id);


--
-- TOC entry 3235 (class 1259 OID 306575)
-- Name: esi_semantic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX esi_semantic_id ON public.entity_semantic_identifier USING btree (semantic_id);


--
-- TOC entry 3250 (class 1259 OID 306582)
-- Name: idx_final_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_final_entity_id ON public.source_entity USING btree (final_entity_id);


--
-- TOC entry 3255 (class 1259 OID 306583)
-- Name: ssi_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ssi_entity_id ON public.source_entity_semantic_identifier USING btree (entity_id);


--
-- TOC entry 3256 (class 1259 OID 306584)
-- Name: ssi_semantic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ssi_semantic_id ON public.source_entity_semantic_identifier USING btree (semantic_id);


--
-- TOC entry 3262 (class 2606 OID 306650)
-- Name: source_entity fk1cg02lhoal5xq86jpj1a7qokg; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_entity
    ADD CONSTRAINT fk1cg02lhoal5xq86jpj1a7qokg FOREIGN KEY (entity_type_id) REFERENCES public.entity_type(id);


--
-- TOC entry 3257 (class 2606 OID 306585)
-- Name: entity fk21ec1ub943occfcpm2jaovtsa; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity
    ADD CONSTRAINT fk21ec1ub943occfcpm2jaovtsa FOREIGN KEY (entity_type_id) REFERENCES public.entity_type(id);


--
-- TOC entry 3260 (class 2606 OID 306640)
-- Name: relation_type fk3is6dski9xnfyk1mo8cv14led; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relation_type
    ADD CONSTRAINT fk3is6dski9xnfyk1mo8cv14led FOREIGN KEY (from_entity_id) REFERENCES public.entity_type(id);


--
-- TOC entry 3264 (class 2606 OID 306660)
-- Name: source_entity fk3lalwvsqjam4yspppv29kpgro; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_entity
    ADD CONSTRAINT fk3lalwvsqjam4yspppv29kpgro FOREIGN KEY (record, source) REFERENCES public.provenance(record, source);


--
-- TOC entry 3263 (class 2606 OID 306655)
-- Name: source_entity fk3obeh2naev2b3gyswvpvw433e; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_entity
    ADD CONSTRAINT fk3obeh2naev2b3gyswvpvw433e FOREIGN KEY (final_entity_id) REFERENCES public.entity(uuid);


--
-- TOC entry 3266 (class 2606 OID 306670)
-- Name: source_entity_semantic_identifier fk8u7995l8qeh56i34ij4jfm7ny; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_entity_semantic_identifier
    ADD CONSTRAINT fk8u7995l8qeh56i34ij4jfm7ny FOREIGN KEY (entity_id) REFERENCES public.source_entity(uuid);


--
-- TOC entry 3265 (class 2606 OID 306665)
-- Name: source_entity_semantic_identifier fk9bf1gs0tx86f4eewbws4hkytp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_entity_semantic_identifier
    ADD CONSTRAINT fk9bf1gs0tx86f4eewbws4hkytp FOREIGN KEY (semantic_id) REFERENCES public.semantic_identifier(semantic_id);


--
-- TOC entry 3259 (class 2606 OID 306595)
-- Name: entity_semantic_identifier fkinjr1aqio6tuon2ypi6ixd4ao; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_semantic_identifier
    ADD CONSTRAINT fkinjr1aqio6tuon2ypi6ixd4ao FOREIGN KEY (entity_id) REFERENCES public.entity(uuid);


--
-- TOC entry 3261 (class 2606 OID 306645)
-- Name: relation_type fkndcced7wia4vkdvhydsvi7rld; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relation_type
    ADD CONSTRAINT fkndcced7wia4vkdvhydsvi7rld FOREIGN KEY (to_entity_id) REFERENCES public.entity_type(id);


--
-- TOC entry 3258 (class 2606 OID 306590)
-- Name: entity_semantic_identifier fkstp4rub2i3fywyrbsebuwjosa; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_semantic_identifier
    ADD CONSTRAINT fkstp4rub2i3fywyrbsebuwjosa FOREIGN KEY (semantic_id) REFERENCES public.semantic_identifier(semantic_id);



COMMIT;
