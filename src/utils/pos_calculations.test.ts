import test from 'node:test';
import assert from 'node:assert/strict';
import {
  calculateCartItem,
  renderWhatsAppMessage,
  formatPakistaniWhatsAppNumber,
  prepareCsvDownloadContent
} from './pos_calculations';

test('calculateCartItem: normal price without bargain', () => {
  const result = calculateCartItem({
    basePrice: 1000,
    transactionPrice: 1000,
    quantity: 3
  });
  assert.equal(result.total, 3000);
  assert.equal(result.isBargain, false);
  assert.equal(result.discountPercent, 0);
  assert.equal(result.requiresPin, false);
});

test('calculateCartItem: within 15% discount threshold does not require PIN', () => {
  // Base 1000, transaction 900 (10% discount)
  const result = calculateCartItem({
    basePrice: 1000,
    transactionPrice: 900,
    quantity: 2.5
  });
  assert.equal(result.total, 2250);
  assert.equal(result.isBargain, true);
  assert.equal(result.discountPercent, 10);
  assert.equal(result.requiresPin, false);
});

test('calculateCartItem: exceeding 15% discount requires Manager PIN', () => {
  // Base 1000, transaction 800 (20% discount)
  const result = calculateCartItem({
    basePrice: 1000,
    transactionPrice: 800,
    quantity: 1
  });
  assert.equal(result.total, 800);
  assert.equal(result.isBargain, true);
  assert.equal(result.discountPercent, 20);
  assert.equal(result.requiresPin, true);
});

test('renderWhatsAppMessage: substitutes placeholders correctly', () => {
  const template = 'Dear {customer_name}, thank you for visiting {shop_name}! Your bill is Rs. {amount}.';
  const rendered = renderWhatsAppMessage(template, {
    customer_name: 'Usman Ghani',
    shop_name: 'Arooj Cloth and Bedsheet Parda',
    amount: 4500
  });
  assert.equal(rendered, 'Dear Usman Ghani, thank you for visiting Arooj Cloth and Bedsheet Parda! Your bill is Rs. 4500.');
});

test('formatPakistaniWhatsAppNumber: formats local 03xx into 923xx', () => {
  assert.equal(formatPakistaniWhatsAppNumber('0300-1234567'), '923001234567');
  assert.equal(formatPakistaniWhatsAppNumber('+92 321 9876543'), '923219876543');
  assert.equal(formatPakistaniWhatsAppNumber('3335557788'), '923335557788');
});

test('prepareCsvDownloadContent: prepends UTF-8 BOM if missing', () => {
  const rawCsv = 'Product,Price\nBedsheet,2500';
  const bomCsv = prepareCsvDownloadContent(rawCsv);
  assert.ok(bomCsv.startsWith('\uFEFF'));
  assert.equal(bomCsv.slice(1), rawCsv);

  // If already present, do not duplicate
  const reBom = prepareCsvDownloadContent(bomCsv);
  assert.equal(reBom, bomCsv);
});
