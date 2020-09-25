# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

import time

import logging
_logger = logging.getLogger(__name__)


class employeeService(models.Model):
    _name = 'employee.services'

    name = fields.Char(string="Nombre")

    telefono = fields.Char(string='Telefono')
    direccion = fields.Char(string='Direccion')
    n_identifiacion = fields.Char(string='CUIT/CUIL/DNI')
    email = fields.Char(string='Email')
    localidad = fields.Char(string='Localidad')
    
    third_employee = fields.Many2one('third.employee.services', string="Chofer Tercerizado")
    
    cbu = fields.Char(string='CBU')
    banco = fields.Many2one('res.bank', string='Banco')
    ref_diario = fields.Many2one('account.journal', string='Diario')
    label_cuenta = fields.Char(string="Label Cuenta Analítica")

    cuenta_analitica_ids = fields.Many2many('account.move.line', compute="_compute_data",string="Cuenta Empleado")
    total_cuenta = fields.Float(string="Saldo", compute="_compute_total_account")

    ref_user = fields.Many2one('res.partner', string="Contacto Relacionado")


    @api.depends('ref_diario')
    def _compute_data(self):
        # Definimos el dominio con el cual queremos filtrar los datos que vamos a traer de la clase service.services
        account_journal_domain = [
            ('journal_id', 'in', self.ref_diario.ids),
            ('account_id', 'in', self.ref_diario.default_debit_account_id.ids),
        ]
        # Traemos los servicios de dicha clase y los ordenamos por los valores que querramos, en caso de querer ordenar por mas valores, seguir con una coma ingresar el campo y el orden
        account_journal = self.env['account.move.line'].search(account_journal_domain, order='date desc')
        self.cuenta_analitica_ids = account_journal

    def _compute_total_account(self):
        credit = 0
        debit = 0
        for linea in self.cuenta_analitica_ids:
            credit += linea.credit
            debit += linea.debit
        self.total_cuenta = debit - credit

    @api.onchange('ref_diario')
    def _get_label_cuenta(self):
        self.label_cuenta = self.ref_diario.default_debit_account_id.name
        _logger.info("Label Cuenta %s", self.label_cuenta)


    def return_action_to_open(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('transport_manager', xml_id)
            res.update(
                context=dict(self.env.context, default_employee=self.id, group_by=False),
                domain=[('employee', '=', self.id)]
            )
            return res
        return False

    def return_action_to_open_gastos(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('account', xml_id)
            res.update(
                context=dict(self.env.context, default_ref_gasto_empleado=self.id, 
                default_es_gasto=True, default_type='in_invoice', group_by=False),
                domain=[('ref_gasto_empleado', '=', self.id)]
            )
            return res
        return False

    # def return_action_to_open_libro_mayor(self):
    #     self.ensure_one()
    #     xml_id = self.env.context.get('xml_id')
    #     if xml_id:
    #         res = self.env['ir.actions.act_window'].for_xml_id('account', xml_id)
    #         res.update(
    #             context=dict(self.env.context, default_journal_id=self.ref_diario.id, group_by=False),
    #             domain=[('journal_id', '=', self.ref_diario.id)]
    #             )
    #         return res
    #     return False

    def return_action_to_open_transferencia(self):
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:
            res = self.env['ir.actions.act_window'].for_xml_id('account_payment_group', xml_id)
            res.update(
                context=dict(self.env.context, default_destination_journal_id=self.ref_diario.id, default_payment_type='transfer', group_by=False),
                domain=[('destination_journal_id', '=', self.ref_diario.id)]
                )
            return res
        return False


class thirdEmployeeService(models.Model):
    _name = 'third.employee.services'

    name = fields.Char(string='Nombre')
    telefono = fields.Char(string='Telefono')
    n_identifiacion = fields.Char(string='DNI')
    email = fields.Char(string='Email')
    pertenece_a = fields.Many2one('res.partner', string='Pertenece A:')

    nota = fields.Text(string='Texto Chofer', readonly=True)

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


class documentEmployeeService(models.Model):
    _inherit = 'account.move'

    ref_gasto_empleado = fields.Many2one('employee.services', string='Empleado')
    es_gasto = fields.Boolean(string="Es Gasto ?", default=False)


    @api.onchange('es_gasto')
    def _field_employee(self):
        if self.es_gasto == False:
            self.ref_gasto_empleado = ''


class sueldosEmployee(models.Model):
    _name = 'sueldos.employee.services'

    name = fields.Char(string="Mes")
    date_start = fields.Date(string='Inicio')
    date_stop = fields.Date(string='Fin')
    employee = fields.Many2one('employee.services', string='Empleado')
    # qty_viatico_comida = fields.Float(string="Comida", compute="_get_viaticos")
    # qty_viatico_especial = fields.Float(string="V. Especial", compute="_get_viaticos")
    # qty_viatico_km = fields.Float(string="Km", compute="_get_viaticos")
    

    # tot_viatico_comida = fields.Float(compute="_get_viaticos")
    # tot_viatico_especial = fields.Float(compute="_get_viaticos")
    # tot_viatico_km = fields.Float(compute="_get_viaticos")


    lista_servicios = fields.Many2many('service.services', compute="_compute_data",string="Servicios")


    @api.depends('date_start', 'date_stop', 'employee')
    def _compute_data(self):
        # Definimos el dominio con el cual queremos filtrar los datos que vamos a traer de la clase service.services
        servicios_domain = [
            ('employee', 'in', self.employee.ids),
            ('date_start', '>=', self.date_start),
            ('date_start', '<=', self.date_stop),
        ]
        # Traemos los servicios de dicha clase y los ordenamos por los valores que querramos, en caso de querer ordenar por mas valores, seguir con una coma ingresar el campo y el orden
        servicios = self.env['service.services'].search(servicios_domain, order='date_start asc')
        self.lista_servicios = servicios

    # def _get_viaticos(self):
    #     if len(self.lista_servicios) == 0:
    #         self.viatico_comida = 0
    #     else:
    #         for obj in self.lista_servicios:
    #             for costos in obj.costos_ids:
    #                 if costos.employee.ids == self.employee.ids:
    #                     _logger.info("Estoy Aca: %s", costos.valor) 
    #                     if costos.name.code == '4.1.12':
    #                         self.qty_viatico_comida += costos.qty
    #                         self.tot_viatico_comida += costos.total
    #                     if costos.name.code == '4.1.13':
    #                         self.qty_viatico_especial += costos.qty
    #                         self.tot_viatico_especial += costos.total
    #                     if costos.name.code == '4.2.4':
    #                         self.qty_viatico_km += costos.qty
    #                         self.tot_viatico_km += costos.total




