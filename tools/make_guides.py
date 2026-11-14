"""Build the free PDF guides for the comment keywords (HOME, STRATEGY, TAX, PENSION, AVD, PROTECT).

Design: navy #0E2A5C + gold, Montserrat (like the weekly RATE UPDATE). Every guide sells the free call:
CTA box on the content pages + full CTA page with QR code to the booking link.
usage: python3 tools/make_guides.py out_dir   (needs /tmp/fnt from `npm pack @fontsource/montserrat`, qrcode, playwright)
"""
import base64, io, os, sys
import qrcode
from playwright.sync_api import sync_playwright

BOOK = "https://outlook.office.com/book/ArenjaRaj@arfinanz.de/"
BOOK_SHORT = "outlook.office.com/book/ArenjaRaj@arfinanz.de"
FNT = "/tmp/fnt/package/files/montserrat-latin-{}-normal.woff2"
STAND = "November 2026"


def font_css():
    css = ""
    for w in (400, 500, 600, 700, 800):
        b64 = base64.b64encode(open(FNT.format(w), "rb").read()).decode()
        css += f"@font-face{{font-family:M;font-weight:{w};src:url(data:font/woff2;base64,{b64}) format('woff2');}}\n"
    return css


def qr_data():
    img = qrcode.make(BOOK, border=1)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


CSS = """
@page{size:A4;margin:0}
*{box-sizing:border-box}
body{margin:0;font-family:M,'Noto Color Emoji',sans-serif;color:#13213b;font-size:10.6pt;line-height:1.5}
.page{width:210mm;height:297mm;position:relative;overflow:hidden;page-break-after:always;padding:20mm 18mm 22mm}
.page:last-child{page-break-after:auto}
.cover{background:linear-gradient(160deg,#0E2A5C 0%,#071733 100%);color:#fff;padding:24mm 20mm}
.cover .brand{letter-spacing:.32em;font-weight:700;color:#D4AF37;font-size:9.5pt}
.cover .kw{display:inline-block;margin-top:28mm;background:#D4AF37;color:#071733;font-weight:800;padding:2mm 5mm;border-radius:20mm;font-size:10pt;letter-spacing:.08em}
.cover h1{font-size:33pt;line-height:1.1;margin:8mm 0 6mm;font-weight:800}
.cover h1 span{color:#D4AF37}
.cover .sub{font-size:13pt;color:#c9d4ea;max-width:150mm}
.cover ul{margin:14mm 0 0;padding:0;list-style:none;font-size:11.5pt}
.cover li{padding:2.2mm 0 2.2mm 9mm;position:relative;border-bottom:1px solid rgba(255,255,255,.12)}
.cover li:before{content:'';position:absolute;left:0;top:4.2mm;width:4mm;height:4mm;border-radius:1mm;background:#D4AF37}
.cover .foot{position:absolute;left:20mm;right:20mm;bottom:18mm;display:flex;justify-content:space-between;align-items:flex-end;font-size:9pt;color:#9fb0cf}
.cover .foot b{color:#fff;font-size:13pt}
.cover .ring{position:absolute;right:-40mm;top:-40mm;width:140mm;height:140mm;border-radius:50%;border:2px solid rgba(212,175,55,.35)}
.cover .ring2{position:absolute;right:-20mm;top:-20mm;width:100mm;height:100mm;border-radius:50%;border:2px solid rgba(212,175,55,.2)}
.hdr{display:flex;justify-content:space-between;font-size:8pt;color:#7a88a3;letter-spacing:.18em;font-weight:600;margin-bottom:7mm}
.hdr b{color:#0E2A5C}
h2{font-size:19pt;color:#0E2A5C;margin:0 0 2mm;font-weight:800;line-height:1.2}
h2 small{display:block;font-size:9pt;color:#D4AF37;letter-spacing:.2em;font-weight:700;margin-bottom:1mm}
h3{font-size:12pt;color:#0E2A5C;margin:6mm 0 2mm;font-weight:700}
p{margin:0 0 3mm}
.lead{font-size:11.5pt;color:#33415c;margin-bottom:5mm}
table{width:100%;border-collapse:collapse;margin:2mm 0 4mm;font-size:9.8pt}
th{background:#0E2A5C;color:#fff;text-align:left;padding:2mm 3mm;font-weight:600}
td{padding:1.8mm 3mm;border-bottom:1px solid #e3e8f1}
tr.hl td{background:#fff4cc;font-weight:700}
td.r,th.r{text-align:right}
.note{font-size:8pt;color:#6b7891;margin-top:-2mm;margin-bottom:4mm}
.grid+.note{margin-top:2mm}
.check{list-style:none;padding:0;margin:2mm 0 4mm}
.check li{padding:1.6mm 0 1.6mm 9mm;position:relative}
.check li:before{content:'';position:absolute;left:0;top:2.2mm;width:4.2mm;height:4.2mm;border:1.6px solid #0E2A5C;border-radius:1mm}
.dots{padding-left:5mm;margin:1mm 0 4mm}.dots li{margin:1.2mm 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:5mm}
.card{border:1px solid #e3e8f1;border-radius:3mm;padding:4mm 5mm;background:#f7f9fc}
.card h4{margin:0 0 1.5mm;color:#0E2A5C;font-size:10.8pt}
.card p{margin:0;font-size:9.6pt}
.trap{border-left:4px solid #E4002B;background:#fff3f5;padding:3mm 5mm;border-radius:0 3mm 3mm 0;margin:3mm 0}
.trap b{color:#b3001f}
.tip{border-left:4px solid #D4AF37;background:#fffaf0;padding:3mm 5mm;border-radius:0 3mm 3mm 0;margin:3mm 0}
.big{font-size:22pt;font-weight:800;color:#0E2A5C;line-height:1}
.cta{position:absolute;left:18mm;right:18mm;bottom:16mm;background:#0E2A5C;color:#fff;border-radius:4mm;padding:4.5mm 6mm;display:flex;justify-content:space-between;align-items:center;gap:6mm}
.cta .t{font-weight:700;font-size:11pt}.cta .s{font-size:8.8pt;color:#c9d4ea}
.cta .btn{background:#D4AF37;color:#071733;font-weight:800;padding:2.5mm 5mm;border-radius:20mm;white-space:nowrap;font-size:9.5pt;text-decoration:none}
.pn{position:absolute;bottom:7mm;right:18mm;font-size:7.5pt;color:#9aa6bd}
.final{background:linear-gradient(160deg,#0E2A5C 0%,#071733 100%);color:#fff}
.final h2{color:#fff;font-size:26pt}
.final h2 small{color:#D4AF37}
.final .lead{color:#c9d4ea}
.steps{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4mm;margin:6mm 0}
.steps div{background:rgba(255,255,255,.07);border:1px solid rgba(212,175,55,.35);border-radius:3mm;padding:4mm}
.steps b{display:block;color:#D4AF37;font-size:20pt;font-weight:800}
.book{display:flex;gap:8mm;align-items:center;background:#fff;color:#0E2A5C;border-radius:4mm;padding:6mm;margin-top:6mm}
.book img{width:38mm;height:38mm}
.book .u{font-weight:700;font-size:10pt;word-break:break-all}
.book .h{font-size:16pt;font-weight:800;margin-bottom:2mm}
.trust{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4mm;margin-top:7mm;font-size:9pt;color:#c9d4ea}
.trust b{display:block;color:#fff;font-size:10.5pt}
.legal{position:absolute;left:20mm;right:20mm;bottom:10mm;font-size:7.2pt;color:#8797b5;line-height:1.45}
"""

LEGAL = ("Arenja &amp; Raj Finanz GmbH – Immobiliardarlehensvermittler §34i GewO und Versicherungsmakler §34d GewO, "
         "Reg.-Nr. D-CEI8-HT1SJ-75, IHK zu Lübeck. General information as of " + STAND + ", no individual advice, no tax or legal advice. "
         "All examples are illustrations, not guarantees – rules, rates and prices can change.")


def cover(kw, title, sub, bullets):
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    return f"""<section class="page cover"><div class="ring"></div><div class="ring2"></div>
<div class="brand">ARENJA &amp; RAJ FINANZ</div>
<div class="kw">FREE GUIDE · {kw}</div>
<h1>{title}</h1><div class="sub">{sub}</div><ul>{lis}</ul>
<div class="foot"><div><b>@arfinanz</b><br>Mortgage &amp; insurance brokers for expats in Germany<br>English · Hindi · German</div><div>{STAND}</div></div></section>"""


def page(kw, n, body, cta_t, cta_s):
    return f"""<section class="page"><div class="hdr"><span><b>ARENJA &amp; RAJ FINANZ</b> · FREE GUIDE {kw}</span><span>@arfinanz</span></div>
{body}
<div class="cta"><div><div class="t">{cta_t}</div><div class="s">{cta_s}</div></div><a class="btn" href="{BOOK}">Book free call →</a></div>
<div class="pn">{n}</div></section>"""


def final(title, lead, steps, qr):
    st = "".join(f"<div><b>{i+1}</b>{s}</div>" for i, s in enumerate(steps))
    return f"""<section class="page final"><div class="hdr" style="color:#8797b5"><span><b style="color:#D4AF37">ARENJA &amp; RAJ FINANZ</b></span><span>@arfinanz</span></div>
<h2><small>YOUR NEXT STEP</small>{title}</h2><p class="lead">{lead}</p>
<div class="steps">{st}</div>
<div class="book"><a href="{BOOK}"><img src="{qr}"></a><div><div class="h">Book your free 30-minute call</div>
<div>Scan the code or tap the link – pick a time that suits you. Online, in English, Hindi or German.</div>
<div class="u" style="margin-top:2mm"><a href="{BOOK}" style="color:#0E2A5C">{BOOK_SHORT}</a></div>
<div style="margin-top:2mm;font-size:9pt">Or send us a DM on Instagram: <b>@arfinanz</b></div></div></div>
<div class="trust"><div><b>Licensed brokers</b>§34i (mortgages) and §34d (insurance) GewO</div><div><b>Many banks &amp; insurers</b>We compare – you don't have to visit them one by one</div><div><b>Made for expats</b>Blue Card, no SCHUFA history, family in India – we know the questions</div></div>
<div class="legal">{LEGAL}</div></section>"""


def guides(qr):
    G = {}
    # ---------------------------------------------------------------- HOME
    kw = "HOME"
    G[kw] = [
        cover(kw, "Buying your first home in <span>Germany</span> as an expat",
              "What banks really check, what it costs on top of the price, and how families get up to €180,000 from KfW.",
              ["Can expats buy? Myths vs. reality", "The real costs: tax, notary, broker – per federal state",
               "KfW family loans: up to €180,000 (existing) / €270,000 (new build)", "How much can you afford? Table by net income",
               "The 10 documents every bank asks for"]),
        page(kw, 2, """<h2><small>STEP 1</small>Yes, you can buy – without a German passport</h2>
<p class="lead">German banks don't ask for citizenship or perfect German. They look at four things: stable income, how long you can stay, your existing debts and how much of the extra costs you can pay yourself.</p>
<div class="grid">
<div class="card"><h4>❌ "I need a German passport"</h4><p>✅ No. A residence permit or Blue Card works. Banks look at how long it is valid and whether a permanent permit is in sight.</p></div>
<div class="card"><h4>❌ "No bank lends to expats"</h4><p>✅ Many do – but not every bank. Some want a permanent permit, others accept a Blue Card. That's why comparing matters.</p></div>
<div class="card"><h4>❌ "I need 20–30% equity"</h4><p>✅ Not always. Strong incomes can get up to 100% of the price financed. The extra buying costs you usually pay yourself.</p></div>
<div class="card"><h4>❌ "My SCHUFA is empty, so no chance"</h4><p>✅ A short history is normal for expats. Clean bank statements and no open consumer loans count a lot.</p></div></div>
<h3>What every bank checks</h3>
<ul class="check"><li><b>Income &amp; job:</b> permanent contract, probation period over (big plus)</li>
<li><b>Residence:</b> type of permit and how long it is valid</li>
<li><b>Debts:</b> car loans, credit cards, "buy now pay later" – they reduce your loan amount</li>
<li><b>Equity:</b> at least the buying costs (around 8–12% of the price) from savings</li>
<li><b>Bank statements:</b> regularly in the red on your account (Dispo) is a warning sign</li></ul>""",
             "Not sure if a bank will finance you?", "We check your chances with several banks at once – before you fall in love with a flat."),
        page(kw, 3, """<h2><small>STEP 2</small>The real price: costs on top of the purchase price</h2>
<p class="lead">On top of the price you pay property transfer tax (Grunderwerbsteuer), notary + land register and – if a broker is involved – the broker fee. Most banks want you to pay these from savings.</p>
<table><tr><th>Federal state</th><th class="r">Transfer tax</th><th>Federal state</th><th class="r">Transfer tax</th></tr>
<tr><td>Bavaria</td><td class="r">3.5%</td><td>Hesse</td><td class="r">6.0%</td></tr>
<tr><td>Baden-Württemberg</td><td class="r">5.0%</td><td>Mecklenburg-Vorpommern</td><td class="r">6.0%</td></tr>
<tr><td>Bremen, Lower Saxony</td><td class="r">5.0%</td><td>Brandenburg</td><td class="r">6.5%</td></tr>
<tr><td>Rhineland-Palatinate, Saxony-Anhalt</td><td class="r">5.0%</td><td>North Rhine-Westphalia</td><td class="r">6.5%</td></tr>
<tr><td>Thuringia</td><td class="r">5.0%</td><td>Saarland</td><td class="r">6.5%</td></tr>
<tr><td>Hamburg, Saxony</td><td class="r">5.5%</td><td>Schleswig-Holstein</td><td class="r">6.5%</td></tr>
<tr><td>Berlin</td><td class="r">6.0%</td><td></td><td></td></tr></table>
<p class="note">Rates 2026 (baufi24, as of Nov 2026). Notary + land register: rule of thumb about 1.5–2% of the price. Broker: buyer's share usually up to 3.57% incl. VAT.</p>
<h3>Example: flat for €400,000</h3>
<table><tr><th></th><th class="r">NRW</th><th class="r">Bavaria</th></tr>
<tr><td>Transfer tax</td><td class="r">€26,000</td><td class="r">€14,000</td></tr>
<tr><td>Notary + land register (2%)</td><td class="r">€8,000</td><td class="r">€8,000</td></tr>
<tr><td>Broker (3.57%)</td><td class="r">€14,280</td><td class="r">€14,280</td></tr>
<tr class="hl"><td>Extra costs total</td><td class="r">€48,280</td><td class="r">€36,280</td></tr></table>
<div class="tip">💡 <b>Tip:</b> These costs are the number to save for first – not 20% of the price.</div>""",
             "How much do you need to save?", "In the call we calculate your exact buying costs and how much the bank can finance."),
        page(kw, 4, """<h2><small>STEP 3 · STATE MONEY</small>KfW family loans: up to €180,000 for an old home</h2>
<p class="lead">KfW is Germany's state-owned development bank. With children you can get a low-interest loan on top of your normal mortgage. Many families don't know it exists – or apply too late.</p>
<h3>"Jung kauft Alt" (KfW 308) – existing house or flat</h3>
<table><tr><th>Children</th><th class="r">Max. taxable income</th><th class="r">KfW loan up to</th></tr>
<tr><td>1 child</td><td class="r">€90,000</td><td class="r">€140,000</td></tr>
<tr class="hl"><td>2 children</td><td class="r">€100,000</td><td class="r">€160,000</td></tr>
<tr><td>3+ children</td><td class="r">€110,000 (+€10,000 per extra child)</td><td class="r">€180,000</td></tr></table>
<ul class="check"><li>At least one child under 18 lives with you</li><li>Home has energy class F, G or H – and you renovate it within 4.5 years</li>
<li>Nobody in your household owns a home <b>in Germany</b> – 🇮🇳 a flat in India does not count</li>
<li>Income = average taxable household income of the 2nd and 3rd year before you apply (German tax assessments)</li></ul>
<h3>"Wohneigentum für Familien" (KfW 300) – new build</h3>
<p>For new, very energy-efficient homes (Efficiency House 40): €170,000–€220,000, with sustainability seal (QNG) €220,000–€270,000, depending on the number of children. Same income limits.</p>
<div class="trap"><b>⚠️ The #1 mistake:</b> signing the purchase contract first. The KfW loan must be applied for through your financing partner <b>before</b> you buy (or the contract needs a condition). Afterwards it's too late.</div>
<p class="note">Sources: KfW leaflet 308 (08/2026), kfw.de programme 300 (2026). Many federal states have their own extra programmes – we check them for you.</p>""",
             "Do you qualify for KfW?", "We check KfW + state programmes and apply for them together with your mortgage."),
        page(kw, 5, """<h2><small>STEP 4</small>How much home can you afford?</h2>
<p class="lead">A common rule: your monthly loan payment should be at most about 35% of your household net income. Find your income in the table.</p>
<table><tr><th>Household net income / month</th><th class="r">Max. payment (35%)</th><th class="r">Possible loan (example)</th></tr>
<tr><td>€3,000</td><td class="r">€1,050</td><td class="r">≈ €210,000</td></tr>
<tr><td>€4,000</td><td class="r">€1,400</td><td class="r">≈ €280,000</td></tr>
<tr class="hl"><td>€5,000</td><td class="r">€1,750</td><td class="r">≈ €350,000</td></tr>
<tr><td>€6,000</td><td class="r">€2,100</td><td class="r">≈ €420,000</td></tr>
<tr><td>€7,000</td><td class="r">€2,450</td><td class="r">≈ €490,000</td></tr></table>
<p class="note">Example: 4.0% interest + 2.0% initial repayment per year. Your real rate depends on equity, term and the market. A KfW loan on top can increase what's possible.</p>
<h3>The 10 documents banks ask for</h3>
<ul class="check" style="columns:2;column-gap:8mm">
<li>Passport + residence permit</li><li>Work contract</li><li>Last 3 payslips</li><li>Last tax assessment (Steuerbescheid)</li><li>Bank statements, last 3 months</li>
<li>SCHUFA report</li><li>Proof of savings</li><li>Exposé of the property</li><li>Floor plan + living area</li><li>Land register extract</li></ul>
<div class="tip">💡 Collect these before viewing flats – then you can make an offer with a financing confirmation in days, not weeks.</div>""",
             "Want your personal number?", "We calculate your budget with real offers from several banks – free."),
        final("Let's find out what you can buy – and which KfW money you get",
              "In a free 30-minute call we look at your situation and give you a clear answer. No obligation, no hard sell.",
              ["We check your budget, residence permit and documents", "We check KfW and state programmes you qualify for", "You get real offers from several banks to compare"], qr)]
    # ---------------------------------------------------------------- STRATEGY
    kw = "STRATEGY"
    G[kw] = [
        cover(kw, "Your first <span>rental property</span> in Germany",
              "How tenants help pay your loan, which three numbers decide if a flat is a good deal, and what expats should plan for.",
              ["Why a rental flat – and the honest downsides", "The 3 numbers to check before you buy", "A full example with real cash flow",
               "Depreciation (AfA) in one table", "Checklist for viewing a buy-to-let flat"]),
        page(kw, 2, """<h2><small>WHY PROPERTY</small>Your tenant pays a big part of the loan</h2>
<p class="lead">With a rental flat, the rent covers most of the monthly loan payment. Over 20–30 years the loan shrinks and the flat becomes your wealth – often with tax benefits on the way.</p>
<div class="grid">
<div class="card"><h4>🏦 Leverage</h4><p>The bank finances most of the price. You build wealth with the bank's money, not only your savings.</p></div>
<div class="card"><h4>📉 Tax effect</h4><p>Interest, depreciation and costs are deducted from the rent. A loss can lower your income tax.</p></div>
<div class="card"><h4>⏳ 10-year rule</h4><p>A privately held rental flat sold after more than 10 years: the gain is generally tax-free (§23 EStG).</p></div>
<div class="card"><h4>🇮🇳 Moving back?</h4><p>The flat can stay rented. Rental income from German property is generally taxed in Germany.</p></div></div>
<h3>The honest part</h3>
<ul class="dots"><li>Most good deals have a <b>negative cash flow</b> at the start – you add some money every month.</li>
<li>Vacancy, repairs and a difficult tenant happen. Plan a buffer.</li>
<li>Interest rates matter: 1 percentage point more changes the numbers a lot.</li></ul>
<p>That's why the right financing structure (term, repayment, KfW, equity) decides whether a flat works for you.</p>""",
             "Is a rental flat right for you?", "We calculate your personal plan – how much, how fast, and what it costs you per month."),
        page(kw, 3, """<h2><small>CHECK BEFORE YOU BUY</small>The 3 numbers that decide</h2>
<table><tr><th>Number</th><th>How to calculate</th><th>Rule of thumb</th></tr>
<tr><td><b>1. Gross yield</b></td><td>Annual cold rent ÷ price × 100</td><td>Below ~4%: check carefully</td></tr>
<tr><td><b>2. Price factor</b></td><td>Price ÷ annual cold rent</td><td>Above ~25: expensive</td></tr>
<tr><td><b>3. Monthly cash flow</b></td><td>Rent – loan payment – non-recoverable costs (+ tax effect)</td><td>Know it before you sign</td></tr></table>
<h3>Example: flat for €250,000, rent €900/month</h3>
<table><tr><th></th><th class="r">Per year</th><th class="r">Per month</th></tr>
<tr><td>Cold rent</td><td class="r">€10,800</td><td class="r">€900</td></tr>
<tr><td>Loan €250,000 (4% interest + 2% repayment)</td><td class="r">–€15,000</td><td class="r">–€1,250</td></tr>
<tr><td>Non-recoverable costs (≈10% of rent)</td><td class="r">–€1,080</td><td class="r">–€90</td></tr>
<tr class="hl"><td>Cash flow before tax</td><td class="r">–€5,280</td><td class="r">–€440</td></tr>
<tr><td>Tax effect at 42% (loss ≈ €4,030)</td><td class="r">+€1,693</td><td class="r">+€141</td></tr>
<tr class="hl"><td>Cash flow after tax</td><td class="r">≈ –€3,590</td><td class="r">≈ –€299</td></tr></table>
<p class="note">Gross yield 4.3%, price factor 23.1. Tax loss: rent €10,800 – interest ≈€10,000 – AfA €3,750 (2% of 75% building share) – costs €1,080. Year 1, simplified, buying costs paid from savings. Example only – not tax advice.</p>
<div class="tip">💡 €299 a month for a flat worth €250,000 that the tenant pays off – that's the logic. Whether it fits your budget, we calculate with your numbers.</div>""",
             "Got a flat in mind?", "Send us the exposé – we run the numbers and show you the financing options."),
        page(kw, 4, """<h2><small>TAX BASICS</small>Depreciation (AfA) in one table</h2>
<p class="lead">You can deduct the building part of the price (not the land) over many years. Which rate applies depends on when the building was finished or started.</p>
<table><tr><th>Building</th><th class="r">AfA per year</th><th>Note</th></tr>
<tr><td>Built before 1925</td><td class="r">2.5%</td><td>linear, 40 years</td></tr>
<tr><td>Built 1925 – 2022</td><td class="r">2%</td><td>linear, 50 years</td></tr>
<tr><td>Finished from 2023</td><td class="r">3%</td><td>linear, about 33 years</td></tr>
<tr class="hl"><td>New build, construction started / bought 01.10.2023 – 30.09.2029</td><td class="r">5% declining</td><td>of the remaining value (§7 (5a) EStG)</td></tr>
<tr><td>Energy-efficient new rental flats</td><td class="r">+5% special</td><td>first 4 years, limits apply (§7b EStG)</td></tr></table>
<p class="note">Source: §7 EStG (lohnsteuer-kompakt, 2025/26). Details and your case: please ask a tax advisor.</p>
<h3>Viewing checklist for a buy-to-let flat</h3>
<ul class="check"><li>Rent vs. local rent index (Mietspiegel) – is the rent realistic?</li><li>Owners' reserve (Erhaltungsrücklage) – is enough saved for repairs?</li>
<li>Minutes of the last 3 owners' meetings – big repairs planned?</li><li>Energy certificate – heating type and class</li>
<li>Declaration of division (Teilungserklärung) – what exactly do you own?</li><li>Location: jobs, transport, population trend</li></ul>""",
             "Want a second opinion on a flat?", "We look at the numbers with you before you commit."),
        final("Let's build your property plan",
              "In a free 30-minute call we work out how much you can invest, what it costs you per month and which bank structure fits.",
              ["We look at income, equity and goals", "We calculate cash flow and financing for a real flat", "You get offers from several banks"], qr)]
    # ---------------------------------------------------------------- TAX
    kw = "TAX"
    G[kw] = [
        cover(kw, "How a rental property can <span>lower your tax</span>",
              "The deductions landlords in Germany use – explained simply. Plus: how to get the benefit every month, not once a year.",
              ["What you can deduct as a landlord", "Your tax saving by tax rate – table", "Get it monthly on your payslip",
               "The 15% trap in the first 3 years", "10-year rule and spouse strategies"]),
        page(kw, 2, """<h2><small>THE BASICS</small>Why property can lower your tax</h2>
<p class="lead">Rental income is taxed – but only after costs. In the first years, interest and depreciation are often higher than the rent. That loss is offset against your salary, so you pay less income tax.</p>
<h3>Typical deductible costs (Werbungskosten)</h3>
<div class="grid">
<div class="card"><h4>🏦 Loan interest</h4><p>Interest on the loan for the rental flat (not the repayment).</p></div>
<div class="card"><h4>📉 Depreciation (AfA)</h4><p>2–3% of the building value per year, new builds up to 5% declining.</p></div>
<div class="card"><h4>🔧 Repairs &amp; maintenance</h4><p>Often deductible right away – watch the 15% rule (page 3).</p></div>
<div class="card"><h4>🧾 Other costs</h4><p>Property management, non-recoverable service charges, insurance, tax advisor share, trips to the flat, tenant search.</p></div></div>
<h3>What it's worth: tax saving per €5,000 loss</h3>
<table><tr><th>Your personal tax rate</th><th class="r">Saving per year</th><th class="r">Per month</th></tr>
<tr><td>30%</td><td class="r">€1,500</td><td class="r">€125</td></tr><tr><td>35%</td><td class="r">€1,750</td><td class="r">€146</td></tr>
<tr class="hl"><td>42%</td><td class="r">€2,100</td><td class="r">€175</td></tr></table>
<p class="note">Simplified, without solidarity surcharge / church tax. Your rate depends on your income – your tax advisor can tell you.</p>""",
             "How big could your effect be?", "We calculate the financing side – your tax advisor confirms the tax side."),
        page(kw, 3, """<h2><small>MORE CASH EVERY MONTH</small>Don't wait 12 months for your refund</h2>
<p class="lead">Most people get the tax benefit once a year with the tax return. But you can apply at the tax office for an allowance (Freibetrag / Lohnsteuerermäßigung) for expected rental losses. Then less wage tax is taken from your payslip every month.</p>
<div class="tip">💡 Apply with the form "Antrag auf Lohnsteuer-Ermäßigung" at your Finanzamt (also online via ELSTER) – ideally with your tax advisor.</div>
<div class="trap"><b>⚠️ The 15% trap:</b> If renovation costs in the first 3 years after buying are higher than 15% of the building value (without VAT), they are not deducted right away – they are added to the building and depreciated over decades (§6 (1) 1a EStG). Plan big renovations with your tax advisor.</div>
<h3>Two rules worth knowing</h3>
<div class="grid">
<div class="card"><h4>⏳ 10-year rule</h4><p>Sell a privately held rental flat after more than 10 years: the gain is generally tax-free (§23 EStG). Sell earlier: the gain is taxed.</p></div>
<div class="card"><h4>💑 Spouse strategies</h4><p>Some couples structure ownership between spouses (e.g. "Ehegattenschaukel"). This only works with a real contract, real financing and a tax advisor – done wrong, the tax office rejects it.</p></div></div>
<p class="note">General information, not tax advice. We are mortgage and insurance brokers, not tax advisors – we work together with yours.</p>""",
             "Planning your first rental flat?", "We find the financing that fits your tax plan – free first call."),
        page(kw, 4, """<h2><small>CHECKLIST</small>Before you buy for tax reasons</h2>
<p class="lead">Tax savings are a bonus, not the reason to buy. A flat must make sense without them. Use this list:</p>
<ul class="check"><li>Does the flat work with a realistic rent and some vacancy?</li><li>Can you carry the monthly cash flow for 10+ years?</li>
<li>Is the building / land split (Kaufpreisaufteilung) realistic? It decides your AfA.</li><li>Which AfA rate applies (2%, 3%, 5% declining, §7b)?</li>
<li>Renovations planned in the first 3 years? → 15% rule</li><li>Allowance on your payslip applied for?</li>
<li>Do you plan to move back to India? → rental income from German property is generally taxed in Germany</li>
<li>Tax advisor on board before signing</li></ul>
<div class="tip">💡 The financing structure changes your tax effect too: more interest in the early years means a higher deduction – but also higher costs. We show you both sides.</div>""",
             "Let's look at your numbers", "Free 30-minute call – financing, cash flow and the questions for your tax advisor."),
        final("Let's see what a rental flat does for you",
              "In a free 30-minute call we calculate financing and cash flow and give you the right questions for your tax advisor.",
              ["We look at your income, tax bracket and savings", "We calculate a real example with financing and tax effect", "You get bank offers – your tax advisor checks the tax part"], qr)]
    # ---------------------------------------------------------------- PENSION
    kw = "PENSION"
    G[kw] = [
        cover(kw, "Your <span>pension gap</span> in Germany – and how to close it",
              "Why expats get less state pension than their German colleagues, what happens if you move back to India, and the 3 ways to fix it.",
              ["How the German state pension is calculated", "Find your starting age: your gap in euros", "Moving back to India: what happens to your pension",
               "Company pension: your boss must add 15%", "Your 5-step pension check"]),
        page(kw, 2, """<h2><small>HOW IT WORKS</small>One year, one point, €42.52</h2>
<p class="lead">For every year you earn the average salary, you get 1 pension point. Since July 2026, 1 point = <b>€42.52 per month</b> of pension. Fewer years in Germany = fewer points.</p>
<h3>Find your starting age 👇 (pension from 67, average salary)</h3>
<table><tr><th>Started working in Germany at</th><th class="r">Years</th><th class="r">Pension / month</th><th class="r">Less than at 22</th></tr>
<tr><td>22</td><td class="r">45</td><td class="r">€1,913</td><td class="r">–</td></tr>
<tr><td>25</td><td class="r">42</td><td class="r">€1,786</td><td class="r">€128</td></tr>
<tr><td>28</td><td class="r">39</td><td class="r">€1,658</td><td class="r">€255</td></tr>
<tr class="hl"><td>30</td><td class="r">37</td><td class="r">€1,573</td><td class="r">€340</td></tr>
<tr><td>32</td><td class="r">35</td><td class="r">€1,488</td><td class="r">€425</td></tr>
<tr><td>35</td><td class="r">32</td><td class="r">€1,361</td><td class="r">€553</td></tr>
<tr><td>40</td><td class="r">27</td><td class="r">€1,148</td><td class="r">€765</td></tr></table>
<p class="note">Example: 1 pension point per year, value €42.52 (since 01.07.2026), before tax and health insurance. Your years in India don't add to the German amount.</p>
<div class="trap"><b>⚠️ And that's before tax:</b> pensions are taxed and you pay health insurance on them. The real gap to your last salary is bigger.</div>""",
             "How big is YOUR gap?", "We calculate it from your pension statement (Renteninformation) – free."),
        page(kw, 3, """<h2><small>INDIA 🇮🇳 + GERMANY 🇩🇪</small>Moving back one day?</h2>
<div class="grid">
<div class="card"><h4>✅ Your pension follows you</h4><p>Germany and India have a social security agreement. The German pension insurance pays your German pension to you in India.</p></div>
<div class="card"><h4>✅ 5-year minimum</h4><p>You need at least 5 years of contributions. Under the agreement, insurance periods in India can be added to reach that minimum.</p></div>
<div class="card"><h4>⚠️ The amount stays small</h4><p>The amount only comes from the years you paid in Germany. Fewer years here = smaller pension in India.</p></div>
<div class="card"><h4>📄 Before you leave</h4><p>Request your pension record (Versicherungsverlauf) and check that all German years are in it.</p></div></div>
<h2 style="margin-top:7mm"><small>THE FIX</small>3 ways to close the gap</h2>
<table><tr><th>Option</th><th>What it is</th><th>Why it helps expats</th></tr>
<tr><td><b>Company pension (bAV)</b></td><td>Part of your gross salary goes into a pension plan</td><td>If your employer saves social security that way, they must add 15% (§1a BetrAVG)</td></tr>
<tr><td><b>Pension depot (AVD)</b></td><td>New state-subsidised depot from 01.01.2027</td><td>Up to €540/year + €300 per child from the state</td></tr>
<tr><td><b>Private pension</b></td><td>Private pension insurance / Rürup</td><td>Lifelong payout – you can't outlive it</td></tr></table>""",
             "Which mix fits you?", "We compare company pension, AVD and private options for your situation."),
        page(kw, 4, """<h2><small>NO EPF IN GERMANY</small>Your boss can add money – if you ask</h2>
<p class="lead">In India your employer pays into your EPF automatically. In Germany, the company pension (Entgeltumwandlung) only starts if you ask for it.</p>
<div class="grid"><div class="card"><h4>You put in</h4><div class="big">€200</div><p>per month from your gross salary</p></div>
<div class="card"><h4>Your employer adds (min. 15%)</h4><div class="big">€30</div><p>per month – many employers pay more</p></div></div>
<div class="tip">💡 Ask HR exactly this: <b>"Do we offer Entgeltumwandlung with the employer subsidy (Arbeitgeberzuschuss)?"</b></div>
<h3>Your 5-step pension check</h3>
<ul class="check"><li>Find your latest pension statement (Renteninformation) – or request it at deutsche-rentenversicherung.de</li>
<li>Check your record (Versicherungsverlauf): are all German years in it?</li><li>Ask HR about the company pension and employer subsidy</li>
<li>Write down: what monthly income do you want at 67?</li><li>Book a free call – we calculate your gap and the cheapest way to close it</li></ul>
<p class="note">Collective agreements can differ. Examples, not guarantees.</p>""",
             "Let's calculate your gap together", "Bring your Renteninformation – in 30 minutes you know your number."),
        final("Let's calculate your pension gap",
              "In a free 30-minute call we read your pension statement with you, show your gap in euros and the cheapest way to close it.",
              ["We check your German pension record and years", "We calculate your gap – with or without moving back to India", "We compare company pension, AVD and private plans"], qr)]
    # ---------------------------------------------------------------- AVD
    kw = "AVD"
    G[kw] = [
        cover(kw, "The new <span>pension depot</span> (AVD) from 2027",
              "Up to €540 a year from the state – plus €300 per child. How it works, what you get, and the mistakes that cost you money.",
              ["The subsidy in one table", "Find your contribution: what the state adds", "Families: the child bonus", "Payout, switching, costs",
               "3 mistakes to avoid"]),
        page(kw, 2, """<h2><small>START 01.01.2027</small>How the state subsidy works</h2>
<p class="lead">The Altersvorsorgedepot (AVD) is a new state-subsidised pension account, decided by the Bundestag (27.03.2026) and Bundesrat (08.05.2026). You pay in, the state adds a bonus.</p>
<div class="grid"><div class="card"><h4>Your first €360 per year</h4><div class="big">+50%</div><p>the state adds 50 cents per euro (max. €180)</p></div>
<div class="card"><h4>From €361 to €1,800 per year</h4><div class="big">+25%</div><p>the state adds 25 cents per euro (max. €360)</p></div>
<div class="card"><h4>Per child</h4><div class="big">+€300</div><p>per year, reached with €25 a month</p></div>
<div class="card"><h4>Starting before 25?</h4><div class="big">+€200</div><p>one-time bonus for young savers</p></div></div>
<h3>Find your contribution 👇 state bonus per year</h3>
<table><tr><th>You pay / month</th><th class="r">No children</th><th class="r">1 child</th><th class="r">2 children</th></tr>
<tr><td>€10</td><td class="r">€60</td><td class="r">€180</td><td class="r">€300</td></tr>
<tr><td>€25</td><td class="r">€150</td><td class="r">€450</td><td class="r">€750</td></tr>
<tr><td>€50</td><td class="r">€240</td><td class="r">€540</td><td class="r">€840</td></tr>
<tr><td>€100</td><td class="r">€390</td><td class="r">€690</td><td class="r">€990</td></tr>
<tr class="hl"><td>€150</td><td class="r">€540</td><td class="r">€840</td><td class="r">€1,140</td></tr></table>
<p class="note">Rules as of Nov 2026; details (BMF guidance) can still change. Minimum €120 a year, otherwise no subsidy. Child bonus for children with Kindergeld, goes to one parent.</p>""",
             "Which contribution fits you?", "We calculate your bonus and how the AVD fits into your pension plan."),
        page(kw, 3, """<h2><small>GOOD TO KNOW</small>Payout, switching, tax</h2>
<ul class="dots"><li><b>Payout:</b> from age 65 at the earliest – as a lifelong pension or a payout plan until at least 85; up to 30% can be taken as a lump sum.</li>
<li><b>Tax:</b> contributions can be deducted as special expenses (Sonderausgaben); gains are tax-free while saving, the payout is taxed later.</li>
<li><b>Switching provider:</b> in the first 5 years it can cost up to €150, afterwards free.</li>
<li><b>Who can use it:</b> employees and – new – also self-employed people.</li>
<li><b>Old Riester contract?</b> It can continue or be paused. Check before you cancel anything.</li></ul>
<h3>The smart split</h3>
<div class="tip">💡 The state only subsidises up to €1,800 a year (€150 a month). Money in the AVD is locked until retirement. So: <b>€150 a month into the AVD, everything above into a flexible savings plan</b> you can access anytime.</div>
<h3>3 mistakes that cost you money</h3>
<div class="trap"><b>❌ Starting late:</b> every year without a contract = up to €540 + €300 per child lost.</div>
<div class="trap"><b>❌ High fees:</b> fees can eat a big part of the bonus. Compare costs before you sign.</div>
<div class="trap"><b>❌ Child bonus with the wrong parent:</b> it goes to one parent – assign it to the one who actually saves.</div>
<p class="note">Sources: Altersvorsorgereformgesetz (Bundestag 27.03.2026, Bundesrat 08.05.2026); fonder-vergleiche.de, vorsorgedepot-lotse.de (as of 2026).</p>""",
             "Don't sign the first offer", "We look at the AVD together with your whole pension – company pension, private, state."),
        page(kw, 4, """<h2><small>FOR EXPATS</small>Why the AVD matters more for you</h2>
<p class="lead">You started paying into the German pension later than your German colleagues – so your state pension will be smaller. The AVD bonus is one of the cheapest ways to close part of that gap.</p>
<div class="grid"><div class="card"><h4>Example family</h4><p>Parent pays €50/month (€600/year), 2 children with Kindergeld → state adds <b>€840 per year</b>. That's more than you pay in.</p></div>
<div class="card"><h4>Moving back to India?</h4><p>Ask before you sign what happens to the bonus and the depot if you leave Germany – the rules for moving abroad matter.</p></div></div>
<h3>Your AVD checklist</h3>
<ul class="check"><li>How much can I save per month – €10, €25, €50, €150?</li><li>Do I have children with Kindergeld? Which parent gets the child bonus?</li>
<li>Do I already have a company pension? Does my employer add money?</li><li>Old Riester contract – continue, pause or switch?</li><li>Do I plan to stay in Germany until retirement?</li>
<li>Fees: what does the provider charge per year?</li></ul>""",
             "Questions about the AVD?", "Book a free call – we answer them for your situation."),
        final("Let's plan your pension – with the AVD",
              "In a free 30-minute call we calculate your state bonus, your pension gap and the best mix for your money.",
              ["We calculate your AVD bonus (with children)", "We look at your full pension: state, company, private", "You get a clear plan – no obligation"], qr)]
    # ---------------------------------------------------------------- PROTECT
    kw = "PROTECT"
    G[kw] = [
        cover(kw, "Protect your family: <span>life insurance</span> in Germany",
              "Term life insurance (in India: a \"term plan\") explained – who needs it, how much, what it costs, and the expat mistakes to avoid.",
              ["5 signs you need life insurance", "How much cover: table by salary", "What it really costs (Finanztest 12/2026)",
               "Home loan? Why you don't need the bank's policy", "Couples: the inheritance tax trap"]),
        page(kw, 2, """<h2><small>DO YOU NEED IT?</small>5 signs you need life insurance</h2>
<p class="lead">Term life insurance (Risikolebensversicherung) pays a fixed amount (sum assured) to your family if you die during the term. Tick how many apply to you:</p>
<ul class="check"><li>🏠 You have a home loan – your family would inherit it</li><li>👩‍👧 Your partner earns less or isn't working (yet)</li>
<li>👶 Your kids are growing up here – school, rent, daily life</li><li>🇮🇳 Your parents in India rely on the money you send</li><li>💼 Your salary pays most of the bills</li></ul>
<div class="tip">💡 Two or more ticks? Then your family depends on your income – and as an expat you often have no family safety net in Germany.</div>
<h3>How much cover? Rule of thumb: 3–5× gross yearly salary + open loans</h3>
<table><tr><th>Gross salary / year</th><th class="r">Cover (3×)</th><th class="r">Cover (5×)</th></tr>
<tr><td>€50,000</td><td class="r">€150,000</td><td class="r">€250,000</td></tr>
<tr class="hl"><td>€70,000</td><td class="r">€210,000</td><td class="r">€350,000</td></tr>
<tr><td>€100,000</td><td class="r">€300,000</td><td class="r">€500,000</td></tr></table>
<p class="note">Rule of thumb from Finanztest 12/2026 – plus your open loan amount. Your real need depends on savings, kids and your partner's income.</p>""",
             "How much cover do you need?", "We calculate your number and compare tariffs from many insurers – free."),
        page(kw, 3, """<h2><small>WHAT IT COSTS</small>Cheaper than most expats think</h2>
<p class="lead">Finanztest (issue 12/2026) compared term life insurance in Germany. For the same payout, expensive tariffs cost more than 3× as much as cheap ones.</p>
<div class="grid"><div class="card"><h4>Age 35, non-smoker</h4><div class="big">€456</div><p>per year (≈ €38/month) for €500,000 until 67 – cheapest tariff</p></div>
<div class="card"><h4>Same tariff at 45</h4><div class="big">€628</div><p>per year – about 38% more. Age and health when you sign decide the price.</p></div></div>
<p class="note">Finanztest 12/2026: model customer non-smoker, BMI 22, €500,000 sum assured until 67. Your price depends on age, health and job.</p>
<div class="trap"><b>⚠️ Home loan offer with life insurance attached?</b> You don't have to take the bank's policy. You can bring your own – often cheaper for the same cover.</div>
<div class="trap"><b>⚠️ Health questions:</b> answer them completely and honestly. Wrong answers can mean no payout when your family needs it.</div>
<div class="trap"><b>⚠️ "The loan dies with me":</b> it doesn't. A home loan is part of the estate – your family inherits it with the home.</div>""",
             "Paying too much already?", "Send us your current policy – we compare price and cover for you."),
        page(kw, 4, """<h2><small>COUPLES</small>The inheritance tax trap</h2>
<p class="lead">Who owns the policy matters. If you insure your own life and the payout goes to your partner, it can count as an inheritance.</p>
<div class="grid"><div class="card"><h4>💍 Married</h4><p>Spouses have a high tax-free allowance (€500,000). Usually no problem.</p></div>
<div class="card"><h4>❤️ Not married</h4><p>Unmarried partners only have €20,000 tax-free. A €300,000 payout can trigger a big tax bill.</p></div></div>
<div class="tip">💡 <b>The fix: "cross-over" policies (über Kreuz).</b> Each partner takes out the policy on the <i>other</i> partner's life and pays for it. Then the payout is your own money, not an inheritance.</div>
<p class="note">General information on §16 ErbStG, no tax advice.</p>
<h3>Your life insurance checklist</h3>
<ul class="check"><li>How many of the 5 signs apply to you?</li><li>Cover: 3–5× gross salary + open loans</li><li>Term: until your youngest child is independent / the loan is paid</li>
<li>Married or not? → who owns the policy</li><li>Existing policy from your bank? → compare</li><li>Also think about income protection: what if you can't work (BU)?</li></ul>""",
             "Let's protect your family the right way", "Free comparison of many insurers – in English, Hindi or German."),
        final("Let's find the right cover for your family",
              "In a free 30-minute call we calculate how much cover you need and compare tariffs from many insurers.",
              ["We calculate your cover: salary, loans, kids", "We compare prices from many insurers", "We set it up right – incl. cross-over for couples"], qr)]
    return G


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    qr = qr_data(); fcss = font_css()
    names = {"HOME": "Buying a home in Germany", "STRATEGY": "Your first rental property", "TAX": "Lower your tax with property",
             "PENSION": "Close your pension gap", "AVD": "The new pension depot 2027", "PROTECT": "Life insurance for your family"}
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        for kw, pages in guides(qr).items():
            html = f"<!doctype html><html><head><meta charset='utf-8'><title>arfinanz {kw} – {names[kw]}</title><style>{fcss}{CSS}</style></head><body>{''.join(pages)}</body></html>"
            open(os.path.join(out_dir, f"{kw}.html"), "w").write(html)
            pg.set_content(html, wait_until="networkidle")
            pdf = os.path.join(out_dir, f"arfinanz_{kw}_guide.pdf")
            pg.pdf(path=pdf, format="A4", print_background=True, prefer_css_page_size=True)
            print(pdf, len(pages))
        b.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "guides")
