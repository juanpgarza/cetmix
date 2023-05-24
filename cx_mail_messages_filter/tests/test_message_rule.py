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


class TestFilterRule(common.TransactionCase):
    def setUp(self):
        super(TestFilterRule, self).setUp()
        self.model_message_filter = self.env["cx.message.filter"]
        self.model_message_rule = self.env["cx.message.filter.rule"]
        self.model_message_condition = self.env["cx.message.filter.condition"]
        self.model_res_partner = self.env["res.partner"]

        self.ir_model_res_partner = self.env.ref("base.model_res_partner").id

        self.filter = self.model_message_filter.create(
            {
                "active": True,
                "name": "Test Filter 1",
                "destination_model_id": self.ir_model_res_partner,
                "action": "m",
            }
        )

        self.filter_2 = self.model_message_filter.create(
            {
                "active": True,
                "name": "Test Filter 1",
                "destination_model_id": self.ir_model_res_partner,
                "action": "m",
            }
        )

        self.rule_1 = self.model_message_rule.create({"filter_id": self.filter.id})

        self.rule_2 = self.model_message_rule.create({"filter_id": self.filter.id})

        self.user_partner = self.model_res_partner.create(
            {"name": "Test Partner", "email": "demouser@example.com"}
        )

    def test_check_conditions(self):
        Condition = self.model_message_condition

        Condition.create(
            {
                "rule_id": self.rule_1.id,
                "trigger": "recipients",
                "partner_ids": [(4, self.user_partner.id)],
            }
        )

        Condition.create(
            {
                "rule_id": self.rule_1.id,
                "trigger": "author",
                "partner_ids": [(4, self.user_partner.id)],
            }
        )

        Condition.create(
            {
                "rule_id": self.rule_2.id,
                "trigger": "from",
                "value": "test@example.com",
            }
        )

        Condition.create(
            {
                "rule_id": self.rule_2.id,
                "trigger": "subject",
                "value": "Test Subject",
            }
        )

        valid_msg_dict = {
            "message_type": "email",
            "message_id": "",
            "subject": "Mail Test Subject",
            "from": "Test User Example <test@example.com>",
            "to": "demo5@example.com, "
            "Test User <test1@example.com>, "
            "demo6@example.com",
            "cc": "",
            "email_from": "Test1 User1 <demo7@exmaple.com>",
            "date": "2021-08-04 15:08:08",
            "body": '<div dir="ltr"><span>DATA Text</span><br></div>',
            "attachments": [],
            "author_id": 1,
        }

        invalid_msg_dict = {
            "message_type": "email",
            "message_id": "",
            "subject": "test message_new()",
            "from": "Test1 User1 <demo7@exmaple.com>",
            "to": "demo5@example.com, "
            "Test User <test1@example.com>, "
            "demo6@example.com",
            "cc": "",
            "email_from": "Test1 User1 <demo7@exmaple.com>",
            "date": "2021-08-04 15:08:08",
            "body": '<div dir="ltr"><span>DATA Text</span><br></div>',
            "attachments": [],
            "author_id": 1,
        }

        result_valid = self.filter.rule_ids.check_conditions(valid_msg_dict)
        self.assertTrue(result_valid)

        result_invalid = self.filter.rule_ids.check_conditions(invalid_msg_dict)
        self.assertFalse(result_invalid)

        result_invalid = self.filter_2.rule_ids.check_conditions(valid_msg_dict)
        self.assertFalse(result_invalid)
