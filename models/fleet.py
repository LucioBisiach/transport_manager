# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

import time

import logging
_logger = logging.getLogger(__name__)


class fleetService(models.Model):
    _name = 'fleet.services'

    name = fields.Char(string="Dominio")

    marca = fields.Many2one('fleet.vehicle.model.brand', string="Marca")
    modelo = fields.Char(string="Modelo")
    año = fields.Char(string="Año")
    odometro_actual = fields.Integer(string="Odometro Actual")

    def return_action_to_open(self):
        """ Esto abre la vista xml especificada en xml_id para el empleado actual """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('transport_manager', xml_id)
            res.update(
                context=dict(self.env.context, default_fleet=self.id, group_by=False),
                domain=[('employee', '=', self.id)]
            )
            return res
        return False

class odometerFleetService(models.Model):
    _name = 'odometer.fleet.service'

    name = fields.Integer(string="Odometro")

    fecha = fields.Date(string="Fecha")
    dominio = fields.Many2one('fleet.service', string="Dominio")


class typeFleetService(models.Model):
    _name = 'type.fleet.services'

    name = fields.Char(string="Tipo Flota")


class thirdEmployeeService(models.Model):
    _name = 'third.fleet.services'

    name = fields.Char(string='Dominio')

    tipo = fields.Many2one('type.fleet.services',string='Tipo')
    pertenece_a = fields.Many2one('res.partner', string='Pertenece A:')

    def return_action_to_open(self):
        """ Esto abre la vista xml especificada en xml_id para el chofer actual """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('transport_manager', xml_id)
            res.update(
                context=dict(self.env.context, default_employee_third=self.id, group_by=False),
                domain=[('employee_third', '=', self.id)]
            )
            return res
        return False


    