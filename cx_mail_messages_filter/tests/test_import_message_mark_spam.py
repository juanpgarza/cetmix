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


class TestMarkSpamIncomingMessage(common.TransactionCase):
    def setUp(self):
        super(TestMarkSpamIncomingMessage, self).setUp()
        cx_message_filter_model = self.env["cx.message.filter"]
        cx_message_filter_rule_model = self.env["cx.message.filter.rule"]
        cx_message_filter_condition_model = self.env["cx.message.filter.condition"]

        self.cx_message_filter_spam_test = cx_message_filter_model.create(
            {
                "active": True,
                "name": "Test spam filter",
                "action": "x",
                "order": 1,
            }
        )

        self.cx_message_rule_spam_test = cx_message_filter_rule_model.create(
            {
                "filter_id": self.cx_message_filter_spam_test.id,
            }
        )

        self.cx_message_condition_spam_test = cx_message_filter_condition_model.create(
            {
                "rule_id": self.cx_message_rule_spam_test.id,
                "trigger": "from",
                "condition": "like",
                "value": "example@exmpl.com",
            }
        )

    def test_move_to_spam(self):
        msg_dict = {
            "message_type": "email",
            "message_id": "",
            "subject": "Mail Test Subject",
            "from": "Test User Example <example@exmpl.com>",
            "to": "demo5@example.com, "
            "Test User <test1@example.com>, "
            "demo6@example.com",
            "cc": "",
            "email_from": "Test1 User1 <example@exmpl.com>",
            "date": "2021-08-04 15:08:08",
            "body": '<div dir="ltr"><span>DATA Text</span><br></div>',
            "attachments": [],
            "author_id": 1,
        }

        result = self.env["cx.message.filter"].message_new(msg_dict, custom_values=None)
        self.assertEqual(result.id, self.cx_message_filter_spam_test.id)
        self.assertEqual(result.action, "x")
        self.assertTrue(result.active)
