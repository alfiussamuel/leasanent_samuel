from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardDashboardSales(models.TransientModel):
    _name = "wizard.dashboard.sales"
    _description = "Dashboard Sales"

    pos_id                      = fields.Many2one('pos.config', 'POS', required=True) 
    sales_id                    = fields.Many2one('res.users', 'Salesperson', required=True) 
    start_date                  = fields.Date('Start Date', required=True) 
    end_date                    = fields.Date('End Date', required=True) 

    #RESULT
    sales_target                = fields.Float('Target Penjualan', readonly=True) 
    sales_result                = fields.Float('Pencapaian (%)', readonly=True) 
    total_sales                 = fields.Float('T. Penjualan', readonly=True) 
    total_sales_normal          = fields.Float('T. Sales Normal', readonly=True) 
    total_sales_disc_a          = fields.Float('T. Sales Disc 20%', readonly=True) 
    total_sales_disc_b          = fields.Float('T. Sales Disc 30%', readonly=True) 
    total_sales_disc_c          = fields.Float('T. Sales Disc 50%', readonly=True) 
    total_sales_special_price   = fields.Float('T. Sales Special', readonly=True) 
    total_qty                   = fields.Float('Total Quantity', readonly=True) 
    total_voucher               = fields.Float('Total Voucher', readonly=True) 
    total_stock                 = fields.Float('Sisa Stock', readonly=True) 

    is_compare                    = fields.Boolean('Compare') 
    is_print                      = fields.Boolean('Is Print') 

    #COMPARISON    
    c_pos_id                      = fields.Many2one('pos.config', 'POS') 
    c_sales_id                    = fields.Many2one('res.users', 'Salesperson') 
    c_start_date                  = fields.Date('Start Date') 
    c_end_date                    = fields.Date('End Date') 

    c_sales_target                = fields.Float('Target Penjualan', readonly=True) 
    c_sales_result                = fields.Float('Pencapaian (%)', readonly=True) 
    c_total_sales                 = fields.Float('T. Penjualan', readonly=True) 
    c_total_sales_normal          = fields.Float('T. Sales Normal', readonly=True) 
    c_total_sales_disc_a          = fields.Float('T. Sales Disc 20%', readonly=True) 
    c_total_sales_disc_b          = fields.Float('T. Sales Disc 30%', readonly=True) 
    c_total_sales_disc_c          = fields.Float('T. Sales Disc 50%', readonly=True) 
    c_total_sales_special_price   = fields.Float('T. Sales Special', readonly=True) 
    c_total_qty                   = fields.Float('Total Quantity', readonly=True) 
    c_total_voucher               = fields.Float('Total Voucher', readonly=True) 
    c_total_stock                 = fields.Float('Sisa Stock', readonly=True) 

    @api.multi
    def button_print_result(self):  
        order_ids = self.env['pos.order'].sudo().search([
            ('session_id.config_id.id', '=', self.pos_id.id),
            ('user_id.id', '=', self.sales_id.id),
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date),
            ('state', 'in', ['paid','done']),
            ])

        order_line_ids = self.env['pos.order.line'].sudo().search([
            ('order_id.session_id.config_id.id', '=', self.pos_id.id),
            ('order_id.user_id.id', '=', self.sales_id.id),
            ('order_id.date_order', '>=', self.start_date),
            ('order_id.date_order', '<=', self.end_date),
            ('order_id.state', 'in', ['paid','done']),
            ('product_id.name', '!=', 'Gift-Coupon'),
            ])

        sales_normal = order_line_ids.filtered(lambda l: l.discount == 0.00 and l.price_unit == l.order_id.pricelist_id.get_product_price(l.product_id, l.qty, l.order_id.partner_id))
        discount_a = order_line_ids.filtered(lambda l: l.discount == 20.00)
        discount_b = order_line_ids.filtered(lambda l: l.discount == 30.00)
        discount_c = order_line_ids.filtered(lambda l: l.discount == 50.00)
        voucher_ids = order_ids.filtered(lambda l: l.coupon_id.id)
        special_price_ids1 = order_line_ids.filtered(lambda l: l.discount != 50.00 and l.discount != 30.00 and l.discount != 20.00 and l.discount != 0.00)
        special_price_ids2 = order_line_ids.filtered(lambda l: l.price_unit != l.order_id.pricelist_id.get_product_price(l.product_id, l.qty, l.order_id.partner_id))
        total_special_price = sum(line.price_subtotal_incl for line in special_price_ids1) + sum(line.price_subtotal_incl for line in special_price_ids2)
        
        #STOCK REMAINING
        stock_ids = self.env['stock.quant'].sudo().search([
            ('location_id.id', '=', self.pos_id.stock_location_id.id),
            ])

        self.total_sales                = sum(line.amount_total for line in order_ids)
        self.total_sales_normal         = sum(line.price_subtotal_incl for line in sales_normal)
        self.total_sales_disc_a         = sum(line.price_subtotal_incl for line in discount_a)
        self.total_sales_disc_b         = sum(line.price_subtotal_incl for line in discount_b)
        self.total_sales_disc_c         = sum(line.price_subtotal_incl for line in discount_c)
        self.total_sales_special_price  = total_special_price
        self.total_qty                  = sum(line.qty for line in order_line_ids)
        self.total_voucher              = len(voucher_ids)
        self.total_stock                = sum(line.qty for line in stock_ids)
        self.sales_target               = self.sales_id.target_sales

        t_pencapaian = 0
        if self.sales_target > 0:
            t_pencapaian = float(self.total_sales) / float(self.sales_target) * 100.00
            self.sales_result = t_pencapaian

        if self.is_compare:
            self.compare_result()

        return {
            'type'          : 'ir.actions.act_window',
            'view_mode'     : 'form',
            'res_model'     : 'wizard.dashboard.sales',
            'target'        : 'new',
            'res_id'        : self.id,
        }

    @api.multi
    def compare_result(self):  
        order_ids = self.env['pos.order'].sudo().search([
            ('session_id.config_id.id', '=', self.c_pos_id.id),
            ('user_id.id', '=', self.c_sales_id.id),
            ('date_order', '>=', self.c_start_date),
            ('date_order', '<=', self.c_end_date),
            ('state', 'in', ['paid','done']),
            ])

        order_line_ids = self.env['pos.order.line'].sudo().search([
            ('order_id.session_id.config_id.id', '=', self.c_pos_id.id),
            ('order_id.user_id.id', '=', self.c_sales_id.id),
            ('order_id.date_order', '>=', self.c_start_date),
            ('order_id.date_order', '<=', self.c_end_date),
            ('order_id.state', 'in', ['paid','done']),
            ('product_id.name', '!=', 'Gift-Coupon'),
            ])

        sales_normal = order_line_ids.filtered(lambda l: l.discount == 0.00 and l.price_unit == l.order_id.pricelist_id.get_product_price(l.product_id, l.qty, l.order_id.partner_id))
        discount_a = order_line_ids.filtered(lambda l: l.discount == 20.00)
        discount_b = order_line_ids.filtered(lambda l: l.discount == 30.00)
        discount_c = order_line_ids.filtered(lambda l: l.discount == 50.00)
        voucher_ids = order_ids.filtered(lambda l: l.coupon_id.id)
        special_price_ids1 = order_line_ids.filtered(lambda l: l.discount != 50.00 and l.discount != 30.00 and l.discount != 20.00 and l.discount != 0.00)
        special_price_ids2 = order_line_ids.filtered(lambda l: l.price_unit != l.order_id.pricelist_id.get_product_price(l.product_id, l.qty, l.order_id.partner_id))
        total_special_price = sum(line.price_subtotal_incl for line in special_price_ids1) + sum(line.price_subtotal_incl for line in special_price_ids2)
        
        #STOCK REMAINING
        stock_ids = self.env['stock.quant'].sudo().search([
            ('location_id.id', '=', self.c_pos_id.stock_location_id.id),
            ])

        self.c_total_sales                = sum(line.amount_total for line in order_ids)
        self.c_total_sales_normal         = sum(line.price_subtotal_incl for line in sales_normal)
        self.c_total_sales_disc_a         = sum(line.price_subtotal_incl for line in discount_a)
        self.c_total_sales_disc_b         = sum(line.price_subtotal_incl for line in discount_b)
        self.c_total_sales_disc_c         = sum(line.price_subtotal_incl for line in discount_c)
        self.c_total_sales_special_price  = total_special_price
        self.c_total_qty                  = sum(line.qty for line in order_line_ids)
        self.c_total_voucher              = len(voucher_ids)
        self.c_total_stock                = sum(line.qty for line in stock_ids)
        self.c_sales_target               = self.c_sales_id.target_sales

        t_pencapaian = 0
        if self.c_sales_target > 0:
            t_pencapaian = float(self.c_total_sales) / float(self.c_sales_target) * 100.00
            self.c_sales_result = t_pencapaian
