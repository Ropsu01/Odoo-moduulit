from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_measurements = fields.Char(string="Mittatiedot", compute="_compute_measurements", store=False)

    def _compute_measurements(self):
        for product in self:
            # Haetaan mittatiedot product_dimension -moduulista
            length = product.product_length or 0
            width = product.product_width or 0
            height = product.product_height or 0
            unit = product.dimensional_uom_id.name if product.dimensional_uom_id else ""
            
            # Muodostetaan näyttöarvo
            if any([length, width, height]):
                product.x_measurements = f"{length} x {width} x {height} {unit}".strip()
            else:
                product.x_measurements = "Ei mittatietoja"
