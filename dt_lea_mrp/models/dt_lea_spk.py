from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from dateutil.relativedelta import relativedelta
import datetime
import time
from datetime import datetime
import odoo.addons.decimal_precision as dp


class dt_lea_spk(models.Model):
    _name = 'dt.lea.spk'
    _description = 'Surat Perintah Kerja'
    _rec_name = "document_number"


    def unlink(self):
        for res in self:
            spk_line = self.env['dt.lea.spk.product.line'].search([('spk_product_id','=',res.id)])
            if spk_line:
                spk_line.unlink()
            spk_bom_line = self.env['dt.lea.spk.bom.line'].search([('spk_bom_id','=',res.id)])
            if spk_bom_line:
                spk_bom_line.unlink()
                
        return super(dt_lea_spk, self).unlink()

    @api.depends('product_list_ids.total')
    def _get_qty_total(self):
        qty_total = 0
        for rec in self.product_list_ids :
            qty_total += rec.total
        self.qty_total = qty_total

    def get_sequence(self, name=False, obj=False, pref=False, context=None):
        sequence_id = self.env['ir.sequence'].search([
            ('name', '=', name),
            ('code', '=', obj),
            ('prefix', '=', pref + '%(month)s-%(year)s/')
        ])
        if not sequence_id :
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': name,
                'code': obj,
                'implementation': 'no_gap',
                'prefix': pref + '%(month)s-%(year)s/',
                'padding': 6
            })
        return sequence_id.next_by_id()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')):
            vals['document_number'] = self.get_sequence('SPK','dt.lea.spk','SPK/'%vals)
        return super(dt_lea_spk, self).create(vals)


    document_number = fields.Char("Document Number")
    date = fields.Date("Date", default=fields.Date.today())
    nomor_ppj = fields.Char("Nomor PPJ")
    lampiran_ppj = fields.Binary("Lampiran PPJ")
    partner_id = fields.Many2one("res.partner", "Customer")
    product_id = fields.Many2one("product.product", "Article No.")
    fitting_style_id = fields.Many2one("dt.lea.fitting.style", "Fitting Style")
    price_unit = fields.Float("Price Unit")
    pola_tanggal = fields.Date("Pola Tanggal")
    lot = fields.Char("Lot")
    consumed_material = fields.Float("Consumed Material")
    consumed_material_uom_id = fields.Many2one("product.uom", "Consumed Material Uom")
    no_batch = fields.Char("No. Batch")
    washing_id = fields.Many2one("dt.lea.washing.method", "Washing")
    code_lab_id = fields.Many2one("dt.lea.code.lab", "Code Lab")
    delivery_time = fields.Date("Delivery Time")
    tanggal_turun_spk = fields.Date("Tanggal Turun SPK")
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('distribute','Distribute'),('cancel','Cancel')], default="draft", string="State")
    jenis_permintaan = fields.Selection([('once','Once'),('repeat','Repeat')])
    brand_id = fields.Many2one("dt.lea.master.brand", "Brand")
    production_group_id = fields.Many2one("dt.lea.production.group", "Production Group")
    qty_total = fields.Integer("Quantity Total", compute="_get_qty_total", store=True)
    notes = fields.Text("Notes")
    product_list_ids = fields.One2many("dt.lea.spk.product.line", "spk_product_id", "Product List")
    spk_bom_ids = fields.One2many("dt.lea.spk.bom.line", "spk_bom_id", "Bill of Material")

    @api.multi
    def action_approved(self):
        self.state = 'approved'

    @api.multi
    def action_distribute(self):
        self.state = 'distribute'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'


class dt_lea_spk_product_line(models.Model):
    _name = 'dt.lea.spk.product.line'
    _description = 'Product Line SPK'


    @api.depends('size_28','size_29','size_30','size_31','size_32','size_33',
                'size_34','size_35','size_36','size_37','size_38','size_39','size_40')
    def _get_total(self):
        for rec in self :
            rec.total = rec.size_28 + rec.size_29 + rec.size_30 + rec.size_31 + rec.size_32 + rec.size_33 + rec.size_34 + rec.size_35 + rec.size_36 + rec.size_37 + rec.size_38 + rec.size_39 + rec.size_40

    spk_product_id = fields.Many2one("dt.lea.spk", "SPK Product")
    distribusi_id = fields.Many2one("stock.warehouse", "Distribusi")
    size_28 = fields.Integer("Size 28")
    size_29 = fields.Integer("Size 29")
    size_30 = fields.Integer("Size 30")
    size_31 = fields.Integer("Size 31")
    size_32 = fields.Integer("Size 32")
    size_33 = fields.Integer("Size 33")
    size_34 = fields.Integer("Size 34")
    size_35 = fields.Integer("Size 35")
    size_36 = fields.Integer("Size 36")
    size_37 = fields.Integer("Size 37")
    size_38 = fields.Integer("Size 38")
    size_39 = fields.Integer("Size 39")
    size_40 = fields.Integer("Size 40")
    total = fields.Integer("Total", compute="_get_total")


class dt_lea_spk_bom_line(models.Model):
    _name = 'dt.lea.spk.bom.line'
    _description = 'Bill of Material SPK'


    @api.onchange("product_id")
    def onchange_uom_id(self):
        self.uom_id = self.product_id.uom_id.id

    spk_bom_id = fields.Many2one("dt.lea.spk", "Bill of Material SPK")
    product_id = fields.Many2one("product.product", "Material")
    kebutuhan_pcs = fields.Float("Kebutuhan / Pcs")
    kebutuhan_batch = fields.Float("Kebutuhan / Batch")
    uom_id = fields.Many2one("product.uom", "Satuan")
    tags_id = fields.Many2one("dt.lea.master.bom.tags", "Tags")
    kode_warna_id = fields.Many2one("dt.lea.master.color.code", "Kode Warna")


class dt_lea_production_group(models.Model):
    _name = 'dt.lea.production.group'
    _description = 'Production Group'

    name = fields.Char("Name")
    active = fields.Boolean("Active")


class dt_lea_master_brand(models.Model):
    _name = 'dt.lea.master.brand'
    _description = 'Master Brand'

    name = fields.Char("Name")
    partner_id = fields.Many2one("res.partner")
    active = fields.Boolean("Active")


class dt_lea_fitting_style(models.Model):
    _name = 'dt.lea.fitting.style'
    _description = 'Fitting Style'

    name = fields.Char("Name")
    active = fields.Boolean("Active")


class dt_lea_washing_method(models.Model):
    _name = 'dt.lea.washing.method'
    _description = 'Washing Method'

    name = fields.Char("Name")
    active = fields.Boolean("Active")


class dt_lea_code_lab(models.Model):
    _name = 'dt.lea.code.lab'
    _description = 'Code Lab'

    name = fields.Char("Name")
    active = fields.Boolean("Active")


class dt_lea_master_color_code(models.Model):
    _name = 'dt.lea.master.color.code'
    _description = 'Master Color Code'

    name = fields.Char("Name")
    active = fields.Boolean("Active")


class dt_lea_master_bom_tags(models.Model):
    _name = 'dt.lea.master.bom.tags'
    _description = 'Master BoM Tags'

    name = fields.Char("Name")
    active = fields.Boolean("Active")