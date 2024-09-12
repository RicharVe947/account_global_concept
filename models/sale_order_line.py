from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    quantity_invoiced_global = fields.Float(string='Quantity', default=0, digits='Product Unit of Measure', copy=False, )
    is_global_concept = fields.Boolean(string="is global concept?", compute="_compute_is_global_concept", store=True, )

    @api.depends("invoice_lines")
    def _compute_is_global_concept(self):
        for line in self:
            line.is_global_concept = False
            move_ids = line.invoice_lines.mapped("move_id")
            for move_id in move_ids:
                if move_id.is_global_concept:
                    line.is_global_concept = True
                    break

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'untaxed_amount_to_invoice', 'quantity_invoiced_global')
    def _compute_qty_invoiced(self):
        res = super()._compute_qty_invoiced()
        for line in self:
            if not line.is_global_concept:
                continue
            qty_invoiced = 0.0
            for invoice_line in line._get_invoice_lines():
                if invoice_line.move_id.state != 'cancel' or invoice_line.move_id.payment_state == 'invoicing_legacy':
                    if invoice_line.move_id.move_type == 'out_invoice':
                        qty_invoiced += invoice_line.product_uom_id._compute_quantity(line.quantity_invoiced_global,
                                                                                      line.product_uom)
                    elif invoice_line.move_id.move_type == 'out_refund':
                        qty_invoiced -= invoice_line.product_uom_id._compute_quantity(line.quantity_invoiced_global,
                                                                                      line.product_uom)
            line.qty_invoiced = qty_invoiced
        return res

    def _open_wizard_create_account_global(self):
        sale_order_line_ids = self.env['sale.order.line'].browse(self._context.get('active_ids', []))
        order_ids = sale_order_line_ids.mapped("order_id")
        not_to_invoice = order_ids.filtered(lambda x: x.invoice_status != "to invoice")
        if not_to_invoice:
            raise ValidationError(_("The selected Sales Order should contain something to invoice."))
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_view_sale_advance_payment_inv")
        action['context'] = {
            'active_ids': order_ids.ids,
            'default_is_invoice_global_concept': True,
            'default_advance_payment_method': "global_concept",
            'sale_order_line_ids': sale_order_line_ids.ids,
        }
        return action
