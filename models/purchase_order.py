# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    service_id = fields.Many2one('service.services', string="Servicio", required=False)