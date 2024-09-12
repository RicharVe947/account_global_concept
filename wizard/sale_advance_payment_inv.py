# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    is_invoice_global_concept = fields.Boolean()
    advance_payment_method = fields.Selection(selection_add=[
        ('global_concept', 'Facturación Concepto Global')
    ], ondelete={'global_concept': 'set delivered'})

    def create_invoices(self):
        if not self.advance_payment_method == 'global_concept':
            return super().create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.is_invoice_global_concept:
            order_lines = self.env['sale.order.line'].browse(self._context.get('sale_order_line_ids', []))
        else:
            order_lines = sale_orders.order_line
        order_lines = order_lines.filtered(lambda x: x.qty_to_invoice)
        # Create global product if necessary
        self.product_id = self.env.ref("account_global_concept.product_global_concept", None)
        amount, name = self._get_advance_details_global_concept(sale_orders)
        self._create_invoice_global_concept(sale_orders, order_lines, amount, name)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    def _create_invoice_global_concept(self, sale_orders, order_lines, amount, name):
        invoice_vals = self._prepare_invoice_values_global_concept(sale_orders, name, amount, order_lines)
        if sale_orders.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = sale_orders.fiscal_position_id.id
        for line in order_lines:
            line.quantity_invoiced_global = line.qty_to_invoice
        invoice = self.env['account.move'].with_company(sale_orders.company_id)\
            .sudo().create(invoice_vals).with_user(self.env.uid)
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': invoice.line_ids.mapped('sale_line_ids.order_id')},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    def _prepare_invoice_values_global_concept(self, sale_orders, name, amount, order_lines):
        #payment_refs = sale_orders.mapped("payment_reference")
        note = sale_orders.filtered(lambda x: x.note).mapped("note")
        invoice_vals = {
            'is_global_concept': True,
            'ref': ', '.join(sale_orders.filtered(lambda x: x.client_order_ref).mapped("client_order_ref"))[:2000],
            'move_type': 'out_invoice',
            'invoice_origin': ', '.join(sale_orders.mapped("name")),
            'invoice_user_id': self.env.user.id,
            'narration': ', '.join(note)[:2000] if note else None,
            'partner_id': None if len(sale_orders.partner_invoice_id ) > 1 else sale_orders.partner_invoice_id.id,
            #'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(order.partner_id.id)).id,
            #'partner_shipping_id': sale_orders.partner_invoice_id.id,
            'currency_id': sale_orders.pricelist_id.currency_id.id,
            #'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            # 'invoice_payment_term_id': sale_orders.payment_term_id.id or None,
            # 'partner_bank_id': sale_orders.company_id.partner_id.bank_ids[:1].id,
            'team_id': sale_orders[0].team_id.id or None,
            'campaign_id': sale_orders[0].campaign_id.id or None,
            'medium_id': sale_orders[0].medium_id.id or None,
            'source_id': sale_orders[0].source_id.id or None,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': None,
                'tax_ids': [(6, 0, order_lines.tax_id.ids)],
                'sale_line_ids': [(6, 0, order_lines.ids)],
                'analytic_tag_ids': [(6, 0, order_lines.analytic_tag_ids.ids)],
                # 'analytic_account_id': order.analytic_account_id.id if not so_line.display_type and order.analytic_account_id.id else False,
            })],
        }

        return invoice_vals

    def _get_advance_details_global_concept(self, order_ids):
        # context = {'lang': order_ids.partner_id.lang}
        name = _('Conepto Factura Global')
        if self.is_invoice_global_concept:
            order_lines = self.env['sale.order.line'].browse(
                self._context.get('sale_order_line_ids', [])).filtered(lambda x: x.qty_to_invoice)
            amount = sum(order_lines.mapped("price_subtotal"))
            # del context
            return amount, name
        amount = sum(order_ids.order_line.filtered(lambda x: x.qty_to_invoice).mapped("price_subtotal"))
        # del context
        return amount, name

    def create_invoice_global_concept(self):
        res = self.create_invoices()
        return res
