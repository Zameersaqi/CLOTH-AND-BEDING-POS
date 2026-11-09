"""
Initial Catalog Seed Data for Arooj Cloth and Bedsheet Parda
Idempotent loader that initializes business categories, units, templates, and default settings.
Pre-populated with rich textile retail items: Kambal, AC Kambal, Razai, Gents/Ladies Suiting,
Abayas, Stoles, Cushions, Bedsheets, and Fabric Rolls.
"""

import sqlite3
import logging
from decimal import Decimal

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
    ("max_cashier_discount_percent", "15.0", "float", "Maximum discount a cashier can give without manager PIN"),
    ("manager_pin", "1234", "string", "Manager authorization PIN for price overrides and exceptions"),
    ("allow_negative_stock", "1", "int", "Whether to allow sales when on-hand stock is 0 (1=yes, 0=no)"),
    ("receipt_footer_text", "Thank you for choosing Arooj Cloth and Bedsheet Parda!\nExchange possible within 7 days with original receipt.", "string", "Receipt footer notes"),
    ("shop_logo_path", "", "string", "Path to custom uploaded shop logo image"),
    ("app_theme", "light", "string", "Application theme mode (light or dark)")
]

DEFAULT_UNITS = [
    ("PCS", "Piece", 0, "Pcs"),
    ("SET", "Set", 0, "Set"),
    ("PAIR", "Pair", 0, "Pr"),
    ("MTR", "Meter", 1, "Mtr"),
    ("YD", "Yard", 1, "Yd"),
    ("ROLL", "Roll / Thaan", 0, "Roll"),
    ("PACK", "Pack", 0, "Pk"),
    ("BOX", "Box", 0, "Box"),
    ("KG", "Kilogram", 1, "Kg"),
    ("GM", "Gram", 1, "Gm")
]

# (Category Code, Name, Name Urdu, Display Order, Subcategories [(Code, Name, Name Urdu)], Products [(Code, Name, UnitCode, is_fabric, [Variants])])
# Variants format: (size, color, design, fabric_type, dimensions, weight_grams, cost_price, selling_price, stock_qty)
CATALOG_DATA = [
    (
        "RAZAI", "Razai", "رضائی", 1,
        [
            ("RZ-SGL", "Single Razai", "سنگل رضائی"),
            ("RZ-DBL", "Double Razai", "ڈبل رضائی"),
            ("RZ-KNG", "King-size Razai", "کنگ سائز رضائی"),
            ("RZ-CTN", "Cotton Razai", "کاٹن رضائی"),
            ("RZ-WNT", "Winter Razai", "سردیوں کی رضائی"),
            ("RZ-OTH", "Other Razai", "دیگر رضائی")
        ],
        [
            ("RZ-001", "Cotton Quilted Single Razai", "PCS", 0, [
                ("Single", "Multicolor Floral", "Diamond Quilt", "Pure Cotton", "60x90 in", 1500, 1800.0, 2800.0, 24.0),
                ("Double", "Multicolor Floral", "Diamond Quilt", "Pure Cotton", "90x100 in", 2200, 2600.0, 3800.0, 16.0)
            ]),
            ("RZ-002", "Double Razai Heavy Winter", "PCS", 0, [
                ("Double", "Maroon Rose", "Heavy Quilted", "Thermal Polyfill", "90x100 in", 2800, 2600.0, 4200.0, 18.0),
                ("Single", "Navy Blue", "Heavy Quilted", "Thermal Polyfill", "60x90 in", 1800, 1900.0, 3100.0, 12.0)
            ])
        ]
    ),
    (
        "KAMBAL", "Kambal", "کمبل", 2,
        [
            ("KM-SGL", "Single Kambal", "سنگل کمبل"),
            ("KM-DBL", "Double Kambal", "ڈبل کمبل"),
            ("KM-KOR", "Korean Kambal", "کورین کمبل"),
            ("KM-HVY", "Heavy Winter Kambal", "بھاری سردیوں کا کمبل"),
            ("KM-OTH", "Other Kambal", "دیگر کمبل")
        ],
        [
            ("KM-001", "Single Ply Heavy Winter Kambal", "PCS", 0, [
                ("Single", "Camel Brown", "Embossed Flora", "Korean Acrylic Mink", "160x220 cm", 3000, 2400.0, 3600.0, 20.0),
                ("Double", "Royal Navy", "Embossed Flora", "Korean Acrylic Mink", "200x240 cm", 4000, 3200.0, 4800.0, 15.0)
            ]),
            ("KM-002", "Double Ply Heavy Korean Kambal", "PCS", 0, [
                ("Double", "Deep Wine Gold", "Heavy 3D Floral", "100% Korean Mink", "220x240 cm", 6500, 3500.0, 5500.0, 15.0),
                ("Single", "Coffee Gold", "Heavy 3D Floral", "100% Korean Mink", "160x220 cm", 4500, 2800.0, 4400.0, 10.0)
            ])
        ]
    ),
    (
        "AC_KAMBAL", "AC Kambal", "اے سی کمبل", 3,
        [
            ("AC-SGL", "Single AC Kambal", "سنگل اے سی کمبل"),
            ("AC-DBL", "Double AC Kambal", "ڈبل اے سی کمبل"),
            ("AC-LGT", "Lightweight AC Blanket", "ہلکا اے سی کمبل"),
            ("AC-QLT", "Summer AC Quilt", "سمر اے سی کوئلٹ"),
            ("AC-OTH", "Other AC Kambal", "دیگر اے سی کمبل")
        ],
        [
            ("AC-001", "Lightweight AC Blanket", "PCS", 0, [
                ("Single", "Pastel Mint", "Soft Flannel", "Micro-fleece", "60x90 in", 800, 1100.0, 1750.0, 30.0),
                ("Double", "Dusty Rose", "Soft Flannel", "Micro-fleece", "90x95 in", 1200, 1500.0, 2400.0, 25.0)
            ]),
            ("AC-002", "Summer AC Quilt", "PCS", 0, [
                ("Single", "Sky Blue Grid", "Ultrasonic Quilted", "Cotton Percale", "60x90 in", 900, 1300.0, 2100.0, 20.0),
                ("Double", "Silver Grey", "Ultrasonic Quilted", "Cotton Percale", "90x100 in", 1400, 1800.0, 2900.0, 18.0)
            ])
        ]
    ),
    (
        "KHAIS", "Khais", "کھیس", 4,
        [
            ("KH-SGL", "Single Khais", "سنگل کھیس"),
            ("KH-DBL", "Double Khais", "ڈبل کھیس"),
            ("KH-MLT", "Multani Khais", "ملتانی روایتی کھیس"),
            ("KH-OTH", "Other Khais", "دیگر کھیس")
        ],
        [
            ("KH-001", "Traditional Multani Single Khais", "PCS", 0, [
                ("Single", "Red-Black Check", "Handloom Traditional", "Cotton Blend", "60x90 in", 1200, 950.0, 1500.0, 25.0)
            ]),
            ("KH-002", "Heavy Double Cotton Khais", "PCS", 0, [
                ("Double", "Classic Multi-Stripe", "Dense Weave", "100% Pure Cotton", "90x100 in", 2200, 1600.0, 2600.0, 15.0)
            ])
        ]
    ),
    (
        "BEDSHEETS", "Bedsheets", "بیڈ شیٹس", 5,
        [
            ("BS-3PC", "Luxury 3-Piece Bedsheet", "تھری پیس بیڈ شیٹ سیٹ"),
            ("BS-BRD", "Bridal Velvet Embroidered", "برائیڈل مخمل کڑھائی سیٹ"),
            ("BS-FIT", "Fitted Bedsheets", "فٹڈ لاسٹک بیڈ شیٹ"),
            ("BS-OTH", "Other Bedsheets", "دیگر بیڈ شیٹس")
        ],
        [
            ("BS-001", "Luxury Cotton 3-Piece Bedsheet Set", "SET", 0, [
                ("King", "Floral Pastel Blue", "Digital Reactive Print", "100% Cotton Percale", "90x100 in (1 Sheet + 2 Pillows)", 1100, 1400.0, 2400.0, 35.0),
                ("King", "Geometric Charcoal", "Digital Reactive Print", "100% Cotton Percale", "90x100 in (1 Sheet + 2 Pillows)", 1100, 1400.0, 2400.0, 28.0),
                ("Single", "Ethnic Yellow", "Digital Reactive Print", "100% Cotton Percale", "60x90 in (1 Sheet + 1 Pillow)", 700, 950.0, 1600.0, 20.0)
            ]),
            ("BS-002", "Bridal Velvet Embroidered Bedsheet Set", "SET", 0, [
                ("Bridal King", "Deep Maroon Gold", "Heavy Tilla Zari Embroidery", "Micro Velvet + Silk", "8-Piece Complete Luxury Set", 4500, 5500.0, 9500.0, 6.0),
                ("Bridal King", "Emerald Green", "Heavy Tilla Zari Embroidery", "Micro Velvet + Silk", "8-Piece Complete Luxury Set", 4500, 5500.0, 9500.0, 4.0)
            ]),
            ("BS-003", "Fitted Bedsheets with Elastic Corner", "PCS", 0, [
                ("King Elastic", "Plain Cream White", "Elastic All-Round Grip", "Export Jersey Cotton", "72x78+10 in", 750, 850.0, 1450.0, 22.0),
                ("Single Elastic", "Plain Grey", "Elastic All-Round Grip", "Export Jersey Cotton", "42x78+10 in", 500, 600.0, 1050.0, 18.0)
            ])
        ]
    ),
    (
        "BRIDAL_SETS", "Bridal Sets", "برائیڈل سیٹ", 6,
        [
            ("BR-SET", "Complete Bridal Razai Set", "مکمل برائیڈل رضائی سیٹ"),
            ("BR-OTH", "Other Bridal Bedding", "دیگر برائیڈل سامان")
        ],
        [
            ("BR-001", "Royal Palace 10-Piece Bridal Bedding Set", "SET", 0, [
                ("Bridal King", "Gold Champagne", "Zari Zardozi Velvet", "Pure Velvet / Jamawar", "10-Piece Set", 6000, 8500.0, 14500.0, 4.0)
            ])
        ]
    ),
    (
        "CUSHIONS", "Cushions & Covers", "کشنز و کور", 7,
        [
            ("CS-CVR", "Cushion Covers", "کشن کور"),
            ("CS-DEC", "Decorative Chair Cushions", "ڈیکوریٹو کرسی کشن"),
            ("CS-OTH", "Other Cushions", "دیگر کشن")
        ],
        [
            ("CS-001", "Velvet Soft Cushion Covers (Pack of 5)", "PACK", 0, [
                ("16x16 in", "Assorted Jewel Tones", "Velvet with Gold Piping", "Micro-Velvet", "16x16 in (Pack of 5)", 400, 600.0, 1200.0, 25.0),
                ("18x18 in", "Maroon Gold", "Velvet with Gold Piping", "Micro-Velvet", "18x18 in (Pack of 5)", 500, 750.0, 1450.0, 15.0)
            ]),
            ("CS-002", "Decorative Chair Cushions with Ties", "PCS", 0, [
                ("Standard", "Brown Check", "Tufted Foam with Ties", "Heavy Canvas", "16x16 in", 300, 250.0, 480.0, 30.0)
            ])
        ]
    ),
    (
        "KAMBAL_SETS", "Kambal Sets", "کمبل سیٹس", 8,
        [
            ("KS-DBL", "Double Bed Kambal Set", "ڈبل بیڈ کمبل سیٹ")
        ],
        [
            ("KS-001", "Double Bed Kambal + 2 Pillow Cover Set", "SET", 0, [
                ("Double", "Brown Embossed", "Winter Warm Ply", "Korean Ply", "3-Piece Set", 3800, 3400.0, 5200.0, 12.0)
            ])
        ]
    ),
    (
        "ABAYAS", "Abayas & Stoles", "عبایاجات و اسکارف", 9,
        [
            ("AB-FRO", "Front-Open Abaya", "فرنٹ اوپن عبایا"),
            ("AB-CLS", "Closed Abaya", "کلوزڈ عبایا"),
            ("AB-OTH", "Other Abayas", "دیگر عبایا")
        ],
        [
            ("AB-001", "Front Open / Closed Abayas", "PCS", 0, [
                ("54", "Black Fancy", "Front Open with Stone Motif", "Saudi Nida", "Size 54 Length", 600, 2200.0, 3600.0, 16.0),
                ("56", "Plain Casual", "Closed Simple Flared Cut", "Korean Crepe", "Size 56 Length", 500, 1600.0, 2600.0, 20.0),
                ("52", "Black Fancy", "Front Open with Lace Work", "Saudi Nida", "Size 52 Length", 580, 2100.0, 3500.0, 10.0)
            ])
        ]
    ),
    (
        "LADIES_STITCHED", "Ladies Stitched Suiting", "خواتین سلا ہوا سوٹ", 10,
        [
            ("LS-3PC", "Ladies Stitched 3-Piece Suit", "تھری پیس سلے سوٹ"),
            ("LS-2PC", "Ladies Stitched 2-Piece Suit", "ٹو پیس سلے سوٹ")
        ],
        [
            ("LS-001", "Ladies Stitched 3-Piece Suit Set", "SET", 0, [
                ("M", "Peach Pink", "Embroidered Neckline & Hem", "Chiffon/Lawn", "Shirt+Trouser+Dupatta", 600, 2100.0, 3400.0, 18.0),
                ("L", "Pistachio Green", "Embroidered Neckline & Hem", "Chiffon/Lawn", "Shirt+Trouser+Dupatta", 600, 2100.0, 3400.0, 15.0),
                ("S", "Sky Blue", "Embroidered Neckline", "Lawn", "Shirt+Trouser+Dupatta", 580, 2000.0, 3200.0, 10.0)
            ]),
            ("LS-002", "Ladies Stitched 2-Piece Suit Set", "SET", 0, [
                ("M", "Floral Teal", "Digital Print", "Premium Lawn", "Shirt + Trouser", 450, 1400.0, 2300.0, 25.0),
                ("L", "Floral Teal", "Digital Print", "Premium Lawn", "Shirt + Trouser", 450, 1400.0, 2300.0, 20.0)
            ])
        ]
    ),
    (
        "LADIES_UNSTITCHED", "Ladies Unstitched Suiting", "خواتین ان سلا کپڑا", 11,
        [
            ("LU-LWN", "Lawn Suit Unstitched", "لان ان سلا سوٹ"),
            ("LU-VLV", "Velvet Embroidered Unstitched", "مخمل ایمبرائیڈڈ سوٹ"),
            ("LU-KRD", "Karandi Unstitched Suit", "کرنڈی ان سلا سوٹ")
        ],
        [
            ("LU-001", "Ladies Unstitched Suit Sets (Lawn)", "SET", 0, [
                ("3-Pc Cut", "Summer Floral Lawn", "Digital Print with Voile Dupatta", "90x70 Premium Lawn", "Shirt 3m, Trouser 2.5m, Dupatta 2.5m", 700, 1350.0, 2200.0, 30.0)
            ]),
            ("LU-002", "Ladies Unstitched Velvet Embroidered Suit", "SET", 0, [
                ("3-Pc Cut", "Royal Wine Velvet", "Heavy Front Thread & Zari", "Micro 5000 Velvet + Silk Dupatta", "Full 3-Piece Heavy Cut", 1200, 3400.0, 5600.0, 12.0)
            ]),
            ("LU-003", "Ladies Unstitched Karandi Suit", "SET", 0, [
                ("3-Pc Cut", "Earthy Mustard", "Self Jacquard Weave", "Pure Karandi Fabric", "Standard 3-Pc Cut", 800, 1800.0, 2900.0, 18.0)
            ])
        ]
    ),
    (
        "GENTS_CLOTH", "Gents Cloth & Suiting", "مردانہ کپڑا و سوٹنگ", 12,
        [
            ("GC-BOX", "Gents Suiting Box Pack", "باکس پیک سوٹنگ"),
            ("GC-THN", "Gents Fabric Than / Roll", "سوٹنگ تھان / گز / میٹر")
        ],
        [
            ("GC-001", "Gents Suiting Box Pack (Wash & Wear / Cotton / Boski)", "BOX", 0, [
                ("4.0 Meters Box", "Off-White", "Solid Plain Executive", "Wash & Wear Wrinkle Free", "4-Meter Box Pack", 750, 1500.0, 2500.0, 30.0),
                ("4.0 Meters Box", "Light Cream", "Solid Pure Latha", "Egyptian Cotton 100%", "4-Meter Box Pack", 900, 2200.0, 3600.0, 20.0),
                ("4.0 Meters Box", "Silk White", "Smooth Lustre", "Premium Boski Box Pack", "4-Meter Box Pack", 650, 2800.0, 4800.0, 15.0)
            ]),
            ("GC-002", "Gents Unstitched Fabric Than / Roll (Karandi / Boski / Cotton)", "MTR", 1, [
                ("Roll / Meter", "Cream White", "Matte Texture", "Boski Karandi Thaan (54 in)", "Measured in Meters/Gaz", 200, 350.0, 580.0, 120.5),
                ("Roll / Meter", "Charcoal Slate", "Crisp Finish", "Pure Cotton Thaan (40 in)", "Measured in Meters/Gaz", 180, 280.0, 450.0, 95.0)
            ])
        ]
    ),
    (
        "CURTAINS", "Curtains and Parda", "پردہ جات", 13,
        [
            ("CP-RDY", "Ready-Made Curtains", "ریڈی میڈ پردے"),
            ("CP-FBR", "Curtain Fabric by Meter", "پردے کا تھان کپڑا")
        ],
        [
            ("CP-001", "Blackout Velvet Window Curtain", "PCS", 0, [
                ("7 Ft (84 in)", "Beige Cream", "Eyelet Ring Top", "Blackout Velvet Jacquard", "54 x 84 in Panel", 1200, 1050.0, 1750.0, 40.0),
                ("9 Ft (108 in)", "Beige Cream", "Eyelet Ring Top", "Blackout Velvet Jacquard", "54 x 108 in Panel", 1500, 1350.0, 2200.0, 25.0)
            ]),
            ("CP-002", "Curtain Heavy Velvet Fabric (Than)", "MTR", 1, [
                ("Roll / Meter", "Royal Blue", "Self Embossed Floral", "Heavy Micro Velvet (54 in)", "Measured in Meters", 350, 420.0, 680.0, 85.0)
            ])
        ]
    ),
    (
        "SCARVES", "Scarves", "اسکارف", 14,
        [
            ("SC-SLK", "Silk Scarf", "سلک اسکارف")
        ],
        [
            ("SC-001", "Printed Silk Square Scarf", "PCS", 0, [
                ("Square 36x36", "Turkish Floral", "Silk Satin", "Silk Blend", "36x36 in", 100, 350.0, 650.0, 30.0)
            ])
        ]
    ),
    (
        "STALLER", "Staller & Stoles", "سٹالر / سٹول", 15,
        [
            ("ST-SLK", "Silk Stoles", "سلک سٹول"),
            ("ST-CHF", "Chiffon Stoles", "شفون سٹول"),
            ("ST-VLV", "Velvet Stoles", "مخمل سٹول")
        ],
        [
            ("ST-001", "Stoller / Stoles (Silk, Chiffon, Velvet)", "PCS", 0, [
                ("Long 72x28", "Rich Burgundy", "Soft Fall Fringe", "Velvet Winter Stole", "72x28 in", 350, 650.0, 1150.0, 25.0),
                ("Long 72x28", "Gold Champagne", "Lustrous Smooth", "Silk Satin Stole", "72x28 in", 200, 450.0, 850.0, 30.0),
                ("Long 72x28", "Jet Black", "Light Drape", "Crinkle Chiffon Stole", "72x28 in", 150, 300.0, 550.0, 35.0)
            ])
        ]
    ),
    (
        "ADDITIONAL", "Additional Items", "دیگر اشیاء", 16,
        [
            ("AD-PLC", "Pillow Covers", "تکیہ کورز"),
            ("AD-OTH", "Other Items", "دیگر سامان")
        ],
        [
            ("AD-001", "Pair of Quilted Pillow Covers (2 Pcs)", "SET", 0, [
                ("Standard Pair", "White Satin Stripe", "Quilted Zippered", "100% Cotton", "19x29 in (2 Pcs)", 300, 400.0, 750.0, 40.0)
            ])
        ]
    )
]

def seed_database(conn: sqlite3.Connection):
    """
    Idempotently seeds units, settings, categories, subcategories, products, variants,
    and initial stock records.
    Never overwrites user custom prices or existing inventory modifications.
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
        pwd_hash = hashlib.pbkdf2_hmac("sha256", "admin".encode("utf-8"), bytes.fromhex(salt), 100000).hex()
        cursor.execute("""
            INSERT INTO users (username, full_name, role, password_hash, salt, manager_pin, is_active)
            VALUES ('admin', 'Shop Owner (Admin)', 'admin', ?, ?, '1234', 1);
        """, (pwd_hash, salt))
        logger.info("Created initial admin account (username: admin, default PIN: 1234)")

    # 4. Seed Default Walking Customer
    cursor.execute("""
        INSERT OR IGNORE INTO customers (code, name, phone, city, notes)
        VALUES ('CUST-001', 'Walk-in Customer (کاؤنٹر گاہک)', '0300-0000000', 'Local Market', 'Default retail walk-in customer');
    """)

    # 5. Seed Categories, Subcategories, Products, and Variants
    # Safe guardrail: Check if this is an active store database with existing sales or completed setup
    cursor.execute("SELECT COUNT(*) FROM sales;")
    has_sales = cursor.fetchone()[0] > 0

    cursor.execute("SELECT COUNT(*) FROM products;")
    has_prods = cursor.fetchone()[0] > 0

    cursor.execute("SELECT value FROM business_settings WHERE key = 'first_run_completed';")
    fr_row = cursor.fetchone()
    is_first_run_done = (fr_row and str(fr_row[0]) == "1")

    if has_sales or (has_prods and is_first_run_done):
        logger.info(f"Active store database detected (Sales: {has_sales}, Products: {has_prods}). Preserving user custom catalog without re-seeding.")
        conn.commit()
        return

    for cat_code, cat_name, cat_urdu, cat_order, subcats, prods in CATALOG_DATA:
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

            # Determine primary cost & selling price from first variant
            if variants and len(variants[0]) >= 8:
                first_cost = variants[0][6]
                first_sale = variants[0][7]
            else:
                first_cost = 1000.0
                first_sale = 1500.0

            if not p_res:
                cursor.execute("""
                    INSERT INTO products (category_id, code, barcode, name, unit_id, is_template, is_fabric, base_cost_price, base_selling_price, is_active)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, 1);
                """, (cat_id, prod_code, prod_code, prod_name, u_id, is_fabric, first_cost, first_sale))
                prod_id = cursor.lastrowid

                # Create variants for this product
                v_idx = 1
                for v_info in variants:
                    if len(v_info) >= 9:
                        v_size, v_color, v_design, v_fabric, v_dims, v_weight, v_cost, v_sale, v_stock = v_info[:9]
                    else:
                        v_size, v_color, v_design, v_fabric, v_dims, v_weight = v_info[:6]
                        v_cost = first_cost
                        v_sale = first_sale
                        v_stock = 20.0

                    v_sku = f"{prod_code}-V{v_idx:02d}"
                    cursor.execute("""
                        INSERT INTO product_variants (
                            product_id, sku, barcode, size, color, design, fabric_type, dimensions, weight_grams,
                            cost_price, selling_price, stock_quantity, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
                    """, (prod_id, v_sku, v_sku, v_size, v_color, v_design, v_fabric, v_dims, v_weight, v_cost, v_sale, v_stock))
                    v_idx += 1

    conn.commit()
    logger.info("Arooj POS seed database successfully pre-populated.")
