from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError


class WizardCreateInvoice(models.TransientModel):
    _name = "wizard.create.invoice"
    _description = "Create Invoice"
        
    @api.multi
    def button_create_invoice(self):       
        context = dict(self._context or {}) 
        so_list = context.get('active_ids')            
        current_partner_id = False
        so_ids = self.env['sale.order'].browse(context.get('active_ids'))

        discount_list = []
        so_temp_list = []
        origin = ''

        wh_invoice_validate = False

        for so in so_ids:

            if so.warehouse_id.validate_invoice == True:
                wh_invoice_validate = True

            #partner validation, must same partner
            if not current_partner_id:
                current_partner_id = so.partner_id.id
            else:
                if so.partner_id.id != current_partner_id:
                    raise Warning('Only sale order with same customer can be created merge invoice !')

            if so.state not in ['sale','done']:
                raise Warning('Only sale order with status Confirmed or Locked !')

            if so.invoice_status not in ['to invoice','no']:
                raise Warning('There are sale order has been invoiced !')

            #search all discount
            for l in so.order_line:
                if l.discount not in discount_list:
                    discount_list.append(l.discount)

            if so.id not in so_temp_list:
                so_temp_list.append(so.id)
                if not origin:
                    origin = so.name
                else:
                    origin += ', ' + so.name

        new_invoice_list = []
        for inv in discount_list:

            all_soi = self.env['sale.order.line'].search([
                ('order_id.id','in',so_list),
                ('discount','=',inv)
                ])
            
            invoice_line = []
            if all_soi:
                for l in all_soi:
                    tax_list = []
                    for tax in l.tax_id:
                        tax_list.append((4, tax.id, None))

                    invoice_line.append((0,0,{
                                            'product_id'            : l.product_id.id,
                                            'name'                  : l.name,      
                                            'account_id'            : l.product_id.categ_id.property_account_income_categ_id.id,
                                            'quantity'              : l.product_uom_qty,
                                            'price_unit'            : l.price_unit,
                                            'uom_id'                : l.product_uom.id,
                                            'discount'              : l.discount,                                        
                                            'invoice_line_tax_ids'  : tax_list,              
                                        }))

                #search journal
                journal_id = self.env['account.journal'].search([('type','=','sale'),('company_id.id','=',self.env.user.company_id.id)],limit=1)

                #start create invoice
                new_invoice_id = self.env['account.invoice'].create({
                                                                'partner_id'        : l.order_id.partner_id.id,
                                                                'date_invoice'      : fields.Datetime.now(),
                                                                'journal_id'        : journal_id.id,
                                                                'account_id'        : journal_id.default_debit_account_id.id,
                                                                'origin'            : origin,
                                                                'user_id'           : self.env.user.id,
                                                                'company_id'        : self.env.user.company_id.id,
                                                                'invoice_line_ids'  : invoice_line,
                                                                })          

                new_invoice_list.append(new_invoice_id.id)
                
                #validate invoice
                if wh_invoice_validate == True:
                    new_invoice_id.action_invoice_open()  

        for so in so_ids:
            so.write({'invoice_status':'invoiced'})

        #GO TO FORM VIEW INVOICE
        action = self.env['ir.model.data'].xmlid_to_object('account.action_invoice_tree1')
        if not action:
            action = {
                'view_type'     : 'form',
                'view_mode'     : 'tree',
                'res_model'     : 'account.invoice',
                'type'          : 'ir.actions.act_window',
            }
        else:
            action = action[0].read()[0]
                
        action['domain'] = "[('id', 'in', " + str(new_invoice_list) + ")]"
        action['name'] = _('Create Invoice')
        return action

