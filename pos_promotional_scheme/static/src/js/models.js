odoo.define('pos_promotional_scheme.models', function (require){
"use strict";

	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var chrome = require('point_of_sale.chrome');
	var gui = require('point_of_sale.gui');
	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var Model = require('web.DataModel');
	var time = require('web.time');
	
	var scheme_available = new Array();
	
	models.load_models({
	    model: 'loyalty.promotional.schemes',
	    fields: ['id','name','from_date','to_date','scheme_type','scheme_basis','available_on','scheme_product',
      		   'locations','buy_a_qty','get_a_qty','discount','qty_disc','buy_a_qty_in_volume','offer_price'],
	    domain: function(self){ return ['&',['from_date','<=',time.date_to_str(new Date())],['to_date','>=',time.date_to_str(new Date())]]; },
	    loaded: function(self,scheme){
	        self.scheme = scheme;
	    },
	});
	models.load_models({
	    model: 'loyalty.available_on',
	    fields: ['id','template_id','product_list'],
	    domain: function(self){ return []; },
	    loaded: function(self,available_on_list){
	        self.available_on_list = available_on_list;
	    },
	});
	models.load_models({
	    model: 'loyalty.qty.disc',
	    fields: ['id','qty','discount'],
	    domain: function(self){ return []; },
	    loaded: function(self,qty_disc){
	        self.qty_disc = qty_disc;
	    },
	});
	
	var OrderlineCollection = Backbone.Collection.extend({
	    model: models.Orderline,
	});
	
	models.Order = models.Order.extend({
		get_orderLineCollection_obj : function(){
			return new OrderlineCollection();
		},
	});
});



