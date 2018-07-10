# -*- coding: utf-8 -*-

"""Módulo 'normalizer' de georef-api

Contiene funciones que manejan la lógica de procesamiento
de los recursos que expone la API.
"""

from service import data, parser, params
from service.names import *
from service.parser import flatten_dict
from elasticsearch import Elasticsearch, ElasticsearchException
from flask import g, abort


def get_elasticsearch():
    if 'elasticsearch' not in g:
        g.elasticsearch = Elasticsearch()

    return g.elasticsearch


def translate_keys(d, translations):
    return {
        translations.get(key, key): value
        for key, value in d.items()
    }


def parse_params(request, name, param_parser):
    if request.method == 'GET':
        params_list = [request.args]
    else:
        params_list = request.json.get(name)
        if not params_list:
            abort(400)  # TODO: Manejo de erroes apropiado

    return param_parser.parse_params_dict_list(params_list)


def queries_from_params(request, name, param_parser, key_translations):
    parse_results = parse_params(request, name, param_parser)
    queries = []

    for parsed_params, errors in parse_results:
        # TODO: Manejo de errores de params
        parsed_params.pop(FLATTEN, None)  # TODO: Manejo de flatten
        query = translate_keys(parsed_params, key_translations)
        queries.append(query)

    try:
        es = get_elasticsearch()
        responses = data.query_entities(es, name, queries)
    except ElasticsearchException:
        abort(500)

    # TODO: Manejo de SOURCE
        
    if request.method == 'GET':
        return parser.get_response({name: responses[0]})
    else:
        responses = [{name: matches} for matches in responses]
        return parser.get_response({RESULTS: responses})


def process_state(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, STATES, params.PARAMS_STATES, {
            ID: 'entity_id',
            NAME: 'name',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_department(request):
    """Procesa una consulta de tipo GET para normalizar provincias.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, DEPARTMENTS, params.PARAMS_DEPARTMENTS, {
            ID: 'entity_id',
            NAME: 'name',
            STATE: 'state',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_municipality(request):
    """Procesa una consulta de tipo GET para normalizar municipios.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, MUNICIPALITIES, params.PARAMS_MUNICIPALITIES, {
            ID: 'entity_id',
            NAME: 'name',
            STATE: 'state',
            DEPT: 'department',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_locality(request):
    """Procesa una consulta de tipo GET para normalizar localidades.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, LOCALITIES, params.PARAMS_LOCALITIES, {
            ID: 'entity_id',
            NAME: 'name',
            STATE: 'state',
            DEPT: 'department',
            MUN: 'municipality',
            EXACT: 'exact',
            ORDER: 'order',
            FIELDS: 'fields'
    })


def process_street(request):
    """Procesa una consulta de tipo GET para normalizar calles.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de la consulta como objeto flask.Response.
    """
    return process_entity(request, STREETS, params.PARAMS_STREETS, {
            NAME: 'road_name',
            STATE: 'state',
            DEPT: 'department',
            EXACT: 'exact',
            FIELDS: 'fields'
    })

    # TODO: Remover geometria?


def process_address(request):
    """Procesa una consulta para normalizar direcciones.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    parse_results = parse_params(request, ADDRESSES, params.PARAMS_ADDRESSES)

    queries = []
    for parsed_params, errors in parse_results:
        road_name, number = parsed_params.pop(ADDRESS)
        print(road_name, number)
        parsed_params['road_name'] = road_name
        parsed_params['number'] = number

        parsed_params.pop(FLATTEN, None)  # TODO: Manejar flatten

        queries.append(translate_keys(parsed_params, {
            DEPT: 'department',
            STATE: 'state',
            EXACT: 'exact',
            FIELDS: 'fields',
            ROAD_TYPE: 'road_type'
        }))

    try:
        es = get_elasticsearch()
        responses = data.query_addresses(es, queries)
    except ElasticsearchException:
        abort(500)

    # TODO: Manejo de SOURCE

    if request.method == 'GET':
        return parser.get_response({ADDRESSES: responses[0]})
    else:
        responses = [{ADDRESSES: matches} for matches in responses]
        return parser.get_response({RESULTS: responses})


def build_place_result(query, dept, muni):
    empty_entity = {
        ID: None,
        NAME: None
    }

    if not dept:
        state = empty_entity.copy()
        dept = empty_entity.copy()
        muni = empty_entity.copy()
    else:
        # Remover la provincia del departamento y colocarla directamente
        # en el resultado. Haciendo esto se logra evitar una consulta
        # al índice de provincias.
        state = dept.pop(STATE)
        muni = muni or empty_entity.copy()

    place = {
        STATE: state,
        DEPT: dept,
        MUN: muni,
        LAT: query['lat'],
        LON: query['lon']
    }

    if query[FIELDS]:
        place = {key: place[key] for key in place if key in query[FIELDS]}

    if query[FLATTEN]:
        parser.flatten_dict(place)

    return place


def process_place(request):
    """Procesa una consulta para georreferenciar una ubicación.

    Args:
        request (flask.Request): Objeto con información de la consulta HTTP.

    Returns:
        Resultado de una de las funciones invocadas según el tipo de Request.
    """
    parse_results = parse_params(request, PLACES, params.PARAMS_PLACE)
    queries = []

    for parsed_params, errors in parse_results:
        # TODO: Manejo de errores de params
        queries.append(parsed_params)

    try:
        es = get_elasticsearch()
        dept_queries = []
        for query in queries:
            dept_queries.append({
                'lat': query['lat'],
                'lon': query['lon'],
                'fields': [ID, NAME, STATE]
            })
            
        departments = data.query_places(es, DEPARTMENTS, dept_queries)

        muni_queries = []
        for query in queries:
            muni_queries.append({
                'lat': query['lat'],
                'lon': query['lon'],
                'fields': [ID, NAME]
            })

        munis = data.query_places(es, MUNICIPALITIES, muni_queries)

        places = []
        for query, dept, muni in zip(queries, departments, munis):
            places.append(build_place_result(query, dept, muni))

    except ElasticsearchException:
        abort(500)

    # TODO: Manejo de SOURCE

    if request.method == 'GET':
        return parser.get_response({PLACE: places[0]})
    else:
        responses = [{PLACE: place} for place in places]
        return parser.get_response({RESULTS: responses})
