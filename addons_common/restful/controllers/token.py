import json
import logging

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wrappers
import werkzeug.wsgi
from odoo.addons.restful.common import invalid_response, valid_response
from werkzeug import urls
from odoo import http
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


class AccessToken(http.Controller):
    """."""

    def get_url_base(self):
        config = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if config:
            return config
        return 'https://test.diligo.vn:15000'

    @http.route("/api/auth/token", methods=["POST"], type="http", auth="none", csrf=False, cors="*")
    def token(self, **post):
        """The token URL to be used for getting the access_token:
        Args:
            **post must contain login and password.
        Returns:
            returns https response code 404 if failed error message in the body in json format
            and status code 202 if successful with the access_token.
        Example:
           import requests
           headers = {'content-type': 'text/plain', 'charset':'utf-8'}
           data = {
               'login': 'admin',
               'password': 'admin',
               'db': 'galago.ng'
            }
           base_url = 'http://odoo.ng'
           eq = requests.post(
               '{}/api/auth/token'.format(base_url), data=data, headers=headers)
           content = json.loads(req.content.decode('utf-8'))
           headers.update(access-token=content.get('access_token'))
        """
        base_url = AccessToken.get_url_base(self)
        _token = request.env["api.access_token"]
        params = ["db", "login", "password"]
        params = {key: post.get(key) for key in params if post.get(key)}
        db, username, password = (
            params.get("db"),
            post.get("login"),
            post.get("password"),
        )
        _credentials_includes_in_body = all([db, username, password])
        if not _credentials_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            db = headers.get("db")
            username = headers.get("login")
            password = headers.get("password")
            _credentials_includes_in_headers = all([db, username, password])
            if not _credentials_includes_in_headers:
                # Empty 'db' or 'username' or 'password:
                return invalid_response(
                    "missing error", "either of the following are missing [db, username,password]", 403,
                )
        # Login in odoo database:
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return invalid_response("Access error", "Error: %s" % aee.name)
        except AccessDenied as ade:
            return invalid_response("Access denied", "Login, password or db invalid")
        except Exception as e:
            # Invalid database:
            info = "The database name is not valid {}".format((e))
            error = "invalid_database"
            _logger.error(info)
            return invalid_response("wrong database name", error, 403)

        uid = request.session.uid
        # print(uid.has_group('base.group_user'))
        # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            return invalid_response(401, error, info)

        # Generate tokens
        access_token = _token.find_one_or_create_token(user_id=uid, create=True)
        partner = request.env.user.partner_id.id
        cource_partner = request.env['slide.channel.partner'].sudo().search([('partner_id', '=', partner)])
        student = request.env['student.student'].sudo().search([('user_id', '=', uid)])
        list_cource = list(set([r for r in cource_partner.channel_id]))
        cource_join = []
        for rec in cource_partner:
            data = {
                'id': rec.channel_id.id,
                'progress': rec.completion
            }
            cource_join.append(data)

        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "uid": uid,
                    "user_context": request.session.get_context() if uid else {},
                    "company_id": request.env.user.company_id.id if uid else None,
                    "company_ids": request.env.user.company_ids.ids if uid else None,
                    "partner_id": request.env.user.partner_id.id,
                    "name": student.name,
                    "access_token": access_token,
                    'go_to_backend': base_url + '/web',
                    "company_name": request.env.user.company_name,
                    "currency": request.env.user.currency_id.name,
                    # "company_name": request.env.user.company_name,
                    "country": request.env.user.country_id.name,
                    "contact_address": request.env.user.contact_address,
                    "customer_rank": request.env.user.customer_rank,
                    'cource_join': cource_join,
                    'avatar': urls.url_join(base_url, '/web/image?model=student.student&id={}&field=avatar'.format(
                        student.id)) if student else ''
                }
            ),
        )


    @http.route(["/api/auth/token"], methods=["DELETE"], type="http", auth="none", csrf=False, cors="*")
    def delete(self, **post):
        """Delete a given token"""
        token = request.env["api.access_token"]
        access_token = post.get("access_token")

        access_token = token.search([("token", "=", access_token)], limit=1)
        if not access_token:
            error = "Access token is missing in the request header or invalid token was provided"
            return invalid_response(400, error)
        for token in access_token:
            token.unlink()
        # Successful response:
        return valid_response([{"message": "access token %s successfully deleted" % (access_token,), "delete": True}])