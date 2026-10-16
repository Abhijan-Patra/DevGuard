"""Local dashboard design primitives. Dynamic strings are always HTML escaped."""
from html import escape
from pathlib import Path
import streamlit as st


def apply_design():
    st.markdown('<style>'+Path(__file__).with_name('dashboard.css').read_text()+'</style>',unsafe_allow_html=True)


def heading(title, description, eyebrow='WORKSPACE'):
    st.markdown(f'<div class="page-heading"><div class="eyebrow">{escape(eyebrow)}</div>'
                f'<h1>{escape(title)}</h1><p>{escape(description)}</p></div>',unsafe_allow_html=True)


def card(label, value, description='', tone='neutral'):
    tone=tone if tone in {'neutral','good','warn','bad'} else 'neutral'
    st.markdown(f'<div class="status-card {tone}"><div class="card-label">{escape(str(label))}</div>'
                f'<div class="card-value">{escape(str(value))}</div>'
                f'<div class="card-detail">{escape(str(description))}</div></div>',unsafe_allow_html=True)


def feature(number, title, description):
    st.markdown(f'<div class="feature"><span class="feature-number">{escape(number)}</span>'
                f'<h3>{escape(title)}</h3><p>{escape(description)}</p></div>',unsafe_allow_html=True)
