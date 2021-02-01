odoo.define('pos_point_redemption.models', function (require){
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var chrome = require('point_of_sale.chrome');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var Model = require('web.DataModel');
var time = require('web.time');
//var PosDB = require('point_of_sale.DB');
//PosDB = PosDB.include({
//	_partner_search_string : function(partner){
//		console.log("Inherited partner_search_string ",partner);
//		var str = this._super(partner);
//		return str;
//	},
//});
//var _super_partner_search_string = PosDB.prototype._partner_search_string;
//PosDB.prototype._partner_search_string = function(partner){
//	console.log("Inherited partner_search_string ",partner);
//	var str = _super_partner_search_string.call(this,partner);
//	return str;
//};
//At POS Startup, load models
models.load_models({
    model: 'reedem.points',
    fields: ['id','name','unit_of_currency','start_date','end_date','shop_company_ids_1'],
    domain: function(self){ return ['&',['end_date','>=',time.date_to_str(new Date())],['state','=','approve'],['start_date','<=',time.date_to_str(new Date())]]; },
    loaded: function(self,reedemPoints){
        self.reedemPoints = reedemPoints;
    },
});

models.load_models({
    model: 'point.scheme',
    fields: ['id','start_date','end_date','points_basis','invoice_ids','shop_company_ids'],
    domain: function(self){ return ['&',['end_date','>=',time.date_to_str(new Date())],['state','=','approve'],['start_date','<=',time.date_to_str(new Date())]]; },
    loaded: function(self,pointRedemption){
        self.pointRedemption = pointRedemption;
    },
});

models.load_models({
    model: 'point.scheme.product.quantity',
    fields: ['product','points','product_no','product_category','id'],
    loaded: function(self,productQuantity){
        self.productQuantity = productQuantity;
    },
});

models.load_models({
    model: 'product.template',
    fields: ['id','categ_id'],
    loaded: function(self,productTemp){
        self.productTemp = productTemp;
    },
});
models.load_fields('account.journal',['name','for_points']);
models.load_fields('res.partner',['id','reedemable_points_available']);

});