import ast
import functools
import json
import logging

from odoo.addons.restful.common import extract_arguments, invalid_response, valid_response

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


def validate_token(func):
    """."""
    print("restful")
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        print('wrap')
        """."""
        headers = request.httprequest.headers
        access_token = get_access_token(headers, kwargs)
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)


        request.session.session_token = access_token_data.user_id._compute_session_token(request.session.sid)
        # self.env.user._compute_session_token(request.session.sid)
        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]

def get_access_token(headers, params):
    if headers.get('access_token'):
        access_token = headers.get('access_token')
        return access_token
    elif params.get('access_token'):
        access_token = params.get('access_token')
        return access_token
    else:
        return False


def get_url_base():
    config = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    if config:
        return config
    return 'https://test.diligo.vn:15000'


class APIController(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    @validate_token
    @http.route(_routes, type="http", auth="public", methods=["GET"], csrf=False)
    def get(self, model=None, id=None, **payload):
        try:
            ioc_name = model
            model = request.env[self._model].search([("model", "=", model)], limit=1)
            if model:
                domain, fields, offset, limit, order = extract_arguments(**payload)
                data = request.env[model.model].search_read(
                    domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                )

                if id:
                    domain = [("id", "=", int(id))]
                    data = request.env[model.model].search_read(
                        domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                    )
                if data:
                    return valid_response(data)
                else:
                    return valid_response(data)
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % ioc_name,
            )
        except AccessError as e:

            return invalid_response("Access error", "Error: %s" % e.name)

    @validate_token
    @http.route(_routes, type="http", auth="public", methods=["POST"], csrf=False)
    def post(self, model=None, id=None, **payload):
        """Create a new record.
        Basic sage:
        import requests

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'charset': 'utf-8',
            'access-token': 'access_token'
        }
        data = {
            'name': 'Babatope Ajepe',
            'country_id': 105,
            'child_ids': [
                {
                    'name': 'Contact',
                    'type': 'contact'
                },
                {
                    'name': 'Invoice',
                   'type': 'invoice'
                }
            ],
            'category_id': [{'id': 9}, {'id': 10}]
        }
        req = requests.post('%s/api/res.partner/' %
                            base_url, headers=headers, data=data)

        """
        fields = payload.get("fields")
        if not fields:
            fields = []
        else:
            fields = fields.split(",")
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        model = request.env[self._model].search([("model", "=", model)], limit=1)
        values = {}
        if model:
            try:
                # changing IDs from string to int.
                for k, v in payload.items():

                    if "__api__" in k:
                        values[k[7:]] = ast.literal_eval(v)
                    else:
                        values[k] = v

                resource = request.env[model.model].create(values)
            except Exception as e:
                request.env.cr.rollback()
                return invalid_response("params", e)
            else:
                data = resource.read(fields=fields)
                if resource:
                    return valid_response(data)
                else:
                    return valid_response(data)
        return invalid_response("invalid object model", "The model %s is not available in the registry." % model, )

    @validate_token
    @http.route(_routes, type="http", auth="public", methods=["PUT"], csrf=False)
    def put(self, model=None, id=None, **payload):
        """."""
        values = {}
        payload = request.httprequest.data.decode()
        payload = json.loads(payload)
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        _model = request.env[self._model].sudo().search([("model", "=", model)], limit=1)
        if not _model:
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % model, 404,
            )
        try:
            record = request.env[_model.model].sudo().browse(_id)
            for k, v in payload.items():
                if "__api__" in k:
                    values[k[7:]] = ast.literal_eval(v)
                else:
                    values[k] = v
            record.write(values)
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e)
        else:
            return valid_response(record.read())

    @validate_token
    @http.route(_routes, type="http", auth="public", methods=["DELETE"], csrf=False)
    def delete(self, model=None, id=None, **payload):
        """."""
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base " % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)])
            if record:
                record.unlink()
            else:
                return invalid_response("missing_record", "record object with id %s could not be found" % _id, 404, )
        except Exception as e:
            request.env.cr.rollback()
            return invalid_response("exception", e.name, 503)
        else:
            return valid_response("record %s has been successfully deleted" % record.id)

    @validate_token
    @http.route(_routes, type="http", auth="public", methods=["PATCH"], csrf=False)
    def patch(self, model=None, id=None, action=None, **payload):
        """."""
        args = []

        payload = request.httprequest.data.decode()
        args = ast.literal_eval(payload)
        try:
            _id = int(id)
        except Exception as e:
            return invalid_response("invalid object id", "invalid literal %s for id with base" % id)
        try:
            record = request.env[model].sudo().search([("id", "=", _id)], limit=1)
            _callable = action in [method for method in dir(record) if callable(getattr(record, method))]
            if record and _callable:
                # action is a dynamic variable.
                res = getattr(record, action)(*args) if args else getattr(record, action)()
            else:
                return invalid_response(
                    "invalid object or method",
                    "The given action '%s ' cannot be performed on record with id '%s' because '%s' has no such method"
                    % (action, _id, model),
                    404,
                )
        except Exception as e:
            return invalid_response("exception", e, 503)
        else:
            return valid_response(res)
