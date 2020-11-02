# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


import logging
_logger = logging.getLogger(__name__)



class serviceCity(models.Model):
    _name = 'service.places'

    name = fields.Char(string="Nombre")
    url_googlemaps = fields.Char(string="Link Google Map")

    ref_service_load = fields.Many2one('service.services', invisible=True, readonly=True)
    ref_service_download = fields.Many2one('service.services', invisible=True, readonly=True)


    @api.onchange('state')
    def _get_country(self):
        for rec in self:
            rec.country = rec.state.country_id


class requirementDocument(models.Model):
    _name = 'requirement.document.service'

    name = fields.Char(string="Documentos Requeridos")



class sueldosTarifas(models.Model):
    _name = 'sueldos.tarifas.employee.services'

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")  
    
    lista_tarifas = fields.One2many('sueldos.tarifas.vencimientos.employee.services', 'ref_sueldos_tarifas', ondelete="cascade", string="Lista Tarifas")

class sueldosTarifasVencimientos(models.Model):
    _name = 'sueldos.tarifas.vencimientos.employee.services'

    name = fields.Char(compute="_get_code", string="Codigo")
    date_start = fields.Datetime(string="Fecha Inicio")
    date_stop = fields.Datetime(string="Fecha Vencimiento")

    tarifa = fields.Float(string="Tarifa")

    ref_sueldos_tarifas = fields.Many2one('sueldos.tarifas.employee.services', invisible=True)

    @api.depends('ref_sueldos_tarifas.code')
    def _get_code(self):
        for item in self:
            item.name = self.ref_sueldos_tarifas.code