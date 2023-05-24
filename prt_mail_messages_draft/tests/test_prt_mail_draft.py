###################################################################################
# 
#    Copyright (C) Cetmix OÜ
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

from odoo.tests import common


class TestPrtMailDraft(common.TransactionCase):
    def setUp(self):
        super(TestPrtMailDraft, self).setUp()
        self.PrtMailMessageDraft = self.env["prt.mail.message.draft"]
        self.MailComposeMessage = self.env["mail.compose.message"]
        ResPartner = self.env["res.partner"]

        self.res_partner_test_1 = ResPartner.create({"name": "Test Partner #1"})

        self.prt_mail_message_draft_test_1 = self.PrtMailMessageDraft.create(
            {
                "subject": "Test Subject #1",
                "body": "Test text body",
            }
        )

    def test_create_draft(self):
        subject = "Test Wizard!"
        body = "Test Body text!"

        form = common.Form(self.MailComposeMessage)
        form.partner_ids.add(self.res_partner_test_1)
        form.subject = subject
        form.body = body
        test_wizard = form.save()
        result = test_wizard.with_context(save_mode="save").save_draft()
        self.assertEqual(result.get("name"), "New message")
        self.assertEqual(result.get("res_model"), "mail.compose.message")
        self.assertEqual(result.get("type"), "ir.actions.act_window")
        self.assertEqual(type(result["context"]["default_current_draft_id"]), int)
        draft_id = result["context"]["default_current_draft_id"]
        draft_obj_id = self.PrtMailMessageDraft.search([("id", "=", draft_id)])
        self.assertEqual(draft_obj_id.id, draft_id)
        self.assertTrue(len(draft_obj_id) == 1)
        self.assertEqual(draft_obj_id.subject, subject)
        self.assertIn(body, draft_obj_id.body)
        self.assertFalse(draft_obj_id.model)
        self.assertEqual(draft_obj_id.res_id, 0)
        self.assertEqual(draft_obj_id.partner_ids, self.res_partner_test_1)

        new_subject = "Test Wizard Change #1"
        test_wizard.subject = new_subject
        result = test_wizard.with_context(save_mode="save").save_draft()
        self.assertEqual(type(result["context"]["default_current_draft_id"]), int)
        updated_draft_id = result["context"]["default_current_draft_id"]
        updated_draft_obj_id = self.PrtMailMessageDraft.search(
            [("id", "=", updated_draft_id)]
        )
        self.assertEqual(updated_draft_obj_id.id, updated_draft_id)
        self.assertTrue(len(updated_draft_obj_id) == 1)
        self.assertEqual(updated_draft_obj_id.subject, new_subject)
        self.assertIn(body, updated_draft_obj_id.body)

    def test_create_draft_result_none(self):
        subject = "Test Wizard!"
        body = "Test Body text!"

        form = common.Form(self.MailComposeMessage)
        form.partner_ids.add(self.res_partner_test_1)
        form.subject = subject
        form.body = body
        test_wizard = form.save()
        result = test_wizard.save_draft()
        self.assertIsNone(result)

    def test_prepare_model_dict(self):
        valid_variant_dict = {"res.partner": ["Contact", 1]}
        res_partner_model_id = self.env["ir.model"].search(
            [
                ("model", "=", "res.partner"),
            ]
        )
        result = self.PrtMailMessageDraft._prepare_model_dict(res_partner_model_id)
        self.assertEqual(valid_variant_dict, result)

    def test_prepare_subject_display(self):
        default_subject_display = "=== No Reference ==="
        empty_model_dict = {}
        _, result = self.prt_mail_message_draft_test_1._prepare_subject_display(
            default_subject_display, empty_model_dict
        )
        self.assertEqual(result, default_subject_display)
        self.prt_mail_message_draft_test_1.write(
            {
                "model": self.res_partner_test_1._name,
                "res_id": self.res_partner_test_1.id,
            }
        )
        _, result = self.prt_mail_message_draft_test_1._prepare_subject_display(
            default_subject_display, empty_model_dict
        )
        self.assertEqual(result, default_subject_display)

        valid_result = "Contact: Test Partner #1"
        valid_variant_dict = {"res.partner": ["Contact", 1]}
        _, result = self.prt_mail_message_draft_test_1._prepare_subject_display(
            default_subject_display, valid_variant_dict
        )
        self.assertEqual(result, valid_result)

        valid_result = "Contact => Test Subject #1"
        invalid_variant_dict = {"res.partner": ["Contact", 0]}
        _, result = self.prt_mail_message_draft_test_1._prepare_subject_display(
            default_subject_display, invalid_variant_dict
        )
        self.assertEqual(result, valid_result)
        self.prt_mail_message_draft_test_1.subject = ""
        _, result = self.prt_mail_message_draft_test_1._prepare_subject_display(
            default_subject_display, invalid_variant_dict
        )
        self.assertEqual(result, default_subject_display)
