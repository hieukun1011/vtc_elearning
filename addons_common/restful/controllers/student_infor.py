import logging

from odoo.addons.restful.common import (
	valid_response,
	invalid_response
)
from odoo.addons.restful.controllers.main import (
	validate_token
)
from werkzeug import urls

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class StudentInfor(http.Controller):

	@validate_token
	@http.route("/api/request/update_infor_student", type="http", auth="public", methods=["POST"], csrf=False, cors="*")
	def update_infor_student_request(self, **payload):
		student = request.env['student.student'].sudo().search([('user_id', '=', request.uid)])
		Approval = request.env['approval.request']
		ctg_id = request.env.ref('vtc_elearning.approval_category_data_info_student', raise_if_not_found=False)
		approver_ids = []
		for rec in ctg_id.sudo().user_ids:
			approver_ids.append([0, 0, {
				'user_id': rec.sudo().id
			}])
		val = {
			'name': "Yêu cầu thay đổi thông tin của học viên {}".format(student.name),
			'student_id': student.id,
			'new_name': payload.get('name'),
			'new_birth': payload.get('birth'),
			'new_phone': payload.get('phone'),
			'category_id': ctg_id.sudo().id,
			'request_owner_id': request.uid,
			'approver_ids': approver_ids
		}
		approve = Approval.sudo().create(val)
		approve.sudo().action_confirm()
		return valid_response('Vui lòng chờ quản trị viên phê duyệt')

	def get_url_base(self):
		config = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
		if config:
			return config
		return 'https://test.diligo.vn:15000'

	@validate_token
	@http.route("/api/get/infor_student", type="http", auth="public", methods=["GET", "OPTIONS"], csrf=False, cors="*")
	def get_infor_student_by_id(self, **payload):
		print(request.uid)
		values = []
		base_url = StudentInfor.get_url_base(self)
		user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
		student = request.env['student.student'].sudo().search([('user_id', '=', user.id)])
		if not student:
			return invalid_response(
				"Kiểm tra xem người đang đăng nhập đã là student chưa, nếu có rồi thì kiểm tra xem trong thằng student này đã có tài khoản chưa")
		# cấp độ học
		datas = {'id': student.id,
		         'name': student.name,
		         'avatar': urls.url_join(base_url,
		                                 '/web/image?model=student.student&id={0}&field=avatar'.format(
			                                 student.id)),
		         'birth': student.birth,
		         'phone': student.phone,
		         'email': student.email,
		         'position': {'id': student.position.id, 'name': student.position.name} or '',
		         'work_unit': student.work_unit,
		         'res_country_state': {'id': student.res_country_state.id,
		                               'name': student.res_country_state.name} or '',
		         'res_country_ward': {'id': student.res_country_ward.id, 'name': student.res_country_ward.name} or '',
		         'res_country_district': {'id': student.res_country_district.id,
		                                  'name': student.res_country_district.name} or '',
		         }
		values.append(datas)
		return valid_response(values)
