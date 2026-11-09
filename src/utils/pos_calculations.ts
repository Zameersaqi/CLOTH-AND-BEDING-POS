/**
 * Arooj POS pure calculation & formatting utilities
 */

export interface CartCalculationInput {
  basePrice: number;
  transactionPrice: number;
  quantity: number;
  customDiscountPercent?: number;
}

export interface CartItemResult {
  total: number;
  isBargain: boolean;
  discountPercent: number;
  requiresPin: boolean;
}

/**
 * Calculates item totals, discount percentages, bargain flags, and manager PIN requirement
 * Default discount threshold is 15%. If discount exceeds 15% from master catalog price, Manager PIN is required.
 */
export function calculateCartItem(input: CartCalculationInput, maxDiscountWithoutPin: number = 15): CartItemResult {
  const { basePrice, transactionPrice, quantity } = input;
  const itemTotal = Math.round(transactionPrice * quantity * 100) / 100;
  
  let discountPercent = 0;
  if (basePrice > 0 && transactionPrice < basePrice) {
    discountPercent = Math.round(((basePrice - transactionPrice) / basePrice) * 100 * 10) / 10;
  }
  
  const isBargain = transactionPrice !== basePrice;
  const requiresPin = discountPercent > maxDiscountWithoutPin;

  return {
    total: itemTotal,
    isBargain,
    discountPercent,
    requiresPin
  };
}

/**
 * Replaces placeholders in WhatsApp offer/invoice message template
 */
export function renderWhatsAppMessage(
  template: string,
  variables: { [key: string]: string | number }
): string {
  let result = template;
  for (const [key, value] of Object.entries(variables)) {
    const placeholder = new RegExp(`\\{${key}\\}`, 'gi');
    result = result.replace(placeholder, String(value));
  }
  return result;
}

/**
 * Formats Pakistani mobile number for WhatsApp international URL (923XXXXXXXXX)
 */
export function formatPakistaniWhatsAppNumber(phone: string): string {
  let cleaned = phone.replace(/\D/g, '');
  if (cleaned.startsWith('0')) {
    cleaned = '92' + cleaned.slice(1);
  } else if (!cleaned.startsWith('92') && cleaned.length === 10) {
    cleaned = '92' + cleaned;
  }
  return cleaned;
}

/**
 * Ensures CSV string has UTF-8 BOM for Microsoft Excel compatibility
 */
export function prepareCsvDownloadContent(csvBody: string): string {
  if (csvBody.startsWith('\uFEFF')) {
    return csvBody;
  }
  return '\uFEFF' + csvBody;
}
