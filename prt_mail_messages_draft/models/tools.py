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

from odoo import _


def _select_draft(draft):
    if not draft:
        return
    return {
        "name": _("New message"),
        "views": [[False, "form"]],
        "res_model": "mail.compose.message",
        "type": "ir.actions.act_window",
        "target": "new",
        "context": {
            "default_res_id": draft.res_id,
            "default_model": draft.model,
            "default_parent_id": draft.parent_id,
            "default_partner_ids": draft.partner_ids.ids or False,
            "default_attachment_ids": draft.attachment_ids.ids or False,
            "default_is_log": False,
            "default_subject": draft.subject,
            "default_body": draft.body,
            "default_subtype_id": draft.subtype_id.id,
            "default_message_type": "comment",
            "default_current_draft_id": draft.id,
            "default_signature_location": draft.signature_location,
            "default_wizard_mode": draft.wizard_mode,
        },
    }
