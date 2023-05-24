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

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class CxMessageFilter(models.Model):
    _name = "cx.message.filter"
    _inherit = "mail.thread"
    _description = "Cetmix Message Filter"
    _order = "order, id desc"

    active = fields.Boolean(default=True)
    order = fields.Integer(default=10)
    name = fields.Char(required=True)
    destination_model_id = fields.Many2one(
        string="Destination Model",
        comodel_name="ir.model",
        help="New record will be created in this model",
    )
    rule_ids = fields.One2many(
        comodel_name="cx.message.filter.rule", inverse_name="filter_id"
    )
    action = fields.Selection(
        [
            ("m", "Post to model"),
            ("r", "Post to record"),
            ("s", "Search for record and post"),
            ("p", "Post to partner"),
            ("x", "Mark spam"),
            ("k", "Keep here"),
            ("n", "Do not receive"),
        ],
        required=True,
        help="'Post to model': will pass message to the selected model."
        " Important: model must have a method for parsing new messages!\n"
        "'Post to record': message will be posted to the selected record. "
        " Important: model must chatter!\n"
        "'Search for record and post': search for record "
        "using patterns and post to it\n"
        "'Post to partner': message will be posted to the partber record of a sender\n"
        "'Mark spam': messages will be moved to spam\n"
        "'Keep here': post message to the current filter record\n"
        "'Do not receive': message wil be simply ignored\n",
    )
    destination_rec = fields.Reference(
        string="Destination record",
        selection="_referencable_models",
    )
    custom_values = fields.Text(
        help="A dictionary of the custom values used for the 'message_new' method",
    )
    message_filtered_ids = fields.One2many(
        "mail.message",
        inverse_name="message_filter_id",
        string="Messages",
        context={"active_test": False},
    )
    message_count = fields.Integer(
        string="Messages", compute="_compute_filter_message_count"
    )

    def _compute_filter_message_count(self):
        """
        Compute message count by records
        in message_filtered_ids with subtype mt_note
        :return: None
        """
        subtype_mt_note = self.env.ref("mail.mt_note")
        for rec in self:
            rec.message_count = len(
                rec.message_filtered_ids.filtered(
                    lambda msg: msg.subtype_id != subtype_mt_note
                )
            )

    @api.model
    def get_or_create_spam_filter(self):
        """
        Get default spam filter or create new default spam filter
        :return: message spam filter
        """
        first_active_spam_filter = self.search(
            [
                ("action", "=", "x"),
                ("active", "=", True),
            ],
            limit=1,
        )
        if len(first_active_spam_filter) > 0:
            return first_active_spam_filter
        return self.create(
            {
                "name": "Default Spam Filter",
                "active": True,
                "action": "x",
                "order": 8,
            }
        )

    @api.model
    def _referencable_models(self):
        """
        List referencable Ref models
        :return: struct [(model, name)]
        """
        return [
            (x.model, x.name)
            for x in self.env["ir.model"]
            .sudo()
            .search([("transient", "=", False), ("is_mail_thread", "=", True)])
        ]

    @api.onchange("rule_ids")
    def onchange_rules(self):
        """Compute rule name before saving"""
        for rec in self:
            rec.rule_ids._compute_rule_name()

    def get_message_filter(self, msg_dict):
        """Get record by filter conditions for new message
        :param dict msg_dict: dictionary holding parsed message variables
        :return: list from record and modified msg_dict
        """
        for rec in self:
            rules = rec.rule_ids
            if rules.check_conditions(msg_dict):
                return rec, msg_dict
        return False, msg_dict

    def get_message_model(self, msg_dict, custom_values):
        """
        Create new record in destination filter model
        :param msg_dict: dictionary holding parsed message variables
        :param custom_values: optional dictionary of default field values
        :return: new ir.model record
        """
        self.ensure_one()

        try:
            custom_values = dict(safe_eval(self.custom_values))
        except Exception as e:
            _logger.warning("Error convert dict(safe_eval()): {}".format(e))
            custom_values = custom_values
        return self.env[self.destination_model_id.model].message_new(
            msg_dict, custom_values=custom_values
        )

    def deps_result_action(self, msg_value, custom_values):
        """
        Use this function to implement your custom actions

        :param msg_value: dictionary holding parsed message variables
        :param custom_values: optional dictionary of default field values
        :return: None or (ir.model, model record)
        """

    @api.model
    def _default_behavior(self, msg_dict, custom_values):
        """Default behavior for filter"""
        model_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("cx_mail_messages_filter.fallback_model_id", False)
        )
        if not model_id:
            return False
        model = self.env["ir.model"].browse(int(model_id)).model
        return self.env[model].message_new(msg_dict, custom_values)

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        Modifying incoming message_dict by filters
        :param dict msg_dict: dictionary holding parsed message variables
        :param dict custom_values: optional dictionary of default field values
        """
        filters = self.env[self._name].search([("active", "=", True)])
        record_filter, new_msg_dict = filters.get_message_filter(msg_dict)
        if record_filter:
            _logger.info(
                "Message from: %s subject: [%s] ID=%d filtered by %s"
                % (
                    msg_dict.get("email_from"),
                    msg_dict.get("subject", "empty"),
                    record_filter.id,
                    record_filter.name,
                )
            )
            msg_dict.update(
                {
                    "message_filter_id": record_filter.id,
                }
            )
            if record_filter.action == "x":
                msg_dict.update({"active": False, "spam_date": fields.Datetime.now()})
                _logger.info("Message moved to spam")
                return record_filter
            if record_filter.action == "r" and record_filter.destination_rec:
                return record_filter.destination_rec
            if record_filter.action == "n":
                self = self.with_context(record_ignore=True)
                _logger.info("Message was not received due to filter settings")
            if record_filter.action == "k":
                return record_filter
            if record_filter.destination_model_id.model and record_filter.action == "m":
                return record_filter.get_message_model(new_msg_dict, custom_values)
            else:
                result = record_filter.deps_result_action(new_msg_dict, custom_values)
                if result is not None:
                    return result

        model_id = self._default_behavior(msg_dict, custom_values)
        if model_id:
            return model_id
        raise ValidationError(
            _(
                "Fallback model is not defined! Please configure it in 'General Settings'"
            )
        )

    def action_filter_message(self):
        self.ensure_one()
        return {
            "name": _("Filtered Messages"),
            "domain": [
                ("message_filter_id", "=", self.id),
                ("subtype_id", "!=", self.env.ref("mail.mt_note").id),
            ],
            "views": [
                [self.env.ref("prt_mail_messages.prt_mail_message_tree").id, "tree"],
                [self.env.ref("prt_mail_messages.prt_mail_message_form").id, "form"],
            ],
            "context": {"active_test": False},
            "res_model": "mail.message",
            "target": "current",
            "type": "ir.actions.act_window",
        }
