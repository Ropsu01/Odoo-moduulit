from odoo import fields, models, api
import re

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    room_number = fields.Char(
        string="Huonenumero",
        help="Mihin huoneisiin tämä rivi kuuluu. "
             "Voit antaa listan pilkulla erotettuna (esim. A1,A2,A3) "
             "tai alueen (esim. A1-A30)."
    )

    qty_per_room = fields.Float(
        string="Määrä / huone",
        help="Kuinka monta kappaletta per huone tarvitaan."
    )

    rooms_count = fields.Integer(
        string="Huoneiden lukumäärä",
        compute="_compute_rooms_count",
        store=True
    )

    @api.depends("room_number")
    def _compute_rooms_count(self):
        range_regex = re.compile(r"^([A-Za-z]*)(\d+)-([A-Za-z]*)(\d+)$")
        for line in self:
            total = 0
            if line.room_number:
                parts = [r.strip() for r in line.room_number.split(",") if r.strip()]
                for part in parts:
                    match = range_regex.match(part)
                    if match:
                        prefix1, start, prefix2, end = match.groups()
                        # Jos prefixit eroavat (A1-B5), lasketaan vain numerot
                        if prefix1 == prefix2:
                            total += int(end) - int(start) + 1
                        else:
                            total += 1  # outo tapaus: eri prefix
                    else:
                        total += 1
            line.rooms_count = total

    @api.onchange("qty_per_room", "rooms_count")
    def _onchange_qty_total(self):
        """Laske kokonaismäärä automaattisesti."""
        for line in self:
            if line.qty_per_room and line.rooms_count:
                line.product_uom_qty = line.qty_per_room * line.rooms_count
            else:
                line.product_uom_qty = 0
