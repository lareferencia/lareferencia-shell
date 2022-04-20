
--
-- Name: transformer; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS transformer (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255) NOT NULL,
    CONSTRAINT transformer_pkey PRIMARY KEY (id)
);


--
-- Name: transformer_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS transformer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transformer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS transformer_id_seq OWNED BY transformer.id;

--
-- Name: transformer id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY transformer ALTER COLUMN id SET DEFAULT nextval('transformer_id_seq'::regclass);

--
-- Name: transformerrule; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS transformerrule (
    id bigint NOT NULL,
    jsonserialization text,
    description character varying(255),
    name character varying(255) NOT NULL,
    runorder integer NOT NULL,
    transformer_id bigint,
    CONSTRAINT transformerrule_pkey PRIMARY KEY (id),
    CONSTRAINT fkbueretrgfy97gyw05cvbpdv6g FOREIGN KEY (transformer_id) REFERENCES transformer(id)
);


--
-- Name: transformerrule_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS transformerrule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transformerrule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS transformerrule_id_seq OWNED BY transformerrule.id;

--
-- Name: transformerrule id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY transformerrule ALTER COLUMN id SET DEFAULT nextval('transformerrule_id_seq'::regclass);


--
-- Name: validator; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS validator (
    id bigint NOT NULL,
    description character varying(255),
    name character varying(255) NOT NULL,
    CONSTRAINT validator_pkey PRIMARY KEY (id)
);


--
-- Name: validator_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS validator_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: validator_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS validator_id_seq OWNED BY validator.id;

--
-- Name: validator id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY validator ALTER COLUMN id SET DEFAULT nextval('validator_id_seq'::regclass);


--
-- Name: validatorrule; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS validatorrule (
    id bigint NOT NULL,
    jsonserialization text,
    description character varying(255),
    mandatory boolean NOT NULL,
    name character varying(255) NOT NULL,
    quantifier integer NOT NULL,
    validator_id bigint,
    CONSTRAINT validatorrule_pkey PRIMARY KEY (id),
    CONSTRAINT fk8g1xrgw6x1rnhse1jhr9v2sai FOREIGN KEY (validator_id) REFERENCES validator(id)
);


--
-- Name: validatorrule_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS validatorrule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: validatorrule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS validatorrule_id_seq OWNED BY validatorrule.id;

--
-- Name: validatorrule id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY validatorrule ALTER COLUMN id SET DEFAULT nextval('validatorrule_id_seq'::regclass);


--
-- Name: network; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS network (
    id bigint NOT NULL,
    acronym character varying(20) NOT NULL,
    attributesjsonserialization text,
    institutionacronym character varying(255),
    institutionname character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    published boolean NOT NULL,
    schedulecronexpression character varying(255),
    secondary_transformer_id bigint,
    transformer_id bigint,
    validator_id bigint,
    CONSTRAINT network_pkey PRIMARY KEY (id),
    CONSTRAINT uk_g8pr1g502c72o0tii4ebxgfcp UNIQUE (acronym),
    CONSTRAINT fkbbkgd5g0hj337vag34y4obfni FOREIGN KEY (validator_id) REFERENCES validator(id),
    CONSTRAINT fkd2dwqqyr0lkyvmmo12vy2poru FOREIGN KEY (secondary_transformer_id) REFERENCES transformer(id)
);


--
-- Name: network_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS network_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: network_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS network_id_seq OWNED BY network.id;


--
-- Name: network id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY network ALTER COLUMN id SET DEFAULT nextval('network_id_seq'::regclass);

--
-- Name: networkproperty; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS networkproperty (
    id bigint NOT NULL,
    name character varying(255),
    value boolean NOT NULL,
    network_id bigint,
    CONSTRAINT networkproperty_pkey PRIMARY KEY (id),
    CONSTRAINT fks1kbku7oldqw89i1jse25bxo0 FOREIGN KEY (network_id) REFERENCES network(id)
);


--
-- Name: networkproperty_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS networkproperty_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: networkproperty_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS networkproperty_id_seq OWNED BY networkproperty.id;

--
-- Name: networkproperty id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY networkproperty ALTER COLUMN id SET DEFAULT nextval('networkproperty_id_seq'::regclass);


--
-- Name: networksnapshot; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS networksnapshot (
    id bigint NOT NULL,
    deleted boolean NOT NULL,
    endtime timestamp without time zone,
    indexstatus integer NOT NULL,
    resumptiontoken character varying(255),
    size integer NOT NULL,
    starttime timestamp without time zone NOT NULL,
    status integer NOT NULL,
    transformedsize integer NOT NULL,
    validsize integer NOT NULL,
    network_id bigint,
    CONSTRAINT networksnapshot_pkey PRIMARY KEY (id),
    CONSTRAINT fks8wjtppucgkji6it4luvoc0wm FOREIGN KEY (network_id) REFERENCES network(id)
);


--
-- Name: networksnapshot_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS networksnapshot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: networksnapshot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS networksnapshot_id_seq OWNED BY networksnapshot.id;

--
-- Name: networksnapshot id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY networksnapshot ALTER COLUMN id SET DEFAULT nextval('networksnapshot_id_seq'::regclass);


--
-- Name: networksnapshotlog; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS networksnapshotlog (
    id bigint NOT NULL,
    message text NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    snapshot_id bigint NOT NULL,
    CONSTRAINT networksnapshotlog_pkey PRIMARY KEY (id),
    CONSTRAINT fkr7nf4n9k9w0vc1gmiltfljnct FOREIGN KEY (snapshot_id) REFERENCES networksnapshot(id)
);


--
-- Name: networksnapshotlog_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS networksnapshotlog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: networksnapshotlog_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS networksnapshotlog_id_seq OWNED BY networksnapshotlog.id;


--
-- Name: networksnapshotlog id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY networksnapshotlog ALTER COLUMN id SET DEFAULT nextval('networksnapshotlog_id_seq'::regclass);


--
-- Name: oaibitstream; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS oaibitstream (
    checksum character varying(255) NOT NULL,
    identifier character varying(255) NOT NULL,
    datestamp timestamp without time zone NOT NULL,
    filename character varying(255) NOT NULL,
    fulltext text,
    mime character varying(255) NOT NULL,
    sid integer NOT NULL,
    status integer NOT NULL,
    type character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    network_id bigint NOT NULL,
    CONSTRAINT oaibitstream_pkey PRIMARY KEY (checksum, identifier, network_id),
    CONSTRAINT fki631xlh52ite94886rdm6gbsg FOREIGN KEY (network_id) REFERENCES network(id)
);


--
-- Name: oaiorigin; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS oaiorigin (
    id bigint NOT NULL,
    metadataprefix character varying(255) NOT NULL,
    name character varying(255),
    uri character varying(255) NOT NULL,
    network_id bigint,
    CONSTRAINT oaiorigin_pkey PRIMARY KEY (id),
    CONSTRAINT fkedfl845q9ba3c5dinmgl90l75 FOREIGN KEY (network_id) REFERENCES network(id)
);


--
-- Name: oaiorigin_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS oaiorigin_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oaiorigin_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS oaiorigin_id_seq OWNED BY oaiorigin.id;



--
-- Name: oaiorigin id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY oaiorigin ALTER COLUMN id SET DEFAULT nextval('oaiorigin_id_seq'::regclass);



--
-- Name: oairecord; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS oairecord (
    id bigint NOT NULL,
    datestamp timestamp without time zone NOT NULL,
    identifier character varying(255) NOT NULL,
    originalxml text,
    publishedxml text,
    status integer NOT NULL,
    wastransformed boolean NOT NULL,
    origin_id bigint NOT NULL,
    snapshot_id bigint NOT NULL,
    CONSTRAINT oairecord_pkey PRIMARY KEY (id),
    CONSTRAINT fkfeww7oucr1rx6ufamawue2ga7 FOREIGN KEY (snapshot_id) REFERENCES networksnapshot(id),
    CONSTRAINT fkjbdjd0g2p06fsbyhjmo4cq4ij FOREIGN KEY (origin_id) REFERENCES oaiorigin(id)
);


--
-- Name: oairecord_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS oairecord_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oairecord_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS oairecord_id_seq OWNED BY oairecord.id;


--
-- Name: oairecord id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY oairecord ALTER COLUMN id SET DEFAULT nextval('oairecord_id_seq'::regclass);

--
-- Name: oaiset; Type: TABLE; Schema: public; 
--

CREATE TABLE IF NOT EXISTS oaiset (
    id bigint NOT NULL,
    name character varying(255),
    spec character varying(255) NOT NULL,
    origin_id bigint,
    CONSTRAINT oaiset_pkey PRIMARY KEY (id),
    CONSTRAINT fkqo3ps8oxo05yejjfwxpi1heyu FOREIGN KEY (origin_id) REFERENCES oaiorigin(id)
);


--
-- Name: oaiset_id_seq; Type: SEQUENCE; Schema: public; 
--

CREATE SEQUENCE IF NOT EXISTS oaiset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: oaiset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; 
--

ALTER SEQUENCE IF EXISTS oaiset_id_seq OWNED BY oaiset.id;

--
-- Name: oaiset id; Type: DEFAULT; Schema: public; 
--

ALTER TABLE IF EXISTS ONLY oaiset ALTER COLUMN id SET DEFAULT nextval('oaiset_id_seq'::regclass);

