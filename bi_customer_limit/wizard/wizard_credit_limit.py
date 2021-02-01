# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID
from odoo import models,fields,api

class wizard_credit_limit(models.TransientModel):
    _name = "wizard_custom_credit"
    _inherit = "sale.order"
    _inherit = "mail.compose.message"
    
    @api.multi
    @api.depends('total_receivable')
    def _bi_compute_exceeded_amount(self):
        self.sale_name = self.env.context.get('sale_order_name')
        self.customer_name = self.env.context.get('default_partner_id_name')
        self.current_quotation = self.env.context.get('amount_total')
        self.customer_credit_limit = self.env.context.get('credit_limit_id')
        self.total_receivable = self.env.context.get('total_recievable')
        self.base_url = self.env.context.get('base_url')
        self.due_before = self.total_receivable + self.current_quotation
        
    @api.multi
    @api.depends('total_receivable', 'customer_credit_limit')
    def _compute_exceeded_amount(self):
        self.exceeded_amount = self.total_receivable - self.customer_credit_limit + self.current_quotation 
        
    
    customer_name = fields.Char(compute='_bi_compute_exceeded_amount', string="Name :")
    sale_name = fields.Char(string="Current Order :", readonly=True)
    customer_credit_limit = fields.Float(string="Credit Limit", readonly=True)
    credit_on_hold = fields.Boolean(string="Put on Hold", readonly=True)
    total_receivable = fields.Float(string="Total Receivable", readonly=True)
    current_quotation = fields.Float(string="Current Quotation", readonly=True)
    due_before = fields.Float(string="Due after this Quotation", readonly=True)
    exceeded_amount = fields.Float(string="Exceeded Amount", compute="_compute_exceeded_amount")
    
    
    @api.multi    
    def confirm_sale(self):        
        su_id =self.env['res.partner'].browse(SUPERUSER_ID)
        partner_id = self.env['res.partner'].search([('name','=',self.customer_name)])
        partner_id.write({'credit_limit' : self.customer_credit_limit})
        context = self._context
        active_ids = context.get('active_ids')
        for partner in partner_id:        
                if partner:
                    template_id = self.env['ir.model.data'].get_object_reference(
                                                        'bi_customer_limit',
                                                        'email_template_edi_credit_limit')[1]
                    email_template_obj = self.env['mail.template'].browse(template_id)
                    if template_id:
                        values = email_template_obj.generate_email(active_ids[0], fields=None)
                        values['email_to']=su_id.email
                        values['email_from']=partner.email
                        values['res_id']=False
                        mail_mail_obj = self.env['mail.mail']
                        msg_id = mail_mail_obj.create(values)
                        if msg_id:
                            mail_mail_obj.send([msg_id])
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

    
     