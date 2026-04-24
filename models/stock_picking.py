# -*- coding: utf-8 -*-

from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        self._stamp_revival_analytic_on_so()
        return res

    def _stamp_revival_analytic_on_so(self):
        """After delivery, stamp analytic on SO line from lot → acquired → analytic_account.

        Flow: move_line.lot_id → lot.itx_acquired_id → acquired.analytic_account_id
              → stamp on sale.order.line.analytic_distribution
        """
        for picking in self:
            if picking.picking_type_code != 'outgoing':
                continue
            for ml in picking.move_line_ids:
                lot = ml.lot_id
                if not lot or not lot.itx_acquired_id:
                    continue
                analytic = lot.itx_acquired_id.analytic_account_id
                if not analytic:
                    continue

                # Find SO line linked to this move
                so_line = ml.move_id.sale_line_id
                if so_line and not so_line.analytic_distribution:
                    so_line.analytic_distribution = {str(analytic.id): 100}
