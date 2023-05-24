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


class TestMessageSpamDelete(common.TransactionCase):
    """
    TEST 1 : Message mark spam and delete (unlink_pro)
        [Mark spam]
        - message mark read
        - message is spam
        [Delete]
        - message is deleted

    TEST 2 : Message move to trash and mark spam
        [Move to trash]
        - message active is False
        - message delete date is not False
        [Mark spam]
        - message active is False
        - message delete date is False
        - message spam date is not False
        - author active is False

    TEST 3 : Create conversation and two messages.
    Mark spam conversation messages. Unmark spam
        [Move to trash]
        - conversation active is True
        [Mark spam]
        - conversation active is False
        [Unmark spam]
        - conversation active is True
    """

    def setUp(self):
        super(TestMessageSpamDelete, self).setUp()
        self.mail_message_model = self.env["mail.message"]
        res_partner_model = self.env["res.partner"]
        cetmix_conversation_model = self.env["cetmix.conversation"]

        self.res_partner_test_1 = res_partner_model.create(
            {
                "name": "Test Partner #1",
                "email": "exmaple1@empl.com",
            }
        )

        self.mail_message_test_1 = self.mail_message_model.create(
            {
                "subject": "Test Message #1",
                "body": "Test no html message",
                "email_from": self.res_partner_test_1.email,
                "author_id": self.res_partner_test_1.id,
            }
        )

        self.cetmix_conversation_test_1 = cetmix_conversation_model.create(
            {
                "name": "Test Conversation #1",
                "active": True,
                "author_id": self.res_partner_test_1.id,
            }
        )

        self.mail_message_conversation_test_1 = self.mail_message_model.create(
            {
                "res_id": self.cetmix_conversation_test_1.id,
                "model": cetmix_conversation_model._name,
                "reply_to": "test.reply1@example.com",
                "email_from": "test.from1@example.com",
                "body": "mail message conversation test 1",
            }
        )

        self.mail_message_conversation_test_2 = self.mail_message_model.create(
            {
                "res_id": self.cetmix_conversation_test_1.id,
                "model": cetmix_conversation_model._name,
                "reply_to": "test.reply2@example.com",
                "email_from": "test.from2@example.com",
                "body": "mail message conversation test 2",
            }
        )

    def test_mark_spam_and_delete(self):
        self.mail_message_test_1.mark_spam()
        self.assertFalse(self.mail_message_test_1.active)
        self.assertTrue(self.mail_message_test_1.spam_date)

        self.mail_message_test_1.unlink_pro()
        message_not_found = self.mail_message_model.search(
            [("id", "=", self.mail_message_test_1.id)]
        )
        self.assertFalse(message_not_found)

    def test_msg_trash_and_mark_spam(self):
        self.mail_message_test_1.unlink_pro()
        self.assertFalse(self.mail_message_test_1.active)
        self.assertTrue(self.mail_message_test_1.delete_date)

        self.mail_message_test_1.mark_spam()
        self.assertFalse(self.mail_message_test_1.active)
        self.assertFalse(self.mail_message_test_1.delete_date)
        self.assertTrue(self.mail_message_test_1.spam_date)
        self.assertFalse(self.mail_message_test_1.author_id.active)

    def test_conversation_spam(self):
        self.mail_message_conversation_test_1.unlink_pro()
        self.assertTrue(self.cetmix_conversation_test_1.active)

        self.mail_message_conversation_test_2.mark_spam()
        self.assertFalse(self.cetmix_conversation_test_1.active)

        self.mail_message_conversation_test_2.unmark_spam()
        self.assertTrue(self.cetmix_conversation_test_1.active)
