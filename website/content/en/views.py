import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"
LANG = json.loads(Path(__file__).with_name("pages.json").read_text(encoding="utf-8"))
NAV = LANG["nav"]
CASES = {"double_post": "Duplicate refund", "complete": "Approved refund", "missing_readback": "Missing readback"}
LABEL = "Illustrative synthetic scenario — not a real customer deployment."
ICON = {
    "arrow": "M4 12h15m-6-6 6 6-6 6", "down": "M12 4v15m-6-6 6 6 6-6",
    "layers": "m3 8 9-5 9 5-9 5-9-5Zm0 5 9 5 9-5m-18 5 9 5 9-5",
    "records": "M5 4h14v16H5zM8 8h8m-8 4h8m-8 4h5",
    "branch": "M6 5v14m0-7h7a4 4 0 0 0 4-4V5m-2 2 2-2 2 2",
    "check": "m4 12 5 5L20 6", "target": "M4 10V4h6m4 0h6v6m0 4v6h-6m-4 0H4v-6m5-2 2 2 4-4",
    "repeat": "M20 8a8 8 0 0 0-14-2L3 9m0-5v5h5m-4 7a8 8 0 0 0 14 2l3-3m0 5v-5h-5",
    "signal": "M3 15h4l3-9 4 13 3-8h4", "out": "M6 18 18 6M6 6h12v12",
    "code": "m8 7-5 5 5 5m8-10 5 5-5 5M14 4l-4 16",
}
def icon(key):
    return f'<svg aria-hidden="true" class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="{ICON[key]}"/></svg>'

def url(page):
    return page + ".html"

def button(label, dest, secondary=False):
    return f'<a class="button {"secondary" if secondary else "primary"}" href="{dest}">{label}{icon("down" if dest.startswith("#") else "arrow")}</a>'

def brand():
    return '<span class="brand"><img width="32" height="32" alt="" src="assets/brand.svg">VerityOps</span>'

def header(active):
    titles = {"testing":"Testing", "research":"Research"}
    items = "".join(f'<a href="{url(k)}" {"aria-current=page" if k==active else ""}>{titles.get(k,v)}</a>' for k,v in NAV.items() if k not in ("contact","index"))
    return f"""<a class="skip" href="#main">Skip to content</a><header class="mast"><div class="wrap nav-wrap">
    <a href="index.html" aria-label="VerityOps home">{brand()}</a>
    <button class="menu-btn" aria-expanded="false" aria-controls="navigation" type="button">Menu <span aria-hidden="true">☰</span></button>
    <nav id="navigation" aria-label="Main navigation">{items}<a class="contact-nav" href="contact.html" {"aria-current=page" if active=="contact" else ""}>Contact {icon("arrow")}</a></nav></div></header>"""

def footer():
    links = "".join(f'<a href="{url(k)}">{v}</a>' for k,v in NAV.items() if k!="index")
    return f'<footer><div class="wrap foot"><div><a href="index.html">{brand()}</a><p>Independent business outcome verification<br>and regression testing for AI agents.</p></div><nav aria-label="Footer">{links}</nav></div></footer>'

def tag(t):
    return f'<p class="eyebrow"><span class="tagline-mark"></span>{t}</p>'

def section_head(label, title, intro=""):
    return f'<div class="section-head">{tag(label)}<h2>{title}</h2>{f"<p>{intro}</p>" if intro else ""}</div>'

def intro(k,title,body,side=""):
    return f'<section class="page-intro dark"><div class="wrap intro-grid"><div>{tag(NAV[k])}<h1>{title}</h1><p class="lead">{body}</p></div>{side}</div></section>'

def cards(items):
    return '<div class="cards">' + "".join(f'<article><div class="card-icon">{icon(i)}</div><h3>{title}</h3><p>{desc}</p></article>' for i,title,desc in items) + '</div>'

def stack():
    return '<figure class="stack"><figcaption><span class="corner"></span>System architecture</figcaption><img width="550" height="365" src="assets/stack.svg" alt="Agent execution, independent readback and an evidence report, shown as three separate layers."><div class="stack-key"><i></i>Read-only verification path</div></figure>'

def verdicts():
    return '<div class="verdict-grid">' + ''.join(f'<article><span class="pill {v.lower()}"><i></i>{v}</span><h3>{title}</h3><p>{desc}</p></article>' for v,title,desc in [
        ("PASS","The contract holds.","The required records are complete and the observed business state satisfies every agreed rule."),
        ("FAIL","A rule was violated.","The observed records establish a concrete violation, such as two refunds against the same order."),
        ("INCONCLUSIVE","Evidence is insufficient.","A required source or ownership field is unavailable. The reviewer cannot establish a reliable outcome.")]) + '</div>'

def dashboard():
    panels=[]
    for key,name in CASES.items():
        ev=json.loads((EVIDENCE/(key+".json")).read_text(encoding="utf-8"))
        d=ev["decision"]; v=d["verdict"]; after=ev["after"]; rows=after.get("ledger")
        amount=d["contract"]["amount_cents"]
        title={"FAIL":"Two refunds posted for one order.","PASS":"One approved refund posted.","INCONCLUSIVE":"The refund ledger could not be read."}[v]
        exp={"FAIL":"The agent reported completion. The ledger contains two postings for the target order.",
             "PASS":"The ledger contains one posting for the approved amount. The order and ticket reached their expected states.",
             "INCONCLUSIVE":"The agent reported completion. The fixture withheld the readback needed to establish the outcome."}[v]
        info=[("Target order",d["contract"]["order"]),("Expected amount",f"{amount:,} minor units"),("Observed entries","Unavailable" if rows is None else str(len(rows))),("Order status",after.get("order",{}).get("status","Unavailable"))]
        cells="".join(f'<div><dt>{escape(k)}</dt><dd>{escape(x)}</dd></div>' for k,x in info)
        lines="".join(f'<tr><td>#{r["id"]}</td><td>{escape(r["order_id"])}</td><td>{r["amount"]:,}</td></tr>' for r in (rows or []))
        table=(f'<table><caption>Refund ledger · minor units</caption><thead><tr><th>Entry</th><th>Order</th><th>Amount</th></tr></thead><tbody>{lines}</tbody></table>' if rows is not None else '<p class="missing">No ledger rows are available for inspection.</p>')
        panels.append(f'<article class="run-panel" id="run-{key}"><div class="run-head"><span class="mono">REFUND / {escape(key.upper())}</span><span class="pill {v.lower()}"><i></i>{v}</span></div><h3>{title}</h3><p>{exp}</p><dl class="stats">{cells}</dl><details><summary>Inspect ledger evidence</summary>{table}<a class="inline-link" href="evidence/{key}.json">Open source JSON {icon("out")}</a></details></article>')
    links="".join(f'<a class="run-choice" href="#run-{k}" data-run="{k}">{icon("records")}{v}<span aria-hidden="true">›</span></a>' for k,v in CASES.items())
    return f'<div class="console" data-console><div class="console-bar"><strong>{icon("signal")} Verification console</strong><span class="sample">Synthetic sandbox</span></div><div class="console-body"><div class="run-picker"><p class="mono">SELECT A RUN</p>{links}</div><div class="panels">{"".join(panels)}</div></div></div>'

def home():
    return f"""<section class="hero dark"><div class="wrap hero-grid"><div class="hero-copy">{tag("Agent release assurance")}
    <h1>Trust the outcome.<br><em>Verify the execution.</em></h1><p class="lead">Independent business outcome verification and regression testing for AI agents. Check what actually changed in the system of record.</p>
    <div class="actions">{button("Explore the platform","platform.html")}{button("View synthetic demo","#demo",True)}</div></div>{stack()}</div>
    <div class="wrap chain"><span>{icon("branch")}Agent action</span><b>→</b><span>{icon("records")}Independent readback</span><b>→</b><span>{icon("target")}Evidence verdict</span><b>→</b><span>{icon("repeat")}Regression replay</span></div></section>
    <section id="demo" class="wrap section">{section_head("Synthetic demonstration","What did the agent actually do?","The same completion message can accompany a correct refund, a duplicate posting or missing evidence. Inspect the saved records behind each outcome.")}{dashboard()}<p class="replay-note">{icon("repeat")}<span>Save a failing case and replay it on the next candidate to catch the same error before release. <a href="evidence/duplicate-replay.json">Inspect the replay input</a></span></p></section>
    <section class="tint"><div class="wrap section">{section_head("Release decisions","Three verdicts. An explicit standard of proof.")}{verdicts()}</div></section>
    <section class="wrap feature-end"><div>{tag("Applied research")}<h2>Refund verification at enterprise scale</h2><p>Explore two fictional commerce operations and the assumptions behind their simulations.</p></div>{button("Read the case studies","use-cases.html#case-studies")}</section>"""

def platform():
    return intro("platform","A separate view of the business outcome.","VerityOps checks an agreed release contract against records held by the business system. A successful tool response is only one piece of context.",stack())+f'<section class="wrap section">{section_head("Architecture","From business contract to evidence")}{cards([("branch","Execution boundary","A deterministic fixture acts on a synthetic order. The verifier does not issue refunds or change the ledger."),("records","Independent observation","A separate read-only SQLite connection reads the order, its ticket and the refund ledger in one transaction."),("target","Business rules","The verifier checks ownership, amount, eligibility at posting and completeness before assigning a verdict.")])}</section><section class="tint"><div class="wrap section">{section_head("Outputs","An inspectable release decision")}{verdicts()}<div class="actions">{button("See the verification workflow","how-it-works.html")}</div></div></section>'

def process():
    steps=[
        ("Agree the contract","Identify the order, expected amount, refund or hold decision, and required order and ticket states."),
        ("Run the candidate","Start with an isolated order. Record the action and its response, including a retry when the scenario calls for one."),
        ("Read the resources","Query the authoritative sandbox records through a separate read-only connection. Keep the observed ledger rows and their order references."),
        ("Decide and replay","Evaluate the contract. Preserve the evidence and replay a reproducible failure against the candidate and the reference fixture.")]
    rows="".join(f'<li><span class="step-num">{n:02d}</span><div><h3>{t}</h3><p>{x}</p></div></li>' for n,(t,x) in enumerate(steps,1))
    return intro("how-it-works","Follow a refund through verification.","A release reviewer starts with the intended business effect and ends with the evidence needed to sign off, reject the release or request a better readback.")+f'<section class="wrap section spread"><div>{section_head("Method","One workflow, end to end.")}<a href="testing.html" class="inline-link">Inspect a saved run {icon("arrow")}</a></div><ol class="steps">{rows}</ol></section>'

def testing():
    rules=[("Order identity","Locate exactly one target order and its linked service ticket."),
           ("Refund ownership","Use the order reference on each ledger posting. A matching request key alone cannot establish ownership."),
           ("Refund amount","Compare each target posting with the contract amount in integer minor units."),
           ("Duplicate refunds","Count all target-order postings, including records with different request keys."),
           ("Eligibility at posting","Inspect approval, permission and the deadline recorded at the time of the effect."),
           ("Record completeness","Check row counts and ownership information before drawing a verdict. An unavailable resource cannot establish PASS."),
           ("Evidence report","Preserve the before and after snapshots, agent responses, contract, issues and verdict."),
           ("Regression replay","Recreate the isolated fixture and run the saved case against candidate and reference versions.")]
    tr="".join(f'<tr><th scope="row">{t}</th><td>{x}</td></tr>' for t,x in rules)
    return intro("testing","Inspect the evidence behind a verdict.","Explore saved synthetic runs, then review the checks used by the local single-order refund verifier.")+f'<section class="wrap section">{dashboard()}</section><section class="tint"><div class="wrap section">{section_head("Release contract","What the verifier checks")}<table class="rules"><thead><tr><th>Check</th><th>Evidence requirement</th></tr></thead><tbody>{tr}</tbody></table></div></section>'


def case_card(market):
    data = json.loads((EVIDENCE / f"task-c-{market}.json").read_text(encoding="utf-8"))
    counts = data["counts"]
    name = {"US":"Juniper Mile Outfitters","CN":"Qingqi Home"}[market]
    if name not in data["company"] or data["market"] != market:
        raise ValueError("Case-study identity differs from the source")
    scope = {"US":"Cancellations, returns and price adjustments across a web store, marketplace and outlet app.",
             "CN":"Returns, refund-only requests and price protection across a flagship mall, livestream commerce and mini-store."}[market]
    source = f'evidence/task-c-{market}.json'
    report = Path(__file__).with_name(f"task-c-{market}.md").read_text(encoding="utf-8")
    paragraphs = [part for part in report.strip().split("\n\n") if not part.startswith(("#", "[", "**SYNTHETIC SIMULATION"))]
    narrative = "".join("<p>" + re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", escape(part)) + "</p>" for part in paragraphs)
    matrix = data["confusion"]["candidate"]
    defect_total = sum(matrix["verified"]["defective"].values())
    if sum(matrix["baseline"]["defective"].values()) != defect_total:
        raise ValueError("Cannot compare cohorts with different denominators")
    compare = "".join(f'<tr><th scope="row">{title}</th>' + "".join(f'<td>{matrix[method]["defective"][v]:,}</td>' for v in ("PASS","FAIL","INCONCLUSIVE")) + '</tr>' for method,title in (("baseline","ACK only"),("verified","Readback")))
    ex = next(e["case"] for e in data["examples"] if e["case"]["ownership_wrong"] and e["case"]["expected_cash"]==e["case"]["posted_cash"])
    return f"""<article class="case-card"><p class="eyebrow">{'United States' if market=='US' else 'China'} · Refund operations</p><h3>{name}</h3>
    <p class="disclosure">{LABEL}</p><p>{scope}</p><dl class="case-metric"><div><dt>Synthetic orders</dt><dd>{counts['orders']:,}</dd></div><div><dt>Refund tickets</dt><dd>{counts['tickets']:,}</dd></div></dl>
    <p>Of {defect_total:,} defective candidate tickets, independent readback flagged {matrix['verified']['defective']['FAIL']:,} and left {matrix['verified']['defective']['INCONCLUSIVE']:,} inconclusive.</p>
    <details><summary>Compare both methods</summary><table><caption>Defective candidate tickets only</caption><thead><tr><th>Method</th><th>PASS</th><th>FAIL</th><th>INC.</th></tr></thead><tbody>{compare}</tbody></table>
    <p>Both methods observe the same synthetic events. PASS here means a missed defect. The denominator excludes correct tickets.</p>
    <p>Ticket {ex['ticket']} had matching expected and posted totals, but the payment ownership was wrong. The acknowledgement method returned {escape(ex['baseline'])}; the readback returned {escape(ex['verified'])}.</p></details>
    <details class="narrative"><summary>Read the executive case study</summary>{narrative}</details>
    <a class="inline-link" href="{source}">Inspect case data {icon('out')}</a></article>"""

def use_cases():
    return intro("use-cases","Refund release acceptance.","The first use case is a single e-commerce refund workflow. The release question is whether the right order received the right amount exactly once.")+f"""<section class="wrap section" id="case-studies">{section_head("Enterprise case studies","Two markets. The same verification question.","These production-scale simulations compare tool acknowledgements with independent readback on identical events. Counts describe generated records and injected faults.")}
    <div class="case-grid">{case_card("US")}{case_card("CN")}</div></section><section class="tint"><div class="wrap section">{section_head("Interpretation","What the simulations establish")}{cards([
    ("records","Independent readback","Read the payment allocation, order state and ticket status. Totals can match even when money is assigned to the wrong original payment."),
    ("target","Missing evidence","A late watermark, incomplete ledger page or missing state can leave an injected defect inconclusive. It still needs review."),
    ("repeat","Limits of inference","Fault prevalence and source completeness are simulation inputs. These studies do not measure real merchant losses, savings or deployment performance.")])}</div></section>"""

def research():
    resources=[("evidence/complete.json","Approved refund evidence","Before and after snapshots, replies and the release verdict."),
        ("evidence/double_post.json","Duplicate refund evidence","Two postings associated with the same target order."),
        ("evidence/missing_readback.json","Missing readback evidence","The fixture withheld the resource snapshot."),
        ("evidence/duplicate-replay.json","Regression replay specification","Input for the frozen single-refund replay runner."),
        ("evidence/task-c-US.json","US synthetic case data","Counts, candidate and reference comparisons, fault examples and modelling assumptions."),
        ("evidence/task-c-CN.json","China synthetic case data","Counts, candidate and reference comparisons, fault examples and modelling assumptions."),
        ("evidence/provenance.json","Source manifest","Dataset locations and SHA-256 fingerprints for the packaged evidence.")]
    listing=''.join(f'<li><a class="inline-link" href="{link}">{title} {icon("out")}</a><small>{desc}</small></li>' for link,title,desc in resources)
    return intro("research","Methods you can inspect.","Trace a release verdict back to its input contract and observed resource state. The public materials on this site are deterministic, synthetic research artifacts.")+f'<section class="wrap section spread"><div>{section_head("Evidence library","Inspect the source records")}<p>Amounts in the small refund fixture use integer minor units. Each enterprise study declares its own currency and assumptions.</p></div><ul class="resources">{listing}</ul></section><section class="tint"><div class="wrap section">{section_head("Engineering practice","Reproduce the decision")}{cards([("code","Local execution","The frozen Python runner re-creates a synthetic SQLite environment. It requires no external model call."),("repeat","Candidate and reference","Replay a saved stimulus on fresh state for each version. Compare the resulting verdict, issues and observed records."),("records","Scope of the evidence","All source systems here are fixtures from one project. Validation against an independently operated business system remains open.")])}</div></section>'

def about():
    return intro("about","Verification for consequential actions.","VerityOps is an engineering project studying whether an independent observer can establish what an AI agent actually did to a business system.")+f'<section class="wrap section spread"><div>{section_head("Our approach","Start with the record.")}</div><div><h3>A narrow, testable commitment</h3><p>For an e-commerce team releasing a refund agent, a convincing answer in a support ticket leaves an essential question open. Which order received the refund, and how many times was it posted? VerityOps makes that question a reproducible release check.</p><p>Enterprise AI teams, implementation partners and engineering reviewers can inspect the contract and evidence together. Fintech teams can evaluate the method through the sandbox materials. All demonstrations here use fictional transactions.</p><a class="inline-link" href="research.html">Explore research and engineering {icon("arrow")}</a></div></section>'

def contact():
    return intro("contact","Discuss a refund release.","The proposed engagement covers one refund agent, one workflow and one isolated sandbox, with independent read-only business records and one candidate-version retest.")+f'<section class="wrap section spread"><div>{section_head("Contact availability","Business contact pending verification.")}<p>A verified business contact channel has not been published. This static page does not collect inquiries or personal data.</p><a class="inline-link" href="testing.html">Inspect the sample evidence {icon("arrow")}</a></div><aside class="contact-box"><h3>Pilot scope</h3><ul><li>A named release owner and an agreed refund contract</li><li>Authorized readback of order, payment and ticket state</li><li>A PASS, FAIL or INCONCLUSIVE evidence report</li><li>Executable regression tests and one candidate-version retest</li></ul><p><strong>United States</strong> · US$1,500 per workflow<br><strong>China</strong> · ¥6,000 per workflow</p></aside></section>'

PAGES = {"index":home,"platform":platform,"how-it-works":process,"use-cases":use_cases,"testing":testing,"research":research,"about":about,"contact":contact}

