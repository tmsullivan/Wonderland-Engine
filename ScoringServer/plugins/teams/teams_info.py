from flask import Response, url_for, redirect, g, request
from . import blueprint
from ScoringServer.utils import mongodb_list_to_dict, create_error_response, requires_parameters, requires_no_parameters, Parameters
from bson import json_util
from copy import deepcopy
import json

@blueprint.route("/", methods=['GET'])
@requires_no_parameters
def get_all_teams():
    data = list(g.db.teams.find())
    new_data = mongodb_list_to_dict(data)
    js = json.dumps(new_data, default=json_util.default)
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@blueprint.route("/", methods=['POST'])
@requires_parameters(required=['name', 'id'])
def create_team():
    data = json.loads(request.data)
    data['score'] = 0
    if len(list(g.db.teams.find({'id':data['id']}))) != 0:
        return create_error_response("TeamExists",  "A team with the id '{}' already exists".format(data['id']))
    g.db.teams.insert(data)
    #todo create new process for team and save port number in db
    resp = redirect(url_for(".get_team", team_id=data['id']), code=201)
    return resp

@blueprint.route("/<team_id>", methods=['GET'])
@requires_no_parameters
def get_team(team_id):
    data = list(g.db.teams.find({'id': team_id}))
    if len(data) == 0:
        return Response(status=404)
    new_data = mongodb_list_to_dict(data)[team_id]
    js = json.dumps(new_data, default=json_util.default)
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@blueprint.route("/<team_id>", methods=['PATCH'])
@requires_parameters(optional=['name'])
def modify_team(team_id):
    data = json.loads(request.data)
    orig_data = list(g.db.teams.find({'id': team_id}))
    if len(orig_data) == 0:
        return Response(status=404)
    new_data = deepcopy(orig_data[0])
    for key in data:
        new_data[key] = data[key]
    g.db.teams.update(orig_data[0], new_data)
    resp = Response(status=204)
    return resp

@blueprint.route("/<team_id>", methods=['DELETE'])
@requires_no_parameters
def delete_method(team_id):
    data = list(g.db.teams.find({'id': team_id}))
    if len(data) == 0:
        return Response(status=404)
    g.db.teams.remove({'id': team_id})
    return Response(status=204)