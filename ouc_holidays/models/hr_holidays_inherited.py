import datetime
from datetime import date
import dateutil.parser
from dateutil.parser import parse
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
import calendar


from openerp import tools
from odoo import api, fields, models, _
from openerp.osv import osv
import openerp.addons.decimal_precision as dp

from openerp.tools.safe_eval import safe_eval as eval
from odoo import exceptions
from odoo.exceptions import UserError, AccessError, ValidationError
from collections import defaultdict

HOURS_PER_DAY = 8
alternate_sat_num = (1, 2, 3, 4, 5, 6, 7, 8, 9)
WITHOUT_SAT_SUN = (0,1,2,3,4)
WITHOUT_SAT_FRI = (0, 1, 2, 3, 6)
WITHOUT_FRI_SUN = (0, 1, 2, 3, 5)
WITHOUT_SUN = (0, 1, 2, 3, 4, 5)
WITHOUT_FRI = (0, 1, 2, 3, 5, 6)
WITHOUT_SAT = (0, 1, 2, 3, 4, 6)
FULL_DAYS = (0, 1, 2, 3, 4, 5, 6)



class Holidays(models.Model):
    _inherit = "hr.holidays"

    @api.onchange('holiday_status_id','employee_id')
    def reseting_rest_days(self):

        employee_id = self.env['hr.employee'].search([('id','=',self.employee_id.id)])
        list = []
        if employee_id:
            for division in self.env['hr.employee'].browse(employee_id.id):
                obj = division.department_id.non_working
                if self.employee_id and self.holiday_status_id and division.department_id:
                    if obj:
                        if obj.is_friday == True:
                            list.append(4)
                        if obj.is_saturday == True:
                            list.append(5)
                        if obj.is_sunday == True:
                            list.append(6)


                        if self.holiday_status_id.include_rest_days == True and self.holiday_status_id.include_pub_holidays == True:
                            self.number_of_days_temp = self.get_totalNumberOfDays()


                        else:
                            if len(list) == 2 and obj.is_saturday == True and obj.is_sunday == True:
                                self.nonWorkingDays_sat_sun()
                            elif len(list) == 2 and obj.is_saturday == True and obj.is_friday == True:
                                self.nonWorkingDays_sat_fri()
                            elif len(list) == 2 and obj.is_friday == True and obj.is_sunday == True:
                                self.nonWorkingDays_fri_sun()
                            elif len(list) ==1 and obj.is_sunday == True and obj.is_alternate_saturday == False:
                                self.nonWorkingDay_sun()
                            elif len(list) == 1 and obj.is_friday == True:
                                self.nonWorkingDay_friday()
                            elif len(list) == 1 and obj.is_saturday == True:
                                self.nonWorkingDay_saturday()
                            elif obj.is_alternate_saturday == True and obj.is_sunday == True:
                                self.nonWorkingDays_alternate_sat_sun()
                            else:
                                if obj.is_friday == False and obj.is_saturday == False and obj.is_sunday == False:
                                    self.number_of_days_temp = self.checking_public_holidays()
                    else:
                        raise exceptions.ValidationError(_('Rest day Type is not mentioned in Department'))

                else:
                    self.number_of_days_temp = self.get_totalNumberOfDays()
                    if not division.department_id:
                        raise exceptions.ValidationError(_('Employee has not mention Department, Please Mentioned Department'))

    def nonWorkingDays_alternate_sat_sun(self):
        today_date = str(datetime.now().date())
        year = today_date.split('-')[0]
        list_of_sat = []
        c = calendar.TextCalendar(calendar.SUNDAY)
        for m in range(1, 13):
            for d in c.itermonthdays(int(year), m):
                if d != 0:
                    day = date(int(year), m, d)
                    if day.weekday() == 5 :  # if its saturday
                        if m in alternate_sat_num:
                            sat = str(year)+'-0'+str(m)+'-'+str(d)
                            if d in alternate_sat_num:
                                sat = str(year) + '-0' + str(m) + '-0' + str(d)
                            else:
                                sat = str(year) + '-0' + str(m) + '-' + str(d)
                        else:
                            sat = str(year) + '-' + str(m) + '-' + str(d)
                            if d in alternate_sat_num:
                                sat = str(year) + '-' + str(m) + '-0' + str(d)
                            else:
                                sat = str(year) + '-' + str(m) + '-' + str(d)
                        q = (m,sat)
                        list_of_sat.append(q)

        dictonary = defaultdict(list)
        for month, te in list_of_sat:
            dictonary[month].append(te)

        even_list = []
        for k in range(1,len(dictonary.keys())+1):
            rr = dictonary[k]
            for j in range(0,4):
                if j%2 != 0:
                    r = (k,rr[j])
                    even_list.append(r)

        odd_dictonary = defaultdict(list)
        for mon, da in even_list:
            odd_dictonary[mon].append(da)

        dates = []
        dates = self.geting_public_holidays()
        rest_days = 0
        public_days = 0
        alt_sat = 0
        only_alt_sat = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')

            for i in xrange(int((to_date - from_date).days) + 1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in dates and nextDate.weekday() in WITHOUT_SUN:
                    public_days = public_days + 1
                month = split_date.split('-')[1]
                for a in range(1,len(odd_dictonary.keys())+1):
                    if str(a) == month[1]:
                        bb = odd_dictonary[a]
                        for b in bb:
                            if b == split_date and b not in dates:
                                alt_sat += 1
                            if b == split_date :
                                only_alt_sat += 1
                if nextDate.weekday() in WITHOUT_SUN:
                    rest_days += 1
            if self.holiday_status_id.include_pub_holidays == True:
                total_leave_days = rest_days - only_alt_sat
            elif self.holiday_status_id.include_rest_days == True:
                total_leave_days = self.checking_public_holidays()
            else:
                total_leave_days = rest_days - alt_sat - public_days
            self.number_of_days_temp = total_leave_days


    def nonWorkingDays_sat_sun(self):
                                                    # for sunday and saturday holiday
        dates = []
        dates = self.geting_public_holidays()
        rest_days = 0
        public_days = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')

            for i in xrange(int((to_date - from_date).days)+1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in dates and nextDate.weekday() in WITHOUT_SAT_SUN:
                    public_days = public_days + 1

                if nextDate.weekday() in WITHOUT_SAT_SUN:
                    rest_days += 1
        self.in_rest_public_days(rest_days,public_days)


    def nonWorkingDays_sat_fri(self):
        dates = []
        dates = self.geting_public_holidays()

        rest_days = 0
        public_days = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')

            for i in xrange(int((to_date - from_date).days) + 1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in dates and nextDate.weekday() in WITHOUT_SAT_FRI:
                    public_days = public_days + 1
                # developer person for saturday and sunday holiday
                if nextDate.weekday() in WITHOUT_SAT_FRI:
                    rest_days += 1
        self.in_rest_public_days(rest_days,public_days)


    def nonWorkingDays_fri_sun(self):
        dates = []
        dates = self.geting_public_holidays()

        rest_days = 0
        public_days = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')

            for i in xrange(int((to_date - from_date).days) + 1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in dates and nextDate.weekday() in WITHOUT_FRI_SUN:
                    public_days = public_days + 1
                # developer person for saturday and sunday holiday
                if nextDate.weekday() in WITHOUT_FRI_SUN:
                    rest_days += 1
        self.in_rest_public_days(rest_days,public_days)


    def nonWorkingDay_sun(self):
        dates = []
        dates = self.geting_public_holidays()

        rest_days = 0
        public_days = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')

            for i in xrange(int((to_date - from_date).days) + 1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in dates and nextDate.weekday() in WITHOUT_SUN:
                    public_days = public_days + 1
                # developer person for saturday and sunday holiday
                if nextDate.weekday() in WITHOUT_SUN:
                    rest_days += 1
        self.in_rest_public_days(rest_days,public_days)


    def nonWorkingDay_friday(self):
        dates = []
        dates = self.geting_public_holidays()

        rest_days = 0
        public_days = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')

            for i in xrange(int((to_date - from_date).days) + 1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in dates and nextDate.weekday() in WITHOUT_FRI:
                    public_days = public_days + 1
                # developer person for saturday and sunday holiday
                if nextDate.weekday() in WITHOUT_FRI:
                    rest_days += 1
        self.in_rest_public_days(rest_days,public_days)


    def nonWorkingDay_saturday(self):
        dates = []
        dates = self.geting_public_holidays()

        rest_days = 0
        public_days = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')
            for i in xrange(int((to_date - from_date).days) + 1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in dates and nextDate.weekday() in WITHOUT_SAT:
                    public_days = public_days + 1
                # developer person for saturday and sunday holiday
                if nextDate.weekday() in WITHOUT_SAT:
                    rest_days += 1
        self.in_rest_public_days(rest_days,public_days)

    def geting_public_holidays(self):
        today_date = str(datetime.now().date())
        year = today_date.split('-')[0]
        pub_holi = self.env['hr.holidays.public'].search([('year','=',year)])
        dates = []
        dict = []
        state = self.employee_id.address_id.state_id
        if not state:
            raise exceptions.ValidationError(_('State of the employee is not mentioned'))
        if pub_holi:
            for val in self.env['hr.holidays.public'].browse(pub_holi.id):
                for record in val.line_ids:
                    dates.append(record.date)
                    list = []
                    if record.state_ids:
                        for t in record.state_ids:
                            if state == t:
                                dict.append(record.date)
                    else:
                        dict.append(record.date)
        return dict


    def get_totalNumberOfDays(self):
        diff = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')
            diff = int((to_date - from_date).days) + 1
        return diff


    def in_rest_public_days(self,rest_days,public_days):
        print ">>>>>>>rest days>>>>>", rest_days
        print ">>>>>>>public days>>>>>", public_days

        if self.holiday_status_id.include_pub_holidays == True:
            total_leave_days = rest_days
        elif self.holiday_status_id.include_rest_days == True:
            total_leave_days = self.checking_public_holidays()
        else:
            total_leave_days = rest_days - public_days
        self.number_of_days_temp = total_leave_days

    def checking_public_holidays(self):
        original_days = self.get_totalNumberOfDays()
        pub_days = self.geting_public_holidays()
        from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
        to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')
        public_days = 0
        if self.date_from and self.date_to:
            from_date = datetime.strptime(self.date_from, '%Y-%m-%d %H:%M:%S')
            to_date = datetime.strptime(self.date_to, '%Y-%m-%d %H:%M:%S')
            for i in xrange(int((to_date - from_date).days) + 1):
                nextDate = from_date + timedelta(i)
                next = str(nextDate)
                split_date = next.split()[0]
                if split_date in pub_days and nextDate.weekday() in FULL_DAYS:
                    public_days = public_days + 1
        total_leave_days = original_days - public_days
        return total_leave_days


