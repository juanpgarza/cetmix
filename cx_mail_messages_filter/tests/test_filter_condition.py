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

from odoo import models
from odoo.tests import common


class TestFilterCondition(common.TransactionCase):
    """
    TEST 1 : Create invalid condition
        [Create invalid condition 'is']
        - has an exception
    TEST 2 : Create valid conversation and change conversation
        [Update condition 'not']
        - has an exception
    TEST 3 : Test function condition_other
        [Create condition 'is']
        - email 'bob@example.co' is valid
        - email 'mr.bob@example.co' is invalid
        - email 'superbob@emample.com' is invalid
        [Create condition 'not']
        - email 'bob@example.co' is invalid
        - email 'mr.bob@example.co' is valid
        - email 'superbob@emample.com' is valid
        - email 'example@exmpl.com' is valid
    TEST 4 : Create condition for message in spam filter
        [Create filter #1, message]
        [Mark spam message]
        - message filter id is filter id #1
        - filter #1 has condition with ("from", "is", "partner_email")
    TEST 5 : Create spam filter with condition. Create message and it marks to spam.
        [Create filter #1, rule, condition]
        condition: ("from" "is" "partner_email")
        [Create message]
        [Mark spam]
        - message_filter_id  is filter #1

    """

    def setUp(self):
        super(TestFilterCondition, self).setUp()
        self.cx_message_filter_model = self.env["cx.message.filter"]
        self.cx_message_filter_condition_model = self.env["cx.message.filter.condition"]
        self.cx_message_filter_rule_model = self.env["cx.message.filter.rule"]
        self.test_ir_model_res_partner = self.env.ref("base.model_res_partner")
        self.res_partner_model = self.env["res.partner"]
        self.mail_message_model = self.env["mail.message"]

        self.res_partner_test_1 = self.res_partner_model.create(
            {"name": "Test Partner", "email": "demouser@example.com"}
        )

        self.mail_message_test_1 = self.mail_message_model.create(
            {
                "subject": "Test Message #1",
                "body": "Test with no html text",
                "email_from": self.res_partner_test_1.email,
                "author_id": self.res_partner_test_1.id,
            }
        )

        self.cx_message_filter_test_1 = self.cx_message_filter_model.create(
            {
                "active": True,
                "name": "Test Filter 1",
                "destination_model_id": self.test_ir_model_res_partner.id,
                "action": "m",
            }
        )

        self.cx_message_filter_rule_test_1 = self.cx_message_filter_rule_model.create(
            {"filter_id": self.cx_message_filter_test_1.id}
        )

        self.cx_message_filter_condition_test_1 = (
            self.cx_message_filter_condition_model.create(
                {
                    "rule_id": self.cx_message_filter_rule_test_1.id,
                    "trigger": "author",
                    "condition": "like",
                    "partner_ids": [(4, self.res_partner_test_1.id)],
                }
            )
        )

        self.cx_message_filter_spam_test_1 = self.cx_message_filter_model.create(
            {
                "active": True,
                "name": "Test spam filter",
                "action": "x",
                "order": 1,
            }
        )

    def test_invalid_condition(self):
        with self.assertRaises(models.UserError):
            self.cx_message_filter_condition_model.create(
                {
                    "rule_id": self.cx_message_filter_rule_test_1.id,
                    "trigger": "author",
                    "condition": "is",
                    "partner_ids": [(4, self.res_partner_test_1.id)],
                }
            )

    def test_update_condition(self):
        with self.assertRaises(models.UserError):
            self.cx_message_filter_condition_test_1.write({"condition": "not"})

    def test_condition_other(self):
        condition = self.cx_message_filter_condition_model.create(
            {
                "rule_id": self.cx_message_filter_rule_test_1.id,
                "trigger": "from",
                "condition": "is",
                "value": "BOB@example.co",
            }
        )
        self.assertTrue(condition.condition_other("Bob Robin <bob@example.co>"))
        self.assertTrue(condition.condition_other("Bob Robin <BOB@EXAMPLE.co>"))
        self.assertFalse(condition.condition_other("Mr Bob <mr.bob@example.co>"))
        self.assertFalse(condition.condition_other("Super Bob <superbob@emample.com>"))

        condition = self.cx_message_filter_condition_model.create(
            {
                "rule_id": self.cx_message_filter_rule_test_1.id,
                "trigger": "from",
                "condition": "not",
                "value": "bob@example.co",
            }
        )
        self.assertFalse(condition.condition_other("Bob Robin <bob@example.co>"))
        self.assertFalse(condition.condition_other("Bob Robin <BOB@EXAMPLE.co>"))
        self.assertTrue(condition.condition_other("Mr Robin <mr.bob@example.co>"))
        self.assertTrue(condition.condition_other("Super Robin <superbob@emample.com>"))
        self.assertTrue(condition.condition_other("Example User <example@exmpl.com>"))

        condition = self.cx_message_filter_condition_model.create(
            {
                "rule_id": self.cx_message_filter_rule_test_1.id,
                "trigger": "from",
                "condition": "like",
                "value": "Bob Robin",
            }
        )

        self.assertTrue(condition.condition_other("Bob Robin <bob@example.co>"))
        self.assertFalse(condition.condition_other("Mr Robin <mr.bob@example.co>"))

        condition = self.cx_message_filter_condition_model.create(
            {
                "rule_id": self.cx_message_filter_rule_test_1.id,
                "trigger": "to",
                "condition": "is",
                "value": "BOB@EX.com",
            }
        )

        self.assertTrue(condition.condition_other("bob@ex.com"))
        self.assertFalse(condition.condition_other("bob@ex.com,bob1@ex.com"))
        self.assertTrue(condition.condition_other("BOB@EX.COM"))

    def test_condition_for_message_spam_filter(self):
        self.mail_message_test_1.mark_spam()
        self.assertFalse(self.mail_message_test_1.active)
        self.assertTrue(self.mail_message_test_1.message_filter_id)
        self.assertEqual(
            self.mail_message_test_1.message_filter_id.id,
            self.cx_message_filter_spam_test_1.id,
        )

        filter_rule = self.cx_message_filter_spam_test_1.rule_ids
        self.assertTrue(len(filter_rule.ids) == 1)
        rule_id = filter_rule[0]
        self.assertTrue(rule_id.message_id == self.mail_message_test_1.id)
        self.assertTrue(len(rule_id.ids) == 1)
        condition = rule_id.condition_ids[0]
        self.assertEqual(condition.trigger, "from")
        self.assertFalse(condition.partner_ids)
        self.assertEqual(condition.value, self.res_partner_test_1.email)
        self.assertEqual(condition.condition, "is")

    def test_spam_filter_set_message_by_condition(self):
        cx_message_filter_spam_test_1 = self.cx_message_filter_model.create(
            {
                "active": False,
                "name": "Test spam filter",
                "action": "x",
                "order": 1,
            }
        )
        cx_message_filter_rule_spam_test_1 = self.cx_message_filter_rule_model.create(
            {"filter_id": cx_message_filter_spam_test_1.id}
        )
        self.cx_message_filter_condition_model.create(
            {
                "rule_id": cx_message_filter_rule_spam_test_1.id,
                "trigger": "from",
                "condition": "is",
                "value": self.res_partner_test_1.email,
            }
        )
        self.mail_message_test_1.mark_spam()

        self.assertEqual(
            self.mail_message_test_1.message_filter_id.id,
            self.cx_message_filter_spam_test_1.id,
        )
        self.assertNotEqual(
            self.mail_message_test_1.message_filter_id.id,
            cx_message_filter_spam_test_1.id,
        )
        self.mail_message_test_1.unmark_spam()
        cx_message_filter_spam_test_1.write({"active": True})
        self.mail_message_test_1.mark_spam()
        self.assertEqual(
            self.mail_message_test_1.message_filter_id.id,
            cx_message_filter_spam_test_1.id,
        )
