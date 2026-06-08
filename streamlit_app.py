"""
PondIQ Streamlit App — Responsive feeding advisor for fish farmers.
Matches Figma prototype: blue #1a5fa8 palette, sliders, inline results.

Run:
    streamlit run streamlit_app.py

Requires the PondIQ FastAPI server running at http://localhost:8000
    cd PondIQ-main && uv run pondiq_api.py
"""

from __future__ import annotations

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import sys
import os
import subprocess
import base64
from pathlib import Path

# ── Page config (must be first Streamlit call) ──────────────────────
st.set_page_config(
    page_title="AQUASENSE AI — Fish Feeding Advisor",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Image helpers ────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).parent / "assets"


def _img_to_b64(path: Path) -> str:
    """Read an image file and return a base64 data URI."""
    if not path.exists():
        return ""
    ext = path.suffix.lower().replace(".", "")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    with open(path, "rb") as f:
        return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"


HERO_B64 = _img_to_b64(ASSETS_DIR / "hero.jpg")
HOW_IT_B64 = _img_to_b64(ASSETS_DIR / "how-it-works.jpg")

# ── Responsive CSS ───────────────────────────────────────────────────


def inject_css() -> None:
    st.markdown(
        """
        <style>
        /* ── Fonts ──────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 16px;
            line-height: 1.7;
            color: #1a1a2e;
            -webkit-font-smoothing: antialiased;
        }

        h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2 {
            font-family: 'Playfair Display', Georgia, serif !important;
            font-weight: 700;
            color: #0f1923;
            letter-spacing: -0.3px;
        }

        h1 { font-size: 32px !important; }
        h2 { font-size: 24px !important; }
        h3 { font-size: 20px !important; }

        p, li, span, div {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* ── Global ──────────────────────────────────────── */
        .stApp {
            background: #f0f4f8;
        }

        .block-container {
            max-width: 1100px !important;
            margin: 0 auto !important;
            padding: 0 2rem 0 !important;
            background: transparent;
            min-height: 100vh;
        }

        .app-inner {
            padding: 0;
            max-width: 100%;
        }

        /* ── Header bars ─────────────────────────────────── */
        .pondiq-header {
            background: linear-gradient(135deg, #1a5fa8 0%, #134b87 100%);
            padding: 24px 32px 28px;
            box-shadow: 0 4px 24px rgba(26,95,168,0.18);
            margin: 0;
        }
        .pondiq-header .header-row {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .pondiq-header h2 {
            color: #ffffff !important;
            font-family: 'Playfair Display', Georgia, serif !important;
            margin: 0;
            font-size: 22px !important;
            font-weight: 700;
            letter-spacing: -0.2px;
        }
        .pondiq-header .subtitle {
            color: rgba(255,255,255,0.7);
            font-size: 13px;
            font-weight: 400;
            margin: 4px 0 0;
        }
        .pondiq-header .progress-bar {
            background: rgba(255,255,255,0.15);
            border-radius: 3px;
            height: 3px;
            margin-top: 16px;
        }
        .pondiq-header .progress-bar-fill {
            background: rgba(255,255,255,0.5);
            border-radius: 3px;
            height: 3px;
            width: 100%;
        }

        /* ── Cards ───────────────────────────────────────── */
        .pondiq-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
            margin-bottom: 16px;
            transition: box-shadow 0.2s ease;
        }

        /* ── Section labels ──────────────────────────────── */
        .section-label {
            font-size: 12px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin: 0 0 8px;
        }

        /* ── Decision banners ────────────────────────────── */
        .decision-banner {
            border-radius: 0;
            padding: 28px 2rem 36px;
            position: relative;
            overflow: hidden;
            color: #ffffff;
            margin: 0 -2rem 28px;
        }
        .decision-banner.feed-now   { background: linear-gradient(135deg, #0d8040 0%, #0a6b35 100%); }
        .decision-banner.reduce     { background: linear-gradient(135deg, #c25a0a 0%, #a34b08 100%); }
        .decision-banner.stop       { background: linear-gradient(135deg, #c1292e 0%, #a12226 100%); }

        .decision-banner .deco-circle {
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.06);
        }
        .decision-banner .deco-1 { top: -30px; right: -30px; width: 120px; height: 120px; }
        .decision-banner .deco-2 { bottom: -40px; left: -20px; width: 100px; height: 100px; }

        .decision-banner .banner-content {
            display: flex;
            align-items: center;
            gap: 16px;
            position: relative;
            z-index: 1;
        }
        .decision-banner .icon-circle {
            background: rgba(255,255,255,0.15);
            border-radius: 50%;
            width: 56px;
            height: 56px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 28px;
        }
        .decision-banner .label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            opacity: 0.65;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .decision-banner .title {
            font-family: 'Playfair Display', Georgia, serif !important;
            font-size: 30px !important;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        /* ── Parameter cards ─────────────────────────────── */
        .param-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(0,0,0,0.06);
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            margin-bottom: 0;
            transition: border-color 0.2s ease;
        }
        .param-card:hover {
            border-color: rgba(26,95,168,0.2);
        }

        /* ── Tip row ─────────────────────────────────────── */
        .tip-row {
            display: flex;
            gap: 12px;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        .tip-number {
            width: 26px; height: 26px;
            min-width: 26px;
            border-radius: 50%;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
        }

        /* ── History entry ────────────────────────────────── */
        .history-entry {
            display: flex;
            align-items: center;
            gap: 14px;
            background: #ffffff;
            border-radius: 10px;
            padding: 16px 18px;
            border: 1px solid rgba(0,0,0,0.05);
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            margin-bottom: 8px;
            transition: box-shadow 0.15s ease;
        }
        .history-entry:hover {
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .history-icon {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            font-size: 22px;
        }
        .history-body {
            flex: 1;
            min-width: 0;
        }
        .history-decision {
            margin: 0;
            font-weight: 700;
            color: #0f2340;
            font-size: 14px;
        }
        .history-date {
            margin: 2px 0 0;
            color: #4a6b8a;
            font-size: 12px;
        }
        .history-right {
            text-align: right;
            flex-shrink: 0;
        }
        .history-do {
            margin: 0;
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 700;
            color: #1a5fa8;
            font-size: 14px;
        }
        .history-ph {
            margin: 0;
            color: #4a6b8a;
            font-size: 11px;
        }

        /* ── Input fields ────────────────────────────────── */
        .stNumberInput input {
            color: #1a1a2e !important;
            font-weight: 500 !important;
            font-size: 15px !important;
            font-family: 'Inter', sans-serif !important;
            background: #f8fafc !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }
        .stNumberInput input:focus {
            border-color: #1a5fa8 !important;
            box-shadow: 0 0 0 3px rgba(26,95,168,0.1) !important;
            outline: none !important;
        }

        /* ── Primary button ──────────────────────────────── */
        .stButton > button {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button[kind="primary"] {
            background: #1a5fa8 !important;
            border: none !important;
            color: #ffffff !important;
            font-size: 15px !important;
            border-radius: 10px !important;
            padding: 14px 28px !important;
            box-shadow: 0 2px 8px rgba(26,95,168,0.25) !important;
        }
        .stButton > button[kind="primary"]:hover {
            background: #15508f !important;
            box-shadow: 0 4px 16px rgba(26,95,168,0.35) !important;
            transform: translateY(-1px);
        }

        /* ── Secondary button ────────────────────────────── */
        .stButton > button[kind="secondary"] {
            background: #ffffff !important;
            color: #374151 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 10px !important;
            font-size: 14px !important;
            padding: 13px 24px !important;
        }
        .stButton > button[kind="secondary"]:hover {
            background: #f9fafb !important;
            border-color: #9ca3af !important;
            color: #1a1a2e !important;
        }

        /* ── Expander ────────────────────────────────────── */
        .streamlit-expanderHeader {
            font-size: 14px !important;
            font-weight: 500 !important;
            color: #64748b !important;
            border: none !important;
            background: transparent !important;
        }
        .info-box {
            background: #eff6ff;
            border-radius: 8px;
            padding: 12px 14px;
            border: 1px solid rgba(26,95,168,0.1);
        }
        .info-box p {
            margin: 0;
            font-size: 13px;
            color: #374151;
            line-height: 1.6;
        }

        /* ── Welcome hero ────────────────────────────────── */
        .welcome-hero {
            position: relative;
            width: 100%;
            height: 360px;
            overflow: hidden;
            background: #0f1923;
            border-radius: 16px;
            margin-bottom: 32px;
        }
        .welcome-hero img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
        }
        .welcome-hero .overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(to bottom, rgba(15,25,35,0.15) 0%, rgba(15,25,35,0.7) 100%);
        }

        .hero-brand {
            position: absolute;
            top: 48px;
            left: 24px;
            z-index: 2;
        }
        .hero-brand-inner {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(15,35,64,0.55);
            backdrop-filter: blur(8px);
            border-radius: 12px;
            padding: 8px 18px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .hero-brand-text {
            font-family: 'Roboto Slab', serif;
            color: #ffffff;
            font-weight: 700;
            font-size: 20px;
            letter-spacing: -0.3px;
        }

        .hero-text {
            position: absolute;
            bottom: 18px;
            left: 20px;
            right: 20px;
            z-index: 2;
        }
        .hero-title {
            font-family: 'Roboto Slab', serif !important;
            color: #ffffff !important;
            margin: 0 0 4px !important;
            font-size: 22px !important;
            text-shadow: 0 1px 6px rgba(0,0,0,0.4);
            line-height: 1.3;
        }
        .hero-sub {
            color: rgba(255,255,255,0.82);
            margin: 0;
            font-size: 13px;
            text-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }

        /* ── How it works block ────────────────────────── */
        .how-it-works-block {
            border-radius: 14px;
            overflow: hidden;
            height: 148px;
            margin-bottom: 16px;
            position: relative;
            background-color: #0f2340;
            background-size: cover;
            background-position: center;
        }
        .how-it-works-gradient {
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, rgba(15,35,64,0.82) 0%, rgba(15,35,64,0.2) 70%);
        }
        .how-it-works-text {
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .how-it-works-label {
            margin: 0 0 8px;
            color: #7ec8f0;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .how-step {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 5px;
        }
        .how-step-num {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #1a5fa8;
            color: #ffffff;
            font-size: 10px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .how-step-text {
            color: #e8f3fc;
            font-size: 13px;
        }

        /* ── Grids ───────────────────────────────────────── */
        .param-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        .welcome-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 28px;
        }
        .result-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        @media (max-width: 768px) {
            .param-grid, .welcome-grid, .result-grid {
                grid-template-columns: 1fr;
            }
        }

        /* ── Footer ──────────────────────────────────────── */
        .pondiq-footer {
            text-align: center;
            padding: 32px 2rem 20px;
            margin: 40px -2rem 0;
            color: #94a3b8;
            font-size: 12px;
            font-weight: 400;
            letter-spacing: 0.3px;
        }

        /* ── Success / warning boxes ─────────────────────── */
        .stAlert {
            border-radius: 10px !important;
            font-size: 14px !important;
        }

        /* ── Progress bar ────────────────────────────────── */
        .stProgress > div > div {
            background: #e5e7eb !important;
        }

        /* ── Captions ────────────────────────────────────── */
        .stCaption {
            color: #9ca3af !important;
            font-size: 12px !important;
        }

        /* ── Responsive ──────────────────────────────────── */
        /* ── Tablet (≤768px) ──────────────────────────── */
        @media (max-width: 768px) {
            html, body, [class*="css"] {
                font-size: 15px;
            }
            h1 { font-size: 26px !important; }
            h2 { font-size: 20px !important; }
            h3 { font-size: 17px !important; }

            .block-container {
                padding: 0 0.75rem 0 !important;
                max-width: 100% !important;
            }

            .pondiq-header {
                padding: 16px 16px 20px !important;
                margin: 0 -0.75rem 20px !important;
            }
            .pondiq-header h2 { font-size: 18px !important; }
            .pondiq-header .subtitle { font-size: 12px; }

            .decision-banner {
                padding: 22px 16px 28px !important;
                margin: 0 -0.75rem 20px !important;
            }
            .decision-banner .title {
                font-size: 22px !important;
            }
            .decision-banner .icon-circle {
                width: 44px; height: 44px;
                font-size: 24px;
            }

            .param-grid, .welcome-grid, .result-grid {
                grid-template-columns: 1fr !important;
                gap: 12px;
            }

            .pondiq-card {
                padding: 16px;
            }

            .welcome-hero {
                height: 200px;
                border-radius: 8px;
                margin-bottom: 20px;
            }

            .hero-brand {
                top: 20px;
                left: 14px;
            }
            .hero-brand-inner {
                padding: 6px 14px;
                border-radius: 10px;
            }
            .hero-brand-text {
                font-size: 16px;
            }

            .hero-text {
                bottom: 12px;
                left: 14px;
                right: 14px;
            }
            .hero-title {
                font-size: 18px !important;
                margin: 0 0 2px !important;
            }
            .hero-sub {
                font-size: 11px;
            }

            .how-it-works-block {
                height: 120px;
                border-radius: 10px;
            }
            .how-it-works-text {
                padding: 12px 16px;
            }
            .how-it-works-label {
                font-size: 10px;
                margin: 0 0 6px;
            }

            .history-entry {
                flex-wrap: wrap;
                padding: 12px 14px;
            }
            .history-entry .history-right {
                width: 100%;
                text-align: left !important;
                margin-top: 8px;
                display: flex;
                gap: 16px;
            }
            .history-icon {
                width: 36px;
                height: 36px;
                font-size: 18px;
            }
            .history-decision {
                font-size: 13px;
            }
            .history-date {
                font-size: 11px;
            }
            .history-do {
                font-size: 13px;
            }
            .history-ph {
                font-size: 10px;
            }

            .pondiq-footer {
                margin: 28px -0.75rem 0 !important;
                padding: 16px 1rem !important;
                font-size: 11px;
            }

            .stButton > button[kind="primary"],
            .stButton > button[kind="secondary"] {
                width: 100% !important;
                padding: 12px 20px !important;
                font-size: 14px !important;
            }

            .stNumberInput input {
                font-size: 14px !important;
                padding: 8px 12px !important;
            }
        }

        /* ── Phone (≤480px) ─────────────────────────────── */
        @media (max-width: 480px) {
            html, body, [class*="css"] {
                font-size: 14px;
            }
            h1 { font-size: 22px !important; }
            h2 { font-size: 18px !important; }
            h3 { font-size: 16px !important; }

            .block-container {
                padding: 0 0.5rem 0 !important;
            }

            .pondiq-header {
                padding: 14px 12px 16px !important;
                margin: 0 -0.5rem 16px !important;
            }
            .pondiq-header h2 { font-size: 17px !important; }

            .decision-banner {
                padding: 18px 12px 22px !important;
                margin: 0 -0.5rem 16px !important;
            }
            .decision-banner .title {
                font-size: 20px !important;
            }
            .decision-banner .banner-content {
                gap: 10px;
            }
            .decision-banner .icon-circle {
                width: 38px; height: 38px;
                font-size: 20px;
            }

            .param-grid, .welcome-grid, .result-grid {
                gap: 10px;
            }

            .pondiq-card {
                padding: 12px;
            }

            .welcome-hero {
                height: 160px;
                border-radius: 6px;
                margin-bottom: 16px;
            }

            .hero-brand {
                top: 12px;
                left: 10px;
            }
            .hero-brand-inner {
                padding: 5px 10px;
                border-radius: 8px;
            }
            .hero-brand-text {
                font-size: 13px;
            }

            .hero-text {
                bottom: 8px;
                left: 10px;
                right: 10px;
            }
            .hero-title {
                font-size: 15px !important;
            }
            .hero-sub {
                font-size: 10px;
            }

            .how-it-works-block {
                height: 100px;
                border-radius: 8px;
                margin-bottom: 12px;
            }
            .how-it-works-text {
                padding: 8px 12px;
            }
            .how-it-works-label {
                font-size: 9px;
                margin: 0 0 4px;
            }
            .how-step-text {
                font-size: 11px;
            }

            .history-entry {
                flex-direction: column;
                align-items: flex-start !important;
                gap: 8px;
                padding: 10px 12px;
            }
            .history-entry .history-right {
                width: 100%;
                text-align: left !important;
                margin-top: 2px;
                display: flex;
                gap: 12px;
            }
            .history-icon {
                width: 32px;
                height: 32px;
                font-size: 16px;
                border-radius: 8px;
            }
            .history-decision {
                font-size: 13px;
            }
            .history-date {
                font-size: 10px;
            }
            .history-do {
                font-size: 13px;
            }
            .history-ph {
                font-size: 10px;
            }

            .tip-row {
                flex-direction: column;
                gap: 6px;
            }

            .pondiq-footer {
                margin: 24px -0.5rem 0 !important;
                padding: 14px 0.75rem !important;
                font-size: 10px;
            }

            .stButton > button[kind="primary"],
            .stButton > button[kind="secondary"] {
                padding: 11px 16px !important;
                font-size: 13px !important;
                border-radius: 8px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── API Client ───────────────────────────────────────────────────────
API_BASE = "http://localhost:8001"


def api_health() -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def api_predict(data: dict) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}/predict", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# ── Page: Welcome ────────────────────────────────────────────────────
def render_welcome() -> None:
    # ── Hero photo ───────────────────────────────────────────
    if HERO_B64:
        st.markdown(
            f'<div class="welcome-hero">'
            f'<img src="{HERO_B64}" alt="Fresh tilapia harvest"/>'
            f'<div class="overlay"></div>'
            f'<div class="hero-brand">'
            f'<div class="hero-brand-inner">'
            f'<span class="hero-brand-text">AQUASENSE AI</span>'
            f'</div></div>'
            f'<div class="hero-text">'
            f'<h1 class="hero-title">AI-Powered Feed Optimisation for Ghanaian Fish Farmers</h1>'
            f'<p class="hero-sub">Instant feeding decisions from 6 water readings.</p>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="height:200px;background:#1a5fa8;display:flex;align-items:center;justify-content:center;">'
            '<h1 style="color:#ffffff;font-family:\'Roboto Slab\',serif;">AQUASENSE AI</h1></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="app-inner">', unsafe_allow_html=True)

    # Desktop 2-column: About card + How it works side by side
    st.markdown('<div class="welcome-grid">', unsafe_allow_html=True)

    # Left column: What is AQUASENSE AI
    st.markdown('<div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pondiq-card">'
        '<p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#4a6b8a;'
        'text-transform:uppercase;letter-spacing:1.5px;">What is AQUASENSE AI?</p>'
        '<p style="margin:0 0 12px;color:#0f2340;line-height:1.7;font-size:15px;">'
        'AQUASENSE AI is a <strong>professional feeding advisor</strong> for fish farmers. '
        'Enter 6 water quality readings from your pond and instantly receive '
        'a science-based recommendation on whether to feed your fish.</p>'
        '<p style="margin:0;color:#0f2340;line-height:1.7;font-size:15px;">'
        'Overfeeding wastes resources and degrades water quality. '
        'AQUASENSE AI helps you make the right call — every single day.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Right column: How it works + Parameters
    st.markdown('<div>', unsafe_allow_html=True)

    # How it works
    if HOW_IT_B64:
        steps_html = ""
        for i, step in enumerate(
            ["Measure 6 water parameters", "Enter readings into AQUASENSE AI", "Receive your feeding decision"], 1
        ):
            steps_html += (
                f'<div class="how-step">'
                f'<div class="how-step-num">{i}</div>'
                f'<span class="how-step-text">{step}</span></div>'
            )
        st.markdown(
            f'<div class="how-it-works-block" style="background-image:url({HOW_IT_B64})">'
            f'<div class="how-it-works-gradient"></div>'
            f'<div class="how-it-works-text">'
            f'<p class="how-it-works-label">How it works</p>'
            f'{steps_html}</div></div>',
            unsafe_allow_html=True,
        )

    # Parameters measured
    st.markdown(
        '<p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#4a6b8a;'
        'text-transform:uppercase;letter-spacing:1.5px;">Parameters measured</p>',
        unsafe_allow_html=True,
    )
    params = [
        "Dissolved Oxygen (DO)", "pH Level", "Ammonia (mg/L)",
        "Temperature", "Nitrate (PPM)", "Turbidity",
    ]
    cols = st.columns(2)
    for i, label in enumerate(params):
        with cols[i % 2]:
            st.markdown(
                f'<div style="background:#ffffff;border-radius:10px;padding:10px 12px;'
                f'border:1px solid rgba(15,35,64,0.08);margin-bottom:8px;">'
                f'<span style="font-size:12px;color:#0f2340;font-weight:500;line-height:1.3;">{label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # close welcome-grid

    # CTA
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✨  Start Pond Check  →", use_container_width=True, type="primary", key="welcome_cta"):
        st.session_state.page = "entry"
        st.rerun()
    st.caption("Free to use · Works on basic mobile data · No account needed")

    st.markdown('</div>', unsafe_allow_html=True)


# ── Page: Data Entry & Inline Prediction ─────────────────────────────
READINGS = [
    {"id": "do", "label": "Dissolved Oxygen (DO)", "emoji": "💧", "min": 0.0, "max": 14.0,
     "step": 0.1, "unit": " mg/L", "good": "5–9 mg/L is ideal",
     "desc": "Measure with a DO meter or test kit near the pond surface. Low DO stresses fish and reduces feed intake."},
    {"id": "ph", "label": "pH Level", "emoji": "⚗️", "min": 4.0, "max": 10.0,
     "step": 0.1, "unit": "", "good": "6.5–8.5 is optimal",
     "desc": "Use a pH test strip or meter. Test in the morning before noon for the most accurate reading."},
    {"id": "ammonia", "label": "Ammonia (mg/L)", "emoji": "🧪", "min": 0.0, "max": 5.0,
     "step": 0.05, "unit": " mg/L", "good": "Below 0.5 mg/L is safe",
     "desc": "Use an ammonia test kit. High ammonia causes gill damage and suppresses appetite."},
    {"id": "temperature", "label": "Temperature", "emoji": "🌡️", "min": 10.0, "max": 40.0,
     "step": 0.5, "unit": "°C", "good": "26–32°C is best",
     "desc": "Measure with a thermometer just below the pond surface, away from any inlet pipes."},
    {"id": "nitrate", "label": "Nitrate (PPM)", "emoji": "🔬", "min": 0.0, "max": 200.0,
     "step": 1.0, "unit": " ppm", "good": "Below 40 ppm is safe",
     "desc": "Use a nitrate test kit. Elevated nitrate over time indicates poor water exchange."},
    {"id": "turbidity", "label": "Turbidity", "emoji": "🌊", "min": 1.0, "max": 5.0,
     "step": 1.0, "unit": "", "good": "2–3 = slightly green (ideal)",
     "desc": "Estimate water clarity visually — can you see your hand 30 cm below the surface?"},
]

TURBIDITY_LABELS = {1: "Crystal Clear", 2: "Slight Colour", 3: "Green-Tinted", 4: "Cloudy", 5: "Very Turbid"}

DEFAULTS: dict[str, float] = {
    "do": 6.5, "ph": 7.2, "ammonia": 0.2, "temperature": 28.0, "nitrate": 20.0, "turbidity": 2.0,
}


def _slider_decimals(step: float) -> int:
    if step < 0.1:
        return 2
    elif step < 1:
        return 1
    return 0


def _render_slider_card(reading: dict) -> None:
    """Render a parameter card with number input for direct value entry."""
    key = reading["id"]
    if key not in st.session_state:
        st.session_state[key] = DEFAULTS[key]

    dec = _slider_decimals(reading["step"])

    with st.container():
        

        # Header: label + good range
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">'
            f'<div>'
            f'<p style="margin:0;font-weight:600;color:#0f2340;font-size:14px;">{reading["label"]}</p>'
            f'<p style="margin:0;color:#4a6b8a;font-size:12px;">{reading["good"]}</p>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Info expander
        with st.expander(f"ℹ️  About {reading['label']}"):
            st.markdown(
                f'<div class="info-box"><p>{reading["desc"]}</p></div>',
                unsafe_allow_html=True,
            )

        # Number input for direct value entry
        col_input, col_unit = st.columns([3, 1])
        with col_input:
            st.number_input(
                label=reading["label"],
                step=reading["step"],
                key=key,
                label_visibility="collapsed",
                format=f"%.{dec}f",
            )
        with col_unit:
            # Turbidity label
            val = st.session_state[key]
            display_label = TURBIDITY_LABELS.get(int(val), "") if key == "turbidity" else ""
            label_text = display_label or reading["unit"]
            st.markdown(
                f'<div style="display:flex;align-items:center;height:100%;padding-top:4px;">'
                f'<span style="font-size:14px;font-weight:600;color:#4a6b8a;">{label_text}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def render_result() -> None:
    """Standalone prediction result page."""
    result = st.session_state.get("_last_result")
    if not result:
        st.session_state.page = "entry"
        st.rerun()
        return

    label = result.get("label", "Feed Now")
    if label == "Prime Feed":
        label = "Feed Now"
    confidence = result.get("confidence", 0.85)
    probs = result.get("probabilities", {})
    if "Prime Feed" in probs:
        probs["Feed Now"] = probs.pop("Prime Feed")
    warnings = result.get("warning_flags", [])

    configs = {
        "Feed Now":     {"css_class": "feed-now", "icon": "✅", "tip_bg": "#0e7a3e"},
        "Reduce Feed":  {"css_class": "reduce",   "icon": "⚠️", "tip_bg": "#b45309"},
        "Halt Feeding": {"css_class": "stop",     "icon": "🚫", "tip_bg": "#b91c1c"},
    }
    cfg = configs.get(label, configs["Feed Now"])
    conf_pct = round(confidence * 100)

    tips_map = {
        "Feed Now": [
            "Feed at your standard daily ration",
            "Distribute feed evenly across the pond surface",
            "Observe fish feeding behaviour for the first 10 minutes",
            "Remove any uneaten feed after 30 minutes",
        ],
        "Reduce Feed": [
            "Feed at 50% of your normal daily ration",
            "Monitor for uneaten feed after 20 minutes and remove it",
            "Increase surface aeration if available",
            "Recheck DO and ammonia this evening",
        ],
        "Halt Feeding": [
            "Stop feeding immediately for at least 24–48 hours",
            "Increase aeration or add fresh water to dilute toxins",
            "Perform a 20–30% water exchange if possible",
            "Retest all parameters before resuming feeding",
        ],
    }

    reasons_map = {
        "Feed Now": (
            f"ML model confidence: {conf_pct}%. All water quality parameters are within "
            "acceptable ranges. Dissolved oxygen, pH, ammonia, and temperature support "
            "healthy fish metabolism. Feeding now will result in efficient feed conversion."
        ),
        "Reduce Feed": (
            f"ML model confidence: {conf_pct}%. Some parameters are outside the ideal range. "
            "A reduced feeding rate will maintain fish health without adding further load to the pond."
        ),
        "Halt Feeding": (
            f"ML model confidence: {conf_pct}%. Critical water quality parameters are outside "
            "safe ranges. Feeding under these conditions will worsen water quality and stress your fish."
        ),
    }

    next_check_map = {
        "Feed Now": "Tomorrow at the same time",
        "Reduce Feed": "This evening — retest DO and ammonia",
        "Halt Feeding": "Tomorrow morning — retest all 6 parameters",
    }

    tips = tips_map.get(label, tips_map["Feed Now"])

    # ── Decision banner (hero) ────────────────────────────
    st.markdown(
        f'<div class="decision-banner {cfg["css_class"]}" style="border-radius:0;margin:0 -2rem 24px;padding:28px 2rem 36px;">'
        f'<div class="deco-circle deco-1"></div>'
        f'<div class="deco-circle deco-2"></div>'
        f'<div class="banner-content">'
        f'<div class="icon-circle">{cfg["icon"]}</div>'
        f'<div>'
        f'<p class="label">Today\'s Decision</p>'
        f'<h2 class="title">{label.upper()}</h2>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="app-inner">', unsafe_allow_html=True)

    # ── Back button ────────────────────────────────────────
    if st.button("←  Back to Readings", key="result_back_entry", use_container_width=False):
        st.session_state.pop("_last_result", None)
        st.session_state.pop("_last_input", None)
        st.session_state.page = "entry"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Analysis + Confidence (side by side) ──────────────
    st.markdown('<div class="result-grid">', unsafe_allow_html=True)

    st.markdown('<div>', unsafe_allow_html=True)
    with st.container():      
        st.markdown(
            '<p style="margin:0 0 8px;font-size:11px;font-weight:700;color:#4a6b8a;'
            'text-transform:uppercase;letter-spacing:1px;">Analysis</p>',
            unsafe_allow_html=True,
        )
        st.markdown(reasons_map.get(label, reasons_map["Feed Now"]))
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div>', unsafe_allow_html=True)
    if probs:
        with st.container():           
            st.markdown(
                '<p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#4a6b8a;'
                'text-transform:uppercase;letter-spacing:1px;">Model Confidence</p>',
                unsafe_allow_html=True,
            )
            st.progress(confidence, text=f"{conf_pct}% confident — XGBoost model")
            for cls, prob in probs.items():
                pct = round(prob * 100, 1)
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;font-size:12px;color:#4a6b8a;">'
                    f'<span>{cls}</span><span style="font-weight:600;">{pct}%</span></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if warnings:
        st.warning("\n\n".join(f"• {w}" for w in warnings))

    # ── Action Steps ───────────────────────────────────────
    with st.container():        
        st.markdown(
            '<p style="margin:0 0 14px;font-size:11px;font-weight:700;color:#4a6b8a;'
            'text-transform:uppercase;letter-spacing:1px;">Action Steps</p>',
            unsafe_allow_html=True,
        )
        for i, tip in enumerate(tips, 1):
            st.markdown(
                f'<div class="tip-row">'
                f'<div class="tip-number" style="background:{cfg["tip_bg"]};">{i}</div>'
                f'<span style="font-size:14px;color:#0f2340;line-height:1.55;">{tip}</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Next check ─────────────────────────────────────────
    nc = next_check_map.get(label, next_check_map["Feed Now"])
    st.info(f"**🕐 Next Check:** {nc}")

    # ── Actions ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_home, col_hist = st.columns(2)
    with col_home:
        if st.button("🏠  Home", use_container_width=True, type="primary", key="result_home"):
            st.session_state.pop("_last_result", None)
            st.session_state.pop("_last_input", None)
            st.session_state.page = "welcome"
            st.rerun()
    with col_hist:
        if st.button("📊  History", use_container_width=True, type="secondary", key="result_history"):
            st.session_state.page = "history"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def render_entry() -> None:
    # ── Blue header bar with back arrow ────────────────────
    st.markdown(
        '<div class="pondiq-header" style="margin:0 -2rem 24px; border-radius:0;">'
        '<div class="header-row">'
        '<div style="flex:1;">'
        '<h2 style="font-size:22px;">Water Quality Readings</h2>'
        '<p class="subtitle">Enter all 6 parameters, then tap the button</p>'
        '</div>'
        '</div>'
        '<div class="progress-bar"><div class="progress-bar-fill"></div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="app-inner">', unsafe_allow_html=True)

    # ── Back arrow button ──────────────────────────────────
    if st.button("←  Back to Home", key="entry_back_home", use_container_width=False):
        st.session_state.pop("_last_result", None)
        st.session_state.page = "welcome"
        st.rerun()

    # Handle reset trigger
    if st.session_state.get("_reset_trigger"):
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.session_state._reset_trigger = False
        st.session_state.pop("_last_result", None)
        st.session_state.pop("_last_input", None)

    # Server health
    health = api_health()
    if health:
        st.success("✅ AQUASENSE AI ML model connected")
    else:
        st.warning("⚠️ ML model offline — API server may need restart")

    # ── 2-column grid of slider cards ───────────────────────
    st.markdown('<div class="param-grid">', unsafe_allow_html=True)
    for reading in READINGS:
        st.markdown('<div>', unsafe_allow_html=True)
        _render_slider_card(reading)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Action buttons (side by side on desktop) ────────────
    col_predict, col_reset = st.columns([2, 1])
    with col_predict:
        predict_clicked = st.button(
            "✨  Get Recommendation & Prediction",
            use_container_width=True, type="primary", key="entry_predict",
        )
    with col_reset:
        reset_clicked = st.button(
            "↺  Reset All",
            use_container_width=True, type="secondary", key="entry_reset",
        )

    if reset_clicked:
        st.session_state._reset_trigger = True
        st.rerun()

    # ── Prediction ───────────────────────────────────────────
    if predict_clicked:
        input_data = {
            "do": st.session_state.do,
            "ph": st.session_state.ph,
            "ammonia": st.session_state.ammonia,
            "temperature": st.session_state.temperature,
            "nitrate": st.session_state.nitrate,
            "turbidity": st.session_state.turbidity,
        }
        with st.spinner("Analysing with ML model…"):
            result = api_predict(input_data)

        if result:
            st.session_state._last_result = result
            st.session_state._last_input = input_data
            # Save to history
            now = datetime.now()
            hour_12 = now.hour % 12 or 12
            ampm = "AM" if now.hour < 12 else "PM"
            lbl = result["label"]
            if lbl == "Prime Feed":
                lbl = "Feed Now"
            entry = {
                "date": now.strftime("%a, %d %b"),
                "time": f"{hour_12}:{now.strftime('%M')} {ampm}",
                "decision": lbl,
                "do": input_data["do"],
                "ph": input_data["ph"],
                "ammonia": input_data["ammonia"],
                "temp": input_data["temperature"],
                "nitrate": input_data["nitrate"],
                "turbidity": input_data["turbidity"],
            }
            if "_history" not in st.session_state:
                st.session_state._history = []
            st.session_state._history.insert(0, entry)
            st.session_state.page = "result"
            st.rerun()
        else:
            st.error(
                "Could not reach the ML model. The API server may need to be restarted."
            )

    st.markdown('</div>', unsafe_allow_html=True)


# ── Page: History ────────────────────────────────────────────────────
MOCK_HISTORY = [
    {"date": "Today", "time": "7:12 AM", "decision": "Feed Now", "do": 6.8, "ph": 7.1,
     "ammonia": 0.15, "temp": 28, "nitrate": 18, "turbidity": 2},
    {"date": "Yesterday", "time": "6:58 AM", "decision": "Reduce Feed", "do": 4.8, "ph": 7.4,
     "ammonia": 0.55, "temp": 31, "nitrate": 25, "turbidity": 3},
    {"date": "Mon, 26 May", "time": "7:03 AM", "decision": "Feed Now", "do": 7.2, "ph": 7.0,
     "ammonia": 0.10, "temp": 27, "nitrate": 14, "turbidity": 2},
    {"date": "Sun, 25 May", "time": "7:30 AM", "decision": "Halt Feeding", "do": 2.8, "ph": 6.2,
     "ammonia": 2.20, "temp": 34, "nitrate": 60, "turbidity": 5},
    {"date": "Sat, 24 May", "time": "6:50 AM", "decision": "Feed Now", "do": 6.5, "ph": 7.3,
     "ammonia": 0.20, "temp": 27, "nitrate": 16, "turbidity": 2},
    {"date": "Fri, 23 May", "time": "7:15 AM", "decision": "Feed Now", "do": 7.0, "ph": 7.2,
     "ammonia": 0.12, "temp": 26, "nitrate": 12, "turbidity": 2},
    {"date": "Thu, 22 May", "time": "7:00 AM", "decision": "Reduce Feed", "do": 4.5, "ph": 7.6,
     "ammonia": 0.60, "temp": 30, "nitrate": 30, "turbidity": 4},
]


def _get_history() -> list[dict]:
    saved = st.session_state.get("_history", [])
    if st.session_state.get("_cleared", False):
        return saved
    return saved + MOCK_HISTORY


def render_history() -> None:
    history = _get_history()
    feed_now = sum(1 for e in history if e["decision"] == "Feed Now")
    reduce = sum(1 for e in history if e["decision"] == "Reduce Feed")
    stop = sum(1 for e in history if e["decision"] == "Halt Feeding")

    # ── Blue header bar with stats (desktop) ──────────────
    st.markdown(
        '<div class="pondiq-header" style="margin:0 -2rem 24px; border-radius:0;">'
        '<div class="header-row" style="margin-bottom:20px;">'
        '<div style="flex:1;">'
        '<h2 style="font-size:22px;">Reading History</h2>'
        '<p class="subtitle">Last 7 days</p>'
        '</div></div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">'
        f'<div style="background:rgba(255,255,255,0.12);border-radius:12px;padding:14px 12px;text-align:center;">'
        f'<p style="margin:0;font-size:20px;">✅</p>'
        f'<p style="margin:4px 0 2px;font-family:Playfair Display,Georgia,serif;font-weight:700;color:#ffffff;font-size:22px;">{feed_now}</p>'
        f'<p style="margin:0;color:rgba(255,255,255,0.6);font-size:11px;">Feed Days</p></div>'
        f'<div style="background:rgba(255,255,255,0.12);border-radius:12px;padding:14px 12px;text-align:center;">'
        f'<p style="margin:0;font-size:20px;">⚠️</p>'
        f'<p style="margin:4px 0 2px;font-family:Roboto Slab,serif;font-weight:700;color:#ffffff;font-size:22px;">{reduce}</p>'
        f'<p style="margin:0;color:rgba(255,255,255,0.6);font-size:11px;">Reduce Days</p></div>'
        f'<div style="background:rgba(255,255,255,0.12);border-radius:12px;padding:14px 12px;text-align:center;">'
        f'<p style="margin:0;font-size:20px;">🚫</p>'
        f'<p style="margin:4px 0 2px;font-family:Roboto Slab,serif;font-weight:700;color:#ffffff;font-size:22px;">{stop}</p>'
        f'<p style="margin:0;color:rgba(255,255,255,0.6);font-size:11px;">Stop Days</p></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="app-inner">', unsafe_allow_html=True)

    # ── Back arrow button ──────────────────────────────────
    if st.button("←  Back to Check Pond", key="hist_back_entry", use_container_width=False):
        st.session_state.page = "entry"
        st.rerun()

    if not history:
        st.info("No readings yet. Run a pond check to see your history here.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # ── Mini bar chart ─────────────────────────────────────
   
    st.markdown(
        '<p style="margin:0 0 12px;font-size:12px;font-weight:700;color:#4a6b8a;'
        'text-transform:uppercase;letter-spacing:1px;">📊 DO Level This Week (mg/L)</p>',
        unsafe_allow_html=True,
    )
    chart_entries = list(reversed(history[-7:]))
    chart_data = pd.DataFrame(
        [{"Day": e["date"].split(",")[0][:3] if "," in e["date"] else e["date"][:3],
          "DO": e["do"], "Decision": e["decision"]} for e in chart_entries]
    )
    st.bar_chart(chart_data, x="Day", y="DO", color="Decision")
    st.markdown(
        '<div style="display:flex;gap:16px;justify-content:center;margin-top:4px;">'
        '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#4a6b8a;">'
        '<span style="width:10px;height:10px;border-radius:3px;background:#0e7a3e;display:inline-block;"></span> Feed Now</span>'
        '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#4a6b8a;">'
        '<span style="width:10px;height:10px;border-radius:3px;background:#b45309;display:inline-block;"></span> Reduce Feed</span>'
        '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#4a6b8a;">'
        '<span style="width:10px;height:10px;border-radius:3px;background:#b91c1c;display:inline-block;"></span> Stop Feeding</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Feed log entries ─────────────────────────────────────
    decision_cfg = {
        "Feed Now":     {"icon": "✅", "color": "#0e7a3e", "bg": "#e6f5ee"},
        "Reduce Feed":  {"icon": "⚠️", "color": "#b45309", "bg": "#fef3e2"},
        "Halt Feeding": {"icon": "🚫", "color": "#b91c1c", "bg": "#fef2f2"},
    }

    for entry in history:
        dc = decision_cfg[entry["decision"]]
        st.markdown(
            f'<div class="history-entry">'
            f'<div class="history-icon" style="background:{dc["bg"]};">'
            f'<span>{dc["icon"]}</span></div>'
            f'<div class="history-body">'
            f'<p class="history-decision">{entry["decision"]}</p>'
            f'<p class="history-date">{entry["date"]} · {entry["time"]}</p>'
            f'</div>'
            f'<div class="history-right">'
            f'<p class="history-do">DO {entry["do"]}</p>'
            f'<p class="history-ph">pH {entry["ph"]} · {entry["temp"]}°C</p>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Clear History", key="clear_history", use_container_width=True, type="secondary"):
        st.session_state._history = []
        st.session_state._cleared = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ── Main ─────────────────────────────────────────────────────────────
def start_api() -> None:
    """Start the FastAPI server in a background process."""
    port = int(os.environ.get("API_PORT", 8001))
    cmd = [sys.executable, "-m", "uvicorn", "pondiq_api:app", "--host", "0.0.0.0", "--port", str(port)]
    try:
        with open(os.devnull, "w") as devnull:
            subprocess.Popen(cmd, stdout=devnull, stderr=devnull, stdin=devnull)
    except Exception:
        return


def main() -> None:
    inject_css()
    start_api()

    if "page" not in st.session_state:
        st.session_state.page = "welcome"

    page = st.session_state.page
    if page == "welcome":
        render_welcome()
    elif page == "entry":
        render_entry()
    elif page == "result":
        render_result()
    elif page == "history":
        render_history()

    # ── Footer ────────────────────────────────────────────
    st.markdown(
        '<div class="pondiq-footer">'
        '© 2026 Code4Food Security &nbsp;|&nbsp; Developed by FYNBYTE</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
