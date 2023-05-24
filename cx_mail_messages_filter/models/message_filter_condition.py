###################################################################################
# 
#    Copyright (C) Cetmix OÜ
#
#   Odoo Proprietary License v1.0
# 
#   This software and associated files (the "Software") may only be used (executed,
#   modified, executed after modifications) if you have purchased a valid license
#   from the authors, typically via Odoo Apps, or if you have received a written
#   agreement from the authors of the Software (see the COPYRIGHT file).
# 
#   You may develop Odoo modules that use the Software as a library (typically
#   by depending on it, importing it and using its resources), but without copying
#   any source code or material from the Software. You may distribute those
#   modules under the license of your choice, provided that this license is
#   compatible with the terms of the Odoo Proprietary License (For example:
#   LGPL, MIT, or proprietary licenses similar to this one).
# 
#   It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#   or modified copies of the Software.
# 
#   The above copyright notice and this permission notice must be included in all
#   copies or substantial portions of the Software.
# 
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
###################################################################################

from odoo import _, api, fields, models
from odoo.tools import getaddresses
from odoo.tools.mail import email_split

from .states import (
    CONDITION,
    CONDITION_STATE_CONTAINS,
    CONDITION_STATE_EQ,
    FILTER_CONDITION,
)


class CxMessageFilterCondition(models.Model):
    _name = "cx.message.filter.condition"
    _description = "Message filter conditions"

    name = fields.Char(string="Condition name", compute="_compute_condition_name")
    rule_id = fields.Many2one(
        "cx.message.filter.rule", string="Filter", ondelete="cascade"
    )
    trigger = fields.Selection(
        FILTER_CONDITION,
        required=True,
    )
    partner_ids = fields.Many2many("res.partner", string="Partners")
    value = fields.Char(string="Search text (optional)")
    condition = fields.Selection(
        [
            ("is", "is"),
            ("not", "not"),
            ("like", "contains"),
            ("not_like", "doesn't contain"),
        ],
        required=True,
        default="like",
    )

    @api.model
    def _check_valid_condition(self, vals=None):
        """
        Check the input data for the correctness
        of the condition
        :param vals: input data dict (optional)
        :return: None
        :raise model.UserError
        """
        vals = vals or dict()
        trigger = vals.get("trigger", False) or self.trigger
        condition = vals.get("condition", False) or self.condition
        if not (trigger and condition):
            return
        valid_trigger = trigger in ["author", "recipients"]
        valid_condition = condition in ["is", "not"]
        if valid_trigger and valid_condition:
            raise models.UserError(_("This action cannot be applied to this field!"))

    @api.onchange("trigger", "condition")
    def _onchange_condition(self):
        """
        Check the input data for the correctness
        of the condition at onchange event
        """
        self._check_valid_condition()

    def _get_trigger_by_condition(self):
        for key, value in FILTER_CONDITION:
            if key == self.trigger:
                return value
        return ""

    def _prepare_condition_name(self):
        """Prepare condition name"""
        trigger = self._get_trigger_by_condition()
        condition = CONDITION.get(self.condition)
        contains = (
            "'%s'" % self.value
            if self.value
            else " or ".join([partner.name for partner in self.partner_ids])
        )
        return "{} {} {}".format(trigger, condition, contains)

    def _compute_condition_name(self):
        """Compute name for condition"""
        for rec in self:
            rec.name = rec._prepare_condition_name()

    def condition_recipients(self, recipient_emails):
        """Contains email in partner filter

        :param str recipient_emails: from mail incoming recipient email
        :return bool contains/doesn't contain by conditions
        """
        state = False
        if not recipient_emails:
            return False
        for recipient_email in recipient_emails:
            is_partner = self.partner_ids.filtered(lambda p: p.email == recipient_email)
            if is_partner:
                state = True
                break
        return state ^ CONDITION_STATE_CONTAINS.get(self.condition)

    def condition_author(self, author_id):
        """Contains author id in partner filter

        :param str author_id: mail author id
        :return bool contains/doesn't contain by conditions
        """
        if not author_id:
            return False
        is_partner = self.partner_ids.filtered(lambda p: p.id == author_id)
        return bool(is_partner) ^ CONDITION_STATE_CONTAINS.get(self.condition)

    def condition_other(self, text):
        """Contains value in text filter

        :param str text: contain/doesn't contain search text in mail field
        :return bool contains/doesn't contain by conditions
        """
        if self.condition not in CONDITION_STATE_EQ.keys():
            return (self.value in text) ^ CONDITION_STATE_CONTAINS.get(self.condition)
        value = self.value
        if self.trigger == "from":
            _, text = getaddresses([text])[0]
        if self.trigger in ["from", "to"]:
            text, value = text.lower(), value.lower()
        return (value == text) ^ CONDITION_STATE_EQ.get(self.condition)

    def check_filter_conditions(self, msg_dict):
        """Check all conditions lines in filters

        :param dict msg_dict: dictionary holding parsed message variables
        :return: bool
        """
        author_id = msg_dict.get("author_id", False)
        recipients = email_split("{} {}".format(msg_dict.get("to"), msg_dict.get("cc")))
        for rec in self:
            condition_author = rec.trigger == "author" and not rec.condition_author(
                author_id
            )
            condition_recipients = (
                rec.trigger == "recipients" and not rec.condition_recipients(recipients)
            )
            condition_other = rec.trigger not in [
                "recipients",
                "author",
            ] and not rec.condition_other(msg_dict.get(rec.trigger, ""))
            if condition_author or condition_recipients or condition_other:
                return False
        return True

    @api.model
    def get_existing_spam_condition(self, email_from):
        """
        Get filter record by spam condition
        :param email_from: email from
        :return: first active filter records or False
        """
        condition = self.search(
            [
                ("trigger", "=", "from"),
                ("condition", "=", "is"),
                ("value", "=", email_from),
            ]
        )
        if not condition:
            return False
        filter_id = condition.mapped("rule_id.filter_id").filtered(lambda f: f.active)
        return filter_id[0] if filter_id else False

    @api.model
    def create(self, vals):
        self._check_valid_condition(vals)
        return super(CxMessageFilterCondition, self).create(vals)

    def write(self, vals):
        self._check_valid_condition(vals)
        return super(CxMessageFilterCondition, self).write(vals)
