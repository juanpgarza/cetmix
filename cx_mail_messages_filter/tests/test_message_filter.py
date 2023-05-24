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


class TestMessageFilter(common.TransactionCase):
    def setUp(self):
        super(TestMessageFilter, self).setUp()
        self.model_message_filter = self.env["cx.message.filter"]
        self.model_message_filter_condition = self.env["cx.message.filter.condition"]
        self.model_ir_model = self.env["ir.model"]
        self.model_res_partner = self.env["res.partner"]
        self.model_rule = self.env["cx.message.filter.rule"]

        self.test_partner = self.model_res_partner.create(
            {"name": "Test Partner", "email": "demouser@example.com"}
        )

        self.test_ir_model_res_partner = self.env.ref("base.model_res_partner")

        self.filter_1 = self.model_message_filter.create(
            {
                "active": True,
                "name": "Test Filter 1",
                "destination_model_id": self.test_ir_model_res_partner.id,
                "action": "m",
            }
        )

        self.test_rule = self.model_rule.create({"filter_id": self.filter_1.id})

        self.msg_dict = {
            "message_type": "email",
            "message_id": "",
            "subject": "test message_new()",
            "from": "Vova Test <test1@example.com>",
            "to": "Administrator <demouser@example.com>",
            "cc": "",
            "email_from": "Vova Test <test1@example.com>",
            "date": "2021-08-04 15:08:08",
            "body": '<div dir="ltr"><br></div>\n',
            "attachments": [],
            "author_id": 75,
        }

    def test_condition_recipient(self):
        condition_recipient = self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "recipients",
                "partner_ids": [(4, self.test_partner.id)],
            }
        )

        result = condition_recipient.condition_recipients(
            ["demouser@example.com", "test1@example.com"]
        )
        self.assertTrue(result)

        result = condition_recipient.condition_recipients(["test1@example.com"])
        self.assertFalse(result)

        condition_recipient.write({"condition": "not_like"})

        result = condition_recipient.condition_recipients(
            ["demouser@example.com", "test1@example.com"]
        )
        self.assertFalse(result)

        result = condition_recipient.condition_recipients(["test1@example.com"])
        self.assertTrue(result)

    def test_condition_author(self):
        condition_author = self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "author",
                "partner_ids": [(4, self.test_partner.id)],
            }
        )
        result = condition_author.condition_author(self.test_partner.id)
        self.assertTrue(result)

        result = condition_author.condition_author(1)
        self.assertFalse(result)

        condition_author.write({"condition": "not_like"})

        result = condition_author.condition_author(self.test_partner.id)
        self.assertFalse(result)

        result = condition_author.condition_author(1)
        self.assertTrue(result)

    def test_condition_other(self):
        condition_text = self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "subject",
                "value": "test",
                "condition": "like",
            }
        )
        result = condition_text.condition_other("test")
        self.assertTrue(result)

        result = condition_text.condition_other("tes1t")
        self.assertFalse(result)

        condition_text.write({"condition": "not_like"})

        result = condition_text.condition_other("test")
        self.assertFalse(result)

        result = condition_text.condition_other("tes1t")
        self.assertTrue(result)

    def test_check_filter_conditions_valid(self):
        self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "recipients",
                "condition": "like",
                "partner_ids": [(4, self.test_partner.id)],
            }
        )
        self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "author",
                "condition": "like",
                "partner_ids": [(4, self.test_partner.id)],
            }
        )
        self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "subject",
                "value": "test",
                "condition": "like",
            }
        )
        self.msg_dict.update(author_id=self.test_partner.id)
        rule = self.filter_1.rule_ids
        result = rule.check_conditions(self.msg_dict)
        self.assertTrue(result)

    def test_check_filter_conditions_invalid(self):
        self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "recipients",
                "partner_ids": [(4, self.test_partner.id)],
                "condition": "like",
            }
        )
        self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "author",
                "partner_ids": [(4, self.test_partner.id)],
                "condition": "like",
            }
        )
        self.model_message_filter_condition.create(
            {
                "rule_id": self.test_rule.id,
                "trigger": "subject",
                "value": "test1",
                "condition": "like",
            }
        )

        rule = self.filter_1.rule_ids
        result = rule.check_conditions(self.msg_dict)
        self.assertFalse(result)

    def test_message_new_empty_filter(self):
        msg_dict = {
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
        self.filter_1.unlink()
        model_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("cx_mail_messages_filter.fallback_model_id", False)
        )
        if not model_id:
            self.assertFalse(model_id)
        self.env["ir.config_parameter"].sudo().set_param(
            "cx_mail_messages_filter.fallback_model_id",
            self.test_ir_model_res_partner.id,
        )
        result = self.env["cx.message.filter"].message_new(msg_dict, custom_values=None)
        model_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("cx_mail_messages_filter.fallback_model_id", False)
        )
        model_config_name = self.env["ir.model"].browse(model_id)._name
        model_valid_name = self.env["ir.model"].browse(result.id)._name
        self.assertEqual(model_config_name, model_valid_name)

    def test_message_new_action_keep_here(self):
        self.filter_1.write(
            {
                "action": "m",
            }
        )
        msg_dict = {
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
        result = self.env["cx.message.filter"].message_new(msg_dict, custom_values=None)
        self.assertNotEqual(result, self.filter_1)

    def test_message_new_post_to_model(self):
        self.filter_1.write(
            {
                "action": "m",
            }
        )
        msg_dict = {
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
        result = self.env["cx.message.filter"].message_new(msg_dict, custom_values=None)
        model_config = result
        self.assertEqual(model_config._name, self.test_ir_model_res_partner.model)
