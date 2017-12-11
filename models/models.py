# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_round

class mrp_production_inherit(models.Model):
	_inherit = 'mrp.production'

	method = fields.Selection([('0', 'Automatic'), ('1', 'Manual')], default='0', help="Determinant whether method of production is manual or automatic")

class mrp_manufacturing_qty(models.TransientModel):
	_inherit = 'change.production.qty'
	
	@api.multi
	def auto_change_qty(self):
		for product in self.env['mrp.production'].search([('state','=','confirmed')]):
			quantity = self.env['mrp.bom'].browse(product.bom_id).id.product_qty
			
			# check stock if needed restock
			if product.product_qty > self.env['product.product'].browse(product.product_id).id.qty_available:
				# check qty in bill of material
				if product.product_qty > quantity:
					# if not enough for given slices must double manufacture quantity
					while product.product_qty > quantity:
						quantity = quantity + self.env['mrp.bom'].browse(product.bom_id).id.product_qty
				# change manufacturing qty
				vals = {
					'mo_id':product.id,
					'product_qty': quantity,
					'create_uid':product.write_uid.id,
					'create_date':datetime.now(),
					'write_date':datetime.now(),
				}
				self.create(vals)
				
				for move in self.env['change.production.qty'].search([('mo_id','=',product.id)]):
					move.change_prod_qty()
			else:
				# cancel
				product.action_cancel()

class automate_mrp_manufacturing(models.TransientModel):
	_inherit = 'mrp.product.produce'

	@api.multi
	def auto_produce_product(self):
		self.confirmed_to_progress()
		for product in self.env['mrp.production'].search([('state','=','progress')]):
			product.button_mark_done()


	@api.multi
	def confirmed_to_progress(self):
		# confirmed to progress
		for product in self.env['mrp.production'].search([('state','=','confirmed')]):
			# insert into product.produce
			vals = {
				'product_id':product.product_id.id,
				'product_uom_id':product.product_uom_id.id,
				'write_uid':product.write_uid.id,
				'create_date':datetime.now(),
				'production_id':product.id,
				'product_qty':product.product_qty,
				'write_date':datetime.now(),
				'lot_id':self.env['stock.production.lot'].search([('product_id','=',product.product_id.id)]),
			}
			self.create(vals)
			
			# do produce method
			quantity = product.product_qty

			for m in self.env['mrp.product.produce'].search([('production_id','=',product.id)]):
				moves = m.production_id.move_raw_ids
				for move in moves.filtered(lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel')):
					if move.unit_factor:
						rounding = move.product_uom.rounding
						move.quantity_done_store += float_round(quantity*move.unit_factor, precision_rounding=rounding)
				
				moves = m.production_id.move_finished_ids.filtered(lambda x: x.product_id.tracking == 'none' and x.state not in ('done', 'cancel'))
				for move in moves:
					rounding = move.product_uom.rounding
					if move.product_id.id == m.production_id.product_id.id:
						move.quantity_done_store += float_round(quantity, precision_rounding=rounding)
					elif move.unit_factor:
						move.quantity_done_store += float_round(quantity*move.unit_factor, precision_rounding=rounding)

				# check finished lots method
				lots = self.env['stock.move.lots']
				produce_move = m.production_id.move_finished_ids.filtered(lambda x: x.product_id == m.product_id and x.state not in ('done', 'cancel'))
				if produce_move and produce_move.product_id.tracking != 'none':
					if not m.lot_id:
						raise UserError(_('You need to provide a lot for the finished product'))
					existing_move_lot = produce_move.move_lot_ids.filtered(lambda x: x.lot_id == m.lot_id)
					if existing_move_lot:
						existing_move_lot.quantity += m.product_qty
						existing_move_lot.quantity_done += m.product_qty
					else:
						vals = {
							'move_id': produce_move.id,
							'product_id': produce_move.product_id.id,
							'production_id': m.production_id.id,
							'quantity': m.product_qty,
							'quantity_done': m.product_qty,
							'lot_id': m.lot_id.id,
						}
						lots.create(vals)
					for move in m.production_id.move_raw_ids:
						for movelots in move.move_lot_ids.filtered(lambda x: not x.lot_produced_id):
							if movelots.quantity_done and m.lot_id:
								#Possibly the entire move is selected
								remaining_qty = movelots.quantity - movelots.quantity_done
								if remaining_qty > 0:
									default = {'quantity': movelots.quantity_done, 'lot_produced_id': m.lot_id.id}
									new_move_lot = movelots.copy(default=default)
									movelots.write({'quantity': remaining_qty, 'quantity_done': 0})
								else:
									movelots.write({'lot_produced_id': m.lot_id.id})

				# product.check_finished_move_lots()
				if m.production_id.state == 'confirmed':
					m.production_id.write({
						'state':'progress',
						'date_start':datetime.now(),
					})