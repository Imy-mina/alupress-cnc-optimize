import streamlit as st
import re
from pypdf import PdfReader
from datetime import datetime

# Set up clean industrial layout configuration
st.set_page_config(page_title="Alupress Process Control", layout="wide", page_icon="⚙️")

st.markdown("""
    <style>
    .reportview-container { background: #f8fafc; }
    .balloon-title { background: #1e293b; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 Alupress CY040 Live Process Control Assistant")
st.caption("Target Component Profile: Cylinder C (OP10 & OP20) // Blueprint Data Spec: 1390_375_038_DES001")

# 1. EXPANDED BLUEPRINT SPECIFICATION MATRIX (10 ITEMS)
specs = {
    "f25":  {"name": "Item 25 — Y 25 Profile Height", "nom": -7.200, "pTol": 0.150,  "nTol": -0.150, "macro": None,   "inv": False, "type": "height"},
    "f17":  {"name": "Item 17 — // REF Parallelism", "nom": 0.000,  "pTol": 0.300,  "nTol": 0.000,  "macro": None,   "inv": False, "type": "geometry"},
    "f100": {"name": "Item 100 — Y 100 Axial Position", "nom": -15.900, "pTol": 0.100, "nTol": -0.100, "macro": "#857", "inv": False, "type": "axial"},
    "f96":  {"name": "Item 96 — Dia 77.5 Pre-Finish Max", "nom": 77.500, "pTol": 0.190, "nTol": 0.000,  "macro": "#851", "inv": True,  "type": "diameter"},
    "f99":  {"name": "Item 99 — Perpendicularity Runout", "nom": 0.000, "pTol": 0.050, "nTol": 0.000,  "macro": None,   "inv": False, "type": "geometry"},
    "f106": {"name": "Item 106 — Ø106 Dia 68.5 Finish ID", "nom": 68.500, "pTol": 0.200, "nTol": 0.000,  "macro": "#852", "inv": True,  "type": "diameter"},
    "f103": {"name": "Item 103 — Y 103 Cavity Step Height", "nom": 4.900, "pTol": 0.100, "nTol": -0.100, "macro": None,   "inv": False, "type": "height"},
    "f40":  {"name": "Item 40 — Ø40 Dia 149 Inner Cavity", "nom": 149.000, "pTol": 0.200, "nTol": -0.200, "macro": "#855", "inv": False, "type": "diameter"},
    "f29":  {"name": "Item 29 — Face Step 3.9 Distance", "nom": 4.000,  "pTol": 0.100, "nTol": -0.100, "macro": "#856", "inv": True,  "type": "axial"},
    "f30":  {"name": "Item 30 — Base Thickness Profile", "nom": -8.700, "pTol": 0.100, "nTol": -0.100, "macro": "#853", "inv": False, "type": "axial"}
}

# 2. INTENT-BASED CALYPSO PDF STRIPPER
def parse_calypso_pdf(uploaded_file):
    extracted_values = {}
    try:
        reader = PdfReader(uploaded_file)
        full_text = " ".join([page.extract_text() for page in reader.pages])
        
        regex_map = {
            "f25": r"(?:Y 25 Min|Y 25 Max)\s+([0-9.-]+)",
            "f17": r"// REF Parallelism\s+([0-9.-]+)",
            "f100": r"Y 100\s+([0-9.-]+)",
            "f96": r"96-1\^Max\s+([0-9.-]+)",
            "f99": r"99\s+([0-9.-]+)",
            "f106": r"(?:Ø106|106)\s+([0-9.-]+)",
            "f103": r"(?:Y 103\(1\)|103\(1\))\s+([0-9.-]+)",
            "f40": r"(?:Ø40|40)\s+([0-9.-]+)",
            "f29": r"(?:29\(1\)|29)\s+([0-9.-]+)",
            "f30": r"(?:30\(1\)|30)\s+([0-9.-]+)"
        }
        for key, pattern in regex_map.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted_values[key] = float(match.group(1))
    except Exception as e:
        st.error(f"Error parsing PDF data streams: {e}")
    return extracted_values

if 'cmm_data' not in st.session_state:
    st.session_state.cmm_data = {k: {"sp1": specs[k]["nom"], "sp2": specs[k]["nom"]} for k in specs}

# 3. UPLOAD AREA TERMINAL DASHBOARD
col1, col2 = st.columns(2)
with col1:
    sp1_file = st.file_uploader("📄 Upload Spindle 1 (SP1) Zeiss CMM PDF", type="pdf")
    if sp1_file:
        parsed = parse_calypso_pdf(sp1_file)
        for k, v in parsed.items(): st.session_state.cmm_data[k]["sp1"] = v
        st.success("Spindle 1 Report Automatically Loaded!")

with col2:
    sp2_file = st.file_uploader("📄 Upload Spindle 2 (SP2) Zeiss CMM PDF", type="pdf")
    if sp2_file:
        parsed = parse_calypso_pdf(sp2_file)
        for k, v in parsed.items(): st.session_state.cmm_data[k]["sp2"] = v
        st.success("Spindle 2 Report Automatically Loaded!")

st.divider()

layout_left, layout_right = st.columns(2)

with layout_left:
    st.subheader("📋 Operator Action Logic Directives")
    
    # Read Current Machine Parameters 
    st.write("#### Active Controller Baseline Matrix")
    m_cols = st.columns(4)
    current_macros = {
        "#851": m_cols.number_input("#851 (Itm 96)", value=-0.050, step=0.001, format="%.3f"),
        "#852": m_cols.number_input("#852 (Itm 106)", value=-0.040, step=0.001, format="%.3f"),
        "#855": m_cols.number_input("#855 (Itm 40)", value=0.065, step=0.001, format="%.3f"),
        "#856": m_cols.number_input("#856 (Itm 29)", value=-0.019, step=0.001, format="%.3f"),
        "#857": m_cols.number_input("#857 (Itm 100)", value=0.150, step=0.001, format="%.3f"),
        "#853": m_cols.number_input("#853 (Itm 30)", value=-0.005, step=0.001, format="%.3f")
    }
    final_macros = current_macros.copy()

    # DYNAMIC DUAL-SPINDLE CHECK CHECKS
    for key, spec in specs.items():
        sp1_val = st.session_state.cmm_data[key]["sp1"]
        sp2_val = st.session_state.cmm_data[key]["sp2"]
        
        dev1 = sp1_val - spec["nom"]
        dev2 = sp2_val - spec["nom"]
        
        upper80 = spec["pTol"] * 0.8
        lower80 = spec["nTol"] * 0.8
        
        breach = (dev1 > upper80 or dev1 < lower80 or dev2 > upper80 or dev2 < lower80)
        
        if not breach:
            st.success(f"**🟢 {spec['name']}**  \nBoth spindles running stable inside 80% boundary limits. No adjustments required.")
        else:
            # INTERVENTION ENGINE RULES: Check for Opposing Imbalances Across the Spindles
            if (dev1 * dev2 < 0) and (abs(dev1) > 0.015 and abs(dev2) > 0.015):
                if spec["type"] == "height":
                    st.error(f"**🛑 {spec['name']} — MECHANICAL IMBALANCE TRAP**  \n"
                             f"SP1 Dev: `{dev1:+.3f}` | SP2 Dev: `{dev2:+.3f}`  \n"
                             f"⚠️ **CRITICAL STOP:** Height measurements are splitting fields. Changing parameters here will throw one spindle out. "
                             f"**DO NOT change global wear parameter settings. Manually adjust finishing tool cartridge mechanically on Spindle 2!**")
                elif spec["type"] == "diameter":
                    st.error(f"**🛑 {spec['name']} — TOOL INTERVENTION TRAP**  \n"
                             f"SP1 Dev: `{dev1:+.3f}` | SP2 Dev: `{dev2:+.3f}`  \n"
                             f"⚠️ **CRITICAL STOP:** Spindle 1 is running too wide but Spindle 2 is cutting too small. "
                             f"**Replace Spindle 2 tool insert insert immediately or check geometric alignment of the carriage chucks.**")
                else:
                    st.error(f"**🛑 {spec['name']} — PROCESS CONFLICT**  \n"
                             f"Diverging opposing data values. Check fixture face for nesting chips or mechanical clamp play.")
            else:
                # Geometric Control Exception Logic
                if spec["type"] == "geometry":
                    st.error(f"**⚠️ {spec['name']} — GEOMETRIC SPECIFICATION ERROR**  \n"
                             f"SP1: `{sp1_val:.3f}` | SP2: `{sp2_val:.3f}`  \n"
                             f"Geometric form errors cannot be adjusted with tool offsets. **ACTION: Check for part nesting chips or adjust clamping pressure down.**")
                # Valid Tool Wear Drift Correction Path
                elif spec["macro"]:
                    mean_dev = (dev1 + dev2) / 2
                    correction = mean_dev if spec["inv"] else -mean_dev
                    new_macro_val = current_macros[spec["macro"]] + correction
                    final_macros[spec["macro"]] = new_macro_val
                    
                    st.warning(f"**⚡ {spec['name']} — Offset Change Advised**  \n"
                               f"SP1 Dev: `{dev1:+.3f}` | SP2 Dev: `{dev2:+.3f}`  \n"
                               f"**Action:** Shift register **{spec['macro']}** from `{current_macros[spec['macro']]:.3f}` to **`{new_macro_val:.3f}`** "
                               f"(Correction entry: `{correction:+.3f}` mm).")
                else:
                    st.error(f"**⚠️ {spec['name']} — Control Window Locked**  \n"
                             f"Adjust dependent variables on master profile features first before modifying parameters here!")

with layout_right:
    st.subheader("📐 Measured Shop Metrics & Fanuc Script Block")
    
    # Render All 10 Expanded Characteristic Entry Blocks
    for key, spec in specs.items():
        with st.expander(f"Data Fields: {spec['name']}", expanded=False):
            mc1, mc2 = st.columns(2)
            st.session_state.cmm_data[key]["sp1"] = mc1.number_input(f"SP1 Actual", value=st.session_state.cmm_data[key]["sp1"], format="%.3f", key=f"v1_{key}")
            st.session_state.cmm_data[key]["sp2"] = mc2.number_input(f"SP2 Actual", value=st.session_state.cmm_data[key]["sp2"], format="%.3f", key=f"v2_{key}")

    # Render Final Corrected Fanuc O1118 Block Code
    gcode = f"""%
O1118(OPTIMIZED ADJUSTMENT SYSTEM BLOCK)
(DIAGNOSTIC TRACK RUN TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
(================================================)
#850=0.000 (Z-Rough Pass Constant Pass)
#851={final_macros['#851']:.3f} (Item 96 Pre-Finish Wear)
#852={final_macros['#852']:.3f} (Item 106 Finish ID Wear)
#853={final_macros['#853']:.3f} (Item 30 Base Face Wear)
#854=-0.005
#855={final_macros['#855']:.3f} (Item 40 Inner Dia Wear)
#856={final_macros['#856']:.3f} (Item 29 Face Step Wear)
#857={final_macros['#857']:.3f} (Item 100 Z Axial Stock)
#860=0.000
#858=0.200
#859=0.200
(================================================)
M99
%"""
    st.write("#### Fanuc Output Code Console Block")
    st.code(gcode, language="gcode")
