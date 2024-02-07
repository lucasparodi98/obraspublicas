import re
import json
import os
import folium
import pandas as pd
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import datetime
from pykml import parser
from folium import plugins
from flaskr.funciones import *

bp = Blueprint('presupuesto', __name__)

list_mes_pago = ['Enero 2024', 'Febrero 2024', 'Marzo 2024', 'Abril 2024', 'Mayo 2024', 'Junio 2024', 
                 'Julio 2024', 'Agosto 2024', 'Setiembre 2024', 'Octubre 2024', 'Noviembre 2024',
                 'Diciembre 2024', '2025', 'Enero 2023', 'Febrero 2023', 'Marzo 2023', 'Abril 2023', 
                 'Mayo 2023', 'Junio 2023', 'Julio 2023', 'Agosto 2023', 'Setiembre 2023', 'Octubre 2023', 
                 'Noviembre 2023', 'Diciembre 2023']

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ['csv']

def get_presupuesto(id, check_user=True):
    presupuesto = get_db().execute(
        """
        SELECT  id, cod_unico, user_id, fecha_creacion, bautizo, documento, fecha_documento, contacto, correo_contacto, telefono_contacto, ip_madre, fecha_creacion_ipmadre,
                estado_ipmadre_webPO, eecc, solicitudOC, fecha_inicio_diseno, fecha_termino_diseno, fecha_entrega_ppto, nro_ppto, montoIGV, prioridad, estado, 
                mes_pago_planificado, nro_convenio, fecha_firma_convenio, plazo_convenio, tiempo, fecha_caducidad, numero_factura, fecha_pago_96, fecha_pago_4, 
                mes_pago_oficial, semana_pago_interno, semana_pago_oficial, bautizo_corto
        FROM presupuesto
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    if presupuesto is None:
        abort(404, f"Presupuesto id {id} doesn't exist.")

    return presupuesto

@bp.route('/presupuesto/<string:option>')
@login_required
def indexPresupuesto(option):
    db = get_db()
    title = 'Gestión'
    if option == 'ver_todo':
        presupuestos = db.execute(
            """
            SELECT p.id, p.cod_unico, p.fecha_creacion, p.bautizo, p.ip_madre, p.montoIGV, p.prioridad, p.estado, p.mes_pago_planificado, p.fecha_pago_96, e.grupo_gestion
            FROM presupuesto p 
            LEFT JOIN inf_red i ON i.id = p.cod_unico
            LEFT JOIN estadosOP e ON e.estado = p.estado
            JOIN user u ON i.user_id = u.id
            ORDER BY p.fecha_creacion DESC
            """
        ).fetchall()
        title = 'Gestión de Diseño - Presupuesto - Convenio'
    elif option == 'pend_ip':
        presupuestos = db.execute(
            """
            SELECT p.id, p.cod_unico, p.fecha_creacion, p.bautizo, p.ip_madre, p.montoIGV, p.prioridad, p.estado, p.mes_pago_planificado, p.fecha_pago_96, e.grupo_gestion
            FROM presupuesto p 
            LEFT JOIN inf_red i ON i.id = p.cod_unico
            LEFT JOIN estadosOP e ON e.estado = p.estado
            JOIN user u ON i.user_id = u.id
            WHERE e.grupo_estado_general = 'Generar IP Madre'
            ORDER BY p.fecha_creacion DESC
            """
        ).fetchall()
        title = 'Pendiente Generar IP Madre'
    elif option == 'pend_oc':
        presupuestos = db.execute(
            """
            SELECT p.id, p.cod_unico, p.fecha_creacion, p.bautizo, p.ip_madre, p.montoIGV, p.prioridad, p.estado, p.mes_pago_planificado, p.fecha_pago_96, e.grupo_gestion
            FROM presupuesto p 
            LEFT JOIN inf_red i ON i.id = p.cod_unico
            LEFT JOIN estadosOP e ON e.estado = p.estado
            JOIN user u ON i.user_id = u.id
            WHERE e.grupo_estado_general = 'Pendiente OC de Diseño'
            ORDER BY p.fecha_creacion DESC
            """
        ).fetchall()
        title = 'Pendiente Generar OC de Diseño'
    elif option == 'diseno':
        presupuestos = db.execute(
            """
            SELECT p.id, p.cod_unico, p.fecha_creacion, p.bautizo, p.ip_madre, p.montoIGV, p.prioridad, p.estado, p.mes_pago_planificado, p.fecha_pago_96, e.grupo_gestion
            FROM presupuesto p 
            LEFT JOIN inf_red i ON i.id = p.cod_unico
            LEFT JOIN estadosOP e ON e.estado = p.estado
            JOIN user u ON i.user_id = u.id
            WHERE e.grupo_estado_general = 'En proceso de Diseño'
            ORDER BY p.fecha_creacion DESC
            """
        ).fetchall()
        title = 'Gestión de Diseño'
    elif option == 'presupuesto':
        presupuestos = db.execute(
            """
            SELECT p.id, p.cod_unico, p.fecha_creacion, p.bautizo, p.ip_madre, p.montoIGV, p.prioridad, p.estado, p.mes_pago_planificado, p.fecha_pago_96, e.grupo_gestion
            FROM presupuesto p 
            LEFT JOIN inf_red i ON i.id = p.cod_unico
            LEFT JOIN estadosOP e ON e.estado = p.estado
            JOIN user u ON i.user_id = u.id
            WHERE e.grupo_estado_general = 'En proceso de Presupuesto'
            ORDER BY p.fecha_creacion DESC
            """
        ).fetchall()
        title = 'Gestión de Presupuesto'
    elif option == 'convenio':
        presupuestos = db.execute(
            """
            SELECT p.id, p.cod_unico, p.fecha_creacion, p.bautizo, p.ip_madre, p.montoIGV, p.prioridad, p.estado, p.mes_pago_planificado, p.fecha_pago_96, e.grupo_gestion
            FROM presupuesto p 
            LEFT JOIN inf_red i ON i.id = p.cod_unico
            LEFT JOIN estadosOP e ON e.estado = p.estado
            JOIN user u ON i.user_id = u.id
            WHERE e.grupo_estado_general IN ('En proceso de Convenio','En proceso de Pago')
            ORDER BY p.fecha_creacion DESC
            """
        ).fetchall()
        title = 'Gestión de Convenio y Pago'
    n = len(presupuestos)
    return render_template('presupuesto/index.html', presupuestos=presupuestos, n=n, title=title)

@bp.route('/presupuesto/<string:cu>/create', methods=('GET', 'POST'))
@login_required
def createPresupuesto(cu):
    date_now = datetime.now().date()
    
    id = get_db().execute(
        """
        SELECT id
        FROM presupuesto
        WHERE id = (SELECT MAX(id) FROM presupuesto)
        """
    ).fetchone()[0]

    id = int(id) + 1

    db_estados = get_db().execute(
        'SELECT id, estado, grupo_estado'
        ' FROM estadosOP'
        ' ORDER BY id'
    ).fetchall()

    inf_red = get_db().execute(
        'SELECT id, proyecto'
        ' FROM inf_red '
        ' WHERE id = ?',
        (cu,)
    ).fetchone()

    list_color_estados = []
    n_estados = len(db_estados)
    for estado in db_estados:
        list_color_estados.append("color:" + get_color_estado(estado['grupo_estado']) + ";")

    if request.method == 'POST':
        fecha_creacion = request.form['fecha_creacion']
        bautizo = request.form['bautizo']
        documento = request.form['documento']
        fecha_documento = request.form['fecha_documento']
        contacto = request.form['contacto']
        correo_contacto = request.form['correo_contacto']
        telefono_contacto = request.form['telefono_contacto']

        ip_madre = request.form['ip_madre']

        fecha_inicio_diseno = request.form['fecha_inicio_diseno']
        fecha_termino_diseno = request.form['fecha_termino_diseno']
        fecha_entrega_ppto = request.form['fecha_entrega_ppto']
        nro_ppto = request.form['nro_ppto']
        montoIGV = request.form['montoIGV']
        prioridad = request.form['prioridad']
        estado = request.form['estado']
        
        mes_pago_planificado = request.form['mes_pago_planificado']
        mes_pago_oficial = request.form['mes_pago_oficial']
        semana_pago_interno = request.form['semana_pago_interno']
        semana_pago_oficial = request.form['semana_pago_oficial']
        bautizo_corto = request.form['bautizo_corto']

        nro_convenio = request.form['nro_convenio']
        fecha_firma_convenio = request.form['fecha_firma_convenio']
        plazo_convenio  = request.form['plazo_convenio']
        tiempo = request.form['tiempo']
        fecha_caducidad = request.form['fecha_caducidad']
        numero_factura  = request.form['numero_factura']
        fecha_pago_96 = request.form['fecha_pago_96']
        fecha_pago_4  = request.form['fecha_pago_4']

        error = None

        #Validación de Datos y Mostrar Error
        if not documento:
            error = 'Es requerido el Nombre del Documento (Oficio, Carta, etc.)'

        if error is not None:
            flash(error)

        #Registrar nueva entrada en la base de datos
        else:
            #if archivoKML.filename != '':
            #    filename = secure_filename(archivoKML.filename)
            #    archivoKML.save(filename)
            #    json_coords = get_coordinates(filename)
            #    os.remove(filename)
            #else:
            #    json_coords = ''

            db = get_db()
            db.execute(
                """
                INSERT INTO presupuesto (id, cod_unico, user_id, fecha_creacion, bautizo, documento, fecha_documento, contacto, correo_contacto, telefono_contacto, 
                    ip_madre, fecha_inicio_diseno, fecha_termino_diseno, fecha_entrega_ppto, nro_ppto, montoIGV, prioridad, estado, mes_pago_planificado, nro_convenio,
                    fecha_firma_convenio, plazo_convenio , tiempo, fecha_caducidad, numero_factura , fecha_pago_96, fecha_pago_4, mes_pago_oficial, semana_pago_interno, 
                    semana_pago_oficial, bautizo_corto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id, cu, g.user['id'], str(fecha_creacion) + ' 00:00:00', bautizo, documento, fecha_documento, contacto, correo_contacto, telefono_contacto, 
                    ip_madre, fecha_inicio_diseno, fecha_termino_diseno, fecha_entrega_ppto, nro_ppto, montoIGV, prioridad, estado, mes_pago_planificado, nro_convenio,
                    fecha_firma_convenio, plazo_convenio , tiempo, fecha_caducidad, numero_factura , fecha_pago_96, fecha_pago_4, mes_pago_oficial, semana_pago_interno, 
                    semana_pago_oficial, bautizo_corto)
            )
            db.commit()

            #Agregar Historial
            if not ip_madre:
                mensaje = "Se registra solicitud de Presupuesto del documento <b>" + str(documento) + "</b> con el Estado: <b>" + str(estado) + "</b>"
            else:
                mensaje = "Se registra solicitud de Presupuesto con el IP Madre <b>" + str(ip_madre) + "</b> con el Estado: <b>" + str(estado) + "</b>"
            db.execute(
                """
                INSERT INTO historial (user_id, fecha, cod_unico, presupuesto_id, tipo, observacion)
                 VALUES (?, (datetime('now','localtime')), ?, ?, ?, ?)
                """,
                (g.user['id'], cu, id, "Creación", mensaje)
            )
            db.commit()

            return redirect(url_for('inf_red.viewAll', id = cu))

    return render_template('presupuesto/create.html', cu = cu, estados = db_estados, inf_red = inf_red, date_now=date_now,
                           list_color_estados=list_color_estados, n_estados=n_estados, list_mes_pago=list_mes_pago)

@bp.route('/presupuesto/<string:id>/update', methods=('GET', 'POST'))
@login_required
def updatePresupuesto(id):
    presupuesto = get_presupuesto(id)

    db_estados = get_db().execute(
        'SELECT id, estado, grupo_estado'
        ' FROM estadosOP'
        ' ORDER BY id'
    ).fetchall()

    inf_red = get_db().execute(
        'SELECT id, proyecto'
        ' FROM inf_red '
        ' WHERE id = ?',
        (presupuesto['cod_unico'],)
    ).fetchone()

    list_color_estados = []
    n_estados = len(db_estados)
    for estado in db_estados:
        list_color_estados.append("color:" + get_color_estado(estado['grupo_estado']) + ";")

    if request.method == 'POST':
        fecha_creacion = request.form['fecha_creacion']
        bautizo = request.form['bautizo']
        documento = request.form['documento']
        fecha_documento = request.form['fecha_documento']
        contacto = request.form['contacto']
        correo_contacto = request.form['correo_contacto']
        telefono_contacto = request.form['telefono_contacto']

        ip_madre = request.form['ip_madre']

        fecha_inicio_diseno = request.form['fecha_inicio_diseno']
        fecha_termino_diseno = request.form['fecha_termino_diseno']
        fecha_entrega_ppto = request.form['fecha_entrega_ppto']
        nro_ppto = request.form['nro_ppto']
        montoIGV = request.form['montoIGV']
        prioridad = request.form['prioridad']
        estado = request.form['estado']
        
        mes_pago_planificado = request.form['mes_pago_planificado']
        mes_pago_oficial = request.form['mes_pago_oficial']
        semana_pago_interno = request.form['semana_pago_interno']
        semana_pago_oficial = request.form['semana_pago_oficial']
        bautizo_corto = request.form['bautizo_corto']

        nro_convenio = request.form['nro_convenio']
        fecha_firma_convenio = request.form['fecha_firma_convenio']
        plazo_convenio  = request.form['plazo_convenio']
        tiempo = request.form['tiempo']
        fecha_caducidad = request.form['fecha_caducidad']
        numero_factura  = request.form['numero_factura']
        fecha_pago_96 = request.form['fecha_pago_96']
        fecha_pago_4  = request.form['fecha_pago_4']

        observacion = request.form["observacion"]
        error = None

        #Validación de Datos y Mostrar Error
        if not documento:
            error = 'Es requerido el Nombre del Documento (Oficio, Carta, etc.)'

        if error is not None:
            flash(error)
        else:

            #Generar Historial
            tipo_comentario = 'Comentario'
            texto_comentario = ''
            if presupuesto['estado'] != estado:
                tipo_comentario = 'Actualización'
                texto_comentario = texto_comentario + 'Cambio estado Gestión de <b>' + str(presupuesto['estado']) + '</b> a <b>' + str(estado) + '</b>'
            if presupuesto['ip_madre'] != ip_madre:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio IP Madre de <b>' + str(presupuesto['ip_madre']) if presupuesto['ip_madre'] else 'Sin IP Madre' + '</b> a <b>' + str(ip_madre) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio IP Madre de <b>' + str(presupuesto['ip_madre']) if presupuesto['ip_madre'] else 'Sin IP Madre' + '</b> a <b>' + str(ip_madre) + '</b>'
            if str(presupuesto['montoIGV']) != str(montoIGV):
                temporal_prev = str('S/. {:,.2f}'.format(float(presupuesto['montoIGV']))) if presupuesto['montoIGV'] else 'Sin monto Cargado'
                temporal_desp = str('S/. {:,.2f}'.format(float(montoIGV))) if montoIGV else 'Sin monto Cargado'
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Monto + IGV de <b>' + temporal_prev + '</b> a <b>' + temporal_desp + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Monto + IGV de <b>' + temporal_prev + '</b> a <b>' + temporal_desp + '</b>'
            if presupuesto['mes_pago_planificado'] != mes_pago_planificado:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Mes Pago Interno de <b>' + str(presupuesto['mes_pago_planificado']) + '</b> a <b>' + str(mes_pago_planificado) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Mes Pago Interno de <b>' + str(presupuesto['mes_pago_planificado']) + '</b> a <b>' + str(mes_pago_planificado) + '</b>'
            if presupuesto['mes_pago_oficial'] != mes_pago_oficial:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Mes Pago Oficial de <b>' + str(presupuesto['mes_pago_oficial']) + '</b> a <b>' + str(mes_pago_oficial) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Mes Pago Oficial de <b>' + str(presupuesto['mes_pago_oficial']) + '</b> a <b>' + str(mes_pago_oficial) + '</b>'
            if presupuesto['semana_pago_interno'] != semana_pago_interno:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Semana Pago Interno de <b>' + str(presupuesto['semana_pago_interno']) + '</b> a <b>' + str(semana_pago_interno) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Semana Pago Interno de <b>' + str(presupuesto['semana_pago_interno']) + '</b> a <b>' + str(semana_pago_interno) + '</b>'
            if presupuesto['semana_pago_oficial'] != semana_pago_oficial:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Semana Pago Oficial de <b>' + str(presupuesto['semana_pago_oficial']) + '</b> a <b>' + str(semana_pago_oficial) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Semana Pago Oficial de <b>' + str(presupuesto['semana_pago_oficial']) + '</b> a <b>' + str(semana_pago_oficial) + '</b>'

            if observacion:
                if texto_comentario == '':
                    texto_comentario = texto_comentario + str(observacion)
                else:
                    texto_comentario = texto_comentario + '<br><b>Observación</b><br>' + str(observacion)


            db = get_db()
            db.execute(
                """
                UPDATE presupuesto 
                    SET     fecha_creacion = ?, bautizo = ?, documento = ?, fecha_documento = ?, contacto = ?, correo_contacto = ?, telefono_contacto = ?, 
                            ip_madre = ?, fecha_inicio_diseno = ?, fecha_termino_diseno = ?, fecha_entrega_ppto = ?, nro_ppto = ?, montoIGV = ?, prioridad = ?,
                            estado = ?, mes_pago_planificado = ?, mes_pago_oficial = ?, semana_pago_interno = ?, semana_pago_oficial = ?, bautizo_corto = ?,
                            nro_convenio = ?, fecha_firma_convenio = ?, plazo_convenio  = ?, tiempo = ?, fecha_caducidad = ?, numero_factura  = ?,
                            fecha_pago_96 = ?, fecha_pago_4 = ?
                WHERE id = ?
                """,
                (str(fecha_creacion) + ' 00:00:00', bautizo, documento, fecha_documento, contacto, correo_contacto, telefono_contacto, ip_madre, fecha_inicio_diseno, fecha_termino_diseno, 
                 fecha_entrega_ppto, nro_ppto, montoIGV, prioridad, estado, mes_pago_planificado, mes_pago_oficial, semana_pago_interno, semana_pago_oficial, 
                 bautizo_corto, nro_convenio, fecha_firma_convenio, plazo_convenio , tiempo, fecha_caducidad, numero_factura , fecha_pago_96, fecha_pago_4, id)
            )
            db.commit()

            #Agregar Historial
            if texto_comentario != '':
                db.execute(
                    """
                    INSERT INTO historial (user_id, fecha, cod_unico, presupuesto_id, tipo, observacion)
                    VALUES (?, (datetime('now','localtime')), ?, ?, ?, ?)
                    """,
                    (g.user['id'], presupuesto['cod_unico'], id, tipo_comentario, texto_comentario)
                )
                db.commit()

            return redirect(url_for('inf_red.viewAll', id = presupuesto['cod_unico']))

    return render_template('presupuesto/update.html', cu = presupuesto['cod_unico'], presupuesto = presupuesto, estados = db_estados, inf_red = inf_red,
                           list_color_estados=list_color_estados, n_estados=n_estados, list_mes_pago=list_mes_pago)

@bp.route('/presupuesto/importar-webpo', methods=('GET', 'POST'))
@login_required
def importWebpo():
    db = get_db()
    presupuestos = db.execute(
            """
            SELECT id, cod_unico, ip_madre, fecha_creacion_ipmadre, estado_ipmadre_webPO, eecc
            FROM presupuesto 
            """
        ).fetchall()
    
    tables_resumenIP = None

    if request.method == 'POST':
        webPO_resumenIP = request.files["webPO_resumenIP"]

        error = None

        #Validación de Datos y Mostrar Error
        if webPO_resumenIP.filename != '' and not(allowed_file(webPO_resumenIP.filename)):
            error = 'Formato del archivo incorrecto'

        if error is not None:
            flash(error)

        #Registrar nueva entrada en la base de datos
        else:
            if webPO_resumenIP.filename != '':
                filename = secure_filename(webPO_resumenIP.filename)
                webPO_resumenIP.save(filename)
                #Columnas Importantes:
                #       IP MADRES - 0
                #       ESTADO ITEM. MADRE - 1
                #       FECHA RECEPCION - 16
                #       MONTO - 11
                #       NOMBRE IP MADRE - 3
                #       EECC - 13
                df_resumenIP = pd.read_csv(filename, delimiter='\\t', encoding='latin-1')
                col_ipmadre = df_resumenIP.columns[0]
                col_estadoIp = df_resumenIP.columns[1]
                col_fechaRec = df_resumenIP.columns[16]
                col_monto = df_resumenIP.columns[11]
                col_nombreIp = df_resumenIP.columns[3]
                col_eecc = df_resumenIP.columns[13]

                df_resumenIP[col_ipmadre] = df_resumenIP[col_ipmadre].str.replace(r'"', '', regex=True)
                #Actualizar campos por IP Madre
                list_mensaje, list_ipmadre, list_estadoIP, list_eecc, list_fechaRec = [], [], [], [], []
                
                for presupuesto in presupuestos:
                    if presupuesto['ip_madre'] in df_resumenIP[col_ipmadre].values:
                        try:
                            row = df_resumenIP.loc[df_resumenIP[col_ipmadre] == presupuesto['ip_madre']].index[0]
                            #Formatear Fecha
                            fecha = df_resumenIP[col_fechaRec][row][:-1]
                            list_temp = fecha.split("/")
                            if list_temp[2] == '0000':
                                fecha = '0001-01-01'
                            else:
                                fecha = list_temp[2] + "-" + list_temp[1] + "-" + list_temp[0]

                            list_mensaje.append('Cargado Correctamente')
                            list_fechaRec.append(df_resumenIP[col_fechaRec][row][:-1])
                            list_ipmadre.append(presupuesto['ip_madre'])
                            list_estadoIP.append(df_resumenIP[col_estadoIp][row])
                            list_eecc.append(df_resumenIP[col_eecc][row])

                            if (fecha != presupuesto['fecha_creacion_ipmadre'] or df_resumenIP[col_estadoIp][row] != presupuesto['estado_ipmadre_webPO'] 
                                or df_resumenIP[col_eecc][row] != presupuesto['eecc']):
                                db.execute(
                                    """
                                    UPDATE presupuesto 
                                            SET     fecha_creacion_ipmadre = ?, estado_ipmadre_webPO = ?, eecc = ?
                                    WHERE ip_madre = ?
                                    """,
                                    (fecha, df_resumenIP[col_estadoIp][row], df_resumenIP[col_eecc][row], presupuesto['ip_madre'])
                                )
                                db.commit()
                        except:
                            list_mensaje.append('Error de Carga')
                            list_ipmadre.append(presupuesto['ip_madre'])
                            list_fechaRec.append("-")
                            list_estadoIP.append("-")
                            list_eecc.append("-")
                    dict_resumenIP = {'Mensaje': list_mensaje, 'IP Madre': list_ipmadre, 'Fecha Creación IP Madre': list_fechaRec, 'Estado IP Madre': list_estadoIP, 'EECC': list_eecc}
                    df_resumenIP_rpta = pd.DataFrame(dict_resumenIP)
                    tables_resumenIP = [df_resumenIP_rpta.to_html(classes='data', header="true")]

                os.remove(filename)

    return render_template('presupuesto/importar_webpo.html', tables_resumenIP=tables_resumenIP)


@bp.route('/comentario/presupuesto/<string:id>/<string:comentario>')
def add_comentario_presupuesto(id, comentario):
    db = get_db()
    presupuesto = get_presupuesto(id)
    db.execute(
            """
            INSERT INTO historial (user_id, fecha, cod_unico, presupuesto_id, tipo, observacion)
             VALUES (?, (datetime('now','localtime')), ?, ?, ?, ?)
            """,
            (g.user['id'], presupuesto['cod_unico'], id, "Comentario", comentario)
        )
    db.commit()
    return ('', 204)