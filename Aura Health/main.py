import sqlite3
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

# PDF Generation imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = FastAPI(title="AuraHealth Automation Platform")
DB_PATH = 'aura_health.db'

# ==========================================
# 1. DATABASE AUTOMATION & CORE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            steps INTEGER,
            water_ml INTEGER,
            sleep_hours REAL,
            diet_quality TEXT,
            energy_level INTEGER
        )
    ''')
    
    # Pre-populate historical data if database is empty to render dashboard trends
    cursor.execute("SELECT COUNT(*) FROM daily_logs")
    if cursor.fetchone()[0] == 0:
        dummy_data = [
            ((datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d'), 8500, 2000, 7.0, 'Clean', 7),
            ((datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'), 4200, 1200, 5.5, 'Junk', 4),
            ((datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'), 9100, 2500, 8.0, 'Clean', 8),
            ((datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'), 5300, 1500, 6.2, 'Balanced', 5),
            ((datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'), 11200, 3000, 7.5, 'Clean', 9),
            ((datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), 3100, 1100, 5.0, 'Junk', 3),
        ]
        cursor.executemany('''
            INSERT INTO daily_logs (date, steps, water_ml, sleep_hours, diet_quality, energy_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', dummy_data)
        conn.commit()
    conn.close()

init_db()

# ==========================================
# 2. PDF GENERATION ENGINE
# ==========================================
def build_pdf_report():
    pdf_filename = "AuraHealth_Weekly_Report.pdf"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_logs ORDER BY date DESC LIMIT 7")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    # Compute descriptive metrics
    avg_steps = sum(row[2] for row in rows) / len(rows)
    avg_water = sum(row[3] for row in rows) / len(rows)
    avg_sleep = sum(row[4] for row in rows) / len(rows)

    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#111827'), spaceAfter=15)
    section_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#DC2626'), spaceBefore=12, spaceAfter=8)
    body_style = ParagraphStyle('BodyTextCustom', parent=styles['Normal'], fontSize=10.5, leading=15, spaceAfter=6)
    bullet_style = ParagraphStyle('BulletCustom', parent=styles['Normal'], fontSize=10.5, leading=15, leftIndent=15, firstLineIndent=-10, spaceAfter=4)

    story = []
    story.append(Paragraph("AuraHealth Analytics: Weekly Metabolic Diagnostics", title_style))
    story.append(Paragraph(f"Compiled on: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Autonomous System Vector", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("1. System Operational Log (Trailing 7 Intervals)", section_style))
    table_data = [['Interval Date', 'Step Vol', 'Hydration', 'Rest Cycle', 'Diet Metric', 'Energy Index']]
    for row in reversed(rows):
        table_data.append([str(row[1]), f"{row[2]:,}", f"{row[3]}ml", f"{row[4]}h", str(row[5]), f"{row[6]}/10"])
        
    metrics_table = Table(table_data, colWidths=[90, 80, 85, 80, 85, 80])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111827')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F9FAFB')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2. Programmatic Recommendations & Interventions", section_style))
    
    story.append(Paragraph("<b>🏃 Target Movement Protocols:</b>", body_style))
    if avg_steps < 7000:
        story.append(Paragraph("• <b>Primary Exercise:</b> Cardiovascular Deficit Detected. Execute a 35-minute steady-state Zone 2 run or power walk 4 times over the upcoming cycle.", bullet_style))
        story.append(Paragraph("• <b>Activation Variant:</b> Introduce 3 structured micro-circuits consisting of 20 deep bodyweight squats and 15 pushups during sedentary work blocks.", bullet_style))
    else:
        story.append(Paragraph("• <b>Primary Exercise:</b> Baseline Target Exceeded. Maintain current operational pacing. Integrate two 20-minute structural HIIT high-exertion sprint sessions.", bullet_style))
        
    story.append(Paragraph("<b>🥗 Nutritional Swaps & Macro-Schedules:</b>", body_style))
    if avg_water < 2000:
        story.append(Paragraph("• <b>Hydration Pipeline:</b> Drink 500ml of ambient water instantly upon waking up. Restrict morning caffeine execution until baseline hydration is logged.", bullet_style))
    story.append(Paragraph("• <b>Diet Optimization:</b> Limit processed refined carbs. Optimize clean protein density (Lean poultry, fish, paneer, sprouts) adjusted to 1.2 grams per kilogram.", bullet_style))
    
    story.append(Paragraph("<b>🍓 Micronutrient & Whole Fruits Sourcing:</b>", body_style))
    story.append(Paragraph("• <b>Oxidative Defense:</b> Consume 150g of fresh black grapes, raspberries, or wild blueberries during afternoon energy dips to maintain glycemic balance.", bullet_style))
    story.append(Paragraph("• <b>Cellular Fluid Reset:</b> Integrate one medium banana or Kiwi post-workout to immediately replenish essential electrolytes and stabilize glycogen pathways.", bullet_style))
    
    doc.build(story)
    return pdf_filename

# ==========================================
# 3. FASTAPI CONTROLLERS & WEB ROUTING
# ==========================================
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Extract historical tracking blocks
    cursor.execute("SELECT * FROM daily_logs ORDER BY date DESC LIMIT 7")
    logs = cursor.fetchall()
    
    # Calculate rolling system metrics
    cursor.execute("SELECT AVG(steps), AVG(water_ml), AVG(sleep_hours), AVG(energy_level) FROM daily_logs WHERE date >= date('now', '-3 days')")
    trends = cursor.fetchone()
    conn.close()
    
    avg_steps = int(trends[0]) if trends[0] else 0
    avg_water = int(trends[1]) if trends[1] else 0
    avg_sleep = round(trends[2], 1) if trends[2] else 0.0
    avg_energy = round(trends[3], 1) if trends[3] else 0.0

    # Dynamic UI Suggestion Generator based on the database state
    ai_alert_box = ""
    if avg_energy <= 5:
        ai_alert_box += '<div class="p-4 bg-red-950/40 border border-red-900 rounded-xl text-xs text-red-400 mb-3"><strong>⚠️ Energy Warning:</strong> System energy levels are compromised. Avoid complex heavy carbs. Utilize clean espresso or match tea combined with healthy fats.</div>'
    if avg_steps < 6000:
        ai_alert_box += '<div class="p-4 bg-orange-950/40 border border-orange-900 rounded-xl text-xs text-orange-400 mb-3"><strong>⚠️ Movement Deficit:</strong> Sedentary logging detected over your trailing window. Complete a 15-minute desk-side activation sequence immediately.</div>'
    if avg_water < 2000:
        ai_alert_box += '<div class="p-4 bg-blue-950/40 border border-blue-900 rounded-xl text-xs text-blue-400 mb-3"><strong>⚠️ Hydration Notice:</strong> Water metrics are critically tracking low. Consume 500ml fluid instantly to restore cellular balance.</div>'

    if not ai_alert_box:
        ai_alert_box = '<div class="p-4 bg-emerald-950/40 border border-emerald-900 rounded-xl text-xs text-emerald-400 mb-3"><strong>✨ System Optimal:</strong> All metabolic operational categories are holding steady within target boundaries. Keep it up!</div>'

    # Build internal log data rows for the HTML view
    table_rows_html = ""
    for row in logs:
        table_rows_html += f"""
        <tr class="border-b border-gray-800 text-xs text-gray-400">
            <td class="py-3 font-mono">{row[1]}</td>
            <td>{row[2]:,}</td>
            <td>{row[3]}ml</td>
            <td>{row[4]}h</td>
            <td><span class="px-2 py-0.5 rounded text-[10px] {'bg-emerald-950 text-emerald-400' if row[5]=='Clean' else 'bg-amber-950 text-amber-400' if row[5]=='Balanced' else 'bg-red-950 text-red-400'}">{row[5]}</span></td>
            <td class="font-bold text-gray-200">{row[6]}/10</td>
        </tr>
        """

    # Fully stylized HTML layout mimicking the premium dark-contrast dashboard image
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AuraHealth - Intelligent Automation</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f9fafb; }}
        </style>
    </head>
    <body class="text-gray-900 antialiased min-h-screen p-4 md:p-8">
        <div class="max-w-6xl mx-auto">
            
            <header class="flex justify-between items-center mb-8">
                <div class="flex items-center space-x-2">
                    <div class="w-6 h-6 bg-red-600 rounded-full animate-pulse"></div>
                    <span class="text-xl font-bold tracking-tight text-gray-900">Aura<span class="text-red-600">Health</span></span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/download-pdf" class="flex items-center space-x-2 bg-gray-900 text-white hover:bg-gray-800 transition px-4 py-2 rounded-xl text-xs font-semibold shadow-sm">
                        <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        <span>Download Weekly Report PDF</span>
                    </a>
                </div>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                <div class="lg:col-span-7 flex flex-col space-y-6">
                    <div class="bg-[#0a0a0a] text-white rounded-3xl p-6 shadow-xl relative overflow-hidden flex flex-col justify-between min-h-[320px]">
                        <div class="absolute -right-16 -top-16 w-48 h-48 bg-red-600/10 rounded-full blur-3xl"></div>
                        <div>
                            <span class="text-xs font-semibold tracking-wider text-gray-400 uppercase">Check Your Metabolic Status</span>
                            <h2 class="text-3xl font-bold mt-1 text-gray-100">Live Health Engine</h2>
                        </div>
                        
                        <div class="my-auto flex items-baseline space-x-4 py-6">
                            <span class="text-7xl font-extrabold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500 font-mono">{avg_steps:,}</span>
                            <span class="text-sm font-medium text-red-500 uppercase tracking-widest">Avg Steps / Day</span>
                        </div>

                        <div class="border-t border-gray-800 pt-4 flex justify-between text-xs text-gray-400">
                            <div>Water Baseline: <span class="text-gray-200 font-mono">{avg_water}ml</span></div>
                            <div>Sleep Window: <span class="text-gray-200 font-mono">{avg_sleep}hrs</span></div>
                        </div>
                    </div>

                    <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
                        <h3 class="text-sm font-bold text-gray-900 mb-4 flex items-center">
                            <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span> Append Daily Analytics Log
                        </h3>
                        <form action="/log" method="POST" class="grid grid-cols-2 md:grid-cols-3 gap-4">
                            <div>
                                <label class="block text-[10px] uppercase tracking-wider text-gray-500 font-bold mb-1">Steps Count</label>
                                <input type="number" name="steps" required class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-red-500" placeholder="e.g. 8000">
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase tracking-wider text-gray-500 font-bold mb-1">Water Intake (ml)</label>
                                <input type="number" name="water_ml" required class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-red-500" placeholder="e.g. 2500">
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase tracking-wider text-gray-500 font-bold mb-1">Sleep Duration (hrs)</label>
                                <input type="number" step="0.1" name="sleep_hours" required class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-red-500" placeholder="e.g. 7.5">
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase tracking-wider text-gray-500 font-bold mb-1">Diet Profile</label>
                                <select name="diet_quality" class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-red-500">
                                    <option value="Clean">Clean Nutrition</option>
                                    <option value="Balanced">Balanced Mix</option>
                                    <option value="Junk">High Glycemic / Junk</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-[10px] uppercase tracking-wider text-gray-500 font-bold mb-1">Energy Metric (1-10)</label>
                                <input type="number" name="energy_level" min="1" max="10" required class="w-full bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-red-500" placeholder="1 to 10">
                            </div>
                            <div class="flex items-end">
                                <button type="submit" class="w-full bg-red-600 hover:bg-red-700 text-white transition text-xs font-bold py-2 rounded-xl shadow-md shadow-red-600/10">Commit Metrics</button>
                            </div>
                        </form>
                    </div>
                </div>

                <div class="lg:col-span-5 flex flex-col space-y-6">
                    
                    <div class="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
                        <div class="flex items-center space-x-4 mb-4">
                            <div class="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center font-bold text-gray-700 text-lg border border-gray-200">PV</div>
                            <div>
                                <h3 class="font-bold text-gray-900 text-base leading-tight">Pavanateja Vemuri</h3>
                                <p class="text-xs text-gray-400">Target Profile: AI Metabolic Automation</p>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100 text-center">
                            <div class="bg-gray-50 p-3 rounded-xl">
                                <div class="text-[10px] font-bold text-gray-400 uppercase">Sleep Index</div>
                                <div class="text-xl font-bold text-gray-800 mt-0.5">{avg_sleep}h</div>
                            </div>
                            <div class="bg-gray-50 p-3 rounded-xl">
                                <div class="text-[10px] font-bold text-gray-400 uppercase">Energy Delta</div>
                                <div class="text-xl font-bold text-gray-800 mt-0.5 text-red-600">{avg_energy}/10</div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-gray-950 text-white rounded-3xl p-6 shadow-xl border border-gray-800">
                        <h4 class="text-xs font-bold text-red-500 uppercase tracking-widest mb-3 flex items-center">
                            <span class="w-1.5 h-1.5 bg-red-500 rounded-full mr-2 animate-ping"></span> Real-Time Automated Actions
                        </h4>
                        {ai_alert_box}
                    </div>
                </div>
            </div>

            <div class="mt-8 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 overflow-hidden">
                <h3 class="text-sm font-bold text-gray-900 mb-4 uppercase tracking-wider">Historical Time-Series Log</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-gray-100 text-[10px] uppercase text-gray-400 font-bold tracking-wider">
                                <th class="pb-3">Timestamp</th>
                                <th class="pb-3">Step Metric</th>
                                <th class="pb-3">Hydration Volume</th>
                                <th class="pb-3">Rest Allocation</th>
                                <th class="pb-3">Diet Factor</th>
                                <th class="pb-3">System Energy</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-50 text-sm text-gray-700">
                            {table_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/log")
async def log_daily_metrics(
    steps: int = Form(...),
    water_ml: int = Form(...),
    sleep_hours: float = Form(...),
    diet_quality: str = Form(...),
    energy_level: int = Form(...)
):
    today_str = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO daily_logs (date, steps, water_ml, sleep_hours, diet_quality, energy_level)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (today_str, steps, water_ml, sleep_hours, diet_quality, energy_level))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database operational write failure: {e}")
    conn.close()
    
    # After submission, redirect back to the home page to update dashboard views
    return HTMLResponse(content="<script>window.location.href='/';</script>")

@app.get("/download-pdf")
async def download_report():
    file_output = build_pdf_report()
    if not file_output or not os.path.exists(file_output):
        raise HTTPException(status_code=404, detail="Analysis engine failed to find current metrics logs.")
    return FileResponse(path=file_output, filename="AuraHealth_Weekly_Report.pdf", media_type="application/pdf")

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)