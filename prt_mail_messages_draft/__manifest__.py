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

{
    "name": """
Mail Messages Draft."
Save Message as Draft, Edit Message Drafts, Send Message from Draft Message
""",
    "version": "15.0.1.0.1",
    "summary": """Adds draft messages support to free 'Mail Messages Easy' app""",
    "author": "Ivan Sokolov, Cetmix",
    "category": "Discuss",
    "license": "LGPL-3",
    "website": "https://cetmix.com",
    "live_test_url": "https://demo.cetmix.com",
    "depends": ["prt_mail_messages"],
    "images": ["static/description/banner.png"],
    "data": [
        "security/ir.model.access.csv",
        "security/rules.xml",
        "views/prt_mail_message_draft_view.xml",
        "wizard/mail_compose_message.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
