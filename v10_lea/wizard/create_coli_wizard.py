from odoo import api,fields,models,_ 
import time
from odoo.exceptions import except_orm, Warning, RedirectWarning


class AdhPreCreateColiWizard(models.Model):
	_name ='lea.create.coli'

	coli_name = fields.Char('Coli')
	barcode = fields.Char('Barcode')	
	product_ids = fields.One2many('lea.create.coli.line', 'reference', 'Daftar Barcode')						
	
	@api.onchange('barcode')
	def barcode_scanning(self):		
		product_obj = self.env['product.product']
		product_id = product_obj.search([('barcode', '=', self.barcode)])
		print "Product ID ", product_id
		if self.barcode and not product_id:
			print "AAAAAAAAAAAAAAAAAAAAA"
			self.barcode = False
			return {'warning': {
					'title': "Warning",
					'message': "No product is available for this barcode",
					}
				}
			
		elif self.barcode and product_id:
			print "BBBBBBBBBBBBBBBBBBBBB"
			current_line = self.env['lea.create.coli.line'].search([('product_id', '=', product_id.id),('reference', '=', self.id)])
			qty = 0
			if current_line:
				print "CCCCCCCCCCCCCCCCCCCCCCCC"
				qty = current_line[0].qty				
				self.env['lea.create.coli.line'].write({														
														'qty': qty + 1,
														})				
			elif not current_line:
				print "DDDDDDDDDDDDDDDDDDDDDDDD"
				new_id = self.env['lea.create.coli.line'].create({
														'reference': self.id,
														'product_id': product_id.id,
														'qty': 1,
														})				
		self.update({
		    'attendance_line': [(0, 0, {new_id})],
		})				

class AdhPreCreateColiWizardLine(models.Model):
	_name ='lea.create.coli.line'

	reference = fields.Many2one('lea.create.coli', 'Reference')	
	product_id = fields.Many2one('product.product', 'Product')
	qty = fields.Integer('Qty')
	
		
	