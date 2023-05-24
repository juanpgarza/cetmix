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

from odoo import models


class MailThread(models.AbstractModel):
    _name = "mail.thread"
    _inherit = "mail.thread"

    def unlink(self):
        """Delete all drafts"""
        if not self._name == "prt.mail.message.draft":
            self.env["prt.mail.message.draft"].sudo().search(
                [
                    ("model", "=", self._name),
                    ("id", "in", self.ids),
                ]
            ).sudo().unlink()
        return super(MailThread, self).unlink()
