# -*- coding: utf-8 -*-
"""
create_pdf_docs.py
------------------
Creates 8 PDF knowledge-base documents used by the RAG system.
Requires: pip install fpdf2

Run:  python scripts/create_pdf_docs.py
Output: docs/*.pdf
"""

import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

os.makedirs("docs", exist_ok=True)

LEFT_MARGIN = 10
PAGE_WIDTH  = 190   # usable width (210 - 2*10)


class RetailPDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.doc_title = title
        self.set_margins(LEFT_MARGIN, 22, LEFT_MARGIN)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_fill_color(15, 52, 96)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 4)
        self.cell(
            0, 10, "Smart Retail Assistant - Knowledge Base",
            new_x=XPos.RIGHT, new_y=YPos.TOP
        )
        self.set_font("Helvetica", "", 9)
        self.set_xy(10, 11)
        self.cell(
            0, 5, self.doc_title,
            new_x=XPos.RIGHT, new_y=YPos.TOP
        )
        self.set_text_color(0, 0, 0)
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0, 8,
            "Page " + str(self.page_no()) + " | Smart Retail Assistant | Confidential",
            align="C"
        )

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(233, 69, 96)
        self.set_text_color(255, 255, 255)
        self.cell(
            PAGE_WIDTH, 9, "  " + title,
            new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True
        )
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(15, 52, 96)
        self.cell(
            PAGE_WIDTH, 7, title,
            new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 10)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.set_x(LEFT_MARGIN)
        self.multi_cell(PAGE_WIDTH, 6, text)
        self.ln(3)

    def bullet_list(self, items):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        bullet_w = 6
        text_w   = PAGE_WIDTH - bullet_w
        for item in items:
            # Save Y before this bullet row
            y_start = self.get_y()
            # Print bullet symbol
            self.set_x(LEFT_MARGIN)
            self.cell(bullet_w, 6, "-", new_x=XPos.RIGHT, new_y=YPos.TOP)
            # Print text — multi_cell advances Y automatically
            self.set_x(LEFT_MARGIN + bullet_w)
            self.multi_cell(text_w, 6, item)
        self.ln(2)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [PAGE_WIDTH // len(headers)] * len(headers)
        # Header row
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(220, 230, 245)
        self.set_x(LEFT_MARGIN)
        for i, h in enumerate(headers):
            self.cell(
                col_widths[i], 7, h, border=1, fill=True,
                new_x=XPos.RIGHT, new_y=YPos.TOP
            )
        self.ln()
        # Data rows
        self.set_font("Helvetica", "", 9)
        for row in rows:
            self.set_x(LEFT_MARGIN)
            for i, val in enumerate(row):
                self.cell(
                    col_widths[i], 6, str(val), border=1,
                    new_x=XPos.RIGHT, new_y=YPos.TOP
                )
            self.ln()
        self.ln(3)


# ----------------------------------------------------------------
# DOC 1 - Return & Refund Policy
# ----------------------------------------------------------------
def doc_return_policy():
    pdf = RetailPDF("Return & Refund Policy")
    pdf.add_page()

    pdf.chapter_title("Return & Refund Policy")
    pdf.body(
        "Smart Retail is committed to customer satisfaction. Our return and refund policy "
        "is designed to be fair, transparent, and easy to use. Please read the following "
        "guidelines carefully before initiating a return."
    )

    pdf.section_title("Standard Return Window")
    pdf.body(
        "Most items purchased in-store or online can be returned within 30 days of the "
        "purchase date. Items must be in their original condition, unused, and in original "
        "packaging with all accessories and documentation included."
    )

    pdf.section_title("Category-Specific Rules")
    pdf.table(
        ["Category", "Return Window", "Condition", "Notes"],
        [
            ["Electronics",  "15 days",   "Sealed/Unopened", "Must include all accessories"],
            ["Footwear",     "30 days",   "Unworn",          "Original box required"],
            ["Apparel",      "30 days",   "Unwashed/Unworn", "Tags must be attached"],
            ["Appliances",   "15 days",   "Unused",          "Original packaging required"],
            ["Sports",       "30 days",   "Unused",          "Hygiene seal intact"],
            ["Stationery",   "30 days",   "Unopened",        "Bundle must be complete"],
            ["Sale Items",   "No return", "N/A",             "Final sale - no exceptions"],
        ],
        col_widths=[35, 28, 35, 92]
    )

    pdf.section_title("How to Return")
    pdf.bullet_list([
        "In-store: Bring the item and your receipt to any Smart Retail store.",
        "Online: Log in to your account, go to Orders, select the item, click Start Return.",
        "By mail: Contact support@smartretail.com to receive a prepaid return label.",
    ])

    pdf.section_title("Refund Processing")
    pdf.body(
        "Refunds are processed within 5-7 business days after the returned item is received "
        "and inspected. Refunds are issued to the original payment method. Gift card purchases "
        "are refunded as store credit. Shipping fees are non-refundable unless the return is "
        "due to a defective or incorrect item."
    )

    pdf.section_title("Exchanges")
    pdf.body(
        "Exchanges are available for the same item in a different size or colour, subject to "
        "stock availability. To exchange, follow the same process as a return and place a new order."
    )

    pdf.section_title("Damaged or Defective Items")
    pdf.body(
        "If you receive a damaged or defective item, contact us within 48 hours of delivery. "
        "We will arrange a free return and send a replacement at no additional cost. "
        "Photos of the damage may be requested to expedite the process."
    )

    pdf.output("docs/01_Return_Refund_Policy.pdf")
    print("OK 01_Return_Refund_Policy.pdf")


# ----------------------------------------------------------------
# DOC 2 - Delivery & Shipping Guide
# ----------------------------------------------------------------
def doc_delivery():
    pdf = RetailPDF("Delivery & Shipping Guide")
    pdf.add_page()

    pdf.chapter_title("Delivery & Shipping Guide")
    pdf.body(
        "Smart Retail offers a range of delivery options to suit your needs. "
        "All orders are processed within 1 business day of placement."
    )

    pdf.section_title("Domestic Shipping Options")
    pdf.table(
        ["Service", "Delivery Time", "Cost", "Tracking"],
        [
            ["Standard Delivery",    "3-5 business days", "Free over $50 / $4.99", "Yes"],
            ["Express Delivery",     "1-2 business days", "$9.99",                  "Yes"],
            ["Same-Day Delivery",    "Same day by 8 PM",  "$14.99",                 "Yes (live)"],
            ["Store Pickup (BOPIS)", "Ready in 2 hours",  "Free",                   "SMS alert"],
            ["Locker Pickup",        "Next business day", "Free",                   "PIN code"],
        ],
        col_widths=[50, 42, 48, 50]
    )

    pdf.section_title("Same-Day Delivery Eligibility")
    pdf.body(
        "Same-day delivery is available in New York, Los Angeles, Chicago, Houston, and Phoenix. "
        "Orders must be placed before 12:00 PM local time. Items marked Same-Day Eligible "
        "in the product listing qualify for this service."
    )

    pdf.section_title("International Shipping")
    pdf.body(
        "We ship to over 50 countries. International delivery typically takes 7-14 business days. "
        "Customs duties and import taxes are the responsibility of the recipient. "
        "International orders over $150 qualify for free standard international shipping."
    )

    pdf.section_title("Order Tracking")
    pdf.body(
        "Once your order ships, you will receive a tracking number via email and SMS. "
        "Track your order at smartretail.com/track or through our mobile app. "
        "Live GPS tracking is available for same-day delivery orders."
    )

    pdf.section_title("Delivery Issues")
    pdf.bullet_list([
        "Missing package: Contact us within 7 days of the expected delivery date.",
        "Wrong item delivered: Report within 48 hours for a free replacement.",
        "Damaged in transit: Send photos to support@smartretail.com within 48 hours.",
        "Delivery to wrong address: We are not liable if the address provided was incorrect.",
    ])

    pdf.output("docs/02_Delivery_Shipping_Guide.pdf")
    print("OK 02_Delivery_Shipping_Guide.pdf")


# ----------------------------------------------------------------
# DOC 3 - Smart Rewards Loyalty Programme
# ----------------------------------------------------------------
def doc_loyalty():
    pdf = RetailPDF("Smart Rewards Loyalty Programme")
    pdf.add_page()

    pdf.chapter_title("Smart Rewards Loyalty Programme")
    pdf.body(
        "Smart Rewards is our free loyalty programme that lets you earn points on every purchase "
        "and redeem them for discounts, free products, and exclusive experiences."
    )

    pdf.section_title("How to Earn Points")
    pdf.table(
        ["Action", "Points Earned"],
        [
            ["Every $1 spent in-store or online",  "1 point"],
            ["First purchase after sign-up",        "100 bonus points"],
            ["Birthday month purchase",             "3x points"],
            ["Referring a friend (per referral)",   "50 points"],
            ["Writing a verified product review",   "10 points"],
            ["Downloading the Smart Retail app",    "25 points"],
        ],
        col_widths=[130, 60]
    )

    pdf.section_title("Membership Tiers")
    pdf.table(
        ["Tier", "Monthly Spend", "Multiplier", "Perks"],
        [
            ["Bronze",   "$0-$99",    "1x",   "Standard benefits"],
            ["Silver",   "$100-$299", "1.5x", "Free standard shipping"],
            ["Gold",     "$300-$699", "2x",   "Free express shipping + early sale access"],
            ["Platinum", "$700+",     "3x",   "All Gold perks + personal shopper + VIP events"],
        ],
        col_widths=[28, 32, 28, 102]
    )

    pdf.section_title("Redeeming Points")
    pdf.body(
        "Points can be redeemed at checkout at a rate of 100 points = $1 discount. "
        "Minimum redemption is 500 points ($5). Points cannot be used on sale items "
        "or combined with other promotional codes."
    )

    pdf.section_title("Points Expiry")
    pdf.body(
        "Points expire 12 months after the date they were earned if your account has no "
        "purchase activity. Platinum members enjoy non-expiring points as long as they "
        "maintain Platinum status."
    )

    pdf.section_title("How to Join")
    pdf.bullet_list([
        "Online: Sign up at smartretail.com/rewards - it is free and instant.",
        "In-store: Ask any team member to create your account at the register.",
        "App: Download the Smart Retail app and register in under 2 minutes.",
    ])

    pdf.output("docs/03_Smart_Rewards_Loyalty.pdf")
    print("OK 03_Smart_Rewards_Loyalty.pdf")


# ----------------------------------------------------------------
# DOC 4 - Product Warranty & Support
# ----------------------------------------------------------------
def doc_warranty():
    pdf = RetailPDF("Product Warranty & Support")
    pdf.add_page()

    pdf.chapter_title("Product Warranty & Support")
    pdf.body(
        "All products sold by Smart Retail come with a manufacturer warranty. "
        "Extended warranty plans are also available for eligible products."
    )

    pdf.section_title("Standard Warranty Coverage")
    pdf.table(
        ["Category", "Warranty Period", "Coverage"],
        [
            ["Electronics", "1 year",   "Manufacturing defects, hardware failure"],
            ["Appliances",  "1 year",   "Parts and labour for manufacturing defects"],
            ["Footwear",    "6 months", "Sole separation, stitching defects"],
            ["Sports",      "6 months", "Material and workmanship defects"],
            ["Home",        "1 year",   "Manufacturing defects"],
            ["Accessories", "3 months", "Manufacturing defects only"],
        ],
        col_widths=[40, 35, 115]
    )

    pdf.section_title("What Is NOT Covered")
    pdf.bullet_list([
        "Accidental damage (drops, spills, physical damage).",
        "Normal wear and tear.",
        "Damage caused by misuse, unauthorised repair, or modification.",
        "Cosmetic damage that does not affect functionality.",
        "Consumable parts (batteries, bulbs) unless defective at purchase.",
    ])

    pdf.section_title("Extended Warranty Plans")
    pdf.body(
        "Smart Protect extended warranty plans are available for Electronics and Appliances. "
        "Plans extend coverage by 1 or 2 additional years and include accidental damage protection. "
        "Plans must be purchased within 30 days of the original product purchase."
    )
    pdf.table(
        ["Plan", "Duration", "Accidental Damage", "Price"],
        [
            ["Smart Protect Basic",   "+1 year",  "No",  "10% of product price"],
            ["Smart Protect Plus",    "+2 years", "No",  "18% of product price"],
            ["Smart Protect Premium", "+2 years", "Yes", "25% of product price"],
        ],
        col_widths=[60, 30, 40, 60]
    )

    pdf.section_title("How to Claim Warranty")
    pdf.bullet_list([
        "Contact support@smartretail.com or call 1-800-RETAIL-1.",
        "Provide your order number, product serial number, and description of the issue.",
        "Our team will assess the claim within 2 business days.",
        "Approved claims: repair, replacement, or store credit at our discretion.",
    ])

    pdf.output("docs/04_Product_Warranty_Support.pdf")
    print("OK 04_Product_Warranty_Support.pdf")


# ----------------------------------------------------------------
# DOC 5 - Store Operations & Hours
# ----------------------------------------------------------------
def doc_store_ops():
    pdf = RetailPDF("Store Operations & Hours")
    pdf.add_page()

    pdf.chapter_title("Store Operations & Hours")

    pdf.section_title("Regular Store Hours")
    pdf.table(
        ["Day", "Opening Time", "Closing Time"],
        [
            ["Monday",    "9:00 AM",  "9:00 PM"],
            ["Tuesday",   "9:00 AM",  "9:00 PM"],
            ["Wednesday", "9:00 AM",  "9:00 PM"],
            ["Thursday",  "9:00 AM",  "9:00 PM"],
            ["Friday",    "9:00 AM",  "10:00 PM"],
            ["Saturday",  "9:00 AM",  "10:00 PM"],
            ["Sunday",    "10:00 AM", "6:00 PM"],
        ],
        col_widths=[70, 60, 60]
    )

    pdf.section_title("Store Locations")
    pdf.table(
        ["Store", "Name",      "City",        "Address",                    "Phone"],
        [
            ["S001", "Downtown",  "New York",    "123 5th Ave, NY 10001",      "212-555-0101"],
            ["S002", "Westfield", "Los Angeles", "456 Sunset Blvd, CA 90028",  "310-555-0202"],
            ["S003", "Northgate", "Chicago",     "789 Michigan Ave, IL 60601", "312-555-0303"],
            ["S004", "Eastside",  "Houston",     "321 Main St, TX 77002",      "713-555-0404"],
            ["S005", "Southpark", "Phoenix",     "654 Central Ave, AZ 85004",  "602-555-0505"],
        ],
        col_widths=[18, 24, 28, 82, 38]
    )

    pdf.section_title("Holiday Hours")
    pdf.body(
        "Store hours may vary on public holidays. Reduced hours typically apply on "
        "Thanksgiving Day, Christmas Eve, and New Year's Eve. Stores are closed on "
        "Christmas Day and New Year's Day. Check smartretail.com/hours for updates."
    )

    pdf.section_title("In-Store Services")
    pdf.bullet_list([
        "Personal Shopping: Book a 1-hour session with a dedicated stylist (Gold/Platinum members).",
        "Click & Collect (BOPIS): Order online, pick up in-store within 2 hours.",
        "Gift Wrapping: Available at all stores for $3.99 per item.",
        "Product Demos: Electronics demos available daily 11 AM - 5 PM.",
        "Recycling Drop-off: Bring old electronics for responsible recycling at any store.",
        "Alterations: Footwear and apparel alterations available at select stores.",
    ])

    pdf.section_title("Accessibility")
    pdf.body(
        "All Smart Retail stores are fully accessible. Features include wheelchair ramps, "
        "accessible fitting rooms, hearing loop systems, and large-print price tags on request. "
        "Assistance dogs are welcome in all stores."
    )

    pdf.output("docs/05_Store_Operations_Hours.pdf")
    print("OK 05_Store_Operations_Hours.pdf")


# ----------------------------------------------------------------
# DOC 6 - Promotions & Pricing Policy
# ----------------------------------------------------------------
def doc_promotions():
    pdf = RetailPDF("Promotions & Pricing Policy")
    pdf.add_page()

    pdf.chapter_title("Promotions & Pricing Policy")
    pdf.body(
        "Smart Retail runs regular promotions throughout the year. This document outlines "
        "our current promotions, pricing rules, and how to apply discounts."
    )

    pdf.section_title("Current Promotions (2024)")
    pdf.table(
        ["Promo Name",     "Period",           "Discount", "Applicable To"],
        [
            ["Summer Sale",    "Jun 1 - Jun 15",   "20% off",  "Electronics, Accessories"],
            ["Back to School", "Jul 20 - Aug 5",   "15% off",  "Sports, Footwear"],
            ["Flash Weekend",  "Aug 10 - Aug 11",  "30% off",  "All categories"],
            ["Loyalty Bonus",  "Sep 1 - Sep 30",   "10% off",  "Electronics only"],
            ["End of Season",  "Oct 15 - Oct 31",  "25% off",  "Footwear, Accessories, Home"],
        ],
        col_widths=[40, 42, 26, 82]
    )

    pdf.section_title("How to Apply Promo Codes")
    pdf.bullet_list([
        "Online: Enter the promo code in the Discount Code field at checkout.",
        "In-store: Show the promo code or loyalty app to the cashier.",
        "App: Promo codes are automatically applied when you shop via the Smart Retail app.",
    ])

    pdf.section_title("Stacking & Restrictions")
    pdf.body(
        "Only one promotional code can be applied per order. Promotions cannot be combined "
        "with loyalty point redemptions unless stated otherwise. Sale items are excluded from "
        "additional promotional discounts. Price matching is available within 7 days of purchase "
        "if the same item is found cheaper at a major competitor."
    )

    pdf.section_title("Price Match Policy")
    pdf.body(
        "We will match the price of any identical item sold by a major competitor (Amazon, "
        "Walmart, Target, Best Buy) if the item is in stock at the competitor at the time of "
        "the request. Price match requests must be made within 7 days of purchase. "
        "Marketplace sellers, auction sites, and clearance prices are excluded."
    )

    pdf.section_title("Bundle Deals")
    pdf.table(
        ["Bundle",                         "Discount"],
        [
            ["Buy any 2 Sports items",          "15% off both"],
            ["Buy any 2 Electronics items",     "10% off both"],
            ["Electronics + Accessories combo", "12% off accessories"],
            ["3+ items from same category",     "Additional 5% off"],
        ],
        col_widths=[130, 60]
    )

    pdf.output("docs/06_Promotions_Pricing_Policy.pdf")
    print("OK 06_Promotions_Pricing_Policy.pdf")


# ----------------------------------------------------------------
# DOC 7 - Payment Methods & Security
# ----------------------------------------------------------------
def doc_payment():
    pdf = RetailPDF("Payment Methods & Security")
    pdf.add_page()

    pdf.chapter_title("Payment Methods & Security")
    pdf.body(
        "Smart Retail accepts a wide range of payment methods both in-store and online. "
        "All transactions are secured with industry-standard encryption."
    )

    pdf.section_title("Accepted Payment Methods")
    pdf.table(
        ["Method",                 "In-Store", "Online", "Notes"],
        [
            ["Visa",                   "Yes", "Yes", "Credit & Debit"],
            ["Mastercard",             "Yes", "Yes", "Credit & Debit"],
            ["American Express",       "Yes", "Yes", "Credit only"],
            ["Discover",               "Yes", "Yes", "Credit & Debit"],
            ["PayPal",                 "No",  "Yes", "Online only"],
            ["Apple Pay",              "Yes", "Yes", "Tap to pay in-store"],
            ["Google Pay",             "Yes", "Yes", "Tap to pay in-store"],
            ["Smart Retail Gift Card", "Yes", "Yes", "Physical & digital"],
            ["Klarna (BNPL)",          "No",  "Yes", "Orders over $100"],
            ["Cash",                   "Yes", "No",  "In-store only"],
        ],
        col_widths=[60, 25, 25, 80]
    )

    pdf.section_title("Buy Now, Pay Later (Klarna)")
    pdf.body(
        "Klarna is available for online orders over $100. Options include: "
        "Pay in 4 (4 interest-free instalments), Pay in 30 days, or Financing (6-36 months). "
        "Klarna approval is subject to a soft credit check. Late payment fees may apply."
    )

    pdf.section_title("Gift Cards")
    pdf.body(
        "Smart Retail gift cards are available in denominations of $10, $25, $50, $100, and $200. "
        "Physical cards are available in-store. Digital gift cards are delivered by email within "
        "15 minutes of purchase. Gift cards do not expire and cannot be exchanged for cash."
    )

    pdf.section_title("Security & Fraud Protection")
    pdf.bullet_list([
        "All online transactions use 256-bit SSL encryption.",
        "We are PCI DSS Level 1 compliant - the highest level of payment security.",
        "3D Secure authentication is required for all online card payments.",
        "We never store full card numbers on our servers.",
        "Suspicious transactions are flagged and reviewed within 1 hour.",
        "Report unauthorised charges to fraud@smartretail.com immediately.",
    ])

    pdf.output("docs/07_Payment_Methods_Security.pdf")
    print("OK 07_Payment_Methods_Security.pdf")


# ----------------------------------------------------------------
# DOC 8 - Customer Support & Contact Guide
# ----------------------------------------------------------------
def doc_support():
    pdf = RetailPDF("Customer Support & Contact Guide")
    pdf.add_page()

    pdf.chapter_title("Customer Support & Contact Guide")
    pdf.body(
        "Our customer support team is here to help you 7 days a week. "
        "Choose the contact method that works best for you."
    )

    pdf.section_title("Contact Channels")
    pdf.table(
        ["Channel",      "Availability",        "Response Time", "Best For"],
        [
            ["Live Chat",    "8 AM - 10 PM daily",  "Instant",       "Quick questions, order status"],
            ["Phone",        "8 AM - 10 PM daily",  "< 3 min wait",  "Complex issues, returns"],
            ["Email",        "24/7 (monitored)",    "< 2 hours",     "Detailed queries, complaints"],
            ["In-Store",     "Store hours",         "Immediate",     "Product help, returns"],
            ["Social Media", "9 AM - 6 PM Mon-Fri", "< 4 hours",     "General enquiries"],
            ["Help Centre",  "24/7 self-service",   "Instant",       "FAQs, guides, tracking"],
        ],
        col_widths=[32, 46, 30, 82]
    )

    pdf.section_title("Contact Details")
    pdf.bullet_list([
        "Phone: 1-800-RETAIL-1 (1-800-738-2451)",
        "Email: support@smartretail.com",
        "Fraud/Security: fraud@smartretail.com",
        "Live Chat: smartretail.com (bottom-right chat icon)",
        "Help Centre: help.smartretail.com",
        "Twitter/X: @SmartRetailHelp",
    ])

    pdf.section_title("Common Issues & Self-Service")
    pdf.table(
        ["Issue",                   "Self-Service Solution"],
        [
            ["Track my order",          "smartretail.com/track - enter order number"],
            ["Cancel an order",         "Account > Orders > Cancel (within 1 hour of placing)"],
            ["Change delivery address", "Account > Orders > Edit Address (before dispatch)"],
            ["Reset password",          "Login page > Forgot Password"],
            ["Update payment method",   "Account > Payment Methods"],
            ["Download invoice",        "Account > Orders > Download Invoice"],
        ],
        col_widths=[65, 125]
    )

    pdf.section_title("Escalation Process")
    pdf.body(
        "If your issue is not resolved within 48 hours, you may request escalation to a "
        "Senior Support Specialist. Escalated cases are reviewed within 24 hours. "
        "For unresolved complaints, you may contact the Consumer Protection Agency in your state."
    )

    pdf.section_title("Feedback & Complaints")
    pdf.body(
        "We value your feedback. After every support interaction, you will receive a short "
        "satisfaction survey. Formal complaints can be submitted at smartretail.com/complaints. "
        "All complaints are acknowledged within 24 hours and resolved within 5 business days."
    )

    pdf.output("docs/08_Customer_Support_Contact.pdf")
    print("OK 08_Customer_Support_Contact.pdf")


# ----------------------------------------------------------------
# Run all
# ----------------------------------------------------------------
if __name__ == "__main__":
    print("Creating PDF knowledge base documents...")
    doc_return_policy()
    doc_delivery()
    doc_loyalty()
    doc_warranty()
    doc_store_ops()
    doc_promotions()
    doc_payment()
    doc_support()
    print("\n8 PDF documents saved to docs/")
