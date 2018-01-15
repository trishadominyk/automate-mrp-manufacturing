odoo.define('automate_mrp_manufacturing.models_pos_order', function (require){
	var pos_model = require('point_of_sale.models');
	var pos_screens = require('point_of_sale.screens');
	var models = pos_model.PosModel.prototype.models;
	var Model = require('web.DataModel');

	pos_screens.ReceiptScreenWidget.include({
		click_next: function(){
			this.pos.get_order().finalize();
			
			new Model("change.production.qty").call("auto_change_qty");
			new Model("mrp.product.produce").call("auto_produce_product");
		}
	});
})