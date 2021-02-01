odoo.define('pos_coupon.pos_coupon', function(require) {
    "use strict";
    var Model = require('web.DataModel');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var utils = require('web.utils');
    var round_di = utils.round_decimals;
    var gui = require('point_of_sale.gui');
    var round_pr = utils.round_precision;
    var QWeb = core.qweb;
    var ActionManager1 = require('web.ActionManager');
    var PopupWidget = require("point_of_sale.popups");
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var SuperPosModel = models.PosModel.prototype;
    var _t = core._t;
    models.load_fields('res.users', 'allow_coupon_create');
    models.load_models([{
        model: 'voucher.config',
        fields: [],
        domain: function(self) {
            return [
                ['active', '=', true]
            ];
        },
        loaded: function(self, wk_coupon_config) {
            self.set({
                'wk_coupon_config': wk_coupon_config
            });
        },
    }, ], {
        'after': 'product.product'
    });

    var CreateConfurmPopupWidget = PopupWidget.extend({
        template: 'CreateConfurmPopupWidget',

        show: function(wk_obj) {
            this._super();
            var self = this;
            var currentOrder = self.pos.get('selectedOrder');
            this.$('#print-coupons').off('click').click(function() {
                if (self.pos.config.iface_print_via_proxy) {
                    (new Model('voucher.voucher')).call('get_coupon_data', [
                            wk_obj.wk_id
                        ])
                        .then(function(result) {
                            var receipt = currentOrder.export_for_printing();
                            receipt['coupon'] = result;
                            var t = QWeb.render('CouponXmlReceipt', {
                                receipt: receipt,
                                widget: self,
                            });
                            var res = self.pos.proxy.print_receipt(t);
                            self.gui.show_screen('products');
                            console.log('---------------hjsdfdasf');
                        });
                } else {
                    (new Model('voucher.voucher')).call('wk_print_report')
                        .then(function(result) {
                            this.action_manager = new ActionManager1(this);
                            this.action_manager.do_action(result, {
                                additional_context: {
                                    active_id: wk_obj.wk_id,
                                    active_ids: [wk_obj.wk_id],
                                    active_model: 'pos.coupons'
                                }
                            })
                            self.gui.show_screen('products');
                        })
                        .fail(function(error, event) {
                            event.preventDefault();
                            self.gui.show_popup('error', {
                                'title': _t('Error: Could not Save Changes'),
                                'body': _t('Your Internet connection is probably down.'),
                            });
                        });
                }
            });
        },
    });
    gui.define_popup({
        name: 'create-confurm-screen',
        widget: CreateConfurmPopupWidget
    });

    var CreateCouponPopupWidget = PopupWidget.extend({
        template: 'CreateCouponPopupWidget',

        saveBackend: function(name, validity, availability, coupon_value, note, customer_type, partner_id, voucher_usage, amount_type, max_expiry_date, redeemption_limit, partial_redeem) {
            self = this;
            (new Model('voucher.voucher')).call('create_coupons', [{
                    'name': name,
                    'validity': validity,
                    'total_available': availability,
                    'coupon_value': coupon_value,
                    'note': note,
                    'customer_type': customer_type,
                    'partner_id': partner_id,
                    'voucher_usage': voucher_usage,
                    'amount_type': amount_type,
                    'max_expiry_date': max_expiry_date,
                    'redeemption_limit': redeemption_limit,
                    'partial_redeem': partial_redeem
                }])
                .fail(function(unused, event) {
                    self.gui.show_popup('error', {
                        'title': _t('Error !!!'),
                        'body': _t("Error in creating voucher !!!!"),
                    });
                })
                .done(function(result) {
                    self.gui.show_popup('create-confurm-screen', {
                        'wk_id': result,
                    });
                });
        },

        renderElement: function() {
            var self = this;
            this._super();
            var wk_config = self.pos.get('wk_coupon_config');
            if (wk_config != false) {
                $("input[name=wk_coupon_name]").val(wk_config[0].default_name || '');
                $("input[name=wk_coupon_validity]").val(wk_config[0].default_validity);
                $("input[name=wk_coupon_availability]").val(wk_config[0].default_availability);
                $("input[name=wk_coupon_value]").val(wk_config[0].default_value);
                $("select[name=wk_customer_type]").val(wk_config[0].customer_type);
                $("input[name=wk_redeemption_limit]").val(wk_config[0].partial_limit);
                $("#wk_partial_redeemed").attr('checked', wk_config[0].partially_use);
            }
            $("select[name=wk_customer_type]").change(function() {
                if ($(this).val() == 'special_customer') {
                    $("input[name=wk_coupon_availability]").parent().hide();
                    $("#wk_partial_redeemed").parent().parent().parent().show();
                } else {
                    $("input[name=wk_coupon_availability]").parent().show();
                    $("#wk_partial_redeemed").parent().parent().parent().hide();
                }
            });
            this.$('.wk_create_coupon_button').click(function() {
                function isNumber(o) {
                    return !isNaN(o - 0) && o !== null && o !== "" && o !== false;
                }
                var wk_config = self.pos.get('wk_coupon_config');
                var order = self.pos.get('selectedOrder');
                if (wk_config == false) {
                    self.gui.show_popup('error', {
                        'title': _t('Error !!!'),
                        'body': _t("Coupon Configuration is Required"),
                    });
                } else {
                    $("input[name=wk_coupon_name]").removeClass("wk_text_error");
                    $("input[name=wk_coupon_validity]").removeClass("wk_text_error");
                    $("input[name=wk_coupon_availability]").removeClass("wk_text_error");
                    $("input[name=wk_coupon_value]").removeClass("wk_text_error");
                    $("input[name=wk_coupon_value]").removeClass("wk_text_error");
                    $("select[name=wk_customer_type]").removeClass("wk_text_error");
                    $("select[name=wk_coupon_usage]").removeClass("wk_text_error");
                    $("input[name=wk_redeemption_limit]").removeClass("wk_text_error");
                    $("select[name=wk_partner_id]").removeClass("wk_text_error");
                    $("select[name=wk_amount_type]").removeClass("wk_text_error");
                    $('.wk_valid_error').html("");
                    var name = $("input[name=wk_coupon_name]").val();
                    var validity = $("input[name=wk_coupon_validity]").val();
                    var availability = $("input[name=wk_coupon_availability]").val();
                    var coupon_value = $("input[name=wk_coupon_value]").val();
                    var note = $("textarea[name=note]").val();
                    var customer_type = $("select[name=wk_customer_type]").val();
                    var voucher_usage = $("select[name=wk_coupon_usage]").val();
                    var redeemption_limit = $("input[name=wk_redeemption_limit]").val();
                    var partial_redeem = $("#wk_partial_redeemed").is(":checked");
                    var amount_type = $("select[name=wk_amount_type]").val();
                    var max_expiry_date = wk_config[0].max_expiry_date;
                    if (name != '') {
                        if (isNumber(validity)) {
                            if (isNumber(availability) && availability != 0) {
                                if (isNumber(coupon_value) && coupon_value != 0) {
                                    if (!(amount_type == 'percent' && (coupon_value < 0 || coupon_value > 100))) {
                                        if (parseInt(coupon_value) >= wk_config[0].min_amount && parseInt(coupon_value) <= wk_config[0].max_amount) {
                                            if (customer_type == 'special_customer') {
                                                if (order.get_client() == null) {
                                                    self.gui.show_popup('error', {
                                                        'title': _t('Error !!!'),
                                                        'body': _t("Please Select Customer!!!!"),
                                                    });
                                                } else {
                                                    if (partial_redeem == true) {
                                                        if (redeemption_limit == 0)
                                                            $('.valid_error_redeeemption').html("This field is required & should not be 0");
                                                        else {
                                                            self.saveBackend(name, validity, availability, coupon_value, note, customer_type, order.get_client().id, voucher_usage, amount_type, max_expiry_date, redeemption_limit, partial_redeem);
                                                        }

                                                    } else
                                                        self.saveBackend(name, validity, availability, coupon_value, note, customer_type, order.get_client().id, voucher_usage, amount_type, max_expiry_date, -1, false);
                                                }
                                            } else
                                                self.saveBackend(name, validity, availability, coupon_value, note, customer_type, false, voucher_usage, amount_type, max_expiry_date, -1, false);
                                        } else {
                                            if (parseInt(coupon_value) < wk_config[0].min_amount)
                                                $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("(Min. allowed value is " + wk_config[0].min_amount + ")");
                                            else
                                                $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("(Max. allowed value is " + wk_config[0].max_amount + ")");
                                        }
                                    } else {
                                        $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("Must be > 0 & <=100");
                                    }
                                } else {
                                    $("input[name=wk_coupon_value]").addClass("wk_text_error");
                                    /*$('.wk_valid_error').html("Value should be >=0");*/
                                    $("input[name=wk_coupon_value]").parent().find('.wk_valid_error').html("Value should be >=0");
                                }
                            } else {
                                $("input[name=wk_coupon_availability]").addClass("wk_text_error");
                                $("input[name=wk_coupon_availability]").parent().find('.wk_valid_error').html("Validity can't be 0");
                            }
                        } else
                            $("input[name=wk_coupon_validity]").addClass("wk_text_error");
                    } else
                        $("input[name=wk_coupon_name]").addClass("wk_text_error");
                }
            });
        },
    });
    gui.define_popup({
        name: 'create_coupon_popup_widget',
        widget: CreateCouponPopupWidget
    });

    var RedeemPopupRetryWidget = PopupWidget.extend({
        template: 'RedeemPopupRetryWidget',
        show: function(options) {
            this._super(options);
            this.gui.play_sound('error');
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('#wk-retry-coupons').click(function() {
                self.gui.show_popup('redeem_coupon_popup_widget', {});
            });
        },
    });
    gui.define_popup({
        name: 'redeem_coupon_retry_popup_widget',
        widget: RedeemPopupRetryWidget
    });

    var RedeemPopupValidateWidget = PopupWidget.extend({
        template: 'RedeemPopupValidateWidget',

        show: function(options) {
            var self = this;
            this._super(options);
            self.wk_product_id = options.wk_product_id;
            self.secret_code = options.secret_code;
            self.total_val = options.total_val;
            self.coupon_name = options.coupon_name;
        },
        renderElement: function() {
            var self = this;
            this._super();
            var selectedOrder = self.pos.get('selectedOrder');

            this.$('#wk-retry-coupons').click(function() {
                (new Model('voucher.voucher')).call('redeem_voucher_create_histoy', [self.coupon_name, self.secret_code, self.total_val, false, false, 'pos'])
                    .fail(function(unused, event) {
                        self.gui.show_popup('error', {
                            'title': _t('Error !!!'),
                            'body': _t("Connection Error. Try again later !!!!"),
                        });
                    })
                    .done(function(result) {
                        if (result['status']) {

                            selectedOrder.coupon_id = self.secret_code;
                            selectedOrder.wk_product_id = self.wk_product_id;
                            selectedOrder.wk_voucher_value = self.total_val;
                            selectedOrder.history_id = result['history_id'];
                            var product = self.pos.db.get_product_by_id(self.wk_product_id);
                            var last_orderline = selectedOrder.get_last_orderline();
                            last_orderline.coupon_name = self.coupon_name;
                            if (product != undefined) {
                                selectedOrder.add_product(product, {
                                    price: -(self.total_val)
                                });
                                self.gui.show_screen('products');
                            } else {
                                self.gui.show_popup('error', {
                                    'title': _t('Error !!!'),
                                    'body': _t("Voucher product not available in POS. Please make the voucher product available in POS"),
                                });
                            }
                        }
                    });
            });
        },
    });
    gui.define_popup({
        name: 'redeem_coupon_validate_popup_widget',
        widget: RedeemPopupValidateWidget
    });

    var RedeemPopupWidget = PopupWidget.extend({
        template: 'RedeemPopupWidget',

        renderElement: function() {
            var self = this;
            this._super();
            var order = self.pos.get('selectedOrder');
            if (order == null) {
                return false;
            }
            var orderlines = order.orderlines;
            var coupon_product = true;
            var prod_list = []
            var selected_prod_percent_price = 0
            for (var i = 0; i < orderlines.models.length; i++) {
                prod_list.push(orderlines.models[i].product.id);
            }
            this.$('#wk-redeem-coupons').click(function() {
                var secret_code = $("#coupon_8d_code").val();
                (new Model('voucher.voucher')).call('validate_voucher', [secret_code, order.get_total_without_tax(), prod_list, 'pos', order.get_client() ? order.get_client().id : 0])
                    .fail(function(unused, event) {
                        self.gui.show_popup('error', {
                            'title': _t('Error !!!'),
                            'body': _t('Connection Error. Try again later !!!!'),
                        });
                    })
                    .done(function(result) {
                        if (orderlines.models.length) {
                            for (var i = 0; i < orderlines.models.length; i++) {
                                if (orderlines.models[i].product.id == result.product_id)
                                    coupon_product = false;
                                if (result.product_ids !== undefined)
                                    if ($.inArray(orderlines.models[i].product.product_tmpl_id, result.product_ids) !== -1)
                                        selected_prod_percent_price += orderlines.models[i].price * orderlines.models[i].quantity;
                            }
                            if (coupon_product) {
                                if (result.status) {
                                    var total_amount = order.get_total_with_tax();
                                    var msg;
                                    var total_val;
                                    var res_value = result.value;
                                    if (result.customer_type == 'general') {
                                        if (result.voucher_val_type == 'percent') {
                                            res_value = (total_amount * result.value) / 100;
                                            if (result.applied_on == 'specific')
                                                res_value = (selected_prod_percent_price * result.value) / 100;
                                            else
                                                total_amount = res_value;
                                        } else {
                                            if (result.applied_on == 'specific')
                                                total_amount = selected_prod_percent_price
                                        }
                                    }
                                    if (total_amount < res_value) {
                                        msg = total_amount;
                                        total_val = total_amount;
                                    } else {
                                        msg = res_value;
                                        total_val = res_value;
                                    }
                                    msg = parseFloat(round_di(msg, 2).toFixed(2));
                                    self.gui.show_popup('redeem_coupon_validate_popup_widget', {
                                        'title': _t(result.message),
                                        'msg': _t(msg),
                                        'wk_product_id': result.product_id,
                                        'secret_code': result.coupon_id,
                                        'total_val': total_val,
                                        'coupon_name': result.coupon_name,
                                        'coupon_code': result.voucher_code,

                                    });
                                } else {
                                    self.gui.show_popup('redeem_coupon_retry_popup_widget', {
                                        'title': _t("Error: " + result.message),
                                    });
                                }
                            } else {
                                self.gui.show_popup('error', {
                                    'title': _t('Error !!!'),
                                    'body': _t("Sorry, you can't use more than one coupon in single order."),
                                });
                            }
                        } else {
                            self.gui.show_popup('error', {
                                'title': _t('Error !!!'),
                                'body': _t("Sorry, there is no product in order line."),
                            });
                        }
                    });
            });
        },
    });
    gui.define_popup({
        name: 'redeem_coupon_popup_widget',
        widget: RedeemPopupWidget
    });

    var CouponPopupWidget = PopupWidget.extend({
        template: 'CouponPopupWidget',

        renderElement: function() {
            var self = this;
            this._super();
            this.$('#gift-coupons-create').click(function() {
                if (self.pos.user.allow_coupon_create)
                    self.gui.show_popup('create_coupon_popup_widget', {});
                else {
                    self.gui.show_popup('error', {
                        'title': _t('Error !!!'),
                        'body': _t("Access denied please contact your Administrator"),
                    });
                }
            });
            this.$('#gift-coupons-redeem').click(function() {
                self.gui.show_popup('redeem_coupon_popup_widget', {});
                $('#coupon_8d_code').focus();
            });
        },
    });
    gui.define_popup({
        name: 'coupon_popup_widget',
        widget: CouponPopupWidget
    });

    var CouponButtonWidget = screens.ActionButtonWidget.extend({
        template: 'CouponButtonWidget',
        button_click: function() {
            self = this;
            self.gui.show_popup('coupon_popup_widget', {});
        },
    });
    screens.define_action_button({
        'name': 'Coupon',
        'widget': CouponButtonWidget,
        'condition': function() {
            return true;
        },
    });

    var _super = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes) {
            this.coupon_id = 0;
            this.wk_product_id = 0;
            this.history_id = 0;
            _super.prototype.initialize.apply(this, arguments);
        },
        export_as_JSON: function() {
            var json = _super.prototype.export_as_JSON.apply(this, arguments);
            var order = this.pos.get('selectedOrder');
            if (order != null) {
                var orderlines = order.orderlines;
                var coupon_state = true;
                for (var i = 0; i < orderlines.models.length; i++)
                    if (orderlines.models[i].product.id == order.wk_product_id)
                        coupon_state = false;
                if (coupon_state)
                    json.coupon_id = 0;
                else
                    json.coupon_id = order.coupon_id || 0;
            }
            return json;
        },
    });

    models.PosModel = models.PosModel.extend({
        _save_to_server: function(orders, options) {
            var self = this;
            return SuperPosModel._save_to_server.call(this, orders, options).then(function(server_ids) {
                /*-------------CODE FOR POS VOUCHERS START------*/
                if (server_ids) {
                    var wk_order = self.get_order();
                    if (wk_order != null) {
                        var coupon_id = wk_order.coupon_id;
                        var wk_product_id = wk_order.wk_product_id;
                        var wk_voucher_value = wk_order.wk_voucher_value;
                        for (var i = 0; i < wk_order.orderlines.models.length; i++) {
                            $('.receipt-screen.screen span.button.next').show();
                            if (wk_order.orderlines.models[i].product.id == wk_product_id) {
                                var client_id = false;
                                if (self.get_client()) {
                                    client_id = self.get_client().id;
                                }
                                console.log('wk_orderlines', wk_order.orderlines.models[i].id);

                                (new Model('voucher.voucher')).call('pos_create_histoy', [coupon_id, wk_voucher_value, server_ids[0], wk_order.orderlines.models[i].id, client_id])
                                    .fail(function(unused, event) {
                                        self.gui.show_popup('error', {
                                            'title': _t('Error !!!'),
                                            'body': _t("Connection Error. Try again later !!!"),
                                        });
                                    })
                                    .done(function(result) {});
                            }
                        }
                    }
                }
                /*-------------CODE FOR POS VOUCHERS END------*/
                return server_ids;
            });
        },
    });


    screens.NumpadWidget.include({
        clickAppendNewChar: function(event) {
            var order = this.pos.get_order();
            var p_id = order.get_selected_orderline();
            if (order.get_selected_orderline() && (order.wk_product_id === order.get_selected_orderline().product.id)) {
                self.gui.show_popup('error', {
                    'title': _t('Error !!!'),
                    'body': _t("You can not change the quantity, discount or price of the applied voucher"),
                });
            } else {
                this._super(event);
            }
        },
    });

     screens.ReceiptScreenWidget.include({
        click_next: function() {
        $('.receipt-screen.screen span.button.next').hide();
        this.pos.get_order().finalize();
    },
    });

});