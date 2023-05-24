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

from datetime import datetime, timedelta

from odoo.tests import common


class TestMessageSpam(common.TransactionCase):
    def setUp(self):
        super(TestMessageSpam, self).setUp()
        res_partner_model = self.env["res.partner"]
        mail_message_model = self.env["mail.message"]
        cx_message_filter_model = self.env["cx.message.filter"]

        self.res_partner_test_1 = res_partner_model.create(
            {"name": "Test Partner", "email": "example@exmp.com"}
        )

        self.mail_message_test_1 = mail_message_model.create(
            {
                "subject": "To Odoo User",
                "body": "Test no html message",
                "email_from": self.res_partner_test_1.email,
                "author_id": self.res_partner_test_1.id,
            }
        )

        self.cx_message_filter = cx_message_filter_model.create(
            {
                "name": "Test Filter",
                "active": False,
                "action": "x",
                "order": 9,
            }
        )

        self.res_partner_test_2 = res_partner_model.create(
            {"name": "Test Partner #2", "email": "example2@exmp.com"}
        )
        self.res_partner_test_3 = res_partner_model.create(
            {"name": "Test Partner #3", "email": "example3@exmp.com"}
        )
        self.res_partner_test_4 = res_partner_model.create(
            {"name": "Test Partner #4", "email": "example4@exmp.com"}
        )

        self.mail_message_test_2 = mail_message_model.create(
            {
                "subject": "To Odoo User",
                "body": "Test no html message",
                "email_from": self.res_partner_test_2.email,
                "author_id": self.res_partner_test_2.id,
            }
        )

        self.mail_message_test_3 = mail_message_model.create(
            {
                "subject": "To Odoo User",
                "body": "Test no html message",
                "email_from": self.res_partner_test_3.email,
                "author_id": self.res_partner_test_3.id,
            }
        )

        self.mail_message_test_4 = mail_message_model.create(
            {
                "subject": "To Odoo User",
                "body": "Test no html message",
                "email_from": self.res_partner_test_4.email,
                "author_id": self.res_partner_test_4.id,
            }
        )

    def test_compute_count_spam_days(self):
        now_datetime = datetime.now()
        old_datetime = now_datetime - timedelta(days=2)
        self.mail_message_test_1.write({"spam_date": old_datetime})
        self.assertTrue(self.mail_message_test_1.spam_days == 2)

    def test_get_or_create_spam_filter(self):
        self.cx_message_filter.write({"active": True})
        custom_filter = self.cx_message_filter.get_or_create_spam_filter()
        self.assertTrue(custom_filter.action == "x")
        self.cx_message_filter.write({"active": False})
        custom_filter = self.cx_message_filter.get_or_create_spam_filter()
        self.assertTrue(custom_filter.name == "Default Spam Filter")
        self.assertTrue(custom_filter.action == "x")
        self.assertTrue(custom_filter.active)

    def test_check_rule_by_message_filter(self):
        cx_message_filter_rule_model = self.env["cx.message.filter.rule"]

        self.cx_message_filter.write({"active": True})
        result = self.mail_message_test_1.check_rule_by_message_filter(
            filter_id=self.cx_message_filter.id,
        )
        self.assertFalse(result)

        cx_message_filter_rule_model.create(
            {
                "filter_id": self.cx_message_filter.id,
                "message_id": self.mail_message_test_1.id,
            }
        )
        result = self.mail_message_test_1.check_rule_by_message_filter(
            filter_id=self.cx_message_filter.id,
        )
        self.assertTrue(result)

        result = self.mail_message_test_1.check_rule_by_message_filter(filter_id=0)
        self.assertFalse(result)

    def test_create_rule_for_spam_filter(self):
        self.cx_message_filter.write({"active": True})
        filter_id = self.cx_message_filter.id
        rule = self.mail_message_test_1.create_rule_for_spam_filter(filter_id)
        self.assertTrue(rule)
        rule = self.mail_message_test_1.create_rule_for_spam_filter(0)
        self.assertFalse(rule)
        rule = self.mail_message_test_1.create_rule_for_spam_filter(None)
        self.assertFalse(rule)

    def test_create_spam_condition(self):
        cx_message_filter_rule_model = self.env["cx.message.filter.rule"]
        rule = cx_message_filter_rule_model.create(
            {
                "filter_id": self.cx_message_filter.id,
                "message_id": self.mail_message_test_1.id,
            }
        )
        status, error_message = rule.create_spam_condition(False)
        self.assertFalse(status)
        self.assertEqual(error_message, "Message is empty!")

        status, error_message = rule.create_spam_condition(self.mail_message_test_1)
        self.assertTrue(status)
        self.assertEqual(error_message, "Ok!")
        self.mail_message_test_1.write({"email_from": ""})
        status, error_message = rule.create_spam_condition(self.mail_message_test_1)
        self.assertFalse(status)
        self.assertEqual(
            error_message,
            "Message ID [%d] email_from is not found!" % self.mail_message_test_1.id,
        )

    def test_mark_spam(self):
        cx_message_filter_rule_model = self.env["cx.message.filter.rule"]
        self.cx_message_filter.write({"active": True, "order": 1})
        self.mail_message_test_1.mark_spam()
        self.assertFalse(self.mail_message_test_1.active)
        self.assertTrue(self.mail_message_test_1.spam_date)
        self.assertEqual(len(self.cx_message_filter.rule_ids.ids), 1)
        rule = cx_message_filter_rule_model.search(
            [("message_id", "=", self.mail_message_test_1.id)]
        )
        self.assertTrue(rule)
        self.assertEqual(len(rule.condition_ids.ids), 1)
        self.assertEqual(rule.filter_id.id, self.cx_message_filter.id)
        self.assertEqual(rule.message_id, self.mail_message_test_1.id)
        self.assertTrue(self.res_partner_test_1.spammer)
        self.assertFalse(self.res_partner_test_1.active)

    def test_delete_spam(self):
        mail_message_model = self.env["mail.message"]
        messages = mail_message_model.search([("body", "=", "Test no html message")])
        self.assertEqual(len(messages), 4)
        messages.mark_spam()
        spam_messages = messages.filtered(lambda msg: msg.spam_date)
        self.assertEqual(len(spam_messages), 4)
        self.assertEqual(len(messages), 4)
        spam_messages._delete_spam()
        messages = mail_message_model.search([("body", "=", "Test no html message")])
        self.assertFalse(messages)

    def test_unmark_spam(self):
        cx_message_filter_rule_model = self.env["cx.message.filter.rule"]
        self.mail_message_test_1.unlink_pro()
        self.assertTrue(self.mail_message_test_1.delete_date)
        self.assertFalse(self.mail_message_test_1.active)
        self.assertTrue(self.mail_message_test_1.delete_uid)
        self.mail_message_test_1.mark_spam()
        rule = cx_message_filter_rule_model.search(
            [("message_id", "=", self.mail_message_test_1.id)]
        )
        self.assertTrue(rule)
        self.assertFalse(self.mail_message_test_1.active)
        self.assertTrue(self.mail_message_test_1.spam_date)
        self.assertTrue(self.mail_message_test_1.author_id.spammer)
        self.assertFalse(self.mail_message_test_1.author_id.active)
        self.mail_message_test_1.unmark_spam()
        self.assertFalse(self.mail_message_test_1.spam_date)
        self.assertTrue(self.mail_message_test_1.active)
        self.assertTrue(self.mail_message_test_1.author_id.active)
        self.assertFalse(self.mail_message_test_1.author_id.spammer)
        rule = cx_message_filter_rule_model.search(
            [("message_id", "=", self.mail_message_test_1.id)]
        )
        self.assertFalse(rule)
