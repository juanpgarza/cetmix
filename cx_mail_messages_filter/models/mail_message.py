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

from odoo import fields, models
from odoo.tools import getaddresses

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    message_filter_id = fields.Many2one("cx.message.filter", string="Mail Filter")

    spam_date = fields.Datetime("Spam on")
    spam_days = fields.Integer("Span days", compute="_compute_spam_days")

    def _compute_spam_days(self):
        """Compute number of days until deletion"""
        date_now = fields.Datetime.now().date()
        for rec in self:
            rec.spam_days = (date_now - rec.spam_date.date()).days

    def _notify_message_notification_update(self):
        self = self.filtered(lambda msg: msg.active and not msg.spam_date)
        return super(MailMessage, self)._notify_message_notification_update()

    def check_rule_by_message_filter(self, filter_id):
        """Check rule contain to the filter"""
        self.ensure_one()
        if not filter_id:
            return False
        msg_filter = self.env["cx.message.filter"].search([("id", "=", filter_id)])
        if not msg_filter:
            return False
        rule_id = msg_filter.rule_ids.filtered(lambda rule: rule.message_id == self.id)
        if rule_id:
            return rule_id[0]
        return False

    def create_rule_for_spam_filter(self, filter_id):
        """Get ot create filter for spam message"""
        self.ensure_one()
        if not filter_id:
            return False
        msg_filter = self.env["cx.message.filter"].search([("id", "=", filter_id)])
        if not msg_filter:
            return False
        rule = self.env["cx.message.filter.rule"].create(
            {"filter_id": msg_filter.id, "message_id": self.id}
        )
        return rule

    def _conversations_archive(self):
        """Archive conversation"""
        # Store Conversation ids
        conversation_ids = {
            rec.res_id for rec in self.sudo() if rec.model == "cetmix.conversation"
        }
        if not conversation_ids:
            return
        (
            conversations_2_archive,
            _,
        ) = self._get_conversation_messages_to_delete_and_archive(conversation_ids)
        if conversations_2_archive:
            self._archive_conversation_record(conversations_2_archive)

    def _check_existsing_condition_by_message(self):
        """
        Check condition by email address.
        If has filter condition by email address
        then update message filter id.
        :return: if has filter: True else False
        """
        self.ensure_one()
        if not self.email_from:
            return False
        _, email = getaddresses([self.email_from])[0]
        filter_id = self.env["cx.message.filter.condition"].get_existing_spam_condition(
            email
        )
        if filter_id:
            self.write({"message_filter_id": filter_id.id})
            return True
        return False

    def mark_spam(self):
        """Mark messages to spam"""
        self = self.filtered(lambda msg: not msg.spam_date)
        if not self:
            return
        trash_msg = self.filtered(lambda msg: msg.delete_date)
        if trash_msg:
            trash_msg.undelete()
        self.write(
            {
                "spam_date": fields.Datetime.now(),
                "active": False,
            }
        )
        # Conversation archive
        self._conversations_archive()

        # Mark read messages
        self.mark_read_multi()

        spam_filter = self.env["cx.message.filter"].get_or_create_spam_filter()
        for rec in self:
            if rec._check_existsing_condition_by_message():
                continue
            if rec.check_rule_by_message_filter(spam_filter.id):
                continue
            rec.write({"message_filter_id": spam_filter.id})
            rule = rec.create_rule_for_spam_filter(spam_filter.id)
            if rec.author_id:
                if not rec.author_id.spammer:
                    rec.author_id.set_partner_spammer_on_off()
            status, error_message = rule.create_spam_condition(rec)
            if not status:
                _logger.warning(error_message)

    def _conversation_unarchive(self):
        """Conversation unarchive"""
        for rec in self.sudo():
            if rec.model == "cetmix.conversation":
                conversation_ids = self.env["cetmix.conversation"].search(
                    [
                        ("active", "=", False),
                        ("id", "=", rec.res_id),
                    ]
                )
                conversation_ids.with_context(only_conversation=True).write(
                    {"active": True}
                )

    def unmark_spam(self):
        """Unmark spam messages"""
        self = self.filtered(lambda msg: msg.spam_date)
        if not self:
            return
        cx_message_filter_rule_model = self.env["cx.message.filter.rule"]
        self.write(
            {
                "spam_date": False,
                "message_filter_id": False,
            }
        )

        # Unarchive conversation
        self._conversation_unarchive()
        for rec in self:
            if not rec.active or rec.delete_date:
                rec.active = True
            rules = cx_message_filter_rule_model.search([("message_id", "=", rec.id)])
            rules.unlink()
            if rec.author_id:
                if rec.author_id.spammer:
                    rec.author_id.set_partner_spammer_on_off(state=False)

    def _delete_spam(self):
        """Delete all spam messages by cron"""
        days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("cx_mail_messages_filter.delete_spam_after", 0)
        )
        if days > 0:
            spam_messages = self.env["mail.message"].search(
                [
                    ("spam_date", "!=", False),
                    ("spam_days", "=", days),
                    ("active", "=", False),
                ]
            )
            spam_messages.unlink()

    # -- Unlink
    def unlink_pro(self):
        """Unlink spam message"""
        if self._context.get("spam_unlink", False):
            return super(MailMessage, self).unlink_pro()
        spam_msg = self.filtered(lambda msg: msg.spam_date)
        if spam_msg:
            spam_msg.with_context(spam_unlink=True).unlink_pro()
        return super(MailMessage, self).unlink_pro()

    def archive(self):
        """Don't archive spam messages"""
        self = self.filtered(lambda msg: not msg.spam_date)
        return super(MailMessage, self).archive()
