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

from odoo.tests import common


class TestSpamAlias(common.TransactionCase):
    """
    TEST 1 : Mark Spam message by alias
        [Create message by function '_message_route_process']
        - message record_ref is spam filter
        - message message_filter_id not empty and equal spam filter
        - message spam_date not False
        - message active is False
    """

    def setUp(self):
        super(TestSpamAlias, self).setUp()
        MailAlias = self.env["mail.alias"]
        CxMessageFilter = self.env["cx.message.filter"]
        CxMessageFilterRule = self.env["cx.message.filter.rule"]
        self.test_ir_model_filter = self.env.ref(
            "cx_mail_messages_filter.model_cx_message_filter"
        )

        self.mail_alias_test = MailAlias.create(
            {
                "alias_name": "test_example",
                "alias_model_id": self.test_ir_model_filter.id,
                "alias_contact": "everyone",
                "alias_user_id": self.env.user.id,
                "check_spam": True,
            }
        )

        self.cx_message_filter_test_1 = CxMessageFilter.create(
            {
                "active": True,
                "name": "Test Spam Filter #1",
                "action": "x",
            }
        )

        self.cx_message_filter_rule_test = CxMessageFilterRule.create(
            {"filter_id": self.cx_message_filter_test_1.id}
        )

        self.cx_message_filter_rule_test.condition_ids.create(
            {
                "rule_id": self.cx_message_filter_rule_test.id,
                "trigger": "from",
                "condition": "is",
                "value": "from_test_example@example.com",
            }
        )

    def test_alias_spam_filter(self):
        routes = [("cx.message.filter", 0, {}, 2, self.mail_alias_test)]
        message_dict = {
            "message_type": "email",
            "message_id": "<CABFLKGmak@mail.example.com>",
            "subject": "DATA",
            "email_from": '"FROM_Test Example" <from_test_example@example.com>',
            "from": '"FROM_Test Example" <from_test_example@example.com>',
            "cc": "",
            "recipients": "test_example@example.com,"
            '"Test Example" <test_example@example.com>',
            "to": 'test_example@example.com,"Test Example" <test_example@example.com>',
            "partner_ids": [],
            "references": "",
            "in_reply_to": "",
            "date": "2022-02-17 08:34:38",
            "body": '<div dir="ltr">TEST DATA<br></div>\n',
            "attachments": [],
            "bounced_email": False,
            "bounced_partner": self.env["res.partner"],
            "bounced_msg_id": False,
            "bounced_message": self.env["mail.message"],
            "author_id": False,
        }
        message = ""
        self.env["mail.thread"]._message_route_process(message, message_dict, routes)
        message_id = self.env["mail.message"].search(
            [
                ("active", "=", False),
                ("message_filter_id", "=", self.cx_message_filter_test_1.id),
            ],
            limit=1,
        )
        self.assertEqual(
            message_id.record_ref.id,
            self.cx_message_filter_test_1.id,
            msg="Record ref must be id equal 'cx_message_filter_test_1'",
        )
        self.assertEqual(
            message_id.message_filter_id,
            self.cx_message_filter_test_1,
            msg="Filter id must be equal 'cx_message_filter_test_1'",
        )
        self.assertNotEqual(
            message_id.spam_date, False, msg="Spam Datetime must be not empty"
        )
        self.assertFalse(message_id.active, msg="Message active must be False")
