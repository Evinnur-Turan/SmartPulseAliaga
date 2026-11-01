"""
Smart Pulse Aliağa — Port & Petrochemical Operations Center
---------------------------------------------
Executive Streamlit dashboard for heavy-industry port / refinery operations.
Runs standalone with synthetic data.

    pip install streamlit pandas numpy plotly
    streamlit run smart_pulse_Aliaga.py
"""

import inspect

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------------------- #
# Page config & theme constants
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Smart Pulse Aliağa",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAVY, BG, INK, BORDER = "#1E293B", "#F8FAFC", "#0F172A", "#E2E8F0"
SLATE, MUTED = "#475569", "#64748B"
GREEN, AMBER, RED = "#0F766E", "#B45309", "#B91C1C"
PALETTE = ["#1E293B", "#64748B", "#0F766E", "#B45309", "#94A3B8", "#7C8DA6"]

CSS = f"""
<style>
html, body, [data-testid="stAppViewContainer"], .stApp {{ background:{BG}; color:{INK}; }}
.block-container {{ padding-top:1.2rem; padding-bottom:3rem; max-width:1500px; }}
h1, h2, h3, h4 {{ color:{INK}; letter-spacing:-0.01em; }}
[data-testid="stSidebar"] {{ background:#EEF2F7; border-right:1px solid {BORDER}; }}
[data-testid="stMetric"] {{
    background:#FFFFFF; border:1px solid {BORDER}; border-radius:10px;
    padding:14px 18px; box-shadow:0 1px 2px rgba(15,23,42,.04);
}}
[data-testid="stMetricLabel"] p {{ color:{SLATE}; font-weight:600; font-size:.82rem; text-transform:uppercase; letter-spacing:.04em; }}
[data-testid="stMetricValue"] {{ color:{INK}; font-weight:700; }}
.hero {{
    background:{NAVY}; color:#F1F5F9; padding:20px 26px; border-radius:12px;
    display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;
}}
.hero h1 {{ color:#FFFFFF; font-size:1.55rem; margin:0; padding:0; }}
.hero p {{ color:#CBD5E1; margin:4px 0 0 0; font-size:.9rem; }}
.live {{ border:1px solid #475569; padding:4px 12px; border-radius:999px; font-size:.75rem; color:#CBD5E1; white-space:nowrap; }}
.section-label {{ font-size:.78rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:{MUTED}; margin:22px 0 6px 0; }}
.takeaway {{
    background:#FFFFFF; border:1px solid {BORDER}; border-left:4px solid {NAVY};
    border-radius:8px; padding:12px 16px; margin:8px 0 14px 0; font-size:.93rem; line-height:1.5;
}}
.takeaway b {{ color:{INK}; }}
.badge {{ display:inline-block; padding:2px 10px; border-radius:999px; font-size:.75rem; font-weight:600; margin-right:6px; border:1px solid; }}
.badge.crit {{ color:{RED}; background:#FBEAEA; border-color:#EBC4C4; }}
.badge.warn {{ color:{AMBER}; background:#FBF1E2; border-color:#EBD3A8; }}
.badge.ok   {{ color:{GREEN}; background:#E6F3F1; border-color:#B7DAD5; }}
.badge.info {{ color:{SLATE}; background:#EEF2F7; border-color:#CBD5E1; }}
.alert-card {{
    background:#FFFFFF; border:1px solid {BORDER}; border-radius:10px; padding:12px 14px;
    margin-bottom:10px; min-height:118px; font-size:.86rem; line-height:1.4;
}}
.alert-card.crit {{ border-left:4px solid {RED}; }}
.alert-card.warn {{ border-left:4px solid {AMBER}; }}
.alert-card .meta {{ color:{MUTED}; font-size:.75rem; margin-bottom:4px; }}
.alert-card .title {{ font-weight:700; color:{INK}; margin:4px 0; }}
.footer {{ color:{MUTED}; font-size:.78rem; margin-top:28px; border-top:1px solid {BORDER}; padding-top:10px; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Version-tolerant "stretch to container width" kwargs
_PLOT_KW = {"width": "stretch"} if "width" in inspect.signature(st.plotly_chart).parameters else {"use_container_width": True}
_DF_KW = {"width": "stretch"} if "width" in inspect.signature(st.dataframe).parameters else {"use_container_width": True}


def show_chart(fig):
    st.plotly_chart(fig, **_PLOT_KW)


def show_df(df, **kw):
    st.dataframe(df, hide_index=True, **_DF_KW, **kw)


def style_fig(fig, height=360, title=None):
    fig.update_layout(
        template="plotly_white", height=height, colorway=PALETTE,
        margin=dict(l=10, r=10, t=48 if title else 16, b=10),
        font=dict(family="Inter, Segoe UI, Helvetica, sans-serif", size=13, color=INK),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF",
        legend=dict(orientation="h", y=-0.22, x=0, title=None),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(gridcolor=BORDER, linecolor="#CBD5E1", zeroline=False, title=None)
    fig.update_yaxes(gridcolor=BORDER, linecolor="#CBD5E1", zeroline=False)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=15, color=INK), x=0))
    return fig


# --------------------------------------------------------------------------- #
# Plant configuration & synthetic data generators
# --------------------------------------------------------------------------- #
PLANTS = {
    # tph: nominal t/h | eff: nominal efficiency % | temp °C | press bar | co2f: kg CO2 per tonne
    "Crude Distillation": dict(tph=650, eff=91.0, temp=365, press=2.8, co2f=190),
    "Catalytic Cracker": dict(tph=260, eff=87.0, temp=520, press=2.2, co2f=320),
    "Petrochem Complex": dict(tph=180, eff=89.0, temp=285, press=18.0, co2f=410),
    "Port Terminal": dict(tph=800, eff=84.0, temp=42, press=11.0, co2f=14),
}
PROC_UNITS = ["Crude Distillation", "Catalytic Cracker", "Petrochem Complex"]

METRICS = {
    "Temperature (°C)": ("temp_c", "Process temperature. Running hot wears equipment faster and can trigger a safety trip."),
    "Pressure (bar)": ("press_bar", "Line or vessel pressure. Sustained high readings raise relief-valve and leak risk."),
    "CO₂ emissions (kg/h)": ("co2_kgh", "Carbon dioxide released per hour. Exceeding the cap counts against ESG compliance."),
}


@st.cache_data(show_spinner=False)
def generate_telemetry(days: int = 35, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = pd.Timestamp.now().floor("h")
    ts = pd.date_range(end=end, periods=days * 24, freq="h")
    n, hod = len(ts), ts.hour.values
    daily = np.sin((hod - 6) / 24 * 2 * np.pi)
    frames = []
    for plant, p in PLANTS.items():
        tph = p["tph"] * (1 + 0.03 * daily + rng.normal(0, 0.015, n))
        eff = np.clip(p["eff"] + 1.8 * daily + rng.normal(0, 0.8, n), 70, 99)
        temp = p["temp"] * (1 + rng.normal(0, 0.012, n))
        press = p["press"] * (1 + rng.normal(0, 0.015, n))
        co2 = tph * p["co2f"] * (1 + rng.normal(0, 0.01, n))
        for arr in (temp, press, co2):  # inject out-of-bounds spikes
            idx = rng.choice(n, size=10, replace=False)
            arr[idx] *= rng.uniform(1.07, 1.25, size=10)
        frames.append(pd.DataFrame(dict(
            timestamp=ts, plant=plant, tph=tph, eff=eff,
            temp_c=temp, press_bar=press, co2_kgh=co2)))
    return pd.concat(frames, ignore_index=True)


@st.cache_data(show_spinner=False)
def generate_vessels(seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    names = ["Aegean Star", "Nemrut Pioneer", "Izmir Spirit", "Foça Voyager", "Kızıldağ", "Candarlı Glory",
             "Ege Meridian", "Bergama Trader", "Mordoğan", "Sığacık Pearl", "Karaburun", "Urla Breeze",
             "Anatolian Dawn", "Gediz River", "Pergamon", "Helle Aspis", "Marmara Sun", "Levant Carrier",
             "Troy Navigator", "Bosphorus Light", "Eolian Crest", "Ionian Wave", "Dikili Express", "Kyme Princess"]
    n = len(names)
    now = pd.Timestamp.now().floor("h")
    return pd.DataFrame(dict(
        vessel=["MT " + x for x in names],
        arrival=now - pd.to_timedelta(rng.uniform(0, 21 * 24, n), unit="h"),
        berth=rng.choice([f"Berth {i}" for i in range(1, 7)], n),
        cargo=rng.choice(["Crude oil", "Naphtha", "Diesel", "LPG", "Petchem feedstock"], n),
        cargo_t=rng.integers(12000, 58000, n),
        pump_tph=rng.uniform(1100, 2400, n).round(0),
        laytime_h=rng.choice([36, 48, 60, 72], n),
        arrival_delay_h=np.clip(rng.gamma(1.6, 3.0, n), 0, 40).round(1),
    )).sort_values("arrival").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Business logic
# --------------------------------------------------------------------------- #
def limit_for(plant, col, tm, cm):
    p = PLANTS[plant]
    return {"temp_c": p["temp"] * (1 + tm), "press_bar": p["press"] * (1 + tm),
            "co2_kgh": p["tph"] * p["co2f"] * (1 + cm)}[col]


def demurrage_model(v, occ, speed, rate, berths):
    """Simplified queueing approximation: wait grows non-linearly as berth occupancy nears 100%."""
    if v.empty:
        return v.assign(service_h=[], wait_h=[], total_h=[], excess_h=[], cost_usd=[])
    rho = min(occ / 100, 0.97)
    service = v["cargo_t"] / (v["pump_tph"] * speed / 100)
    wait = service.mean() * rho / (1 - rho) * 0.5 / np.sqrt(berths)
    total = service + wait
    excess = (total - v["laytime_h"]).clip(lower=0)
    return v.assign(service_h=service, wait_h=wait, total_h=total, excess_h=excess, cost_usd=excess / 24 * rate)


def build_alerts(tel, ves, tm, cm, delay_thr):
    rows = []
    units = {"temp_c": ("Temperature", "°C"), "press_bar": ("Pressure", "bar"), "co2_kgh": ("Emission spike", "kg/h")}
    for plant in tel["plant"].unique():
        d = tel[tel["plant"] == plant]
        for col, (kind, unit) in units.items():
            lim = limit_for(plant, col, tm, cm)
            hit = d[d[col] > lim]
            if not hit.empty:
                rows.append(pd.DataFrame(dict(Time=hit["timestamp"], Asset=plant, Type=kind,
                                              Value=hit[col], Limit=lim, Unit=unit)))
    late = ves[ves["arrival_delay_h"] > delay_thr]
    if not late.empty:
        rows.append(pd.DataFrame(dict(Time=late["arrival"], Asset=late["vessel"], Type="Supply delay",
                                      Value=late["arrival_delay_h"], Limit=float(delay_thr), Unit="h")))
    cols = ["Time", "Asset", "Type", "Value", "Limit", "Unit", "Over limit %", "Severity", "Plain-language summary"]
    if not rows:
        return pd.DataFrame(columns=cols)
    a = pd.concat(rows, ignore_index=True)
    a["Over limit %"] = (a["Value"] / a["Limit"] - 1) * 100
    crit_at = np.where(a["Type"] == "Supply delay", 50, 12)
    a["Severity"] = np.where(a["Over limit %"] >= crit_at, "Critical", "Warning")

    def words(r):
        if r["Type"] == "Supply delay":
            return f"{r['Asset']} arrived {r['Value']:.0f} h late (alert after {r['Limit']:.0f} h), which can push berth schedules and laytime."
        what = {"Temperature": "temperature", "Pressure": "pressure", "Emission spike": "CO₂ output"}[r["Type"]]
        return f"{r['Asset']} {what} hit {r['Value']:,.0f} {r['Unit']}, {r['Over limit %']:.0f}% above its alert limit ({r['Limit']:,.0f})."

    a["Plain-language summary"] = a.apply(words, axis=1)
    return a.sort_values("Time", ascending=False).reset_index(drop=True)[cols]


def pct_change(a, b):
    return None if not b else (a - b) / b * 100


# --------------------------------------------------------------------------- #
# Sidebar: navigation filters
# --------------------------------------------------------------------------- #
tel_all, ves_all = generate_telemetry(), generate_vessels()
d_min, d_max = tel_all["timestamp"].min().date(), tel_all["timestamp"].max().date()

with st.sidebar:
    st.markdown("### 🏭 Filters")
    date_sel = st.date_input("Reporting window", value=(d_max - pd.Timedelta(days=13), d_max),
                             min_value=d_min, max_value=d_max,
                             help="Select a start and end date. The previous window of equal length is used for trend arrows.")
    plants_sel = st.multiselect("Plants / units", list(PLANTS), default=list(PLANTS))
    gran = st.radio("Summary granularity", ["Daily", "Weekly"], horizontal=True)

    st.divider()
    st.markdown("### 🚨 Alert thresholds")
    temp_margin = st.slider("Temp / pressure margin (%)", 2, 20, 8,
                            help="How far above a unit's normal operating level a reading can go before it is flagged.") / 100
    co2_margin = st.slider("CO₂ cap headroom (%)", 2, 20, 10,
                           help="Emission cap = nominal emissions + this headroom.") / 100
    delay_thr = st.slider("Supply delay alert (h)", 4, 24, 12,
                          help="Vessels arriving later than this are flagged as supply delays.")

    st.divider()
    st.markdown("### ⚓ Port & demurrage")
    berths = st.slider("Active berths", 3, 10, 6)
    occupancy = st.slider("Berth occupancy (%)", 40, 95, 78,
                          help="Share of time berths are busy. Higher occupancy means vessels queue longer.")
    speed = st.slider("Processing speed (% of rated)", 70, 130, 100,
                      help="Actual cargo pumping speed relative to the vessel's rated pump rate.")
    rate = st.number_input("Demurrage rate (USD/day)", 10000, 80000, 28000, step=1000)

if isinstance(date_sel, (tuple, list)) and len(date_sel) == 2:
    d0, d1 = date_sel
else:
    st.info("Select both a start and an end date in the sidebar to continue.")
    st.stop()
if not plants_sel:
    st.warning("Select at least one plant or unit in the sidebar.")
    st.stop()

t0, t1 = pd.Timestamp(d0), pd.Timestamp(d1) + pd.Timedelta(days=1)
pt0 = t0 - (t1 - t0)
sel_mask = tel_all["plant"].isin(plants_sel)
cur = tel_all[sel_mask & (tel_all["timestamp"] >= t0) & (tel_all["timestamp"] < t1)].copy()
prev = tel_all[sel_mask & (tel_all["timestamp"] >= pt0) & (tel_all["timestamp"] < t0)]
if cur.empty:
    st.warning("No telemetry in the selected window.")
    st.stop()

caps = {p: limit_for(p, "co2_kgh", temp_margin, co2_margin) for p in PLANTS}
cur["co2_cap"] = cur["plant"].map(caps)
cur["co2_pct_cap"] = cur["co2_kgh"] / cur["co2_cap"] * 100

ves = ves_all[(ves_all["arrival"] >= t0) & (ves_all["arrival"] < t1)]
ves_m = demurrage_model(ves, occupancy, speed, rate, berths)
alerts = build_alerts(cur, ves, temp_margin, co2_margin, delay_thr)
n_crit = int((alerts["Severity"] == "Critical").sum())

# --------------------------------------------------------------------------- #
# Header + executive KPI row
# --------------------------------------------------------------------------- #
st.markdown(
    f"""<div class="hero"><div><h1>Smart Pulse Aliağa</h1>
    <p>Executive view · {d0:%d %b %Y} – {d1:%d %b %Y} · {len(plants_sel)} of {len(PLANTS)} units in scope</p></div>
    <span class="live">● Synthetic demo data</span></div>""",
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Executive summary</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)

proc_c = cur.loc[cur["plant"].isin(PROC_UNITS), "tph"].sum()
proc_p = prev.loc[prev["plant"].isin(PROC_UNITS), "tph"].sum()
d_thr = pct_change(proc_c, proc_p)
k1.metric("Processed throughput", f"{proc_c / 1000:,.0f} kt",
          f"{d_thr:+.1f}% vs prior" if d_thr is not None else None,
          help="Total crude and feedstock processed by the selected refinery/petrochemical units (kilotonnes).")

eff_c, eff_p = cur["eff"].mean(), prev["eff"].mean() if len(prev) else None
k2.metric("Plant efficiency", f"{eff_c:.1f}%", f"{eff_c - eff_p:+.1f} pts" if eff_p else None,
          help="Average share of nominal output achieved. Higher means less wasted energy and feedstock.")

co2_c, co2_p = cur["co2_kgh"].sum() / 1000, prev["co2_kgh"].sum() / 1000
d_co2 = pct_change(co2_c, co2_p)
k3.metric("CO₂ emitted", f"{co2_c:,.0f} t", f"{d_co2:+.1f}% vs prior" if d_co2 is not None else None,
          delta_color="inverse", help="Total CO₂ released in the window. A falling trend is good, so down arrows show green.")

k4.metric("Active alerts", f"{len(alerts)}", f"{n_crit} critical", delta_color="off",
          help="Readings or deliveries outside normal bounds. Critical alerts exceed their limit by a wide margin.")

exposure = ves_m["cost_usd"].sum() if len(ves_m) else 0
k5.metric("Demurrage exposure", f"${exposure / 1000:,.0f}k",
          f"{int((ves_m['excess_h'] > 0).sum()) if len(ves_m) else 0} vessels over laytime", delta_color="off",
          help="Estimated penalty for vessels staying longer than agreed laytime, using the sidebar port assumptions.")

# --------------------------------------------------------------------------- #
# Analytical tabs
# --------------------------------------------------------------------------- #
st.markdown('<div class="section-label">Analysis</div>', unsafe_allow_html=True)
tab_ops, tab_esg, tab_dem, tab_sensor = st.tabs(
    ["📈 Operations", "🌿 Carbon & ESG", "⚓ Demurrage", "🔬 Sensor telemetry"])

# ---- Operations ----------------------------------------------------------- #
with tab_ops:
    freq = "D" if gran == "Daily" else "W"
    agg = (cur.groupby([pd.Grouper(key="timestamp", freq=freq), "plant"])
              .agg(throughput_t=("tph", "sum"), efficiency=("eff", "mean")).reset_index())

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(agg, x="timestamp", y="throughput_t", color="plant", barmode="stack",
                     labels={"throughput_t": "Tonnes", "plant": ""}, color_discrete_sequence=PALETTE)
        show_chart(style_fig(fig, title=f"{gran} throughput by unit (t)"))
    with c2:
        fig = px.line(agg, x="timestamp", y="efficiency", color="plant", markers=True,
                      labels={"efficiency": "Efficiency %", "plant": ""}, color_discrete_sequence=PALETTE)
        fig.update_yaxes(range=[max(60, agg["efficiency"].min() - 3), 100])
        show_chart(style_fig(fig, title=f"{gran} efficiency by unit (%)"))

    st.markdown("**Active plant efficiency**")
    cols = st.columns(len(plants_sel))
    for col, plant in zip(cols, plants_sel):
        e_c = cur.loc[cur["plant"] == plant, "eff"].mean()
        e_p = prev.loc[prev["plant"] == plant, "eff"].mean() if len(prev) else np.nan
        col.metric(plant, f"{e_c:.1f}%", f"{e_c - e_p:+.1f} pts" if not np.isnan(e_p) else None,
                   help=f"Average efficiency of {plant} in the selected window versus the prior window.")

    eff_by = cur.groupby("plant")["eff"].mean().sort_values()
    best, worst = eff_by.index[-1], eff_by.index[0]
    trend = (f"{d_thr:+.1f}% versus the prior window" if d_thr is not None else "with no prior window to compare")
    st.markdown(
        f'<div class="takeaway"><b>In plain words:</b> Processing units moved <b>{proc_c / 1000:,.0f} kt</b> ({trend}). '
        f'<b>{best}</b> is the most efficient unit at {eff_by.iloc[-1]:.1f}%'
        + (f', while <b>{worst}</b> trails at {eff_by.iloc[0]:.1f}% and is the first place to look for recoverable output.'
           if best != worst else '.') + '</div>', unsafe_allow_html=True)

    with st.expander("View summary table"):
        tbl = agg.pivot(index="timestamp", columns="plant", values="throughput_t").round(0)
        tbl.index = tbl.index.strftime("%d %b %Y")
        show_df(tbl.reset_index().rename(columns={"timestamp": "Period"}))

# ---- Carbon & ESG --------------------------------------------------------- #
with tab_esg:
    plant_hours = len(cur)
    exceed = int((cur["co2_pct_cap"] > 100).sum())
    comp = 100 - exceed / plant_hours * 100
    status, cls = (("Compliant", "ok") if comp >= 99 else ("Watch", "warn") if comp >= 97 else ("Non-compliant", "crit"))
    last24 = cur[cur["timestamp"] > cur["timestamp"].max() - pd.Timedelta(hours=24)]
    cap24 = sum(caps[p] for p in plants_sel) * 24
    util24 = last24["co2_kgh"].sum() / cap24 * 100

    e1, e2, e3 = st.columns([2.2, 1, 1])
    with e1:
        fig = px.line(cur, x="timestamp", y="co2_pct_cap", color="plant",
                      labels={"co2_pct_cap": "% of emission cap", "plant": ""}, color_discrete_sequence=PALETTE)
        fig.update_traces(line=dict(width=1.4))
        fig.add_hline(y=100, line=dict(color=RED, dash="dash", width=2),
                      annotation_text="Emission cap (100%)", annotation_position="top left",
                      annotation_font_color=RED)
        over = cur[cur["co2_pct_cap"] > 100]
        if not over.empty:
            fig.add_trace(go.Scatter(x=over["timestamp"], y=over["co2_pct_cap"], mode="markers",
                                     name="Over cap", marker=dict(color=RED, size=8, symbol="diamond"),
                                     hovertext=over["plant"]))
        show_chart(style_fig(fig, height=390, title="Hourly CO₂ vs cap, by unit"))
    with e2:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=util24, number={"suffix": "%", "font": {"color": INK}},
            title={"text": "Last 24 h vs cap", "font": {"size": 14}},
            gauge={"axis": {"range": [0, 120]}, "bar": {"color": NAVY},
                   "steps": [{"range": [0, 90], "color": "#E2E8F0"}, {"range": [90, 100], "color": "#F5E6C8"},
                             {"range": [100, 120], "color": "#EBC4C4"}],
                   "threshold": {"line": {"color": RED, "width": 3}, "value": 100}}))
        show_chart(style_fig(gauge, height=390))
    with e3:
        st.metric("Compliance status", status,
                  help="Share of unit-hours that stayed under the emission cap: ≥99% Compliant, 97–99% Watch, below 97% Non-compliant.")
        st.markdown(f'<span class="badge {cls}">{comp:.1f}% of hours within cap</span>', unsafe_allow_html=True)
        st.metric("Cap exceedances", f"{exceed}", help="Number of unit-hours above the emission cap.")
        intensity = cur["co2_kgh"].sum() / cur.loc[cur["plant"].isin(PROC_UNITS), "tph"].sum() if proc_c else np.nan
        st.metric("Carbon intensity", f"{intensity:,.0f} kg/t" if proc_c else "n/a",
                  help="CO₂ per tonne processed. Lower is better and comparable across periods.")

    daily = (cur.assign(day=cur["timestamp"].dt.floor("D")).groupby(["day", "plant"])["co2_kgh"].sum() / 1000).reset_index()
    fig = px.bar(daily, x="day", y="co2_kgh", color="plant", barmode="stack",
                 labels={"co2_kgh": "Tonnes CO₂", "plant": ""}, color_discrete_sequence=PALETTE)
    fig.add_trace(go.Scatter(x=sorted(daily["day"].unique()), y=[cap24 / 1000] * daily["day"].nunique(),
                             mode="lines", name="Daily cap", line=dict(color=RED, dash="dash", width=2)))
    show_chart(style_fig(fig, height=330, title="Daily CO₂ emissions vs combined cap (t)"))

    worst_p = cur.groupby("plant")["co2_pct_cap"].max().sort_values().index[-1]
    st.markdown(
        f'<div class="takeaway"><b>In plain words:</b> Emissions stayed within the cap for <b>{comp:.1f}%</b> of unit-hours '
        f'(<b>{status}</b>). The last 24 hours used <b>{util24:.0f}%</b> of the combined cap. '
        f'The highest single reading came from <b>{worst_p}</b> ({cur.loc[cur["plant"] == worst_p, "co2_pct_cap"].max():.0f}% of its cap).</div>',
        unsafe_allow_html=True)

# ---- Demurrage ------------------------------------------------------------ #
with tab_dem:
    if ves_m.empty:
        st.info("No vessel calls in the selected window.")
    else:
        n_over = int((ves_m["excess_h"] > 0).sum())
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Fleet exposure", f"${ves_m['cost_usd'].sum():,.0f}", help="Sum of estimated demurrage for all vessels in the window.")
        m2.metric("Vessels over laytime", f"{n_over} / {len(ves_m)}")
        m3.metric("Avg berth wait", f"{ves_m['wait_h'].iloc[0]:.1f} h", help="Estimated queue time before pumping starts, driven by occupancy and berth count.")
        m4.metric("Avg pumping time", f"{ves_m['service_h'].mean():.1f} h", help="Cargo tonnes divided by effective pump rate.")

        d1c, d2c = st.columns([1.3, 1])
        with d1c:
            top = ves_m.sort_values("cost_usd", ascending=False).head(12)
            fig = go.Figure(go.Bar(x=top["cost_usd"], y=top["vessel"], orientation="h",
                                   marker_color=[RED if c > 0 else "#94A3B8" for c in top["cost_usd"]],
                                   hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>"))
            fig.update_yaxes(autorange="reversed")
            show_chart(style_fig(fig, height=400, title="Estimated demurrage by vessel (USD)"))
        with d2c:
            sens = []
            for sp in (80, 100, 120):
                for occ in range(50, 96, 5):
                    sens.append(dict(Occupancy=occ, Speed=f"{sp}% speed",
                                     Cost=demurrage_model(ves, occ, sp, rate, berths)["cost_usd"].sum()))
            fig = px.line(pd.DataFrame(sens), x="Occupancy", y="Cost", color="Speed", markers=True,
                          color_discrete_sequence=[AMBER, NAVY, GREEN], labels={"Cost": "USD", "Occupancy": "Berth occupancy %"})
            fig.add_vline(x=occupancy, line=dict(color=MUTED, dash="dot"), annotation_text="Current")
            show_chart(style_fig(fig, height=400, title="Sensitivity: cost vs occupancy"))

        nxt = demurrage_model(ves, min(occupancy + 5, 97), speed, rate, berths)["cost_usd"].sum()
        st.markdown(
            f'<div class="takeaway"><b>In plain words:</b> At <b>{occupancy}%</b> berth occupancy, vessels wait about '
            f'<b>{ves_m["wait_h"].iloc[0]:.0f} h</b> before pumping starts. <b>{n_over} of {len(ves_m)}</b> calls exceed laytime, '
            f'a projected <b>${ves_m["cost_usd"].sum():,.0f}</b>. A further 5-point rise in occupancy would change that by roughly '
            f'<b>${nxt - ves_m["cost_usd"].sum():+,.0f}</b>; faster pumping is the quickest lever.</div>', unsafe_allow_html=True)

    st.markdown("**Single-vessel calculator**")
    q1, q2, q3, q4 = st.columns(4)
    cargo_in = q1.number_input("Cargo (t)", 1000, 150000, 35000, step=1000)
    pump_in = q2.number_input("Rated pump rate (t/h)", 300, 4000, 1800, step=100)
    lay_in = q3.number_input("Allowed laytime (h)", 12, 120, 48, step=6)
    rate_in = q4.number_input("Rate for this vessel (USD/day)", 10000, 80000, int(rate), step=1000)
    one = demurrage_model(pd.DataFrame(dict(cargo_t=[cargo_in], pump_tph=[pump_in], laytime_h=[lay_in])),
                          occupancy, speed, rate_in, berths)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Pumping time", f"{one['service_h'].iloc[0]:.1f} h")
    r2.metric("Expected berth wait", f"{one['wait_h'].iloc[0]:.1f} h")
    r3.metric("Hours over laytime", f"{one['excess_h'].iloc[0]:.1f} h")
    r4.metric("Estimated demurrage", f"${one['cost_usd'].iloc[0]:,.0f}")

    if not ves_m.empty:
        with st.expander("Vessel call details"):
            det = ves_m[["vessel", "berth", "cargo", "cargo_t", "arrival", "laytime_h", "service_h", "wait_h", "excess_h", "cost_usd"]].copy()
            det[["service_h", "wait_h", "excess_h", "cost_usd"]] = det[["service_h", "wait_h", "excess_h", "cost_usd"]].round(1)
            show_df(det.rename(columns={"cargo_t": "Cargo (t)", "laytime_h": "Laytime (h)", "service_h": "Pumping (h)",
                                        "wait_h": "Wait (h)", "excess_h": "Over laytime (h)", "cost_usd": "Cost (USD)"}))

# ---- Sensor telemetry ----------------------------------------------------- #
with tab_sensor:
    s1, s2 = st.columns([1, 1])
    s_plant = s1.selectbox("Unit", plants_sel)
    s_metric = s2.radio("Sensor", list(METRICS), horizontal=True)
    s_col, s_help = METRICS[s_metric]
    sd = cur[cur["plant"] == s_plant]
    lim = limit_for(s_plant, s_col, temp_margin, co2_margin)
    nominal = lim / (1 + (co2_margin if s_col == "co2_kgh" else temp_margin))
    hits = sd[sd[s_col] > lim]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sd["timestamp"], y=sd[s_col], mode="lines", name=s_metric, line=dict(color=NAVY, width=1.5)))
    fig.add_trace(go.Scatter(x=hits["timestamp"], y=hits[s_col], mode="markers", name="Out of bounds",
                             marker=dict(color=RED, size=8, symbol="diamond")))
    fig.add_hline(y=lim, line=dict(color=RED, dash="dash"), annotation_text="Alert limit", annotation_font_color=RED)
    fig.add_hline(y=nominal, line=dict(color=GREEN, dash="dot"), annotation_text="Normal level", annotation_font_color=GREEN)
    show_chart(style_fig(fig, height=380, title=f"{s_plant} · {s_metric}"))

    peak = sd[s_col].max()
    st.markdown(
        f'<div class="takeaway"><b>What this sensor means:</b> {s_help}<br>'
        f'<b>In plain words:</b> {s_plant} normally runs near <b>{nominal:,.1f}</b>. Over this window it crossed the alert limit of '
        f'<b>{lim:,.1f}</b> <b>{len(hits)}</b> time(s), peaking at <b>{peak:,.1f}</b> ({(peak / nominal - 1) * 100:+.0f}% vs normal). '
        + ("No action needed beyond routine monitoring." if len(hits) == 0 else "Review the red markers below for the exact times.") + "</div>",
        unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Alerts & drill-down
# --------------------------------------------------------------------------- #
st.markdown('<div class="section-label">Anomaly alerts &amp; drill-down</div>', unsafe_allow_html=True)

if alerts.empty:
    st.markdown('<span class="badge ok">All systems within bounds</span>', unsafe_allow_html=True)
else:
    counts = alerts["Type"].value_counts()
    badges = (f'<span class="badge crit">{n_crit} Critical</span>'
              f'<span class="badge warn">{len(alerts) - n_crit} Warning</span>'
              + "".join(f'<span class="badge info">{k}: {v}</span>' for k, v in counts.items()))
    st.markdown(badges, unsafe_allow_html=True)

    feed = alerts[alerts["Severity"] == "Critical"].head(4)
    if feed.empty:
        feed = alerts.head(4)
    cards = st.columns(len(feed))
    for col, (_, r) in zip(cards, feed.iterrows()):
        sev = "crit" if r["Severity"] == "Critical" else "warn"
        col.markdown(
            f'<div class="alert-card {sev}"><div class="meta">{r["Time"]:%d %b %H:%M} · {r["Type"]}</div>'
            f'<span class="badge {sev}">{r["Severity"]}</span>'
            f'<div class="title">{r["Asset"]}</div>{r["Plain-language summary"]}</div>', unsafe_allow_html=True)

    f1, f2 = st.columns([2, 1])
    types = f1.multiselect("Alert types", sorted(alerts["Type"].unique()), default=sorted(alerts["Type"].unique()))
    sevs = f2.multiselect("Severity", ["Critical", "Warning"], default=["Critical", "Warning"])
    view = alerts[alerts["Type"].isin(types) & alerts["Severity"].isin(sevs)].copy()
    view["Value"], view["Limit"], view["Over limit %"] = view["Value"].round(1), view["Limit"].round(1), view["Over limit %"].round(1)
    show_df(view, height=320)
    st.download_button("⬇ Export alerts (CSV)", view.to_csv(index=False).encode("utf-8"),
                       file_name="aliaga_alerts.csv", mime="text/csv")

st.markdown(
    f'<div class="footer">Smart Pulse Aliağa · synthetic data refreshed {pd.Timestamp.now():%d %b %Y %H:%M} · '
    'Demurrage uses a simplified queueing approximation for planning purposes only.</div>', unsafe_allow_html=True)
