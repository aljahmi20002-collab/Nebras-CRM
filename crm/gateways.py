"""Payment channel registry — wallets, national remittance networks,
international gateways, card schemes and prepaid cards.

Every channel is described declaratively: the checkout UI, the validation rules
and the fee engine are all generated from this table, so adding a new provider
is a dict entry — not new code.
"""

def CH(code, name_en, name_ar, kind, **kw):
    return dict(code=code, name_en=name_en, name_ar=name_ar, kind=kind, **kw)


# kind: wallet | remittance | gateway | card | prepaid | bank | cash
CHANNELS = [
    # ---------------- Mobile wallets (Yemen + regional) ----------------
    CH("jawali", "Jawali", "جوالي", "wallet", country="YE", icon="📱",
       fields=["msisdn", "otp"], prefix=["77", "78"], fee_pct=1.0, fee_flat=0,
       currency=["YER", "USD", "SAR"], instant=True),
    CH("jaib", "Jaib", "جيب", "wallet", country="YE", icon="👛",
       fields=["msisdn", "otp"], prefix=["73", "70"], fee_pct=1.0, fee_flat=0,
       currency=["YER", "USD"], instant=True),
    CH("onecash", "ONE Cash", "ون كاش", "wallet", country="YE", icon="1️⃣",
       fields=["msisdn", "otp"], prefix=["71"], fee_pct=1.2, fee_flat=0,
       currency=["YER", "USD"], instant=True),
    CH("floosak", "Floosak", "فلوسك", "wallet", country="YE", icon="💸",
       fields=["msisdn", "otp"], prefix=["77", "73", "71", "70"], fee_pct=1.0,
       currency=["YER", "USD"], instant=True),
    CH("mfloos", "mFloos", "إم فلوس", "wallet", country="YE", icon="📲",
       fields=["msisdn", "otp"], fee_pct=1.1, currency=["YER"], instant=True),
    CH("cash_wallet", "Cash Wallet", "كاش", "wallet", country="YE", icon="💰",
       fields=["msisdn", "otp"], fee_pct=1.0, currency=["YER", "USD"], instant=True),
    CH("stcpay", "STC Pay", "إس تي سي باي", "wallet", country="SA", icon="🟣",
       fields=["msisdn", "otp"], fee_pct=1.5, currency=["SAR"], instant=True),
    CH("apple_pay", "Apple Pay", "أبل باي", "wallet", country="INTL", icon="",
       fields=["token"], fee_pct=2.4, currency=["USD", "SAR", "AED"], instant=True),
    CH("google_pay", "Google Pay", "جوجل باي", "wallet", country="INTL", icon="🅖",
       fields=["token"], fee_pct=2.4, currency=["USD", "SAR", "AED"], instant=True),

    # ---------------- National remittance / exchange networks ----------------
    CH("kuraimi", "Al-Kuraimi Islamic Bank", "بنك الكريمي", "remittance", country="YE", icon="🏦",
       fields=["beneficiary", "branch", "voucher"], fee_pct=0.5, fee_flat=2,
       currency=["YER", "USD", "SAR"], settlement_hours=4),
    CH("alamal", "Al-Amal Microfinance Bank", "بنك الأمل", "remittance", country="YE", icon="🏛️",
       fields=["beneficiary", "branch", "voucher"], fee_pct=0.6, fee_flat=2,
       currency=["YER", "USD"], settlement_hours=6),
    CH("bindowal", "Bin Dowal Exchange", "بن دول للصرافة", "remittance", country="YE", icon="🔁",
       fields=["beneficiary", "branch", "voucher"], fee_pct=0.5, fee_flat=1,
       currency=["YER", "USD", "SAR"], settlement_hours=3),
    CH("alnajm", "Al-Najm Al-Thaqib", "النجم الثاقب", "remittance", country="YE", icon="⭐",
       fields=["beneficiary", "branch", "voucher"], fee_pct=0.6, currency=["YER", "USD"],
       settlement_hours=5),
    CH("alqutaibi", "Al-Qutaibi Exchange", "القطيبي للصرافة", "remittance", country="YE", icon="🔷",
       fields=["beneficiary", "branch", "voucher"], fee_pct=0.5, currency=["YER", "USD", "SAR"],
       settlement_hours=4),
    CH("alomqy", "Al-Omqy Exchange", "العمقي للصرافة", "remittance", country="YE", icon="🔶",
       fields=["beneficiary", "branch", "voucher"], fee_pct=0.55, currency=["YER", "USD"],
       settlement_hours=6),
    CH("western_union", "Western Union", "ويسترن يونيون", "remittance", country="INTL", icon="🌍",
       fields=["beneficiary", "mtcn"], fee_pct=1.5, fee_flat=5, currency=["USD", "EUR"],
       settlement_hours=1),
    CH("moneygram", "MoneyGram", "موني جرام", "remittance", country="INTL", icon="🌐",
       fields=["beneficiary", "mtcn"], fee_pct=1.5, fee_flat=5, currency=["USD", "EUR"],
       settlement_hours=1),

    # ---------------- International gateways ----------------
    CH("stripe", "Stripe", "سترايب", "gateway", country="INTL", icon="🟦",
       fields=["card"], fee_pct=2.9, fee_flat=0.30, currency=["USD", "EUR", "GBP", "AED", "SAR"],
       webhook=True, instant=True),
    CH("paypal", "PayPal", "باي بال", "gateway", country="INTL", icon="🅿️",
       fields=["email"], fee_pct=3.49, fee_flat=0.49, currency=["USD", "EUR", "GBP"],
       webhook=True, instant=True),
    CH("tap", "Tap Payments", "تاب", "gateway", country="GCC", icon="🟢",
       fields=["card"], fee_pct=2.75, fee_flat=0.25, currency=["SAR", "AED", "KWD", "USD"],
       webhook=True, instant=True),
    CH("paytabs", "PayTabs", "باي تابس", "gateway", country="GCC", icon="🔵",
       fields=["card"], fee_pct=2.85, fee_flat=0.20, currency=["SAR", "AED", "USD", "EGP"],
       webhook=True, instant=True),
    CH("hyperpay", "HyperPay", "هايبر باي", "gateway", country="GCC", icon="⚡",
       fields=["card"], fee_pct=2.7, fee_flat=0.25, currency=["SAR", "AED", "USD"],
       webhook=True, instant=True),
    CH("checkout", "Checkout.com", "تشيك أوت", "gateway", country="INTL", icon="✔️",
       fields=["card"], fee_pct=2.6, fee_flat=0.20, currency=["USD", "EUR", "AED", "SAR"],
       webhook=True, instant=True),
    CH("myfatoorah", "MyFatoorah", "ماي فاتورة", "gateway", country="GCC", icon="🧾",
       fields=["card"], fee_pct=2.5, fee_flat=0.15, currency=["KWD", "SAR", "AED", "USD"],
       webhook=True, instant=True),
    CH("moyasar", "Moyasar", "ميسر", "gateway", country="SA", icon="🟩",
       fields=["card"], fee_pct=2.75, currency=["SAR", "USD"], webhook=True, instant=True),

    # ---------------- Card schemes ----------------
    CH("visa", "Visa", "فيزا", "card", country="INTL", icon="💳",
       fields=["card"], fee_pct=2.4, iin=["4"], length=[13, 16, 19],
       currency=["USD", "YER", "SAR", "AED", "EUR"], instant=True),
    CH("mastercard", "Mastercard", "ماستركارد", "card", country="INTL", icon="💳",
       fields=["card"], fee_pct=2.5, iin=["51", "52", "53", "54", "55", "22", "23", "24", "25", "26", "27"],
       length=[16], currency=["USD", "YER", "SAR", "AED", "EUR"], instant=True),
    CH("amex", "American Express", "أمريكان إكسبريس", "card", country="INTL", icon="💳",
       fields=["card"], fee_pct=3.5, iin=["34", "37"], length=[15],
       currency=["USD", "EUR"], instant=True),
    CH("mada", "mada", "مدى", "card", country="SA", icon="💳",
       fields=["card"], fee_pct=1.0, iin=["4", "5", "6"], length=[16],
       currency=["SAR"], instant=True),
    CH("unionpay", "UnionPay", "يونيون باي", "card", country="INTL", icon="💳",
       fields=["card"], fee_pct=2.2, iin=["62"], length=[16, 19],
       currency=["USD", "CNY"], instant=True),

    # ---------------- Prepaid ----------------
    CH("prepaid_card", "Prepaid Card", "بطاقة دفع مسبق", "prepaid", country="INTL", icon="🎴",
       fields=["card"], fee_pct=1.8, currency=["USD", "YER", "SAR"], instant=True),
    CH("scratch_card", "Scratch / Voucher Card", "كرت شحن مسبق", "prepaid", country="YE", icon="🎟️",
       fields=["voucher_pin"], fee_pct=0, currency=["YER"], instant=True),
    CH("gift_card", "Gift Card", "بطاقة هدايا", "prepaid", country="INTL", icon="🎁",
       fields=["voucher_pin"], fee_pct=0, currency=["USD", "YER"], instant=True),

    # ---------------- Offline ----------------
    CH("bank_transfer", "Bank Transfer", "حوالة بنكية", "bank", country="ALL", icon="🏦",
       fields=["beneficiary", "voucher"], fee_pct=0, fee_flat=0, currency=["ALL"],
       settlement_hours=24),
    CH("cash", "Cash", "نقداً", "cash", country="ALL", icon="💵",
       fields=[], fee_pct=0, currency=["ALL"], instant=True),
    CH("cheque", "Cheque", "شيك", "bank", country="ALL", icon="🧾",
       fields=["voucher"], fee_pct=0, currency=["ALL"], settlement_hours=72),
]

BY_CODE = {c["code"]: c for c in CHANNELS}

KINDS = {
    "wallet":     {"en": "Mobile Wallets",        "ar": "محافظ الجوال",        "icon": "📱"},
    "remittance": {"en": "Remittance Networks",   "ar": "شبكات الحوالات",      "icon": "🔁"},
    "gateway":    {"en": "Payment Gateways",      "ar": "بوابات الدفع",        "icon": "🌐"},
    "card":       {"en": "Cards",                 "ar": "البطاقات",            "icon": "💳"},
    "prepaid":    {"en": "Prepaid",               "ar": "الدفع المسبق",        "icon": "🎴"},
    "bank":       {"en": "Bank / Cheque",         "ar": "بنكي / شيك",          "icon": "🏦"},
    "cash":       {"en": "Cash",                  "ar": "نقدي",                "icon": "💵"},
}

# Field descriptors drive the checkout form
FIELD_META = {
    "msisdn":      {"en": "Mobile Number", "ar": "رقم الجوال", "type": "tel"},
    "otp":         {"en": "OTP Code", "ar": "رمز التحقق", "type": "text"},
    "card":        {"en": "Card", "ar": "البطاقة", "type": "card"},
    "token":       {"en": "Device Token", "ar": "رمز الجهاز", "type": "text"},
    "beneficiary": {"en": "Beneficiary Name", "ar": "اسم المستفيد", "type": "text"},
    "branch":      {"en": "Branch / City", "ar": "الفرع / المدينة", "type": "text"},
    "voucher":     {"en": "Transfer / Voucher No.", "ar": "رقم الحوالة / السند", "type": "text"},
    "mtcn":        {"en": "MTCN / Control No.", "ar": "رقم التحويل", "type": "text"},
    "voucher_pin": {"en": "Card PIN", "ar": "رقم الكرت السري", "type": "text"},
    "email":       {"en": "Account Email", "ar": "بريد الحساب", "type": "email"},
}


def detect_card_scheme(number: str):
    n = "".join(c for c in (number or "") if c.isdigit())
    if not n:
        return None
    best = None
    for c in CHANNELS:
        if c["kind"] != "card":
            continue
        for p in c.get("iin", []):
            if n.startswith(p) and (best is None or len(p) > best[1]):
                best = (c["code"], len(p))
    return best[0] if best else None


def compute_fee(code: str, amount: float):
    c = BY_CODE.get(code)
    if not c:
        return 0.0
    return round(amount * c.get("fee_pct", 0) / 100 + c.get("fee_flat", 0), 2)


def public_list():
    out = []
    for c in CHANNELS:
        d = {k: v for k, v in c.items()}
        d["fields_meta"] = [{"key": f, **FIELD_META.get(f, {})} for f in c.get("fields", [])]
        out.append(d)
    return {"channels": out, "kinds": KINDS}
