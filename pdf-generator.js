/**
 * Geo Vision Plan-Net - Comprehensive PDF Report Generator
 * Includes Key Metrics, Executive Summary, Multi-Year Trends, and Recommended Conservation Actions.
 */

function generateDistrictPDFReport(district) {
  if (!district) return;

  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const greenDark = '#064e3b';
  const greenMid = '#10b981';
  const textDark = '#1f2937';
  const textLight = '#4b5563';
  const redAlert = '#ef4444';

  const summary = district.summary || {};
  const recommendations = district.recommendations && district.recommendations.length > 0 ? district.recommendations : [
    "Deploy drone surveillance teams along eco-sensitive corridors.",
    "Issue immediate stop-work notices for illegal hill cutting in sub-divisions.",
    "Initiate native afforestation along degraded riparian buffers."
  ];

  // 1. Header Banner
  doc.setFillColor(6, 78, 59); // Deep Emerald
  doc.rect(0, 0, 210, 35, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.text('GEO VISION PLAN-NET REPORT', 14, 18);

  doc.setFontSize(9.5);
  doc.setFont('helvetica', 'normal');
  doc.text('Smart Green Cover Detection & AI Deforestation Analysis System', 14, 26);
  doc.text(`Generated: ${new Date().toLocaleDateString()}`, 152, 26);

  // 2. Region Title & Risk Badge
  doc.setTextColor(textDark);
  doc.setFontSize(15);
  doc.setFont('helvetica', 'bold');
  doc.text(`${district.displayName || 'District'} (${district.state || 'India'})`, 14, 46);

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(textLight);
  doc.text(`Study Period: ${summary.studyPeriod || '2017 - 2025'}`, 14, 52);

  // Risk Score Badge
  const risk = summary.riskScore || 85;
  doc.setFillColor(risk > 80 ? 239 : 245, risk > 80 ? 68 : 158, risk > 80 ? 68 : 11);
  doc.roundedRect(142, 40, 54, 14, 2, 2, 'F');

  doc.setTextColor(255, 255, 255);
  doc.setFontSize(9.5);
  doc.setFont('helvetica', 'bold');
  doc.text(`RISK SCORE: ${risk}/100`, 147, 49);

  // 3. Key Metrics Table Summary Box
  doc.setFillColor(243, 244, 246);
  doc.rect(14, 58, 182, 42, 'F');

  doc.setTextColor(greenDark);
  doc.setFontSize(10.5);
  doc.setFont('helvetica', 'bold');
  doc.text('KEY METRICS SUMMARY (Hectares)', 18, 66);

  const kpis = [
    { label: 'Vegetation Loss', val: `${Number(summary.totalVegLossHa || 0).toLocaleString()} ha` },
    { label: 'Vegetation Gain', val: `${Number(summary.totalVegGainHa || 0).toLocaleString()} ha` },
    { label: 'Protected Area Encroachment', val: `${Number(summary.protectedAreaEncroachmentHa || 0).toLocaleString()} ha` },
    { label: 'Buffer Zone Violation', val: `${Number(summary.bufferZoneViolationHa || 0).toLocaleString()} ha` },
    { label: 'Severe Loss', val: `${Number(summary.severeLossHa || 0).toLocaleString()} ha` },
    { label: 'Total Flagged Violations', val: `${Number(summary.totalFlaggedViolationHa || 0).toLocaleString()} ha` }
  ];

  let startY = 74;
  kpis.forEach((kpi, idx) => {
    const col = idx % 2;
    const row = Math.floor(idx / 2);
    const x = 18 + col * 90;
    const y = startY + row * 7.5;

    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(textLight);
    doc.text(`• ${kpi.label}:`, x, y);

    doc.setFont('helvetica', 'bold');
    doc.setTextColor(textDark);
    doc.text(kpi.val, x + 50, y);
  });

  // 4. Executive Analytical Summary
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(greenDark);
  doc.text('EXECUTIVE ANALYTICAL SUMMARY', 14, 110);

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(textDark);

  const execSummary = district.executiveSummary || (
    `Over the study period (${summary.studyPeriod || '2017 - 2025'}), ${district.displayName} experienced `
    + `${Number(summary.totalVegLossHa || 0).toLocaleString()} hectares of vegetation loss and `
    + `${Number(summary.totalVegGainHa || 0).toLocaleString()} hectares of vegetation gain. `
    + `A total of ${Number(summary.totalFlaggedViolationHa || 0).toLocaleString()} hectares were flagged across violations.`
  );

  const splitSummary = doc.splitTextToSize(execSummary, 182);
  doc.text(splitSummary, 14, 117);

  let currentCursorY = 117 + (splitSummary.length * 5) + 6;

  // 5. Multi-Year Trend Table
  if (district.trend && district.trend.length > 0) {
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(greenDark);
    doc.text('MULTI-YEAR TEMPORAL TREND HISTORY', 14, currentCursorY);

    currentCursorY += 5;

    // Table Header
    doc.setFillColor(6, 78, 59);
    doc.rect(14, currentCursorY, 182, 7, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(8.5);
    doc.text('Period', 18, currentCursorY + 5);
    doc.text('Loss (ha)', 70, currentCursorY + 5);
    doc.text('Gain (ha)', 110, currentCursorY + 5);
    doc.text('Flagged Violations (ha)', 150, currentCursorY + 5);

    currentCursorY += 7;

    district.trend.forEach((t, i) => {
      if (i % 2 === 0) {
        doc.setFillColor(249, 250, 251);
        doc.rect(14, currentCursorY, 182, 6, 'F');
      }
      doc.setTextColor(textDark);
      doc.setFont('helvetica', 'normal');
      doc.text(String(t.period), 18, currentCursorY + 4.5);
      doc.text(`${Number(t.lossHa).toLocaleString()} ha`, 70, currentCursorY + 4.5);
      doc.text(`${Number(t.gainHa).toLocaleString()} ha`, 110, currentCursorY + 4.5);
      doc.text(`${Number(t.violationsHa).toLocaleString()} ha`, 150, currentCursorY + 4.5);
      currentCursorY += 6.5;
    });

    currentCursorY += 6;
  }

  // 6. RECOMMENDED CONSERVATION ACTIONS SECTION
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(greenDark);
  doc.text('RECOMMENDED CONSERVATION ACTIONS', 14, currentCursorY);

  currentCursorY += 7;

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(textDark);

  recommendations.forEach((rec) => {
    // Draw bullet point icon box
    doc.setFillColor(16, 185, 129); // Emerald accent dot
    doc.circle(17, currentCursorY - 1.5, 1.2, 'F');

    const splitRec = doc.splitTextToSize(rec, 172);
    doc.text(splitRec, 22, currentCursorY);
    currentCursorY += (splitRec.length * 5) + 3;
  });

  // 7. Footer & Digital Audit Signature Stamp
  doc.setDrawColor(229, 231, 235);
  doc.line(14, 276, 196, 276);

  doc.setFontSize(8);
  doc.setTextColor(textLight);
  doc.text('Geo Vision Plan-Net AI System — Official Environmental Audit Document', 14, 282);
  doc.text('Page 1 of 1', 180, 282);

  // Download PDF file
  const filename = `GeoVision_Report_${district.slug || 'district'}.pdf`;
  doc.save(filename);
}
