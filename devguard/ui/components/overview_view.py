"""Operator overview: actual readiness, explicit actions and bounded audit metadata."""
from html import escape
import streamlit as st
from devguard.config import MODEL
from devguard.ui.client import DevGuardError
from devguard.ui.design import card, feature, heading


def _jump(view):
    st.session_state['nav_view']=view


def render_overview_view(client):
    heading('Your development safety workspace.',
            'Inspect shared context, control text capture, and review backend repairs in one place.',
            'DEVGUARD / OVERVIEW')
    try:
        status=client.get_status()
        health=client.get_health()
        clipboard=client.get_clipboard_status()
    except DevGuardError as error:
        st.warning('Connect to the local backend to see live readiness. No simulated results are substituted.')
        st.caption(f'{error.code} · Open connection settings in the sidebar, then connect on this Mac or enter an operator token.')
        _features()
        return
    repair=status.get('repair',{})
    columns=st.columns(4)
    with columns[0]:
        ready=health.get('model_ready') is True
        card('Local intelligence','Ready' if ready else 'Unavailable',
             'Gemma 4 E4B · local inference', 'good' if ready else 'warn')
    with columns[1]:
        enabled=clipboard.get('enabled') is True
        card('Text clipboard',clipboard.get('state','OFF').replace('_',' ').title(),
             'Opt-in capture is running' if enabled else 'Capture is off · explicit consent required',
             'warn' if enabled else 'neutral')
    with columns[2]:
        state=repair.get('state','UNAVAILABLE')
        card('Repair worker',state.replace('_',' ').title(),
             'Original files require your approval' if repair.get('available') else 'Trusted verifier configuration required',
             'good' if state=='PAUSED' else 'neutral')
    with columns[3]:
        queue=status.get('inference_queue',{})
        waiting=queue.get('foreground_waiting',0)+queue.get('background_waiting',0) if queue else None
        card('Inference queue',str(waiting) if waiting is not None else '—',
             'Waiting requests · privacy takes priority' if queue else 'Queue telemetry is not available')
    st.write('')
    left,right=st.columns([2,1])
    with left:
        st.subheader('Everything you can control')
        _features()
    with right:
        with st.container(border=True):
            st.subheader('Runtime details')
            st.caption('MODEL')
            st.code(health.get('model_name') or MODEL,language=None)
            st.caption('MODEL DIGEST')
            st.code(health.get('model_digest') or 'Not available',language=None,wrap_lines=True)
            audit=status.get('audit',{})
            st.write('Audit storage: '+('Persistent metadata' if audit.get('durable') else 'Session / simulated'))
            if audit.get('retention_events'):
                st.caption(f"Up to {audit['retention_events']:,} redacted events. Raw clipboard history is not stored.")
            st.caption('Capture is advisory. It does not block every paste into other apps.')
            st.button('View integration coverage',on_click=_jump,args=('📊 Integration Coverage',),use_container_width=True)
    st.subheader('Recent recorded activity')
    try:
        events=client.get_events().get('events',[])
        if not events:st.info('No events yet. An inspection or repair action will create a redacted audit record.')
        for event in reversed(events[-4:]):
            st.markdown('<div class="audit-row"><div class="audit-top"><span class="audit-title">'+
                escape(str(event.get('kind','event')))+' · '+escape(str(event.get('state','')))+
                '</span><span>'+escape(str(event.get('timestamp','')))+
                '</span></div><div class="audit-summary">'+escape(str(event.get('redacted_summary','')))+
                '</div></div>',unsafe_allow_html=True)
        st.caption('Showing the latest entries from the loaded audit page.')
    except DevGuardError as error:st.caption('Audit feed unavailable: '+error.code)


def _features():
    rows=[
      [('01','Privacy gate','Inspect prompts, file text and tool results. Review approved text before any supported delivery.','🛡️ Privacy Gate'),
       ('02','Text clipboard','Enable capture with consent, inspect future copies and explicitly copy cleaned text.','📋 Text Clipboard')],
      [('03','Backend repairs','Queue a named investigation, control background work and review independently tested diffs.','🔧 Repair & Patches'),
       ('04','Activity & coverage','Read redacted audit records and see the exact limits of each integration.','📜 Audit Event Log')],
    ]
    for row in rows:
        for col,entry in zip(st.columns(2),row):
            number,title,description,view=entry
            with col:
                with st.container(border=True):
                    feature(number,title,description)
                    st.button('Open '+title.lower(),key='open-'+number,on_click=_jump,args=(view,),use_container_width=True)
