# -*- coding: utf-8 -*-

import base64
from ast import literal_eval

from odoo import models, fields, api
from odoo.tools import pickle as cPickle


class pos_data_cache(models.Model):
    _name = 'pos.data.cache'

    compute_user_id = fields.Many2one('res.users', 'Cache compute user', required=True)
    config_id = fields.Many2one('pos.config', ondelete='cascade', required=True)
    cache = fields.Binary(attachment=True)
    partner_domain = fields.Text(required=True)
    partner_fields = fields.Text(required=True)


    @api.model
    def refresh_all_caches(self):
        self.env['pos.data.cache'].search([]).refresh_cache()

    @api.one
    def refresh_cache(self):
        partners = self.env['res.partner'].search(self.get_partner_domain())
        prod_ctx = partners.with_context(pricelist=self.config_id.pricelist_id.id, display_default_code=False,
                                         lang=self.compute_user_id.lang)
        prod_ctx = prod_ctx.sudo(self.compute_user_id.id)
        res = prod_ctx.read(self.get_partner_fields())
        datas = {
            'cache': base64.encodestring(cPickle.dumps(res)),
        }

        self.write(datas)

    @api.model
    def get_partner_domain(self):
        return literal_eval(self.partner_domain)

    @api.model
    def get_partner_fields(self):
        return literal_eval(self.partner_fields)

    @api.model
    def get_cache(self, domain, fields):
        if not self.cache or domain != self.get_partner_domain() or fields != self.get_partner_fields():
            self.partner_domain = str(domain)
            self.partner_fields = str(fields)
            self.refresh_cache()

        cache = base64.decodestring(self.cache)
        return cPickle.loads(cache)


class pos_config(models.Model):
    _inherit = 'pos.config'

    @api.one
    @api.depends('partner_cache_ids')
    def _get_oldest_partner_cache_time(self):
        pos_partner_cache = self.env['pos.data.cache']
        oldest_cache = pos_partner_cache.search([('config_id', '=', self.id)], order='write_date', limit=1)
        if oldest_cache:
            self.oldest_partner_cache_time = oldest_cache.write_date

    # Use a related model to avoid the load of the cache when the pos load his config
    partner_cache_ids = fields.One2many('pos.data.cache', 'config_id')
    oldest_partner_cache_time = fields.Datetime(compute='_get_oldest_partner_cache_time', string='Oldest Partner cache time', readonly=True)

    def _get_partner_cache_for_user(self):
        pos_cache = self.env['pos.data.cache']
        cache_for_user = pos_cache.search([('id', 'in', self.partner_cache_ids.ids), ('compute_user_id', '=', self.env.uid)])

        if cache_for_user:
            return cache_for_user[0]
        else:
            return None

    @api.multi
    def get_partner_from_cache(self, fields, domain):
        cache_for_user = self._get_partner_cache_for_user()

        if cache_for_user:
            return cache_for_user.get_cache(domain, fields)
        else:
            pos_cache = self.env['pos.data.cache']
            pos_cache.create({
                'config_id': self.id,
                'partner_domain': str(domain),
                'partner_fields': str(fields),
                'compute_user_id': self.env.uid
            })
            new_cache = self._get_partner_cache_for_user()
            return new_cache.get_cache(domain, fields)

    @api.one
    def delete_partner_cache(self):
        self.partner_cache_ids.unlink()

