'''
    Copyright (c) 2012 Alexander Abbott

    This file is part of the Cheshire Cyber Defense Scoring Engine (henceforth
    referred to as Cheshire).

    Cheshire is free software: you can redistribute it and/or modify it under
    the terms of the GNU Affero General Public License as published by the
    Free Software Foundation, either version 3 of the License, or (at your
    option) any later version.

    Cheshire is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
    more details.

    You should have received a copy of the GNU Affero General Public License
    along with Cheshire.  If not, see <http://www.gnu.org/licenses/>.
'''
import json, bcrypt, hashlib
from flask import Blueprint, g, redirect, url_for, Response
from flask.ext.login import login_required, login_user, logout_user
from flask.globals import request
from flask_login import UserMixin, current_user
from ScoringServer import login_manager, app
from ScoringServer.utils import requires_parameters, requires_no_parameters, create_error_response

blueprint = Blueprint(__name__, 'session')
url_prefix = '/session'

@login_manager.user_loader
def load_user(username):
    return User(username)

@blueprint.route("/", methods=['GET'])
@login_required
@requires_no_parameters
def get_current_session_info():
    user = g.db.get_specific_user(current_user.get_id())[0]
    user['username'] = current_user.get_id()
    js = json.dumps(user)
    return Response(js, status=200, mimetype='application/json')

@blueprint.route("/", methods=['POST'])
@requires_parameters(required=['username', 'password'])
def create_new_session():
    data = json.loads(request.data)
    if app.config['SERVER']['PASSWORD_HASH'] == 'bcrypt':
        data['password'] = bcrypt.hashpw(data['password'], bcrypt.gensalt(14))
    elif app.config['SERVER']['PASSWORD_HASH'] == 'md5':
        data['password'] = hashlib.md5(data['password']).hexdigest()
    if g.db.get_specific_user(data['username'], data['password']) == []:
        return create_error_response('IncorrectLogin', 'Either the user does not exist or password is incorrect.')
    try:
        login_user(User(data['username']))
    except BaseException, e:
        return create_error_response(type(e).__name__, e.message)
    return redirect(url_for('session.get_current_session_info'), code=201)

@blueprint.route("/", methods=['DELETE'])
def remove_current_session():
    logout_user()
    return Response(status=204)


class User(UserMixin):
    def __init__(self, user):
        self._user = unicode(user)
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return self._user