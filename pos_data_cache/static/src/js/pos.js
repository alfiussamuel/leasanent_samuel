odoo.define('pos_data_cache.pos_data_cache', function (require) {
    "use strict";
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var Model = require('web.DataModel');
    var _t = core._t;

    var posmodel_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        load_new_partners: function(){
            var self = this;
            var def  = new $.Deferred();
            var fields = ['name','street','city','state_id','country_id','vat','phone','zip','mobile','email','barcode','write_date','property_account_position_id'];
            new Model('res.partner')
                .query(fields)
                .filter([['customer','=',true],['write_date','>',this.db.get_partner_write_date()]])
                .all({'timeout':3000, 'shadow': true})
                .then(function(partners){
                    if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                        def.resolve();
                    } else {
                        def.reject();
                    }
                }, function(err,event){ event.preventDefault(); def.reject(); });    
            return def;
        },
        load_server_data: function () {
            var self = this;

            var partner_index = _.findIndex(this.models, function (model) {
                return model.model === "res.partner";
            });
            var partner_model = this.models[partner_index];
            var partner_fields = partner_model.fields;
            var partner_domain = partner_model.domain;
            if (partner_index !== -1) {
                this.models.splice(partner_index, 1);
            }
            return posmodel_super.load_server_data.apply(this, arguments).then(function () {
                var records = new Model('pos.config').call('get_partner_from_cache',
                                                           [self.pos_session.config_id[0], partner_fields, partner_domain]);

                self.chrome.loading_message(_t('Loading') + ' res.partner', 1);
                return records.then(function (partners) {
                        self.partners = partners;
                        self.db.add_partners(partners);
                });
            });
        },
    });
});
