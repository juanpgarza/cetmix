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

from odoo import fields, models

from ..models.tools import _select_draft


class MailComposer(models.TransientModel):
    _name = "mail.compose.message"
    _inherit = "mail.compose.message"

    current_draft_id = fields.Many2one("prt.mail.message.draft", string="Draft")

    def _update_existing_draft(self, draft):
        """Update existing draft"""
        return draft.write(
            {
                "res_id": self.res_id,
                "model": self.model,
                "parent_id": self.parent_id.id,
                "author_id": self.author_id.id,
                "partner_ids": [(6, False, self.partner_ids.ids)],
                "attachment_ids": [(6, False, self.attachment_ids.ids)],
                "subject": self.subject,
                "signature_location": self.signature_location,
                "body": self.body,
                "wizard_mode": self.wizard_mode,
                "subtype_id": self.subtype_id.id,
            }
        )

    def _create_new_draft(self):
        """Create new draft"""
        return self.env["prt.mail.message.draft"].create(
            {
                "res_id": self.res_id,
                "model": self.model,
                "parent_id": self.parent_id.id,
                "author_id": self.author_id.id,
                "partner_ids": [(4, x, False) for x in self.partner_ids.ids],
                "attachment_ids": [(4, x, False) for x in self.attachment_ids.ids],
                "subject": self.subject,
                "signature_location": self.signature_location,
                "wizard_mode": self.wizard_mode,
                "body": self.body,
                "subtype_id": self.subtype_id.id,
            }
        )

    def _save_draft(self, draft):
        """Save draft wrapper"""
        self.ensure_one()
        if draft:
            return self._update_existing_draft(draft)
        return self._create_new_draft()

    def save_draft(self):
        """Save draft button"""
        result = self._save_draft(self.current_draft_id)
        if self._context.get("save_mode", False) == "save":
            if self.current_draft_id:
                return _select_draft(self.current_draft_id)
            return _select_draft(result)
        if self.wizard_mode == "compose":
            return self.env["ir.actions.act_window"]._for_xml_id(
                "prt_mail_messages_draft.action_prt_mail_messages_draft"
            )
        return

    def send_mail(self, auto_commit=False):
        result = super(MailComposer, self).send_mail(auto_commit=auto_commit)
        self.env["prt.mail.message.draft"].sudo().search(
            [
                ("model", "=", self.model),
                ("res_id", "=", self.res_id),
                ("write_uid", "=", self.create_uid.id),
            ]
        ).sudo().unlink()
        if not self._context.get("wizard_mode", False) == "compose":
            return result
        return self.env["ir.actions.act_window"]._for_xml_id(
            "prt_mail_messages.action_prt_mail_messages"
        )
