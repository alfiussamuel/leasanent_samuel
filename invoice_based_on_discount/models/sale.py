from odoo import api, fields, models,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError, except_orm, Warning

class SalesOrderCustom(models.Model):
	_name = 'sale.order.custom'

	@api.multi
	def buat_invoice(self):
		self.ensure_one()
		context = dict(self._context or {})
		active_ids = context.get('active_ids', []) or []
		sale_order = self.env['sale.order'].browse(active_ids)
		invoice_id = self.env['account.invoice']
		invoice_line_id = self.env['account.invoice.line']
		sale_order_line = self.env['sale.order.line']
		discount = []
		order_data = []
		i = 0

		for rec in sale_order:
			for res in rec.order_line:
				discount.append(res.discount)

		grouping = [x for n, x in enumerate(discount) if x not in discount[:n]]
		# print "LEN============", len(grouping)
		print "grup============", grouping
		print "dis============", discount
		# print "LENdis============", len(discount)
		for x in grouping:
			order_line_ids = sale_order_line.search([('order_id','in',active_ids),('discount','=',grouping[i])])
			print "============ORDER",order_line_ids
			vals = invoice_id.create({
					# 'origin' : ", ".join(source),
					'partner_id' : rec.partner_id.id,
					'payment_term_id' : rec.payment_term_id.id,
				})
			for data in order_line_ids:
				invoice_line_id.create({
					'invoice_id' : vals.id,
					'product_id' : data.product_id.id,
					'name' : data.name,
					'account_id' : vals.partner_id.property_account_receivable_id.id,
					'quantity' : data.product_uom_qty,
					'price_unit' : data.price_unit,
					'discount' : data.discount,
					})
			i +=1