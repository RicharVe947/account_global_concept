from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_global_concept = fields.Boolean(string="is global concept?", store=True, )