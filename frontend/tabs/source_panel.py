import streamlit as st

def render_source_panel(api):
    st.subheader("Sources")
    try:
        for filename in api("GET", "/sources")["files"]:
            cols = st.columns([0.75, 0.25])
            cols[0].caption(filename)
            if cols[1].button("Remove", key=f"remove-{filename}"):
                api("DELETE", f"/upload/{filename}")
                st.rerun()
    except Exception as exc:
        st.warning(str(exc))

    upload = st.file_uploader("Upload CSV", type="csv")
    if upload and st.button("Add source"):
        api("POST", "/upload", files={"file": (upload.name, upload.getvalue(), "text/csv")})
        st.rerun()

    cols = st.columns(2)
    if cols[0].button("Rebuild Graph"):
        try:
            st.session_state["status"] = api("POST", "/rebuild-graph")
        except Exception as exc:
            if hasattr(exc, 'response') and exc.response is not None:
                st.error(exc.response.json())
            else:
                st.error(str(exc))
    if cols[1].button("Reset to demo data"):
        st.session_state["status"] = api("POST", "/reset-demo")
        st.rerun()

    try:
        status = api("GET", "/graph/status")
        st.metric("Assets", status["assets"])
        st.metric("Relationships", status["relationships"])
        st.caption(f"Last rebuilt: {status.get('last_rebuilt', 'unknown')}")
        for warning in status.get("warnings", []):
            st.warning(warning)
    except Exception as exc:
        st.info(f"Graph not ready: {exc}")
