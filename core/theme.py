"""Global stylesheet - Enterprise Dark theme + reusable design-system classes.

All base colours come from the Palette in core/config.py. This file also defines
shared component classes (badges, boot hardware/layer visualisation) so every
module renders with one consistent design language.
"""
import streamlit as st
from core.config import AppConfig

_P = AppConfig.PALETTE


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        #MainMenu, header, footer {{ visibility: hidden; }}

        .stApp {{
            background:
                radial-gradient(1100px 520px at 15% -8%, rgba(59,130,246,.10), transparent 60%),
                radial-gradient(900px 480px at 100% 0%, rgba(56,189,248,.06), transparent 55%),
                {_P.bg};
        }}
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
            color: {_P.text};
        }}
        .block-container {{
            padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1250px;
            animation: psFade .4s ease both;
        }}
        @keyframes psFade {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
        @keyframes psPulse {{
            0%,100% {{ box-shadow: 0 0 0 0 rgba(59,130,246,0); }}
            50% {{ box-shadow: 0 0 18px 2px rgba(59,130,246,.45); }}
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: {_P.radius}; border: 1px solid {_P.border};
            background: {_P.surface}; color: {_P.text};
            font-weight: 500; padding: .45rem .9rem; transition: all .18s ease;
        }}
        .stButton > button:hover {{
            border-color: {_P.accent}; color: #ffffff; transform: translateY(-1px);
            box-shadow: 0 0 0 1px rgba(59,130,246,.25), 0 6px 18px rgba(59,130,246,.15);
            background: #1c2534;
        }}
        .stButton > button[kind="primary"] {{
            background: linear-gradient(180deg, {_P.accent}, {_P.accent_hover});
            border: 1px solid {_P.accent}; color: #ffffff;
            box-shadow: 0 2px 12px rgba(59,130,246,.30);
        }}
        .stButton > button[kind="primary"]:hover {{
            box-shadow: 0 4px 20px rgba(59,130,246,.50); transform: translateY(-1px);
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {_P.surface}, #12161d);
            border-right: 1px solid {_P.border};
        }}
        section[data-testid="stSidebar"] .stButton > button {{ text-align: left; width: 100%; }}

        /* Cards */
        .ps-card {{
            background: linear-gradient(180deg, {_P.surface_alt}, #1b2432);
            border: 1px solid {_P.border}; border-radius: {_P.radius};
            box-shadow: {_P.shadow}; padding: 1.1rem 1.25rem; margin-bottom: 1rem;
            transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
        }}
        .ps-card:hover {{
            transform: translateY(-2px); border-color: #3a4a66;
            box-shadow: 0 2px 6px rgba(0,0,0,.5), 0 18px 44px rgba(0,0,0,.38);
        }}

        .ps-h1 {{ font-size: 1.55rem; font-weight: 700; margin: 0; letter-spacing: -.01em; color: {_P.text}; }}
        .ps-sub {{ color: {_P.text_muted}; font-size: .95rem; margin-top: .2rem; }}
        .ps-pill {{
            display:inline-block; padding:.15rem .6rem; border-radius:999px;
            font-size:.75rem; font-weight:600; background: rgba(59,130,246,.15);
            color:#8fb8fb; border:1px solid rgba(59,130,246,.25);
        }}
        .ps-kv {{ color:{_P.text_muted}; font-size:.82rem; text-transform:uppercase; letter-spacing:.05em; }}
        code {{
            background:#0e1420; color:#7dd3fc; padding:.12rem .4rem; border-radius:6px;
            border:1px solid {_P.border}; font-family:'JetBrains Mono', ui-monospace, monospace; font-size:.85em;
        }}

        /* Status badges (design system) */
        .ps-badge {{
            display:inline-flex; align-items:center; gap:.3rem; padding:.15rem .55rem;
            border-radius:999px; font-size:.72rem; font-weight:600; border:1px solid transparent;
        }}
        .ps-badge.success  {{ background:rgba(34,197,94,.14);  color:#4ade80; border-color:rgba(34,197,94,.30); }}
        .ps-badge.warning  {{ background:rgba(245,158,11,.14); color:#fbbf24; border-color:rgba(245,158,11,.30); }}
        .ps-badge.critical {{ background:rgba(239,68,68,.14);  color:#f87171; border-color:rgba(239,68,68,.30); }}
        .ps-badge.info     {{ background:rgba(56,189,248,.14); color:#7dd3fc; border-color:rgba(56,189,248,.30); }}
        .ps-badge.neutral  {{ background:rgba(148,163,184,.14);color:#cbd5e1; border-color:rgba(148,163,184,.30); }}

        /* Boot Simulator - hardware grid */
        .ps-hwgrid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:.5rem; }}
        .ps-hw {{
            background:#0e1420; border:1px solid {_P.border}; border-radius:10px;
            padding:.55rem .4rem; text-align:center; color:{_P.text_muted};
            font-size:.72rem; transition:all .25s ease;
        }}
        .ps-hw .ic {{ font-size:1.15rem; display:block; margin-bottom:.15rem; color:{_P.text_muted}; }}
        .ps-hw.active {{
            border-color:{_P.accent}; color:{_P.text}; background:#12203a;
            animation:psPulse 1.2s ease-in-out infinite;
        }}
        .ps-hw.active .ic {{ color:{_P.info}; }}

        /* Boot Simulator - OS layer stack */
        .ps-layer {{
            display:flex; align-items:center; gap:.55rem; padding:.4rem .65rem; margin:.22rem 0;
            border-radius:8px; border:1px solid #232c3d; background:#0e1420;
            color:#5b6572; font-size:.82rem; transition:all .25s ease;
        }}
        .ps-layer .dot {{ width:8px; height:8px; border-radius:50%; background:#39435a; flex:none; }}
        .ps-layer.on {{ color:{_P.text}; border-color:{_P.border}; background:#141c2b; }}
        .ps-layer.on .dot {{ background:{_P.success}; }}
        .ps-layer.cur {{ border-color:{_P.accent}; background:#12203a; animation:psPulse 1.2s ease-in-out infinite; }}
        .ps-layer.cur .dot {{ background:{_P.accent}; }}

        /* Inputs */
        .stTextInput label, .stSelectbox label {{ color:{_P.text_muted} !important; font-size:.82rem; }}
        .stTextInput input, .stTextInput > div > div > input {{
            background:{_P.surface} !important; color:{_P.text} !important;
            border:1px solid {_P.border} !important; border-radius:{_P.radius} !important;
        }}
        .stTextInput input:focus {{ border-color:{_P.accent} !important; box-shadow:0 0 0 2px rgba(59,130,246,.25) !important; }}
        div[data-baseweb="select"] > div {{
            background:{_P.surface} !important; border-color:{_P.border} !important; border-radius:{_P.radius} !important;
        }}

        /* Progress bar */
        .stProgress > div > div > div > div {{ background: linear-gradient(90deg, {_P.accent}, {_P.info}) !important; }}

        /* Alerts */
        [data-testid="stAlert"] {{
            background:{_P.surface_alt}; border:1px solid {_P.border};
            border-radius:{_P.radius}; color:{_P.text};
        }}

        [data-testid="stGraphVizChart"] {{ background:transparent; }}

        ::-webkit-scrollbar {{ width:10px; height:10px; }}
        ::-webkit-scrollbar-thumb {{ background:{_P.border}; border-radius:8px; }}
        ::-webkit-scrollbar-thumb:hover {{ background:#3a4a66; }}
        ::-webkit-scrollbar-track {{ background:transparent; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
