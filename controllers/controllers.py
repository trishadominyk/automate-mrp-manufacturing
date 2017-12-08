# -*- coding: utf-8 -*-
from odoo import http

# class AutomateMrpManufacturing(http.Controller):
#     @http.route('/automate_mrp_manufacturing/automate_mrp_manufacturing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/automate_mrp_manufacturing/automate_mrp_manufacturing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('automate_mrp_manufacturing.listing', {
#             'root': '/automate_mrp_manufacturing/automate_mrp_manufacturing',
#             'objects': http.request.env['automate_mrp_manufacturing.automate_mrp_manufacturing'].search([]),
#         })

#     @http.route('/automate_mrp_manufacturing/automate_mrp_manufacturing/objects/<model("automate_mrp_manufacturing.automate_mrp_manufacturing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('automate_mrp_manufacturing.object', {
#             'object': obj
#         })