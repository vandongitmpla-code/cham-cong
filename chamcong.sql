--
-- PostgreSQL database dump
--

-- Dumped from database version 17.3
-- Dumped by pg_dump version 17.3

-- Started on 2025-10-01 08:03:37

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 223 (class 1259 OID 24786)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO admin;

--
-- TOC entry 220 (class 1259 OID 24763)
-- Name: attendance_logs; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.attendance_logs (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    date date NOT NULL,
    checkin time without time zone,
    checkout time without time zone
);


ALTER TABLE public.attendance_logs OWNER TO admin;

--
-- TOC entry 219 (class 1259 OID 24762)
-- Name: attendance_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.attendance_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.attendance_logs_id_seq OWNER TO admin;

--
-- TOC entry 4829 (class 0 OID 0)
-- Dependencies: 219
-- Name: attendance_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.attendance_logs_id_seq OWNED BY public.attendance_logs.id;


--
-- TOC entry 218 (class 1259 OID 24754)
-- Name: employees; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    code character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    department character varying(100),
    contract_type character varying(50),
    salary_base double precision,
    team character varying(100),
    att_code character varying(50)
);


ALTER TABLE public.employees OWNER TO admin;

--
-- TOC entry 217 (class 1259 OID 24753)
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employees_id_seq OWNER TO admin;

--
-- TOC entry 4830 (class 0 OID 0)
-- Dependencies: 217
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- TOC entry 222 (class 1259 OID 24775)
-- Name: payrolls; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.payrolls (
    id integer NOT NULL,
    employee_id integer NOT NULL,
    month character varying(7) NOT NULL,
    working_days integer,
    absent_days integer,
    overtime_hours double precision,
    salary double precision
);


ALTER TABLE public.payrolls OWNER TO admin;

--
-- TOC entry 221 (class 1259 OID 24774)
-- Name: payrolls_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.payrolls_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payrolls_id_seq OWNER TO admin;

--
-- TOC entry 4831 (class 0 OID 0)
-- Dependencies: 221
-- Name: payrolls_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.payrolls_id_seq OWNED BY public.payrolls.id;


--
-- TOC entry 4656 (class 2604 OID 24766)
-- Name: attendance_logs id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.attendance_logs ALTER COLUMN id SET DEFAULT nextval('public.attendance_logs_id_seq'::regclass);


--
-- TOC entry 4655 (class 2604 OID 24757)
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- TOC entry 4657 (class 2604 OID 24778)
-- Name: payrolls id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payrolls ALTER COLUMN id SET DEFAULT nextval('public.payrolls_id_seq'::regclass);


--
-- TOC entry 4823 (class 0 OID 24786)
-- Dependencies: 223
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.alembic_version (version_num) FROM stdin;
1f499944be4e
\.


--
-- TOC entry 4820 (class 0 OID 24763)
-- Dependencies: 220
-- Data for Name: attendance_logs; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.attendance_logs (id, employee_id, date, checkin, checkout) FROM stdin;
\.


--
-- TOC entry 4818 (class 0 OID 24754)
-- Dependencies: 218
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.employees (id, code, name, department, contract_type, salary_base, team, att_code) FROM stdin;
2	DUYVD	Võ Đức Duy	R&D	HDLD	0	nan	1
3	QUYPG	Phan Gia Quý	R&D	HDLD	0	nan	2
4	NGANNTH	Nguyễn Thị Hữu Ngân	R&D	HDLD	0	VP	3
5	GIANGTT	Trịnh Thúy Giang	R&D	HDLD	0	VP	4
6	TRINHVTD	Văn Thị Diệu Trinh	R&D	HDLD	0	VP	5
7	GIAONTQ	Nguyễn Thị Quỳnh Giao	R&D	HDLD	0	VP	6
8	HOACHLV	Lê Văn Hoạch	R&D	HDTV	0	VP	7
9	ANLV	Lê Văn An	Farm	HDLD	0	nan	8
10	DONGTV	Trần Văn Đồng	Farm	HDLD	0	Cơ điện	9
11	HOALS	Lâm Sỹ Hòa	Farm	HDLD	0	Cơ điện	10
12	DANHNT	Nguyễn Trọng Danh	Farm	HDLD	0	Cơ điện	11
13	TRONGVV	Võ Văn Trọng	Farm	HDLD	0	Cơ điện	12
14	TUANNM	Nguyễn Mạnh Tuấn	Farm	HDLD	0	Cơ điện	13
15	QUYCH	Châu Hồng Quy	Farm	HDLD	0	Giống	14
16	QUOCCH	Châu Thành Quốc	Farm	HDTV	0	Giống	15
17	NHANNV	Nguyễn Văn Nhân	Farm	HDLD	0	A14	16
18	LAMLV	Lê Văn Lam	Farm	HDLD	0	A14	17
19	TRUCDT	Dương Thanh Trúc	Farm	HDLD	0	A14	18
20	GIANGNT	Nguyễn Thanh Giang	Farm	HDLD	0	A14	19
21	HUNGNV	Nguyễn Văn Hùng	Farm	HDLD	0	A14	20
22	SANGTV	Trần Văn Sang	Farm	HDLD	0	A14	21
23	BAYPV	Phạm Văn Bảy	Farm	HDLD	0	A14	22
24	XAVV	Võ Văn Xá	Farm	HDLD	0	A14	23
25	TAIDT	Đặng Thành Tài	Farm	HDLD	0	A14	24
26	HUNGDV	Đặng Việt Hùng	Farm	HDTV	0	A14	25
27	CUONGHV	Hồ Văn Cường 	Farm	HDLD	0	A14	26
28	GIAUTN	Trịnh Ngọc Giàu	Farm	HDLD	0	A14	27
29	MINHTD	Tưởng Đức Minh	Farm	HDLD	0	A15	28
30	TIENNM02	Nguyễn Minh Tiến	Farm	HDLD	0	A15	29
31	THANHNV	Nguyễn Văn Thành	Farm	HDLD	0	A15	30
32	PHUONGDV	Đào Văn Phương	Farm	HDLD	0	A15	31
33	GIANV	Nguyễn Văn Gia	Farm	HDLD	0	A15	32
34	CONGDT	Dương Thành Công	Farm	HDLD	0	A15	33
35	THUANDV	Dương Văn Thuận	Farm	HDLD	0	A15	34
36	DUNN	Nguyễn Nhàn Du	Farm	HDLD	0	A15	35
37	MENTV	Trần Văn Mến 	Farm	HDLD	0	A15	36
38	DIENLH	Lê Hoài Diên 	Farm	HDLD	0	A15	37
39	DAYTV	Trần Văn Đầy	Farm	HDTV	0	A15	38
40	THACHLH	Lương Hoàng Thạch	Farm	HDTV	0	A15	39
41	NAMNH	Nguyễn Hào Nam	Farm	CTV	0	A15	40
42	TAOMC	Mai Chí Tạo	Farm	CTV	0	A15	41
43	LINHTN	Tô Nhựt Linh	Farm	CTV	0	A15	42
44	KHOAPN	Phạm Nhựt Khoa	Farm	CTV	0	A15	43
45	TIENNM01	Nguyễn Minh Tiến	Farm	HDLD	0	A16	44
46	SONVV	Võ Văn Sơn	Farm	HDLD	0	A16	45
47	LUANHM	Huỳnh Minh Luân	Farm	HDLD	0	A16	46
48	THUONGDH	Dương Hoàng Thương	Farm	HDLD	0	A16	47
49	TIENLN	Lê Nhất Tiến	Farm	HDLD	0	A16	48
50	LAMNH	Nguyễn Hữu Lâm	Farm	HDLD	0	A16	49
51	PHONGHT	Hồ Thanh Phong	Farm	HDLD	0	A16	50
52	QUANGPQN	Phan Quốc Nhật Quang	Farm	HDLD	0	A16	51
53	PHUPV	Phạm Văn Phú	Farm	HDLD	0	A16	52
54	DUONGPV	Phạm Văn Dương	Farm	HDLD	0	A16	53
55	ANHLVH	Lê Văn Hùng Anh	Farm	HDLD	0	A16	54
56	PHATPM	Phan Minh Phát	Farm	CTV	0	A16	55
57	MINHTV	Trần Văn Minh	Farm	HDTV	0	A15	56
\.


--
-- TOC entry 4822 (class 0 OID 24775)
-- Dependencies: 222
-- Data for Name: payrolls; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.payrolls (id, employee_id, month, working_days, absent_days, overtime_hours, salary) FROM stdin;
\.


--
-- TOC entry 4832 (class 0 OID 0)
-- Dependencies: 219
-- Name: attendance_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.attendance_logs_id_seq', 1, false);


--
-- TOC entry 4833 (class 0 OID 0)
-- Dependencies: 217
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.employees_id_seq', 59, true);


--
-- TOC entry 4834 (class 0 OID 0)
-- Dependencies: 221
-- Name: payrolls_id_seq; Type: SEQUENCE SET; Schema: public; Owner: admin
--

SELECT pg_catalog.setval('public.payrolls_id_seq', 1, false);


--
-- TOC entry 4669 (class 2606 OID 24790)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 4665 (class 2606 OID 24768)
-- Name: attendance_logs attendance_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.attendance_logs
    ADD CONSTRAINT attendance_logs_pkey PRIMARY KEY (id);


--
-- TOC entry 4659 (class 2606 OID 24792)
-- Name: employees employees_att_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_att_code_key UNIQUE (att_code);


--
-- TOC entry 4661 (class 2606 OID 24761)
-- Name: employees employees_code_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_code_key UNIQUE (code);


--
-- TOC entry 4663 (class 2606 OID 24759)
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- TOC entry 4667 (class 2606 OID 24780)
-- Name: payrolls payrolls_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payrolls
    ADD CONSTRAINT payrolls_pkey PRIMARY KEY (id);


--
-- TOC entry 4670 (class 2606 OID 24769)
-- Name: attendance_logs attendance_logs_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.attendance_logs
    ADD CONSTRAINT attendance_logs_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- TOC entry 4671 (class 2606 OID 24781)
-- Name: payrolls payrolls_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.payrolls
    ADD CONSTRAINT payrolls_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


-- Completed on 2025-10-01 08:03:37

--
-- PostgreSQL database dump complete
--

