odoo.define('automate_mrp_manufacturing.models_pos_order', function (require){
	"use strict";
	var pos_model = require('point_of_sale.models');
	var pos_screens = require('point_of_sale.screens');
	var models = pos_model.PosModel.prototype.models;
	var Model = require('web.DataModel');


	for(var i=0; i<models.length; i++){
		var model=models[i];
		if(model.model === 'product.product'){
			model.fields.push('to_make_mrp');
		}
	}

	pos_screens.PaymentScreenWidget.include({
		validate_order: function(force_validation) {
			var self = this
			this._super(force_validation);
			var order = self.pos.get_order();
			var order_line = order.orderlines.models;
			var list_product = []
			var due   = order.get_due();
			if (due == 0){
				for (var i in order_line){
					if (order_line[i].product.to_make_mrp){
						if (order_line[i].quantity>0){
							var product_dict = {
								'id': order_line[i].product.id,
								'qty': order_line[i].quantity,
								'product_tmpl_id': order_line[i].product.product_tmpl_id,
								'pos_reference': order.name,
								'uom_id': order_line[i].product.uom_id[0],
							};
						list_product.push(product_dict);
						}
					}
				}
				if (list_product.length){
					new Model("mrp.production")
						.call("create_mrp_from_pos", [1, list_product]).then(function(response){
							new Model('change.production.qty').call('auto_change_qty',[[]]).then(function(){
								new Model('mrp.product.produce').call('auto_produce_product',[[]])
							})
						})
				}
			}
		},
	});

	pos_screens.ReceiptScreenWidget.include({
		click_next: function(){
			this.pos.get_order().finalize();
			location.reload();
		},
	});
});
