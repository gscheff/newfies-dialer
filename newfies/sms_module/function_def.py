#
# Newfies-Dialer License
# http://www.newfies-dialer.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2012 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.utils.translation import ugettext_lazy as _
from dialer_cdr.function_def import return_query_string
from dialer_contact.models import Phonebook, Contact
from common.common_functions import variable_value
from user_profile.models import UserProfile
from sms.models import Gateway
from models import SMSCampaign, SMSDialerSetting
from constants import SMS_CAMPAIGN_STATUS, SMS_CAMPAIGN_STATUS_COLOR
from datetime import datetime


def field_list(name, user=None):
    """Return List of SMSCampaign"""
    if name == "smscampaign" and user is not None:
        list = SMSCampaign.objects.filter(user=user)
    if name == "phonebook" and user is None:
        list = Phonebook.objects.all()
    if name == "phonebook" and user is not None:
        list = Phonebook.objects.filter(user=user)
    if name == "gateway" and user is not None:
        list = Gateway.objects.all()
    return ((l.id, l.name) for l in list)


def get_sms_campaign_status_name(id):
    """To get status name from SMS_CAMPAIGN_STATUS"""
    for i in SMS_CAMPAIGN_STATUS:
        if i[0] == id:
            #return i[1]
            if i[1] == 'START':
                return '<font color="%s">STARTED</font>' % SMS_CAMPAIGN_STATUS_COLOR[id]
            if i[1] == 'PAUSE':
                return '<font color="%s">PAUSED</font>' % SMS_CAMPAIGN_STATUS_COLOR[id]
            if i[1] == 'ABORT':
                return '<font color="%s">ABORTED</font>' % SMS_CAMPAIGN_STATUS_COLOR[id]
            if i[1] == 'END':
                return '<font color="%s">STOPPED</font>' % SMS_CAMPAIGN_STATUS_COLOR[id]


def check_sms_dialer_setting(request, check_for, field_value=''):
    """Check SMS Dialer Setting Limitation

    **Attribute**

        * ``check_for`` -  for sms campaign or for contact
    """
    try:
        user_obj = UserProfile.objects.get(
            user=request.user, dialersetting__isnull=False)
        # DialerSettings link to the User
        if user_obj:
            sms_dialer_set_obj = SMSDialerSetting.objects.get(
                dialer_setting=user_obj.dialersetting)
            if sms_dialer_set_obj:
                # check running campaign for User
                if check_for == "smscampaign":
                    smscampaign_count = SMSCampaign.objects.filter(
                        user=request.user).count()
                    # Total active sms campaign matched with
                    # sms_max_number_campaign
                    if smscampaign_count >= sms_dialer_set_obj.sms_max_number_campaign:
                        # Limit matched or exceeded
                        return True
                    else:
                        # Limit not matched
                        return False

                # check for subscriber per campaign
                if check_for == "contact":
                    # SMS Campaign list for User
                    smscampaign_list = SMSCampaign.objects.filter(user=request.user)
                    for i in smscampaign_list:
                        # Total contacts per campaign
                        contact_count = Contact.objects.filter(
                            phonebook__campaign=i.id).count()
                        # Total active contacts matched with
                        # sms_max_number_subscriber_campaign
                        if contact_count >= sms_dialer_set_obj.sms_max_number_subscriber_campaign:
                            # Limit matched or exceeded
                            return True
                        # Limit not matched
                    return False

                # check for frequency limit
                if check_for == "frequency":
                    if field_value > sms_dialer_set_obj.sms_max_frequency:
                        # Limit matched or exceeded
                        return True
                        # Limit not exceeded
                    return False

                # check for sms retry limit
                if check_for == "retry":
                    if field_value > sms_dialer_set_obj.sms_maxretry:
                        # Limit matched or exceeded
                        return True
                        # Limit not exceeded
                    return False
            else:
                # SMS DialerSettings not link to the DialerSettings
                return False
    except:
        # SMS DialerSettings not link to the User
        return False


def sms_dialer_setting_limit(request, limit_for):
    """Return SMS Dialer Setting's limit

    e.g. sms_max_number_subscriber_campaign
         sms_max_number_campaign
         sms_max_frequency
         sms_maxretry
    """
    user_obj = UserProfile.objects.get(
        user=request.user, dialersetting__isnull=False)
    # DialerSettings link to the User
    if user_obj:
        sms_dialer_set_obj = SMSDialerSetting.objects.get(
            dialer_setting=user_obj.dialersetting)

        if sms_dialer_set_obj:
            if limit_for == "contact":
                return str(sms_dialer_set_obj.sms_max_number_subscriber_campaign)
            if limit_for == "smscampaign":
                return str(sms_dialer_set_obj.sms_max_number_campaign)
            if limit_for == "frequency":
                return str(sms_dialer_set_obj.sms_max_frequency)
            if limit_for == "retry":
                return str(sms_dialer_set_obj.sms_maxretry)


def sms_attached_with_dialer_settings(request):
    """Check user is attached with dialer setting or not"""
    try:
        user_obj = UserProfile.objects.get(
            user=request.user, dialersetting__isnull=False)
        # DialerSettings link to the User
        if user_obj:
            sms_dialer_set_obj = SMSDialerSetting.objects.get(
                dialer_setting=user_obj.dialersetting)

            # SMS DialerSettings is exists
            if sms_dialer_set_obj:
                # attached with dialer setting
                return False
            else:
                # not attached
                return True
    except:
        # not attached
        return True


def sms_dialer_setting(user):
    """Get SMS Dialer setting for user"""
    try:
        user_profile = UserProfile.objects.get(user__username=user)
        sms_dialer_setting = SMSDialerSetting.objects.get(
            dialer_setting=user_profile.dialersetting)
    except:
        sms_dialer_setting = []
    return sms_dialer_setting


def sms_dialer_setting_msg(user):
    msg = ''
    if not sms_dialer_setting(user):
        msg = _('Your settings are not configured properly, \
                 Please contact the administrator.')
    return msg


def sms_record_common_fun(request):
    """Return Form with Initial data or Array (kwargs) for SMS_Report
    Changelist_view"""
    start_date = ''
    end_date = ''
    if request.POST.get('from_date'):
        from_date = request.POST.get('from_date')
        start_date = datetime(int(from_date[0:4]), int(from_date[5:7]),
            int(from_date[8:10]), 0, 0, 0, 0)
    if request.POST.get('to_date'):
        to_date = request.POST.get('to_date')
        end_date = datetime(int(to_date[0:4]), int(to_date[5:7]),
            int(to_date[8:10]), 23, 59, 59, 999999)

    # Assign form field value to local variable
    status = variable_value(request, 'status')
    smscampaign = variable_value(request, 'smscampaign')

    # Patch code for persist search
    if request.method != 'POST':

        if request.session.get('from_date'):
            from_date = request.session['from_date']
            start_date = datetime(
                int(from_date[0:4]), int(from_date[5:7]), int(from_date[8:10]), 0, 0, 0, 0)

        if request.session.get('to_date'):
            to_date = request.session['to_date']
            end_date = datetime(
                int(to_date[0:4]), int(to_date[5:7]), int(to_date[8:10]), 23, 59, 59, 999999)

        if request.session.get('status'):
            status = request.session['status']

        if request.session.get('smscampaign'):
            smscampaign = request.session['smscampaign']

    kwargs = {}
    if start_date and end_date:
        kwargs['send_date__range'] = (start_date, end_date)
    if start_date and end_date == '':
        kwargs['send_date__gte'] = start_date
    if start_date == '' and end_date:
        kwargs['send_date__lte'] = end_date

    if status:
        if status != 'all':
            kwargs['status__exact'] = status

    if smscampaign and smscampaign != '0':
        kwargs['sms_campaign'] = smscampaign

    if len(kwargs) == 0:
        tday = datetime.today()
        kwargs['send_date__gte'] = datetime(tday.year,
                                            tday.month,
                                            tday.day, 0, 0, 0, 0)
    return kwargs


def sms_search_admin_form_fun(request):
    """Return query string for SMSMessage Changelist_view"""
    start_date = ''
    end_date = ''
    smscampaign = ''
    if request.POST.get('from_date'):
        start_date = request.POST.get('from_date')

    if request.POST.get('to_date'):
        end_date = request.POST.get('to_date')

    # Assign form field value to local variable
    status = variable_value(request, 'status')
    smscampaign = variable_value(request, 'smscampaign')
    query_string = ''

    if start_date and end_date:
        date_string = 'send_date__gte=' + start_date + '&send_date__lte=' \
            + end_date + '+23%3A59%3A59'
        query_string = return_query_string(query_string, date_string)

    if start_date and end_date == '':
        date_string = 'send_date__gte=' + start_date
        query_string = return_query_string(query_string, date_string)

    if start_date == '' and end_date:
        date_string = 'send_date__lte=' + end_date
        query_string = return_query_string(query_string, date_string)

    if status:
        if status != 'all':
            status_string = 'status__exact=' + status
            query_string = return_query_string(query_string, status_string)

    if smscampaign and smscampaign != '0':
        smscampaign_string = 'sms_campaign=' + smscampaign
        query_string = return_query_string(query_string, smscampaign_string)

    return query_string
