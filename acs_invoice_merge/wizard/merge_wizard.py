# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MergeWizard(models.TransientModel):
    _name = 'merge.wizard'
    _description = 'Merge Record'

    partner_id = fields.Many2one('res.partner', 'Customer/Supplier', required=True)
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    create_new_record = fields.Boolean('Create New Record', default=True)
    merge_in_record = fields.Boolean('Merge in Existing Record')
    order_todo =  fields.Selection([
            ('cancel','Cancel Orders'),
            ('delete','Delete Orders'),
        ], 'Cancel/Delete Other Orders', default='cancel' ,required=True)

    @api.model
    def default_get(self, fields):
        active_model = self._context.get('active_model')
        res = super(MergeWizard, self).default_get(fields)

        if len(self._context.get('active_ids'))<=1:
            raise UserError(_('Select two or more than two records.'))

        partner_group = self.env[active_model].read_group([('id', 'in', self._context.get('active_ids', []))] , fields=['partner_id'], groupby=['partner_id'])
        if len(partner_group) > 1:
            raise UserError(_('Select records for same Customer/Supplier.'))

        non_draft_orders = self.env[active_model].browse(self._context.get('active_ids')).filtered(lambda s: s.state!='draft')
        if len(non_draft_orders) >= 1:
            raise UserError(_('Select records which are in draft state.'))

        active_record = self.env[active_model].browse(self._context.get('active_ids')[0])
        res.update({'partner_id': active_record.partner_id.id})

        return res

    @api.onchange('create_new_record')
    def onchange_create_new_record(self):
        if self.create_new_record:
            self.merge_in_record = False
        else:
            self.merge_in_record = True

    @api.onchange('merge_in_record')
    def onchange_merge_in_record(self):
        if self.merge_in_record:
            self.create_new_record = False
        else:
            self.create_new_record = True

    @api.multi
    def merge_record(self):
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        if active_model == 'account.invoice':
            InvLine = self.env['account.invoice.line']

            if self.create_new_record:
                new_rec_id = active_records[0].copy()
                rec_to_exclude = active_records[0]
                if self.order_todo=='cancel':
                    rec_to_exclude.action_invoice_cancel()
                else:
                    rec_to_exclude.unlink()

            else:
                new_rec_id = self.invoice_id
                rec_to_exclude = self.invoice_id

            for rec in (active_records - rec_to_exclude):
                for line in rec.invoice_line_ids:
                    same_line = InvLine.search([
                        ('invoice_id', '=', new_rec_id.id),
                        ('product_id','=',line.product_id.id),
                        ('price_unit','=',line.price_unit),
                        ('discount','=',line.discount),
                        #('invoice_line_tax_ids','in',line.invoice_line_tax_ids.ids),
                    ], limit=1)
                    if same_line:
                        same_line.quantity += line.quantity
                    else:
                        InvLine.create({
                            'product_id': line.product_id and line.product_id.id or False,
                            'quantity' : line.quantity,
                            'uom_id' : line.uom_id.id,
                            'price_unit' : line.price_unit,
                            'invoice_id': new_rec_id.id,
                            'name': line.name,
                            'discount': line.discount,
                            'account_id': line.account_id.id,
                            'invoice_line_tax_ids': [(6,0, line.invoice_line_tax_ids.ids)]
                        })
                if self.order_todo=='cancel':
                    rec.action_invoice_cancel()
                else:
                    rec.unlink()
                new_rec_id.compute_taxes()

            action = self.env.ref('account.action_invoice_tree1').read()[0]
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = new_rec_id.id
            return action
