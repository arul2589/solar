// English / Tamil text for the admin menu and the technician (project) screens.
// Same language switch as the public site (stored in the browser).
// Tamil wording should be reviewed by a native speaker.
import { useI18n, type Lang } from "./i18n";

const en = {
  nav_pipeline: "Pipeline", nav_calculator: "Calculator", nav_projects: "Projects", nav_knowledge: "Knowledge (AI)",
  nav_catalogue: "Price list & catalogue", nav_settings: "Settings", nav_users: "Users", nav_emails: "Email log",
  nav_platform: "Installers", sign_out: "Sign out", loading: "Loading...",
  nav_account: "My account", acc_title: "My account", acc_change_pw: "Change my password",
  acc_current: "Current password", acc_new: "New password (min 8 characters)", acc_confirm: "Type the new password again",
  acc_save: "Change password", acc_mismatch: "The two new passwords do not match",
  acc_short: "The new password must be at least 8 characters", acc_changed: "Password changed. Use the new password next time you sign in.",
  projects: "Projects", no_projects: "No projects yet. A project is created when a customer accepts a quotation.",
  back_projects: "← Projects", pack_pdf: "Project pack PDF", request: "Request", assign_tech: "Assign technician...",
  st_planned: "Planned", st_in_progress: "In progress", st_net_metering: "Net metering", st_done: "Completed",
  tab_checklist: "Checklist", tab_readings: "Readings", tab_photos: "Photos", tab_materials: "Materials",
  tab_drawings: "Drawings", tab_netmetering: "Net metering", tab_explain: "Design explanation",
  notes: "Notes", readings_title: "Test readings",
  readings_expected: "Expected max string Voc (cold design): {v} V · earth resistance below 5 Ω per pit.",
  test: "Test", label: "Label", value: "Value", save: "Save", expected: "Expected", result: "Result",
  rk_voc: "Voc (V)", rk_isc: "Isc (A)", rk_earth_resistance: "Earth resistance (Ω)", rk_insulation: "Insulation (MΩ)",
  rk_ac_voltage: "AC voltage (V)", rk_other: "Other", ok: "OK", check: "CHECK",
  photos_title: "Site photos", bom: "Bill of materials", string_plan: "String plan",
  string_line: "String {n}: {m} modules · {inv}MPPT {mppt}", inverter_n: "inverter {i} · ", tools: "Tools",
  nm_docs: "TANGEDCO net-metering documents", drawings_note: "Drawings are in English (standard electrical labels).",
  explain_title: "Why this design", explain_lead: "Plain-language explanation of this system, with references to your documents.",
  explain_none: "No explanation yet.", explain_make: "Create explanation", explain_again: "Create again",
  explain_working: "Writing…", explain_lang: "Language",
  explain_ta_note: "Tamil text is written by AI. Have it checked before sharing with customers.",
};

type AKey = keyof typeof en;

const ta: Record<AKey, string> = {
  nav_pipeline: "கோரிக்கைகள்", nav_calculator: "கணிப்பான்", nav_projects: "திட்டங்கள்", nav_knowledge: "அறிவுத் தளம் (AI)",
  nav_catalogue: "விலைப் பட்டியல்", nav_settings: "அமைப்புகள்", nav_users: "பயனர்கள்", nav_emails: "மின்னஞ்சல் பதிவு",
  nav_platform: "நிறுவுநர்கள்", sign_out: "வெளியேறு", loading: "ஏற்றுகிறது...",
  nav_account: "என் கணக்கு", acc_title: "என் கணக்கு", acc_change_pw: "என் கடவுச்சொல்லை மாற்று",
  acc_current: "தற்போதைய கடவுச்சொல்", acc_new: "புதிய கடவுச்சொல் (குறைந்தது 8 எழுத்துகள்)", acc_confirm: "புதிய கடவுச்சொல்லை மீண்டும் உள்ளிடவும்",
  acc_save: "கடவுச்சொல்லை மாற்று", acc_mismatch: "இரண்டு புதிய கடவுச்சொற்களும் பொருந்தவில்லை",
  acc_short: "புதிய கடவுச்சொல் குறைந்தது 8 எழுத்துகள் இருக்க வேண்டும்", acc_changed: "கடவுச்சொல் மாற்றப்பட்டது. அடுத்த முறை புதிய கடவுச்சொல்லுடன் உள்நுழையவும்.",
  projects: "திட்டங்கள்", no_projects: "இன்னும் திட்டங்கள் இல்லை. வாடிக்கையாளர் விலைப்புள்ளியை ஏற்றதும் திட்டம் உருவாகும்.",
  back_projects: "← திட்டங்கள்", pack_pdf: "திட்ட ஆவணம் PDF", request: "கோரிக்கை", assign_tech: "தொழில்நுட்பரை ஒதுக்கு...",
  st_planned: "திட்டமிடப்பட்டது", st_in_progress: "நடைபெறுகிறது", st_net_metering: "நெட் மீட்டரிங்", st_done: "முடிந்தது",
  tab_checklist: "சரிபார்ப்புப் பட்டியல்", tab_readings: "அளவீடுகள்", tab_photos: "புகைப்படங்கள்", tab_materials: "பொருட்கள்",
  tab_drawings: "வரைபடங்கள்", tab_netmetering: "நெட் மீட்டரிங்", tab_explain: "வடிவமைப்பு விளக்கம்",
  notes: "குறிப்புகள்", readings_title: "சோதனை அளவீடுகள்",
  readings_expected: "எதிர்பார்க்கும் அதிகபட்ச ஸ்ட்ரிங் Voc (குளிர் நிலை): {v} V · ஒவ்வொரு எர்த் குழிக்கும் மின்தடை 5 Ω-க்குக் கீழ்.",
  test: "சோதனை", label: "குறிப்பு", value: "மதிப்பு", save: "சேமி", expected: "எதிர்பார்ப்பு", result: "முடிவு",
  rk_voc: "Voc (V)", rk_isc: "Isc (A)", rk_earth_resistance: "எர்த் மின்தடை (Ω)", rk_insulation: "இன்சுலேஷன் (MΩ)",
  rk_ac_voltage: "AC மின்னழுத்தம் (V)", rk_other: "மற்றவை", ok: "சரி", check: "சரிபார்க்கவும்",
  photos_title: "தளப் புகைப்படங்கள்", bom: "பொருட்கள் பட்டியல்", string_plan: "ஸ்ட்ரிங் திட்டம்",
  string_line: "ஸ்ட்ரிங் {n}: {m} பேனல்கள் · {inv}MPPT {mppt}", inverter_n: "இன்வெர்ட்டர் {i} · ", tools: "கருவிகள்",
  nm_docs: "TANGEDCO நெட் மீட்டரிங் ஆவணங்கள்", drawings_note: "வரைபடங்கள் ஆங்கிலத்தில் உள்ளன (நிலையான மின் குறியீடுகள்).",
  explain_title: "இந்த வடிவமைப்பு ஏன்", explain_lead: "இந்த அமைப்பின் எளிய விளக்கம், உங்கள் ஆவணங்களின் மேற்கோள்களுடன்.",
  explain_none: "இன்னும் விளக்கம் இல்லை.", explain_make: "விளக்கம் உருவாக்கு", explain_again: "மீண்டும் உருவாக்கு",
  explain_working: "எழுதுகிறது…", explain_lang: "மொழி",
  explain_ta_note: "இந்தத் தமிழ் உரை AI மூலம் எழுதப்பட்டது. வாடிக்கையாளருக்குப் பகிரும் முன் சரிபார்க்கவும்.",
};

/** Tamil for the default checklist points, tools and net-metering documents (see backend services/projects.py).
 *  Text an installer has customised in Settings falls back to English. */
const TA_TEXT: Record<string, string> = {
  "Roof type (RCC / sheet / tile)": "கூரை வகை (RCC / ஷீட் / ஓடு)",
  "Shadow analysis (buildings, trees)": "நிழல் ஆய்வு (கட்டடங்கள், மரங்கள்)",
  "Orientation (south best)": "திசை (தெற்கு சிறந்தது)",
  "Tilt angle ~10-15° (Tamil Nadu)": "சாய்வுக் கோணம் ~10-15° (தமிழ்நாடு)",
  "Shadow-free area 9:00-16:00": "காலை 9 - மாலை 4 வரை நிழல் இல்லாத இடம்",
  "EB service type (1 / 3 phase)": "மின் இணைப்பு வகை (1 / 3 கட்டம்)",
  "Load and EB bill analysis": "சுமை மற்றும் மின் கட்டண ஆய்வு",
  "System size finalised": "அமைப்பின் அளவு இறுதி செய்யப்பட்டது",
  "Panel selection": "பேனல் தேர்வு",
  "Inverter selection": "இன்வெர்ட்டர் தேர்வு",
  "String calculation (Voc within limit)": "ஸ்ட்ரிங் கணக்கீடு (Voc வரம்புக்குள்)",
  "Mounting structure design": "தாங்கும் அமைப்பு வடிவமைப்பு",
  "Cable sizing (DC & AC)": "கேபிள் அளவு (DC & AC)",
  "Earthing & lightning plan": "எர்த்திங் & மின்னல் பாதுகாப்புத் திட்டம்",
  "Solar panels": "சோலார் பேனல்கள்",
  "Inverter": "இன்வெர்ட்டர்",
  "Mounting structure (GI/aluminium)": "தாங்கும் அமைப்பு (GI/அலுமினியம்)",
  "DC cable (4/6 sq mm)": "DC கேபிள் (4/6 ச.மி.மீ)",
  "AC cable": "AC கேபிள்",
  "MC4 connectors": "MC4 இணைப்பான்கள்",
  "DCDB & ACDB": "DCDB & ACDB",
  "Earthing kit": "எர்த்திங் கிட்",
  "Lightning arrester": "மின்னல் தடுப்பான்",
  "Cable trays / conduits": "கேபிள் தட்டுகள் / குழாய்கள்",
  "Mark layout as per design": "வடிவமைப்பின்படி அமைப்பைக் குறிக்கவும்",
  "Fix base (chemical anchor / clamp)": "அடித்தளம் பொருத்து (கெமிக்கல் ஆங்கர் / கிளாம்ப்)",
  "Align structure (tilt & direction)": "அமைப்பை சீரமை (சாய்வு & திசை)",
  "Tighten all bolts (torque check)": "எல்லா போல்ட்களையும் இறுக்கு (டார்க் சோதனை)",
  "Corrosion protection": "துரு பாதுகாப்பு",
  "Place panels carefully (no damage)": "பேனல்களைக் கவனமாக வை (சேதம் இல்லாமல்)",
  "Proper mid & end clamps": "சரியான மிட் & எண்ட் கிளாம்ப்கள்",
  "Maintain spacing for airflow": "காற்றோட்டத்துக்கு இடைவெளி விடு",
  "Label panel strings": "பேனல் ஸ்ட்ரிங்குகளுக்கு லேபிள் இடு",
  "Series connection (string formation)": "தொடர் இணைப்பு (ஸ்ட்ரிங் அமைத்தல்)",
  "Proper MC4 crimping": "சரியான MC4 கிரிம்பிங்",
  "Polarity check (+/-)": "துருவ சரிபார்ப்பு (+/-)",
  "Cable routing, no loose hanging": "கேபிள் வழி, தொங்காமல்",
  "DC cable in conduit / tray": "DC கேபிள் குழாய் / தட்டில்",
  "String voltage check (Voc test)": "ஸ்ட்ரிங் மின்னழுத்தச் சோதனை (Voc)",
  "Mount in shade / ventilated area": "நிழல் / காற்றோட்டமான இடத்தில் பொருத்து",
  "Clearance around inverter": "இன்வெர்ட்டரைச் சுற்றி இடைவெளி",
  "Connect DC input from strings": "ஸ்ட்ரிங்குகளிலிருந்து DC உள்ளீட்டை இணை",
  "Connect AC output to ACDB": "AC வெளியீட்டை ACDB-யுடன் இணை",
  "Earthing connection": "எர்த்திங் இணைப்பு",
  "DCDB installation (SPD + MCB/isolator)": "DCDB நிறுவல் (SPD + MCB/ஐசோலேட்டர்)",
  "ACDB installation (MCB + SPD)": "ACDB நிறுவல் (MCB + SPD)",
  "Proper earthing (min 2 pits)": "சரியான எர்த்திங் (குறைந்தது 2 குழிகள்)",
  "Lightning arrester (if needed)": "மின்னல் தடுப்பான் (தேவைப்பட்டால்)",
  "Panel earthing": "பேனல் எர்த்திங்",
  "Inverter earthing": "இன்வெர்ட்டர் எர்த்திங்",
  "Structure earthing": "அமைப்பு எர்த்திங்",
  "Earth resistance check (< 5 ohm)": "எர்த் மின்தடை சோதனை (< 5 ஓம்)",
  "String Voc measurement": "ஸ்ட்ரிங் Voc அளவீடு",
  "Polarity verification": "துருவ உறுதிப்படுத்தல்",
  "Continuity test": "தொடர்ச்சிச் சோதனை",
  "Insulation test (Megger)": "இன்சுலேஷன் சோதனை (மெகர்)",
  "Tightness check of all terminals": "எல்லா டெர்மினல்களின் இறுக்கச் சோதனை",
  "Turn ON DC isolator": "DC ஐசோலேட்டரை ஆன் செய்",
  "Turn ON inverter": "இன்வெர்ட்டரை ஆன் செய்",
  "Turn ON AC side": "AC பக்கத்தை ஆன் செய்",
  "Check inverter display": "இன்வெர்ட்டர் திரையைச் சரிபார்",
  "Verify generation data": "உற்பத்தித் தரவைச் சரிபார்",
  "Apply EB net meter": "மின் வாரிய நெட் மீட்டருக்கு விண்ணப்பி",
  "Documentation submission": "ஆவணங்கள் சமர்ப்பிப்பு",
  "System demo to customer": "வாடிக்கையாளருக்கு செயல்விளக்கம்",
  "Warranty & manuals": "உத்தரவாதம் & கையேடுகள்",
  "Explain monitoring app": "கண்காணிப்பு ஆப்பை விளக்கு",
  // tools
  "Screwdriver set": "ஸ்க்ரூடிரைவர் செட்", "Spanner / wrench set": "ஸ்பானர் / ரெஞ்ச் செட்",
  "Electric drill machine": "மின் டிரில் இயந்திரம்", "MC4 crimping tool": "MC4 கிரிம்பிங் கருவி",
  "Wire stripper": "வயர் ஸ்ட்ரிப்பர்", "Cable cutter": "கேபிள் கட்டர்", "Measuring tape": "அளவு நாடா",
  "Clamp meter": "கிளாம்ப் மீட்டர்", "Spirit level": "ஸ்பிரிட் லெவல்", "Hammer": "சுத்தியல்",
  "Safety tools (helmet, gloves, harness)": "பாதுகாப்புக் கருவிகள் (ஹெல்மெட், கையுறை, ஹார்னஸ்)",
  "Digital multimeter": "டிஜிட்டல் மல்டிமீட்டர்", "DC clamp meter": "DC கிளாம்ப் மீட்டர்",
  "Insulation tester (Megger)": "இன்சுலேஷன் டெஸ்டர் (மெகர்)", "Earth resistance tester": "எர்த் மின்தடை டெஸ்டர்",
  "Solar irradiance meter": "சூரிய ஒளிச்செறிவு மீட்டர்", "Non-contact voltage tester": "தொடாத மின்னழுத்த டெஸ்டர்",
  "MC4 spanner": "MC4 ஸ்பானர்",
  // net-metering documents
  "Form-1 net-metering connection application (with Rs 100 registration fee)": "படிவம்-1 நெட் மீட்டரிங் இணைப்பு விண்ணப்பம் (ரூ.100 பதிவுக் கட்டணத்துடன்)",
  "Copy of latest electricity bill (Annexure-II declaration)": "சமீபத்திய மின் கட்டண ரசீதின் நகல் (இணைப்பு-II உறுதிமொழி)",
  "Annexure-II declaration signed by consumer": "நுகர்வோர் கையொப்பமிட்ட இணைப்பு-II உறுதிமொழி",
  "Solar grid inverter make/type; confirmation of automatic isolation (anti-islanding) protection": "சோலார் கிரிட் இன்வெர்ட்டர் தயாரிப்பு/வகை; தானியங்கி துண்டிப்பு (ஆன்டி-ஐலண்டிங்) பாதுகாப்பு உறுதிப்படுத்தல்",
  "Single-line diagram of the SPV generator": "SPV ஜெனரேட்டரின் ஒற்றைக் கோட்டு வரைபடம்",
  "Specification sheets of all equipment (modules, inverter, protection)": "அனைத்து உபகரணங்களின் விவரக் குறிப்புகள் (பேனல்கள், இன்வெர்ட்டர், பாதுகாப்பு)",
  "Readiness intimation to Section Office after installation": "நிறுவலுக்குப் பின் பிரிவு அலுவலகத்துக்குத் தயார்நிலை அறிவிப்பு",
  "Safety inspection: AEE/O&M below 10 kW; Electrical Inspectorate (CEIG) for 10 kW and above": "பாதுகாப்பு ஆய்வு: 10 kW-க்குக் கீழ் AEE/O&M; 10 kW மற்றும் அதற்கு மேல் மின் ஆய்வகம் (CEIG)",
  "Form-2 net-metering connection agreement (signed)": "படிவம்-2 நெட் மீட்டரிங் இணைப்பு ஒப்பந்தம் (கையொப்பமிட்டது)",
  "Bi-directional meter (TANGEDCO approved), and solar generation meter if GBI is claimed": "இருவழி மீட்டர் (TANGEDCO அங்கீகரித்தது), GBI கோரினால் சோலார் உற்பத்தி மீட்டர்",
  "Caution stickers 'Solar PV Systems' and sign board near meter": "மீட்டர் அருகே 'Solar PV Systems' எச்சரிக்கை ஸ்டிக்கர்கள் மற்றும் அறிவிப்புப் பலகை",
  "Manual isolator with locking at ground floor; separate earthing and lightning arrester": "தரைத்தளத்தில் பூட்டுடன் கூடிய கைமுறை ஐசோலேட்டர்; தனி எர்த்திங் மற்றும் மின்னல் தடுப்பான்",
};

export function useAdminI18n() {
  const { lang, setLang } = useI18n();
  const dict = lang === "ta" ? ta : en;
  const at = (k: AKey, vars?: Record<string, string | number>) => {
    let s = dict[k] ?? en[k];
    if (vars) for (const [n, v] of Object.entries(vars)) s = s.replace(`{${n}}`, String(v));
    return s;
  };
  /** Translate a data string (checklist point, tool, document) if a Tamil version is known. */
  const tx = (s: string) => (lang === "ta" && TA_TEXT[s]) || s;
  return { lang, setLang, at, tx };
}

export type { AKey, Lang };
