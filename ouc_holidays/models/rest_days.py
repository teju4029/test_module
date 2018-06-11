from odoo import api, fields, models, _
from openerp.osv import osv

from odoo.exceptions import UserError, AccessError, ValidationError
from odoo import exceptions
from odoo.exceptions import ValidationError




class hr_rest_days(models.Model):
    _name = 'hr.non_working.days'
    _rec_name = 'non_working'

    non_working = fields.Char(string='Non-Working Days')

    is_friday = fields.Boolean(string='Is Friday')
    is_saturday = fields.Boolean(string='Is Saturday')
    is_sunday = fields.Boolean(string='Is Sunday')
    is_alternate_saturday = fields.Boolean(string='Is Alternate Saturday')

    @api.model
    def create(self, vals):
        rec = super(hr_rest_days, self).create(vals)
        if rec.non_working:
            print ">>>>>>>rec.c_rest_day_type>>>>>>",rec.non_working
            days = rec.non_working.split(',')
            if len(days) > 2:
                raise exceptions.ValidationError(_('Non working days contain 2 days only'))
        return rec

    @api.multi
    def write(self, values):
        rec = super(hr_rest_days, self).write(values)
        if values.get('non_working'):
            days = values.get('non_working').split(',')
            if len(days) > 2:
                raise exceptions.ValidationError(_('Non working days contain 2 days only'))
        return rec


    @api.onchange('is_friday','is_saturday','is_sunday','is_alternate_saturday')
    def auto_filling_rest_days(self):
        list = []
        if self.is_friday == True:
            list.append("Friday")
        if self.is_saturday == True:
            list.append("Saturday")
        if self.is_sunday == True:
            list.append("Sunday")
        if self.is_alternate_saturday == True:
            list.append("Alternate Saturday")
        print " ".join(list)
        self.non_working = list



class hr_department(models.Model):
    _inherit = 'hr.department'

    non_working = fields.Many2one('hr.non_working.days',string='Non-Working Days')

class hr_holidays_status(models.Model):
    _inherit = 'hr.holidays.status'

    include_rest_days = fields.Boolean(string='Include Rest Days')
    include_pub_holidays = fields.Boolean(string='Include Public Holidays')


