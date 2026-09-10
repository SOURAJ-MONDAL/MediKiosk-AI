import streamlit as st
from components.ui import inject_global_styles
from services.patient_service import PatientService
from services.document_service import DocumentService
from utils.helpers import format_date


def require_patient():
    inject_global_styles()
    if "user" not in st.session_state or not st.session_state.user:
        st.info("Please log in to manage documents.", icon=":material/lock:")
        if st.button("Go to login", icon=":material/login:"):
            st.switch_page("app_pages/login.py")
        st.stop()
    if st.session_state.user.get("role") != "patient":
        st.error("This page is for patients.", icon=":material/error:")
        st.stop()


require_patient()

user = st.session_state.user
patient = PatientService.get_patient_by_user_id(user["id"])

if not patient:
    st.error("Patient profile not found.", icon=":material/error:")
    st.stop()

st.markdown("""
<div class="mk-section" style="margin-top: 0.5rem;">
    <div class="mk-eyebrow">Health records</div>
    <div class="mk-section-title">Documents</div>
    <div class="mk-section-sub">Upload and organize lab reports, prescriptions, and medical records.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("### Upload a document")
doc_type_labels = {
    "lab_report": "Lab report",
    "prescription": "Prescription",
    "imaging": "Imaging / scan",
    "other": "Other",
}
with st.form("upload_form"):
    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Document title", placeholder="e.g. Blood test July 2026")
    with c2:
        doc_type = st.selectbox("Document type", list(doc_type_labels.keys()),
                                format_func=lambda x: doc_type_labels.get(x, x))
    uploaded = st.file_uploader("Choose a file", type=["pdf", "jpg", "jpeg", "png", "gif", "doc", "docx"])
    notes = st.text_input("Notes (optional)")
    submitted = st.form_submit_button("Upload document", icon=":material/upload:", type="primary")

if submitted:
    if not title or uploaded is None:
        st.error("Title and file are required.", icon=":material/error:")
    else:
        result = DocumentService.upload_document(
            patient_id=patient["id"],
            title=title,
            file_bytes=uploaded.getvalue(),
            filename=uploaded.name,
            document_type=doc_type,
            notes=notes,
        )
        if result["success"]:
            st.success("Document uploaded!", icon=":material/check_circle:")
            st.rerun()
        else:
            st.error(result["error"], icon=":material/error:")

st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)
st.markdown("### Your documents")

documents = DocumentService.get_patient_documents(patient["id"])

if not documents:
    st.markdown("""
    <div class="mk-empty">
        <div class="mk-empty-icon">📁</div>
        <div class="mk-empty-title">No health documents uploaded yet</div>
        <div class="mk-empty-text">Upload lab reports, imaging results, or prescriptions above.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for doc in documents:
        st.markdown(f"""
        <div class="mk-card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
                <div>
                    <div class="mk-card-title">{doc['title']}</div>
                    <div class="mk-card-subtitle">
                        <span class="mk-badge mk-badge-blue mk-badge-sm">{doc_type_labels.get(doc['document_type'], doc['document_type']).title()}</span>
                        <span style="margin-left:0.5rem;">{format_date(doc['uploaded_at'][:10])}</span>
                    </div>
                </div>
            </div>
            {f"<div style='font-size:0.85rem; color:#6b7f94;'>Notes: {doc['notes']}</div>" if doc.get('notes') else ""}
            <div style="margin-top:0.5rem;">
                <span class="mk-badge mk-badge-gray mk-badge-sm">{(doc.get('file_size') or 0) / 1024:.0f} KB</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Delete", key=f"del_doc_{doc['id']}", icon=":material/delete:"):
            result = DocumentService.delete_document(doc["id"], patient["id"])
            if result["success"]:
                st.success("Document deleted.", icon=":material/check_circle:")
                st.rerun()
            else:
                st.error(result["error"], icon=":material/error:")

st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
st.caption("Uploaded files are stored for demonstration purposes only. This prototype does not guarantee HIPAA-level data protection.")