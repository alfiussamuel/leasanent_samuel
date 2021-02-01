odoo.define('pos_coupons_gift_voucher.pos', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var popups = require('point_of_sale.popups');
    var Model = require('web.DataModel');
    //var date = require('web.date');
    var _t = core._t;

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this,arguments);
            json.coupon_id = this.coupon_id;
            return json;
        },
    });

    models.load_models({
        model: 'pos.gift.coupon',
        fields: ['name', 'gift_coupen_code', 'user_id', 'issue_date', 'expiry_date', 'validity', 'total_available', 'partner_id', 'order_ids', 'active', 'amount', 'description','used','coupon_count', 'coupon_apply_times','expiry_date','partner_true','partner_id'],
        domain: null,
        loaded: function(self, pos_gift_coupon) {
            self.pos_gift_coupon = pos_gift_coupon;
        },
    });

    models.load_models({
        model: 'pos.order',
        fields: ['coupon_id'],
        domain: function(self){ return [['session_id', '=', self.pos_session.name],['state', 'not in', ['draft', 'cancel']]]; },
        loaded: function(self, pos_order) {
            self.pos_order = pos_order;
        },
    });

    models.load_models({
        model: 'pos.coupons.setting',
        fields: ['name', 'product_id', 'min_coupan_value', 'max_coupan_value', 'max_exp_date', 'one_time_use', 'partially_use', 'default_name', 'default_validity', 'default_value', 'default_availability', 'active'],
        domain: null,
        loaded: function(self, pos_coupons_setting) {
            self.pos_coupons_setting = pos_coupons_setting;
        },
    });

    // Popup start

    var SelectExistingPopupWidget = popups.extend({
        template: 'SelectExistingPopupWidget',
        init: function(parent, args) {
            this._super(parent, args);
            this.options = {};
        },
        //
        show: function(options) {
            var self = this;
            this._super(options);

        },
        //
        renderElement: function() {
            var self = this;
            this._super();
            var order = this.pos.get_order();
            var selectedOrder = self.pos.get('selectedOrder');
            
            /*
            function formatDate(date) {
				var d = new Date(date),
					month = '' + (d.getMonth() + 1),
					day = '' + d.getDate(),
					year = d.getFullYear();

				if (month.length < 2) month = '0' + month;
				if (day.length < 2) day = '0' + day;

				return [year, month, day].join('-');
			}
			*/
						
            
            this.$('#apply_coupon_code').click(function() {
                var entered_code = $("#existing_coupon_code").val();
                var used = false;
                var partner_id = false;
                var coupon_applied = true;
                var gift_partner_id = self.pos.pos_gift_coupon[0].partner_id;
                var partner_true = self.pos.pos_gift_coupon[0].partner_true;
                if (order.get_client() != null)
                    partner_id = order.get_client();
                (new Model('pos.gift.coupon')).call('existing_coupon', [partner_id ? partner_id.id : 0, entered_code]).fail(function(unused, event) {
                }).done(function(output) {
                    var orderlines = order.orderlines;
                    if (!partner_id) {
                        self.gui.show_popup('error', {
                            'title': _t('Unknown customer'),
                            'body': _t('You cannot use Coupons/Gift Voucher. Select customer first.'),
                        });
                        return;
                    }
                    
                    /*if (partner_true == true) {
                    	console.log('Trrrrruuuuuuuuuuuuueeeeeeeeeeeeeeeeeeeeeeeeeeeee', partner_true);
                    	if(partner_id != gift_partner_id){
                    	console.log('ggift CCCCCCCCCCCCCCCCCCCCCCCCCCCCCC', gift_partner_id)
                        self.gui.show_popup('error', {
                            'title': _t('Invalid Customer '),
                            'body': _t('This Gift Coupon is not applicable for this Customer '),
                        });
                        return;
                       }
                    }*/

                    if (orderlines.length === 0) {
                        self.gui.show_popup('error', {
                            'title': _t('Empty Order'),
                            'body': _t('There must be at least one product in your order before it can be apply for voucher code.'),
                        });
                        return;
                    }

                    if (orderlines.models.length) {
                        if (output == 'true') {
                            var selectedOrder = self.pos.get('selectedOrder');
                            selectedOrder.coupon_id = entered_code;
                            var total_amount = selectedOrder.get_total_without_tax();
                            new Model('pos.gift.coupon').call('search_coupon', [partner_id ? partner_id.id : 0, entered_code]).fail(function(unused, event) {
                            }).done(function(output) {
                                order.coupon_id = output[0];
                                var amount = output[1];
                                used = output[2];
                                var coupon_count = output[3];
                                var coupon_times = output[4];
                                var expiry = output[5]; 
                                
                                var current_date = new Date().toUTCString();
                                //var n = date.datetime_to_str(new Date())
                                var d = new Date();
                                //var month = d.getMonth();
                                var month = '' + (d.getMonth() + 1);
                                var day = '' + d.getDate();
								var year = d.getFullYear();
								var date_format = [year, month, day].join('-');
								var hours = d.getHours();
								var minutes = d.getMinutes();
                                var seconds = d.getSeconds();
                                var time_format = [hours, minutes, seconds].join(':');
                                var date_time = [date_format, time_format].join(' ');
                                var partner_true = output[6];
                                var gift_partner_id = output[7];
                                var product_id = self.pos.pos_coupons_setting[0].product_id[0];
                                
                                for (var i = 0; i < orderlines.models.length; i++) {
                                    if (orderlines.models[i].product.id == product_id){
                                        coupon_applied = false;
                                        }
						        }   
						        
						        if (coupon_applied == false) {
						            self.gui.show_popup('error', {
						                'title': _t('Coupon Already Applied'),
						                'body': _t("The Coupon You are trying to apply is already applied in the OrderLines"),
						            });
						        }
                                
                                
                                /*if (date_time > expiry){ // expired
						        	self.gui.show_popup('error', {
						                'title': _t('Expired'),
						                'body': _t("The Coupon You are trying to apply is Expired"),
						            });
						        }*/
						        
						        else if (coupon_count > coupon_times){ // maximum limit
						        	self.gui.show_popup('error', {
						                'title': _t('Maximum Limit Exceeded !!!'),
						                'body': _t("You already exceed the maximum number of limit for this Coupon code"),
						            });
						        }
						        
						        else if (partner_true == true && gift_partner_id != partner_id.id){
								    	self.gui.show_popup('error', {
								            'title': _t('Invalid Customer !!!'),
								            'body': _t("This Gift Coupon is not applicable for this Customer"),
								        });
						        }
						       
                                else { // if coupon is not used
                                
		                            var total_val = total_amount - amount;
		                            var product_id = self.pos.pos_coupons_setting[0].product_id[0];
		                            var product = self.pos.db.get_product_by_id(product_id);
		                            var selectedOrder = self.pos.get('selectedOrder');
		                            selectedOrder.add_product(product, {
		                                price: -amount
		                            });
		                       }

                            });
                            self.gui.show_screen('products');
                        } else { //Invalid Coupon Code
                            self.gui.show_popup('error', {
                                'title': _t('Invalid Code !!!'),
                                'body': _t("Voucher Code Entered by you is Invalid. Enter Valid Code..."),
                            });
                        }
                        

                    } else { // Popup Shows, you can't use more than one Voucher Code in single order.
                        self.gui.show_popup('error', {
                            'title': _t('Already Used !!!'),
                            'body': _t("You have already use this Coupon code, at a time you can use one coupon in a Single Order"),
                        });
                    }

                });
            });
        },

    });
    gui.define_popup({
        name: 'select_existing_popup_widget',
        widget: SelectExistingPopupWidget
    });

    // End Popup start

    var GiftButtonWidget = screens.ActionButtonWidget.extend({
        template: 'GiftButtonWidget',
        button_click: function() {
            var order = this.pos.get_order();
            var self = this;
            this.gui.show_popup('select_existing_popup_widget', {});
        },
    });

    screens.define_action_button({
        'name': 'POS Coupens Gift Voucher',
        'widget': GiftButtonWidget,
        'condition': function() {
            return true;
        },
    });

});
