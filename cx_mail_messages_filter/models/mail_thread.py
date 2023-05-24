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

from odoo import api, fields, models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        message_filter_id = msg_dict.get("message_filter_id", False)
        if self._context.get("alias_spam", False):
            filter_id = self.env["cx.message.filter"].search(
                [("id", "=", message_filter_id)]
            )
            if filter_id:
                return filter_id
        return super(MailThread, self).message_new(msg_dict, custom_values)

    @api.model
    def check_alias_has_check_spam(self, routes):
        """
        Check Alias has check spam state
        :param routes: list message route
        :return: bool
        """
        for route in routes:
            alias_id = route[4]
            if not alias_id:
                continue
            if alias_id.check_spam:
                return True
        return False

    @api.model
    def _message_route_process(self, message, message_dict, routes):
        if len(routes) == 0:
            return super(MailThread, self)._message_route_process(
                message, message_dict, routes
            )
        spam_filters = self.env["cx.message.filter"].search(
            [
                ("active", "=", True),
                ("action", "=", "x"),
            ]
        )
        record_filter, _ = spam_filters.get_message_filter(message_dict)
        if not record_filter:
            if self.check_alias_has_check_spam(routes):
                message_dict.update(
                    {
                        "active": False,
                        "spam_date": fields.Datetime.now(),
                        "message_filter_id": record_filter.id,
                    }
                )
                self = self.with_context(alias_spam=True)
        return super(MailThread, self)._message_route_process(
            message, message_dict, routes
        )

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        """Return empty record"""
        if self._context.get("record_ignore", False):
            return self.env["mail.message"]
        if kwargs.get("message_filter_id", False):
            kwargs.update(subtype_id=self.env.ref("mail.mt_comment").id)
        return super(MailThread, self).message_post(**kwargs)
