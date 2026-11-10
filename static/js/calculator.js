function initCalculator() {
  const calcForm = document.getElementById('calc-form');
  if (!calcForm) return;

  const typeInput = document.getElementById('calc-type');
  const sizeInput = document.getElementById('calc-size');
  const currentRentInput = document.getElementById('calc-current-rent');
  const tierInputs = document.querySelectorAll('input[name="calc-tier"]');

  const projectedRentEl = document.getElementById('res-projected-rent');
  const rentGrowthEl = document.getElementById('res-rent-growth');
  const annualNetEl = document.getElementById('res-annual-net');
  const taxSavingsEl = document.getElementById('res-tax-savings');
  const capexEl = document.getElementById('res-capex');
  const paybackEl = document.getElementById('res-payback');

  function calculate() {
    const size = parseFloat(sizeInput.value) || 30;
    const currentRent = parseFloat(currentRentInput.value) || 16000;
    let selectedTier = 'medium';
    tierInputs.forEach(r => {
      if (r.checked) selectedTier = r.value;
    });

    // Multipliers based on extensive Tainan property market data
    let growthRate = 1.6; // default 60% increase
    let capexPerPing = 25000; // NTD per ping

    if (selectedTier === 'light') {
      growthRate = 1.35; // +35%
      capexPerPing = 12000;
    } else if (selectedTier === 'medium') {
      growthRate = 1.75; // +75%
      capexPerPing = 28000;
    } else if (selectedTier === 'luxury') {
      growthRate = 2.30; // +130%
      capexPerPing = 48000;
    }

    const projectedMonthlyRent = Math.round((currentRent * growthRate) / 500) * 500;
    const monthlyNetIncrease = projectedMonthlyRent - currentRent;
    const annualNetIncrease = monthlyNetIncrease * 12;
    const totalCapex = Math.round(size * capexPerPing);
    const paybackYears = annualNetIncrease > 0 ? (totalCapex / annualNetIncrease).toFixed(1) : 0;

    // Statutory Tax Exemption:
    // Income tax: 15,000/mo * 12 = 180,000 exempt from taxable income
    // Plus 60% deduction on remainder vs 43%
    // House tax drops from 3.6%~4.8% to 1.2%
    // Estimated tax savings approx NT$ 24,000 ~ 58,000 / year
    const estimatedTaxSavings = Math.round(Math.min(projectedMonthlyRent, 15000) * 12 * 0.12 + 8000);

    if (projectedRentEl) projectedRentEl.textContent = `NT$ ${projectedMonthlyRent.toLocaleString()}`;
    if (rentGrowthEl) rentGrowthEl.textContent = `+${Math.round((growthRate - 1) * 100)}%`;
    if (annualNetEl) annualNetEl.textContent = `+NT$ ${annualNetIncrease.toLocaleString()}`;
    if (taxSavingsEl) taxSavingsEl.textContent = `約 NT$ ${estimatedTaxSavings.toLocaleString()} / 年`;
    if (capexEl) capexEl.textContent = `NT$ ${totalCapex.toLocaleString()}`;
    if (paybackEl) paybackEl.textContent = `約 ${paybackYears} 年回本`;
  }

  // Attach event listeners
  [typeInput, sizeInput, currentRentInput].forEach(el => {
    if (el) el.addEventListener('input', calculate);
  });
  tierInputs.forEach(el => {
    el.addEventListener('change', calculate);
  });

  // Add to RFQ Button
  const btnAddCalcToRfq = document.getElementById('btn-add-calc-to-rfq');
  if (btnAddCalcToRfq) {
    btnAddCalcToRfq.addEventListener('click', (e) => {
      e.preventDefault();
      const typeText = typeInput.options[typeInput.selectedIndex].text;
      const sizeVal = sizeInput.value;
      let tierLabel = '全室模組化管線翻新 (高性價比)';
      tierInputs.forEach(r => {
        if (r.checked) {
          tierLabel = r.parentElement.textContent.trim();
        }
      });
      const projectedRent = projectedRentEl.textContent;

      RFQCart.addItem({
        code: 'spatial_renovation_calc',
        title: `空間活化試算委託 (${typeText} ${sizeVal}坪)`,
        specs: {
          '物業型態': typeText,
          '坪數': `${sizeVal} 坪`,
          '改造等級': tierLabel,
          '試算預期月租': projectedRent
        },
        price: '試算方案專人到府勘查'
      });
      RFQCart.openDrawer();
    });
  }

  // Run initial calculation
  calculate();
}

document.addEventListener('DOMContentLoaded', initCalculator);
window.addEventListener('contentLoaded', initCalculator);

