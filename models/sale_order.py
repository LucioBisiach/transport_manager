# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

from datetime import datetime


# Clase de vinculo con ordenes de venta y compra


class saleInherit(models.Model):
    _inherit = 'sale.order'

    service_id = fields.Many2one('service.services', string="Servicio", required=False)