odoo.define('aces_pos_product_sync.sync', function (require) {
"use strict";

    var db = require('point_of_sale.DB');
    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');
    var screens = require('point_of_sale.screens');

    models.load_fields("product.product", ['write_date']);

    screens.ProductCategoriesWidget.include({ 
        renderElement: function(){
            var self = this;
            this._super();
            $('#syncbutton').click(function(){
            	var currency_symbol = (self.pos && self.pos.currency) ? self.pos.currency : {symbol:'$', position: 'after', rounding: 0.01, decimals: 2};
            	$('#syncbutton').toggleClass('rotate', 'rotate-reset');
                self.pos.load_new_products(currency_symbol)
            });
        },
    });
    
    db.include({
    	init: function(options){
    		this.currency_symbol = {};
    		this.product_write_date = null;
            this._super(options);
        },
        get_product_write_date: function(){
            return this.product_write_date || "1970-01-01 00:00:00";
        },
        add_products: function(products){
            var self = this;
            this._super(products);
            var product;
            var new_write_date = '';
            var symbol = this.currency_symbol ? this.currency_symbol.symbol : "$";
            for(var i = 0, len = products.length; i < len; i++){
                product = products[i];
                if(product['list_price']) {
                	product['price'] = product['list_price']
                	var unit_name = product.uom_id[1] ? product.uom_id[1] : "";
                	if(product.to_weight){
                		$("[data-product-id='"+product.id+"']").find('.price-tag').html(symbol+" "+product['list_price'].toFixed(2)+'/'+unit_name);
                	} else {
                		$("[data-product-id='"+product.id+"']").find('.price-tag').html(symbol+" "+product['list_price'].toFixed(2));
                	}
                    $("[data-product-id='"+product.id+"']").find('.product-name').html(product.display_name);
                }
                if (this.product_write_date && 
                        this.product_by_id[product.id] &&
                        new Date(this.product_write_date).getTime() + 1000 >=
                        new Date(product.write_date).getTime() ) {
                    continue;
                } else if ( new_write_date < product.write_date ) {
                    new_write_date  = product.write_date;
                }
            }
            this.product_write_date = new_write_date || this.product_write_date;
        },
    });

    var posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_new_products: function(currency_symbol){
            var self = this;
            var def  = new $.Deferred();
            var fields =self.prod_model ? self.prod_model.fields : [];
            var ctx = {
                pricelist: self.pricelist.id,
                display_default_code: false,
            }

            new Model('product.product')
                .query(fields)
                .filter([['sale_ok','=',true],['available_in_pos','=',true],['write_date','>',self.db.get_product_write_date()]])
                .context(ctx)
                .all({'shadow': true})
                .then(function(products){
                	self.db.currency_symbol = currency_symbol;
                    if (self.db.add_products(products)) {
                        product_list_obj.renderElement(self);
                        def.resolve();
                    } else {
                        def.reject();
                    }
                }, function(err,event){ event.preventDefault(); def.reject(); });    
            return def;
        },
        load_server_data: function () {
            var self = this;
            _.each(this.models, function(model){
                if (model && model.model === 'product.product'){
                    self.prod_model = model;
                }
            });
            return posmodel.load_server_data.apply(this, arguments)
        },
    });
});