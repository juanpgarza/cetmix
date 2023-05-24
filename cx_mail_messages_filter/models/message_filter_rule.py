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

from odoo import api, fields, models
from odoo.tools import getaddresses


class CxMessageFilterRules(models.Model):
    _name = "cx.message.filter.rule"
    _order = "id desc"

    name = fields.Char("Condition", compute="_compute_rule_name")

    filter_id = fields.Many2one(
        "cx.message.filter", string="Filter", ondelete="cascade"
    )
    condition_ids = fields.One2many("cx.message.filter.condition", "rule_id")

    message_id = fields.Integer(string="Related Message")

    def _prepare_rule_name(self):
        """Prepare rule name"""
        self.ensure_one()
        full_name = ""
        for index, condition in enumerate(self.condition_ids, start=0):
            full_name += condition.name if index == 0 else " AND %s" % condition.name
        return full_name

    def _compute_rule_name(self):
        """Compute rule name"""
        for rec in self:
            rec.name = rec._prepare_rule_name()

    @api.onchange("condition_ids")
    def onchange_conditions(self):
        for rec in self:
            rec.condition_ids._compute_condition_name()

    def check_conditions(self, msg_dict):
        """
        Check all conditions from rule
        return: True/False
        """
        for rec in self:
            conditions = rec.condition_ids
            if conditions.check_filter_conditions(msg_dict):
                return True
        return False

    def _create_new_condition(self, email):
        """Create default condition for email"""
        self.condition_ids.create(
            {
                "rule_id": self.id,
                "trigger": "from",
                "condition": "is",
                "value": email,
            }
        )

    def create_spam_condition(self, mail_message):
        """Creations default condition for spam rule"""
        self.ensure_one()
        if not mail_message:
            return False, "Message is empty!"
        email_from = mail_message.email_from
        if not email_from:
            return False, "Message ID [%d] email_from is not found!" % mail_message.id
        _, email = getaddresses([email_from])[0]
        self._create_new_condition(email)
        return True, "Ok!"
