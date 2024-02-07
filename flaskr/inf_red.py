import re
import json
import os
import folium
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

bp = Blueprint('inf_red', __name__)

#Revisa si el archivo de Google Earth es un KML
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ['kml']

#No me acuerdo
def parse(root, points, linestring, polygon):
    for elt in root.getchildren():
        # strip the namespace
        tag = re.sub(r'^.*\}', '', elt.tag)

        if tag in ["Document", "Folder"]:
            # recursively iterate over child elements
            parse(elt, points, linestring, polygon)
        elif tag == "Placemark":
            if hasattr(elt, 'Point'):
                points.append(elt.Point.coordinates)
            elif hasattr(elt, 'LineString'):
                linestring.append(elt.LineString.coordinates)
            elif hasattr(elt, 'Polygon'):
                polygon.append(elt.Polygon.outerBoundaryIs.LinearRing.coordinates)
            elif hasattr(elt, 'MultiGeometry'):
                for gg in elt.MultiGeometry.getchildren():
                    tag = re.sub(r'^.*\}', '', gg.tag)
                    if tag == "Polygon":
                        polygon.append(gg.outerBoundaryIs.LinearRing.coordinates)
    return points, linestring, polygon

#Función para obtener las coordenadas de una archivo kml
def get_coordinates(file):
    with open(file, 'r', encoding="utf8") as f:
        root = parser.parse(f).getroot()
        
    points = []
    linestring = []
    polygon = []
    points, linestring, polygon = parse(root, points, linestring, polygon)

    aux = [ ['Points', points], ['LineStrings', linestring], ['Polygons', polygon]  ]
    coordinates = [ ['Points', []], ['LineStrings', []], ['Polygons', []]  ]

    for i in range(len(aux)):
        for text in aux[i][1]:
            temp = []
            for coor in (str(text).strip()).split():
                temp2 = [float(x) for x in coor.split(',')]
                temp2 = temp2[0:2]
                temp2.reverse()
                temp.append(temp2)
            coordinates[i][1].append(temp)
    return json.dumps(coordinates)

#Dibuja en el mapita
def draw_figures(fig, data, estado):
  #Elaborar un Mapa
    coordinates = json.loads(data["json_coords"])
    tooltip = str(data["id"])
    color = get_color_estado(estado)

    for coor_type in coordinates:
        if coor_type[0] == 'Points':
            for point in coor_type[1]:
                folium.Marker(
                point[0], color=color, opacity=0.8, tooltip=tooltip,
                ).add_to(fig)
        elif coor_type[0] == 'LineStrings':
            for line in coor_type[1]:
                folium.PolyLine(
                line, color=color, weight=4, opacity=0.8, tooltip=tooltip
                ).add_to(fig)
        elif coor_type[0] == 'Polygons':
            for pol in coor_type[1]:
                folium.PolyLine(
                pol, color=color, fill_color="blue", tooltip=tooltip
                ).add_to(fig)
    return fig

#Obtiene la inf en la base de datos segun el ID
def get_inf(id, check_user=True):
    inf_red = get_db().execute(
        'SELECT i.id, documento, link_archivos, fecha_creacion, user_id, username, fecha_documento, titulo_correo, fecha_correo, nombre_entidad, entidad, proyecto, departamento, provincia, distrito, contacto, correo_contacto, telefono_contacto, resumen_planta, fecha_respuesta, tma, estado_inf_red, estado_proyecto, peso_kml, formulario_completado, inicio_obras, complejidad, json_coords'
        ' FROM inf_red i JOIN user u ON i.user_id = u.id'
        ' WHERE i.id = ?',
        (id,)
    ).fetchone()

    if inf_red is None:
        abort(404, f"Post id {id} doesn't exist.")

    #Revisa que el usuario que edita solo sea el mismo que lo creo
    #if check_user and inf_red['user_id'] != g.user['id']:
    #    abort(403)

    return inf_red

#Obtiene los presupuestos en la base de datos segun el CU
def get_presupuesto(cu, check_user=True):
    presupuesto = get_db().execute(
        """
        SELECT id, cod_unico, user_id, date(fecha_creacion) as fecha_creacion, bautizo, documento, fecha_documento, contacto, correo_contacto,
            telefono_contacto, ip_madre, fecha_creacion_ipmadre, estado_ipmadre_webPO, eecc, solicitudOC, fecha_inicio_diseno,
            fecha_termino_diseno, fecha_entrega_ppto, nro_ppto, montoIGV, prioridad, estado, mes_pago_planificado, nro_convenio,
            fecha_firma_convenio, plazo_convenio, tiempo, fecha_caducidad, numero_factura, fecha_pago_96, fecha_pago_4, semana_pago_interno,
            semana_pago_oficial, mes_pago_oficial
         FROM presupuesto
         WHERE cod_unico = ?
        """,
        (cu,)
    ).fetchall()

    #for data in presupuesto:
    #    data['montoIGV'] = '${:,.2f}'.format(data['montoIGV'])

    if presupuesto is None:
        abort(404, f"Presupuesto para CU {id} doesn't exist.")

    #Revisa que el usuario que edita solo sea el mismo que lo creo
    #if check_user and inf_red['user_id'] != g.user['id']:
    #    abort(403)

    return presupuesto

@bp.route('/inf_red')
@login_required
def indexInfRed():
    db = get_db()
    inf_redes = db.execute(
        """
        SELECT i.id, i.proyecto, i.entidad, i.nombre_entidad, i.link_archivos, i.fecha_creacion, i.estado_inf_red, count(p.id) AS cant_ppto
        FROM inf_red i JOIN user u ON i.user_id = u.id
		LEFT JOIN presupuesto p ON i.id = p.cod_unico
		GROUP BY i.id
        ORDER BY i.fecha_creacion DESC
        """
    ).fetchall()
    n = len(inf_redes)

    style_cell_estadoRed = []
    for inf_red in inf_redes:
        if inf_red['estado_inf_red'] == 'ATENDIDO':
            style_cell_estadoRed.append('color: #006100;background-color: #c6efce;')
        elif inf_red['estado_inf_red'] == 'CANCELADO':
            style_cell_estadoRed.append('color: #9c0006;background-color: #ffc7ce;')
        else:
            style_cell_estadoRed.append('color: #9c5700;background-color: #ffeb9c;')
    return render_template('inf_red/index.html', inf_redes=inf_redes, n=n, style_cell_estadoRed=style_cell_estadoRed)

@bp.route('/inf_red/create', methods=('GET', 'POST'))
@login_required
def createInfRed():
    today = datetime.today()
    id_or = str(today.year) + '-' + str('%02d' % today.month) + str('%02d' % today.day) + str('%02d' % (today.hour + today.second))

    db = get_db()
    db_departamentos = db.execute(
        'SELECT departamento'
        ' FROM departamentos'
        ' ORDER BY departamento'
    ).fetchall()

    if request.method == 'POST':
        id = request.form['id']
        document = request.form['documento']
        link = request.form['link']
        fecha_documento = request.form['fecha_documento']
        titulo_correo = request.form['titulo_correo']
        fecha_correo = request.form['fecha_correo']
        nombre_entidad = request.form['nombre_entidad']
        entidad = request.form['entidad']
        proyecto = request.form['proyecto']
        departamento = request.form['departamento']
        provincia = request.form['provincia']
        distrito = request.form['distrito']
        contacto = request.form['contacto']
        correo_contacto = request.form['correo_contacto']
        telefono_contacto = request.form['telefono_contacto']
        resumen_planta = request.form['resumen_planta']
        fecha_respuesta = request.form['fecha_respuesta']
        tma = request.form['tma']
        estado_inf_red = request.form['estado_inf_red']
        estado_proyecto = request.form['estado_proyecto']
        peso_kml = request.form['peso_kml']
        formulario_completado = request.form['formulario_completado']
        inicio_obras = request.form['inicio_obras']
        complejidad = request.form['complejidad']
        archivoKML = request.files["archivoKML"]

        error = None

        #Validación de Datos y Mostrar Error
        if not document:
            error = 'Es requerido el Nombre del Documento (Oficio, Carta, etc.)'

        if archivoKML.filename != '' and not(allowed_file(archivoKML.filename)):
            error = 'Formato del archivo incorrecto'

        if error is not None:
            flash(error)
        #Registrar nueva entrada en la base de datos
        else:
            if archivoKML.filename != '':
                filename = secure_filename(archivoKML.filename)
                archivoKML.save(filename)
                json_coords = get_coordinates(filename)
                os.remove(filename)
            else:
                json_coords = ''

            db = get_db()
            db.execute(
                """
                INSERT INTO inf_red (id, fecha_creacion, user_id, documento, link_archivos, fecha_documento, titulo_correo, fecha_correo, nombre_entidad, entidad, proyecto, departamento, provincia, distrito, contacto, correo_contacto, telefono_contacto, resumen_planta, fecha_respuesta, tma, estado_inf_red, estado_proyecto, peso_kml, formulario_completado, inicio_obras, complejidad, json_coords)
                 VALUES (?, (datetime('now','localtime')), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id, g.user['id'], document, link, fecha_documento, titulo_correo, fecha_correo, nombre_entidad, entidad, proyecto, departamento, provincia, distrito, contacto, correo_contacto, telefono_contacto, resumen_planta, fecha_respuesta, tma, estado_inf_red, estado_proyecto, peso_kml, formulario_completado, inicio_obras, complejidad, json_coords)
            )
            db.commit()

            #Agregar Historial
            db.execute(
                """
                INSERT INTO historial (user_id, fecha, cod_unico, tipo, observacion)
                 VALUES (?, (datetime('now','localtime')), ?, ?, ?)
                """,
                (g.user['id'], id, "Creación", "Se crea el Código Único " + str(id) + " en Información de Red con el Estado: " + str(estado_inf_red))
            )
            db.commit()

            return redirect(url_for('inf_red.viewAll', id = id))

    return render_template('inf_red/create.html', id = id_or, departamentos = db_departamentos)

@bp.route('/inf_red/<string:id>/update', methods=('GET', 'POST'))
@login_required
def updateInfRed(id):
    inf_red = get_inf(id)

    db_departamentos = get_db().execute(
        'SELECT departamento'
        ' FROM departamentos'
        ' ORDER BY departamento'
    ).fetchall()

    if request.method == 'POST':
        documento = request.form['documento']
        link_archivos = request.form['link_archivos']
        fecha_documento = request.form['fecha_documento']
        titulo_correo = request.form['titulo_correo']
        fecha_correo = request.form['fecha_correo']
        nombre_entidad = request.form['nombre_entidad']
        entidad = request.form['entidad']
        proyecto = request.form['proyecto']
        departamento = request.form['departamento']
        provincia = request.form['provincia']
        distrito = request.form['distrito']
        contacto = request.form['contacto']
        correo_contacto = request.form['correo_contacto']
        telefono_contacto = request.form['telefono_contacto']
        resumen_planta = request.form['resumen_planta']
        fecha_respuesta = request.form['fecha_respuesta']
        tma = request.form['tma']
        estado_inf_red = request.form['estado_inf_red']
        estado_proyecto = request.form['estado_proyecto']
        peso_kml = request.form['peso_kml']
        formulario_completado = request.form['formulario_completado']
        inicio_obras = request.form['inicio_obras']
        complejidad = request.form['complejidad']
        archivoKML = request.files["archivoKML"]

        observacion = request.form["observacion"]
        error = None

        if not documento:
            error = 'Documento is required.'
        if archivoKML.filename != '' and not(allowed_file(archivoKML.filename)):
            error = 'Formato del archivo incorrecto'

        if error is not None:
            flash(error)
        else:
            if archivoKML.filename != '':
                filename = secure_filename(archivoKML.filename)
                archivoKML.save(filename)
                json_coords = get_coordinates(filename)
                os.remove(filename)
            else:
                json_coords = inf_red['json_coords']

            #Validar Cambios
            tipo_comentario = 'Comentario'
            texto_comentario = ''
            if inf_red['estado_inf_red'] != estado_inf_red:
                tipo_comentario = 'Actualización'
                texto_comentario = texto_comentario + 'Cambio estado Inf. de Red de <b>' + str(inf_red['estado_inf_red']) + '</b> a <b>' + str(estado_inf_red) + '</b>'
            if inf_red['estado_proyecto'] != estado_proyecto:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Estado del Proyecto de <b>' + str(inf_red['estado_proyecto']) + '</b> a <b>' + str(estado_proyecto) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Estado del Proyecto de <b>' + str(inf_red['estado_proyecto']) + '</b> a <b>' + str(estado_proyecto) + '</b>'
            if inf_red['inicio_obras'] != inicio_obras:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Inico de Obras de <b>' + str(inf_red['inicio_obras']) + '</b> a <b>' + str(inicio_obras) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Inico de Obras de <b>' + str(inf_red['inicio_obras']) + '</b> a <b>' + str(inicio_obras) + '</b>'
            if inf_red['nombre_entidad'] != nombre_entidad:
                tipo_comentario = 'Actualización'
                if texto_comentario == '':
                    texto_comentario = texto_comentario + 'Cambio Entidad de <b>' + str(inf_red['nombre_entidad']) + '</b> a <b>' + str(nombre_entidad) + '</b>'
                else:
                    texto_comentario = texto_comentario + '<br>Cambio Entidad de <b>' + str(inf_red['nombre_entidad']) + '</b> a <b>' + str(nombre_entidad) + '</b>'

            if observacion:
                if texto_comentario == '':
                    texto_comentario = texto_comentario + str(observacion)
                else:
                    texto_comentario = texto_comentario + '<br><b>Observación</b><br>' + str(observacion)


            db = get_db()
            db.execute(
                'UPDATE inf_red SET documento = ?, link_archivos = ?, fecha_documento = ?, titulo_correo = ?, fecha_correo = ?, nombre_entidad = ?, entidad = ?, proyecto = ?, departamento = ?, provincia = ?, distrito = ?, contacto = ?, correo_contacto = ?, telefono_contacto = ?, resumen_planta = ?, fecha_respuesta = ?, tma = ?, estado_inf_red = ?, estado_proyecto = ?, peso_kml = ?, formulario_completado = ?, inicio_obras = ?, complejidad = ?, json_coords = ?'
                ' WHERE id = ?',
                (documento, link_archivos, fecha_documento, titulo_correo, fecha_correo, nombre_entidad, entidad, proyecto, departamento, provincia, distrito, contacto, correo_contacto, telefono_contacto, resumen_planta, fecha_respuesta, tma, estado_inf_red, estado_proyecto, peso_kml, formulario_completado, inicio_obras, complejidad, json_coords, id)
            )
            db.commit()

            #Agregar Historial
            if texto_comentario != '':
                db.execute(
                    """
                    INSERT INTO historial (user_id, fecha, cod_unico, tipo, observacion)
                    VALUES (?, (datetime('now','localtime')), ?, ?, ?)
                    """,
                    (g.user['id'], id, tipo_comentario, texto_comentario)
                )
                db.commit()

            return redirect(url_for('inf_red.viewAll', id = id))

    return render_template('inf_red/update.html', inf_red=inf_red, departamentos = db_departamentos)

@bp.route('/inf_red/<string:id>/delete', methods=('POST',))
@login_required
def deleteInfRed(id):
    get_inf(id)
    db = get_db()
    db.execute('DELETE FROM inf_red WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('inf_red.indexInfRed'))

@bp.get('/provincia')
def provincia():
    departamento = request.args.get('departamento')
    db_provincias = get_db().execute(
        'SELECT departamento, provincia'
        ' FROM provincias'
        ' WHERE departamento = ?',
        (departamento,)
    ).fetchall()
    return render_template('utilidad/provincia_options.html', provincias = db_provincias)

@bp.get('/distrito')
def distrito():
    provincia = request.args.get('provincia')
    db_distritos = get_db().execute(
        'SELECT departamento, provincia, distrito'
        ' FROM distritos'
        ' WHERE provincia = ?',
        (provincia,)
    ).fetchall()
    return render_template('utilidad/distrito_options.html', distritos = db_distritos)

#Función que muestra todo el detalle de un Código Único
@bp.route('/obra_publica/<string:id>')
@login_required
def viewAll(id):
    inf_red = get_inf(id)
    presupuestos = get_presupuesto(id)
    #Generar lista de Estados Generales si hay 1 o más presupuestos
    if len(presupuestos) > 0:
        estado_general = []
        for presupuesto in presupuestos:
            estado_general.append(get_db().execute(
                """
                    SELECT grupo_estado
                    FROM estadosOP
                    WHERE estado = ?
                """,
                (presupuesto['estado'],)
            ).fetchone()[0])
    else:
        estado_general = get_estado_grupo_infred(inf_red["estado_inf_red"])
    
    estado_general_html = []
    for i in range(len(estado_general)):
        if len(presupuestos) > 0:
            estado_general_html.append("<i style='color:" + get_color_estado(estado_general[i]) +";'>" + presupuestos[i]['estado'] + "</i>")
        else:
            estado_general_html.append("<i style='color:" + get_color_estado(estado_general[i]) +";'>" + estado_general[i] + "</i>")

    color = get_color_estado(estado_general)
    list_class = get_estado_grupo_class(estado_general)

    list_historial = []
    #Historial Inf de Red
    historial = get_db().execute(
        """
        SELECT h.fecha, h.cod_unico, 'Inf. Red' AS ip_madre, u.username, h.observacion
        FROM historial h 
        LEFT JOIN user u ON h.user_id = u.id
        LEFT JOIN presupuesto p ON h.cod_unico = p.cod_unico
        WHERE h.cod_unico = ? AND h.presupuesto_id IS NULL
		GROUP BY h.fecha
        ORDER BY h.fecha DESC
        """,
        (id,)
    ).fetchall()
    list_historial.append([historial, '<b>Historial Inf. Red</b>', 'inf_redA'])
    #Historial de cada presupuesto
    for presupuesto in presupuestos:
        historial = get_db().execute(
            """
            SELECT h.fecha, h.cod_unico, p.ip_madre, u.username, h.observacion
            FROM historial h 
            LEFT JOIN user u ON h.user_id = u.id
            LEFT JOIN presupuesto p ON h.cod_unico = p.cod_unico
            WHERE h.presupuesto_id = ?
            GROUP BY h.fecha
            ORDER BY h.fecha DESC
            """,
            (presupuesto['id'],)
        ).fetchall()
        list_historial.append([historial, '<b>IP Madre </b>' + str(presupuesto['ip_madre']) + '<br><b>Bautizo </b>' + str(presupuesto['bautizo']),
                               str(presupuesto['id'])])

    init_coord = []
    if inf_red["json_coords"] != '' and inf_red["json_coords"] != None:
        coordinates = json.loads(inf_red["json_coords"])
        #Obtener coordenadas para localizacion inicial
        for coor_type in coordinates:
            if coor_type[0] == 'Points':
                for points in coor_type[1]:
                    for point in points:
                        init_coord = point
                        break
                    if len(init_coord) > 0:
                        break
            elif coor_type[0] == 'LineStrings':
                for line in coor_type[1]:
                    for point in line:
                        init_coord = point
                        break
                    if len(init_coord) > 0:
                        break
            elif coor_type[0] == 'Polygons':
                for pol in coor_type[1]:
                    for point in pol:
                        init_coord = point
                        break
                    if len(init_coord) > 0:
                        break
            if len(init_coord) > 0:
                break

    if len(init_coord) == 0:
        init_coord = [-9, -75]

    fig_map = folium.Map(location=init_coord, zoom_start=15)

    if inf_red["json_coords"] != '' and inf_red["json_coords"] != None:
        draw_figures(fig_map, inf_red, estado_general)

    plugins.Geocoder().add_to(fig_map)
    plugins.Fullscreen(
        position                = "topright",
        title                   = "Open full-screen map",
        title_cancel            = "Close full-screen map",
        force_separate_button   = True,
    ).add_to(fig_map)

    iframe = fig_map.get_root()._repr_html_()

    return render_template('/view.html', inf_red=inf_red, iframe=iframe, list_historial=list_historial,
                           list_class=list_class, presupuestos=presupuestos, num_estados=len(estado_general), estado_general=estado_general_html)

@bp.route('/comentario/<string:cu>/<string:comentario>')
def add_comentario(cu, comentario):
    db = get_db()
    db.execute(
            """
            INSERT INTO historial (user_id, fecha, cod_unico, tipo, observacion)
             VALUES (?, (datetime('now','localtime')), ?, ?, ?)
            """,
            (g.user['id'], cu, "Comentario", comentario)
        )
    db.commit()
    return ('', 204)