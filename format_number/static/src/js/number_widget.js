/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('format_number.form_widgets', function (require) {
    "use strict";
    var core = require('web.core');

    var form_widgets = require('web.form_widgets');

    form_widgets.FieldFloat.include({
        init: function (field_manager, node) {
            this._super(field_manager, node);
            this.thousands_sep = core._t.database.parameters.thousands_sep || ',';
            this.decimal_point = core._t.database.parameters.decimal_point || '.';
            this.rep = "[^" + this.decimal_point + "-\\d]";
            this.re = new RegExp(this.rep,"g");
        },
        render_value: function () {
            this._super();
            var self = this;
            if (this.widget === "float_time"){
                return;
            }
            if (this.$input) {
                this.$input.on('keyup', function (event) {
                    // skip arrow keys
                    if (event.which >= 37 && event.which <= 40) return;
                    // format number
                    $(this).val(function (index, value) {
                        var v1 = value.replace(self.re, "").replace(/\B(?=((\d{3})+(?!\d)))/g, self.thousands_sep);
                        var v = v1.split(self.decimal_point);
                        var re = new RegExp("\\" + self.thousands_sep, "g");
                        if(v.length > 1){
                            v = v[0] + self.decimal_point + v[1].replace(re, '');
                        }

                        return v
                    });
                });
            }
        }
    });
});