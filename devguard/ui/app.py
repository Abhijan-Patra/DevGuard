"""DevGuard local operator workspace; presentation never substitutes backend decisions."""
import streamlit as st
from devguard.config import MODEL
from devguard.ui.client import BaseDevGuardClient,DevGuardError,FixtureDevGuardClient,HttpDevGuardClient
from devguard.ui.components.banner import render_fixture_banner
from devguard.ui.components.clipboard_view import render_clipboard_view
from devguard.ui.components.coverage_view import render_coverage_view
from devguard.ui.components.events_view import render_events_view
from devguard.ui.components.incident_view import render_incident_view
from devguard.ui.components.overview_view import render_overview_view
from devguard.ui.components.privacy_view import render_privacy_view
from devguard.ui.design import apply_design
from devguard.ui.session import load_local_token

st.set_page_config(page_title='DevGuard · Operator workspace',page_icon='🛡️',layout='wide',initial_sidebar_state='expanded')
FIXTURE='Fixture Mode (Simulated)'
LIVE='Live Mode (FastAPI Backend)'
VIEWS=['Overview','🛡️ Privacy Gate','📋 Text Clipboard','🔧 Repair & Patches','📜 Audit Event Log','📊 Integration Coverage']


def get_client() -> BaseDevGuardClient:
    if st.session_state.get('app_mode',FIXTURE)==FIXTURE:
        if 'fixture_client' not in st.session_state:st.session_state.fixture_client=FixtureDevGuardClient()
        return st.session_state.fixture_client
    return HttpDevGuardClient(base_url=st.session_state.get('backend_url','http://127.0.0.1:8765/api/v1'),
        token=st.session_state.get('session_token') or st.session_state.get('local_operator_token') or None)


def _clear_results():
    for key in ('last_eval_result','last_eval_binding','delivery_receipt','audit_pages','audit_cursor'):
        st.session_state.pop(key,None)


def main():
    apply_design()
    with st.sidebar:
        st.markdown('<div class="brand"><span class="brand-mark">D</span><div><div class="brand-name">DevGuard</div><div class="brand-sub">LOCAL OPERATOR WORKSPACE</div></div></div>',unsafe_allow_html=True)
        st.subheader('Data source')
        mode=st.radio('Select Data Mode',[FIXTURE,LIVE],index=0 if st.session_state.get('app_mode')!=LIVE else 1,label_visibility='collapsed')
        st.session_state.app_mode=mode
        if mode==LIVE:
            with st.expander('Connection settings',expanded=not bool(st.session_state.get('session_token') or st.session_state.get('local_operator_token'))):
                base_url=st.text_input('Base URL',value=st.session_state.get('backend_url','http://127.0.0.1:8765/api/v1'))
                st.session_state.backend_url=base_url
                manual=st.text_input('Operator Session Token',type='password',value=st.session_state.get('session_token',''),help='Manual enrolment. Never share this token in chat or commit it.')
                st.session_state.session_token=manual
                if st.button('Connect on this Mac',use_container_width=True):
                    try:
                        st.session_state.local_operator_token=load_local_token(base_url)
                        get_client().get_status()
                        st.success('Connected locally. Token stays on the server.')
                    except DevGuardError as error:
                        st.session_state.pop('local_operator_token',None)
                        st.error(f'{error.code}: {error}')
                st.caption('Local connection reads the private session file only after you click. It does not enable clipboard capture.')
                if st.button('Test connection',use_container_width=True):
                    try:
                        health=get_client().get_health()
                        st.success('Authenticated API connection established.')
                        if not health.get('model_ready'):st.warning('Gemma unavailable; contextual checks remain held.')
                    except DevGuardError as error:st.error(f'{error.code}: {error}')
        identity=(mode,st.session_state.get('backend_url'),st.session_state.get('session_token'),st.session_state.get('local_operator_token'))
        if st.session_state.get('_connection_identity')!=identity:
            _clear_results()
            st.session_state._connection_identity=identity
        st.divider()
        st.subheader('Workspace')
        if st.session_state.get('nav_view') not in VIEWS:st.session_state.nav_view='Overview'
        active=st.radio('Go to View',VIEWS,key='nav_view',label_visibility='collapsed')
        st.divider()
        st.subheader('Local intelligence')
        try:
            client=get_client()
        except DevGuardError as error:
            st.error(str(error));st.stop()
        try:
            health=client.get_health()
            st.caption('MODEL READY' if health.get('model_ready') else 'MODEL UNAVAILABLE')
            st.markdown('**Gemma 4 E4B**')
            st.caption('One local model · foreground privacy priority')
        except DevGuardError:
            st.caption('API NOT CONNECTED')
            st.markdown('**Gemma 4 E4B**')
        st.divider()
        st.caption('Local by design. Review before delivery.\nv0.1 · Open-source project')
    top_left,top_right=st.columns([5,1])
    with top_left:render_fixture_banner(client.is_fixture_mode())
    with top_right:
        st.button('Refresh status',use_container_width=True,help='Fetch current backend metadata. Does not enable capture or resume repair.')
    {
        'Overview':render_overview_view,
        '🛡️ Privacy Gate':render_privacy_view,
        '📋 Text Clipboard':render_clipboard_view,
        '🔧 Repair & Patches':render_incident_view,
        '📜 Audit Event Log':render_events_view,
        '📊 Integration Coverage':render_coverage_view,
    }[active](client)
    st.markdown('<div class="footer-note">DevGuard · Local Gemma intelligence · Explicit operator control · No screenshot or recording dependency</div>',unsafe_allow_html=True)


if __name__=='__main__':main()
