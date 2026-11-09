"""
Initial Catalog Seed Data for Arooj Cloth and Bedsheet Parda
Idempotent loader that initializes business categories, units, templates, and default settings.
"""

import sqlite3
import logging

logger = logging.getLogger("arooj_pos.seed")

DEFAULT_SETTINGS = [
    ("shop_name", "Arooj Cloth and Bedsheet Parda", "string", "Retail store trade name"),
    ("shop_name_urdu", "عروج کلوتھ اینڈ بیڈ شیٹ پردہ", "string", "Urdu shop name for receipts"),
    ("shop_address", "Main Commercial Market, Pakistan", "string", "Store address for receipts"),
    ("shop_phone", "+92 300 0000000 / +92 321 0000000", "string", "Contact numbers"),
    ("currency", "PKR", "string", "Default ISO currency code"),
    ("currency_symbol", "Rs. ", "string", "Currency symbol shown on POS and receipts"),
    ("receipt_paper_width", "80mm", "string", "Default thermal printer width (58mm or 80mm)"),
    ("default_printer", "Default Thermal Printer", "string", "Windows printer name"),
    ("tax_rate_percent", "0.0", "float", "Default sales tax percentage"),
    ("max_cashier_discount_percent", "10.0", "float", "Maximum discount a cashier can give without manager PIN"),
    ("manager_pin", "1234", "string", "Manager authorization PIN for price overrides and exceptions"),
    ("allow_negative_stock", "1", "int", "Whether to allow sales when on-hand stock is 0 (1=yes, 0=no)"),
    ("receipt_footer_text", "Thank you for choosing Arooj Cloth and Bedsheet Parda!\nExchange possible within 7 days with original receipt.", "string", "Receipt footer notes"),
    ("shop_logo_path", "", "string", "Path to custom uploaded shop logo image")
]

DEFAULT_UNITS = [
    ("PCS", "Piece", 0, "Pcs"),
    ("SET", "Set", 0, "Set"),
    ("PAIR", "Pair", 0, "Pr"),
    ("MTR", "Meter", 1, "Mtr"),
    ("YD", "Yard", 1, "Yd"),
    ("ROLL", "Roll / Thaan", 0, "Roll"),
    ("PACK", "Pack", 0, "Pk"),
    ("KG", "Kilogram", 1, "Kg"),
    ("GM", "Gram", 1, "Gm")
]

# (Category Code, Name, Name Urdu, Display Order, Subcategories [(Code, Name, Name Urdu)], Products [(Code, Name, UnitCode, is_fabric, [Variants])])
CATALOG_DATA = [
    (
        "RAZAI", "Razai", "رضائی", 1,
        [
            ("RZ-SGL", "Single Razai", "سنگل رضائی"),
            ("RZ-DBL", "Double Razai", "ڈبل رضائی"),
            ("RZ-KNG", "King-size Razai", "کنگ سائز رضائی"),
            ("RZ-QUN", "Queen-size Razai", "کوئین سائز رضائی"),
            ("RZ-CTN", "Cotton Razai", "کاٹن رضائی"),
            ("RZ-PLY", "Polyester-filled Razai", "پالئیےسٹر رضائی"),
            ("RZ-PRN", "Printed Razai", "پرنٹڈ رضائی"),
            ("RZ-PLN", "Plain Razai", "پلین رضائی"),
            ("RZ-LGT", "Lightweight Razai", "ہلکی رضائی"),
            ("RZ-HVY", "Heavy Razai", "بھاری رضائی"),
            ("RZ-WNT", "Winter Razai", "سردیوں کی رضائی"),
            ("RZ-OTH", "Other Razai", "دیگر رضائی")
        ],
        [
            ("RZ-001", "Single Razai - Cotton", "PCS", 0, [("Single", "Assorted", "Standard", "Cotton", "Single Bed", 0)]),
            ("RZ-002", "Double Razai - Winter Heavy", "PCS", 0, [("Double", "Assorted", "Heavy Quilted", "Polyester", "Double Bed", 0)]),
            ("RZ-003", "King-size Razai - Printed Luxury", "PCS", 0, [("King", "Floral", "Embossed", "Microfiber", "King Bed", 0)]),
            ("RZ-004", "Lightweight AC Razai", "PCS", 0, [("Single", "Multicolor", "Light Quilt", "Cotton/Poly", "Single Bed", 0)])
        ]
    ),
    (
        "KAMBAL", "Kambal", "کمبل", 2,
        [
            ("KM-SGL", "Single Kambal", "سنگل کمبل"),
            ("KM-DBL", "Double Kambal", "ڈبل کمبل"),
            ("KM-KNG", "King-size Kambal", "کنگ سائز کمبل"),
            ("KM-QUN", "Queen-size Kambal", "کوئین سائز کمبل"),
            ("KM-LGT", "Lightweight Kambal", "ہلکا کمبل"),
            ("KM-HVY", "Heavy Kambal", "بھاری کمبل"),
            ("KM-PLN", "Plain Kambal", "پلین کمبل"),
            ("KM-PRN", "Printed Kambal", "پرنٹڈ کمبل"),
            ("KM-SFT", "Soft Kambal", "سوفٹ کمبل"),
            ("KM-OTH", "Other Kambal", "دیگر کمبل")
        ],
        [
            ("KM-001", "Single Ply Soft Kambal", "PCS", 0, [("Single", "Plain Camel", "Soft Touch", "Mink", "Single", 0), ("Single", "Maroon", "Soft Touch", "Mink", "Single", 0)]),
            ("KM-002", "Double Ply Heavy Winter Kambal", "PCS", 0, [("Double", "Floral Brown", "Heavy Embossed", "Korean Mink", "Double", 0), ("King", "Royal Blue", "Heavy Embossed", "Korean Mink", "King", 0)])
        ]
    ),
    (
        "AC_KAMBAL", "AC Kambal", "اے سی کمبل", 3,
        [
            ("AC-SGL", "Single AC Kambal", "سنگل اے سی کمبل"),
            ("AC-DBL", "Double AC Kambal", "ڈبل اے سی کمبل"),
            ("AC-LGT", "Lightweight AC Kambal", "ہلکا اے سی کمبل"),
            ("AC-OTH", "Other AC Kambal", "دیگر اے سی کمبل")
        ],
        [
            ("AC-001", "Summer Breeze Single AC Kambal", "PCS", 0, [("Single", "Pastel Green", "Geometric", "Flannel", "Single", 0)]),
            ("AC-002", "Ultra-Light Double AC Kambal", "PCS", 0, [("Double", "Silver Grey", "Plain", "Coral Fleece", "Double", 0)])
        ]
    ),
    (
        "KHAIS", "Khais", "کھیس", 4,
        [
            ("KH-SGL", "Single Khais", "سنگل کھیس"),
            ("KH-DBL", "Double Khais", "ڈبل کھیس"),
            ("KH-PLN", "Plain Khais", "پلین کھیس"),
            ("KH-PRN", "Printed Khais", "پرنٹڈ کھیس"),
            ("KH-TRD", "Traditional Khais", "روایتی کھیس"),
            ("KH-OTH", "Other Khais", "دیگر کھیس")
        ],
        [
            ("KH-001", "Traditional Multani Single Khais", "PCS", 0, [("Single", "Traditional Check", "Handloom Style", "Cotton Blend", "Single Bed", 0)]),
            ("KH-002", "Heavy Double Cotton Khais", "PCS", 0, [("Double", "Striped Multi", "Dense Weave", "100% Cotton", "Double Bed", 0)])
        ]
    ),
    (
        "BEDSHEETS", "Bedsheets", "بیڈ شیٹس", 5,
        [
            ("BS-SGL", "Single Bedsheet", "سنگل بیڈ شیٹ"),
            ("BS-DBL", "Double Bedsheet", "ڈبل بیڈ شیٹ"),
            ("BS-QUN", "Queen Bedsheet", "کوئین بیڈ شیٹ"),
            ("BS-KNG", "King Bedsheet", "کنگ بیڈ شیٹ"),
            ("BS-PRN", "Printed Bedsheet", "پرنٹڈ بیڈ شیٹ"),
            ("BS-PLN", "Plain Bedsheet", "پلین بیڈ شیٹ"),
            ("BS-CTN", "Cotton Bedsheet", "کاٹن بیڈ شیٹ"),
            ("BS-SET", "Bedsheet with Pillow Covers", "بیڈ شیٹ سیٹ بمعہ تکیے"),
            ("BS-OTH", "Other Bedsheets", "دیگر بیڈ شیٹس")
        ],
        [
            ("BS-001", "Cotton King Bedsheet Set (1 Sheet + 2 Pillows)", "SET", 0, [("King", "Floral Pastel", "Printed", "Pure Cotton", "90x100 in", 0), ("King", "Geometric Blue", "Printed", "Pure Cotton", "90x100 in", 0)]),
            ("BS-002", "Single Bed Printed Sheet (1 Sheet + 1 Pillow)", "SET", 0, [("Single", "Abstract", "Printed", "Cotton Poly", "60x90 in", 0)]),
            ("BS-003", "Luxury Satin Stripe King Bed Sheet", "PCS", 0, [("King", "White Hotel Satin", "Stripe", "Percale Cotton", "100x108 in", 0)])
        ]
    ),
    (
        "BRIDAL_SETS", "Bridal Razai Sets", "برائیڈل سیٹ", 6,
        [
            ("BR-SET", "Bridal Razai Set", "برائیڈل رضائی سیٹ"),
            ("BR-DEC", "Decorative Razai Set", "ڈیکوریٹو سیٹ"),
            ("BR-EMB", "Embroidered Bedding Set", "کڑھائی والا بیڈنگ سیٹ"),
            ("BR-CUS", "Custom Bridal Set", "کسٹم برائیڈل سیٹ")
        ],
        [
            ("BR-001", "8-Piece Velvet Embroidered Bridal Set", "SET", 0, [("Bridal King", "Maroon Gold", "Zari Embroidery", "Velvet Silk", "8-Piece Complete", 0), ("Bridal King", "Emerald Green", "Zari Embroidery", "Velvet Silk", "8-Piece Complete", 0)]),
            ("BR-002", "6-Piece Luxury Silk Bridal Bedding Set", "SET", 0, [("Bridal Double", "Champagne Gold", "Cutwork", "Raw Silk", "6-Piece", 0)])
        ]
    ),
    (
        "CUSHIONS", "Cushions", "کشنز", 7,
        [
            ("CS-DEC", "Decorative Cushion", "ڈیکوریٹو کشن"),
            ("CS-PLN", "Plain Cushion", "پلین کشن"),
            ("CS-PRN", "Printed Cushion", "پرنٹڈ کشن"),
            ("CS-FLD", "Filled Cushion", "بھرا ہوا کشن"),
            ("CS-CVR", "Cushion Cover", "کشن کور"),
            ("CS-SET", "Cushion Set", "کشن سیٹ"),
            ("CS-OTH", "Other Cushions", "دیگر کشنز")
        ],
        [
            ("CS-001", "Filled Square Cushion 16x16", "PCS", 0, [("16x16 in", "White/Cream", "Plain Filled", "Microfiber/Cotton", "16x16", 450)]),
            ("CS-002", "Embroidered Velvet Cushion Cover", "PCS", 0, [("16x16 in", "Navy Blue", "Gold Thread", "Velvet", "16x16", 0), ("18x18 in", "Maroon", "Gold Thread", "Velvet", "18x18", 0)]),
            ("CS-003", "5-Piece Printed Cushion Cover Set", "SET", 0, [("Standard", "Multicolor Ethnic", "Digital Print", "Canvas Cotton", "16x16", 0)])
        ]
    ),
    (
        "KAMBAL_SETS", "Kambal Sets", "کمبل سیٹس", 8,
        [
            ("KS-SGL", "Single Kambal Set", "سنگل کمبل سیٹ"),
            ("KS-DBL", "Double Kambal Set", "ڈبل کمبل سیٹ"),
            ("KS-FAM", "Family Kambal Set", "فیملی کمبل سیٹ"),
            ("KS-CUS", "Custom Kambal Set", "کسٹم کمبل سیٹ")
        ],
        [
            ("KS-001", "Double Bed Kambal + 2 Pillow Cover Set", "SET", 0, [("Double", "Brown Embossed", "Winter Warm", "Korean Ply", "3-Piece Set", 0)])
        ]
    ),
    (
        "ABAYAS", "Abayas", "عبایاجات", 9,
        [
            ("AB-PLN", "Plain Abaya", "پلین عبایا"),
            ("AB-EMB", "Embroidered Abaya", "کڑھائی والا عبایا"),
            ("AB-PTY", "Party Wear Abaya", "پارٹی ویئر عبایا"),
            ("AB-OPN", "Open Abaya", "اوپن عبایا"),
            ("AB-CLS", "Closed Abaya", "کلوزڈ عبایا"),
            ("AB-FRO", "Front-Open Abaya", "فرنٹ اوپن عبایا"),
            ("AB-OTH", "Other Abayas", "دیگر عبایا")
        ],
        [
            ("AB-001", "Classic Black Front-Open Abaya", "PCS", 0, [("52", "Jet Black", "Front-Open", "Nida Fabric", "Length 52", 0), ("54", "Jet Black", "Front-Open", "Nida Fabric", "Length 54", 0), ("56", "Jet Black", "Front-Open", "Nida Fabric", "Length 56", 0)]),
            ("AB-002", "Embroidered Sleeve Designer Abaya with Scarf", "PCS", 0, [("54", "Black/Grey", "Sleeve Lace", "Crepe Nida", "Length 54 + Scarf", 0), ("56", "Black/Gold", "Sleeve Lace", "Crepe Nida", "Length 56 + Scarf", 0)])
        ]
    ),
    (
        "LADIES_STITCHED", "Ladies Stitched Suiting", "خواتین سلا ہوا سوٹ", 10,
        [
            ("LS-2PC", "Two-Piece Stitched Suit", "ٹو پیس سلے سوٹ"),
            ("LS-3PC", "Three-Piece Stitched Suit", "تھری پیس سلے سوٹ"),
            ("LS-CSL", "Casual Suit", "کیژول سوٹ"),
            ("LS-FRM", "Formal Suit", "فارمل سوٹ"),
            ("LS-EMB", "Embroidered Suit", "ایمبرائیڈڈ سوٹ"),
            ("LS-PRN", "Printed Suit", "پرنٹڈ سوٹ"),
            ("LS-OTH", "Other Stitched Suits", "دیگر سلے سوٹ")
        ],
        [
            ("LS-001", "Printed Lawn 2-Piece Stitched (Shirt+Trouser)", "PCS", 0, [("S", "Floral Mint", "Printed", "Lawn", "Standard S", 0), ("M", "Floral Mint", "Printed", "Lawn", "Standard M", 0), ("L", "Floral Mint", "Printed", "Lawn", "Standard L", 0)]),
            ("LS-002", "Embroidered 3-Piece Stitched (Shirt+Trouser+Dupatta)", "PCS", 0, [("M", "Peach Pink", "Neckline Zari", "Chiffon/Lawn", "Standard M", 0), ("L", "Peach Pink", "Neckline Zari", "Chiffon/Lawn", "Standard L", 0)])
        ]
    ),
    (
        "LADIES_UNSTITCHED", "Ladies Unstitched Suiting", "خواتین ان سلا کپڑا", 11,
        [
            ("LU-2PC", "Two-Piece Suit Fabric", "ٹو پیس سوٹ کپڑا"),
            ("LU-3PC", "Three-Piece Suit Fabric", "تھری پیس سوٹ کپڑا"),
            ("LU-LWN", "Lawn Fabric", "لان فیبرک"),
            ("LU-CTN", "Cotton Fabric", "کاٹن فیبرک"),
            ("LU-KHD", "Khaddar Fabric", "کھدر فیبرک"),
            ("LU-LNN", "Linen Fabric", "لینن فیبرک"),
            ("LU-EMB", "Embroidered Fabric", "ایمبرائیڈڈ فیبرک"),
            ("LU-PRN", "Printed Fabric", "پرنٹڈ فیبرک"),
            ("LU-OTH", "Other Ladies Fabric", "دیگر کپڑا")
        ],
        [
            ("LU-001", "Classic Digital Print 3-Piece Lawn Suit", "PCS", 0, [("Standard 3-Pc", "Multicolor Summer", "Digital Print", "Premium Lawn", "Shirt 3m, Trouser 2.5m, Dupatta 2.5m", 0)]),
            ("LU-002", "Winter Khaddar 3-Piece Suit", "PCS", 0, [("Standard 3-Pc", "Mustard Charcoal", "Traditional Weave", "Winter Khaddar", "Standard Cut", 0)]),
            ("LU-003", "Ladies Plain Cotton Fabric by Meter", "MTR", 1, [("Per Meter", "White/Off-white", "Plain Solid", "Cambric Cotton", "Width 40 in", 0)])
        ]
    ),
    (
        "GENTS_CLOTH", "Gents Cloth", "مردانہ کپڑا", 12,
        [
            ("GC-BRN", "Branded Suiting", "برانڈڈ سوٹنگ"),
            ("GC-BOX", "Box-Packed Suiting", "باکس پیک سوٹنگ"),
            ("GC-THN", "Suiting Thaan", "سوٹنگ تھان"),
            ("GC-UNS", "Unstitched Gents Fabric", "ان سلا مردانہ کپڑا"),
            ("GC-CTN", "Cotton Fabric", "کاٹن فیبرک"),
            ("GC-WNW", "Wash-and-Wear Fabric", "واش اینڈ ویئر"),
            ("GC-WNT", "Winter Suiting", "سردیوں کا کپڑا"),
            ("GC-OTH", "Other Gents Cloth", "دیگر مردانہ کپڑا")
        ],
        [
            ("GC-001", "Gents Box Suiting (4 Meters Cut)", "PCS", 0, [("4.0 Meters", "Off-White", "Solid Plain", "Premium Cotton Latha", "4 Meter Box", 0), ("4.0 Meters", "Sky Blue", "Solid Plain", "Wash & Wear", "4 Meter Box", 0), ("4.0 Meters", "Charcoal Grey", "Solid Plain", "Wash & Wear", "4 Meter Box", 0)]),
            ("GC-002", "Gents Fabric Thaan (Sold by Meter)", "MTR", 1, [("Cut by Meter", "Cream White", "Matte Finish", "Wash & Wear Thaan", "Bara Baza 54 in", 0), ("Cut by Meter", "Slate Black", "Matte Finish", "Wash & Wear Thaan", "Bara Baza 54 in", 0)])
        ]
    ),
    (
        "CURTAINS", "Curtains and Parda", "پردہ جات", 13,
        [
            ("CP-RDY", "Ready-Made Curtains", "ریڈی میڈ پردے"),
            ("CP-FBR", "Curtain Fabric", "پردے کا کپڑا"),
            ("CP-PLN", "Plain Parda", "پلین پردہ"),
            ("CP-PRN", "Printed Parda", "پرنٹڈ پردہ"),
            ("CP-EMB", "Embroidered Parda", "کڑھائی والا پردہ"),
            ("CP-OTH", "Other Curtains", "دیگر پردے")
        ],
        [
            ("CP-001", "Ready-Made Eyelet Curtain Ring Panel", "PCS", 0, [("7 Ft (84 in)", "Beige Cream", "Textured Weave", "Blackout Jacquard", "Width 54 in x Height 84 in", 0), ("9 Ft (108 in)", "Beige Cream", "Textured Weave", "Blackout Jacquard", "Width 54 in x Height 108 in", 0)]),
            ("CP-002", "Curtain Velvet Fabric (by Meter)", "MTR", 1, [("Per Meter", "Royal Blue", "Self Embossed", "Heavy Velvet Parda", "Width 54 in", 0)])
        ]
    ),
    (
        "SCARVES", "Scarves", "اسکارف", 14,
        [
            ("SC-PRN", "Printed Scarf", "پرنٹڈ اسکارف"),
            ("SC-PLN", "Plain Scarf", "پلین اسکارف"),
            ("SC-BRN", "Branded Scarf", "برانڈڈ اسکارف"),
            ("SC-EMB", "Embroidered Scarf", "کڑھائی والا اسکارف"),
            ("SC-OTH", "Other Scarves", "دیگر اسکارف")
        ],
        [
            ("SC-001", "Printed Silk Square Scarf", "PCS", 0, [("Square 36x36", "Turkish Floral", "Silk Satin", "Silk Blend", "36x36 in", 0)]),
            ("SC-002", "Crinkle Chiffon Plain Scarf", "PCS", 0, [("Standard", "Black", "Crinkle Texture", "Chiffon", "Standard", 0), ("Standard", "Skin Beige", "Crinkle Texture", "Chiffon", "Standard", 0)])
        ]
    ),
    (
        "STALLER", "Staller and Stoles", "سٹالر / سٹول", 15,
        [
            ("ST-PLN", "Plain Staller", "پلین سٹالر"),
            ("ST-PRN", "Printed Staller", "پرنٹڈ سٹالر"),
            ("ST-EMB", "Embroidered Staller", "کڑھائی والا سٹالر"),
            ("ST-BRN", "Branded Staller", "برانڈڈ سٹالر"),
            ("ST-OTH", "Other Stoles", "دیگر سٹول")
        ],
        [
            ("ST-001", "Viscose Printed Long Staller", "PCS", 0, [("Long 72x28", "Geometric Print", "Soft Fall", "Viscose Pashmina", "72x28 in", 0)]),
            ("ST-002", "Plain Woolen Warm Winter Stole", "PCS", 0, [("Long 80x30", "Charcoal Grey", "Fringed Borders", "Wool Cashmere Blend", "80x30 in", 0)])
        ]
    ),
    (
        "ADDITIONAL", "Additional Items", "دیگر اشیاء", 16,
        [
            ("AD-ACC", "Accessories", "لوازمات"),
            ("AD-CSC", "Cushion Covers", "کشن کورز"),
            ("AD-PLC", "Pillow Covers", "تکیہ کورز"),
            ("AD-FBM", "Fabric by Meter", "کپڑا گز / میٹر"),
            ("AD-FBY", "Fabric by Yard", "کپڑا یارڈ"),
            ("AD-BDB", "Bedding Bundles", "بیڈنگ بنڈلز"),
            ("AD-CUS", "Custom Products", "کسٹم پراڈکٹس"),
            ("AD-OTH", "Other Shop Items", "دیگر دکان کا سامان")
        ],
        [
            ("AD-001", "Pair of Quilted Pillow Covers (2 Pcs)", "SET", 0, [("Standard", "White Satin", "Quilted Zippered", "Cotton", "19x29 in", 0)]),
            ("AD-002", "Curtain Rod Bracket Set & Rings", "SET", 0, [("Standard", "Antique Brass", "Double Rod", "Metal", "Set of 2 Brackets + 20 Rings", 0)])
        ]
    )
]

def seed_database(conn: sqlite3.Connection):
    """
    Idempotently seeds units, settings, categories, subcategories, and editable product templates.
    Never overwrites existing user custom prices or stock levels.
    """
    cursor = conn.cursor()

    # 1. Seed Business Settings (INSERT OR IGNORE)
    for key, val, dtype, desc in DEFAULT_SETTINGS:
        cursor.execute("""
            INSERT OR IGNORE INTO business_settings (key, value, data_type, description)
            VALUES (?, ?, ?, ?);
        """, (key, val, dtype, desc))

    # 2. Seed Units (INSERT OR IGNORE)
    unit_map = {}
    for code, name, is_dec, sym in DEFAULT_UNITS:
        cursor.execute("""
            INSERT OR IGNORE INTO units (code, name, is_decimal, symbol)
            VALUES (?, ?, ?, ?);
        """, (code, name, is_dec, sym))
    conn.commit()

    cursor.execute("SELECT code, id FROM units;")
    for row in cursor.fetchall():
        unit_map[row[0]] = row[1]

    # 3. Seed Default Admin User if no users exist
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        import hashlib, os
        salt = os.urandom(16).hex()
        # Default first-run setup password: 'admin' (User can change immediately)
        # Using standard pbkdf2_hmac sha256
        pwd_hash = hashlib.pbkdf2_hmac("sha256", "admin".encode("utf-8"), bytes.fromhex(salt), 100000).hex()
        cursor.execute("""
            INSERT INTO users (username, full_name, role, password_hash, salt, manager_pin, is_active)
            VALUES ('admin', 'Shop Owner (Admin)', 'admin', ?, ?, '1234', 1);
        """, (pwd_hash, salt))
        logger.info("Created initial admin account (username: admin, default PIN: 1234)")

    # 4. Seed Default Walking Customer
    cursor.execute("""
        INSERT OR IGNORE INTO customers (code, name, phone, city, notes)
        VALUES ('CUST-001', 'Walk-in Customer (کاؤنٹر گاہک)', '0300-0000000', 'Local', 'Default retail walk-in customer');
    """)

    # 5. Seed Categories, Subcategories, and Templates
    for cat_code, cat_name, cat_urdu, cat_order, subcats, prods in CATALOG_DATA:
        # Check or Insert Category
        cursor.execute("SELECT id FROM categories WHERE code = ?;", (cat_code,))
        res = cursor.fetchone()
        if res:
            cat_id = res[0]
        else:
            cursor.execute("""
                INSERT INTO categories (code, name, name_urdu, display_order, is_active)
                VALUES (?, ?, ?, ?, 1);
            """, (cat_code, cat_name, cat_urdu, cat_order))
            cat_id = cursor.lastrowid

        # Subcategories
        subcat_map = {}
        sub_order = 1
        for sub_code, sub_name, sub_urdu in subcats:
            cursor.execute("SELECT id FROM subcategories WHERE category_id = ? AND code = ?;", (cat_id, sub_code))
            s_res = cursor.fetchone()
            if s_res:
                subcat_map[sub_code] = s_res[0]
            else:
                cursor.execute("""
                    INSERT INTO subcategories (category_id, code, name, name_urdu, display_order, is_active)
                    VALUES (?, ?, ?, ?, ?, 1);
                """, (cat_id, sub_code, sub_name, sub_urdu, sub_order))
                subcat_map[sub_code] = cursor.lastrowid
            sub_order += 1

        # Products & Variants
        for prod_code, prod_name, unit_code, is_fabric, variants in prods:
            cursor.execute("SELECT id FROM products WHERE code = ?;", (prod_code,))
            p_res = cursor.fetchone()
            u_id = unit_map.get(unit_code, 1)

            if not p_res:
                cursor.execute("""
                    INSERT INTO products (category_id, code, barcode, name, unit_id, is_template, is_fabric, base_cost_price, base_selling_price, is_active)
                    VALUES (?, ?, ?, ?, ?, 1, ?, 0.0, 0.0, 1);
                """, (cat_id, prod_code, prod_code, prod_name, u_id, is_fabric))
                prod_id = cursor.lastrowid

                # Create variants for this template
                v_idx = 1
                for v_size, v_color, v_design, v_fabric, v_dims, v_weight in variants:
                    v_sku = f"{prod_code}-V{v_idx:02d}"
                    cursor.execute("""
                        INSERT INTO product_variants (
                            product_id, sku, barcode, size, color, design, fabric_type, dimensions, weight_grams,
                            cost_price, selling_price, stock_quantity, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, 0.0, 0.0, 1);
                    """, (prod_id, v_sku, v_sku, v_size, v_color, v_design, v_fabric, v_dims, v_weight))
                    v_idx += 1

    conn.commit()
    logger.info("Seeding completed successfully.")
