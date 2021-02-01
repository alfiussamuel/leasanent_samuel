# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import werkzeug.urls

class res_pertner(models.Model):
    _inherit = "res.partner"
    
    credit_limit = fields.Integer(string="Credit Limit")
    credit_on_hold = fields.Boolean(string="Put on Hold")

    
class sale_order(models.Model):
    _inherit = "sale.order"
    
    credit_limit_id = fields.Integer(string="Credit Limit")
    total_receivable = fields.Float(string="Total Receivable", compute="_compute_total_receivable")
    exceeded_amount = fields.Float(string="Exceeded Amount")
    sale_url = fields.Char(string="url")
    
     
    @api.multi
    def _compute_total_receivable(self):
        for rec in self:
            if rec.partner_id.credit:
                rec.update({'total_receivable' : rec.partner_id.credit})
            if not rec.partner_id.credit:
                rec.update({'total_receivable' : rec.partner_id.parent_id.credit})
            
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            static_url = "/web"
            view_id = "#id=%d" %rec.id
            view_type = "&view_type=form&model=sale.order"
            sale_url_id = str(base_url)+static_url+view_id+view_type
            rec.sale_url = unicode(sale_url_id)

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        print(self.partner_id,"PArtner iddddd")
        if not self.partner_id:
            self.update({
                'partner_invoice_id' : False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return
        if not self.partner_id.credit:
            self.partner_id.credit = self.partner_id.parent_id.credit
            
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        vals = {
            'pricelist_id' : self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id' : self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'note': self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note,
            'credit_limit_id': self.partner_id.credit_limit,
            'total_receivable': self.partner_id.credit,
            }
        if self.partner_id.user_id:
            values['user_id'] = self.partner_id.user_id.id
        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(vals)

    @api.multi
    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        partner = self.partner_id
        
        account_move_line = self.env['account.move.line']
        if partner.is_company:
            account_move_line = account_move_line.\
                search([('partner_id', '=', partner.id),
                        ('account_id.user_type_id.name', 'in',
                         ['Receivable', 'Payable'])
                        ])
        if not partner.is_company:
            account_move_line = account_move_line.\
                search([('partner_id', '=', partner.parent_id.id),
                        ('account_id.user_type_id.name', 'in',
                         ['Receivable', 'Payable'])
                        ])
            self.partner_id.credit_on_hold = self.partner_id.parent_id.credit_on_hold
            
        credit = 0.0
        debit = 0.0
        
        for line in account_move_line:
            credit += line.credit
            debit += line. debit
        
        total = debit - credit + self.amount_total
        self.exceeded_amount = self.total_receivable - self.credit_limit_id + self.amount_total 
        self.sale_url = self.sale_url
        for order in self:
            order.write({'exceeded_amount' : self.exceeded_amount,
                         'credit_limit_id' : self.credit_limit_id,
                         })
            if self.partner_id.credit_on_hold is False:
                if (total) > partner.credit_limit:
                    wizard_credit_limit_obj = self.env.ref('bi_customer_limit.view_wizard_credit_limit_form')
                    res = {}
                    if wizard_credit_limit_obj:
                        res={
                            'name' : _('Credit Limit'),
                            'type' : 'ir.actions.act_window',
                            'view_type' : 'form',
                            'view_mode' : 'form',
                            'res_model' : 'wizard_custom_credit',
                            'view_id' : wizard_credit_limit_obj.id,
                            'target' : 'new',
                            'context' : {'default_sale_id' : self.id,
                                         'sale_order_name' : self.name,
                                         'amount_total' : self.amount_total,
                                         'credit_limit_id' : self.credit_limit_id,
                                         'default_partner_id_credit' : self.partner_id.credit,
                                         'default_partner_id_name' : self.partner_id.name,
                                         'total_recievable' : self.total_receivable,
                                         },
                        }
                        return res
                
                else:
                    order.write({'credit_limit_id':partner.credit_limit})
                return True
                    
            else:
                raise UserError(_('You have been put on hold due to exceeding your credit limit. Please contact administration for further guidance. \n Thank You'))
                return False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: