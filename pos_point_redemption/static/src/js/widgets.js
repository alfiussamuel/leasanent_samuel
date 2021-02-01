odoo.define('pos_point_redemption.widgets', function (require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var chrome = require('point_of_sale.chrome');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var Model = require('web.DataModel');
var formats = require('web.formats');
var QWeb = core.qweb;
var _t = core._t;
var points_type;
var points_gained_onProduct=0;
var points_gained_onIvoice=0;
var customer_available_points=0;
var available_points =0;
var msg1="";
var	msg3="";
var number_of_point=0;
var current_client;
var amt_product_points=0;

//get_screens will return all the classes screens, as this is require 
//because not all the screen widgets has return from point_of_sale.screens
gui.Gui.include({
	get_screens : function() {
		return this.screen_classes;
	},
});
//It will then set ClientListScreenWidget to return screens object at the time of product screen start(), 
//so that it will be accessible for later use
screens.ProductScreenWidget.include({
	start: function(){
		this._super();
		
// ClientListScreenWidget inherited in start of ProductScreeenWidget
		
		_.each(this.gui.get_screens(),function(screen){
			if(screen.name == 'clientlist'){
				screens.ClientListScreenWidget = screen.widget;
				screen.widget.include({
					show: function(){
						this._super();
				    },
				    save_changes : function(){
				    	this._super();
				    	var self = this;
				    	var change_client=self.pos.get_order().get_client();
				    	var r_point = self.pos.reedemPoints;
				    	if(change_client){
				    		var points_avail_obj=self.pos.partners;
				    		self.gui.screen_instances.payment.available_points(points_avail_obj,change_client.id);
				    		self.pos.get('selectedOrder').set_point_redeems(0);
				    		console.log('\n\n\n customer_available_points =====',customer_available_points);
			    		    self.pos.get('selectedOrder').set_avail_points(customer_available_points);
			    		    self.pos.get('selectedOrder').set_point_gained(points_gained_onProduct+points_gained_onIvoice);
			    		    self.gui.screen_instances.payment.renderElement();
			    		    self.pos.get('selectedOrder').clean_empty_paymentlines();
				    	}else{
			    			 self.pos.get('selectedOrder').set_point_redeems(0);
				    		 self.pos.get('selectedOrder').set_avail_points(0);
				    		 self.pos.get('selectedOrder').set_point_gained(0);
				    		 self.pos.get('selectedOrder').set_missed_points(points_gained_onIvoice+points_gained_onProduct);
				    		 self.gui.screen_instances.payment.renderElement();
				    		 self.pos.get('selectedOrder').clean_empty_paymentlines();
				    	   }
				    },
				});
			}
		});
	},
});
screens.PaymentScreenWidget.include({
	init: function(parent, options){
		this._super(parent, options);
		var self = this;
		var _super_keyboard_handler = self.keyboard_handler;
		self.keyboard_handler = function(event){
			var line = self.pos.get_order().selected_paymentline;
			if(line.cashregister.journal.for_points){
				var key = '';

	            if (event.type === "keypress") {
	                if (event.keyCode === 13) { // Enter
	                	console.log('\n\n\n hi in before validate');
	                    self.validate_order();
	                    console.log('\n\n\n hi in after validate');
	                } else if ( event.keyCode === 190 || // Dot
	                            event.keyCode === 110 ||  // Decimal point (numpad)
	                            event.keyCode === 188 ||  // Comma
	                            event.keyCode === 46 ) {  // Numpad dot
	                    key = self.decimal_point;
	                } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
	                    key = '' + (event.keyCode - 48);
	                } else if (event.keyCode === 45) { // Minus
	                    key = '-';
	                } else if (event.keyCode === 43) { // Plus
	                    key = '+';
	                }
	            } else { // keyup/keydown
	                if (event.keyCode === 46) { // Delete
	                    key = 'CLEAR';
	                } else if (event.keyCode === 8) { // Backspace
	                    key = 'BACKSPACE';
	                }
	            }
	            
            	self.payment_point_input(key);
	            event.preventDefault();
            }else{
            	_super_keyboard_handler.call(self,event);
            }
		}
	},
	show: function(){
		this._super();
		var self = this;
		$('.paymentlines.paymentline-point').hide();
	},
	set_amount_on_points: function(amount,points){
		var self = this;
		var order = self.pos.get_order();
		var pos_shop=self.pos.shop;
		var shop_id=pos_shop.id;
		var pointRedeem = self.pos.reedemPoints;
		if(pointRedeem){
			for (var j=0;j<pointRedeem[0].shop_company_ids_1.length;j++){
				if (pointRedeem[0].shop_company_ids_1[j] == shop_id){
					order.selected_paymentline.set_amount(amount);
	                self.order_changes();
	                self.render_paymentlines();
	                self.$('.paymentline.selected .edit').text(self.format_currency_no_symbol(amount));
	                $('#number-of-point').val(points);
	                console.log('\n\n\n  in if set_amount_on_points customer_available_points ======',customer_available_points);
	                order.set_avail_points(customer_available_points);
	                order.set_point_gained(points_gained_onIvoice+points_gained_onProduct);
	                order.set_point_redeems(points);
	                break;
				}else{
					console.log('\n\n\n  in else set_amount_on_points customer_available_points ======',customer_available_points);
					order.set_avail_points(customer_available_points);
					order.set_point_gained(points_gained_onIvoice+points_gained_onProduct);
					order.set_point_redeems(0);
				}
			}
        }
	},
	get_amount_on_points: function(points){
		var self = this;
		var amount = 0.0;
		var pointRedeem = self.pos.reedemPoints;
    	if(pointRedeem){
			amount = parseInt(points/pointRedeem[0].unit_of_currency);
		}
		return amount;
	},
	render_paymentlines: function(){
		this._super();
		var self = this;
		var line = this.pos.get_order().selected_paymentline;
		if(line && !line.cashregister.journal.for_points){
			$('.paymentlines.paymentline-point').hide();
			if(available_points > 0){
				console.log('\n\n\n  in if render_paymentlines available_points ======',available_points);
        		$('#available-point-lable').text("Customer Available Point(s) is : "+available_points);
        	}else{
        		console.log('\n\n\n  in else render_paymentlines customer_available_points ======',customer_available_points);
        		$('#available-point-lable').text("Customer Available Point(s) is : "+customer_available_points);
        	}
			if(points_gained_onIvoice+points_gained_onProduct>=0){
     			$('#point-earning-text-msg').text("You earned "+(points_gained_onIvoice+points_gained_onProduct)+" point(s) on this order");
		   	}
		}else{
			var order = self.pos.get_order();
			var client = order.get_client();
			if(client){
				console.log('\n\n\n  in else  if client render_paymentlines available_points ======',available_points);
				$('#available-point-lable').text("Customer Available Point(s) is : "+available_points);
			   	if(points_gained_onIvoice+points_gained_onProduct>=0){
	     			$('#point-earning-text-msg').text("You earned "+(points_gained_onIvoice+points_gained_onProduct)+" point(s) on this order");
			   	}
			}else{
				if(points_gained_onIvoice+points_gained_onProduct>=0){
					$('#point-earning-text-msg').text("You missed "+(points_gained_onIvoice+points_gained_onProduct)+" point(s) on this order");
				}
			}
		}
	},
	payment_point_input: function(input){
		var self = this;
		console.log('\n\n\n in payment_point_input customer_available_points==== ',customer_available_points);
		available_points = customer_available_points;
		if(input == '.'){
			return;
		}
			var newbuf = self.gui.numpad_input(self.inputbuffer, input, {'firstinput': self.firstinput});
			if(newbuf > available_points){
				this.gui.show_popup('alert',{
	                'title': _t('Warning'),
	                'body':  _t('Points not available'),
	            });
	            return;
			}
	        self.firstinput = (newbuf.length === 0);
	
	        // popup block inputs to prevent sneak editing. 
	        if (self.gui.has_popup()) {
	            return;
	        }
	        if(newbuf){
	        	console.log('\n\n\n newbuf ======',newbuf);
	        	available_points = available_points - parseInt(newbuf);
	        }
	        if (newbuf !== self.inputbuffer) {
	            self.inputbuffer = newbuf;
	            var points = self.inputbuffer;
	            if (self.inputbuffer !== "-") {
	            	points = formats.parse_value(self.inputbuffer, {type: "int"}, 0);
	            }
	            var order = self.pos.get_order();
	            if (order.selected_paymentline) {
	                var amount = self.get_amount_on_points(points);
	                self.set_amount_on_points(amount,self.inputbuffer);
	            }
	        }
	},
	click_numpad: function(button) {
		console.log('\n\n\n click_numpad');
		var self = this;
		var paymentlines = this.pos.get_order().get_paymentlines();
		var flag = true;
		for (var i = 0; i < paymentlines.length; i++) {
			if(paymentlines[i].selected &&  paymentlines[i].cashregister.journal.for_points){
				flag = false;
				break;
			}
		}
		if(flag){
			self._super(button);
			$('.paymentlines.paymentline-point').hide();
		}else{
			self.payment_point_input(button.data('action'));
		}
	},
	click_delete_paymentline: function(cid){
        this._super(cid);
        $('.paymentlines.paymentline-point').hide();
    },
	click_paymentline: function(cid){
		console.log('\n\n\n click_paymentline');
		var self = this;
		self._super(cid);
        var lines = this.pos.get_order().get_paymentlines();
        for ( var i = 0; i < lines.length; i++ ) {
            if (lines[i].cid === cid) {
                if(lines[i].cashregister.journal.for_points){
                	$('.paymentlines.paymentline-point').show();
                	$('#number-of-point').focus();
                }
                else{
                	$('.paymentlines.paymentline-point').hide();
                	$('#available-point-lable').text("Customer Available Point(s) is : "+available_points);
                }
                break;
            }
        }
    },
	click_paymentmethods: function(id) {
    	this._super(id);
    	var self = this;
    	console.log('\n\n\n available_points =====',available_points);
    	var cashregister = null;
    	for ( var i = 0; i < this.pos.cashregisters.length; i++ ) {
    		if ( this.pos.cashregisters[i].journal_id[0] === id ){
    			cashregister = this.pos.cashregisters[i];
    			break;
    		}
    	}
    	var currentOrder = self.pos.get("selectedOrder");
    	var partners = self.pos.partners;
        var pointsProductQuantity = self.pos.productQuantity;
        var pointRedeem = self.pos.pointRedemption;
        var subtotal = parseInt(currentOrder.get_subtotal());
        points_type = cashregister.journal.for_points;
        current_client = currentOrder.get_client();
        self.calculate_points(currentOrder,pointsProductQuantity,pointRedeem);
        if(pointRedeem){
 		   self.calculate_points_onInvoice((subtotal - amt_product_points),pointRedeem);
 	   	}
        if(points_type){
     	   if(!current_client){
     		  self.pos.get_order().clean_empty_paymentlines();
     	      self.reset_input();
     	      self.render_paymentlines();
     	      self.order_changes();
     	     self.$('.paymentlines.paymentline-point').hide();
     		  self.gui.show_popup('alert',{
	                'title': _t('Warning'),
	                'body':  _t('Please select Customer to redeem Points'),
	            });
	            return;
     	   }
     	   if(current_client){
     		   $('.paymentlines.paymentline-point').show();
     		   self.available_points(partners,current_client.id);
     		   if(available_points > 0){
	        		$('#available-point-lable').text("Customer Available Point(s) is : "+available_points);
	        	}else{
	        		$('#available-point-lable').text("Customer Available Point(s) is : "+customer_available_points);
	        	}
     		   $('#number-of-point').focus();
     		   
     		   if(points_gained_onIvoice+points_gained_onProduct>=0){
         			$('#point-earning-text-msg').text("You earned "+(points_gained_onIvoice+points_gained_onProduct)+" point(s) on this order");
     		   }
     	   }
         }else if(!points_type && current_client){
        	 	$('.paymentlines.paymentline-point').hide();
	        	$('#point-earning-text-msg').text("You earned "+(points_gained_onIvoice+points_gained_onProduct)+" point(s) on this order");
	        	self.available_points(partners,current_client.id);//calling
	        	currentOrder.set_avail_points(customer_available_points);
	        	currentOrder.set_point_gained(points_gained_onIvoice+points_gained_onProduct);
	        	if(available_points > 0){
	        		$('#available-point-lable').text("Customer Available Point(s) is : "+available_points);
	        	}else{
	        		$('#available-point-lable').text("Customer Available Point(s) is : "+customer_available_points);
	        	}
         }else{
  		   $('.paymentlines.paymentline-point').hide();
  		   currentOrder.set_point_redeems(0);
  		   currentOrder.set_avail_points(0);
  		   currentOrder.set_point_gained(0);
  		   currentOrder.set_missed_points(points_gained_onIvoice + points_gained_onProduct);
		   if(points_gained_onIvoice+points_gained_onProduct >= 0){
			   $('#point-earning-text-msg').text("You missed "+(points_gained_onIvoice+points_gained_onProduct)+" point(s) on this order");
      		}
	   }
    },
    calculate_points:function(current_order,get_points_on_qty,points_details){
    	points_gained_onProduct=0;
	   	var currentOrderLines=current_order.orderlines;  
    	var shop = this.pos.shop;
        var shop_id=shop.id;
    	var product_points=0;
    	var orderline_product_qty=0;
    	amt_product_points=0;
    	for (var points in points_details)
		{
    		for (var shop in points_details[points].shop_company_ids)
			{
    			if (points_details[points].shop_company_ids[shop]==shop_id)
				{
    				var points_basis = points_details[points].points_basis
    				var invoice_ids = points_details[points].invoice_ids 
    				if(points_basis=="on_product_quantity")
    					{
							var point_redemption_id = parseInt(points_details[points].id)
							for (var p in get_points_on_qty)
								{
									if(get_points_on_qty[p].product_no[0] == point_redemption_id)
									{
										product_points = get_points_on_qty[p].points
										for(var line in currentOrderLines['models'])
										{
											orderline_product_qty = currentOrderLines['models'][line].get_quantity()
											var product_price = currentOrderLines['models'][line].get_product().list_price;
											if(get_points_on_qty[p].product)
											{
												var product_id = get_points_on_qty[p].product[0]
												var orderline_product_id = currentOrderLines['models'][line].get_product().id
											
												if(orderline_product_id == product_id) 
												{
													amt_product_points = (amt_product_points +(product_price*orderline_product_qty));
													points_gained_onProduct = parseInt(points_gained_onProduct) + parseInt(orderline_product_qty)*(product_points) 
												}
											}
											else
											{
												var orderline_product_category = currentOrderLines['models'][line].product.product_tmpl_id;
												var category_id = this.get_category_id(orderline_product_category);
												var prod_category =get_points_on_qty[p].product_category[0];
												if(category_id==prod_category) 
												{
													amt_product_points = (amt_product_points +(product_price*orderline_product_qty));
													points_gained_onProduct = parseInt((points_gained_onProduct) + parseInt(orderline_product_qty)*(product_points));
												}
											}
										}
									}
								}
    					}
				}
			}
		}
    },
    calculate_points_onInvoice:function(invoice_total,point_release_obj){
    	points_gained_onIvoice=0;
		var pos_shop=this.pos.shop;
		var shop_id=pos_shop.id;
		for(var points in point_release_obj){   
			for (var loc in point_release_obj[points].shop_company_ids){
				if (point_release_obj[points].shop_company_ids[loc]==shop_id){
					for(var i=0;i<point_release_obj.length;i++){
						if(point_release_obj[i].points_basis=="sale_invoice"){
							points_gained_onIvoice=parseInt((invoice_total*point_release_obj[i].invoice_ids)/100)
						}
					}
				}
			}
		}
    },
	available_points:function(available_points_obj,c_id){
		if(available_points_obj){
			for(var i=0;i<available_points_obj.length;i++){
				if(available_points_obj[i].id==c_id){
					customer_available_points=available_points_obj[i].reedemable_points_available;
					available_points=available_points_obj[i].reedemable_points_available;
					break;
				}
				
			}
		}
	},

});

//Extend order models
var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
	initialize : function(attributes,options){
		_super_order.initialize.call(this,attributes,options);
		this.set({
			point_gained: (points_gained_onIvoice+points_gained_onProduct),
    	 	point_redeems: 0,
    	 	avail_points: customer_available_points,
		});
	},
	add_paymentline : function(cashregister){
		var self = this;
		var flag = true;
		var paymentlines = self.pos.get('selectedOrder').get_paymentlines();
		if(paymentlines.length > 0 && cashregister.journal.for_points){
			_.each(paymentlines, function(paymentline){
				if(paymentline.cashregister.journal.for_points){
					flag = false;
				}
			});
			if(flag){
				_super_order.add_paymentline.call(self,cashregister);
			}
		}else{
			_super_order.add_paymentline.call(self,cashregister);
		}
	},
	export_as_JSON : function(){
        var export_=_super_order.export_as_JSON.call(this);
        export_.gained_points=this.get_point_gained();
        export_.redeems_point=this.get_point_redeems();
        export_.points_avail=this.get_avail_points();
        export_.logo =  this.pos.company_logo_base64;
        return export_;
	},
	export_for_printing : function(){
        var export_=_super_order.export_for_printing.call(this);

        export_.gained_points=this.get_point_gained();
        export_.missed_points=this.get_missed_points();
        export_.redeems_point=this.get_point_redeems();
        export_.points_avail=this.get_avail_points();
        
        return export_;
        
	},
	remove_paymentline: function(line){
		var order = this.pos.get_order();
		var points = order.get_point_redeems();
        if(line.cashregister.journal.for_points && points > 0){
        	available_points = parseInt(available_points) + parseInt(points);
        	order.set_point_redeems(0);
        }
        _super_order.remove_paymentline.call(this, line);
    },
	finalize: function(){
		var self = this;
		var order = self.pos.get_order();
		var client = order.get_client();
		if(client){
			var model = 'res.partner';
	        var fields = ['name','street','city','state_id','country_id','vat','phone','zip','mobile','email','barcode','write_date','id','reedemable_points_available'];
	        var domain = [['customer','=',true],['id','=',client.id]];
			var records = new Model(model)
	        .query(fields)
	        .filter(domain)
	        .all();
			records.then(function(result){
				var partners = self.pos.partners;
				self.pos.partners = result;
				for(var i = 0; i < partners.length; i++){
					if(partners[i].id == result[0].id){
						self.pos.partners[i] = result[0];
					}
				}
			});
		}
		_super_order.finalize.call(self);
    },
	set_point_gained:function(point_gained){
    	this.set('point_gained',point_gained)
    },
    set_point_redeems:function(point_redeems){
    	this.set('point_redeems',point_redeems);
    },
    set_avail_points:function(avail_points){
    	this.set('avail_points',avail_points);
    },
    set_missed_points: function(missed_points){
    	this.set('missed_points',missed_points);
    },
    
    get_missed_points:function(){
    	return this.get('missed_points');
    },
    get_point_gained:function(){
    	return this.get('point_gained');
    },
    get_point_redeems:function(){
    	return this.get('point_redeems');
    },
    get_avail_points:function(){
    	return this.get('avail_points');
    },
});

});