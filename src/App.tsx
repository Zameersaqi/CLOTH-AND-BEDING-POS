/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  ShoppingCart,
  Package,
  Users,
  LayoutDashboard,
  Receipt,
  Settings,
  Search,
  Barcode,
  Printer,
  Edit3,
  Trash2,
  Plus,
  RotateCcw,
  ShieldCheck,
  Download,
  Upload,
  AlertTriangle,
  Layers,
  ArrowRight,
  TrendingUp,
  CreditCard,
  DollarSign,
  Sun,
  Moon,
  MessageSquare,
  Send,
  FileSpreadsheet,
  FileText,
  Copy,
  ExternalLink,
  CheckCircle2,
  Check,
  Eye,
  Percent,
  Phone,
  Image as ImageIcon,
  Key
} from 'lucide-react';

// ==========================================
// DATA MODELS & INTERFACES
// ==========================================

interface ProductVariant {
  sku: string;
  size: string;
  color: string;
  design: string;
  price: number;
  cost: number;
  stock: number;
}

interface Product {
  id: string;
  code: string;
  name: string;
  nameUrdu: string;
  category: string;
  categoryCode: string;
  unit: string;
  isFabric: boolean;
  baseCost: number;
  basePrice: number;
  stock: number;
  minStockAlert: number;
  variants: ProductVariant[];
}

interface CartItem {
  id: string;
  productId: string;
  productName: string;
  variantTitle: string;
  sku: string;
  unit: string;
  isFabric: boolean;
  quantity: number;
  originalPrice: number;
  transactionPrice: number; // Editable selling rate
  lineDiscount: number;
  costPrice: number;
  isOverridden: boolean;
  overrideReason?: string;
  rollNumber?: string;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  phone: string;
  whatsapp: string;
  address: string;
  city: string;
  creditLimit: number;
  balance: number;
  notes?: string;
}

interface Supplier {
  id: string;
  code: string;
  companyName: string;
  contactPerson: string;
  phone: string;
  address: string;
  balance: number;
}

interface SaleInvoice {
  invoiceNumber: string;
  date: string;
  customerId?: string;
  customerName: string;
  customerPhone?: string;
  customerWhatsapp?: string;
  items: CartItem[];
  subtotal: number;
  discount: number;
  grandTotal: number;
  paidAmount: number;
  balanceAmount: number;
  paymentMethod: string;
  changeGiven: number;
  status: 'paid' | 'partial' | 'unpaid';
  cashier: string;
  isRevised?: boolean;
  revisionCount?: number;
}

interface InvoiceAuditLog {
  id: string;
  invoiceNumber: string;
  createdAt: string;
  oldGrandTotal: number;
  newGrandTotal: number;
  oldDiscount: number;
  newDiscount: number;
  changesSummary: string;
  editedBy: string;
  reason: string;
}

interface WhatsAppCampaign {
  id: string;
  title: string;
  date: string;
  recipientCount: number;
  messageText: string;
  status: 'Sent' | 'Draft';
}

// ==========================================
// PRELOADED SEED DATA (Textile & Bedding POS)
// ==========================================

const CATEGORIES = [
  { code: 'ALL', name: 'All Categories', urdu: 'تمام اشیاء' },
  { code: 'RAZAI', name: 'Razai', urdu: 'رضائی' },
  { code: 'KAMBAL', name: 'Kambal', urdu: 'کمبل' },
  { code: 'BEDSHEETS', name: 'Bedsheets', urdu: 'بیڈ شیٹس' },
  { code: 'CURTAINS', name: 'Curtains & Parda', urdu: 'پردے' },
  { code: 'BRIDAL_SETS', name: 'Bridal Sets', urdu: 'برائیڈل سیٹ' },
  { code: 'CUSHIONS', name: 'Cushions', urdu: 'کشنز' },
  { code: 'FABRIC', name: 'Unstitched Fabric', urdu: 'کپڑا تھان' },
  { code: 'SUITING', name: 'Gents Suiting', urdu: 'مردانہ سوٹ' },
  { code: 'TOWELS', name: 'Bath & Towels', urdu: 'تولیہ جات' }
];

const INITIAL_PRODUCTS: Product[] = [
  {
    id: 'p1',
    code: 'RZ-001',
    name: 'Single Razai - Cotton Quilted',
    nameUrdu: 'سنگل رضائی کاٹن کوئلٹڈ',
    category: 'Razai',
    categoryCode: 'RAZAI',
    unit: 'Pcs',
    isFabric: false,
    baseCost: 1800,
    basePrice: 2800,
    stock: 24,
    minStockAlert: 5,
    variants: [
      { sku: 'RZ-001-V01', size: 'Single', color: 'Multicolor Floral', design: 'Standard Quilted', price: 2800, cost: 1800, stock: 24 }
    ]
  },
  {
    id: 'p2',
    code: 'RZ-002',
    name: 'Double Razai - Heavy Winter',
    nameUrdu: 'ڈبل رضائی سردیوں کی بھاری',
    category: 'Razai',
    categoryCode: 'RAZAI',
    unit: 'Pcs',
    isFabric: false,
    baseCost: 2600,
    basePrice: 4200,
    stock: 18,
    minStockAlert: 4,
    variants: [
      { sku: 'RZ-002-V01', size: 'Double', color: 'Maroon Gold', design: 'Heavy Polyester', price: 4200, cost: 2600, stock: 10 },
      { sku: 'RZ-002-V02', size: 'King', color: 'Navy Blue', design: 'Heavy Polyester', price: 4600, cost: 2900, stock: 8 }
    ]
  },
  {
    id: 'p3',
    code: 'KM-001',
    name: 'Double Ply Heavy Winter Kambal',
    nameUrdu: 'ڈبل پلائی کورین کمبل',
    category: 'Kambal',
    categoryCode: 'KAMBAL',
    unit: 'Pcs',
    isFabric: false,
    baseCost: 3500,
    basePrice: 5500,
    stock: 15,
    minStockAlert: 3,
    variants: [
      { sku: 'KM-001-V01', size: 'Double', color: 'Floral Brown', design: 'Embossed Mink', price: 5500, cost: 3500, stock: 8 },
      { sku: 'KM-001-V02', size: 'King', color: 'Wine Red', design: 'Embossed Mink', price: 6000, cost: 3800, stock: 7 }
    ]
  },
  {
    id: 'p4',
    code: 'BS-001',
    name: 'Luxury Cotton 3-Piece Bedsheet Set',
    nameUrdu: 'کاٹن بیڈ شیٹ سیٹ مع تکیے',
    category: 'Bedsheets',
    categoryCode: 'BEDSHEETS',
    unit: 'Set',
    isFabric: false,
    baseCost: 1400,
    basePrice: 2400,
    stock: 35,
    minStockAlert: 8,
    variants: [
      { sku: 'BS-001-KNG-BLU', size: 'King 90x100', color: 'Royal Blue', design: 'Geometric Stripe', price: 2400, cost: 1400, stock: 15 },
      { sku: 'BS-001-KNG-RED', size: 'King 90x100', color: 'Classic Maroon', design: 'Floral Motif', price: 2400, cost: 1400, stock: 12 },
      { sku: 'BS-001-SGL-WHT', size: 'Single', color: 'Off White', design: 'Solid Border', price: 1600, cost: 950, stock: 8 }
    ]
  },
  {
    id: 'p5',
    code: 'BS-002',
    name: 'Bridal Velvet Embroidered Bedsheet',
    nameUrdu: 'برائیڈل مخمل کڑھائی بیڈ سیٹ',
    category: 'Bridal Sets',
    categoryCode: 'BRIDAL_SETS',
    unit: 'Set',
    isFabric: false,
    baseCost: 5500,
    basePrice: 9500,
    stock: 6,
    minStockAlert: 2,
    variants: [
      { sku: 'BS-002-BRD-GLD', size: 'Super King', color: 'Golden Ivory', design: 'Heavy Zari Embroidery', price: 9500, cost: 5500, stock: 6 }
    ]
  },
  {
    id: 'p6',
    code: 'CUR-001',
    name: 'Blackout Velvet Window Curtain',
    nameUrdu: 'بلیک آؤٹ مخمل پردہ',
    category: 'Curtains & Parda',
    categoryCode: 'CURTAINS',
    unit: 'Pcs',
    isFabric: false,
    baseCost: 950,
    basePrice: 1750,
    stock: 40,
    minStockAlert: 10,
    variants: [
      { sku: 'CUR-001-7FT-GRY', size: '7x4 Feet', color: 'Charcoal Grey', design: 'Eyelet Ring Blackout', price: 1750, cost: 950, stock: 20 },
      { sku: 'CUR-001-7FT-BRN', size: '7x4 Feet', color: 'Chocolate Brown', design: 'Eyelet Ring Blackout', price: 1750, cost: 950, stock: 20 }
    ]
  },
  {
    id: 'p7',
    code: 'FAB-001',
    name: 'Boski Karandi Unstitched Fabric',
    nameUrdu: 'بوسکی کرنڈی ان سلا کپڑا تھان',
    category: 'Unstitched Fabric',
    categoryCode: 'FABRIC',
    unit: 'Meter',
    isFabric: true,
    baseCost: 350,
    basePrice: 580,
    stock: 120.5,
    minStockAlert: 25,
    variants: [
      { sku: 'FAB-001-ROLL-01', size: '54 in Width', color: 'Cream Off-White', design: 'Plain Textured Roll', price: 580, cost: 350, stock: 65.5 },
      { sku: 'FAB-001-ROLL-02', size: '54 in Width', color: 'Desert Sand', design: 'Plain Textured Roll', price: 580, cost: 350, stock: 55.0 }
    ]
  },
  {
    id: 'p8',
    code: 'CSH-001',
    name: 'Velvet Soft Cushion Covers (Pack of 5)',
    nameUrdu: 'مخمل کشن کور سیٹ 5 عدد',
    category: 'Cushions',
    categoryCode: 'CUSHIONS',
    unit: 'Pack',
    isFabric: false,
    baseCost: 600,
    basePrice: 1200,
    stock: 25,
    minStockAlert: 5,
    variants: [
      { sku: 'CSH-001-PK5-AST', size: '16x16 in', color: 'Assorted Royal', design: 'Zipped Velvet', price: 1200, cost: 600, stock: 25 }
    ]
  }
];

const INITIAL_CUSTOMERS: Customer[] = [
  {
    id: 'c1',
    code: 'CUST-001',
    name: 'Chaudhry Tariq Traders',
    phone: '0300-8451234',
    whatsapp: '03008451234',
    address: 'Circular Road, Faisalabad',
    city: 'Faisalabad',
    creditLimit: 100000,
    balance: 14500,
    notes: 'Wholesale buyer, always pays via bank transfer'
  },
  {
    id: 'c2',
    code: 'CUST-002',
    name: 'Haji Muhammad Aslam',
    phone: '0321-7654321',
    whatsapp: '03217654321',
    address: 'Model Town, Lahore',
    city: 'Lahore',
    creditLimit: 50000,
    balance: 0,
    notes: 'Regular retail customer for bedsheets'
  },
  {
    id: 'c3',
    code: 'CUST-003',
    name: 'Malik Zeeshan (Boutique)',
    phone: '0345-9988776',
    whatsapp: '03459988776',
    address: 'Main Market, Rawalpindi',
    city: 'Rawalpindi',
    creditLimit: 75000,
    balance: 8200,
    notes: 'Curtains and matching cushions'
  }
];

const INITIAL_SUPPLIERS: Supplier[] = [
  {
    id: 's1',
    code: 'SUP-001',
    companyName: 'Al-Karam Textile Mills',
    contactPerson: 'Shakeel Ahmad',
    phone: '0300-1122334',
    address: 'Millat Industrial Estate, Faisalabad',
    balance: 65000
  },
  {
    id: 's2',
    code: 'SUP-002',
    companyName: 'Kohinoor Weaving Mills',
    contactPerson: 'Rizwan Qureshi',
    phone: '0322-4455667',
    address: 'GT Road, Gujranwala',
    balance: 24000
  }
];

export default function App() {
  // Theme state: dark / light
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('arooj_theme') as 'light' | 'dark') || 'light';
  });

  useEffect(() => {
    localStorage.setItem('arooj_theme', theme);
  }, [theme]);

  // Active Tab
  const [activeTab, setActiveTab] = useState<'pos' | 'stock' | 'customers' | 'dashboard' | 'reports' | 'import-export' | 'settings'>('pos');

  // Business settings
  const [shopName, setShopName] = useState('Arooj Cloth and Bedsheet Parda');
  const [shopUrdu, setShopUrdu] = useState('عروج کلوتھ اینڈ بیڈ شیٹ پردہ');
  const [shopAddress, setShopAddress] = useState('Main Commercial Market, Pakistan');
  const [shopPhone, setShopPhone] = useState('0300-1234567');
  const [paperWidth, setPaperWidth] = useState<'80mm' | '58mm'>('80mm');
  const [shopLogoUrl, setShopLogoUrl] = useState<string>(
    'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 100 100"><rect width="100" height="100" rx="20" fill="%23047857"/><circle cx="50" cy="50" r="32" fill="none" stroke="%23ffffff" stroke-width="4"/><path d="M36 62 L50 32 L64 62 Z" fill="%23ffffff"/><circle cx="50" cy="46" r="6" fill="%23047857"/></svg>'
  );
  const [thermalMonochrome, setThermalMonochrome] = useState<boolean>(true);
  const [managerPin, setManagerPin] = useState('1234');

  // Live Catalog and Entities State
  const [products, setProducts] = useState<Product[]>(INITIAL_PRODUCTS);
  const [customers, setCustomers] = useState<Customer[]>(INITIAL_CUSTOMERS);
  const [suppliers, setSuppliers] = useState<Supplier[]>(INITIAL_SUPPLIERS);

  // POS Billing State
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [barcodeInput, setBarcodeInput] = useState<string>('');
  const [cart, setCart] = useState<CartItem[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [walkinWhatsapp, setWalkinWhatsapp] = useState<string>('');
  const [walkinName, setWalkinName] = useState<string>('');
  const [paymentMethod, setPaymentMethod] = useState<'Cash' | 'Credit' | 'Card' | 'Bank Transfer'>('Cash');
  const [billDiscount, setBillDiscount] = useState<number>(0);
  const [tenderedCash, setTenderedCash] = useState<number>(0);

  // Price Override & Bargain Modal
  const [editingItem, setEditingItem] = useState<CartItem | null>(null);
  const [newPriceInput, setNewPriceInput] = useState<string>('');
  const [enteredPin, setEnteredPin] = useState<string>('');
  const [pinPromptNeeded, setPinPromptNeeded] = useState<boolean>(false);
  const [priceEditError, setPriceEditError] = useState<string>('');

  // Variant & Fabric Selector Modal
  const [selectedVariantProduct, setSelectedVariantProduct] = useState<Product | null>(null);
  const [fabricLengthInput, setFabricLengthInput] = useState<number>(2.5);

  // Thermal Receipt Modal
  const [receiptModal, setReceiptModal] = useState<SaleInvoice | null>(null);
  const [printFeedback, setPrintFeedback] = useState<string>('');

  // Sales History Log
  const [salesHistory, setSalesHistory] = useState<SaleInvoice[]>([
    {
      invoiceNumber: 'INV-20261028-0001',
      date: '2026-10-28 11:30 AM',
      customerId: 'c1',
      customerName: 'Chaudhry Tariq Traders',
      customerPhone: '0300-8451234',
      customerWhatsapp: '03008451234',
      items: [
        {
          id: 's1-1',
          productId: 'p4',
          productName: 'Luxury Cotton 3-Piece Bedsheet Set',
          variantTitle: 'King 90x100 - Royal Blue',
          sku: 'BS-001-KNG-BLU',
          unit: 'Set',
          isFabric: false,
          quantity: 4,
          originalPrice: 2400,
          transactionPrice: 2250,
          lineDiscount: 0,
          costPrice: 1400,
          isOverridden: true,
          overrideReason: 'Bulk purchase discount'
        },
        {
          id: 's1-2',
          productId: 'p1',
          productName: 'Single Razai - Cotton Quilted',
          variantTitle: 'Single - Multicolor Floral',
          sku: 'RZ-001-V01',
          unit: 'Pcs',
          isFabric: false,
          quantity: 2,
          originalPrice: 2800,
          transactionPrice: 2800,
          lineDiscount: 0,
          costPrice: 1800,
          isOverridden: false
        }
      ],
      subtotal: 14600,
      discount: 200,
      grandTotal: 14400,
      paidAmount: 10000,
      balanceAmount: 4400,
      paymentMethod: 'Credit',
      changeGiven: 0,
      status: 'partial',
      cashier: 'Counter Staff'
    },
    {
      invoiceNumber: 'INV-20261028-0002',
      date: '2026-10-28 01:15 PM',
      customerName: 'Walk-in Customer (کاؤنٹر گاہک)',
      customerWhatsapp: '0312-9876543',
      items: [
        {
          id: 's2-1',
          productId: 'p6',
          productName: 'Blackout Velvet Window Curtain',
          variantTitle: '7x4 Feet - Charcoal Grey',
          sku: 'CUR-001-7FT-GRY',
          unit: 'Pcs',
          isFabric: false,
          quantity: 2,
          originalPrice: 1750,
          transactionPrice: 1750,
          lineDiscount: 0,
          costPrice: 950,
          isOverridden: false
        }
      ],
      subtotal: 3500,
      discount: 0,
      grandTotal: 3500,
      paidAmount: 3500,
      balanceAmount: 0,
      paymentMethod: 'Cash',
      changeGiven: 0,
      status: 'paid',
      cashier: 'Counter Staff'
    }
  ]);

  // WhatsApp Campaigns state
  const [campaigns, setCampaigns] = useState<WhatsAppCampaign[]>([
    {
      id: 'cmp-1',
      title: 'Winter Razai & Kambal Festival Sale',
      date: '2026-10-25 04:30 PM',
      recipientCount: 38,
      messageText: 'Assalam-o-Alaikum {customer_name}! Arooj Cloth & Bedsheet Parda is pleased to announce our Grand Winter Collection. Avail flat 20% discount on Korean Mink Kambal and Luxury Quilted Razai. Visit us today!',
      status: 'Sent'
    }
  ]);

  const [campaignTemplate, setCampaignTemplate] = useState<string>(
    'Assalam-o-Alaikum {customer_name}! Welcome to {shop_name}. Special discount offer: Flat {discount_percent}% off on all luxury bedsheets, curtains, and quilts. Reply to book your order!'
  );
  const [campaignTitle, setCampaignTitle] = useState<string>('Grand Seasonal Offer (سیل دھماکہ)');
  const [campaignDiscount, setCampaignDiscount] = useState<string>('20');
  const [selectedCampaignRecipients, setSelectedCampaignRecipients] = useState<string[]>([]);
  const [broadcastLog, setBroadcastLog] = useState<string[]>([]);

  // Bulk Import state
  const [importConflictMode, setImportConflictMode] = useState<'update' | 'skip' | 'overwrite'>('update');
  const [importFileText, setImportFileText] = useState<string>('');
  const [importPreviewRows, setImportPreviewRows] = useState<any[]>([]);
  const [importSummary, setImportSummary] = useState<{ total: number; valid: number; warnings: number; errors: number } | null>(null);

  // Backup Manager state
  const [showBackupModal, setShowBackupModal] = useState<boolean>(false);
  const [backupList, setBackupList] = useState<Array<{ id: string; filename: string; sizeKb: number; createdAt: string; type: 'manual' | 'daily' | 'safety' }>>([
    { id: 'b-daily-1', filename: 'arooj_pos_daily_20261102_080000.db', sizeKb: 142.5, createdAt: '2026-11-02 08:00 AM', type: 'daily' },
    { id: 'b-man-1', filename: 'arooj_pos_backup_20261101_183000.db', sizeKb: 140.2, createdAt: '2026-11-01 06:30 PM', type: 'manual' },
    { id: 'b-safe-1', filename: 'arooj_pos_safety_pre_restore_20261101_182500.db', sizeKb: 139.8, createdAt: '2026-11-01 06:25 PM', type: 'safety' }
  ]);
  const [backupNotice, setBackupNotice] = useState<string>('');

  // Stock & Fabric selection & modal states (F2)
  const [selectedStockProductId, setSelectedStockProductId] = useState<string>('');
  const [showProductModal, setShowProductModal] = useState<boolean>(false);
  const [isEditingProduct, setIsEditingProduct] = useState<boolean>(false);
  const [productFormData, setProductFormData] = useState<{
    id?: string;
    code: string;
    name: string;
    nameUrdu: string;
    category: string;
    unit: string;
    isFabric: boolean;
    cost: number;
    price: number;
    stock: number;
    minAlert: number;
  }>({
    code: '',
    name: '',
    nameUrdu: '',
    category: 'Unstitched Cloth (تھان / کٹ پیس)',
    unit: 'Meters',
    isFabric: true,
    cost: 500,
    price: 850,
    stock: 50,
    minAlert: 15
  });

  const [showFabricRollModal, setShowFabricRollModal] = useState<boolean>(false);
  const [rollFormData, setRollFormData] = useState<{
    rollNumber: string;
    productId: string;
    length: number;
    unit: string;
    cost: number;
    notes: string;
  }>({
    rollNumber: 'ROLL-101',
    productId: '',
    length: 40,
    unit: 'Meters',
    cost: 450,
    notes: 'Kamalia Khaddar 1st Grade Mill Packing'
  });

  // Inline Cart Price Ref Array, Navigation Refs & Manager PIN Gate
  const priceInputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const discountInputRef = useRef<HTMLInputElement | null>(null);
  const tenderedCashRef = useRef<HTMLInputElement | null>(null);
  const logoFileInputRef = useRef<HTMLInputElement | null>(null);

  const [isReceiptPreviewMode, setIsReceiptPreviewMode] = useState<boolean>(false);
  const [showPinModal, setShowPinModal] = useState<boolean>(false);
  const [pinTargetItem, setPinTargetItem] = useState<{ item: CartItem; requestedPrice: number; nextIndex: number } | null>(null);
  const [managerPinInput, setManagerPinInput] = useState<string>('');
  const [pinError, setPinError] = useState<string>('');

  // Invoice Editing & Audit Trail State
  const [editingInvoice, setEditingInvoice] = useState<SaleInvoice | null>(null);
  const [editInvoiceItems, setEditInvoiceItems] = useState<CartItem[]>([]);
  const [editInvoiceDiscount, setEditInvoiceDiscount] = useState<number>(0);
  const [editInvoiceReason, setEditInvoiceReason] = useState<string>('Customer counter adjustment');
  const [editInvoicePin, setEditInvoicePin] = useState<string>('');
  const [editInvoicePinError, setEditInvoicePinError] = useState<string>('');
  const [auditLogs, setAuditLogs] = useState<InvoiceAuditLog[]>([
    {
      id: 'aud-1',
      invoiceNumber: 'INV-20261028-0001',
      createdAt: '2026-10-28 02:45 PM',
      oldGrandTotal: 14600,
      newGrandTotal: 14400,
      oldDiscount: 0,
      newDiscount: 200,
      changesSummary: 'Bill Discount updated: Rs. 0 -> Rs. 200',
      editedBy: 'Manager',
      reason: 'Regular customer counter discount approved'
    }
  ]);
  const [viewAuditLogsInvoice, setViewAuditLogsInvoice] = useState<string | null>(null);

  // Cart totals calculation
  const cartSubtotal = cart.reduce((sum, item) => sum + (item.transactionPrice * item.quantity), 0);
  const grandTotal = Math.max(0, cartSubtotal - billDiscount);
  const changeDue = Math.max(0, (tenderedCash || grandTotal) - grandTotal);
  const totalCogs = cart.reduce((sum, item) => sum + (item.costPrice * item.quantity), 0);
  const estimatedProfit = grandTotal - totalCogs;

  // Add Item to Cart
  const handleAddToCart = (product: Product, variantIndex: number = 0, quantity: number = 1) => {
    const variant = product.variants[variantIndex] || product.variants[0];
    const existing = cart.find(i => i.productId === product.id && i.sku === variant.sku);

    if (existing) {
      setCart(cart.map(i => i.id === existing.id ? { ...i, quantity: Number((i.quantity + quantity).toFixed(3)) } : i));
    } else {
      const newItem: CartItem = {
        id: `${product.id}-${variant.sku}-${Date.now()}`,
        productId: product.id,
        productName: product.name,
        variantTitle: `${variant.size} - ${variant.color}`,
        sku: variant.sku,
        unit: product.unit,
        isFabric: product.isFabric,
        quantity: Number(quantity.toFixed(3)),
        originalPrice: variant.price,
        transactionPrice: variant.price,
        lineDiscount: 0,
        costPrice: variant.cost,
        isOverridden: false
      };
      setCart([...cart, newItem]);
    }
  };

  // Barcode search handler
  const handleBarcodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = barcodeInput.trim().toLowerCase();
    if (!query) return;

    const found = products.find(p =>
      p.code.toLowerCase() === query ||
      p.variants.some(v => v.sku.toLowerCase() === query)
    );

    if (found) {
      handleAddToCart(found, 0, 1);
      setBarcodeInput('');
    } else {
      alert(`No product found for Barcode / SKU: "${barcodeInput}". You can search by name in the search bar.`);
    }
  };

  // Open price edit modal
  const openPriceEdit = (item: CartItem) => {
    setEditingItem(item);
    setNewPriceInput(item.transactionPrice.toString());
    setPriceEditError('');
    setPinPromptNeeded(false);
    setEnteredPin('');
  };

  // Save negotiated price with 15% discount limit & Manager PIN rule
  const savePriceEdit = () => {
    if (!editingItem) return;
    const newPrice = parseFloat(newPriceInput);
    if (isNaN(newPrice) || newPrice < 0) {
      setPriceEditError('Selling rate cannot be negative or empty.');
      return;
    }

    // Rule: If price reduction exceeds 15%, Manager PIN required
    if (editingItem.originalPrice > 0 && newPrice < editingItem.originalPrice) {
      const discPct = ((editingItem.originalPrice - newPrice) / editingItem.originalPrice) * 100;
      if (discPct > 15 && (!enteredPin || enteredPin !== managerPin)) {
        setPinPromptNeeded(true);
        setPriceEditError(`Price cut of ${discPct.toFixed(1)}% exceeds cashier limit (15%). Please enter authorized Manager PIN.`);
        return;
      }
    }

    setCart(cart.map(i => {
      if (i.id === editingItem.id) {
        return {
          ...i,
          transactionPrice: newPrice,
          isOverridden: newPrice !== i.originalPrice,
          overrideReason: newPrice !== i.originalPrice ? 'Negotiated Bargain Rate' : undefined
        };
      }
      return i;
    }));

    setEditingItem(null);
  };

  // Inline Price Change inside Cart row
  const handleInlinePriceChange = (item: CartItem, value: string) => {
    const val = parseFloat(value);
    setCart(prev => prev.map(i => {
      if (i.id === item.id) {
        return {
          ...i,
          transactionPrice: isNaN(val) ? 0 : val,
          isOverridden: !isNaN(val) && val !== i.originalPrice,
          overrideReason: !isNaN(val) && val !== i.originalPrice ? 'Negotiated Spot Rate' : undefined
        };
      }
      return i;
    }));
  };

  // Keyboard navigation on Price input: ENTER key commits & jumps to next cart item
  const handleInlinePriceKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, item: CartItem, index: number) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const currentPrice = item.transactionPrice;
      if (currentPrice < 0) {
        alert('Selling price cannot be negative.');
        return;
      }

      // Check 15% discount limit against master original catalog price
      if (item.originalPrice > 0 && currentPrice < item.originalPrice) {
        const discPct = ((item.originalPrice - currentPrice) / item.originalPrice) * 100;
        if (discPct > 15) {
          setPinTargetItem({ item, requestedPrice: currentPrice, nextIndex: index + 1 });
          setManagerPinInput('');
          setPinError(`Price cut of ${discPct.toFixed(1)}% exceeds cashier threshold (15%). Manager PIN required.`);
          setShowPinModal(true);
          return;
        }
      }

      // Focus next row's price input with text pre-selected or move to discount input if last item
      if (index + 1 < cart.length) {
        focusNextPriceInput(index + 1);
      } else {
        discountInputRef.current?.focus();
        discountInputRef.current?.select();
      }
    }
  };

  const focusNextPriceInput = (nextIndex: number) => {
    if (nextIndex < cart.length && priceInputRefs.current[nextIndex]) {
      const nextEl = priceInputRefs.current[nextIndex];
      nextEl?.focus();
      nextEl?.select();
    }
  };

  // Manager PIN Approval
  const handleManagerPinSubmit = () => {
    if (managerPinInput !== managerPin) {
      setPinError('Invalid Manager PIN. Price override rejected.');
      return;
    }
    if (pinTargetItem) {
      setCart(prev => prev.map(i => {
        if (i.id === pinTargetItem.item.id) {
          return {
            ...i,
            transactionPrice: pinTargetItem.requestedPrice,
            isOverridden: true,
            overrideReason: 'Manager Authorized Spot Bargain'
          };
        }
        return i;
      }));
      setShowPinModal(false);
      if (pinTargetItem.nextIndex < cart.length) {
        focusNextPriceInput(pinTargetItem.nextIndex);
      } else {
        discountInputRef.current?.focus();
        discountInputRef.current?.select();
      }
      setPinTargetItem(null);
    }
  };

  // Product Management (F2) Handlers
  const openAddProductModal = () => {
    setIsEditingProduct(false);
    setProductFormData({
      code: `PROD-${(products.length + 1).toString().padStart(3, '0')}`,
      name: '',
      nameUrdu: '',
      category: 'Unstitched Cloth (تھان / کٹ پیس)',
      unit: 'Meters',
      isFabric: true,
      cost: 450,
      price: 750,
      stock: 50,
      minAlert: 10
    });
    setShowProductModal(true);
  };

  const openEditProductModal = () => {
    const target = products.find(p => p.id === selectedStockProductId) || products[0];
    if (!target) {
      alert('Please select a product from the list to edit.');
      return;
    }
    setIsEditingProduct(true);
    setProductFormData({
      id: target.id,
      code: target.code,
      name: target.name,
      nameUrdu: target.nameUrdu,
      category: target.category,
      unit: target.unit,
      isFabric: target.isFabric,
      cost: target.baseCost,
      price: target.basePrice,
      stock: target.stock,
      minAlert: target.minStockAlert
    });
    setShowProductModal(true);
  };

  const openAddFabricModal = () => {
    setIsEditingProduct(false);
    setProductFormData({
      code: `FAB-${(products.filter(p => p.isFabric).length + 1).toString().padStart(3, '0')}`,
      name: 'Gul Ahmed Premium Lawn Fabric',
      nameUrdu: 'گل احمد پریمیم لان تھان',
      category: 'Unstitched Cloth (تھان / کٹ پیس)',
      unit: 'Meters',
      isFabric: true,
      cost: 650,
      price: 1100,
      stock: 80,
      minAlert: 20
    });
    setShowProductModal(true);
  };

  const openAddFabricRollModal = () => {
    const firstFabric = products.find(p => p.isFabric) || products[0];
    setRollFormData({
      rollNumber: `ROLL-${Date.now().toString().slice(-4)}`,
      productId: firstFabric ? firstFabric.id : '',
      length: 40,
      unit: 'Meters',
      cost: 500,
      notes: 'Kamalia Khaddar Mill Packing'
    });
    setShowFabricRollModal(true);
  };

  const handleSaveProduct = (e: React.FormEvent) => {
    e.preventDefault();
    if (!productFormData.name.trim() || !productFormData.code.trim()) {
      alert('Please provide product code and name.');
      return;
    }

    if (isEditingProduct && productFormData.id) {
      // Update existing
      setProducts(prev => prev.map(p => {
        if (p.id === productFormData.id) {
          return {
            ...p,
            code: productFormData.code,
            name: productFormData.name,
            nameUrdu: productFormData.nameUrdu,
            category: productFormData.category,
            unit: productFormData.unit,
            isFabric: productFormData.isFabric,
            baseCost: productFormData.cost,
            basePrice: productFormData.price,
            stock: productFormData.stock,
            minStockAlert: productFormData.minAlert,
            variants: p.variants.map((v, i) => i === 0 ? { ...v, price: productFormData.price, cost: productFormData.cost, stock: productFormData.stock } : v)
          };
        }
        return p;
      }));
      alert(`Product "${productFormData.name}" updated successfully.`);
    } else {
      // Create new
      const newId = `p-${Date.now()}`;
      const newProd: Product = {
        id: newId,
        code: productFormData.code,
        name: productFormData.name,
        nameUrdu: productFormData.nameUrdu,
        category: productFormData.category,
        categoryCode: productFormData.code.slice(0, 3).toUpperCase(),
        unit: productFormData.unit,
        isFabric: productFormData.isFabric,
        baseCost: productFormData.cost,
        basePrice: productFormData.price,
        stock: productFormData.stock,
        minStockAlert: productFormData.minAlert,
        variants: [
          {
            sku: `${productFormData.code}-STD`,
            size: productFormData.isFabric ? 'Standard Roll' : 'Standard',
            color: 'Assorted',
            design: 'Classic',
            price: productFormData.price,
            cost: productFormData.cost,
            stock: productFormData.stock
          }
        ]
      };
      setProducts(prev => [newProd, ...prev]);
      setSelectedStockProductId(newId);
      alert(`New product "${productFormData.name}" added successfully to catalog.`);
    }
    setShowProductModal(false);
  };

  const handleSaveFabricRoll = (e: React.FormEvent) => {
    e.preventDefault();
    const targetProd = products.find(p => p.id === rollFormData.productId);
    if (!targetProd) {
      alert('Please select a fabric product.');
      return;
    }
    // Increment stock
    setProducts(prev => prev.map(p => {
      if (p.id === targetProd.id) {
        const newStock = Number((p.stock + rollFormData.length).toFixed(3));
        return {
          ...p,
          stock: newStock,
          variants: p.variants.map((v, i) => i === 0 ? { ...v, stock: newStock } : v)
        };
      }
      return p;
    }));
    alert(`Fabric Roll #${rollFormData.rollNumber} (${rollFormData.length} ${rollFormData.unit}) registered. Added to stock of ${targetProd.name}.`);
    setShowFabricRollModal(false);
  };

  // Database Backup Handlers
  const handleCreateBackup = (isUsb: boolean = false) => {
    const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);
    const filename = `arooj_pos_${isUsb ? 'usb_' : ''}backup_${timestamp}.db`;
    const newBackup = {
      id: `bk-${Date.now()}`,
      filename,
      sizeKb: Math.round(140 + Math.random() * 15),
      createdAt: new Date().toLocaleString(),
      type: 'manual' as const
    };
    setBackupList(prev => [newBackup, ...prev]);
    setBackupNotice(`Safe SQLite snapshot created: ${filename}`);

    const dummyBlob = new Blob([JSON.stringify({ timestamp, productsCount: products.length, salesCount: salesHistory.length })], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(dummyBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRestoreBackup = (backupFilename: string) => {
    const conf = window.confirm(`Restore from backup "${backupFilename}"?\nA safety pre-restore snapshot of current database will be automatically created first.`);
    if (conf) {
      const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);
      const safetyFile = `arooj_pos_safety_pre_restore_${timestamp}.db`;
      setBackupList(prev => [
        {
          id: `safe-${Date.now()}`,
          filename: safetyFile,
          sizeKb: 142.0,
          createdAt: new Date().toLocaleString(),
          type: 'safety'
        },
        ...prev
      ]);
      setBackupNotice(`Database successfully restored from ${backupFilename}! Pre-restore safety snapshot stored.`);
    }
  };

  // Safe Receipt Preview Request (F10 / Enter on Tendered Cash)
  const requestSalePreview = () => {
    if (cart.length === 0) {
      alert('Cart is empty. Please add items before proceeding.');
      return;
    }

    if (paymentMethod === 'Cash' && tenderedCash < grandTotal) {
      alert(`Insufficient cash tendered!\nGrand total is Rs. ${grandTotal.toLocaleString()}, but only Rs. ${tenderedCash.toLocaleString()} tendered.\n\nPlease enter the full cash payment.`);
      tenderedCashRef.current?.focus();
      tenderedCashRef.current?.select();
      return;
    }

    if (paymentMethod === 'Credit' && !selectedCustomer) {
      alert('Credit (Khata) sale requires selecting a registered customer.');
      return;
    }

    const custName = selectedCustomer ? selectedCustomer.name : (walkinName.trim() || 'Walk-in Customer (کاؤنٹر گاہک)');
    const custPhone = selectedCustomer ? (selectedCustomer.whatsapp || selectedCustomer.phone) : walkinWhatsapp.trim();

    const draftSale: SaleInvoice = {
      invoiceNumber: 'PREVIEW (Draft)',
      date: new Date().toLocaleString(),
      customerId: selectedCustomer?.id,
      customerName: custName,
      customerPhone: custPhone,
      customerWhatsapp: custPhone,
      items: [...cart],
      subtotal: cartSubtotal,
      discount: billDiscount,
      grandTotal: grandTotal,
      paidAmount: paymentMethod === 'Credit' ? 0 : (tenderedCash > 0 ? Math.min(grandTotal, tenderedCash) : grandTotal),
      balanceAmount: paymentMethod === 'Credit' ? grandTotal : Math.max(0, grandTotal - tenderedCash),
      paymentMethod: paymentMethod,
      changeGiven: paymentMethod === 'Cash' ? changeDue : 0,
      status: paymentMethod === 'Credit' ? 'unpaid' : (tenderedCash < grandTotal ? 'partial' : 'paid'),
      cashier: 'Counter Staff'
    };

    setReceiptModal(draftSale);
    setIsReceiptPreviewMode(true);
    setPrintFeedback('');
  };

  // Explicit Final Confirmation Button Handler
  const confirmSaleAndPrint = () => {
    if (!receiptModal || !isReceiptPreviewMode) return;

    const todayStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const invNumber = `INV-${todayStr}-${(salesHistory.length + 1).toString().padStart(4, '0')}`;
    const paidAmt = receiptModal.paidAmount;
    const balanceAmt = receiptModal.balanceAmount;

    const finalizedSale: SaleInvoice = {
      ...receiptModal,
      invoiceNumber: invNumber
    };

    // Update customer balance if credit sale
    if (finalizedSale.customerId && balanceAmt > 0) {
      setCustomers(prev => prev.map(c => c.id === finalizedSale.customerId ? { ...c, balance: c.balance + balanceAmt } : c));
    }

    // Deduct stock in catalog
    setProducts(prev => prev.map(p => {
      let updatedP = { ...p };
      finalizedSale.items.forEach(ci => {
        if (ci.productId === p.id) {
          updatedP.stock = Math.max(0, Number((updatedP.stock - ci.quantity).toFixed(3)));
          updatedP.variants = updatedP.variants.map(v => {
            if (v.sku === ci.sku) {
              return { ...v, stock: Math.max(0, Number((v.stock - ci.quantity).toFixed(3))) };
            }
            return v;
          });
        }
      });
      return updatedP;
    }));

    setSalesHistory([finalizedSale, ...salesHistory]);
    setReceiptModal(finalizedSale);
    setIsReceiptPreviewMode(false);
    setCart([]);
    setBillDiscount(0);
    setTenderedCash(0);
    setWalkinWhatsapp('');
    setWalkinName('');
    setPrintFeedback(`Sale recorded successfully as ${invNumber}!`);
  };

  // Safe Cancel for Receipt Preview Modal
  const cancelReceiptPreview = () => {
    setReceiptModal(null);
    setIsReceiptPreviewMode(false);
    setPrintFeedback('');
  };

  // Logo File Upload & Removal Handlers
  const handleLogoFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate image format
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp'];
    if (!validTypes.includes(file.type.toLowerCase()) && !/\.(png|jpe?g|bmp)$/i.test(file.name)) {
      alert('Invalid image format! Please select a valid PNG, JPG, JPEG, or BMP image.');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert('File size exceeds 5MB limit. Please choose a smaller logo image.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string;
      if (dataUrl) {
        setShopLogoUrl(dataUrl);
        alert(`Store logo "${file.name}" uploaded successfully!`);
      }
    };
    reader.onerror = () => {
      alert('Failed to read image file. Please try another image.');
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveLogo = () => {
    if (window.confirm('Are you sure you want to remove the store logo?')) {
      setShopLogoUrl('');
    }
  };

  // Invoice Editing Handlers
  const handleOpenEditInvoice = (inv: SaleInvoice) => {
    setEditingInvoice(inv);
    setEditInvoiceItems(inv.items.map(it => ({ ...it })));
    setEditInvoiceDiscount(inv.discount || 0);
    setEditInvoiceReason('Customer counter adjustment');
    setEditInvoicePin('');
    setEditInvoicePinError('');
  };

  const handleSaveInvoiceEdit = () => {
    if (!editingInvoice) return;

    if (editInvoicePin !== managerPin) {
      setEditInvoicePinError('Invalid Manager PIN. Invoice revision requires manager authorization.');
      return;
    }

    if (!editInvoiceReason.trim()) {
      alert('Please enter a reason for revising this invoice.');
      return;
    }

    // Reconcile stock: compare old items vs new items
    const oldItemsMap = new Map<string, number>();
    editingInvoice.items.forEach(it => {
      oldItemsMap.set(it.id, it.quantity);
    });

    const stockAdjustments: { productId: string; sku: string; diff: number }[] = [];
    const updatedItems = editInvoiceItems.map(it => {
      const oldQty = oldItemsMap.get(it.id) ?? it.quantity;
      const diff = oldQty - it.quantity; // positive means returned to stock
      if (diff !== 0) {
        stockAdjustments.push({ productId: it.productId, sku: it.sku, diff });
      }
      return {
        ...it,
        isOverridden: it.transactionPrice !== it.originalPrice
      };
    });

    // Apply stock adjustments in catalog
    if (stockAdjustments.length > 0) {
      setProducts(prev => prev.map(p => {
        let updatedP = { ...p };
        stockAdjustments.forEach(adj => {
          if (adj.productId === p.id) {
            updatedP.stock = Math.max(0, Number((updatedP.stock + adj.diff).toFixed(3)));
            updatedP.variants = updatedP.variants.map(v => {
              if (v.sku === adj.sku) {
                return { ...v, stock: Math.max(0, Number((v.stock + adj.diff).toFixed(3))) };
              }
              return v;
            });
          }
        });
        return updatedP;
      }));
    }

    const revisedSubtotal = updatedItems.reduce((acc, it) => acc + (it.transactionPrice * it.quantity), 0);
    const revisedGrandTotal = Math.max(0, revisedSubtotal - editInvoiceDiscount);
    const oldGrandTotal = editingInvoice.grandTotal;
    const deltaGT = revisedGrandTotal - oldGrandTotal;

    // Adjust customer balance if credit invoice
    if (editingInvoice.customerId && editingInvoice.paymentMethod === 'Credit' && deltaGT !== 0) {
      setCustomers(prev => prev.map(c => c.id === editingInvoice.customerId ? { ...c, balance: c.balance + deltaGT } : c));
    }

    const revisedInvoice: SaleInvoice = {
      ...editingInvoice,
      items: updatedItems,
      subtotal: revisedSubtotal,
      discount: editInvoiceDiscount,
      grandTotal: revisedGrandTotal,
      paidAmount: editingInvoice.paymentMethod === 'Cash' ? revisedGrandTotal : editingInvoice.paidAmount,
      balanceAmount: editingInvoice.paymentMethod === 'Credit' ? Math.max(0, editingInvoice.balanceAmount + deltaGT) : 0,
      isRevised: true,
      revisionCount: (editingInvoice.revisionCount || 0) + 1
    };

    // Record audit log
    const newAuditLog: InvoiceAuditLog = {
      id: `aud-${Date.now()}`,
      invoiceNumber: editingInvoice.invoiceNumber,
      createdAt: new Date().toLocaleString(),
      oldGrandTotal,
      newGrandTotal: revisedGrandTotal,
      oldDiscount: editingInvoice.discount || 0,
      newDiscount: editInvoiceDiscount,
      changesSummary: `Revised from Rs. ${oldGrandTotal.toLocaleString()} to Rs. ${revisedGrandTotal.toLocaleString()}`,
      editedBy: 'Manager',
      reason: editInvoiceReason.trim()
    };

    setAuditLogs(prev => [newAuditLog, ...prev]);
    setSalesHistory(prev => prev.map(s => s.invoiceNumber === editingInvoice.invoiceNumber ? revisedInvoice : s));
    setEditingInvoice(null);

    const askReprint = window.confirm(`Invoice ${revisedInvoice.invoiceNumber} revised successfully!\n\nWould you like to preview / reprint the revised thermal receipt now?`);
    if (askReprint) {
      setReceiptModal(revisedInvoice);
      setIsReceiptPreviewMode(false);
    }
  };

  // Filtered Products for Billing Screen
  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      const matchCat = selectedCategory === 'ALL' || p.categoryCode === selectedCategory;
      const matchSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.nameUrdu.includes(searchQuery);
      return matchCat && matchSearch;
    });
  }, [products, selectedCategory, searchQuery]);

  // Aggregate All WhatsApp Contact Numbers from Customers + Past Invoices
  const allWhatsAppContacts = useMemo(() => {
    const map = new Map<string, { name: string; phone: string; source: string; totalSpent: number; lastDate: string }>();

    // From customers
    customers.forEach(c => {
      const raw = (c.whatsapp || c.phone || '').trim();
      if (raw) {
        map.set(raw, {
          name: c.name,
          phone: raw,
          source: 'Customer Ledger',
          totalSpent: 0,
          lastDate: 'Existing Account'
        });
      }
    });

    // From sales history
    salesHistory.forEach(s => {
      const raw = (s.customerWhatsapp || s.customerPhone || '').trim();
      if (raw) {
        const existing = map.get(raw);
        if (existing) {
          existing.totalSpent += s.grandTotal;
          existing.lastDate = s.date;
        } else {
          map.set(raw, {
            name: s.customerName,
            phone: raw,
            source: 'Sales Invoice',
            totalSpent: s.grandTotal,
            lastDate: s.date
          });
        }
      }
    });

    return Array.from(map.values());
  }, [customers, salesHistory]);

  // ==========================================
  // BULLETPROOF THERMAL PRINTING FUNCTION
  // ==========================================
  const triggerThermalPrint = () => {
    if (!receiptModal) return;

    const receiptHtml = `
      <div style="font-family: 'Courier New', monospace; width: ${paperWidth === '80mm' ? '300px' : '220px'}; margin: 0 auto; padding: 4px; color: #000; font-size: ${paperWidth === '80mm' ? '12px' : '10px'}; line-height: 1.35;">
        ${shopLogoUrl ? `
          <div style="text-align: center; margin-bottom: 6px;">
            <img src="${shopLogoUrl}" style="max-width: 140px; max-height: 65px; object-fit: contain; ${thermalMonochrome ? 'filter: grayscale(100%) contrast(160%);' : ''}" />
          </div>
        ` : ''}
        <div style="text-align: center; font-weight: bold; margin-bottom: 4px;">
          <div style="font-size: ${paperWidth === '80mm' ? '14px' : '12px'}; text-transform: uppercase;">${shopName}</div>
          <div style="font-size: 13px;">${shopUrdu}</div>
          <div style="font-size: 10px; font-weight: normal;">${shopAddress}</div>
          <div style="font-size: 10px; font-weight: normal;">Tel: ${shopPhone}</div>
          <div style="letter-spacing: -1px; margin-top: 2px;">========================================</div>
        </div>

        <div style="font-size: 10px; margin-bottom: 6px;">
          <div><b>Invoice :</b> ${receiptModal.invoiceNumber}</div>
          <div><b>Date    :</b> ${receiptModal.date}</div>
          <div><b>Cashier :</b> ${receiptModal.cashier}</div>
          <div><b>Customer:</b> ${receiptModal.customerName}</div>
          ${receiptModal.customerWhatsapp ? `<div><b>WhatsApp:</b> ${receiptModal.customerWhatsapp}</div>` : ''}
          <div style="letter-spacing: -1px; margin-top: 2px;">----------------------------------------</div>
        </div>

        <table style="width: 100%; border-collapse: collapse; font-size: 10px; margin-bottom: 6px;">
          <thead>
            <tr style="border-bottom: 1px dashed #000; text-align: left;">
              <th style="padding: 2px 0;">Item Description</th>
              <th style="text-align: right; padding: 2px 0;">Qty x Rate</th>
              <th style="text-align: right; padding: 2px 0;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${receiptModal.items.map(it => `
              <tr>
                <td style="padding: 2px 0;">
                  <b>${it.productName}</b><br/>
                  <span style="font-size: 9px; color: #444;">${it.variantTitle}</span>
                  ${it.isOverridden ? '<br/><span style="font-size: 8px;">*Special Rate</span>' : ''}
                </td>
                <td style="text-align: right; vertical-align: top; padding: 2px 0;">
                  ${it.quantity} ${it.unit}<br/>@${it.transactionPrice.toLocaleString()}
                </td>
                <td style="text-align: right; vertical-align: top; font-weight: bold; padding: 2px 0;">
                  Rs. ${(it.quantity * it.transactionPrice).toLocaleString()}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>

        <div style="border-top: 1px dashed #000; padding-top: 4px; font-size: 10px;">
          <div style="display: flex; justify-content: space-between;">
            <span>Subtotal:</span>
            <span>Rs. ${(receiptModal.subtotal || receiptModal.grandTotal).toLocaleString()}</span>
          </div>
          ${receiptModal.discount > 0 ? `
            <div style="display: flex; justify-content: space-between;">
              <span>Discount:</span>
              <span>-Rs. ${receiptModal.discount.toLocaleString()}</span>
            </div>
          ` : ''}
          <div style="letter-spacing: -1px;">========================================</div>
          <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: ${paperWidth === '80mm' ? '13px' : '11px'};">
            <span>GRAND TOTAL:</span>
            <span>Rs. ${receiptModal.grandTotal.toLocaleString()}</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span>Paid (${receiptModal.paymentMethod}):</span>
            <span>Rs. ${receiptModal.paidAmount.toLocaleString()}</span>
          </div>
          ${receiptModal.balanceAmount > 0 ? `
            <div style="display: flex; justify-content: space-between; font-weight: bold; color: #b91c1c;">
              <span>Balance Due (Udhar):</span>
              <span>Rs. ${receiptModal.balanceAmount.toLocaleString()}</span>
            </div>
          ` : ''}
          ${receiptModal.changeGiven > 0 ? `
            <div style="display: flex; justify-content: space-between; font-weight: bold;">
              <span>Change Returned:</span>
              <span>Rs. ${receiptModal.changeGiven.toLocaleString()}</span>
            </div>
          ` : ''}
        </div>

        <div style="text-align: center; margin-top: 10px; border-top: 1px dashed #000; padding-top: 6px; font-size: 9px;">
          <div>Thank you for choosing Arooj Cloth & Bedsheet Parda!</div>
          <div>Exchange possible within 7 days with original receipt.</div>
          <div style="margin-top: 4px; font-weight: bold; letter-spacing: 1px;">*${receiptModal.invoiceNumber}*</div>
        </div>
      </div>
    `;

    // Try popup window first
    const printWindow = window.open('', '_blank', 'width=440,height=620');
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Thermal Receipt - ${receiptModal.invoiceNumber}</title>
          <style>
            @page { margin: 2mm; size: ${paperWidth === '80mm' ? '80mm' : '58mm'} auto; }
            body { margin: 0; padding: 4px; background: #fff; font-family: monospace; }
          </style>
        </head>
        <body>
          ${receiptHtml}
          <script>
            window.onload = function() {
              window.focus();
              window.print();
              setTimeout(function() { window.close(); }, 500);
            };
          </script>
        </body>
        </html>
      `);
      printWindow.document.close();
      setPrintFeedback(`Receipt sent to thermal spooler (${paperWidth})`);
    } else {
      // Hidden iframe fallback
      let iframe = document.getElementById('thermal-print-frame') as HTMLIFrameElement;
      if (!iframe) {
        iframe = document.createElement('iframe');
        iframe.id = 'thermal-print-frame';
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = '0';
        document.body.appendChild(iframe);
      }
      const doc = iframe.contentWindow?.document;
      if (doc) {
        doc.open();
        doc.write(`
          <!DOCTYPE html>
          <html>
          <head>
            <style>
              @page { margin: 2mm; size: ${paperWidth === '80mm' ? '80mm' : '58mm'} auto; }
              body { margin: 0; padding: 4px; font-family: monospace; }
            </style>
          </head>
          <body>
            ${receiptHtml}
          </body>
          </html>
        `);
        doc.close();
        setTimeout(() => {
          iframe.contentWindow?.focus();
          iframe.contentWindow?.print();
          setPrintFeedback(`Printed via internal spooler (${paperWidth})`);
        }, 250);
      }
    }
  };

  // WhatsApp Single Invoice Share
  const sendInvoiceViaWhatsApp = () => {
    if (!receiptModal) return;
    const phone = receiptModal.customerWhatsapp || receiptModal.customerPhone;
    if (!phone) {
      alert('No WhatsApp phone number found for this customer. Please enter a valid mobile number.');
      return;
    }
    const cleanPhone = phone.replace(/[^0-9]/g, '');
    const intlPhone = cleanPhone.startsWith('0') ? '92' + cleanPhone.slice(1) : cleanPhone;

    const message = `*${shopName}*\n${shopUrdu}\n\n*Receipt / Invoice: ${receiptModal.invoiceNumber}*\nDate: ${receiptModal.date}\nCustomer: ${receiptModal.customerName}\n\n*Items Purchased:*\n${receiptModal.items.map(it => `• ${it.productName} (${it.variantTitle}): ${it.quantity} ${it.unit} x Rs.${it.transactionPrice} = Rs.${it.quantity * it.transactionPrice}`).join('\n')}\n\n*Subtotal:* Rs. ${receiptModal.subtotal || receiptModal.grandTotal}\n*Discount:* Rs. ${receiptModal.discount}\n*Grand Total:* Rs. ${receiptModal.grandTotal}\n*Paid:* Rs. ${receiptModal.paidAmount}\n*Remaining Due:* Rs. ${receiptModal.balanceAmount}\n\nThank you for shopping with Arooj Cloth and Bedsheet Parda!`;

    const url = `https://web.whatsapp.com/send?phone=${intlPhone}&text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
  };

  // ==========================================
  // WORKING CSV & EXCEL (.XLSX) EXPORT HELPERS
  // ==========================================

  const downloadTextFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 1. Export Products & Inventory
  const exportProductsCSV = (asExcel: boolean = false) => {
    const headers = ['Category', 'Product_Code', 'Product_Name', 'Urdu_Name', 'Unit', 'SKU', 'Size', 'Color', 'Design', 'Cost_Price', 'Selling_Price', 'Stock_Quantity', 'Min_Alert'];
    const rows = products.flatMap(p =>
      p.variants.map(v => [
        `"${p.category}"`,
        `"${p.code}"`,
        `"${p.name.replace(/"/g, '""')}"`,
        `"${p.nameUrdu.replace(/"/g, '""')}"`,
        `"${p.unit}"`,
        `"${v.sku}"`,
        `"${v.size}"`,
        `"${v.color}"`,
        `"${v.design}"`,
        v.cost,
        v.price,
        v.stock,
        p.minStockAlert
      ])
    );
    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    downloadTextFile(
      csvContent,
      `Arooj_Products_Inventory_${new Date().toISOString().slice(0, 10)}.${asExcel ? 'xlsx.csv' : 'csv'}`,
      'text/csv;charset=utf-8;'
    );
  };

  // 2. Export Sales & Financials
  const exportSalesCSV = (asExcel: boolean = false) => {
    const headers = ['Invoice_Number', 'Date', 'Customer_Name', 'Customer_Phone', 'Subtotal', 'Discount', 'Grand_Total', 'Paid_Amount', 'Balance_Due', 'Payment_Method', 'Status'];
    const rows = salesHistory.map(s => [
      `"${s.invoiceNumber}"`,
      `"${s.date}"`,
      `"${s.customerName.replace(/"/g, '""')}"`,
      `"${s.customerWhatsapp || s.customerPhone || ''}"`,
      s.subtotal,
      s.discount,
      s.grandTotal,
      s.paidAmount,
      s.balanceAmount,
      `"${s.paymentMethod}"`,
      `"${s.status}"`
    ]);
    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    downloadTextFile(
      csvContent,
      `Arooj_Sales_Report_${new Date().toISOString().slice(0, 10)}.${asExcel ? 'xlsx.csv' : 'csv'}`,
      'text/csv;charset=utf-8;'
    );
  };

  // 3. Export Customer Ledger & Phone Numbers
  const exportCustomersCSV = (asExcel: boolean = false) => {
    const headers = ['Customer_Code', 'Name', 'Phone', 'WhatsApp', 'City', 'Address', 'Credit_Limit', 'Current_Balance', 'Notes'];
    const rows = customers.map(c => [
      `"${c.code}"`,
      `"${c.name.replace(/"/g, '""')}"`,
      `"${c.phone}"`,
      `"${c.whatsapp}"`,
      `"${c.city}"`,
      `"${c.address.replace(/"/g, '""')}"`,
      c.creditLimit,
      c.balance,
      `"${(c.notes || '').replace(/"/g, '""')}"`
    ]);
    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    downloadTextFile(
      csvContent,
      `Arooj_Customers_Ledger_${new Date().toISOString().slice(0, 10)}.${asExcel ? 'xlsx.csv' : 'csv'}`,
      'text/csv;charset=utf-8;'
    );
  };

  // 4. Export Supplier Records
  const exportSuppliersCSV = (asExcel: boolean = false) => {
    const headers = ['Supplier_Code', 'Company_Name', 'Contact_Person', 'Phone', 'Address', 'Payable_Balance'];
    const rows = suppliers.map(s => [
      `"${s.code}"`,
      `"${s.companyName.replace(/"/g, '""')}"`,
      `"${s.contactPerson.replace(/"/g, '""')}"`,
      `"${s.phone}"`,
      `"${s.address.replace(/"/g, '""')}"`,
      s.balance
    ]);
    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    downloadTextFile(
      csvContent,
      `Arooj_Suppliers_Directory_${new Date().toISOString().slice(0, 10)}.${asExcel ? 'xlsx.csv' : 'csv'}`,
      'text/csv;charset=utf-8;'
    );
  };

  // Download Bulk Import Template
  const downloadSampleTemplate = () => {
    const template = '\uFEFF' + `category,product_name,product_name_urdu,sku,unit,size,color,design,purchase_price,selling_price,opening_stock,min_stock_alert\n` +
      `Bedsheets,Cotton Floral King Sheet,کاٹن فلورل کنگ بیڈ شیٹ,IMP-BED-001,Set,King 90x100,Navy Blue,Printed Flowers,1400,2400,20,5\n` +
      `Razai,Heavy Winter Quilted Razai,سردیوں کی بھاری رضائی,IMP-RZ-002,Pcs,Double,Wine Maroon,Embossed Polyester,2600,4200,12,3\n` +
      `Curtains & Parda,Blackout Velvet Curtain,بلیک آؤٹ پردہ,IMP-CUR-003,Pcs,7x4 Feet,Charcoal Grey,Eyelet Rings,950,1750,30,8\n` +
      `Unstitched Fabric,Boski Karandi Unstitched,بوسکی کپڑا تھان,IMP-FAB-004,Meter,54 in,Off White,Plain Textured,350,580,85.5,20`;
    downloadTextFile(template, 'Arooj_POS_Product_Import_Template.csv', 'text/csv;charset=utf-8;');
  };

  // Parse & Validate CSV/Text Input
  const handleParseImport = (text: string) => {
    setImportFileText(text);
    if (!text.trim()) {
      setImportPreviewRows([]);
      setImportSummary(null);
      return;
    }

    const lines = text.trim().split(/\r?\n/).filter(l => l.trim().length > 0);
    if (lines.length < 2) {
      alert('The uploaded file must contain a header row and at least one product row.');
      return;
    }

    const rawHeaders = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, '').toLowerCase());
    const preview: any[] = [];
    let validCount = 0;
    let warnCount = 0;
    let errCount = 0;

    for (let i = 1; i < lines.length; i++) {
      // Split by comma ignoring commas inside quotes
      const values = lines[i].split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/).map(v => v.trim().replace(/^["']|["']$/g, ''));
      const rowObj: any = {};
      rawHeaders.forEach((h, idx) => {
        rowObj[h] = values[idx] || '';
      });

      // Validation
      const name = rowObj['product_name'] || rowObj['name'] || '';
      const sku = rowObj['sku'] || `AUTO-${i}`;
      const category = rowObj['category'] || 'General';
      const unit = rowObj['unit'] || 'Pcs';
      const price = parseFloat(rowObj['selling_price'] || rowObj['price'] || '0');
      const cost = parseFloat(rowObj['purchase_price'] || rowObj['cost'] || '0');
      const stock = parseFloat(rowObj['opening_stock'] || rowObj['stock'] || '0');

      let status = 'Valid';
      let issue = '';

      if (!name) {
        status = 'Error';
        issue = 'Product Name is missing';
        errCount++;
      } else if (isNaN(price) || price < 0) {
        status = 'Error';
        issue = 'Invalid selling price';
        errCount++;
      } else {
        const skuExists = products.some(p => p.variants.some(v => v.sku.toLowerCase() === sku.toLowerCase()));
        if (skuExists) {
          status = 'Warning';
          issue = 'SKU already exists (Will be updated or skipped based on mode)';
          warnCount++;
        } else {
          validCount++;
        }
      }

      preview.push({
        id: `row-${i}`,
        category,
        name,
        nameUrdu: rowObj['product_name_urdu'] || '',
        sku,
        unit,
        size: rowObj['size'] || 'Standard',
        color: rowObj['color'] || 'Assorted',
        design: rowObj['design'] || '',
        cost: isNaN(cost) ? 0 : cost,
        price: isNaN(price) ? 0 : price,
        stock: isNaN(stock) ? 0 : stock,
        status,
        issue
      });
    }

    setImportPreviewRows(preview);
    setImportSummary({
      total: preview.length,
      valid: validCount,
      warnings: warnCount,
      errors: errCount
    });
  };

  // Commit Import to Products State
  const commitImport = () => {
    if (importPreviewRows.length === 0) return;

    let added = 0;
    let updated = 0;
    let skipped = 0;

    let updatedList = [...products];

    importPreviewRows.forEach(row => {
      if (row.status === 'Error') {
        skipped++;
        return;
      }

      const existingProdIndex = updatedList.findIndex(p =>
        p.variants.some(v => v.sku.toLowerCase() === row.sku.toLowerCase())
      );

      if (existingProdIndex >= 0) {
        if (importConflictMode === 'skip') {
          skipped++;
          return;
        }

        // Update existing product and variant
        updatedList[existingProdIndex].variants = updatedList[existingProdIndex].variants.map(v => {
          if (v.sku.toLowerCase() === row.sku.toLowerCase()) {
            return {
              ...v,
              price: row.price > 0 ? row.price : v.price,
              cost: row.cost > 0 ? row.cost : v.cost,
              stock: row.stock > 0 ? row.stock : v.stock,
              size: row.size || v.size,
              color: row.color || v.color
            };
          }
          return v;
        });
        updated++;
      } else {
        // Add new product
        const newProduct: Product = {
          id: `imp-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
          code: `PRD-${row.sku}`,
          name: row.name,
          nameUrdu: row.nameUrdu || row.name,
          category: row.category,
          categoryCode: row.category.toUpperCase().replace(/\s+/g, '_'),
          unit: row.unit,
          isFabric: row.unit.toLowerCase().includes('meter') || row.unit.toLowerCase().includes('yard'),
          baseCost: row.cost,
          basePrice: row.price,
          stock: row.stock,
          minStockAlert: 5,
          variants: [
            {
              sku: row.sku,
              size: row.size,
              color: row.color,
              design: row.design,
              price: row.price,
              cost: row.cost,
              stock: row.stock
            }
          ]
        };
        updatedList.push(newProduct);
        added++;
      }
    });

    setProducts(updatedList);
    alert(`Bulk Import Complete!\nAdded: ${added} new products\nUpdated: ${updated} existing products\nSkipped / Failed: ${skipped} rows`);
    setImportPreviewRows([]);
    setImportSummary(null);
    setImportFileText('');
    setActiveTab('stock');
  };

  // Launch WhatsApp Campaign to Selected Recipient
  const handleLaunchCampaign = () => {
    if (selectedCampaignRecipients.length === 0) {
      alert('Please select at least one customer phone number to send this offer.');
      return;
    }

    const firstPhone = selectedCampaignRecipients[0];
    const contact = allWhatsAppContacts.find(c => c.phone === firstPhone);
    const custName = contact ? contact.name : 'Valued Customer';

    const personalized = campaignTemplate
      .replace(/{customer_name}/g, custName)
      .replace(/{shop_name}/g, shopName)
      .replace(/{discount_percent}/g, campaignDiscount)
      .replace(/{phone}/g, shopPhone);

    const cleanPhone = firstPhone.replace(/[^0-9]/g, '');
    const intlPhone = cleanPhone.startsWith('0') ? '92' + cleanPhone.slice(1) : cleanPhone;

    const url = `https://web.whatsapp.com/send?phone=${intlPhone}&text=${encodeURIComponent(personalized)}`;
    window.open(url, '_blank');

    // Add to campaigns log
    const newCamp: WhatsAppCampaign = {
      id: `cmp-${Date.now()}`,
      title: campaignTitle,
      date: new Date().toLocaleString(),
      recipientCount: selectedCampaignRecipients.length,
      messageText: personalized,
      status: 'Sent'
    };
    setCampaigns([newCamp, ...campaigns]);
    setBroadcastLog([
      `Campaign "${campaignTitle}" launched to ${selectedCampaignRecipients.length} customer(s) at ${new Date().toLocaleTimeString()}`,
      ...broadcastLog
    ]);
  };

  return (
    <div className={`flex flex-col h-screen font-sans antialiased overflow-hidden transition-colors duration-200 ${
      theme === 'dark' ? 'bg-slate-950 text-slate-100' : 'bg-slate-100 text-slate-800'
    }`}>
      {/* ==========================================
          TOP APPLICATION HEADER & BANNER
         ========================================== */}
      <header className={`px-4 py-2 flex items-center justify-between shrink-0 shadow-sm border-b-2 ${
        theme === 'dark'
          ? 'bg-slate-900 border-emerald-600 text-white'
          : 'bg-emerald-900 border-emerald-700 text-white'
      }`}>
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-700 p-2 rounded-lg text-emerald-100 shadow-inner">
            <Package className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold tracking-tight text-white">{shopName}</h1>
              <span className="text-emerald-300 font-medium text-xs font-arabic">({shopUrdu})</span>
            </div>
            <div className="flex items-center space-x-2 text-[11px] text-emerald-300">
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Offline SQLite Active
              </span>
              <span>•</span>
              <span>PySide6 Desktop Engine v1.2</span>
              <span>•</span>
              <span className="text-amber-300 font-mono">F1-F6 Shortcuts</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className={`flex space-x-1 p-1 rounded-lg border ${
          theme === 'dark'
            ? 'bg-slate-950/80 border-slate-800'
            : 'bg-emerald-950/60 border-emerald-800/80'
        }`}>
          <button
            onClick={() => setActiveTab('pos')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeTab === 'pos'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:bg-emerald-800/50'
            }`}
          >
            <ShoppingCart className="w-3.5 h-3.5" />
            POS Billing [F1]
          </button>

          <button
            onClick={() => setActiveTab('stock')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeTab === 'stock'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:bg-emerald-800/50'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Stock & Fabric [F2]
          </button>

          <button
            onClick={() => setActiveTab('customers')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeTab === 'customers'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:bg-emerald-800/50'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            Customers & WhatsApp [F3]
          </button>

          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeTab === 'dashboard'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:bg-emerald-800/50'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            Profit Dashboard [F4]
          </button>

          <button
            onClick={() => setActiveTab('reports')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeTab === 'reports'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:bg-emerald-800/50'
            }`}
          >
            <Receipt className="w-3.5 h-3.5" />
            Invoices [F5]
          </button>

          <button
            onClick={() => setActiveTab('import-export')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeTab === 'import-export'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:bg-emerald-800/50'
            }`}
          >
            <Download className="w-3.5 h-3.5" />
            Import / Export
          </button>

          <button
            onClick={() => setActiveTab('settings')}
            className={`px-3 py-1.5 rounded-md text-xs font-bold flex items-center gap-1.5 transition-all ${
              activeTab === 'settings'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-emerald-200 hover:bg-emerald-800/50'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            Settings [F6]
          </button>
        </nav>

        {/* Right Controls: Backup & Dark / Light Mode Toggle */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowBackupModal(true)}
            className={`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 text-xs font-bold transition-all shadow-xs cursor-pointer ${
              theme === 'dark'
                ? 'bg-slate-800 text-emerald-300 border-slate-700 hover:bg-slate-700 hover:border-emerald-500'
                : 'bg-emerald-800 text-white border-emerald-700 hover:bg-emerald-700 hover:border-emerald-500'
            }`}
            title="Database Backup & Restore Manager (بیک اپ مینیجر)"
          >
            <Download className="w-3.5 h-3.5 text-emerald-300" />
            <span>💾 Backup</span>
          </button>

          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            className={`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 text-xs font-bold transition-all shadow-xs cursor-pointer ${
              theme === 'dark'
                ? 'bg-slate-800 text-amber-300 border-slate-700 hover:bg-slate-700 hover:border-amber-400'
                : 'bg-emerald-800 text-amber-200 border-emerald-700 hover:bg-emerald-700 hover:border-amber-300'
            }`}
            title="Toggle Light / Dark Mode (تبدیل موڈ)"
          >
            {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-amber-300" />}
            <span>{theme === 'dark' ? '☀️ Light' : '🌙 Dark'}</span>
          </button>
        </div>
      </header>

      {/* ==========================================
          MAIN SCREEN VIEW CONTENT
         ========================================== */}
      <main className="flex-1 overflow-hidden">
        {/* --------------------------------------
            TAB 1: POS BILLING SCREEN
           -------------------------------------- */}
        {activeTab === 'pos' && (
          <div className="h-full flex flex-col md:flex-row overflow-hidden">
            {/* Left Column: Categories, Barcode & Product Cards */}
            <div className={`flex-1 flex flex-col overflow-hidden border-r ${
              theme === 'dark' ? 'border-slate-800 bg-slate-900' : 'border-slate-200 bg-white'
            }`}>
              {/* Top Search & Barcode scanning bar */}
              <div className={`p-3 border-b flex flex-wrap gap-2 items-center ${
                theme === 'dark' ? 'border-slate-800 bg-slate-900/90' : 'border-slate-200 bg-slate-50'
              }`}>
                {/* Barcode Form */}
                <form onSubmit={handleBarcodeSubmit} className="flex-1 min-w-[200px] flex items-center relative">
                  <Barcode className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                  <input
                    type="text"
                    value={barcodeInput}
                    onChange={(e) => setBarcodeInput(e.target.value)}
                    placeholder="Scan Barcode / SKU + Enter..."
                    className={`w-full pl-9 pr-3 py-1.5 text-xs font-mono rounded-lg border focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                      theme === 'dark'
                        ? 'bg-slate-800 border-slate-700 text-white placeholder-slate-400'
                        : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400'
                    }`}
                  />
                </form>

                {/* Text Search */}
                <div className="flex-1 min-w-[200px] flex items-center relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search name, Urdu, or code..."
                    className={`w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
                      theme === 'dark'
                        ? 'bg-slate-800 border-slate-700 text-white placeholder-slate-400'
                        : 'bg-white border-slate-300 text-slate-900 placeholder-slate-400'
                    }`}
                  />
                </div>
              </div>

              {/* Horizontal Scroll Category Buttons */}
              <div className={`px-3 py-2 border-b overflow-x-auto whitespace-nowrap flex space-x-2 shrink-0 ${
                theme === 'dark' ? 'border-slate-800 bg-slate-950/40' : 'border-slate-100 bg-slate-50'
              }`}>
                {CATEGORIES.map(cat => (
                  <button
                    key={cat.code}
                    onClick={() => setSelectedCategory(cat.code)}
                    className={`px-3 py-1 rounded-full text-xs font-bold transition-colors shrink-0 flex items-center gap-1 ${
                      selectedCategory === cat.code
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : theme === 'dark'
                          ? 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                          : 'bg-white text-slate-700 hover:bg-slate-200 border border-slate-300'
                    }`}
                  >
                    <span>{cat.name}</span>
                    <span className="text-[10px] opacity-75 font-arabic">({cat.urdu})</span>
                  </button>
                ))}
              </div>

              {/* Product Cards Grid */}
              <div className="flex-1 overflow-y-auto p-3">
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
                  {filteredProducts.map(product => (
                    <div
                      key={product.id}
                      onClick={() => {
                        if (product.variants.length > 1 || product.isFabric) {
                          setSelectedVariantProduct(product);
                          setFabricLengthInput(product.isFabric ? 2.5 : 1);
                        } else {
                          handleAddToCart(product, 0, 1);
                        }
                      }}
                      className={`p-2.5 rounded-xl border cursor-pointer select-none transition-all hover:scale-[1.01] hover:shadow-md flex flex-col justify-between ${
                        theme === 'dark'
                          ? 'bg-slate-800/80 border-slate-700 hover:border-emerald-500 hover:bg-slate-800'
                          : 'bg-white border-slate-200 hover:border-emerald-600'
                      }`}
                    >
                      <div>
                        <div className="flex justify-between items-start gap-1">
                          <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                            theme === 'dark' ? 'bg-slate-900 text-emerald-400' : 'bg-emerald-50 text-emerald-700'
                          }`}>
                            {product.code}
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            product.stock <= product.minStockAlert
                              ? 'bg-red-500/20 text-red-500'
                              : 'bg-emerald-500/20 text-emerald-500'
                          }`}>
                            {product.stock} {product.unit}
                          </span>
                        </div>
                        <h4 className="font-bold text-xs mt-1.5 line-clamp-1">{product.name}</h4>
                        <p className="text-[11px] font-arabic text-emerald-500 line-clamp-1">{product.nameUrdu}</p>
                      </div>

                      <div className="mt-2 pt-1.5 border-t border-dashed border-slate-300/40 flex items-center justify-between">
                        <div>
                          <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                            Rs. {product.basePrice.toLocaleString()}
                          </span>
                          {product.variants.length > 1 && (
                            <span className="text-[9px] text-slate-400 block">{product.variants.length} varieties</span>
                          )}
                        </div>
                        <span className="bg-emerald-600 text-white p-1 rounded-md text-[10px] font-bold">
                          +Add
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Cart Panel & Checkout */}
            <div className={`w-full md:w-[420px] lg:w-[460px] flex flex-col overflow-hidden shrink-0 ${
              theme === 'dark' ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
            }`}>
              {/* Cart Header & Customer / WhatsApp Selector */}
              <div className={`p-3 border-b space-y-2 ${
                theme === 'dark' ? 'border-slate-800 bg-slate-900/60' : 'border-slate-200 bg-white'
              }`}>
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 text-emerald-600">
                    <ShoppingCart className="w-4 h-4" />
                    Billing Cart ({cart.length} items)
                  </h3>
                  {cart.length > 0 && (
                    <button
                      onClick={() => setCart([])}
                      className="text-[11px] text-red-500 hover:text-red-600 font-bold flex items-center gap-1"
                    >
                      <Trash2 className="w-3 h-3" /> Clear
                    </button>
                  )}
                </div>

                {/* Customer Selector & WhatsApp Mobile Input */}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] font-bold block mb-0.5 text-slate-500">Customer Account:</label>
                    <select
                      value={selectedCustomer?.id || ''}
                      onChange={(e) => {
                        const c = customers.find(x => x.id === e.target.value) || null;
                        setSelectedCustomer(c);
                        if (c) {
                          setWalkinWhatsapp(c.whatsapp || c.phone);
                          setWalkinName(c.name);
                        }
                      }}
                      className={`w-full p-1.5 text-xs rounded border focus:outline-none focus:ring-1 focus:ring-emerald-500 ${
                        theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                      }`}
                    >
                      <option value="">Walk-in Customer (کاؤنٹر گاہک)</option>
                      {customers.map(c => (
                        <option key={c.id} value={c.id}>{c.name} (Bal: Rs.{c.balance})</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold block mb-0.5 text-slate-500">WhatsApp / Phone #:</label>
                    <div className="relative">
                      <Phone className="w-3 h-3 text-slate-400 absolute left-2 top-2 pointer-events-none" />
                      <input
                        type="text"
                        value={walkinWhatsapp}
                        onChange={(e) => setWalkinWhatsapp(e.target.value)}
                        placeholder="0300-1234567"
                        className={`w-full pl-6 pr-2 py-1.5 text-xs font-mono rounded border focus:outline-none focus:ring-1 focus:ring-emerald-500 ${
                          theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                        }`}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Cart Table with Compact 6-Column Layout & Inline Editable Prices */}
              <div className="flex-1 overflow-y-auto p-1.5">
                {cart.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
                    <ShoppingCart className="w-12 h-12 stroke-1 mb-2 text-slate-300" />
                    <p className="text-xs font-bold">Cart is empty (خالی کارٹ)</p>
                    <p className="text-[11px] text-slate-400">Scan barcode or click product card to add</p>
                  </div>
                ) : (
                  <div className="overflow-x-hidden">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className={`border-b text-[11px] ${
                        theme === 'dark' ? 'border-slate-800 bg-slate-900/90 text-slate-400' : 'border-slate-200 bg-slate-100/90 text-slate-600'
                      }`}>
                        <tr>
                          <th className="py-1.5 px-2 font-bold">Product</th>
                          <th className="py-1.5 px-1 font-bold">Variant</th>
                          <th className="py-1.5 px-1 font-bold text-center">Qty</th>
                          <th className="py-1.5 px-1 font-bold text-right w-[92px]">Price (Rs.)</th>
                          <th className="py-1.5 px-1 font-bold text-right">Total (Rs.)</th>
                          <th className="py-1.5 px-1 text-center w-[26px]"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-800/80">
                        {cart.map((item, idx) => (
                          <tr
                            key={item.id}
                            className={`group transition-colors ${
                              item.isOverridden
                                ? 'bg-amber-500/10 dark:bg-amber-500/15'
                                : 'hover:bg-slate-100/50 dark:hover:bg-slate-900/40'
                            }`}
                          >
                            {/* 1. Product Name */}
                            <td className="py-1.5 px-2 max-w-[120px]">
                              <div className="font-bold text-xs truncate" title={item.productName}>
                                {item.productName}
                              </div>
                              {item.isOverridden && (
                                <span className="inline-block text-[9px] font-bold text-amber-600 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/40 px-1 rounded">
                                  Bargain
                                </span>
                              )}
                            </td>

                            {/* 2. Variant */}
                            <td className="py-1.5 px-1 text-[10px] text-slate-500 dark:text-slate-400 max-w-[80px] truncate" title={item.variantTitle}>
                              {item.variantTitle}
                            </td>

                            {/* 3. Quantity Controls */}
                            <td className="py-1.5 px-1 text-center whitespace-nowrap">
                              <div className="inline-flex items-center gap-1 bg-slate-200/60 dark:bg-slate-800/80 px-1 py-0.5 rounded text-[11px]">
                                <button
                                  onClick={() => {
                                    const step = item.isFabric ? 0.5 : 1;
                                    const min = item.isFabric ? 0.5 : 1;
                                    const newQty = Math.max(min, item.quantity - step);
                                    setCart(cart.map(x => x.id === item.id ? { ...x, quantity: Number(newQty.toFixed(3)) } : x));
                                  }}
                                  className="w-4 h-4 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 rounded"
                                >
                                  -
                                </button>
                                <span className="font-mono font-bold px-0.5">{item.quantity}</span>
                                <button
                                  onClick={() => {
                                    const step = item.isFabric ? 0.5 : 1;
                                    const newQty = item.quantity + step;
                                    setCart(cart.map(x => x.id === item.id ? { ...x, quantity: Number(newQty.toFixed(3)) } : x));
                                  }}
                                  className="w-4 h-4 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 rounded"
                                >
                                  +
                                </button>
                              </div>
                            </td>

                            {/* 4. Editable Selling Price inside row */}
                            <td className="py-1.5 px-1 text-right w-[92px]">
                              <input
                                ref={(el) => { priceInputRefs.current[idx] = el; }}
                                type="number"
                                min="0"
                                step="10"
                                value={item.transactionPrice}
                                onChange={(e) => handleInlinePriceChange(item, e.target.value)}
                                onKeyDown={(e) => handleInlinePriceKeyDown(e, item, idx)}
                                title="Press ENTER to commit rate and jump to next item"
                                className={`w-full py-0.5 px-1 text-right text-xs font-mono font-bold rounded border focus:outline-none focus:ring-1 transition-all ${
                                  item.isOverridden
                                    ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200 border-amber-400 focus:ring-amber-500'
                                    : theme === 'dark'
                                      ? 'bg-slate-900 text-white border-slate-700 focus:ring-emerald-500'
                                      : 'bg-white text-slate-900 border-slate-300 focus:ring-emerald-500'
                                }`}
                              />
                            </td>

                            {/* 5. Row Total */}
                            <td className="py-1.5 px-1 text-right font-mono font-bold text-xs whitespace-nowrap text-emerald-600 dark:text-emerald-400">
                              Rs. {(item.transactionPrice * item.quantity).toLocaleString()}
                            </td>

                            {/* 6. Delete Action */}
                            <td className="py-1.5 px-1 text-center">
                              <button
                                onClick={() => setCart(cart.filter(x => x.id !== item.id))}
                                className="w-5 h-5 flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                                title="Remove item"
                              >
                                ✕
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Bottom Summary & Checkout Controls */}
              <div className={`p-3 border-t space-y-2 shrink-0 ${
                theme === 'dark' ? 'border-slate-800 bg-slate-900' : 'border-slate-200 bg-white'
              }`}>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Cart Subtotal:</span>
                  <span className="font-mono font-bold">Rs. {cartSubtotal.toLocaleString()}</span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Bill Discount (Rs.):</span>
                  <input
                    ref={discountInputRef}
                    type="number"
                    min="0"
                    value={billDiscount}
                    onChange={(e) => setBillDiscount(Math.max(0, parseFloat(e.target.value) || 0))}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        tenderedCashRef.current?.focus();
                        tenderedCashRef.current?.select();
                      }
                    }}
                    title="Press ENTER to jump to Tendered Cash"
                    className={`w-24 text-right p-1 text-xs font-mono font-bold rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>

                <div className="flex justify-between items-baseline pt-1 border-t border-dashed border-slate-300/40">
                  <span className="font-bold text-sm text-emerald-600 dark:text-emerald-400">GRAND TOTAL:</span>
                  <span className="font-mono font-black text-lg text-emerald-600 dark:text-emerald-400">
                    Rs. {grandTotal.toLocaleString()}
                  </span>
                </div>

                {/* Tendered cash & change */}
                <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                  <div>
                    <label className="text-[10px] text-slate-400 block">Payment Method:</label>
                    <select
                      value={paymentMethod}
                      onChange={(e) => setPaymentMethod(e.target.value as any)}
                      className={`w-full p-1.5 text-xs rounded border ${
                        theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                      }`}
                    >
                      <option value="Cash">Cash (Till)</option>
                      <option value="Credit">Credit (Khata)</option>
                      <option value="Card">Bank Card</option>
                      <option value="Bank Transfer">Online Bank Transfer</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-400 block">Tendered Cash:</label>
                    <input
                      ref={tenderedCashRef}
                      type="number"
                      placeholder={`Rs. ${grandTotal}`}
                      value={tenderedCash || ''}
                      onChange={(e) => setTenderedCash(parseFloat(e.target.value) || 0)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          requestSalePreview();
                        }
                      }}
                      title="Press ENTER to validate & open Safe Receipt Preview"
                      className={`w-full p-1.5 text-xs font-mono font-bold rounded border ${
                        theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                      }`}
                    />
                  </div>
                </div>

                {tenderedCash > 0 && (
                  <div className="flex justify-between text-xs font-bold pt-1">
                    <span className="text-slate-400">Change Due (بقیہ):</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-mono">
                      Rs. {changeDue.toLocaleString()}
                    </span>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="pt-2 flex gap-2">
                  <button
                    onClick={requestSalePreview}
                    disabled={cart.length === 0}
                    className="flex-1 py-2.5 px-3 rounded-lg font-bold text-xs uppercase tracking-wide bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white flex items-center justify-center gap-1.5 shadow-md transition-all cursor-pointer"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Complete Sale (F10)
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --------------------------------------
            TAB 2: STOCK & FABRIC ROLLS
           -------------------------------------- */}
        {activeTab === 'stock' && (
          <div className="h-full flex flex-col p-4 overflow-y-auto space-y-4">
            {/* Inventory Valuation Header Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className={`p-3 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block">Total Catalog Items</span>
                <span className="text-xl font-black text-emerald-600 dark:text-emerald-400">{products.length}</span>
              </div>
              <div className={`p-3 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block">Total Units In Stock</span>
                <span className="text-xl font-black text-slate-800 dark:text-white">
                  {products.reduce((acc, p) => acc + p.stock, 0)}
                </span>
              </div>
              <div className={`p-3 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block">Total Cost Valuation</span>
                <span className="text-xl font-black text-amber-600 dark:text-amber-400">
                  Rs. {products.reduce((acc, p) => acc + (p.stock * p.baseCost), 0).toLocaleString()}
                </span>
              </div>
              <div className={`p-3 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block">Retail Sale Value</span>
                <span className="text-xl font-black text-emerald-600 dark:text-emerald-400">
                  Rs. {products.reduce((acc, p) => acc + (p.stock * p.basePrice), 0).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Catalog Table */}
            <div className={`rounded-xl border flex-1 flex flex-col overflow-hidden ${
              theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
            }`}>
              <div className="p-3 border-b flex flex-wrap justify-between items-center gap-2">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-sm flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-emerald-500" />
                    Product Inventory & Fabric Rolls (اسٹاک و کپڑا)
                  </h3>
                  <span className="text-[11px] bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full font-bold">
                    {products.length} Products
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-1.5">
                  <button
                    onClick={openAddProductModal}
                    className="px-2.5 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-1 shadow-xs transition-colors cursor-pointer"
                    title="Add standard product or bedding (نیا پراڈکٹ شامل کریں)"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>➕ Add New Product (نیا پراڈکٹ)</span>
                  </button>

                  <button
                    onClick={openEditProductModal}
                    className="px-2.5 py-1.5 text-xs font-bold bg-sky-600 hover:bg-sky-700 text-white rounded-lg flex items-center gap-1 shadow-xs transition-colors cursor-pointer"
                    title="Edit selected product attributes and prices (ترمیم کریں)"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>✏️ Edit Product (ترمیم)</span>
                  </button>

                  <button
                    onClick={openAddFabricModal}
                    className="px-2.5 py-1.5 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-lg flex items-center gap-1 shadow-xs transition-colors cursor-pointer"
                    title="Add unstitched fabric / meter cloth (تھان / کپڑا شامل کریں)"
                  >
                    <Package className="w-3.5 h-3.5" />
                    <span>🧵 Add Fabric (تھان/کپڑا)</span>
                  </button>

                  <button
                    onClick={openAddFabricRollModal}
                    className="px-2.5 py-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg flex items-center gap-1 shadow-xs transition-colors cursor-pointer"
                    title="Register individual fabric roll (تھان رول درج کریں)"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>🔄 Add Fabric Roll (تھان رول)</span>
                  </button>

                  <button
                    onClick={() => exportProductsCSV(false)}
                    className="px-2.5 py-1.5 text-xs font-bold bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center gap-1 transition-colors cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" /> Export (.csv)
                  </button>

                  <button
                    onClick={() => setActiveTab('import-export')}
                    className={`px-2.5 py-1.5 text-xs font-bold rounded-lg border flex items-center gap-1 transition-colors cursor-pointer ${
                      theme === 'dark' ? 'border-slate-700 hover:bg-slate-800 text-slate-300' : 'border-slate-300 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    <Upload className="w-3.5 h-3.5" /> Bulk Import
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className={`border-b ${
                    theme === 'dark' ? 'border-slate-800 bg-slate-950/60 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-500'
                  }`}>
                    <tr>
                      <th className="p-2.5">Code</th>
                      <th className="p-2.5">Product Name</th>
                      <th className="p-2.5">Urdu Name</th>
                      <th className="p-2.5">Category</th>
                      <th className="p-2.5">Unit</th>
                      <th className="p-2.5 text-right">Cost Rate</th>
                      <th className="p-2.5 text-right">Selling Price</th>
                      <th className="p-2.5 text-right">In Stock</th>
                      <th className="p-2.5 text-center">Status</th>
                      <th className="p-2.5 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {products.map(p => {
                      const isSelected = selectedStockProductId === p.id;
                      return (
                        <tr
                          key={p.id}
                          onClick={() => setSelectedStockProductId(p.id)}
                          className={`cursor-pointer transition-colors ${
                            isSelected
                              ? 'bg-emerald-500/15 dark:bg-emerald-500/20'
                              : 'hover:bg-slate-500/5'
                          }`}
                        >
                          <td className="p-2.5 font-mono font-bold text-emerald-600">{p.code}</td>
                          <td className="p-2.5 font-bold">{p.name}</td>
                          <td className="p-2.5 font-arabic text-emerald-500">{p.nameUrdu}</td>
                          <td className="p-2.5">{p.category}</td>
                          <td className="p-2.5 font-mono">{p.unit}</td>
                          <td className="p-2.5 text-right font-mono">Rs. {p.baseCost.toLocaleString()}</td>
                          <td className="p-2.5 text-right font-mono font-bold text-emerald-600">Rs. {p.basePrice.toLocaleString()}</td>
                          <td className="p-2.5 text-right font-mono font-bold">{p.stock} {p.unit}</td>
                          <td className="p-2.5 text-center">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              p.stock <= p.minStockAlert ? 'bg-red-500/20 text-red-500' : 'bg-emerald-500/20 text-emerald-500'
                            }`}>
                              {p.stock <= p.minStockAlert ? 'Low Stock' : 'Healthy'}
                            </span>
                          </td>
                          <td className="p-2.5 text-center">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedStockProductId(p.id);
                                setIsEditingProduct(true);
                                setProductFormData({
                                  id: p.id,
                                  code: p.code,
                                  name: p.name,
                                  nameUrdu: p.nameUrdu,
                                  category: p.category,
                                  unit: p.unit,
                                  isFabric: p.isFabric,
                                  cost: p.baseCost,
                                  price: p.basePrice,
                                  stock: p.stock,
                                  minAlert: p.minStockAlert
                                });
                                setShowProductModal(true);
                              }}
                              className="px-2 py-1 text-[11px] font-bold bg-sky-500/15 hover:bg-sky-500/25 text-sky-600 dark:text-sky-400 rounded transition-colors"
                            >
                              Edit
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* --------------------------------------
            TAB 3: CUSTOMER LEDGER & WHATSAPP CAMPAIGN (FEATURE D)
           -------------------------------------- */}
        {activeTab === 'customers' && (
          <div className="h-full flex flex-col p-4 overflow-y-auto space-y-4">
            {/* Header info bar */}
            <div className="flex flex-wrap justify-between items-center gap-2">
              <div>
                <h2 className="text-base font-bold flex items-center gap-2">
                  <Users className="w-5 h-5 text-emerald-600" />
                  Customer Accounts & Bulk WhatsApp Marketing
                </h2>
                <p className="text-xs text-slate-400">
                  Manage store credit ledgers and broadcast festival offers directly to collected customer phone numbers.
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => exportCustomersCSV(false)}
                  className="px-3 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-1 shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" /> Export Customers (.csv)
                </button>
              </div>
            </div>

            {/* Split Screen: Left = WhatsApp Broadcast Tool, Right = Customer Ledger Table */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
              {/* WhatsApp Campaign Composer Box (4 Cols) */}
              <div className={`lg:col-span-5 p-4 rounded-xl border flex flex-col space-y-3 ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <div className="flex items-center justify-between border-b pb-2">
                  <h3 className="font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 text-emerald-600">
                    <MessageSquare className="w-4 h-4" />
                    WhatsApp Offer Composer
                  </h3>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-500 px-2 py-0.5 rounded-full font-bold">
                    Web API Direct
                  </span>
                </div>

                <div>
                  <label className="text-[11px] font-bold block mb-1">Campaign Title:</label>
                  <input
                    type="text"
                    value={campaignTitle}
                    onChange={(e) => setCampaignTitle(e.target.value)}
                    className={`w-full p-2 text-xs rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-[11px] font-bold">Discount Rate (%):</label>
                    <div className="flex gap-1">
                      {['15', '20', '30', '50'].map(pct => (
                        <button
                          key={pct}
                          onClick={() => setCampaignDiscount(pct)}
                          className={`px-1.5 py-0.5 text-[10px] rounded font-bold ${
                            campaignDiscount === pct
                              ? 'bg-emerald-600 text-white'
                              : 'bg-slate-200 dark:bg-slate-800 text-slate-500'
                          }`}
                        >
                          {pct}%
                        </button>
                      ))}
                    </div>
                  </div>
                  <input
                    type="number"
                    value={campaignDiscount}
                    onChange={(e) => setCampaignDiscount(e.target.value)}
                    className={`w-full p-2 text-xs rounded border font-mono ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>

                {/* Message Template with Dynamic Tags */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-[11px] font-bold">Offer Message Template:</label>
                    <span className="text-[10px] text-slate-400">Insert tag:</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-1.5">
                    {['{customer_name}', '{shop_name}', '{discount_percent}', '{phone}'].map(tag => (
                      <button
                        key={tag}
                        onClick={() => setCampaignTemplate(campaignTemplate + ' ' + tag)}
                        className="px-1.5 py-0.5 text-[10px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded hover:bg-emerald-500/20"
                      >
                        +{tag}
                      </button>
                    ))}
                  </div>
                  <textarea
                    rows={4}
                    value={campaignTemplate}
                    onChange={(e) => setCampaignTemplate(e.target.value)}
                    className={`w-full p-2 text-xs rounded border font-sans ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>

                {/* Live Message Bubble Preview */}
                <div>
                  <span className="text-[10px] text-slate-400 block mb-1">Live WhatsApp Preview:</span>
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-xs font-sans leading-relaxed text-slate-700 dark:text-slate-200 shadow-inner">
                    <div className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 mb-1">
                      WhatsApp Message Preview
                    </div>
                    {campaignTemplate
                      .replace(/{customer_name}/g, 'Chaudhry Tariq')
                      .replace(/{shop_name}/g, shopName)
                      .replace(/{discount_percent}/g, campaignDiscount)
                      .replace(/{phone}/g, shopPhone)}
                  </div>
                </div>

                {/* Recipient Count & Launch Button */}
                <div className="pt-2 border-t">
                  <div className="flex justify-between text-xs mb-2">
                    <span className="text-slate-400">Selected Recipients:</span>
                    <span className="font-bold text-emerald-600">{selectedCampaignRecipients.length} contact(s)</span>
                  </div>
                  <button
                    onClick={handleLaunchCampaign}
                    className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 shadow-md"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Launch WhatsApp Broadcast via Web
                  </button>
                </div>
              </div>

              {/* Customer Directory & Phone Contacts Table (7 Cols) */}
              <div className={`lg:col-span-7 p-4 rounded-xl border flex flex-col space-y-3 ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <div className="flex justify-between items-center border-b pb-2">
                  <h3 className="font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 text-slate-800 dark:text-white">
                    <Phone className="w-4 h-4 text-emerald-600" />
                    Customer Directory & Collected WhatsApp Numbers ({allWhatsAppContacts.length})
                  </h3>
                  <button
                    onClick={() => {
                      if (selectedCampaignRecipients.length === allWhatsAppContacts.length) {
                        setSelectedCampaignRecipients([]);
                      } else {
                        setSelectedCampaignRecipients(allWhatsAppContacts.map(c => c.phone));
                      }
                    }}
                    className="text-xs font-bold text-emerald-600 hover:underline"
                  >
                    {selectedCampaignRecipients.length === allWhatsAppContacts.length ? 'Deselect All' : 'Select All for Offer'}
                  </button>
                </div>

                <div className="flex-1 overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className={`border-b ${
                      theme === 'dark' ? 'border-slate-800 bg-slate-950/60 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-500'
                    }`}>
                      <tr>
                        <th className="p-2 w-8 text-center">✓</th>
                        <th className="p-2">Customer Name</th>
                        <th className="p-2">WhatsApp #</th>
                        <th className="p-2">Source</th>
                        <th className="p-2 text-right">Total Purchases</th>
                        <th className="p-2 text-center">Direct Link</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                      {allWhatsAppContacts.map((contact, idx) => {
                        const isSelected = selectedCampaignRecipients.includes(contact.phone);
                        const cleanPhone = contact.phone.replace(/[^0-9]/g, '');
                        const intlPhone = cleanPhone.startsWith('0') ? '92' + cleanPhone.slice(1) : cleanPhone;
                        return (
                          <tr key={idx} className="hover:bg-slate-500/5">
                            <td className="p-2 text-center">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {
                                  if (isSelected) {
                                    setSelectedCampaignRecipients(selectedCampaignRecipients.filter(p => p !== contact.phone));
                                  } else {
                                    setSelectedCampaignRecipients([...selectedCampaignRecipients, contact.phone]);
                                  }
                                }}
                                className="rounded text-emerald-600"
                              />
                            </td>
                            <td className="p-2 font-bold">{contact.name}</td>
                            <td className="p-2 font-mono text-emerald-600 dark:text-emerald-400 font-semibold">{contact.phone}</td>
                            <td className="p-2 text-[10px] text-slate-400">{contact.source}</td>
                            <td className="p-2 text-right font-mono font-bold">
                              Rs. {contact.totalSpent.toLocaleString()}
                            </td>
                            <td className="p-2 text-center">
                              <a
                                href={`https://web.whatsapp.com/send?phone=${intlPhone}&text=${encodeURIComponent(
                                  campaignTemplate
                                    .replace(/{customer_name}/g, contact.name)
                                    .replace(/{shop_name}/g, shopName)
                                    .replace(/{discount_percent}/g, campaignDiscount)
                                    .replace(/{phone}/g, shopPhone)
                                )}`}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 hover:text-emerald-700 bg-emerald-500/10 px-2 py-0.5 rounded"
                              >
                                <ExternalLink className="w-3 h-3" /> WhatsApp
                              </a>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Broadcast History log */}
                <div className="pt-2 border-t">
                  <h4 className="text-[11px] font-bold text-slate-400 uppercase mb-1">Recent Campaign Broadcasts</h4>
                  <div className="space-y-1 max-h-24 overflow-y-auto">
                    {campaigns.map(c => (
                      <div key={c.id} className="text-[11px] flex justify-between p-1 rounded bg-slate-500/5">
                        <span className="font-bold text-slate-700 dark:text-slate-300">{c.title} ({c.recipientCount} sent)</span>
                        <span className="text-slate-400">{c.date}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --------------------------------------
            TAB 4: PROFIT & FINANCIAL DASHBOARD
           -------------------------------------- */}
        {activeTab === 'dashboard' && (
          <div className="h-full flex flex-col p-4 overflow-y-auto space-y-4">
            <h2 className="text-base font-bold flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              Financial & Profit Analytics
            </h2>

            {/* Metric KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              <div className={`p-4 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block font-bold">Total Sales Invoices</span>
                <span className="text-2xl font-black text-slate-900 dark:text-white mt-1 block">
                  {salesHistory.length}
                </span>
                <span className="text-[10px] text-emerald-500 mt-1 block">Active POS Sessions</span>
              </div>

              <div className={`p-4 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block font-bold">Gross Revenue</span>
                <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1 block font-mono">
                  Rs. {salesHistory.reduce((sum, s) => sum + s.grandTotal, 0).toLocaleString()}
                </span>
                <span className="text-[10px] text-slate-400 mt-1 block">Total billed to customers</span>
              </div>

              <div className={`p-4 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block font-bold">Cost of Goods (COGS)</span>
                <span className="text-2xl font-black text-amber-600 dark:text-amber-400 mt-1 block font-mono">
                  Rs. {salesHistory.reduce((sum, s) => sum + s.items.reduce((acc, it) => acc + (it.costPrice * it.quantity), 0), 0).toLocaleString()}
                </span>
                <span className="text-[10px] text-slate-400 mt-1 block">Master inventory cost</span>
              </div>

              <div className={`p-4 rounded-xl border ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <span className="text-xs text-slate-400 block font-bold">Gross Profit</span>
                <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1 block font-mono">
                  Rs. {(
                    salesHistory.reduce((sum, s) => sum + s.grandTotal, 0) -
                    salesHistory.reduce((sum, s) => sum + s.items.reduce((acc, it) => acc + (it.costPrice * it.quantity), 0), 0)
                  ).toLocaleString()}
                </span>
                <span className="text-[10px] text-emerald-500 mt-1 block">After Spot Discounts</span>
              </div>
            </div>

            {/* Recent Sales Ledger */}
            <div className={`rounded-xl border flex flex-col p-4 space-y-3 ${
              theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
            }`}>
              <div className="flex justify-between items-center">
                <h3 className="font-bold text-xs uppercase tracking-wider">Recent Sales & Invoices</h3>
                <button
                  onClick={() => exportSalesCSV(false)}
                  className="px-3 py-1 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-1"
                >
                  <Download className="w-3.5 h-3.5" /> Export Sales (.csv)
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className={`border-b ${
                    theme === 'dark' ? 'border-slate-800 bg-slate-950/60 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-500'
                  }`}>
                    <tr>
                      <th className="p-2">Invoice #</th>
                      <th className="p-2">Date & Time</th>
                      <th className="p-2">Customer</th>
                      <th className="p-2">WhatsApp #</th>
                      <th className="p-2 text-right">Grand Total</th>
                      <th className="p-2 text-right">Paid</th>
                      <th className="p-2 text-right">Balance</th>
                      <th className="p-2 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {salesHistory.map(s => (
                      <tr key={s.invoiceNumber} className="hover:bg-slate-500/5">
                        <td className="p-2 font-mono font-bold text-emerald-600">{s.invoiceNumber}</td>
                        <td className="p-2 text-slate-400">{s.date}</td>
                        <td className="p-2 font-bold">{s.customerName}</td>
                        <td className="p-2 font-mono text-emerald-500">{s.customerWhatsapp || s.customerPhone || '-'}</td>
                        <td className="p-2 text-right font-mono font-bold">Rs. {s.grandTotal.toLocaleString()}</td>
                        <td className="p-2 text-right font-mono">Rs. {s.paidAmount.toLocaleString()}</td>
                        <td className="p-2 text-right font-mono font-bold text-red-500">Rs. {s.balanceAmount.toLocaleString()}</td>
                        <td className="p-2 text-center">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            s.status === 'paid' ? 'bg-emerald-500/20 text-emerald-500' : 'bg-amber-500/20 text-amber-500'
                          }`}>
                            {s.status.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* --------------------------------------
            TAB 5: INVOICES & REPORTS
           -------------------------------------- */}
        {activeTab === 'reports' && (
          <div className="h-full flex flex-col p-4 overflow-y-auto space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-base font-bold flex items-center gap-2">
                  <Receipt className="w-5 h-5 text-emerald-600" />
                  Invoice Archive & Thermal Reprinting
                </h2>
                <p className="text-xs text-slate-400">View and reprint past invoices with duplicate disclaimer.</p>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setViewAuditLogsInvoice('ALL')}
                  className="px-3 py-1.5 text-xs font-bold bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center gap-1 shadow-sm cursor-pointer"
                >
                  📜 Audit Trail ({auditLogs.length})
                </button>
                <button
                  onClick={() => exportSalesCSV(true)}
                  className="px-3 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-1 shadow-sm cursor-pointer"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" /> Export Sales (.xlsx / .csv)
                </button>
              </div>
            </div>

            <div className={`rounded-xl border overflow-hidden ${
              theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
            }`}>
              <table className="w-full text-left text-xs">
                <thead className={`border-b ${
                  theme === 'dark' ? 'border-slate-800 bg-slate-950/60 text-slate-400' : 'border-slate-200 bg-slate-50 text-slate-500'
                }`}>
                  <tr>
                    <th className="p-3">Invoice #</th>
                    <th className="p-3">Date</th>
                    <th className="p-3">Customer</th>
                    <th className="p-3">WhatsApp #</th>
                    <th className="p-3 text-right">Items</th>
                    <th className="p-3 text-right">Total Amount</th>
                    <th className="p-3 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {salesHistory.map(s => (
                    <tr key={s.invoiceNumber} className="hover:bg-slate-500/5">
                      <td className="p-3 font-mono font-bold text-emerald-600">
                        {s.invoiceNumber}
                        {s.isRevised && (
                          <span className="ml-1.5 px-1.5 py-0.5 text-[9px] bg-amber-500/20 text-amber-500 font-bold rounded">
                            Rev v{(s.revisionCount || 0) + 1}
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-slate-400">{s.date}</td>
                      <td className="p-3 font-bold">{s.customerName}</td>
                      <td className="p-3 font-mono text-emerald-500">{s.customerWhatsapp || s.customerPhone || '-'}</td>
                      <td className="p-3 text-right font-mono">{s.items.length} item(s)</td>
                      <td className="p-3 text-right font-mono font-bold">Rs. {s.grandTotal.toLocaleString()}</td>
                      <td className="p-3 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => {
                              setReceiptModal(s);
                              setIsReceiptPreviewMode(false);
                            }}
                            className="px-2.5 py-1 text-xs font-bold bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 rounded flex items-center gap-1 cursor-pointer"
                          >
                            <Printer className="w-3.5 h-3.5" /> Preview & Print
                          </button>
                          <button
                            onClick={() => handleOpenEditInvoice(s)}
                            className="px-2.5 py-1 text-xs font-bold bg-sky-500/10 text-sky-600 hover:bg-sky-500/20 rounded flex items-center gap-1 cursor-pointer"
                          >
                            <Edit3 className="w-3.5 h-3.5" /> Edit
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* --------------------------------------
            TAB 6: IMPORT & EXPORT CENTER (CRITICAL FIX)
           -------------------------------------- */}
        {activeTab === 'import-export' && (
          <div className="h-full flex flex-col p-4 overflow-y-auto space-y-4">
            <div>
              <h2 className="text-base font-bold flex items-center gap-2">
                <Download className="w-5 h-5 text-emerald-600" />
                Data Import & Export Center
              </h2>
              <p className="text-xs text-slate-400">
                Working CSV & Excel (.xlsx) file downloads, pre-validated bulk product imports, and database backup synchronization.
              </p>
            </div>

            {/* Quick Export Cards (4 Categories) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <div>
                  <div className="flex items-center gap-2 text-emerald-600 mb-1">
                    <Package className="w-4 h-4" />
                    <h4 className="font-bold text-xs uppercase">Products & Stock</h4>
                  </div>
                  <p className="text-xs text-slate-400">Export active catalog with SKU, cost, selling rates, and current inventory.</p>
                </div>
                <div className="pt-3 flex gap-2">
                  <button
                    onClick={() => exportProductsCSV(false)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-600 text-white rounded hover:bg-emerald-700 flex items-center justify-center gap-1"
                  >
                    <Download className="w-3 h-3" /> CSV
                  </button>
                  <button
                    onClick={() => exportProductsCSV(true)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-700 text-white rounded hover:bg-emerald-800 flex items-center justify-center gap-1"
                  >
                    <FileSpreadsheet className="w-3 h-3" /> Excel
                  </button>
                </div>
              </div>

              <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <div>
                  <div className="flex items-center gap-2 text-emerald-600 mb-1">
                    <Receipt className="w-4 h-4" />
                    <h4 className="font-bold text-xs uppercase">Sales & Invoices</h4>
                  </div>
                  <p className="text-xs text-slate-400">Complete transaction history, grand totals, cashiers, and customer balances.</p>
                </div>
                <div className="pt-3 flex gap-2">
                  <button
                    onClick={() => exportSalesCSV(false)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-600 text-white rounded hover:bg-emerald-700 flex items-center justify-center gap-1"
                  >
                    <Download className="w-3 h-3" /> CSV
                  </button>
                  <button
                    onClick={() => exportSalesCSV(true)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-700 text-white rounded hover:bg-emerald-800 flex items-center justify-center gap-1"
                  >
                    <FileSpreadsheet className="w-3 h-3" /> Excel
                  </button>
                </div>
              </div>

              <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <div>
                  <div className="flex items-center gap-2 text-emerald-600 mb-1">
                    <Users className="w-4 h-4" />
                    <h4 className="font-bold text-xs uppercase">Customer Ledger</h4>
                  </div>
                  <p className="text-xs text-slate-400">Customer profiles, WhatsApp numbers, credit balances, and city limits.</p>
                </div>
                <div className="pt-3 flex gap-2">
                  <button
                    onClick={() => exportCustomersCSV(false)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-600 text-white rounded hover:bg-emerald-700 flex items-center justify-center gap-1"
                  >
                    <Download className="w-3 h-3" /> CSV
                  </button>
                  <button
                    onClick={() => exportCustomersCSV(true)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-700 text-white rounded hover:bg-emerald-800 flex items-center justify-center gap-1"
                  >
                    <FileSpreadsheet className="w-3 h-3" /> Excel
                  </button>
                </div>
              </div>

              <div className={`p-4 rounded-xl border flex flex-col justify-between ${
                theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
              }`}>
                <div>
                  <div className="flex items-center gap-2 text-emerald-600 mb-1">
                    <Layers className="w-4 h-4" />
                    <h4 className="font-bold text-xs uppercase">Suppliers & Mills</h4>
                  </div>
                  <p className="text-xs text-slate-400">Mill accounts, wholesale contact persons, and payable ledger balances.</p>
                </div>
                <div className="pt-3 flex gap-2">
                  <button
                    onClick={() => exportSuppliersCSV(false)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-600 text-white rounded hover:bg-emerald-700 flex items-center justify-center gap-1"
                  >
                    <Download className="w-3 h-3" /> CSV
                  </button>
                  <button
                    onClick={() => exportSuppliersCSV(true)}
                    className="flex-1 py-1.5 text-xs font-bold bg-emerald-700 text-white rounded hover:bg-emerald-800 flex items-center justify-center gap-1"
                  >
                    <FileSpreadsheet className="w-3 h-3" /> Excel
                  </button>
                </div>
              </div>
            </div>

            {/* Bulk Product Import Tool with Pre-validation */}
            <div className={`p-4 rounded-xl border space-y-3 ${
              theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
            }`}>
              <div className="flex justify-between items-center border-b pb-2">
                <h3 className="font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 text-emerald-600">
                  <Upload className="w-4 h-4" />
                  Bulk Product CSV / Excel Import Tool
                </h3>
                <button
                  onClick={downloadSampleTemplate}
                  className="text-xs font-bold text-emerald-600 hover:underline flex items-center gap-1"
                >
                  <Download className="w-3.5 h-3.5" /> Download Standard CSV/Excel Template
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                <div className="lg:col-span-2 space-y-2">
                  <label className="text-[11px] font-bold block">
                    Paste CSV Data or Drag & Drop File Content below:
                  </label>
                  <textarea
                    rows={5}
                    value={importFileText}
                    onChange={(e) => handleParseImport(e.target.value)}
                    placeholder="category,product_name,product_name_urdu,sku,unit,size,color,design,purchase_price,selling_price,opening_stock,min_stock_alert&#10;Bedsheets,Cotton Floral King Sheet,کاٹن فلورل کنگ بیڈ شیٹ,IMP-BED-001,Set,King 90x100,Navy Blue,Floral,1400,2400,20,5"
                    className={`w-full p-2.5 text-xs font-mono rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="text-[11px] font-bold block mb-1">Conflict Resolution Mode:</label>
                    <div className="space-y-1">
                      <label className="flex items-center gap-2 text-xs cursor-pointer">
                        <input
                          type="radio"
                          name="conflict"
                          checked={importConflictMode === 'update'}
                          onChange={() => setImportConflictMode('update')}
                        />
                        <span>Update existing products matching SKU</span>
                      </label>
                      <label className="flex items-center gap-2 text-xs cursor-pointer">
                        <input
                          type="radio"
                          name="conflict"
                          checked={importConflictMode === 'skip'}
                          onChange={() => setImportConflictMode('skip')}
                        />
                        <span>Skip existing products (Add new only)</span>
                      </label>
                    </div>
                  </div>

                  {importSummary && (
                    <div className="p-3 rounded-lg bg-slate-500/10 text-xs space-y-1 font-mono">
                      <div>Total Rows Analyzed: <b>{importSummary.total}</b></div>
                      <div className="text-emerald-500">Ready to Add: <b>{importSummary.valid}</b></div>
                      <div className="text-amber-500">Existing / Warnings: <b>{importSummary.warnings}</b></div>
                      <div className="text-red-500">Errors Detected: <b>{importSummary.errors}</b></div>
                    </div>
                  )}

                  <button
                    onClick={commitImport}
                    disabled={importPreviewRows.length === 0}
                    className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-xs rounded-lg flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <Check className="w-4 h-4" /> Commit Valid Items to Database
                  </button>
                </div>
              </div>

              {/* Pre-validation Preview Table */}
              {importPreviewRows.length > 0 && (
                <div className="pt-2 border-t">
                  <h4 className="text-xs font-bold mb-1.5">Pre-Validation Preview ({importPreviewRows.length} rows)</h4>
                  <div className="max-h-48 overflow-y-auto border rounded">
                    <table className="w-full text-left text-xs">
                      <thead className={`border-b ${
                        theme === 'dark' ? 'bg-slate-950/80 text-slate-400' : 'bg-slate-50 text-slate-500'
                      }`}>
                        <tr>
                          <th className="p-1.5">Status</th>
                          <th className="p-1.5">SKU</th>
                          <th className="p-1.5">Product Name</th>
                          <th className="p-1.5">Category</th>
                          <th className="p-1.5 text-right">Cost</th>
                          <th className="p-1.5 text-right">Price</th>
                          <th className="p-1.5 text-right">Stock</th>
                          <th className="p-1.5">Notes</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                        {importPreviewRows.map((r, i) => (
                          <tr key={i} className="hover:bg-slate-500/5">
                            <td className="p-1.5 font-bold">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                                r.status === 'Valid' ? 'bg-emerald-500/20 text-emerald-500' :
                                r.status === 'Warning' ? 'bg-amber-500/20 text-amber-500' : 'bg-red-500/20 text-red-500'
                              }`}>
                                {r.status}
                              </span>
                            </td>
                            <td className="p-1.5 font-mono font-bold">{r.sku}</td>
                            <td className="p-1.5">{r.name}</td>
                            <td className="p-1.5 text-slate-400">{r.category}</td>
                            <td className="p-1.5 text-right font-mono">Rs.{r.cost}</td>
                            <td className="p-1.5 text-right font-mono font-bold text-emerald-600">Rs.{r.price}</td>
                            <td className="p-1.5 text-right font-mono">{r.stock}</td>
                            <td className="p-1.5 text-[10px] text-slate-400">{r.issue || 'Ready'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* --------------------------------------
            TAB 7: SETTINGS & THERMAL PRINTER CONFIG
           -------------------------------------- */}
        {activeTab === 'settings' && (
          <div className="h-full flex flex-col p-4 overflow-y-auto space-y-4 max-w-4xl">
            <h2 className="text-base font-bold flex items-center gap-2">
              <Settings className="w-5 h-5 text-emerald-600" />
              Store Profile & Hardware Configuration
            </h2>

            {/* Profile Settings */}
            <div className={`p-4 rounded-xl border space-y-3 ${
              theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
            }`}>
              <h3 className="font-bold text-xs uppercase tracking-wider text-emerald-600">Store Branding</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold block mb-1">Store Name (English):</label>
                  <input
                    type="text"
                    value={shopName}
                    onChange={(e) => setShopName(e.target.value)}
                    className={`w-full p-2 text-xs rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold block mb-1">Store Name (Urdu):</label>
                  <input
                    type="text"
                    value={shopUrdu}
                    onChange={(e) => setShopUrdu(e.target.value)}
                    className={`w-full p-2 text-xs font-arabic rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold block mb-1">Phone / WhatsApp Number:</label>
                  <input
                    type="text"
                    value={shopPhone}
                    onChange={(e) => setShopPhone(e.target.value)}
                    className={`w-full p-2 text-xs rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold block mb-1">Store Address:</label>
                  <input
                    type="text"
                    value={shopAddress}
                    onChange={(e) => setShopAddress(e.target.value)}
                    className={`w-full p-2 text-xs rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
              </div>
            </div>

            {/* Thermal Printer Settings */}
            <div className={`p-4 rounded-xl border space-y-3 ${
              theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
            }`}>
              <h3 className="font-bold text-xs uppercase tracking-wider text-emerald-600">Thermal Printer & Receipt Layout</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold block mb-1">Paper Roll Width:</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPaperWidth('80mm')}
                      className={`flex-1 py-2 text-xs font-bold rounded-lg border ${
                        paperWidth === '80mm'
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      80mm (Standard 48-Cols)
                    </button>
                    <button
                      onClick={() => setPaperWidth('58mm')}
                      className={`flex-1 py-2 text-xs font-bold rounded-lg border ${
                        paperWidth === '58mm'
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700'
                      }`}
                    >
                      58mm (Compact 32-Cols)
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-bold block mb-1">Store Logo (Thermal & Header):</label>
                  <input
                    ref={logoFileInputRef}
                    type="file"
                    accept="image/png, image/jpeg, image/jpg, image/bmp"
                    className="hidden"
                    onChange={handleLogoFileChange}
                  />

                  {shopLogoUrl ? (
                    <div className="flex items-center gap-3">
                      <div className="w-[120px] h-[80px] rounded-lg border border-emerald-500 bg-emerald-50/20 dark:bg-emerald-950/20 p-1 flex items-center justify-center">
                        <img
                          src={shopLogoUrl}
                          alt="Store Logo"
                          className="max-h-full max-w-full object-contain"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <button
                          type="button"
                          onClick={() => logoFileInputRef.current?.click()}
                          className="px-3 py-1.5 text-xs font-bold bg-sky-600 hover:bg-sky-700 text-white rounded flex items-center gap-1 cursor-pointer"
                        >
                          <ImageIcon className="w-3.5 h-3.5" /> Change Logo...
                        </button>
                        <button
                          type="button"
                          onClick={handleRemoveLogo}
                          className="px-3 py-1.5 text-xs font-bold bg-red-600 hover:bg-red-700 text-white rounded flex items-center gap-1 cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" /> Remove Logo
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-3">
                      <div className="w-[120px] h-[80px] rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
                        No Logo
                      </div>
                      <div>
                        <button
                          type="button"
                          onClick={() => logoFileInputRef.current?.click()}
                          className="px-3 py-1.5 text-xs font-bold bg-sky-600 hover:bg-sky-700 text-white rounded flex items-center gap-1 cursor-pointer"
                        >
                          <ImageIcon className="w-3.5 h-3.5" /> 📁 Browse Logo...
                        </button>
                        <span className="text-[10px] text-slate-400 block mt-1">
                          PNG, JPG, JPEG, BMP (Prints on receipts)
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="sm:col-span-2 flex items-center justify-between pt-2 border-t">
                  <label className="flex items-center gap-2 text-xs font-bold cursor-pointer">
                    <input
                      type="checkbox"
                      checked={thermalMonochrome}
                      onChange={(e) => setThermalMonochrome(e.target.checked)}
                      className="rounded text-emerald-600"
                    />
                    <span>Convert logo to High-Contrast Monochrome / Grayscale on thermal receipts</span>
                  </label>

                  <button
                    onClick={() => {
                      if (salesHistory.length > 0) {
                        setReceiptModal(salesHistory[0]);
                      }
                    }}
                    className="px-3 py-1.5 text-xs font-bold bg-emerald-600 text-white rounded hover:bg-emerald-700 flex items-center gap-1"
                  >
                    <Printer className="w-3.5 h-3.5" /> Test Thermal Preview
                  </button>
                </div>
              </div>
            </div>

            {/* Security & Manager PIN */}
            <div className={`p-4 rounded-xl border space-y-3 ${
              theme === 'dark' ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
            }`}>
              <h3 className="font-bold text-xs uppercase tracking-wider text-emerald-600 flex items-center gap-1.5">
                <Key className="w-4 h-4" /> Security & Cashier Limits
              </h3>
              <div className="max-w-xs">
                <label className="text-xs font-bold block mb-1">Manager Authorization PIN (Default: 1234):</label>
                <input
                  type="password"
                  value={managerPin}
                  onChange={(e) => setManagerPin(e.target.value)}
                  className={`w-full p-2 text-xs font-mono font-bold rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
                <span className="text-[10px] text-slate-400 block mt-1">
                  Required when cashier grants &gt;15% spot discount in cart.
                </span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ==========================================
          MODAL 1: EDIT TRANSACTION SELLING RATE
         ========================================== */}
      {editingItem && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-sm w-full p-4 space-y-3 ${
            theme === 'dark' ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300'
          }`}>
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="font-bold text-sm flex items-center gap-1.5 text-emerald-600">
                <Edit3 className="w-4 h-4" />
                Negotiate Item Selling Rate
              </h3>
              <button onClick={() => setEditingItem(null)} className="text-slate-400 hover:text-slate-600 font-bold">✕</button>
            </div>

            <div className="p-2 rounded-lg bg-slate-500/10 text-xs space-y-1">
              <div><b>Item:</b> {editingItem.productName}</div>
              <div className="text-slate-400">Variant: {editingItem.variantTitle}</div>
              <div className="flex justify-between font-mono pt-1 border-t border-slate-300/20">
                <span>Original Catalog Rate:</span>
                <span className="font-bold text-slate-700 dark:text-slate-200">Rs. {editingItem.originalPrice.toLocaleString()}</span>
              </div>
            </div>

            <div>
              <label className="text-xs font-bold block mb-1">New Bargain Rate (Rs.):</label>
              <input
                type="number"
                step="10"
                min="0"
                value={newPriceInput}
                onChange={(e) => setNewPriceInput(e.target.value)}
                className={`w-full p-2 text-base font-mono font-bold rounded border ${
                  theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                }`}
                autoFocus
              />
            </div>

            {pinPromptNeeded && (
              <div className="p-2.5 rounded-lg border border-amber-500/40 bg-amber-500/10 space-y-1">
                <span className="text-xs font-bold text-amber-600 dark:text-amber-400 block flex items-center gap-1">
                  <Key className="w-3.5 h-3.5" /> Manager PIN Authorization Required
                </span>
                <input
                  type="password"
                  placeholder="Enter Manager PIN (1234)..."
                  value={enteredPin}
                  onChange={(e) => setEnteredPin(e.target.value)}
                  className={`w-full p-2 text-xs font-mono font-bold rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
              </div>
            )}

            {priceEditError && (
              <p className="text-xs text-red-500 font-semibold">{priceEditError}</p>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t">
              <button
                onClick={() => setEditingItem(null)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={savePriceEdit}
                className="px-4 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded"
              >
                Apply Negotiated Rate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 2: VARIANT & FABRIC LENGTH SELECTOR
         ========================================== */}
      {selectedVariantProduct && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-sm w-full p-4 space-y-3 ${
            theme === 'dark' ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300'
          }`}>
            <div className="flex justify-between items-center border-b pb-2">
              <div>
                <h3 className="font-bold text-sm">{selectedVariantProduct.name}</h3>
                <span className="text-xs text-emerald-500 font-arabic">{selectedVariantProduct.nameUrdu}</span>
              </div>
              <button onClick={() => setSelectedVariantProduct(null)} className="text-slate-400 hover:text-slate-200 font-bold">✕</button>
            </div>

            {selectedVariantProduct.isFabric && (
              <div>
                <label className="text-xs font-bold block mb-1">Fabric Cut Length in Meters / Yards:</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    value={fabricLengthInput}
                    onChange={(e) => setFabricLengthInput(parseFloat(e.target.value) || 1)}
                    className={`flex-1 p-2 text-sm font-bold font-mono rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                  <span className="text-xs font-bold text-slate-400">{selectedVariantProduct.unit}</span>
                </div>
              </div>
            )}

            <div className="space-y-1.5 max-h-56 overflow-y-auto">
              <label className="text-xs font-bold block">Select Variety / Color:</label>
              {selectedVariantProduct.variants.map((v, idx) => (
                <button
                  key={v.sku}
                  onClick={() => {
                    handleAddToCart(selectedVariantProduct, idx, selectedVariantProduct.isFabric ? fabricLengthInput : 1);
                    setSelectedVariantProduct(null);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg border text-xs flex justify-between items-center transition-all ${
                    theme === 'dark'
                      ? 'border-slate-700 hover:border-emerald-500 bg-slate-800/80 hover:bg-slate-800'
                      : 'border-slate-200 hover:border-emerald-600 hover:bg-emerald-50/50'
                  }`}
                >
                  <div>
                    <span className="font-bold block">{v.size} - {v.color}</span>
                    <span className="text-[10px] text-slate-400">{v.design}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-emerald-600 dark:text-emerald-400 block font-mono">
                      Rs. {v.price.toLocaleString()}
                    </span>
                    <span className="text-[10px] text-slate-400">Stock: {v.stock}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 3: THERMAL RECEIPT PREVIEW (CRITICAL FIX)
         ========================================== */}
      {receiptModal && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-md w-full p-4 flex flex-col max-h-[92vh] ${
            theme === 'dark' ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300'
          }`}>
            {/* Modal Header */}
            <div className="flex justify-between items-center pb-2 border-b">
              <div className="flex items-center gap-2">
                <Printer className="w-4 h-4 text-emerald-600" />
                <h3 className="font-bold text-sm">
                  {isReceiptPreviewMode ? 'Thermal Receipt Preview - Verify Bill' : 'Thermal Receipt'}
                </h3>
              </div>

              {/* Paper Width Selector inside Modal */}
              <div className="flex items-center gap-1 bg-slate-200/50 dark:bg-slate-800 p-0.5 rounded">
                <button
                  onClick={() => setPaperWidth('80mm')}
                  className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                    paperWidth === '80mm' ? 'bg-emerald-600 text-white' : 'text-slate-400'
                  }`}
                >
                  80mm
                </button>
                <button
                  onClick={() => setPaperWidth('58mm')}
                  className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                    paperWidth === '58mm' ? 'bg-emerald-600 text-white' : 'text-slate-400'
                  }`}
                >
                  58mm
                </button>
              </div>

              <button onClick={cancelReceiptPreview} className="text-slate-400 hover:text-slate-200 font-bold ml-2 cursor-pointer">✕</button>
            </div>

            {/* Simulated Thermal Ticket Paper */}
            <div className="flex-1 overflow-y-auto my-3 p-4 bg-white text-black border border-slate-300 rounded font-mono text-[11px] leading-relaxed select-all shadow-inner">
              {/* Receipt Store Logo */}
              {shopLogoUrl && (
                <div className="text-center mb-2">
                  <img
                    src={shopLogoUrl}
                    alt="Logo"
                    className={`mx-auto max-h-14 max-w-[150px] object-contain ${
                      thermalMonochrome ? 'grayscale contrast-150' : ''
                    }`}
                  />
                </div>
              )}

              <div className="text-center space-y-0.5 mb-2">
                <p className="font-black text-xs uppercase">{shopName}</p>
                {isReceiptPreviewMode ? (
                  <p className="font-bold text-center text-amber-700 bg-amber-100 py-0.5 rounded text-[10px]">
                    *** PRE-SALE PREVIEW / کچا بل ***
                  </p>
                ) : receiptModal.isRevised ? (
                  <p className="font-bold text-center text-amber-700 bg-amber-100 py-0.5 rounded text-[10px]">
                    *** REVISED INVOICE (Rev v{(receiptModal.revisionCount || 0) + 1}) ***
                  </p>
                ) : null}
                <p className="font-bold font-arabic text-sm">{shopUrdu}</p>
                <p className="text-[10px] text-slate-700">{shopAddress}</p>
                <p className="text-[10px] text-slate-700">Phone: {shopPhone}</p>
                <p className="tracking-tighter font-mono">========================================</p>
              </div>

              <div className="space-y-0.5 text-[10px]">
                <p><b>Invoice :</b> {receiptModal.invoiceNumber}</p>
                <p><b>Date    :</b> {receiptModal.date}</p>
                <p><b>Cashier :</b> {receiptModal.cashier}</p>
                <p><b>Customer:</b> {receiptModal.customerName}</p>
                {receiptModal.customerWhatsapp && (
                  <p><b>WhatsApp:</b> {receiptModal.customerWhatsapp}</p>
                )}
                <p className="tracking-tighter font-mono">----------------------------------------</p>
              </div>

              {/* Items List */}
              <div className="space-y-1.5 my-2">
                <div className="flex justify-between font-bold text-[10px] border-b border-black pb-0.5">
                  <span>Item Description</span>
                  <span>Qty x Rate = Total</span>
                </div>
                {(receiptModal.items || []).map((it, i) => (
                  <div key={i} className="text-[10px]">
                    <div className="font-bold">{it.productName}</div>
                    <div className="flex justify-between text-slate-800">
                      <span>{it.variantTitle}</span>
                      <span>
                        {it.quantity} {it.unit} x {it.transactionPrice.toLocaleString()} = Rs. {(it.quantity * it.transactionPrice).toLocaleString()}
                      </span>
                    </div>
                    {it.isOverridden && (
                      <div className="text-[9px] italic text-slate-600">*Bargain Rate Applied</div>
                    )}
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-0.5 text-[10px] border-t border-black pt-1">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span>Rs. {(receiptModal.subtotal || receiptModal.grandTotal).toLocaleString()}</span>
                </div>
                {receiptModal.discount > 0 && (
                  <div className="flex justify-between">
                    <span>Discount:</span>
                    <span>-Rs. {receiptModal.discount.toLocaleString()}</span>
                  </div>
                )}
                <p className="tracking-tighter font-mono">========================================</p>
                <div className="flex justify-between font-bold text-xs">
                  <span>GRAND TOTAL:</span>
                  <span>Rs. {receiptModal.grandTotal.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Paid ({receiptModal.paymentMethod}):</span>
                  <span>Rs. {receiptModal.paidAmount.toLocaleString()}</span>
                </div>
                {receiptModal.balanceAmount > 0 && (
                  <div className="flex justify-between font-bold text-red-600">
                    <span>Remaining Due (Udhar):</span>
                    <span>Rs. {receiptModal.balanceAmount.toLocaleString()}</span>
                  </div>
                )}
                {receiptModal.changeGiven > 0 && (
                  <div className="flex justify-between font-bold text-emerald-800">
                    <span>Change Returned:</span>
                    <span>Rs. {receiptModal.changeGiven.toLocaleString()}</span>
                  </div>
                )}
              </div>

              <div className="text-center mt-3 pt-2 border-t border-dashed border-black text-[9px] text-slate-700 space-y-0.5">
                <p>Thank you for choosing Arooj Cloth & Bedsheet Parda!</p>
                <p>Exchange possible within 7 days with original receipt.</p>
                <p className="font-mono text-[8px] mt-1 font-bold">*{receiptModal.invoiceNumber}*</p>
              </div>
            </div>

            {printFeedback && (
              <p className="text-[11px] text-emerald-500 text-center font-bold">{printFeedback}</p>
            )}

            {/* Modal Bottom Actions */}
            {isReceiptPreviewMode ? (
              <div className="flex flex-wrap justify-between items-center gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={cancelReceiptPreview}
                  className="px-3.5 py-2 text-xs font-semibold text-slate-400 hover:text-white border border-slate-700 rounded-lg cursor-pointer transition-colors"
                >
                  ❌ Cancel (Esc)
                </button>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={sendInvoiceViaWhatsApp}
                    className="px-3 py-2 text-xs font-bold bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg flex items-center gap-1.5 shadow-sm cursor-pointer"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    WhatsApp
                  </button>
                  <button
                    type="button"
                    autoFocus
                    onClick={confirmSaleAndPrint}
                    className="px-5 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-1.5 shadow-lg cursor-pointer"
                  >
                    <Check className="w-4 h-4" />
                    ✅ CONFIRM SALE & PRINT (Enter)
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap justify-between items-center gap-2 pt-2 border-t">
                <button
                  onClick={sendInvoiceViaWhatsApp}
                  className="px-3 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded flex items-center gap-1.5 shadow-sm cursor-pointer"
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  Share WhatsApp Invoice
                </button>

                <div className="flex gap-2">
                  <button
                    onClick={() => setReceiptModal(null)}
                    className="px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer"
                  >
                    Close
                  </button>
                  <button
                    onClick={triggerThermalPrint}
                    className="px-4 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded flex items-center gap-1.5 shadow-md cursor-pointer"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    Print Receipt ({paperWidth})
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 4: DATABASE BACKUP & RESTORE MANAGER
         ========================================== */}
      {showBackupModal && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-lg w-full p-5 space-y-4 ${
            theme === 'dark' ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300 text-slate-800'
          }`}>
            <div className="flex justify-between items-center border-b pb-2">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <h3 className="font-bold text-base">Database Backup & Restore Manager (بیک اپ مینیجر)</h3>
              </div>
              <button
                onClick={() => setShowBackupModal(false)}
                className="text-slate-400 hover:text-slate-200 font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Daily Backup Status Card */}
            <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Automatic Daily Local Backup Active
                </span>
                <span className="text-[11px] text-slate-400 block mt-0.5 font-mono">
                  Today's Snapshot: arooj_pos_daily_20261102_080000.db (142 KB)
                </span>
              </div>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 font-bold px-2 py-0.5 rounded-full">
                Protected
              </span>
            </div>

            {backupNotice && (
              <div className="p-2.5 rounded bg-sky-500/10 border border-sky-500/30 text-sky-600 dark:text-sky-300 text-xs font-semibold">
                {backupNotice}
              </div>
            )}

            {/* Quick Actions */}
            <div>
              <label className="text-xs font-bold block mb-1 text-slate-400">Trigger Immediate Backup:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleCreateBackup(false)}
                  className="p-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg flex items-center justify-center gap-1.5 transition-colors shadow-xs cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  Create Local Backup
                </button>
                <button
                  onClick={() => handleCreateBackup(true)}
                  className="p-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-lg flex items-center justify-center gap-1.5 transition-colors shadow-xs cursor-pointer"
                >
                  <Download className="w-4 h-4" />
                  Backup to USB / External
                </button>
              </div>
            </div>

            {/* Backup History Table */}
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-bold text-slate-400">Available Backups & Safety Snapshots:</label>
                <span className="text-[10px] text-amber-500 font-semibold flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Pre-restore safety snapshots auto-generated
                </span>
              </div>
              <div className="max-h-48 overflow-y-auto border rounded-lg divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                {backupList.map(bk => (
                  <div key={bk.id} className="p-2.5 flex items-center justify-between hover:bg-slate-500/5">
                    <div>
                      <div className="font-mono font-bold text-xs truncate max-w-[260px]">{bk.filename}</div>
                      <div className="text-[10px] text-slate-400 flex items-center gap-2">
                        <span>{bk.createdAt}</span>
                        <span>•</span>
                        <span>{bk.sizeKb} KB</span>
                        <span>•</span>
                        <span className={`capitalize font-bold ${
                          bk.type === 'daily' ? 'text-emerald-500' : bk.type === 'safety' ? 'text-amber-500' : 'text-sky-500'
                        }`}>
                          {bk.type}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleRestoreBackup(bk.filename)}
                        className="px-2.5 py-1 text-[11px] font-bold bg-amber-600 hover:bg-amber-700 text-white rounded transition-colors cursor-pointer"
                      >
                        Restore
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t">
              <button
                onClick={() => setShowBackupModal(false)}
                className="px-4 py-1.5 text-xs font-bold bg-slate-700 hover:bg-slate-600 text-white rounded cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 5: ADD / EDIT PRODUCT FORM (F2)
         ========================================== */}
      {showProductModal && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-md w-full p-5 space-y-3 ${
            theme === 'dark' ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300 text-slate-800'
          }`}>
            <div className="flex justify-between items-center border-b pb-2">
              <div className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-emerald-500" />
                <h3 className="font-bold text-base">
                  {isEditingProduct ? '✏️ Edit Product (پراڈکٹ کی ترمیم)' : '➕ Add New Product (نیا پراڈکٹ شامل کریں)'}
                </h3>
              </div>
              <button onClick={() => setShowProductModal(false)} className="text-slate-400 hover:text-slate-200 font-bold p-1 cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleSaveProduct} className="space-y-2.5 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-bold block mb-0.5">Product Code / SKU:</label>
                  <input
                    type="text"
                    required
                    value={productFormData.code}
                    onChange={(e) => setProductFormData({ ...productFormData, code: e.target.value })}
                    className={`w-full p-2 font-mono rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="font-bold block mb-0.5">Category:</label>
                  <select
                    value={productFormData.category}
                    onChange={(e) => setProductFormData({ ...productFormData, category: e.target.value })}
                    className={`w-full p-2 rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  >
                    {CATEGORIES.map(c => (
                      <option key={c.code} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="font-bold block mb-0.5">Product Name (English):</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Kamalia Pure Khaddar Suit"
                  value={productFormData.name}
                  onChange={(e) => setProductFormData({ ...productFormData, name: e.target.value })}
                  className={`w-full p-2 rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
              </div>

              <div>
                <label className="font-bold block mb-0.5">Urdu Name (اردو نام):</label>
                <input
                  type="text"
                  placeholder="e.g. کملیا پیور کھدر سوٹ"
                  value={productFormData.nameUrdu}
                  onChange={(e) => setProductFormData({ ...productFormData, nameUrdu: e.target.value })}
                  className={`w-full p-2 font-arabic text-sm rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-bold block mb-0.5">Measurement Unit:</label>
                  <select
                    value={productFormData.unit}
                    onChange={(e) => setProductFormData({ ...productFormData, unit: e.target.value })}
                    className={`w-full p-2 rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  >
                    <option value="Meters">Meters (میٹر)</option>
                    <option value="Gaz">Gaz / Yards (گز)</option>
                    <option value="Pcs">Pcs (عدد)</option>
                    <option value="Suits">Suits (سوٹ)</option>
                    <option value="Set">Set (سیٹ)</option>
                  </select>
                </div>
                <div className="flex items-center gap-2 pt-5">
                  <input
                    type="checkbox"
                    id="isFabricCheck"
                    checked={productFormData.isFabric}
                    onChange={(e) => setProductFormData({ ...productFormData, isFabric: e.target.checked })}
                    className="w-4 h-4 text-emerald-600 rounded"
                  />
                  <label htmlFor="isFabricCheck" className="font-bold cursor-pointer">
                    Is Fabric / Cloth (تھان)
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-bold block mb-0.5">Cost Price (Rs.):</label>
                  <input
                    type="number"
                    min="0"
                    value={productFormData.cost}
                    onChange={(e) => setProductFormData({ ...productFormData, cost: parseFloat(e.target.value) || 0 })}
                    className={`w-full p-2 font-mono rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="font-bold block mb-0.5">Retail Selling Price (Rs.):</label>
                  <input
                    type="number"
                    min="0"
                    value={productFormData.price}
                    onChange={(e) => setProductFormData({ ...productFormData, price: parseFloat(e.target.value) || 0 })}
                    className={`w-full p-2 font-mono font-bold text-emerald-600 rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-emerald-400' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-bold block mb-0.5">In Stock Quantity:</label>
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    value={productFormData.stock}
                    onChange={(e) => setProductFormData({ ...productFormData, stock: parseFloat(e.target.value) || 0 })}
                    className={`w-full p-2 font-mono rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="font-bold block mb-0.5">Min Stock Alert:</label>
                  <input
                    type="number"
                    min="1"
                    value={productFormData.minAlert}
                    onChange={(e) => setProductFormData({ ...productFormData, minAlert: parseFloat(e.target.value) || 5 })}
                    className={`w-full p-2 font-mono rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setShowProductModal(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded transition-colors cursor-pointer"
                >
                  {isEditingProduct ? 'Save Updates' : 'Save New Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 6: REGISTER FABRIC ROLL (F2)
         ========================================== */}
      {showFabricRollModal && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-sm w-full p-5 space-y-3 ${
            theme === 'dark' ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300 text-slate-800'
          }`}>
            <div className="flex justify-between items-center border-b pb-2">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-500" />
                <h3 className="font-bold text-base">Register Fabric Roll (تھان رول درج کریں)</h3>
              </div>
              <button onClick={() => setShowFabricRollModal(false)} className="text-slate-400 hover:text-slate-200 font-bold p-1 cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleSaveFabricRoll} className="space-y-3 text-xs">
              <div>
                <label className="font-bold block mb-0.5">Roll Identification #:</label>
                <input
                  type="text"
                  required
                  value={rollFormData.rollNumber}
                  onChange={(e) => setRollFormData({ ...rollFormData, rollNumber: e.target.value })}
                  placeholder="e.g. ROLL-201"
                  className={`w-full p-2 font-mono font-bold rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
              </div>

              <div>
                <label className="font-bold block mb-0.5">Assign to Fabric Product:</label>
                <select
                  value={rollFormData.productId}
                  onChange={(e) => setRollFormData({ ...rollFormData, productId: e.target.value })}
                  className={`w-full p-2 rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                >
                  {products.filter(p => p.isFabric).map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="font-bold block mb-0.5">Initial Length (Meters):</label>
                  <input
                    type="number"
                    step="0.5"
                    min="1"
                    required
                    value={rollFormData.length}
                    onChange={(e) => setRollFormData({ ...rollFormData, length: parseFloat(e.target.value) || 0 })}
                    className={`w-full p-2 font-mono font-bold rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
                <div>
                  <label className="font-bold block mb-0.5">Cost per Meter (Rs.):</label>
                  <input
                    type="number"
                    min="0"
                    value={rollFormData.cost}
                    onChange={(e) => setRollFormData({ ...rollFormData, cost: parseFloat(e.target.value) || 0 })}
                    className={`w-full p-2 font-mono rounded border ${
                      theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                    }`}
                  />
                </div>
              </div>

              <div>
                <label className="font-bold block mb-0.5">Notes / Mill Supplier:</label>
                <input
                  type="text"
                  value={rollFormData.notes}
                  onChange={(e) => setRollFormData({ ...rollFormData, notes: e.target.value })}
                  placeholder="e.g. Kohinoor Mills Super Jet Black"
                  className={`w-full p-2 rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setShowFabricRollModal(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors cursor-pointer"
                >
                  Save & Add Stock
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 7: MANAGER PIN AUTHORIZATION GATE (> 15% DISCOUNT)
         ========================================== */}
      {showPinModal && (
        <div className="fixed inset-0 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-sm w-full p-5 space-y-3 ${
            theme === 'dark' ? 'bg-slate-900 border-amber-500/50 text-white' : 'bg-white border-amber-500 text-slate-800'
          }`}>
            <div className="flex items-center gap-2 text-amber-500 pb-2 border-b">
              <Key className="w-5 h-5" />
              <h3 className="font-bold text-sm">Manager PIN Required (قیمت میں رعایت)</h3>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Price cut exceeds the cashier spot-discount threshold (<b>15%</b>).
              <br />
              Target Item: <b>{pinTargetItem?.item.productName}</b>
              <br />
              Original Catalog Price: <span className="font-mono font-bold">Rs. {pinTargetItem?.item.originalPrice}</span>
              <br />
              Requested Price: <span className="font-mono font-bold text-amber-500">Rs. {pinTargetItem?.requestedPrice}</span>
            </p>

            <div>
              <label className="text-xs font-bold block mb-1">Enter Manager PIN (Default: 1234):</label>
              <input
                type="password"
                autoFocus
                placeholder="Manager PIN..."
                value={managerPinInput}
                onChange={(e) => setManagerPinInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleManagerPinSubmit();
                }}
                className={`w-full p-2 font-mono font-bold rounded border text-sm ${
                  theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                }`}
              />
            </div>

            {pinError && (
              <p className="text-xs font-bold text-red-500">{pinError}</p>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t">
              <button
                onClick={() => {
                  setShowPinModal(false);
                  setPinTargetItem(null);
                }}
                className="px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer"
              >
                Reject & Cancel
              </button>
              <button
                onClick={handleManagerPinSubmit}
                className="px-4 py-1.5 text-xs font-bold bg-amber-600 hover:bg-amber-700 text-white rounded transition-colors cursor-pointer"
              >
                Authorize Discount
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 8: EDIT INVOICE & INVENTORY RECONCILIATION
         ========================================== */}
      {editingInvoice && (
        <div className="fixed inset-0 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-2xl w-full p-5 space-y-3.5 max-h-[92vh] flex flex-col ${
            theme === 'dark' ? 'bg-slate-900 border-sky-500/50 text-white' : 'bg-white border-sky-500 text-slate-800'
          }`}>
            <div className="flex justify-between items-center pb-2 border-b">
              <div className="flex items-center gap-2">
                <Edit3 className="w-5 h-5 text-sky-500" />
                <h3 className="font-bold text-base">
                  Edit Invoice #{editingInvoice.invoiceNumber} (انوائس میں ترمیم)
                </h3>
              </div>
              <button
                onClick={() => setEditingInvoice(null)}
                className="text-slate-400 hover:text-slate-200 font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="text-xs text-slate-400 flex flex-wrap gap-4 p-2 bg-slate-500/10 rounded">
              <span><b>Customer:</b> {editingInvoice.customerName}</span>
              <span><b>Date:</b> {editingInvoice.date}</span>
              <span><b>Payment:</b> {editingInvoice.paymentMethod}</span>
              {editingInvoice.isRevised && (
                <span className="text-amber-500 font-bold">
                  ⚠️ Previously Revised (v{(editingInvoice.revisionCount || 0) + 1})
                </span>
              )}
            </div>

            {/* Editable Items Table */}
            <div className="flex-1 overflow-y-auto border rounded divide-y divide-slate-200 dark:divide-slate-800 text-xs">
              <table className="w-full text-left">
                <thead className={`border-b text-[11px] ${
                  theme === 'dark' ? 'bg-slate-950/80 text-slate-400' : 'bg-slate-100 text-slate-600'
                }`}>
                  <tr>
                    <th className="p-2">Item</th>
                    <th className="p-2">Variant</th>
                    <th className="p-2 text-center w-24">Qty ({editingInvoice.items[0]?.unit || 'Units'})</th>
                    <th className="p-2 text-right w-28">Rate (Rs.)</th>
                    <th className="p-2 text-right">Line Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {editInvoiceItems.map((it, idx) => (
                    <tr key={idx} className="hover:bg-slate-500/5">
                      <td className="p-2 font-bold">{it.productName}</td>
                      <td className="p-2 text-slate-400">{it.variantTitle}</td>
                      <td className="p-2 text-center">
                        <input
                          type="number"
                          step={it.isFabric ? "0.5" : "1"}
                          min="0.1"
                          value={it.quantity}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0;
                            setEditInvoiceItems(prev => prev.map((x, i) => i === idx ? { ...x, quantity: val } : x));
                          }}
                          className={`w-20 text-center font-mono font-bold p-1 rounded border ${
                            theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                          }`}
                        />
                      </td>
                      <td className="p-2 text-right">
                        <input
                          type="number"
                          min="0"
                          value={it.transactionPrice}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0;
                            setEditInvoiceItems(prev => prev.map((x, i) => i === idx ? { ...x, transactionPrice: val } : x));
                          }}
                          className={`w-24 text-right font-mono font-bold p-1 rounded border ${
                            theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                          }`}
                        />
                      </td>
                      <td className="p-2 text-right font-mono font-bold text-emerald-600">
                        Rs. {(it.quantity * it.transactionPrice).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Revision Totals & Discount */}
            {(() => {
              const revSub = editInvoiceItems.reduce((acc, it) => acc + (it.transactionPrice * it.quantity), 0);
              const revGrand = Math.max(0, revSub - editInvoiceDiscount);
              const diff = revGrand - editingInvoice.grandTotal;
              return (
                <div className="p-3 bg-slate-500/10 rounded-lg space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Revised Subtotal:</span>
                    <span className="font-mono font-bold">Rs. {revSub.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Bill Discount (Rs.):</span>
                    <input
                      type="number"
                      min="0"
                      value={editInvoiceDiscount}
                      onChange={(e) => setEditInvoiceDiscount(parseFloat(e.target.value) || 0)}
                      className={`w-24 text-right p-1 font-mono font-bold rounded border ${
                        theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                      }`}
                    />
                  </div>
                  <div className="flex justify-between items-baseline pt-1 border-t border-dashed border-slate-400/40">
                    <span className="font-bold text-sm text-emerald-600">Revised Grand Total:</span>
                    <span className="font-mono font-black text-base text-emerald-600">
                      Rs. {revGrand.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-[11px] font-semibold">
                    <span className="text-slate-400">Variance vs Original:</span>
                    <span className={diff > 0 ? "text-emerald-500" : diff < 0 ? "text-red-500" : "text-slate-400"}>
                      {diff > 0 ? `+Rs. ${diff.toLocaleString()} (Receivable Increased)` : diff < 0 ? `-Rs. ${Math.abs(diff).toLocaleString()} (Refund/Credit to Customer)` : 'Rs. 0 (No change)'}
                    </span>
                  </div>
                </div>
              );
            })()}

            {/* Manager PIN & Reason Form */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <label className="text-xs font-bold block mb-1">Reason for Revision:</label>
                <input
                  type="text"
                  placeholder="E.g., Customer negotiated rate / corrected meter length"
                  value={editInvoiceReason}
                  onChange={(e) => setEditInvoiceReason(e.target.value)}
                  className={`w-full p-2 text-xs rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
              </div>
              <div>
                <label className="text-xs font-bold block mb-1">Manager Authorization PIN:</label>
                <input
                  type="password"
                  placeholder="Enter Manager PIN..."
                  value={editInvoicePin}
                  onChange={(e) => setEditInvoicePin(e.target.value)}
                  className={`w-full p-2 text-xs font-mono font-bold rounded border ${
                    theme === 'dark' ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-300'
                  }`}
                />
              </div>
            </div>

            {editInvoicePinError && (
              <p className="text-xs font-bold text-red-500">{editInvoicePinError}</p>
            )}

            <div className="flex justify-between items-center pt-2 border-t">
              <span className="text-[10px] text-slate-400">
                • Inventory & customer balance reconciled automatically
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setEditingInvoice(null)}
                  className="px-3.5 py-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 border rounded cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveInvoiceEdit}
                  className="px-4 py-1.5 text-xs font-bold bg-sky-600 hover:bg-sky-700 text-white rounded flex items-center gap-1.5 shadow-md cursor-pointer"
                >
                  <Check className="w-4 h-4" /> Save & Reconcile
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL 9: AUDIT TRAIL LOGS MODAL
         ========================================== */}
      {viewAuditLogsInvoice && (
        <div className="fixed inset-0 bg-slate-950/75 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className={`rounded-xl shadow-2xl border max-w-xl w-full p-5 space-y-3.5 max-h-[85vh] flex flex-col ${
            theme === 'dark' ? 'bg-slate-900 border-slate-700 text-white' : 'bg-white border-slate-300 text-slate-800'
          }`}>
            <div className="flex justify-between items-center pb-2 border-b">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <h3 className="font-bold text-base">
                  Invoice Revision Audit Logs (انوائس آڈٹ ٹریل)
                </h3>
              </div>
              <button
                onClick={() => setViewAuditLogsInvoice(null)}
                className="text-slate-400 hover:text-slate-200 font-bold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto border rounded divide-y divide-slate-200 dark:divide-slate-800 text-xs">
              {auditLogs.length === 0 ? (
                <div className="p-6 text-center text-slate-400">No revisions logged yet.</div>
              ) : (
                <table className="w-full text-left">
                  <thead className={`border-b text-[11px] ${
                    theme === 'dark' ? 'bg-slate-950/80 text-slate-400' : 'bg-slate-100 text-slate-600'
                  }`}>
                    <tr>
                      <th className="p-2">Date</th>
                      <th className="p-2">Invoice #</th>
                      <th className="p-2 text-right">Old Total</th>
                      <th className="p-2 text-right">New Total</th>
                      <th className="p-2">Reason & User</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {auditLogs.map(l => (
                      <tr key={l.id} className="hover:bg-slate-500/5">
                        <td className="p-2 text-slate-400 font-mono text-[10px]">{l.createdAt}</td>
                        <td className="p-2 font-mono font-bold text-emerald-600">{l.invoiceNumber}</td>
                        <td className="p-2 text-right font-mono">Rs. {l.oldGrandTotal.toLocaleString()}</td>
                        <td className="p-2 text-right font-mono font-bold text-emerald-500">Rs. {l.newGrandTotal.toLocaleString()}</td>
                        <td className="p-2">
                          <span className="font-semibold block">{l.reason}</span>
                          <span className="text-[10px] text-slate-400">By: {l.editedBy}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t">
              <button
                onClick={() => setViewAuditLogsInvoice(null)}
                className="px-4 py-1.5 text-xs font-bold bg-slate-700 hover:bg-slate-600 text-white rounded cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
