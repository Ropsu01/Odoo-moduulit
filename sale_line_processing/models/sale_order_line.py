from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    processed = fields.Boolean(string="Käsitelty", default=False)
