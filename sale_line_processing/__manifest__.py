{
    'name': 'Sale Line Toggle Processed',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Add checkbox to hide processed sale order lines',
    'depends': ['sale_management'],
    'data': [
        'views/sale_order_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_line_processing/static/src/js/toggle_processed.js',
            'sale_line_processing/static/src/css/toggle_processed.css',
        ],
    },
    'installable': True,
    'application': False,
}
