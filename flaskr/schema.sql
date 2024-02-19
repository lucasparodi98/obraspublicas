/*DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS inf_red;
DROP TABLE IF EXISTS departamentos;
DROP TABLE IF EXISTS provincias;
DROP TABLE IF EXISTS distritos;
DROP TABLE IF EXISTS estadosOP;*/
PRAGMA foreign_keys = OFF;

/*CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    user_type TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);*/

/*CREATE TABLE inf_red (
    id VARCHAR(20) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    link_archivos TEXT NOT NULL,
    documento VARCHAR(500) NOT NULL,
    fecha_documento DATE,
    titulo_correo TEXT,
    fecha_correo DATE,
    nombre_entidad TEXT NOT NULL,
    entidad VARCHAR(150) NOT NULL,
    proyecto TEXT NOT NULL,
    departamento VARCHAR (150) NOT NULL,
    provincia VARCHAR (150) NOT NULL,
    distrito VARCHAR (150) NOT NULL,
    contacto TEXT,
    correo_contacto TEXT,
    telefono_contacto TEXT,
    resumen_planta VARCHAR(10),
    fecha_respuesta DATE,
    tma INTEGER,
    estado_inf_red VARCHAR(60) NOT NULL,
    estado_proyecto VARCHAR(60),
    peso_kml VARCHAR(20),
    formulario_completado VARCHAR(50),
    inicio_obras TEXT,
    complejidad TEXT,
    json_coords TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id)
);*/

/*CREATE TABLE "presupuesto" (
	"id"	INTEGER,
	"cod_unico"	VARCHAR(20) NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"fecha_creacion"	TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"bautizo"	TEXT,
	"documento"	VARCHAR(500) NOT NULL,
	"fecha_documento"	DATE,
	"contacto"	TEXT,
	"correo_contacto"	TEXT,
	"telefono_contacto"	TEXT,
	"ip_madre"	VARCHAR(20),
	"fecha_creacion_ipmadre"	DATE,
	"estado_ipmadre_webPO"	VARCHAR(100),
	"eecc"	VARCHAR(50),
	"solicitudOC"	VARCHAR(150),
	"fecha_inicio_diseno"	DATE,
	"fecha_termino_diseno"	DATE,
	"fecha_entrega_ppto"	DATE,
	"nro_ppto"	VARCHAR(50),
	"montoIGV"	DECIMAL,
	"prioridad"	VARCHAR(100),
	"estado"	VARCHAR(500),
	"mes_pago_planificado"	VARCHAR(50),
	"nro_convenio"	VARCHAR(100),
	"fecha_firma_convenio"	DATE,
	"plazo_convenio"	VARCHAR(100),
	"tiempo"	VARCHAR(50),
	"fecha_caducidad"	DATE,
	"numero_factura"	NUMERIC,
	"fecha_pago_96"	DATE,
	"fecha_pago_4"	DATE,
	"mes_pago_oficial"	VARCHAR(50),
	"semana_pago_interno"	VARCHAR(50),
	"semana_pago_oficial"	VARCHAR(50),
	"bautizo_corto"	VARCHAR(250),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	FOREIGN KEY("cod_unico") REFERENCES "inf_red"("id"),
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE historial (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    cod_unico VARCHAR(20) NOT NULL,
    presupuesto_id INTEGER,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo VARCHAR(100),
    observacion TEXT,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (cod_unico) REFERENCES inf_red (id),
    FOREIGN KEY (presupuesto_id) REFERENCES presupuesto (id)
);*/
/*
CREATE TABLE estadosOP (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estado VARCHAR(500),
    grupo_estado VARCHAR(500),
    vista_gerencia VARCHAR(500),
    grupo_gestion VARCHAR(500),
    proceso VARCHAR(500),
    vista_direccion VARCHAR(500),
    grupo_estado VARCHAR(500),
    grupo_estado_general VARCHAR(500)
);*/

/*
CREATE TABLE departamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    departamento VARCHAR (150) NOT NULL,
    color VARCHAR (10),
    json_coords TEXT
);
*/
/*
CREATE TABLE provincias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    departamento VARCHAR (150) NOT NULL,
    provincia VARCHAR (150) NOT NULL,
    color VARCHAR (10),
    json_coords TEXT
);

CREATE TABLE distritos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    departamento VARCHAR (150) NOT NULL,
    provincia VARCHAR (150) NOT NULL,
    distrito VARCHAR (150) NOT NULL,
    color VARCHAR (10),
    json_coords TEXT
);*/

/*
INSERT INTO user (id, username, password, user_type, email)
VALUES (1, 'Admin', 'Admin', 'Admin', 'example@example.com')
*/

/*
CREATE TABLE info_webpo (
    ip_madre TEXT PRIMARY KEY,
    estado_ip TEXT ,
    fecha_recepcion DATE ,
    eecc TEXT ,
    pep TEXT ,
    situacion TEXT ,
    tipo_solicitud TEXT ,
    monto_actual DECIMAL ,
    estado_solicitud_actual TEXT ,
    solicitud_oc_actual DATE ,
    validacion_oc_actual DATE ,
    estado_firma TEXT ,
    monto_diseño_final DECIMAL ,
    monto_inicial DECIMAL ,
    solicitud_oc_creacion DATE ,
    validacion_oc_creacion DATE ,

);*/