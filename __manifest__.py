{

    'name': 'Transport Manager',
    'version': '11.0',
    'category': 'Tools',
    'summary': 'transport manager',
    'sequence': '10',
    'author': 'Bisiach Lucio',
    'maintainer': 'Bisiach Lucio',
    'website': 'N/A',
    'depends': ['sale_management', 'purchase', 'base', 'account_payment', 'fleet', 'om_account_accountant', 'stock', 'board'],
    'demo': [],
    'data': [

        #Data
        'data/ir_sequence_data.xml',
        'data/data_requisitos.xml',

        #Security
        'security/ir.model.access.csv',
    
        #Dashboard
        'views/dashboard.xml',
        
        # Services
        'views/service/service.xml',

        #Config
        'views/config/config_general.xml',

        #Menues
        'views/config/config_menu.xml',

        #Empleados
        'views/employee/employee.xml',

        #Flota
        'views/fleet/fleet.xml',

        #Inherit
        'views/inherit_sale.xml',
        'views/inherit_purchase.xml',
        'views/inherit_purchase_invoice.xml',


    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',


}
