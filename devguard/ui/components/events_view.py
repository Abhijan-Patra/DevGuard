"""Bounded redacted audit feed. No raw prompt/clipboard content is rendered."""
from html import escape
import json
import streamlit as st
from devguard.ui.client import DevGuardError
from devguard.ui.design import heading


def render_events_view(client):
    heading('A clear record of what happened.','Review privacy decisions and repair activity. The audit stores redacted metadata, not raw inputs.','DEVGUARD / ACTIVITY')
    try:
        page=client.get_events()
    except DevGuardError as error:
        st.error(f'Audit unavailable [{error.code}]: {error}');return
    events=list(page.get('events',[]))+st.session_state.get('audit_pages',[])
    unique={event['event_id']:event for event in events if event.get('event_id')}
    events=list(unique.values())[-1000:]
    if not events:st.info('No audit events yet. Inspections and repair actions create redacted records.');return
    left,middle,right=st.columns([2,2,1])
    with left:
        kinds=st.multiselect('Event type',sorted({str(e.get('kind','event')) for e in events}))
    with middle:
        severities=st.multiselect('Severity',['INFO','WARNING','ERROR','CRITICAL'])
    with right:
        st.caption('LOADED RECORDS')
        st.write(str(len(events)))
    filtered=[e for e in events if (not kinds or e.get('kind') in kinds) and
              (not severities or str(e.get('severity','info')).upper() in severities)]
    if not filtered:st.info('No loaded events match these filters.')
    for event in reversed(filtered):
        kind=escape(str(event.get('kind','event')))
        state=escape(str(event.get('state','')))
        stamp=escape(str(event.get('timestamp','')))
        summary=escape(str(event.get('redacted_summary','')))
        st.markdown(f'<div class="audit-row"><div class="audit-top"><span class="audit-title">{kind} · {state}</span><span>{stamp}</span></div><div class="audit-summary">{summary}</div></div>',unsafe_allow_html=True)
    st.caption('Up to 1,000 loaded records are kept in this dashboard session. Backend retention is separate.')
    if not client.is_fixture_mode():
        if st.button('Load next audit page'):
            try:
                cursor=st.session_state.get('audit_cursor') or page.get('next_cursor')
                more=client.get_events(cursor)
                extra=st.session_state.get('audit_pages',[])+more.get('events',[])
                st.session_state.audit_pages=extra[-900:]
                st.session_state.audit_cursor=more.get('next_cursor')
                if not more.get('events'):st.info('No more audit records at this cursor.')
                else:st.rerun()
            except DevGuardError as error:st.error(f'{error.code}: {error}')
    fields=('event_id','timestamp','project_id','kind','state','severity','redacted_summary','run_id','request_id')
    export=[{key:event.get(key) for key in fields if key in event} for event in filtered]
    st.download_button('Export displayed redacted metadata',json.dumps(export,indent=2),file_name='devguard-redacted-audit.json',mime='application/json')
