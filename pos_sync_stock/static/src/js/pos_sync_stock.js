odoo.define('pos_sync_stock', function (require) {

    var core = require('web.core');
    var _t = core._t;
    var models = require('point_of_sale.models');
    var session = require('web.session');
    var Backbone = window.Backbone;
    var bus = require('bus.bus');
    var exports = {}

    exports.pos_stock_syncing = Backbone.Model.extend({
        initialize: function (pos) {
            this.pos = pos;
        },
        start: function () {
            this.bus = bus.bus;
            this.bus.last = this.pos.db.load('bus_last', 0);
            this.bus.on("notification", this, this.on_notification);
            this.bus.start_polling();
        },
        on_notification: function (notification) {
            if (notification && notification[0] && notification[0][0] && typeof notification[0][0] === 'string') {
                notification = [notification]
            }
            if (notification.length) {
                for (var i = 0; i < notification.length; i++) {
                    var channel = notification[i][0];
                    var message = notification[i][1];
                    this.on_notification_do(channel, message);
                }
            }
        },
        on_notification_do: function (channel, message) {
            if (Array.isArray(channel) && channel[1] === 'pos.stock.update' && this.pos.config.allow_syncing_stock == true) {
                this.pos.update_stock(message)
            }
            this.pos.db.save('bus_last', this.bus.last)
        }
    });

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({

        load_orders: function () {
            this.the_first_load = true;
            _super_posmodel.load_orders.call(this);
            this.the_first_load = false;
        },

        load_server_data: function () {
            var self = this;
            return _super_posmodel.load_server_data.apply(this, arguments).then(function () {
                if (self.config.allow_syncing_stock) {
                    self.pos_stock_syncing = new exports.pos_stock_syncing(self);
                    self.pos_stock_syncing.start();
                }
                if (self.config.stock_location_id) {
                    self.chrome.loading_message(_t('Waiting syncing your stock locations'), 1);
                    var product_ids = [];
                    for (var i in self.db.product_by_id) {
                        product_ids.push(self.db.product_by_id[i].id)
                    }
                    return session.rpc("/pos/get/stock", {
                        values: {
                            product_ids: product_ids,
                            location_id: self.config.stock_location_id[0]
                        }
                    }).then(function (datas) {
                        var product_datas = JSON.parse(datas);
                        for (var j = 0; j < product_datas.length; j++) {
                            var product = self.db.product_by_id[product_datas[j].product_id];
                            if (product) {
                                product['qty_available'] = product_datas[j]['qty_available'];
                            }
                            ;
                        }
                        ;
                    });
                }
            })
        },

        update_stock: function (stock_quants) {
            if (stock_quants['stock_location_id'] == this.config.stock_location_id[0]) {
                var product = this.db.get_product_by_id(stock_quants['product_id']);
                if (product) {
                    product['qty_available'] = stock_quants['qty_available'];
                    this.update_pos_screen(product)
                }
            }


        },

        update_pos_screen: function (product) {
            var $elem_qty_available = $("[data-product-id='" + product.id + "'] .qty_available");
            if (product.qty_available <= 0) {
                $elem_qty_available.html('<i class="fa fa-expeditedssl"/>' + product.qty_available);
            } else {
                $elem_qty_available.html('<i class="fa fa-unlock"/>' + product.qty_available);
            }
        },

        push_order: function (order, opts) {
            var parent_transaction = _super_posmodel.push_order.call(this, order, opts);
            if (order) {
                for (var i = 0; i < order.orderlines.models.length; i++) {
                    var product = order.orderlines.models[i].get_product();
                    product['qty_available'] -= order.orderlines.models[i].get_quantity();
                    this.update_pos_screen(order.orderlines.models[i].get_product());
                }
            }
            return parent_transaction;
        },

        push_and_invoice_order: function (order) {
            var parent_transaction = _super_posmodel.push_and_invoice_order.call(this, order);
            if (order && order.get_client()) {
                for (var i = 0; i < order.orderlines.models.length; i++) {
                    var product = order.orderlines.models[i].get_product();
                    product['qty_available'] -= order.orderlines.models[i].get_quantity();
                    this.update_pos_screen(order.orderlines.models[i].get_product());
                }
            }
            return parent_transaction;
        },
    });
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        add_product: function (product, options) {
            if (product['qty_available'] <= 0 && this.pos.config['allow_order_out_of_stock'] == false) {
                return this.pos.gui.show_popup('error-traceback', {
                    'title': 'Error',
                    'body': 'You can not add product have out of stock',
                });
            }
            return _super_order.add_product.call(this, product, options);
        }
    });

    var _super_order_line = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        set_quantity: function (quantity) {
            if (this.pos.the_first_load == false && quantity != 'remove' && this.product['qty_available'] < quantity && this.pos.config['allow_order_out_of_stock'] == false) {
                return this.pos.gui.show_popup('error-traceback', {
                    'title': 'Error',
                    'body': 'Your stock location only have ' + this.product['qty_available'] + ' unit',
                });
            }
            return _super_order_line.set_quantity.call(this, quantity);
        }
    });

    return exports;
});
