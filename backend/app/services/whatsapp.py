"""WhatsApp delivery without a paid API: an official click-to-chat link (https://wa.me/...).

Staff press "Send on WhatsApp"; WhatsApp (phone, desktop or web) opens a chat with the customer and the
message already typed, including the secure quotation link. Staff press Send in their own WhatsApp
Business app. Free, uses the business's own number, and follows WhatsApp's rules (no unofficial bots).
To automate later, swap this for the WhatsApp Cloud API (paid per message) behind the same function.
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote

MESSAGES = {
    "en": ("Hello {name}, your solar quotation #{number} from {company} is ready.\n"
           "View, download the PDF or accept it here: {url}\n"
           "Reply here if you have any questions."),
    "ta": ("வணக்கம் {name}, {company} வழங்கும் உங்கள் சோலார் விலைப்புள்ளி #{number} தயாராக உள்ளது.\n"
           "பார்க்க, PDF பதிவிறக்க அல்லது ஏற்றுக்கொள்ள: {url}\n"
           "ஏதேனும் சந்தேகம் இருந்தால் இங்கே பதில் அனுப்புங்கள்."),
}


def wa_number(number: Optional[str]) -> Optional[str]:
    """10-digit Indian mobile -> 91XXXXXXXXXX (digits only, as wa.me expects)."""
    digits = "".join(ch for ch in (number or "") if ch.isdigit())
    if len(digits) == 10:
        return "91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return digits
    return None


def quotation_link(*, number: Optional[str], customer_name: str, company: str, quote_number: int, url: str,
                   lang: str = "en") -> Optional[dict]:
    wa = wa_number(number)
    if not wa:
        return None
    text = MESSAGES.get(lang, MESSAGES["en"]).format(name=customer_name.split(" ")[0] or customer_name,
                                                       number=quote_number, company=company, url=url)
    return {"number": "+" + wa, "text": text, "url": f"https://wa.me/{wa}?text={quote(text)}"}
