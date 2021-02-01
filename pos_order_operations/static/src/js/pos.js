odoo.define('pos_order_operations.pos_order_operations', function (require) {
"use strict";

	var models = require('point_of_sale.models');
	var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var PosPopWidget = require('point_of_sale.popups');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var QWeb = core.qweb;
    var _t = core._t;

	models.load_models({
	    model: 'pos.order',
	    fields: ['id','pos_reference','date_order','partner_id','amount_total','posreference_number'],
	    domain: function(self){ 
	    	var from = moment(new Date()).subtract(self.config.wv_order_date,'d').format('YYYY-MM-DD')+" 00:00:00";
	    	if(self.config.pos_order_reprint){
	    		return [['date_order','>',from],['amount_total','>',0]];
	    	} 
	    	else{
	    		return [['id','=',0]];
	    	} 
	    },
	    loaded: function(self,old_order){
	    	self.old_order = old_order;
	    },
	});
	screens.ReceiptScreenWidget.include({
	    render_receipt: function() {
	    	var self = this;
	        this._super();
	        var order = self.pos.get_order();
	        var barcodeval = order.uid.replace(/-/g, '');
	        $("#pos-order-return").barcode(barcodeval, "ean13",{barWidth:2, barHeight:50});
	    },
    });
    var PosOrderReturnWidget = PosPopWidget.extend({
        template: 'PosOrderReturnWidget',
	    
        renderElement: function(options){
            this._super();
            var self = this;
            var selectedOrder = this.pos.get_order();
            this.$('.return_all_order_button').click(function(){
            	var order_id = $(this).data('order_id');
            	var order_name = $(this).data('order_name');

           		$.each($(".return_product_qty"), function(index, value) {
				 	var qty = $(this).data('qty');
				 	var discount = $(this).data('discount');
				 	var line_id = $(this).data('line_id');
				 	var product_id = $(this).data('product-id');
				 	var price_unit = $(this).data('price_unit');
				 	var product = self.pos.db.get_product_by_id(product_id);
                	selectedOrder.add_product(product, {
                        quantity: parseFloat(qty),
                        price: - price_unit,
                        discount: discount,
                    });
                    selectedOrder.selected_orderline.db_line_id = line_id;
            	});
            	selectedOrder.order_id = order_id;
                selectedOrder.order_name = order_name;
            	self.gui.show_screen('products');
	        });
	        this.$('.return_order_button').click(function(){
	        	var order_id = $(this).data('order_id');
            	var order_name = $(this).data('order_name');
           		$.each($(".return_product_qty"), function(index, value) {
				 	var qty = $(this).val();
				 	var discount = $(this).data('discount');
				 	var line_id = $(this).data('line_id');
				 	var product_id = $(this).data('product-id');
				 	var price_unit = $(this).data('price_unit');
				 	var product = self.pos.db.get_product_by_id(product_id);
				 	if(parseFloat(qty) > 0){
	                	selectedOrder.add_product(product, {
	                        quantity: - parseFloat(qty),
	                        price: price_unit,
	                        discount: discount,
	                    });                    
	                    selectedOrder.selected_orderline.db_line_id = line_id;
	                }
            	});
            	selectedOrder.order_id = order_id;
                selectedOrder.order_name = order_name;
            	self.gui.show_screen('products');
	        });
        },
        show: function(options){
            this.options = options || {};
            var self = this;
            this._super(options); 
            this.renderElement(options);
        },
    });

    gui.define_popup({
        'name': 'pos-order-return', 
        'widget': PosOrderReturnWidget,
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.reference_number = this.uid.replace(/-/g, '');
            json.order_id = this.order_id || 0;
            json.order_name = this.order_name||0;
            return json;
        },
        init_from_JSON: function(json) {
            _super_order.init_from_JSON.apply(this,arguments);
            this.reference_number = json.uid.replace(/-/g, '');
            this.order_id = '' ;
            this.order_name = '';
        },
        export_for_printing: function(){
        	var json = _super_order.export_for_printing.apply(this);
        	json.order_id = this.order_id || false;
            json.order_name = this.order_name|| false;
            // console.log("Testing>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",json.order_id,json.order_name);
            return json;
        },
    });

    var OrderlineSuper = models.Orderline;
    models.Orderline = models.Orderline.extend({
        initialize: function(){
            var self = this;
            self.order_line_id = 0;
            self.db_line_id = 0;
            OrderlineSuper.prototype.initialize.apply(this, arguments);   
        },
        export_as_JSON: function(){
            var data = OrderlineSuper.prototype.export_as_JSON.apply(this, arguments);
            data.order_line_id = this.db_line_id || 0;
            return data;
        }
    });
	var OrdersReceiptScreenWidget = screens.ReceiptScreenWidget.extend({
        template: 'OrdersReceiptScreenWidget',
        click_next: function(){
            this.gui.show_screen('products');
        },
        click_back: function(){
            this.gui.show_screen('products');
        },
        render_receipt: function(){
            self = this;
            var order = self.pos.get_order();
            self.$('.pos-receipt-container').html(order.receipt_reprint_val);
            order.receipt_reprint_val = "";
        },
        print_web: function(){
            window.print();
        },
    });

    gui.define_screen({name:'wv-orders-receipt', widget: OrdersReceiptScreenWidget});
    var PosOrderPopupWidget = PosPopWidget.extend({
    template: 'PosOrderPopupWidget',
        renderElement: function(){
            this._super(); 
            var self = this;
            $(".print_normal_printer").click(function(){
                var order_id = $(this).data('id');
	            new Model('pos.config').call('get_order_detail',[order_id]).then(function(result){
	                var order = self.pos.get_order();
	                order.receipt_reprint_val = QWeb.render('PosTicketReprint',{
	                    widget:self,
	                    order: result.order,
	                    change: result.change,
	                    orderlines: result.order_line,
	                    discount_total: result.discount,
	                    paymentlines: result.payment_lines,
	                    receipt: order.export_for_printing(),
	                });
	                self.gui.show_screen('wv-orders-receipt');
	                $("#pos-order-return").barcode(result.order.posreference_number, "ean13",{barWidth:2, barHeight:50});
	            });
            }); 
            $(".print_thermal_printer").click(function(){
            	var order_id = $(this).data('id');
	            new Model('pos.config').call('get_order_detail',[order_id]).then(function(result){
	                var order = self.pos.get_order();
	                var env = {
			            widget:  self,
			            receipt: self.pos.get_order().export_for_printing(),
			            order: result.order,
			            tax_details2:result.tax_details2,
			            orderlines: result.order_line,
			            change: result.change,
			            discount_total: result.discount,
			            paymentlines: result.payment_lines,
			        };
			        var receipt = QWeb.render('XmlReceiptCopy',env);
			        self.pos.proxy.print_receipt(receipt);
	            });
                      
            	
            });
            $(".download_normal_printer").click(function(){
            	var order_id = $(this).data('id');
	            // self.chrome.do_action('pos_orders_reprint.pos_receipt_report',{additional_context:{
             //        active_ids:[order_id],
             //    }});
	            self.chrome.do_action('pos_order_operations.pos_receipt_report',{additional_context:{
                    active_ids:[order_id],
                }});
            });
            $(".wv_pos_reorder").click(function(){
                var order_id = $(this).data('id');
                var order = self.pos.get_order();
                var orderlines = order.get_orderlines();
                if(orderlines.length == 0){
                    new Model('pos.config').call('get_reorder_detail',[order_id]).then(function(result){
                        order.set('client',undefined);
                        if(result.partner_id){
                            order.set_client(self.pos.db.get_partner_by_id(result.partner_id));
                        }
                        for(var i=0;i<result.order_line.length;i++){
                            var product = self.pos.db.get_product_by_id(result.order_line[i]['product_id']);
                            order.add_product(product,{'quantity':result.order_line[i]['qty']});
                        }
                        self.gui.back();
                    },function(err,event){
                        event.preventDefault();
                        self.gui.show_popup('error',{
                            'title': _t('Error: Could not Save Changes'),
                            'body': _t('Your Internet connection is probably down.'),
                        });
                    });
            }
            else{
                self.gui.show_popup('error',{
                        'title': _t('Error'),
                        'body': _t('Please remove all products from cart and try again.'),
                    });
            }
            }); 
            $('.order_return_search').click(function(){
            	var order_id = $(this).data('id');
            	if(order_id != ''){
	            	new Model('pos.order').call('search_return_orders',[order_id]).then(function(result){
	            			if(result != undefined){
	        					self.gui.show_popup('pos-order-return',result);
	            			}
	            			else{
	            				alert("Your Order Ref is not valid");
	            			}
				        },function(err,event){
				            event.preventDefault();
				            self.gui.show_popup('error',{
				                'title': _t('Error'),
				                'body': _t('Your Internet connection is probably down.'),
				            });
				        });
	            	}
	            else{
	            	alert("Enter your Order No.");
	            }
		    });	
        },

        show: function(options){
            this.options = options || {};
            var self = this;
            this._super(options); 
            this.renderElement();
        },
    });

    gui.define_popup({
        'name': 'pos-order-popup', 
        'widget': PosOrderPopupWidget,
    });
    
	var OrderListScreenWidget = screens.ScreenWidget.extend({
	    template: 'OrderListScreenWidget',

	    auto_back: true,
	    renderElement: function() {
	        var self = this;
	        this._super();
	       	this.$('.back').click(function(){
	            self.gui.back();
	        });
	        var search_timeout = null;
	       	this.$('.searchbox input').on('keyup',function(event){
	            var query = this.value;
	            if(query==""){
	            	self.render_list(self.pos.old_order);
	            }
	            else{
	            	self.perform_search(query);
	            }
	        });
	        this.$('.client-list-contents').delegate('.wv_checkout_button','click',function(event){
            	var order_id = $(this).data('id');
            	var order = self.pos.get_order();
	            new Model('pos.config').call('get_order_detail',[order_id]).then(function(result){
	        		self.gui.show_popup('pos-order-popup',{
	                    order: result.order,
	                    change: result.change,
	                    orderlines: result.order_line,
	                    discount_total: result.discount,
	                    paymentlines: result.payment_lines,
	                    receipt: order.export_for_printing(),
	        		});
		        },function(err,event){
		            event.preventDefault();
		            self.gui.show_popup('error',{
		                'title': _t('Error: Could not Save Changes'),
		                'body': _t('Your Internet connection is probably down.'),
		            });
		        });
		});
	    },
	    show: function(){
	        var self = this;
	        this._super();
	        this.renderElement();
	        this.render_list(self.pos.old_order);
	    },

	    perform_search: function(query){
	    	var old_order = this.pos.old_order;
	    	var results = [];
	        for(var i = 0; i < old_order.length; i++){
	        	var res = this.search_quotations(query, old_order[i]);
	        	if(res != false){
	        	results.push(res);
	        }
	        }
	        this.render_list(results);
	    },
	    search_quotations: function(query,old_order){
	        try {
	            query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
	            query = query.replace(' ','.+');
	            var re = RegExp("([0-9]+):.*?"+query,"gi");
	        }catch(e){
	            return [];
	        }
	        var results = [];
            var r = re.exec(this._quotations_search_string(old_order));
            if(r){
                var id = Number(r[1]);
                return this.get_quotations_by_id(id);
            }
	        return false;
	    },
	    get_quotations_by_id:function(id){
	    	var old_order = this.pos.old_order;
	    	for(var i=0;i<old_order.length;i++){
	    		if(old_order[i].id == id){
	    			return old_order[i];
	    		}
	    	}
	    },
	    _quotations_search_string: function(old_order){
		        var str =  old_order.pos_reference;
		        str += " " +old_order.posreference_number;
		        if(old_order.partner_id){
		            str += '|' + old_order.partner_id[1];
		        }
		        str = '' + old_order.id + ':' + str.replace(':','') + '\n';
		        return str;
		    },
	    render_list: function(quotationsVal){
	    	var self = this;
	        var contents = this.$el[0].querySelector('.client-list-contents');
	        contents.innerHTML = "";
	        var quotations = quotationsVal;
	        for(var i = 0;i<quotations.length; i++){
	            var quotation    = quotations[i];
                var clientline_html = QWeb.render('WVOrderLine',{widget: self, order:quotation});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];
	            contents.appendChild(clientline);
	        }
	    },

	    close: function(){
	        this._super();
	    },
	});
	gui.define_screen({name:'allOrderlist', widget: OrderListScreenWidget});


	var POSOrderListButton = screens.ActionButtonWidget.extend({
        template: 'POSOrderListButton',
        button_click: function(){
        	var self = this;
        	var quotation = this.pos.old_order;
        	var available_qt = []
        	for(var i=0;i<quotation.length;i++){
        		available_qt.push(quotation[i].id)
        	}
	        	var config_id = self.pos.config.id
	        	var from = moment(new Date()).subtract(self.pos.config.wv_order_date,'d').format('YYYY-MM-DD')+" 00:00:00";
				new Model('pos.order').call('search_read',[[['id','!=',available_qt],['date_order','>',from],['amount_total','>',0]],['id','name','pos_reference','date_order','partner_id','amount_total','posreference_number']]).then(function(order){
						for(var k=0;k<order.length;k++){
							self.pos.old_order.push(order[k]);
						}
    				self.gui.show_screen('allOrderlist',{},'refresh');

			        },function(err,event){
			            event.preventDefault();
			            self.gui.show_popup('error',{
			                'title': _t('Error: Could not Save Changes'),
			                'body': _t('Your Internet connection is probably down.'),
			            });
		      });
        },
    });
	screens.define_action_button({
        'name': 'POS Order List',
        'widget': POSOrderListButton,
        'condition': function(){
            return this.pos.config.pos_order_reprint;
        },
    });
    
});
