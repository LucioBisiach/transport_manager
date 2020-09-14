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
    state_document = fields.Boolean(default=False, string="Estado de Documentos", invisible=True, store=True)

    # Relacion con compras
    purchase_orders_ids = fields.One2many('purchase.order', 'service_id', string="Compras")
    total_purchases = fields.Integer(compute='_get_total_purchases', store=False)
    state_inv_p = fields.Boolean(compute="_state_fa_c", string="Estado FA Compra", store=True)

    # Relacion con ventas
    sale_order_ids = fields.One2many('sale.order', 'service_id', 'Ventas')
    total_ventas = fields.Integer(compute='_get_total_ventas', store=False) 
    state_inv_s = fields.Boolean(compute="_state_fa_v", default=False, string="Estado FA Venta", store=True)

    # Documentacion requerida para el viaje correspondiente
    requirements_ids = fields.Many2many('requirement.document.service', string="Requisitos")

    # Relacion con Costos
    costos_ids = fields.One2many('costos.services', 'ref_services', ondelete="cascade")
    gastos_ids = fields.One2many('account.move', 'ref_gasto_service', context={'default_type': 'in_invoice', 'default_es_gasto': True})

    total_costos = fields.Float(string="Total Costos", compute="get_total_costos")

    @api.onchange('costos_ids')
    def get_total_costos(self):
        for obj in self.costos_ids:
            self.total_costos += obj.total

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

    # Vemos si el servicio tiene remitos registrados, si es asi lo tomamos como un valor completo.
    @api.onchange('lst_documents')
    def _state_documents(self):
        for state_d in self:
            if len(state_d.lst_documents) >= 1:
                state_d.state_document = True
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
                if flag == True:
                    fact_c.state_inv_p = False
            else: 
                fact_c.state_inv_p = True

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
    

        

