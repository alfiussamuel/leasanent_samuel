# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from odoo import api, fields, models, _
from odoo import tools
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class VoucherConfig(models.Model):
	_name = "voucher.config"

	@api.model
	def _get_default_voucher_product(self):
		ir_model_data = self.env['ir.model.data']
		temp_id = ir_model_data.get_object_reference('wk_coupons', 'product_product_coupon')[1]
		if temp_id:
			return temp_id


	name = fields.Char(string='Name', size=100, default='Default Configuration for Website Gift Voucher' )
	product_id = fields.Many2one(comodel_name='product.product', string='Product', default=_get_default_voucher_product)
	min_amount =  fields.Float(string='Minimum Voucher Value',default=1.0)
	max_amount = fields.Float(string='Maximum Voucher Value', default=9999)
	max_expiry_date = fields.Date(string='Expiry Date',help="Date on which Voucher is expired." ,default=datetime.now().date())
	partially_use = fields.Boolean(string='Partially Use')
	active = fields.Boolean(string='Active', default=1, help="By unchecking the active field you can disable this voucher  configuration without deleting it.")
	default_name = fields.Char(string='Name', size=100, default="Gift Voucher", help="This will be displayed in the order summary, as well as on the invoice.")
	default_validity = fields.Integer(string='Validity(in days)', default=-1, help="Validity of this Voucher in days")
	default_availability = fields.Integer(string='Total Available', default=1, help="Total availability of this voucher")
	default_value = fields.Float(string='Voucher Value', default=1.0)
	voucher_usage = fields.Selection([('both', 'Both POS & Ecommerce'),('ecommerce', 'Ecommerce'),('pos', 'Point Of Sale')], default="both", string="Coupon Used In" ,help="Choose where you want to use the coupon pos/ecommerce and odoocore")
	customer_type = fields.Selection([('special_customer', 'Special Customer'),('general', 'All Customers')], required=True, default="general", string="Customer Type" ,help="on choosing the General the coupon can be applied for all customers, and on choosing the Special Customer the Coupon can be used for a particlar customer and can be partially redeemed.")
	partial_limit = fields.Integer('Partial Limit' , default=-1)
	use_minumum_cart_value = fields.Boolean('Use Cart Amount Validation', help="Use this option for using this voucher based on the cart amount.")
	minimum_cart_amount = fields.Float('Minimum Cart Amount', help="Apply this coupon only if the cart value is greater than this amount.")
	

	@api.model
	def _get_default_values(self):
		self_obj = self.search([('active','=',True)])
		if not self_obj:
			raise ValidationError("Sorry, Please configure the module before creating any voucher.")
		temp_dict = {
		'product_id':self_obj.product_id.id,
		'max_amount':self_obj.max_amount,
		'min_amount':self_obj.min_amount,
		'max_expiry_date':self_obj.max_expiry_date,
		# 'one_time_use':self_obj.one_time_use,
		'default_name':self_obj.default_name,
		'default_validity':self_obj.default_validity,
		'default_availability':self_obj.default_availability,
		'default_value':self_obj.default_value,
		'partially_use':self_obj.partially_use,
		'voucher_usage':self_obj.voucher_usage,
		'customer_type':self_obj.customer_type,
		'partial_limit':self_obj.partial_limit,
		'use_minumum_cart_value':self_obj.use_minumum_cart_value,
		'minimum_cart_amount':self_obj.minimum_cart_amount,
		}
		return temp_dict
		
	@api.model
	def create(self, vals):
		self_obj = self.search([('active','=',True)])
		if self_obj:
			raise UserError("Sorry, you can not create more than one configuration.")
		if vals.get('min_amount') < 0 or vals.get('max_amount') < 0 :
			raise ValidationError('Minimum or maximum value should not be negative.')
		if  vals.get('max_amount') < vals.get('min_amount'):
			raise ValidationError('Maximum value should be greater than minimum value.')
		if vals.get('default_value') < vals.get('min_amount'):
			raise ValidationError('Voucher value should be greater than minimum value')
		if vals.get('default_value') > vals.get('max_amount'):
			raise ValidationError('Voucher value should be less than maximum value')
		if vals.get('default_value') <= 0:
			raise ValidationError('Voucher value should be greater than 0.')
		if  vals.get('min_amount') <= 0:
			raise ValidationError('Minimum value should not be <= 0')
		if  vals.get('max_amount') <= 0:
			raise ValidationError('Maximum value should not be <= 0')
		return super(VoucherConfig, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.has_key('default_value') and vals['default_value'] <= 0 :
			raise ValidationError('Voucher value should be greater than 0.')
		if vals.has_key('min_amount') and vals['min_amount'] <= 0:
			raise ValidationError('Minimum value should not be <= 0')
		if vals.has_key('max_amount') and vals['max_amount'] <=0:
			raise ValidationError('Maximum value should not be <= 0')
		if vals.get('min_amount') and vals.get('max_amount') and vals.get('min_amount') >  vals.get('max_amount'):
			raise ValidationError('Maximum value should not be less than minimum value.')
		if vals.get('min_amount') and vals.get('min_amount') > self.max_amount:
			raise ValidationError('Maximum value should not be less than minimum value.')
		if vals.get('max_amount') and vals.get('max_amount') < self.min_amount:
			raise ValidationError('Maximum value should be greater than minimum value.')
		if vals.get('default_value'):
			if vals.get('min_amount'):
				if vals.get('default_value') < vals.get('min_amount'):
					raise ValidationError('Voucher value should be greater than minimum value')
			elif vals.get('default_value') < self.min_amount:
				raise ValidationError('Voucher value should be greater than minimum value')
			if vals.get('max_amount'):
				if vals.get('default_value') > vals.get('max_amount'):
					raise ValidationError('Voucher value should be less than maximum value')
			elif vals.get('default_value') > self.max_amount:
				raise ValidationError('Voucher value should be less than maximum value')
		return super(VoucherConfig, self).write(vals)