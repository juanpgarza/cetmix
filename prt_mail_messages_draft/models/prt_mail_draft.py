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

from odoo import api, fields, models

from .tools import _select_draft


class PRTMailMessageDraft(models.Model):
    _name = "prt.mail.message.draft"
    _description = "Draft Message"
    _order = "write_date desc, id desc"
    _rec_name = "subject"

    def _get_subtypes(self):
        return [
            (
                "id",
                "in",
                [
                    self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_comment"),
                    self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_note"),
                ],
            )
        ]

    subject = fields.Char()
    subject_display = fields.Char(string="Subject", compute="_compute_subject_display")
    body = fields.Html(
        string="Contents", default="", sanitize_style=True, strip_classes=True
    )

    model = fields.Char(string="Related Document Model", index=True)
    res_id = fields.Integer(string="Related Document ID", index=True)

    subtype_id = fields.Many2one(
        string="Message Type",
        comodel_name="mail.message.subtype",
        domain=_get_subtypes,
        default=lambda self: self.env["ir.model.data"]._xmlid_to_res_id(
            "mail.mt_comment"
        ),
        required=True,
    )

    parent_id = fields.Integer(string="Parent Message")
    author_id = fields.Many2one(
        "res.partner",
        string="Author",
        index=True,
        ondelete="set null",
        default=lambda self: self.env.user.partner_id.id,
    )
    partner_ids = fields.Many2many("res.partner", string="Recipients")
    record_ref = fields.Reference(
        string="Message Record",
        selection="_referenceable_models",
        compute="_compute_record_ref",
    )
    attachment_ids = fields.Many2many(
        string="Attachments",
        comodel_name="ir.attachment",
        relation="prt_message_draft_attachment_rel",
        column1="message_id",
        column2="attachment_id",
    )
    ref_partner_ids = fields.Many2many(
        "res.partner",
        string="Followers",
        compute="_compute_message_followers",
    )
    ref_partner_count = fields.Integer(
        string="Followers", compute="_compute_ref_partner_count"
    )
    wizard_mode = fields.Char(default="composition")
    signature_location = fields.Selection(
        [("b", "Before quote"), ("a", "Message bottom"), ("n", "No signature")],
        default="b",
        required=True,
        help="Whether to put signature before or after the quoted text.",
    )

    def _compute_ref_partner_count(self):
        """Count ref Partners"""
        for rec in self:
            rec.ref_partner_count = len(rec.ref_partner_ids)

    @api.depends("record_ref")
    def _compute_message_followers(self):
        """Get related record followers"""
        for rec in self:
            if rec.record_ref:
                rec.ref_partner_ids = rec.record_ref.message_partner_ids

    @api.model
    def _prepare_model_dict(self, ir_models):
        """
        Prepare model dict
        :param ir_models: models records
        :return: struct {model._name [name, count field name]}
        """
        model_dict = {}
        for model in ir_models:
            has_name = (
                self.env["ir.model.fields"]
                .sudo()
                .search_count([("model_id", "=", model.id), ("name", "=", "name")])
            )
            model_dict.update({model.model: [model.name, has_name]})
        return model_dict

    def _prepare_subject_display(self, default_subject, model_dict):
        """
        Prepare subject display
        :param default_subject: default subject name
        :param model_dict: struct {model._name [name, count field name]}
        :return: State bool value and prepared subject display value
        """
        if not self.record_ref:
            return True, default_subject
        result = model_dict.get(self.model, False)
        if not (result and len(result) == 2):
            return True, default_subject
        subject_display, has_name = result
        if has_name:
            return True, "{}: {}".format(subject_display, self.record_ref.name)
        if self.subject:
            return True, "{} => {}".format(subject_display, self.subject)
        return False, default_subject

    def _compose_subject(self, model_dict):
        """
        Prepare subject display
        :param model_dict: Prepare subject display
        :return: None
        """
        subject_display = "=== No Reference ==="
        for rec in self:
            __, subject_display = rec._prepare_subject_display(
                subject_display, model_dict
            )
            rec.subject_display = subject_display

    @api.depends("subject")
    def _compute_subject_display(self):
        """Get Subject for tree view"""
        model_ids = list(set(self.mapped("model")))
        ir_models = self.env["ir.model"].search([("model", "in", model_ids)])
        model_dict = self._prepare_model_dict(ir_models)
        self._compose_subject(model_dict)

    @api.model
    def _referenceable_models(self):
        """Compute ref models"""
        return [
            (x.model, x.name)
            for x in self.env["ir.model"]
            .sudo()
            .search([("model", "!=", "mail.channel")])
        ]

    @api.depends("res_id")
    def _compute_record_ref(self):
        """Compute compose reference"""
        for rec in self:
            if not rec.res_id and not rec.model:
                rec.record_ref = False
                continue
            res = self.env[rec.model].sudo().search([("id", "=", rec.res_id)])
            if res:
                rec.record_ref = res

    def send_it(self):
        """Send message"""
        self.ensure_one()
        return _select_draft(self)
