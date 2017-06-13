# -*- coding: utf-8 -*-
from openerp import models, fields


class OVHLog(models.Model):
    _name = 'ovh.log'
    _order = 'date_log'

    name = fields.Char(string="Name")
    date_log = fields.Datetime(string="Date")
    log_type = fields.Selection(
        [('warning', 'Warning'), ('error', 'Error')], string="Type", index=True)
    message = fields.Text(string="Message")
