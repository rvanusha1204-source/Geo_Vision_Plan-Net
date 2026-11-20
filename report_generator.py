"""
report_generator.py — PDF Report Generator (BI-Dashboard Style)
Green Cover Detection & Deforestation Analysis System — Stage 7 of the pipeline

Builds a visually rich, dashboard-style PDF report from the pipeline's outputs:
  - violation_summary.csv (required)
  - violation_trend.csv (optional — enables multi-year trend section)
  - violation_zones.geojson (optional — enables violation count breakdown)
  - ndvi_change_map.tif (optional — embeds the NDVI heatmap as an image)

Usage:
    from report_generator import generate_pdf_report
    generate_pdf_report(
        summary_csv_path='violation_summary.csv',
        trend_csv_path='violation_trend.csv',
        geojson_path='violation_zones.geojson',
        tif_path='ndvi_change_map.tif',
        output_path='Green_Cover_Report.pdf',
        region_name='Coimbatore District, Tamil Nadu'
    )
"""

import os
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image as RLImage
)

# ---------------------------------------------------------------------------
# Color theme — used consistently across every chart and card
# ---------------------------------------------------------------------------
COLOR_DARK_GREEN = '#1b4332'
COLOR_MID_GREEN = '#2d6a4f'
COLOR_LIGHT_GREEN = '#40916c'
COLOR_RED = '#c0392b'
COLOR_DARK_RED = '#7f0000'
COLOR_ORANGE = '#e67e22'
COLOR_PURPLE = '#6c3483'
COLOR_GOLD = '#f4a300'
COLOR_BG = '#f1faee'
COLOR_GREY_TEXT = colors.HexColor('#555555')

PAGE_W, PAGE_H = A4


# ---------------------------------------------------------------------------
# Header / footer bars drawn on every page
# ---------------------------------------------------------------------------
def _header_footer(canvas, doc, region_name):
    canvas.saveState()

    # Top bar
    canvas.setFillColor(colors.HexColor(COLOR_DARK_GREEN))
    canvas.rect(0, PAGE_H - 1.4 * cm, PAGE_W, 1.4 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawString(1.5 * cm, PAGE_H - 0.95 * cm, "🌍 GREEN COVER MONITORING REPORT")
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(PAGE_W - 1.5 * cm, PAGE_H - 0.95 * cm, region_name)

    # Bottom bar
    canvas.setFillColor(colors.HexColor(COLOR_DARK_GREEN))
    canvas.rect(0, 0, PAGE_W, 0.9 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(1.5 * cm, 0.35 * cm, f"Generated {datetime.now().strftime('%d %b %Y')}")
    canvas.drawCentredString(PAGE_W / 2, 0.35 * cm, "AI-Powered Green Cover Detection & Deforestation Analysis System")
    canvas.drawRightString(PAGE_W - 1.5 * cm, 0.35 * cm, f"Page {doc.page}")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# KPI cards — Power BI-style colored metric tiles
# ---------------------------------------------------------------------------
def _kpi_card(label, value, color_hex, unit='ha'):
    label_style = ParagraphStyle('kpi_label', fontSize=7.5, textColor=colors.white,
                                  alignment=1, fontName='Helvetica-Bold', leading=9)
    value_style = ParagraphStyle('kpi_value', fontSize=17, textColor=colors.white,
                                  alignment=1, fontName='Helvetica-Bold', leading=20)
    unit_style = ParagraphStyle('kpi_unit', fontSize=7, textColor=colors.white,
                                 alignment=1, fontName='Helvetica')

    cell = [
        [Paragraph(label.upper(), label_style)],
        [Paragraph(f"{value:,.1f}", value_style)],
        [Paragraph(unit, unit_style)],
    ]
    t = Table(cell, colWidths=[3.3 * cm], rowHeights=[0.85 * cm, 0.75 * cm, 0.4 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(color_hex)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    return t


def _kpi_row(cards, gap=0.15 * cm):
    row = Table([cards], colWidths=[3.3 * cm] * len(cards))
    row.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), gap),
        ('RIGHTPADDING', (0, 0), (-1, -1), gap),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return row


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------
def _make_bar_chart(summary_row, out_path):
    categories = ['Veg Loss', 'Veg Gain', 'Protected\nEncroachment', 'Buffer\nViolation', 'Severe\nLoss']
    values = [
        summary_row.get('total_veg_loss_ha', 0),
        summary_row.get('total_veg_gain_ha', 0),
        summary_row.get('protected_area_encroachment_ha', 0),
        summary_row.get('buffer_zone_violation_ha', 0),
        summary_row.get('severe_loss_ha', 0),
    ]
    bar_colors = [COLOR_RED, COLOR_LIGHT_GREEN, COLOR_PURPLE, COLOR_ORANGE, COLOR_DARK_RED]

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('white')
    bars = ax.bar(categories, values, color=bar_colors, width=0.6)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f'{val:,.1f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax.set_ylabel('Area (hectares)', fontsize=9)
    ax.set_title('Vegetation Change Summary', fontsize=12, fontweight='bold', color=COLOR_DARK_GREEN)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.25)
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _make_donut_chart(summary_row, out_path):
    labels = ['Protected\nEncroachment', 'Buffer\nViolation', 'Severe Loss\n(other areas)']
    values = [
        max(summary_row.get('protected_area_encroachment_ha', 0), 0.001),
        max(summary_row.get('buffer_zone_violation_ha', 0), 0.001),
        max(summary_row.get('severe_loss_ha', 0), 0.001),
    ]
    donut_colors = [COLOR_DARK_RED, COLOR_ORANGE, COLOR_PURPLE]

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    fig.patch.set_facecolor('white')
    wedges, _texts, autotexts = ax.pie(
        values, colors=donut_colors, autopct='%1.0f%%', pctdistance=0.8,
        startangle=90, wedgeprops=dict(width=0.42, edgecolor='white', linewidth=2),
        textprops=dict(color='white', fontsize=10, fontweight='bold')
    )
    total = sum(values)
    ax.text(0, 0, f'{total:,.0f}\nha', ha='center', va='center', fontsize=15,
            fontweight='bold', color=COLOR_DARK_GREEN)
    ax.legend(wedges, labels, loc='center', bbox_to_anchor=(0.5, -0.15), ncol=1,
              fontsize=8, frameon=False)
    ax.set_title('Violation Breakdown by Category', fontsize=12, fontweight='bold', color=COLOR_DARK_GREEN)
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _make_risk_gauge(summary_row, out_path):
    """Half-donut gauge showing what fraction of vegetation loss was flagged as a violation."""
    loss = summary_row.get('total_veg_loss_ha', 0)
    flagged = summary_row.get('total_flagged_violation_ha', 0)
    pct = min(100, (flagged / loss * 100) if loss > 0 else 0)

    fig, ax = plt.subplots(figsize=(6, 3.6), subplot_kw={'aspect': 'equal'})
    fig.patch.set_facecolor('white')

    # Background bands: green (low risk) -> gold (medium) -> red (high)
    band_colors = ['#2d6a4f', '#f4a300', '#c0392b']
    band_ranges = [(0, 40), (40, 70), (70, 100)]
    for (start, end), c in zip(band_ranges, band_colors):
        theta1 = 180 - (start / 100 * 180)
        theta2 = 180 - (end / 100 * 180)
        wedge = matplotlib.patches.Wedge((0, 0), 1, theta2, theta1, width=0.3, facecolor=c, edgecolor='white')
        ax.add_patch(wedge)

    # Needle
    needle_angle = np.radians(180 - (pct / 100 * 180))
    ax.plot([0, 0.75 * np.cos(needle_angle)], [0, 0.75 * np.sin(needle_angle)],
            color='black', linewidth=3, solid_capstyle='round')
    ax.add_patch(plt.Circle((0, 0), 0.05, color='black', zorder=5))

    ax.text(0, -0.35, f'{pct:.1f}%', ha='center', va='center', fontsize=22,
            fontweight='bold', color=COLOR_DARK_GREEN)
    ax.text(0, -0.55, 'of vegetation loss flagged as a violation', ha='center', va='center',
            fontsize=8, color='#555555')

    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.6, 1.1)
    ax.axis('off')
    ax.set_title('Violation Risk Index', fontsize=12, fontweight='bold', color=COLOR_DARK_GREEN, pad=0)
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _make_trend_chart(trend_df, out_path):
    fig, ax = plt.subplots(figsize=(7.2, 4))
    fig.patch.set_facecolor('white')

    x = trend_df['period_label']
    ax.fill_between(range(len(x)), trend_df['total_veg_loss_ha'], color=COLOR_RED, alpha=0.15)
    ax.plot(x, trend_df['total_veg_loss_ha'], marker='o', label='Vegetation Loss (ha)',
            color=COLOR_RED, linewidth=2.2)
    ax.plot(x, trend_df['total_veg_gain_ha'], marker='o', label='Vegetation Gain (ha)',
            color=COLOR_LIGHT_GREEN, linewidth=2.2)
    ax.plot(x, trend_df['total_flagged_violation_ha'], marker='s', label='Flagged Violations (ha)',
            color=COLOR_DARK_RED, linewidth=2, linestyle='--')

    ax.set_xlabel('Period', fontsize=9)
    ax.set_ylabel('Area (hectares)', fontsize=9)
    ax.set_title('Multi-Year Vegetation Trend', fontsize=12, fontweight='bold', color=COLOR_DARK_GREEN)
    ax.legend(fontsize=8, frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.25)
    plt.xticks(rotation=25, ha='right')
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _make_ndvi_heatmap_image(tif_path, out_path):
    import rasterio
    with rasterio.open(tif_path) as src:
        data = src.read(1)
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    fig.patch.set_facecolor('white')
    im = ax.imshow(data, cmap='RdYlGn', vmin=-0.5, vmax=0.5)
    cbar = plt.colorbar(im, ax=ax, label='NDVI Change (red = loss, green = gain)', shrink=0.85)
    ax.set_title('NDVI Change Map', fontsize=12, fontweight='bold', color=COLOR_DARK_GREEN)
    ax.axis('off')
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _violation_count_from_geojson(geojson_path):
    try:
        import geopandas as gpd
        gdf = gpd.read_file(geojson_path)
        return len(gdf)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main report builder
# ---------------------------------------------------------------------------
def generate_pdf_report(
    summary_csv_path,
    output_path='Green_Cover_Report.pdf',
    trend_csv_path=None,
    geojson_path=None,
    tif_path=None,
    region_name='Study Area',
):
    if not os.path.exists(summary_csv_path):
        raise FileNotFoundError(f"Required file not found: {summary_csv_path}")

    summary_df = pd.read_csv(summary_csv_path)
    summary_row = summary_df.iloc[0]

    trend_df = None
    if trend_csv_path and os.path.exists(trend_csv_path):
        trend_df = pd.read_csv(trend_csv_path)

    tmp_dir = os.path.dirname(output_path) or '.'
    bar_chart_path = os.path.join(tmp_dir, '_tmp_bar_chart.png')
    donut_chart_path = os.path.join(tmp_dir, '_tmp_donut_chart.png')
    gauge_chart_path = os.path.join(tmp_dir, '_tmp_gauge_chart.png')
    trend_chart_path = os.path.join(tmp_dir, '_tmp_trend_chart.png')
    ndvi_chart_path = os.path.join(tmp_dir, '_tmp_ndvi_chart.png')

    _make_bar_chart(summary_row, bar_chart_path)
    _make_donut_chart(summary_row, donut_chart_path)
    _make_risk_gauge(summary_row, gauge_chart_path)

    has_trend_chart = trend_df is not None and len(trend_df) > 0
    if has_trend_chart:
        _make_trend_chart(trend_df, trend_chart_path)

    has_ndvi_chart = False
    if tif_path and os.path.exists(tif_path):
        try:
            _make_ndvi_heatmap_image(tif_path, ndvi_chart_path)
            has_ndvi_chart = True
        except Exception:
            has_ndvi_chart = False

    violation_count = None
    if geojson_path and os.path.exists(geojson_path):
        violation_count = _violation_count_from_geojson(geojson_path)

    # --- Document setup ---
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=2.1 * cm, bottomMargin=1.6 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor(COLOR_DARK_GREEN),
                         spaceAfter=8, spaceBefore=4)
    h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor(COLOR_MID_GREEN),
                         spaceAfter=6, spaceBefore=10)
    body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9.5, leading=14, textColor=colors.HexColor('#333333'))
    caption = ParagraphStyle('caption', parent=styles['Normal'], fontSize=8, textColor=COLOR_GREY_TEXT)
    disclaimer = ParagraphStyle('disclaimer', parent=body, fontSize=7.5, textColor=COLOR_GREY_TEXT, leading=11)

    story = []

    # --- COVER / KPI SECTION ---
    story.append(Paragraph("Green Cover Detection &amp; Deforestation Analysis", h1))
    story.append(Paragraph(
        f"<b>Region:</b> {region_name} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Study Period:</b> {summary_row.get('study_period', 'N/A')} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Protected Areas in AOI:</b> {summary_row.get('protected_areas_in_aoi', 'N/A')}",
        body
    ))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Key Metrics", h2))
    kpi_cards = [
        _kpi_card("Veg. Loss", summary_row.get('total_veg_loss_ha', 0), COLOR_RED),
        _kpi_card("Veg. Gain", summary_row.get('total_veg_gain_ha', 0), COLOR_LIGHT_GREEN),
        _kpi_card("Protected\nEncroachment", summary_row.get('protected_area_encroachment_ha', 0), COLOR_PURPLE),
        _kpi_card("Buffer\nViolation", summary_row.get('buffer_zone_violation_ha', 0), COLOR_ORANGE),
        _kpi_card("Severe Loss", summary_row.get('severe_loss_ha', 0), COLOR_DARK_RED),
        _kpi_card("Total\nViolations", summary_row.get('total_flagged_violation_ha', 0), COLOR_DARK_GREEN),
    ]
    story.append(_kpi_row(kpi_cards))
    story.append(Spacer(1, 16))

    veg_loss = summary_row.get('total_veg_loss_ha', 0)
    veg_gain = summary_row.get('total_veg_gain_ha', 0)
    net_change = veg_gain - veg_loss
    trend_word = "a net loss" if net_change < 0 else "a net gain"
    story.append(Paragraph("Executive Summary", h2))
    story.append(Paragraph(
        f"Over the study period, the analyzed region experienced <b>{veg_loss:,.1f} hectares</b> of "
        f"vegetation loss and <b>{veg_gain:,.1f} hectares</b> of vegetation gain, resulting in {trend_word} "
        f"of approximately <b>{abs(net_change):,.1f} hectares</b>. "
        + (f"A total of <b>{violation_count:,}</b> individual violation polygons were identified. "
           if violation_count is not None else "")
        + f"<b>{summary_row.get('total_flagged_violation_ha', 0):,.1f} hectares</b> was flagged across all "
        f"violation categories, based on NDVI change detection cross-referenced against protected area "
        f"boundaries and buffer zones.",
        body
    ))
    story.append(Spacer(1, 14))

    # Side-by-side donut + gauge
    combo_table = Table(
        [[RLImage(donut_chart_path, width=8 * cm, height=8 * cm),
          RLImage(gauge_chart_path, width=8 * cm, height=4.8 * cm)]],
        colWidths=[8.5 * cm, 8.5 * cm]
    )
    combo_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    story.append(combo_table)

    # --- PAGE 2: Statistics + bar chart ---
    story.append(PageBreak())
    story.append(Paragraph("Vegetation &amp; Violation Statistics", h1))

    table_data = [
        ['Metric', 'Value (hectares)'],
        ['Vegetation Loss', f"{summary_row.get('total_veg_loss_ha', 0):,.1f}"],
        ['Vegetation Gain', f"{summary_row.get('total_veg_gain_ha', 0):,.1f}"],
        ['Protected Area Encroachment', f"{summary_row.get('protected_area_encroachment_ha', 0):,.1f}"],
        ['Buffer Zone Violation', f"{summary_row.get('buffer_zone_violation_ha', 0):,.1f}"],
        ['Severe Loss (any location)', f"{summary_row.get('severe_loss_ha', 0):,.1f}"],
        ['Total Flagged Violations', f"{summary_row.get('total_flagged_violation_ha', 0):,.1f}"],
    ]
    stats_table = Table(table_data, colWidths=[9.5 * cm, 6 * cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_DARK_GREEN)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLOR_BG)]),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 14))
    story.append(RLImage(bar_chart_path, width=16 * cm, height=9 * cm))

    # --- PAGE 3: NDVI heatmap ---
    if has_ndvi_chart:
        story.append(PageBreak())
        story.append(Paragraph("NDVI Change Map", h1))
        story.append(Paragraph(
            "Pixel-level NDVI change across the study area. Red indicates vegetation loss; "
            "green indicates vegetation gain.", body
        ))
        story.append(Spacer(1, 10))
        story.append(RLImage(ndvi_chart_path, width=16 * cm, height=12.5 * cm))

    # --- PAGE 4: Multi-year trend ---
    if has_trend_chart:
        story.append(PageBreak())
        story.append(Paragraph("Multi-Year Trend Analysis", h1))
        story.append(Paragraph(
            f"Tracking vegetation loss, gain, and flagged violations across {len(trend_df)} consecutive "
            f"periods, from {trend_df['year_start'].min()} to {trend_df['year_end'].max()}.", body
        ))
        story.append(Spacer(1, 10))
        story.append(RLImage(trend_chart_path, width=16 * cm, height=9 * cm))
        story.append(Spacer(1, 12))

        trend_table_data = [['Period', 'Loss (ha)', 'Gain (ha)', 'Violations (ha)']]
        for _, r in trend_df.iterrows():
            trend_table_data.append([
                r['period_label'], f"{r['total_veg_loss_ha']:,.1f}",
                f"{r['total_veg_gain_ha']:,.1f}", f"{r['total_flagged_violation_ha']:,.1f}",
            ])
        trend_table = Table(trend_table_data, colWidths=[4 * cm, 3.8 * cm, 3.8 * cm, 4 * cm])
        trend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_DARK_GREEN)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLOR_BG)]),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        story.append(trend_table)

    # --- FINAL PAGE: Impact + Recommendations ---
    story.append(PageBreak())
    story.append(Paragraph("Environmental Impact Analysis", h1))

    impact_text = (
        f"The recorded vegetation loss of {veg_loss:,.1f} hectares represents a measurable reduction in "
        f"green cover within the study period. "
    )
    if summary_row.get('protected_area_encroachment_ha', 0) > 0:
        impact_text += (
            f"Of particular concern, {summary_row.get('protected_area_encroachment_ha', 0):,.1f} hectares of "
            f"loss was detected within officially recognized protected area boundaries, indicating potential "
            f"encroachment requiring further ground-verification and regulatory attention. "
        )
    if summary_row.get('severe_loss_ha', 0) > 0:
        impact_text += (
            f"An additional {summary_row.get('severe_loss_ha', 0):,.1f} hectares showed severe vegetation loss, "
            f"consistent with large-scale clearing activity."
        )
    story.append(Paragraph(impact_text, body))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Recommendations", h2))
    recommendations = [
        "Ground-verify flagged protected-area encroachment zones with field survey teams before regulatory action.",
        "Prioritize monitoring of buffer-zone violations, as these often precede direct protected-area encroachment.",
        "Cross-reference severe-loss zones against known land-use permits to distinguish authorized clearing from violations.",
        "Repeat this analysis at 1-2 year intervals to track whether flagged areas show continued degradation or recovery.",
    ]
    rec_data = [[Paragraph(f"• {r}", body)] for r in recommendations]
    rec_table = Table(rec_data, colWidths=[16 * cm])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLOR_BG)),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.white),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        "This report was generated by an AI-powered analysis pipeline using satellite imagery (Sentinel-2), "
        "NDVI-based change detection, and rule-based violation flagging. Findings should be treated as a "
        "screening tool to prioritize field investigation, not as definitive legal evidence.",
        disclaimer
    ))

    # --- Build with header/footer on every page ---
    def _on_page(canvas, doc_):
        _header_footer(canvas, doc_, region_name)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)

    for p in [bar_chart_path, donut_chart_path, gauge_chart_path, trend_chart_path, ndvi_chart_path]:
        if os.path.exists(p):
            os.remove(p)

    return output_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Generate the Green Cover PDF report.")
    parser.add_argument('--summary', default='violation_summary.csv')
    parser.add_argument('--trend', default='violation_trend.csv')
    parser.add_argument('--geojson', default='violation_zones.geojson')
    parser.add_argument('--tif', default='ndvi_change_map.tif')
    parser.add_argument('--output', default='Green_Cover_Report.pdf')
    parser.add_argument('--region', default='Study Area')
    args = parser.parse_args()

    out = generate_pdf_report(
        summary_csv_path=args.summary,
        trend_csv_path=args.trend if os.path.exists(args.trend) else None,
        geojson_path=args.geojson if os.path.exists(args.geojson) else None,
        tif_path=args.tif if os.path.exists(args.tif) else None,
        output_path=args.output,
        region_name=args.region,
    )
    print(f"Report generated: {out}")
