# -*- coding: utf-8 -*-

from odoo import models, fields, multi_process,api, _
from odoo.exceptions import ValidationError

# from pyfcm import FCMNotification

from datetime import datetime



import logging
_logger = logging.getLogger(__name__)

class services(models.Model):
    _name = 'service.services'
    _description = 'Services of Transport Manager'

    # Nombre y sequencia
    name = fields.Char(string="N° Servicio", copy=False, readonly=True)
    label_service = fields.Char(string="Nombre del Servicio", required=True)

    # N° Referencia
    n_ref = fields.Char(string="N° de Referencia")
    n_talonario = fields.Char(string="N° Talonario")

    # Fechas
    date_start = fields.Datetime(string="Fecha Inicio ", default=fields.Datetime.now, required=True)
    date_stop = fields.Datetime(string="Fecha Fin ", default=fields.Datetime.now, required=True)

    # Odometro
    odo_start = fields.Integer(string="Odometro Inicial", default=False)
    odo_end = fields.Integer(string="Odometro Final", default=False)
    odo_total = fields.Integer(compute="_odo_total", string="Odometro Total")

    #Asignaciones
    employee = fields.Many2many('employee.services', string="Empleado")
    fleet = fields.Many2one('fleet.services', string="Flota")
    fleet_add = fields.Many2one('fleet.services', string="Enganche")

    #Tercerizado
    employee_third = fields.Many2one('third.employee.services', string="Chofer")
    fleet_third = fields.Many2one('third.fleet.services', string="Dominio Tractor")
    fleet_add_third = fields.Many2one('third.fleet.services', string="Dominio Acoplado")


    # Origenes y Destinos
    location_load = fields.Many2many('service.places', 'ref_service_load',string="Localidad de Carga", required=True)
    location_download = fields.Many2many('service.places', 'ref_service_download',string="Localidad de Descarga", required=True)

    nota = fields.Text(string="Nota")

    # Clientes (Falta crear filtro)
    customer = fields.Many2one('res.partner', string="Cliente", required=True)

    # Provedores (falta crear filtro)
    provider = fields.Many2one('res.partner', string="Proveedor")


    # Campos de estados
    state = fields.Selection([
        ('borrador','Borrador'),
        ('confirmado','Confirmado'),
        ('realizado','Realizado'),
        ('cancelado','Cancelado')], string="Estado", default="borrador")

    #Sevicio tercerizado
    outsourced_service = fields.Boolean(string="Servicio Tercerizado", default=False)

    # Relacion con documentos del servicio
    lst_documents = fields.One2many('service.documents', 'ref_services', string="Documentos", ondelete="cascade")
    state_document = fields.Boolean(default=False, string="Estado de Documentos", invisible=True)

    # Relacion con compras
    purchase_orders_ids = fields.One2many('purchase.order', 'service_id', string="Compras")
    total_purchases = fields.Integer(compute='_get_total_purchases', store=False)
    state_inv_p = fields.Boolean(compute="_state_fa_c", string="Estado FA Compra")

    # Relacion con ventas
    sale_order_ids = fields.One2many('sale.order', 'service_id', 'Ventas')
    total_ventas = fields.Integer(compute='_get_total_ventas', store=False) 
    state_inv_s = fields.Boolean(compute="_state_fa_v", default=False, string="Estado FA Venta")

    # Documentacion requerida para el viaje correspondiente
    requirements_ids = fields.Many2many('requirement.document.service', string="Requisitos")

    # Relacion con Costos
    costos_ids = fields.One2many('costos.services', 'ref_services', ondelete="cascade")
    gastos_ids = fields.One2many('account.move', 'ref_gasto_service', context={'default_type': 'in_invoice', 'default_es_gasto': True})

    total_gastos = fields.Float(string="Total Gastos", compute="get_total_gastos")
    total_costos = fields.Float(string="Total Costos", compute="get_total_costos")

    total_adicional = fields.Float(string="Extra", default=0)

    residual = fields.Float(string="Resiual", compute="get_residual")

    state_invoice = fields.Boolean(string="Estado Facturación", default=False)

    gasto_sin_contabilizar = fields.One2many('gastonocont.service.service', 'ref_services', string="Gastos sin contabilizar", ondelete="cascade")
    total_gasto_sin_contabilizar = fields.Float(string="Tot Gasto S/Contabilizar", compute="get_total_gastos_no_contabilizado")


    @api.onchange('gasto_sin_contabilizar')
    def get_total_gastos_no_contabilizado(self):
        if len(self.gasto_sin_contabilizar) > 0:
            for obj in self.gasto_sin_contabilizar:
                self.total_gasto_sin_contabilizar += obj.total
        else:
            self.total_gasto_sin_contabilizar = 0

    @api.onchange('gastos_ids')
    def get_total_gastos(self):
        if len(self.gastos_ids) > 0:
            for obj in self.gastos_ids:
                self.total_gastos += obj.amount_total
        else:
            self.total_gastos = 0

    @api.onchange('costos_ids')
    def get_total_costos(self):
        if len(self.costos_ids) > 0:
            for obj in self.costos_ids:
                self.total_costos += obj.total
        else:
            self.total_costos = 0

    @api.depends('total_costos','total_gastos', 'total_ventas', 'total_purchases', 'total_adicional', 'total_gasto_sin_contabilizar')
    def get_residual(self):
        self.residual = self.total_ventas - (self.total_costos + self.total_gastos + self.total_adicional + self.total_purchases + self.total_gasto_sin_contabilizar)

    #Crear secuencia de los servicios.
    @api.model
    def create(self,vals):
        if vals.get('name', _('Nuevo')) == _('Nuevo'):
            vals['name'] = self.env['ir.sequence'].next_by_code('service.services') or _('Nuevo')
        res = super(services, self).create(vals)
        return res

    # Calculo odometro
    @api.depends('odo_end', 'odo_start')
    def _odo_total(self):
        for obj in self:
            obj.odo_total = obj.odo_end - obj.odo_start


    # Funcion que redirecciona a la orden de venta, llevando el id de este servicio en particular y añadiendolo a la orden de vente, asi tenemos una relacion entre ellos
    def act_show_sales(self, context=None):
        action = self.env.ref('sale.action_orders')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'context': {
                'default_partner_id': self.customer.id,
                'default_service_id': self.ids[0],
                'default_date_order': self.date_start,
                'default_validity_date': self.date_start
            }
        }
        result['domain'] = "[('id','in',[" + \
            ','.join(map(str, self.sale_order_ids.ids))+"])]"
        return result

    def _get_total_ventas(self):
        self.total_ventas = sum(order.amount_untaxed for order in self.sale_order_ids.filtered(lambda s: s.state in ('sale')))
        

    @api.depends('outsourced_service')
    def _get_total_purchases(self):
        if self.outsourced_service == True:
            self.total_purchases = sum(order.amount_untaxed for order in self.purchase_orders_ids.filtered(lambda s: s.state in ('purchase')))
        else: 
            self.total_purchases = 0


    def act_show_purchases(self):  
        action = self.env.ref('purchase.purchase_form_action')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
            'context': {
                'default_partner_id': self.provider.id,
                'default_service_id': self.ids[0],
                'default_date_order': self.date_start,
                'default_date_planned': self.date_start
            }
        }
        result['domain'] = "[('id','in',[" + \
            ','.join(map(str, self.purchase_orders_ids.ids))+"])]"
        return result

    #Funciones estados
    def status_confirmar(self):
        self.state = 'confirmado'

    def status_borrador(self):
        self.state = 'borrador'

    def status_realizar(self):
        self.state = 'realizado'
        
    def status_cancelar(self):
        self.state = 'cancelado'   


    #Estado de Facturación
    def _get_state_all_invoice(self):
        for obj in self:
            if obj.state_document == True and obj.state_inv_s == True and obj.state_inv_p == True:
                obj.state_invoice = True
            else:
                obj.state_invoice = False


    # Vemos si el servicio tiene remitos registrados, si es asi lo tomamos como un valor completo.
    @api.onchange('lst_documents')
    def _state_documents(self):
        for state_d in self:
            if len(state_d.lst_documents) >= 1:
                state_d.state_document = True
                if state_d.state_document == True and state_d.state_inv_s == True and state_d.state_inv_p == True:
                    state_d.state_invoice = True
                else:
                    state_d.state_invoice = False
            else:
                state_d.state_document = False

    # Estado de factura de compra
    def _state_fa_c(self):
        for fact_c in self:
            if fact_c.outsourced_service == True:
                fact_c.state_inv_p = False
                flag = False
                for obj in fact_c.purchase_orders_ids:
                    if obj.invoice_count == 0:
                        flag = True
                    else:
                        fact_c.state_inv_p = True
                        if fact_c.state_document == True and fact_c.state_inv_s == True and fact_c.state_inv_p == True:
                            fact_c.state_invoice = True
                        else:
                            fact_c.state_invoice = False         
                if flag == True:
                    fact_c.state_inv_p = False
            else: 
                fact_c.state_inv_p = True
                if fact_c.state_document == True and fact_c.state_inv_s == True and fact_c.state_inv_p == True:
                    fact_c.state_invoice = True
                else:
                    fact_c.state_invoice = False
                

    # Estado de factura de venta
    def _state_fa_v(self):
        for state_s in self:
            state_s.state_inv_s = False
            flag = False
            for obj in state_s.sale_order_ids:
                if obj.invoice_count == 0:
                    flag = True
                else:
                    state_s.state_inv_s = True
                    if state_s.state_document == True and state_s.state_inv_s == True and state_s.state_inv_p == True:
                        state_s.state_invoice = True
                    else:
                        state_s.state_invoice = False
            if flag == True:
                state_s.state_inv_s = False


class gastoEmployeeInService(models.Model):
    _inherit = 'account.move'

    ref_gasto_service = fields.Many2one('service.services', string='Gastos')


class DocumentsService(models.Model):
    _name = 'service.documents'

    name = fields.Char(string="N° Documento")

    ref_services = fields.Many2one('service.services', invisible=True)
    n_ref = fields.Char(compute="_get_n_ref", string="N° Referencia")
    url_document = fields.Char(string="URL")

    comentario = fields.Text(string="Comentario")

    def _get_n_ref(self):
        for obj in self:
            obj.n_ref = obj.ref_services.n_ref


class costosService(models.Model):
    _name = 'costos.services'

    name = fields.Many2one('sueldos.tarifas.employee.services', string="Viaticos")
    employee = fields.Many2one('employee.services', string="Empleado")

    qty = fields.Float(string="QTY")
    valor = fields.Float(string="Valor", compute="_get_montos")
    total = fields.Float(string="Total", compute="_get_montos")

    ref_services = fields.Many2one('service.services')

    def _get_montos(self):
        for obj in self:
            for rec in obj.name.lista_tarifas:
                if obj.ref_services.date_start >= rec.date_start and obj.ref_services.date_start <= rec.date_stop:
                    obj.valor = rec.tarifa
                
            obj.total = obj.qty * obj.valor

    class gastoSinContabilizarService(models.Model):

        _name = 'gastonocont.service.service'
        
        name = fields.Char(string="Descripción")

        qty = fields.Float(string="Cantidad")
        valor = fields.Float(string="Valor")
        total = fields.Float(string="Total", compute="_get_total")
    
        ref_services = fields.Many2one('service.services', invisible=True)

        @api.depends('valor', 'qty')
        def _get_total(self):
            for obj in self:
                obj.total = obj.qty * obj.valor        

