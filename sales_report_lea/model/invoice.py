from odoo import api, fields, models, _
from odoo.exceptions import UserError, except_orm, Warning, RedirectWarning, ValidationError
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.osv import expression
from odoo.tools.float_utils import float_compare
import odoo.addons.decimal_precision as dp
import re

class Company(models.Model):
    _inherit = "res.company"
    ppn_account_id = fields.Many2one("account.account", string="Akun PPN")
    hpp_account_id = fields.Many2one("account.account", string="Akun HPP Internal")
    persediaan_account_id = fields.Many2one("account.account", string="Akun Persediaan Barang Jadi")
    hpp_account_id2 = fields.Many2one("account.account", string="Akun HPP Internal Eksternal")



class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _get_picking_po(self):
        for order in self:
            line_ids = []
            if order.purchase_id :
                for l in order.purchase_id.picking_ids:
                    line_ids.append(l.id)
            order.picking_lines = line_ids


    is_internal = fields.Boolean(string="Internal Invoice")
    no_faktur_vendor = fields.Char("No. Faktur Vendor")
    no_po_vendor = fields.Char("No. PO Vendor")
    picking_lines = fields.One2many('stock.picking', compute='_get_picking_po')
    is_hpp_journal = fields.Boolean(string="HPP Journal Posted")

    @api.multi
    def action_correct_paid(self):
        self.write({'move_id': False})
        #self.move_id.unlink()
        self.write({'state': 'cancel'})
        self.action_invoice_cancel

    @api.multi
    def action_post_hpp(self):
        for inv in self:
            if inv.is_internal == True :
                raise UserError(_('Khusus Invoice Eksternal'))
            if not inv.move_id :
                raise UserError(_('Jurnal Pendapatan Harus Di Posting Terlebuh dahulu'))

            data = []
            hpp = 0
            for li in inv.invoice_line_ids:
                hpp = hpp + li.product_id.standard_price
            #DEBIT
            move_d = {
                    'journal_id': inv.move_id.journal_id.id,
                    'account_id': inv.company_id.hpp_account_id2.id,
                    'date': inv.move_id.date,
                    'name': inv.company_id.hpp_account_id2.name,
                    'credit': 0,
                    'debit': hpp
            }

            data.append(((0, 0, move_d)))
            move_c = {
                    'journal_id': inv.move_id.journal_id.id,
                    'account_id': inv.company_id.persediaan_account_id.id,
                    'date': inv.move_id.date,
                    'name': inv.company_id.persediaan_account_id.name,
                    'credit': hpp,
                    'debit': 0
            }
            data.append(((0, 0, move_c)))

            if inv.move_id.state == 'posted':
                inv.move_id.button_cancel()
            inv.move_id.write({'line_ids': data})
            inv.move_id.post()
            inv.write({'is_hpp_journal':True})

    @api.multi
    def action_unpost_hpp(self):
        for inv in self:
            if inv.is_internal == True:
                raise UserError(_('Khusus Invoice Eksternal'))
            if not inv.move_id:
                raise UserError(_('Jurnal Pendapatan Harus Di Posting Terlebuh dahulu'))

            cursor = self.env.cr
            account_hpp = []
            account_hpp.append(inv.company_id.persediaan_account_id.id)
            account_hpp.append(inv.company_id.hpp_account_id2.id)
            move_line_ids = self.env['account.move.line'].search([('move_id', '=', inv.move_id.id),('account_id', 'in', account_hpp)])
            if move_line_ids :
                if inv.move_id.state == 'posted':
                    inv.move_id.button_cancel()

                cursor.execute( """
                                delete from account_move_line where move_id = %s and account_id in %s
                                """, (inv.move_id.id, tuple(account_hpp)))

                inv.move_id.post()
                inv.write({'is_hpp_journal': False})

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            date_invoice = inv.date_invoice
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            if inv.type == 'out_invoice' or 'out_refund':
                iml += inv.tax_line_move_line_get_ppn_keluaran()
            else:
                iml += inv.tax_line_move_line_get()
            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = \
                inv.with_context(ctx).payment_term_id.with_context(currency_id=inv.currency_id.id).compute(total,
                                                                                                           date_invoice)[
                    0]
                res_amount_currency = total_currency
                ctx['date'] = date_invoice
                for i, t in enumerate(totlines):

                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
                    else:
                        amount_currency = False
                    # raise Warning(_(str(t[1])))
                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                #if inv.type == 'out_invoice':
                   #total = total + inv.amount_tax
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })

            if inv.is_internal == True :
                hpp = 0
                for li in inv.invoice_line_ids :
                    hpp = hpp + li.product_id.standard_price

                iml.append({
                    'type': 'dest',
                    'name': inv.company_id.persediaan_account_id.name,
                    'price': 0 - hpp,
                    'account_id': inv.company_id.persediaan_account_id.id,
                    'date_maturity': inv.date_due,
                    'invoice_id': inv.id
                })

                iml.append({
                    'type': 'src',
                    'name': inv.company_id.hpp_account_id.name,
                    'price': hpp,
                    'account_id': inv.company_id.hpp_account_id.id,
                    'date_maturity': inv.date_due,
                    'invoice_id': inv.id
                })


            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)
            #raise Warning(_(str(line)))


            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or date_invoice

            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        if self.nomor_faktur_id:
            self.faktur_pajak_create()
        return True

    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            if line.quantity == 0:
                continue
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))
            analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
            price = line.price_subtotal
            if self.type == 'out_invoice' or 'out_refund':
                price = line.lea_dpp

            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': price,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'invoice_id': self.id,
                'analytic_tag_ids': analytic_tag_ids
            }
            if line['account_analytic_id']:
                move_line_dict['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            res.append(move_line_dict)
        # raise Warning('Tes')
        return res

    @api.model
    def tax_line_move_line_get_ppn_keluaran(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for x in self:
            res.append({
                    'type': 'tax',
                    'name': x.company_id.ppn_account_id.name,
                    'price_unit': x.amount_tax,
                    'quantity': 1,
                    'price': x.amount_tax,
                    'account_id': x.company_id.ppn_account_id.id,
                    'invoice_id': self.id,
            })
        return res

        # Load all unsold PO lines

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line:
            # Load a PO line only once
            if line in self.invoice_line_ids.mapped('purchase_line_id'):
                continue
            if line.product_id.purchase_method == 'purchase':
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                qty = 0.0
            taxes = line.taxes_id
            invoice_line_tax_ids = self.purchase_id.fiscal_position_id.map_tax(taxes)
            data = {
                'purchase_line_id': line.id,
                'name': self.purchase_id.name + ': ' + line.name,
                'origin': self.purchase_id.origin,
                'uom_id': line.product_uom.id,
                'product_id': line.product_id.id,
                'account_id': self.env['account.invoice.line'].with_context(
                    {'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
                'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id, round=False),
                'quantity': qty,
                'discount': 0.0,
                'account_analytic_id': line.account_analytic_id.id,
                'analytic_tag_ids': line.analytic_tag_ids.ids,
                'invoice_line_tax_ids': invoice_line_tax_ids.ids
            }
            account = new_lines.get_invoice_line_account('in_invoice', line.product_id,
                                                         self.purchase_id.fiscal_position_id, self.env.user.company_id)
            if account:
                data['account_id'] = account.id
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids = new_lines
        self.payment_term_id = self.purchase_id.payment_term_id.id

        #self.purchase_id = False
        return {}


