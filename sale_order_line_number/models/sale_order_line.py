from odoo import api, fields, models


STEP = 10  # väljä sequence-askel, helpottaa manuaalista siirtelyä


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    line_number = fields.Integer(
        string="Rivi",
        help="Rivin järjestysnumero myyntitilauksessa.",
        copy=False,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if self.env.context.get("_bypass_line_number"):
            return records

        changed_ids = []
        for rec, vals in zip(records, vals_list):
            if vals.get("line_number"):
                changed_ids.append(rec.id)

        for order in records.mapped("order_id"):
            order.with_context(_ln_changed_ids=changed_ids)._resequence_lines()
        return records

    def write(self, vals):
        old_orders = self.mapped("order_id")
        changed_ids = list(self.ids) if "line_number" in vals else []

        res = super().write(vals)
        if self.env.context.get("_bypass_line_number"):
            return res

        orders = (old_orders | self.mapped("order_id"))
        if orders:
            orders.with_context(_ln_changed_ids=changed_ids)._resequence_lines()
        return res

    def unlink(self):
        orders = self.mapped("order_id")
        res = super().unlink()
        if orders:
            orders._resequence_lines()
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _resequence_lines(self):
        """
        Tavoite:
          - Käyttäjän antama line_number siirtää rivin siihen kohtaan.
          - Jos numero on varattu, muut siirtyvät eteenpäin.
          - Lopputulos: normaalit rivit (display_type False) numeroidaan 1..n.
          - Section/note-rivien paikka säilyy (ei numeroida).
          - UI:n järjestys = `sequence`, joten päivitetään myös `sequence`.
        """
        for order in self:
            all_lines = order.order_line.sorted(lambda l: (l.sequence, l.id))
            if not all_lines:
                continue

            changed_ids = set(self.env.context.get("_ln_changed_ids") or [])

            # Jaa rivit: normaalit (numeroitavat) ja erityisrivit (section/note)
            normal_lines = [l for l in all_lines if not l.display_type]
            special_mask = [bool(l.display_type) for l in all_lines]  # True jos special

            # 1) Laske haluttu paikka normaaliriveille käyttäjän syötön mukaan
            #    - priorisoi juuri muokatut rivit, jotta ne saavat "halutun" numeron
            #    - muut täyttävät vapaat paikat
            #    - numerointi vain 1..N (N = len(normal_lines))
            # Kerätään ehdotukset muodossa (wanted_pos, priority, orig_order, line)
            proposals = []
            for idx, line in enumerate(normal_lines):
                wanted = max(1, int(line.line_number or 999999))
                priority = 0 if line.id in changed_ids else 1
                proposals.append((wanted, priority, idx, line))

            # Käsittele ensin pienin wanted, sitten prioriteetti, sitten vakaa järjestys
            proposals.sort(key=lambda t: (t[0], t[1], t[2]))

            # Täytetään paikat 1..N siirtäen varauksia eteenpäin
            N = len(normal_lines)
            taken = [None] * (N + 1)  # 1-pohjainen
            for wanted, _prio, _idx, line in proposals:
                pos = wanted if wanted <= N else N  # clamp
                while pos <= N and taken[pos] is not None:
                    pos += 1
                # jos mentiin yli, etsitään taaksepäin eka vapaa (harvinainen, mut varma)
                if pos > N:
                    pos = 1
                    while pos <= N and taken[pos] is not None:
                        pos += 1
                taken[pos] = line

            # Rakennetaan uusi järjestys normaaliriveille pos 1..N
            new_normals_in_order = [taken[i] for i in range(1, N + 1)]

            # 2) Sijoita uudet normaalirivit takaisin ALL-runkolistaan
            #    - säilytä special-rivien paikat (missä ne olivat)
            it_norm = iter(new_normals_in_order)
            final_order = []
            for is_special, old_line in zip(special_mask, all_lines):
                if is_special:
                    final_order.append(old_line)         # pidä paikoillaan
                else:
                    final_order.append(next(it_norm))     # korvaa seuraavalla normaalilla

            # 3) Kirjoita `sequence` ja `line_number`
            seq = STEP
            running_num = 1
            for line in final_order:
                vals = {"sequence": seq}
                if line.display_type:
                    # ei numeroida section/note-rivejä
                    pass
                else:
                    vals["line_number"] = running_num
                    running_num += 1

                if line.sequence != seq or (not line.display_type and line.line_number != vals["line_number"]):
                    line.with_context(_bypass_line_number=True).write(vals)

                seq += STEP
