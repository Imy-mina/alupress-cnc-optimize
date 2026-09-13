import streamlit as st
import re
from pypdf import PdfReader
from datetime import datetime

# Configure industrial theme configuration
st.set_page_config(page_title="Alupress Process Control", layout="wide", page_icon="🛠️")

st.markdown("""
    <style>
    .reportview-container { background: #f8fafc; }
    .balloon { background: #0f172a; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
    </style>
""", unsafe_view_header=True)

st.title("🌐 Alupress CY040 Live Process Dashboard")
st.caption("Target Component Profile: Cylinder C (OP10 & OP20) // Blueprint Data Spec: 1390_375_038_DES001")

# 1. Blueprint Tolerance Profiles Matrix Definition
specs = {
    "f25":  {"name": "Item 25 — Y 25 Profile Height", "nom": -7.200, "pTol": 0.150,  "nTol": -0.150, "macro": None,   "inv": False, "isHeight": True},
    "f77":  {"name": "Item 96 — Dia 77.5 Pre-Finish", "nom": 77.500, "pTol": 0.190,  "nTol": 0.000,  "macro": "#851", "inv": True,  "isHeight": False},
    "f68":  {"name": "Item 106 — Dia 68.5 Finish ID", "nom": 68.500, "pTol": 0.200,  "nTol": 0.000,  "macro": "#852", "inv": True,  "isHeight": False},
    "f149": {"name": "Item 40 — Dia 149 Inner Cavity","nom": 149.000,"pTol": 0.200,  "nTol": -0.200, "macro": "#855", "inv": False, "isHeight": False},
    "f39":  {"name": "Item 29 — Face Step 3.9 Distance","nom": 4.000,  "pTol": 0.100,  "nTol": -0.100, "macro": "#856", "inv": True,  "isHeight": False}
}

# 2. Automated Parsing Functions for Calypso Data Structure
def parse_calypso_pdf(uploaded_file):
    extracted_values = {}
    try:
        reader = PdfReader(uploaded_file)
        full_text = " ".join([page.extract_text() for page in reader.pages])
        
        regex_map = {
            "f25": r"(?:Y 25 Min|Y 25 Max)\s+([0-9.-]+)",
            "f77": r"96-1\^Max\s+([0-9.-]+)",
            "f68": r"(?:Ø106|106)\s+([0-9.-]+)",
            "f149": r"(?:Ø40|40)\s+([0-9.-]+)",
            "f39": r"(?:29\(1\)|29)\s+([0-9.-]+)"
        }
        for key, pattern in regex_map.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                extracted_values[key] = float(match.group(1))
    except Exception as e:
        st.error(f"Error parsing PDF file stream: {e}")
    return extracted_values

# Setup persistent file data store registers
if 'cmm_data' not in st.session_state:
    st.session_state.cmm_data = {k: {"sp1": specs[k]["nom"], "sp2": specs[k]["nom"]} for k in specs}

# 3. Structural Upload Panel Bars Layout
col1, col2 = st.columns(2)
with col1:
    sp1_file = st.file_uploader("📄 Upload Spindle 1 (SP1) Zeiss CMM PDF", type="pdf")
    if sp1_file:
        parsed = parse_calypso_pdf(sp1_file)
        for k, v in parsed.items(): st.session_state.cmm_data[k]["sp1"] = v
        st.success("Spindle 1 Report Synchronized!")

with col2:
    sp2_file = st.file_uploader("📄 Upload Spindle 2 (SP2) Zeiss CMM PDF", type="pdf")
    if sp2_file:
        parsed = parse_calypso_pdf(sp2_file)
        for k, v in parsed.items(): st.session_state.cmm_data[k]["sp2"] = v
        st.success("Spindle 2 Report Synchronized!")

st.divider()

# 4. Main Diagnostic Workflow UI Split
layout_left, layout_right = st.columns([4, 3])

with layout_left:
    st.subheader("📋 Operator Directives & Action Logic")
    
    # Read Controller Baseline Values
    st.write("#### Current Active Controller Baseline Values")
    macro_input_cols = st.columns(4)
    current_macros = {
        "#851": macro_input_cols[0].number_input("#851 (Itm 96)", value=-0.050, step=0.001, format="%.3f"),
        "#852": macro_input_cols[1].number_input("#852 (Itm 106)", value=-0.040, step=0.001, format="%.3f"),
        "#855": macro_input_cols[2].number_input("#855 (Itm 40)", value=0.065, step=0.001, format="%.3f"),
        "#856": macro_input_cols[3].number_input("#856 (Itm 29)", value=-0.019, step=0.001, format="%.3f")
    }

    final_macros = current_macros.copy()

    # Process Expert Rules Engine Calculations
    for key, spec in specs.items():
        sp1_val = st.session_state.cmm_data[key]["sp1"]
        sp2_val = st.session_state.cmm_data[key]["sp2"]
        
        dev1 = sp1_val - spec["nom"]
        dev2 = sp2_val - spec["nom"]
        
        upper80 = spec["pTol"] * 0.8
        lower80 = spec["nTol"] * 0.8
        
        breach = (dev1 > upper80 or dev1 < lower80 or dev2 > upper80 or dev2 < lower80)
        
        if not breach:
            st.success(f"**🟢 {spec['name']}**  \nBoth spindles running stable inside 80% boundary limits. No compensation actions requested.")
        else:
            # Check for Opposing Error / Imbalance Trap Conditions
            if (dev1 * dev2 < 0) and (abs(dev1) > 0.02 and abs(dev2) > 0.02):
                if spec["isHeight"]:
                    st.error(f"**🛑 {spec['name']} — MECHANICAL IMBALANCE TRAP**  \n"
                             f"SP1 Dev: `{dev1:+.3f}` | SP2 Dev: `{dev2:+.3f}`  \n"
                             f"**CRITICAL REPAIR ACTION:** Spindles heights are diverging in opposite vector fields! Changing tool registers will compromise the alternative spindle. "
                             f"**Do not touch controller offsets. Inspect finishing cartridge inserts on Spindle 2 mechanically now!**")
                else:
                    st.error(f"**🛑 {spec['name']} — TOOL INTERVENTION REQUIRED**  \n"
                             f"SP1 Dev: `{dev1:+.3f}` | SP2 Dev: `{dev2:+.3f}`  \n"
                             f"**CRITICAL ACTION:** One spindle is executing cuts too large while the other runs tight. A standard linear macro tool shift cannot fix this. "
                             f"**Replace the Spindle 2 tool insert immediately or audit geometric carriage alignments.**")
            else:
                # Valid Tool Wear Drift Trend: Compute offset shift corrections
                if spec["macro"]:
                    mean_dev = (dev1 + dev2) / 2
                    correction = mean_dev if spec["inv"] else -mean_dev
                    new_macro_val = current_macros[spec["macro"]] + correction
                    final_macros[spec["macro"]] = new_macro_val
                    
                    st.warning(f"**⚡ {spec['name']} — Offset Adjustment Recommended**  \n"
                               f"SP1 Dev: `{dev1:+.3f}` | SP2 Dev: `{dev2:+.3f}`  \n"
                               f"**Action:** Shift register **{spec['macro']}** from `{current_macros[spec['macro']]:.3f}` to **`{new_macro_val:.3f}`** "
                               f"(Input Value Change: `{correction:+.3f}` mm).")
                else:
                    st.error(f"**⚠️ {spec['name']} — Sequence Protocol Blocked**  \n"
                             f"Profile out of position window bounds. Target **Dimension 16-0.2 (Item 100)** in secondary operation profile first before modifying parameters here!")

with layout_right:
    st.subheader("📐 Live Inspection Data & Fanuc Block")
    
    # Render Interactive Metrics Inspection Chart
    for key, spec in specs.items():
        with st.expander(f"Data Matrix: {spec['name']}", expanded=True):
            mc1, mc2 = st.columns(2)
            st.session_state.cmm_data[key]["sp1"] = mc1.number_input(f"SP1 Value", value=st.session_state.cmm_data[key]["sp1"], format="%.3f", key=f"inp_sp1_{key}")
            st.session_state.cmm_data[key]["sp2"] = mc2.number_input(f"SP2 Value", value=st.session_state.cmm_data[key]["sp2"], format="%.3f", key=f"inp_sp2_{key}")

    # Generate G-Code Script Box
    gcode = f"""%
O1118(DUAL SPINDLE COMPILED BLOCK)
(GENERATION TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
(================================================)
#850=0.000 (Z-Rough Pass Constant)
#851={final_macros['#851']:.3f} (Item 96 Wear Correction)
#852={final_macros['#852']:.3f} (Item 106 Wear Correction)
#853=-0.005
#854=-0.005
#855={final_macros['#855']:.3f} (Item 40 Wear Correction)
#856={final_macros['#856']:.3f} (Item 29 Wear Correction)
#857=0.150
#860=0.000
#858=0.200
#859=0.200
(================================================)
M99
%"""
    st.write("#### Fanuc Output Code Terminal Block")
    st.code(gcode, language="gcode")
