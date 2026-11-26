// Copy for the public marketing pages added on 2026-11-26 (English + Tamil):
// Home, Residential, Commercial, Industrial, Systems & Products, Savings Calculator,
// How It Works and Our Projects. Edit text here; no code changes needed elsewhere.
// Use {name} for the installer's company name.
// Tamil wording should be reviewed by a native speaker before launch.
//
// IMPORTANT: no prices here. Customers never see a price automatically; the engineer sends a
// quotation after reviewing the bill and roof (see CLAUDE.md).
import type { Lang } from "./i18n";

export type Card = { icon: string; title: string; text: string };
export type QA = { q: string; a: string };
export type SolutionKey = "residential" | "commercial" | "industrial";

export type Solution = {
  eyebrow: string;
  title: string;
  lead: string;
  image: string;
  idealTitle: string;
  ideal: string[];
  benefitsTitle: string;
  benefits: Card[];
  sizesTitle: string;
  sizesLead: string;
  sizes: { label: string; value: string }[];
  pointsTitle: string;
  points: string[];
  calcTitle: string;
  faq: QA[];
};

export type Project = {
  title: string;
  location: string;
  type: "residential" | "commercial" | "industrial";
  capacity: string;        // e.g. "5 kW"
  system: string;          // e.g. "On-grid with net metering"
  image: string;           // put photos in frontend/public/img/projects/
  result?: string;         // a saving the customer has confirmed, e.g. "Bill down from ₹4,200 to ₹600"
  year?: string;
  sample?: boolean;        // sample entries show only in `npm run dev`, never in the live build
};

export type SiteContent = {
  nav: {
    solutions: string; residential: string; commercial: string; industrial: string; products: string;
    calculator: string; how: string; projects: string; about: string; quote: string; survey: string; menu: string;
  };
  common: {
    explore: string; freeSurvey: string; faqTitle: string; readyTitle: string; readyText: string;
    callUs: string; viewAll: string; noPrice: string;
  };
  home: {
    badge: string; title: string; titleHi: string; lead: string; ctaHow: string;
    trust: { icon: string; title: string }[];
    solEyebrow: string; solTitle: string; solLead: string;
    solutions: { key: string; icon: string; title: string; text: string; image: string }[];
    calcEyebrow: string; calcTitle: string;
    stepsEyebrow: string; stepsTitle: string;
    whyEyebrow: string; whyTitle: string;
    projectsTitle: string; projectsLead: string;
  };
  calc: {
    eyebrow: string; title: string; lead: string;
    byBill: string; byUnits: string; billLabel: string; unitsLabel: string;
    siteType: string; home: string; commercial: string; industry: string;
    phase: string; single: string; three: string;
    system: string; onGrid: string; hybrid: string;
    submit: string; working: string; error: string;
    resultsTitle: string; emptyHint: string;
    size: string; panels: string; roof: string; generation: string;
    monthlySaving: string; annualSaving: string; unitsFromBill: string; unitsMonth: string;
    note: string; cta: string;
    notes: Record<string, string>;
    howTitle: string; how: string[];
  };
  solutions: Record<SolutionKey, Solution>;
  products: {
    eyebrow: string; title: string; lead: string;
    typesTitle: string;
    types: { icon: string; title: string; text: string; best: string; points: string[] }[];
    bestFor: string;
    partsTitle: string; partsLead: string;
    parts: Card[];
    compareTitle: string;
    compareHead: string[];
    compareRows: string[][];
    note: string;
  };
  how: {
    eyebrow: string; title: string; lead: string;
    steps: { icon: string; title: string; text: string; points: string[]; time: string }[];
    flowTitle: string;
    readyTitle: string; ready: string[];
    afterTitle: string; after: Card[];
  };
  projects: {
    eyebrow: string; title: string; lead: string;
    all: string; filters: Record<Project["type"], string>;
    capacity: string; system: string; result: string;
    empty: string; sampleTag: string;
    items: Project[];
  };
  footer: { tagline: string; explore: string; company: string; contact: string; rights: string };
};

const en: SiteContent = {
  nav: {
    solutions: "Solutions", residential: "Residential solar", commercial: "Commercial solar",
    industrial: "Industrial solar", products: "Systems & products", calculator: "Savings calculator",
    how: "How it works", projects: "Projects", about: "About", quote: "Get a free site survey",
    survey: "Free site survey", menu: "Menu",
  },
  common: {
    explore: "Explore", freeSurvey: "Get a free site survey", faqTitle: "Common questions",
    readyTitle: "Ready to go solar?",
    readyText: "Send your EB bill and a few roof photos. Our engineer reviews them and sends a quotation made for your building.",
    callUs: "Call us", viewAll: "View all projects",
    noPrice: "We do not show automatic prices. Your quotation is prepared by an engineer after reviewing your bill and roof, and confirmed after a site visit.",
  },
  home: {
    badge: "Rooftop solar for homes, businesses and industries",
    title: "Power your building with clean,",
    titleHi: "reliable solar energy",
    lead: "Lower your electricity bills, gain energy independence and build a greener future, with a system designed for your roof and your bill.",
    ctaHow: "See how it works",
    trust: [
      { icon: "rupee", title: "Lower electricity bills" },
      { icon: "leaf", title: "Clean, green energy" },
      { icon: "shield", title: "Long-life panels" },
      { icon: "wrench", title: "End-to-end service" },
      { icon: "bolt", title: "Safe installation" },
    ],
    solEyebrow: "Our solar solutions",
    solTitle: "Find the right solar solution for you",
    solLead: "Systems for homes, businesses and industries, with support from survey to net metering.",
    solutions: [
      { key: "residential", icon: "home", title: "Residential solar", text: "Bring down your home electricity bill with a rooftop system sized to your usage.", image: "/img/residential.jpg" },
      { key: "commercial", icon: "building", title: "Commercial solar", text: "Lower operating costs for offices, schools, hospitals, hotels and shops.", image: "/img/commercial.jpg" },
      { key: "industrial", icon: "factory", title: "Industrial solar", text: "High-capacity, reliable plants for factories and warehouses.", image: "/img/industrial.jpg" },
      { key: "products", icon: "battery", title: "Hybrid & battery", text: "Solar with battery backup, so chosen loads keep running in power cuts.", image: "/img/hybrid-battery.jpg" },
    ],
    calcEyebrow: "Solar savings calculator",
    calcTitle: "See how much you could save",
    stepsEyebrow: "How it works",
    stepsTitle: "Your solar journey in simple steps",
    whyEyebrow: "Why solar",
    whyTitle: "How solar helps you",
    projectsTitle: "Recent projects",
    projectsLead: "A look at some of our completed installations.",
  },
  calc: {
    eyebrow: "Solar savings calculator",
    title: "Estimate your solar system and savings",
    lead: "Enter your monthly EB bill or units. We use our current tariff and generation settings to suggest a system size and an indicative savings range.",
    byBill: "Monthly bill (₹)", byUnits: "Monthly units (kWh)",
    billLabel: "Average monthly bill (₹)", unitsLabel: "Average monthly units (kWh)",
    siteType: "Building type", home: "Home", commercial: "Shop / office / institution", industry: "Industry",
    phase: "Supply", single: "Single phase", three: "Three phase",
    system: "System type", onGrid: "On-grid (net metering)", hybrid: "Hybrid (with battery)",
    submit: "Calculate savings", working: "Calculating…", error: "Could not calculate right now. Please try again.",
    resultsTitle: "Your estimated savings",
    emptyHint: "Enter your bill and press Calculate to see a recommended system size and savings range.",
    size: "Recommended system", panels: "panels", roof: "Shade-free roof needed",
    generation: "Expected generation", monthlySaving: "Monthly savings", annualSaving: "Annual savings",
    unitsFromBill: "Worked out from your bill: about {u} units a month",
    unitsMonth: "units / month",
    note: "Indicative estimate only. Actual savings depend on your roof, shade, tariff and usage. Your price is prepared by our engineer and confirmed after a site visit.",
    cta: "Get a detailed quotation",
    notes: {
      SANCTION_LOAD_CAP: "Your sanctioned load may limit the system size; a load enhancement may be needed.",
      CEIG_INSPECTION: "A system of this size needs a safety inspection by the Electrical Inspectorate (CEIG). We handle the paperwork.",
      HT_CONNECTION: "A plant of this size connects at high tension (HT). Our engineer will discuss the options with you.",
      NO_HYBRID_INVERTER: "Hybrid sizing needs a site survey; the figures shown are for an on-grid system.",
    },
    howTitle: "How we estimate",
    how: [
      "If you enter a bill, we work out your monthly units from the current tariff slabs.",
      "We size the system so it covers your usage, based on typical generation in Tamil Nadu.",
      "Savings are shown as a range (cloudier and sunnier years), after network charges.",
      "Shade, roof direction and your sanctioned load are checked at the site survey.",
    ],
  },
  solutions: {
    residential: {
      eyebrow: "Residential solar",
      title: "Rooftop solar for your home",
      lead: "For individual houses, villas and apartment terraces. Use your own solar power during the day, send the surplus to the grid through net metering, and watch your EB bill come down.",
      image: "/img/residential.jpg",
      idealTitle: "Ideal for",
      ideal: ["Independent houses", "Villas", "Apartment terraces (with association approval)", "Single-phase and three-phase homes", "Homes with frequent power cuts (hybrid)"],
      benefitsTitle: "What you get",
      benefits: [
        { icon: "rupee", title: "A much smaller EB bill", text: "Every unit your roof makes is a unit you do not buy. Most homes cover most of their daytime use." },
        { icon: "meter", title: "Net metering", text: "Surplus power is exported and adjusted in your bill. We help with the TANGEDCO application." },
        { icon: "battery", title: "Backup if you want it", text: "Add batteries with a hybrid inverter to keep lights, fans and the fridge running in power cuts." },
        { icon: "wifi", title: "Track it on your phone", text: "Most inverters have an app that shows today's generation and your savings." },
        { icon: "shield", title: "Safe, tidy installation", text: "Proper earthing, surge protection and neat cable routing on your terrace." },
        { icon: "clock", title: "Long life", text: "Panels usually carry a long performance warranty, often 25 years; details are in your quotation." },
      ],
      sizesTitle: "Typical home system sizes",
      sizesLead: "A rough guide only. Your system is sized from your actual bill.",
      sizes: [
        { label: "Up to ~150 units a month", value: "1 – 2 kW" },
        { label: "~150 – 350 units a month", value: "2 – 3 kW" },
        { label: "~350 – 550 units a month", value: "3 – 5 kW" },
        { label: "Above ~550 units a month", value: "5 – 10 kW" },
      ],
      pointsTitle: "What decides your price",
      points: [
        "System size (kW) and the panel and inverter models you choose",
        "Roof type and height: RCC terrace, sheet or tile, and the structure needed",
        "Cable run from roof to meter and the protection devices required",
        "On-grid or hybrid, and the battery size if you want backup",
      ],
      calcTitle: "Estimate savings for your home",
      faq: [
        { q: "How much roof space do I need?", a: "Roughly 9 to 10 sq m (about 100 sq ft) of shade-free area for each kW. A 3 kW system needs around 30 sq m." },
        { q: "Can I install solar on an apartment terrace?", a: "Yes, usually with written approval from the association, and the system is connected to your own meter. We help you check what is possible." },
        { q: "Will an on-grid system work in a power cut?", a: "No. For safety it switches off when the grid fails. Choose a hybrid system with batteries if you need backup." },
        { q: "How long does installation take?", a: "Installation on site usually takes one to three days for a home. Net-meter approval by TANGEDCO takes longer and varies." },
      ],
    },
    commercial: {
      eyebrow: "Commercial solar",
      title: "Solar for offices, schools, hospitals and shops",
      lead: "Businesses and institutions use most of their power during the day, exactly when solar produces it. That makes rooftop solar one of the most effective ways to cut operating costs.",
      image: "/img/commercial.jpg",
      idealTitle: "Ideal for",
      ideal: ["Offices and IT parks", "Schools and colleges", "Hospitals and clinics", "Hotels and restaurants", "Shops and showrooms", "Places of worship and community halls"],
      benefitsTitle: "Why it works for business",
      benefits: [
        { icon: "chart", title: "Lower operating costs", text: "Daytime consumption is matched directly by solar, so savings start from the first billing cycle." },
        { icon: "rupee", title: "Higher tariffs, bigger savings", text: "Commercial tariffs are higher than domestic, so each solar unit is worth more to you." },
        { icon: "leaf", title: "Sustainability goals", text: "Show customers, students and patients a visible commitment to clean energy." },
        { icon: "clipboard", title: "Clear business case", text: "Your quotation includes expected generation and savings so you can plan the investment." },
        { icon: "wifi", title: "Remote monitoring", text: "Track generation across your sites from one app or web dashboard." },
        { icon: "wrench", title: "Low upkeep", text: "Periodic cleaning and a yearly check, with service support when you need it." },
      ],
      sizesTitle: "Typical commercial system sizes",
      sizesLead: "Sized from your daytime load and roof area during the survey.",
      sizes: [
        { label: "Shops, clinics, small offices", value: "3 – 15 kW" },
        { label: "Schools, hotels, mid-size offices", value: "15 – 50 kW" },
        { label: "Hospitals, colleges, large buildings", value: "50 – 150 kW+" },
      ],
      pointsTitle: "Your business case, explained",
      points: [
        "Expected monthly generation and units offset, from your actual bills",
        "Indicative savings range per year, after network charges",
        "Approvals needed for your size (net metering, CEIG inspection for larger plants)",
        "A clear, itemised quotation with GST shown line by line",
      ],
      calcTitle: "Estimate savings for your business",
      faq: [
        { q: "Do commercial buildings get net metering?", a: "Rooftop systems on commercial LT connections can be connected under the TANGEDCO scheme that applies to your category and size. We confirm the right route for you." },
        { q: "Will it disturb our working hours?", a: "We plan the work to keep disruption low. The final connection usually needs a short, scheduled shutdown." },
        { q: "Can we install on a sheet roof?", a: "Yes. We use a mounting structure suited to metal sheet roofs and check the roof condition first." },
        { q: "How do we get an ROI figure?", a: "Share your recent bills. Your quotation shows the investment, expected savings and the payback period for your building." },
      ],
    },
    industrial: {
      eyebrow: "Industrial solar",
      title: "High-capacity solar for factories and warehouses",
      lead: "Large roofs and steady daytime loads make industrial units ideal for solar. We design multi-inverter, three-phase plants with the protection, approvals and documentation a bigger installation needs.",
      image: "/img/industrial.jpg",
      idealTitle: "Ideal for",
      ideal: ["Manufacturing units", "Warehouses and logistics hubs", "Textile, food processing and engineering units", "Cold storage", "Industrial estates and SIDCO units"],
      benefitsTitle: "Built for industry",
      benefits: [
        { icon: "factory", title: "Large-scale design", text: "Several three-phase inverters, string design and cable sizing done properly for big arrays." },
        { icon: "rupee", title: "Big savings on high tariffs", text: "Industrial power is expensive; offsetting daytime units has a direct effect on your costs." },
        { icon: "shield", title: "Protection and safety", text: "AC/DC protection, surge devices, earthing and lightning protection to the required standards." },
        { icon: "doc", title: "Approvals handled", text: "We prepare documents for net metering and the Electrical Inspectorate (CEIG) safety inspection where required." },
        { icon: "wifi", title: "Plant monitoring", text: "Per-inverter generation data and alerts so you spot problems early." },
        { icon: "wrench", title: "Operation and maintenance", text: "Scheduled cleaning, inspection and performance checks to keep yield high." },
      ],
      sizesTitle: "Typical industrial plant sizes",
      sizesLead: "Sized from your load profile, roof area and connection type.",
      sizes: [
        { label: "Small units and workshops", value: "10 – 50 kW" },
        { label: "Medium factories and warehouses", value: "50 – 112 kW" },
        { label: "Large plants (HT connections)", value: "Above 112 kW" },
      ],
      pointsTitle: "What we take care of",
      points: [
        "Roof survey, structural check and shadow analysis",
        "Inverter and string design for three-phase supply",
        "Cable, ACDB/DCDB and protection schedule",
        "CEIG inspection and net-metering documents where applicable",
        "Testing, commissioning and a complete project pack with drawings",
      ],
      calcTitle: "Estimate savings for your plant",
      faq: [
        { q: "Is there a size limit?", a: "LT connections have limits. Larger plants connect at high tension (HT) with different metering rules. Our engineer explains what applies to your connection." },
        { q: "Do we need an inspection?", a: "Larger systems need a safety inspection by the Electrical Inspectorate (CEIG). We prepare the documents and attend the inspection." },
        { q: "Can work happen while production runs?", a: "Most work is on the roof. We schedule the final interconnection with your maintenance team to keep downtime short." },
        { q: "What about roof strength?", a: "We check the roof and structure during the survey and design the mounting to suit it." },
      ],
    },
  },
  products: {
    eyebrow: "Systems & products",
    title: "Solar systems and the products inside them",
    lead: "On-grid, off-grid and hybrid systems built from quality panels, inverters, batteries, structures and protection devices. Your quotation lists every model and its warranty.",
    typesTitle: "Choose your system type",
    bestFor: "Best for",
    types: [
      { icon: "plug", title: "On-grid", text: "Connected to the grid with a net meter. No batteries.", best: "Lowering bills at the lowest investment",
        points: ["Most economical option", "Surplus exported through net metering", "Switches off in a grid power cut (safety rule)"] },
      { icon: "battery", title: "Hybrid", text: "Grid-connected, with batteries for backup.", best: "Lower bills plus backup in power cuts",
        points: ["Keeps chosen loads running in cuts", "Uses solar first, then battery, then grid", "Battery sized to your backup needs"] },
      { icon: "sun", title: "Off-grid", text: "Panels, batteries and inverter with no grid connection.", best: "Farms, remote sites, no reliable supply",
        points: ["Works without the grid", "Battery bank sized for your loads", "Ideal for pumps, farmhouses and remote sites"] },
    ],
    partsTitle: "What goes into a system",
    partsLead: "We use products from established manufacturers. Exact makes, models and warranties are listed in your quotation.",
    parts: [
      { icon: "panel", title: "Solar panels", text: "High-efficiency mono PERC, TOPCon or bifacial modules with long performance warranties." },
      { icon: "inverter", title: "Inverters", text: "On-grid string inverters, and hybrid inverters with battery charging and backup output." },
      { icon: "battery", title: "Batteries", text: "Lithium (LFP) for long life and deep cycling, or lead-acid where budget matters most." },
      { icon: "ruler", title: "Mounting structure", text: "Hot-dip galvanised or aluminium structures for RCC, sheet and tile roofs." },
      { icon: "shield", title: "Protection", text: "ACDB and DCDB with surge protection, fuses, MCBs, earthing and lightning arrestors." },
      { icon: "wifi", title: "Monitoring", text: "Wi-Fi or GSM monitoring so you can see generation on your phone." },
    ],
    compareTitle: "Quick comparison",
    compareHead: ["", "On-grid", "Hybrid", "Off-grid"],
    compareRows: [
      ["Grid connection", "Yes", "Yes", "No"],
      ["Batteries", "No", "Yes", "Yes"],
      ["Works in a power cut", "No", "Yes (chosen loads)", "Yes"],
      ["Net metering", "Yes", "Yes", "No"],
      ["Relative investment", "Lowest", "Higher", "Higher"],
    ],
    note: "Not sure which one fits? Tell us how you use power and whether you need backup; our engineer will recommend the right system.",
  },
  how: {
    eyebrow: "How it works",
    title: "From first call to switching on",
    lead: "A clear, step-by-step process, so you always know what happens next.",
    steps: [
      { icon: "phone", title: "Free consultation", text: "Tell us about your building and share your EB bill.", time: "Day 1",
        points: ["Online request or a phone call", "We understand your usage and goals", "Bill and roof photos uploaded online"] },
      { icon: "ruler", title: "Site survey", text: "Our team visits to check your roof and wiring.", time: "Within a few days",
        points: ["Roof area, direction and shade", "Structure and cable route", "Meter, phase and sanctioned load"] },
      { icon: "clipboard", title: "System design & quotation", text: "We design the system and send an itemised quotation.", time: "After the survey",
        points: ["Right system size for your bill", "Single-line diagram and roof layout", "Expected generation and savings"] },
      { icon: "wrench", title: "Installation", text: "Structure, panels, inverter and protection installed by our team.", time: "1–3 days for most homes",
        points: ["Safe work on the roof", "Neat, labelled cable routing", "Earthing and surge protection"] },
      { icon: "doc", title: "Approvals", text: "Net-metering application and inspections where required.", time: "Depends on TANGEDCO",
        points: ["Documents prepared for you", "CEIG inspection for larger plants", "We follow up until the meter is fixed"] },
      { icon: "bolt", title: "Commissioning & handover", text: "Testing, switch-on and a demonstration.", time: "Go solar",
        points: ["Voltage, earth and insulation tests", "Monitoring app set up", "Warranty papers and manuals handed over"] },
    ],
    flowTitle: "How your solar system powers your building",
    readyTitle: "Keep these ready",
    ready: ["A recent EB bill (photo or PDF)", "Photos of your roof or terrace", "Your EB consumer number", "Rough roof size, if you know it"],
    afterTitle: "After installation",
    after: [
      { icon: "wifi", title: "Monitoring", text: "Watch your generation every day on the inverter app." },
      { icon: "wrench", title: "Service support", text: "Call us for questions, cleaning advice or a service visit." },
      { icon: "shield", title: "Warranty", text: "Product warranties as stated in your quotation and handover papers." },
    ],
  },
  projects: {
    eyebrow: "Our projects",
    title: "Completed installations",
    lead: "Rooftop systems we have designed and installed for homes, businesses and industries.",
    all: "All",
    filters: { residential: "Residential", commercial: "Commercial", industrial: "Industrial" },
    capacity: "Capacity", system: "System", result: "Customer-reported result",
    empty: "Project photos are being added. Ask us for references near you.",
    sampleTag: "Sample (dev only)",
    // Add real projects here. Only add a "result" the customer has confirmed.
    items: [
      { title: "Independent house", location: "Sample location", type: "residential", capacity: "3 kW", system: "On-grid with net metering", image: "/img/residential.jpg", sample: true },
      { title: "Hospital campus", location: "Sample location", type: "commercial", capacity: "50 kW", system: "On-grid", image: "/img/commercial.jpg", sample: true },
      { title: "Manufacturing unit", location: "Sample location", type: "industrial", capacity: "300 kW", system: "On-grid, multi-inverter", image: "/img/industrial.jpg", sample: true },
      { title: "Home with backup", location: "Sample location", type: "residential", capacity: "5 kW + 10 kWh", system: "Hybrid with lithium battery", image: "/img/hybrid-battery.jpg", sample: true },
    ],
  },
  footer: {
    tagline: "Rooftop solar for homes, businesses and industries in Tamil Nadu.",
    explore: "Explore", company: "Company", contact: "Contact", rights: "All rights reserved.",
  },
};

const ta: SiteContent = {
  nav: {
    solutions: "தீர்வுகள்", residential: "வீட்டு சோலார்", commercial: "வணிக சோலார்",
    industrial: "தொழிற்சாலை சோலார்", products: "அமைப்புகள் & பொருட்கள்", calculator: "சேமிப்பு கணிப்பான்",
    how: "எப்படி செயல்படுகிறது", projects: "திட்டங்கள்", about: "எங்களைப் பற்றி", quote: "இலவச தள ஆய்வு பெற",
    survey: "இலவச தள ஆய்வு", menu: "மெனு",
  },
  common: {
    explore: "மேலும் அறிய", freeSurvey: "இலவச தள ஆய்வு பெற", faqTitle: "பொதுவான கேள்விகள்",
    readyTitle: "சோலாருக்கு மாறத் தயாரா?",
    readyText: "உங்கள் மின் கட்டண ரசீதையும் சில கூரை புகைப்படங்களையும் அனுப்புங்கள். எங்கள் பொறியாளர் பரிசீலித்து உங்கள் கட்டடத்துக்கான விலைப்புள்ளியை அனுப்புவார்.",
    callUs: "அழையுங்கள்", viewAll: "அனைத்து திட்டங்களும்",
    noPrice: "நாங்கள் தானியங்கி விலையைக் காட்டுவதில்லை. உங்கள் ரசீதையும் கூரையையும் பரிசீலித்த பின் பொறியாளர் விலைப்புள்ளி தயாரிப்பார்; தள ஆய்வுக்குப் பின் உறுதிசெய்யப்படும்.",
  },
  home: {
    badge: "வீடுகள், தொழில்கள், தொழிற்சாலைகளுக்கான கூரை சோலார்",
    title: "உங்கள் கட்டடத்துக்கு சுத்தமான,",
    titleHi: "நம்பகமான சூரிய மின்சாரம்",
    lead: "உங்கள் கூரைக்கும் மின் கட்டணத்துக்கும் ஏற்ப வடிவமைத்த அமைப்புடன் மின் கட்டணத்தைக் குறைத்து, ஆற்றல் சுதந்திரம் பெற்று, பசுமையான எதிர்காலத்தை உருவாக்குங்கள்.",
    ctaHow: "எப்படி செயல்படுகிறது",
    trust: [
      { icon: "rupee", title: "குறைந்த மின் கட்டணம்" },
      { icon: "leaf", title: "சுத்தமான பசுமை ஆற்றல்" },
      { icon: "shield", title: "நீண்ட ஆயுள் பேனல்கள்" },
      { icon: "wrench", title: "முழுமையான சேவை" },
      { icon: "bolt", title: "பாதுகாப்பான நிறுவல்" },
    ],
    solEyebrow: "எங்கள் சோலார் தீர்வுகள்",
    solTitle: "உங்களுக்கு ஏற்ற சோலார் தீர்வைக் கண்டறியுங்கள்",
    solLead: "வீடுகள், தொழில்கள், தொழிற்சாலைகளுக்கான அமைப்புகள்; தள ஆய்வு முதல் நெட் மீட்டரிங் வரை உதவி.",
    solutions: [
      { key: "residential", icon: "home", title: "வீட்டு சோலார்", text: "உங்கள் பயன்பாட்டுக்கு ஏற்ற கூரை அமைப்புடன் வீட்டு மின் கட்டணத்தைக் குறையுங்கள்.", image: "/img/residential.jpg" },
      { key: "commercial", icon: "building", title: "வணிக சோலார்", text: "அலுவலகங்கள், பள்ளிகள், மருத்துவமனைகள், ஹோட்டல்கள், கடைகளுக்கு இயக்கச் செலவு குறைவு.", image: "/img/commercial.jpg" },
      { key: "industrial", icon: "factory", title: "தொழிற்சாலை சோலார்", text: "தொழிற்சாலைகள், கிடங்குகளுக்கான அதிக திறன் கொண்ட நம்பகமான ஆலைகள்.", image: "/img/industrial.jpg" },
      { key: "products", icon: "battery", title: "ஹைப்ரிட் & பேட்டரி", text: "பேட்டரி பேக்அப்புடன் சோலார்; மின்தடையிலும் தேர்ந்தெடுத்த சுமைகள் இயங்கும்.", image: "/img/hybrid-battery.jpg" },
    ],
    calcEyebrow: "சோலார் சேமிப்பு கணிப்பான்",
    calcTitle: "எவ்வளவு சேமிக்கலாம் என்று பாருங்கள்",
    stepsEyebrow: "எப்படி செயல்படுகிறது",
    stepsTitle: "எளிய படிகளில் உங்கள் சோலார் பயணம்",
    whyEyebrow: "ஏன் சோலார்",
    whyTitle: "சோலார் உங்களுக்கு எப்படிப் பயன்படும்",
    projectsTitle: "சமீபத்திய திட்டங்கள்",
    projectsLead: "நாங்கள் முடித்த சில நிறுவல்கள்.",
  },
  calc: {
    eyebrow: "சோலார் சேமிப்பு கணிப்பான்",
    title: "உங்கள் சோலார் அமைப்பையும் சேமிப்பையும் கணக்கிடுங்கள்",
    lead: "உங்கள் மாத மின் கட்டணம் அல்லது யூனிட்களை உள்ளிடுங்கள். தற்போதைய கட்டண மற்றும் உற்பத்தி அமைப்புகளைக் கொண்டு அமைப்பின் அளவையும் தோராயமான சேமிப்பு வரம்பையும் பரிந்துரைக்கிறோம்.",
    byBill: "மாதக் கட்டணம் (₹)", byUnits: "மாத யூனிட்கள் (kWh)",
    billLabel: "சராசரி மாதக் கட்டணம் (₹)", unitsLabel: "சராசரி மாத யூனிட்கள் (kWh)",
    siteType: "கட்டட வகை", home: "வீடு", commercial: "கடை / அலுவலகம் / நிறுவனம்", industry: "தொழிற்சாலை",
    phase: "மின் இணைப்பு", single: "ஒற்றை கட்டம்", three: "மூன்று கட்டம்",
    system: "அமைப்பு வகை", onGrid: "ஆன்-கிரிட் (நெட் மீட்டரிங்)", hybrid: "ஹைப்ரிட் (பேட்டரியுடன்)",
    submit: "சேமிப்பைக் கணக்கிடு", working: "கணக்கிடுகிறது…", error: "இப்போது கணக்கிட முடியவில்லை. மீண்டும் முயற்சிக்கவும்.",
    resultsTitle: "உங்கள் மதிப்பிடப்பட்ட சேமிப்பு",
    emptyHint: "பரிந்துரைக்கப்பட்ட அமைப்பு அளவையும் சேமிப்பு வரம்பையும் பார்க்க உங்கள் கட்டணத்தை உள்ளிட்டு கணக்கிடு அழுத்தவும்.",
    size: "பரிந்துரைக்கப்பட்ட அமைப்பு", panels: "பேனல்கள்", roof: "தேவையான நிழலில்லா கூரை",
    generation: "எதிர்பார்க்கும் உற்பத்தி", monthlySaving: "மாத சேமிப்பு", annualSaving: "ஆண்டு சேமிப்பு",
    unitsFromBill: "உங்கள் கட்டணத்திலிருந்து: மாதம் சுமார் {u} யூனிட்கள்",
    unitsMonth: "யூனிட் / மாதம்",
    note: "இது தோராயமான மதிப்பீடு மட்டுமே. உண்மையான சேமிப்பு உங்கள் கூரை, நிழல், கட்டண வகை, பயன்பாட்டைப் பொறுத்தது. விலையை எங்கள் பொறியாளர் தயாரிப்பார்; தள ஆய்வுக்குப் பின் உறுதிசெய்யப்படும்.",
    cta: "விரிவான விலைப்புள்ளி பெற",
    notes: {
      SANCTION_LOAD_CAP: "உங்கள் அனுமதிக்கப்பட்ட சுமை அமைப்பின் அளவைக் கட்டுப்படுத்தலாம்; சுமை உயர்வு விண்ணப்பம் தேவைப்படலாம்.",
      CEIG_INSPECTION: "இந்த அளவு அமைப்புக்கு மின் ஆய்வகத்தின் (CEIG) பாதுகாப்பு ஆய்வு தேவை. ஆவணங்களை நாங்கள் கவனிப்போம்.",
      HT_CONNECTION: "இந்த அளவு ஆலை உயர் மின்னழுத்த (HT) இணைப்பில் இணையும். எங்கள் பொறியாளர் விருப்பங்களை விளக்குவார்.",
      NO_HYBRID_INVERTER: "ஹைப்ரிட் அளவீட்டுக்கு தள ஆய்வு தேவை; காட்டப்படும் எண்கள் ஆன்-கிரிட் அமைப்புக்கானவை.",
    },
    howTitle: "நாங்கள் எப்படி மதிப்பிடுகிறோம்",
    how: [
      "கட்டணத்தை உள்ளிட்டால், தற்போதைய கட்டணப் படிநிலைகளைக் கொண்டு மாத யூனிட்களைக் கணக்கிடுகிறோம்.",
      "தமிழ்நாட்டின் வழக்கமான உற்பத்தியின் அடிப்படையில் உங்கள் பயன்பாட்டை ஈடுசெய்யும் அளவில் அமைப்பை வடிவமைக்கிறோம்.",
      "நெட்வொர்க் கட்டணங்களுக்குப் பின் சேமிப்பு ஒரு வரம்பாகக் காட்டப்படும்.",
      "நிழல், கூரை திசை, அனுமதிக்கப்பட்ட சுமை ஆகியவை தள ஆய்வில் சரிபார்க்கப்படும்.",
    ],
  },
  solutions: {
    residential: {
      eyebrow: "வீட்டு சோலார்",
      title: "உங்கள் வீட்டுக்கான கூரை சோலார்",
      lead: "தனி வீடுகள், வில்லாக்கள், அடுக்குமாடி மொட்டைமாடிகளுக்கு. பகலில் உங்கள் சோலார் மின்சாரத்தைப் பயன்படுத்தி, மிகையை நெட் மீட்டரிங் மூலம் கிரிட்டுக்கு அனுப்புங்கள்; மின் கட்டணம் குறைவதைப் பாருங்கள்.",
      image: "/img/residential.jpg",
      idealTitle: "யாருக்கு ஏற்றது",
      ideal: ["தனி வீடுகள்", "வில்லாக்கள்", "அடுக்குமாடி மொட்டைமாடிகள் (சங்க அனுமதியுடன்)", "ஒற்றை மற்றும் மூன்று கட்ட வீடுகள்", "அடிக்கடி மின்தடை உள்ள வீடுகள் (ஹைப்ரிட்)"],
      benefitsTitle: "உங்களுக்குக் கிடைப்பது",
      benefits: [
        { icon: "rupee", title: "மிகக் குறைந்த மின் கட்டணம்", text: "உங்கள் கூரை தயாரிக்கும் ஒவ்வொரு யூனிட்டையும் வாங்க வேண்டியதில்லை. பெரும்பாலான வீடுகள் பகல் பயன்பாட்டின் பெரும்பகுதியை ஈடுசெய்கின்றன." },
        { icon: "meter", title: "நெட் மீட்டரிங்", text: "மிகை மின்சாரம் ஏற்றுமதியாகி உங்கள் கட்டணத்தில் சரிசெய்யப்படும். TANGEDCO விண்ணப்பத்தில் உதவுகிறோம்." },
        { icon: "battery", title: "தேவைப்பட்டால் பேக்அப்", text: "ஹைப்ரிட் இன்வெர்ட்டருடன் பேட்டரி சேர்த்தால் மின்தடையில் விளக்கு, மின்விசிறி, ஃப்ரிட்ஜ் இயங்கும்." },
        { icon: "wifi", title: "போனில் கண்காணிக்கலாம்", text: "பெரும்பாலான இன்வெர்ட்டர்களுக்கு இன்றைய உற்பத்தியைக் காட்டும் ஆப் உண்டு." },
        { icon: "shield", title: "பாதுகாப்பான, நேர்த்தியான நிறுவல்", text: "சரியான எர்த்திங், சர்ஜ் பாதுகாப்பு, மொட்டைமாடியில் நேர்த்தியான கேபிள் வழி." },
        { icon: "clock", title: "நீண்ட ஆயுள்", text: "பேனல்களுக்கு பொதுவாக நீண்ட செயல்திறன் உத்தரவாதம், பெரும்பாலும் 25 ஆண்டுகள்; விவரம் விலைப்புள்ளியில்." },
      ],
      sizesTitle: "வழக்கமான வீட்டு அமைப்பு அளவுகள்",
      sizesLead: "தோராய வழிகாட்டி மட்டுமே. உங்கள் உண்மையான கட்டணத்திலிருந்து அளவு முடிவு செய்யப்படும்.",
      sizes: [
        { label: "மாதம் ~150 யூனிட் வரை", value: "1 – 2 kW" },
        { label: "மாதம் ~150 – 350 யூனிட்", value: "2 – 3 kW" },
        { label: "மாதம் ~350 – 550 யூனிட்", value: "3 – 5 kW" },
        { label: "மாதம் ~550 யூனிட்டுக்கு மேல்", value: "5 – 10 kW" },
      ],
      pointsTitle: "உங்கள் விலையை எது தீர்மானிக்கிறது",
      points: [
        "அமைப்பின் அளவு (kW) மற்றும் நீங்கள் தேர்ந்தெடுக்கும் பேனல், இன்வெர்ட்டர் மாடல்கள்",
        "கூரை வகை, உயரம்: RCC, ஷீட் அல்லது ஓடு, தேவையான தாங்கும் அமைப்பு",
        "கூரையிலிருந்து மீட்டர் வரை கேபிள் நீளம், தேவையான பாதுகாப்புச் சாதனங்கள்",
        "ஆன்-கிரிட் அல்லது ஹைப்ரிட், பேக்அப் வேண்டுமெனில் பேட்டரி அளவு",
      ],
      calcTitle: "உங்கள் வீட்டுக்கான சேமிப்பைக் கணக்கிடுங்கள்",
      faq: [
        { q: "எவ்வளவு கூரை இடம் தேவை?", a: "ஒரு kW-க்கு நிழலில்லா தோராயமாக 9 முதல் 10 ச.மீ (சுமார் 100 ச.அடி). 3 kW அமைப்புக்கு சுமார் 30 ச.மீ." },
        { q: "அடுக்குமாடி மொட்டைமாடியில் நிறுவலாமா?", a: "ஆம், பொதுவாக சங்கத்தின் எழுத்துப்பூர்வ அனுமதியுடன்; அமைப்பு உங்கள் சொந்த மீட்டருடன் இணைக்கப்படும். என்ன சாத்தியம் என்பதைச் சரிபார்க்க உதவுகிறோம்." },
        { q: "மின்தடையில் ஆன்-கிரிட் அமைப்பு இயங்குமா?", a: "இல்லை. பாதுகாப்புக்காக கிரிட் செயலிழக்கும்போது நின்றுவிடும். பேக்அப் வேண்டுமெனில் பேட்டரியுடன் ஹைப்ரிட் அமைப்பைத் தேர்ந்தெடுங்கள்." },
        { q: "நிறுவ எவ்வளவு நாள் ஆகும்?", a: "வீட்டுக்கு தளத்தில் நிறுவல் பொதுவாக ஒன்று முதல் மூன்று நாட்கள். TANGEDCO நெட் மீட்டர் ஒப்புதலுக்கு அதிக காலம் ஆகும்." },
      ],
    },
    commercial: {
      eyebrow: "வணிக சோலார்",
      title: "அலுவலகங்கள், பள்ளிகள், மருத்துவமனைகள், கடைகளுக்கான சோலார்",
      lead: "தொழில்களும் நிறுவனங்களும் பெரும்பாலான மின்சாரத்தைப் பகலில், சோலார் உற்பத்தி செய்யும் அதே நேரத்தில் பயன்படுத்துகின்றன. அதனால் இயக்கச் செலவைக் குறைக்க கூரை சோலார் மிகச் சிறந்த வழி.",
      image: "/img/commercial.jpg",
      idealTitle: "யாருக்கு ஏற்றது",
      ideal: ["அலுவலகங்கள், IT பூங்காக்கள்", "பள்ளிகள், கல்லூரிகள்", "மருத்துவமனைகள், கிளினிக்குகள்", "ஹோட்டல்கள், உணவகங்கள்", "கடைகள், ஷோரூம்கள்", "வழிபாட்டுத் தலங்கள், சமுதாயக் கூடங்கள்"],
      benefitsTitle: "தொழிலுக்கு ஏன் பொருந்தும்",
      benefits: [
        { icon: "chart", title: "குறைந்த இயக்கச் செலவு", text: "பகல் பயன்பாட்டை சோலார் நேரடியாக ஈடுசெய்வதால் முதல் கட்டணச் சுழற்சியிலேயே சேமிப்பு தொடங்கும்." },
        { icon: "rupee", title: "அதிக கட்டணம், அதிக சேமிப்பு", text: "வணிகக் கட்டணம் வீட்டுக் கட்டணத்தை விட அதிகம்; எனவே ஒவ்வொரு சோலார் யூனிட்டும் அதிக மதிப்புடையது." },
        { icon: "leaf", title: "நிலைத்தன்மை இலக்குகள்", text: "வாடிக்கையாளர்கள், மாணவர்கள், நோயாளிகளுக்கு சுத்தமான ஆற்றலில் உங்கள் அர்ப்பணிப்பைக் காட்டுங்கள்." },
        { icon: "clipboard", title: "தெளிவான வணிகக் கணக்கு", text: "முதலீட்டைத் திட்டமிட உங்கள் விலைப்புள்ளியில் எதிர்பார்க்கும் உற்பத்தியும் சேமிப்பும் இருக்கும்." },
        { icon: "wifi", title: "தொலை கண்காணிப்பு", text: "உங்கள் எல்லா தளங்களின் உற்பத்தியையும் ஒரே ஆப்பில் கண்காணிக்கலாம்." },
        { icon: "wrench", title: "குறைந்த பராமரிப்பு", text: "அவ்வப்போது சுத்தம், ஆண்டுக்கு ஒரு சோதனை, தேவைப்படும்போது சேவை." },
      ],
      sizesTitle: "வழக்கமான வணிக அமைப்பு அளவுகள்",
      sizesLead: "தள ஆய்வில் உங்கள் பகல் சுமை, கூரை பரப்பைக் கொண்டு அளவிடப்படும்.",
      sizes: [
        { label: "கடைகள், கிளினிக்குகள், சிறு அலுவலகங்கள்", value: "3 – 15 kW" },
        { label: "பள்ளிகள், ஹோட்டல்கள், நடுத்தர அலுவலகங்கள்", value: "15 – 50 kW" },
        { label: "மருத்துவமனைகள், கல்லூரிகள், பெரிய கட்டடங்கள்", value: "50 – 150 kW+" },
      ],
      pointsTitle: "உங்கள் வணிகக் கணக்கு, விளக்கமாக",
      points: [
        "உங்கள் உண்மையான கட்டணங்களிலிருந்து எதிர்பார்க்கும் மாத உற்பத்தி, ஈடுசெய்யப்படும் யூனிட்கள்",
        "நெட்வொர்க் கட்டணங்களுக்குப் பின் ஆண்டுக்கான தோராய சேமிப்பு வரம்பு",
        "உங்கள் அளவுக்குத் தேவையான ஒப்புதல்கள் (நெட் மீட்டரிங், பெரிய ஆலைகளுக்கு CEIG ஆய்வு)",
        "GST வரிவரியாகக் காட்டப்படும் தெளிவான, விவரமான விலைப்புள்ளி",
      ],
      calcTitle: "உங்கள் தொழிலுக்கான சேமிப்பைக் கணக்கிடுங்கள்",
      faq: [
        { q: "வணிகக் கட்டடங்களுக்கு நெட் மீட்டரிங் உண்டா?", a: "வணிக LT இணைப்புகளில் உள்ள கூரை அமைப்புகள் உங்கள் வகைக்கும் அளவுக்கும் பொருந்தும் TANGEDCO திட்டத்தின் கீழ் இணைக்கப்படலாம். சரியான வழியை நாங்கள் உறுதிசெய்வோம்." },
        { q: "எங்கள் வேலை நேரம் பாதிக்கப்படுமா?", a: "இடையூறு குறைவாக இருக்கும்படி வேலையைத் திட்டமிடுகிறோம். இறுதி இணைப்புக்கு பொதுவாக குறுகிய, திட்டமிட்ட மின் நிறுத்தம் தேவை." },
        { q: "ஷீட் கூரையில் நிறுவலாமா?", a: "ஆம். உலோக ஷீட் கூரைக்கு ஏற்ற தாங்கும் அமைப்பைப் பயன்படுத்துகிறோம்; முதலில் கூரையின் நிலையைச் சரிபார்க்கிறோம்." },
        { q: "ROI கணக்கை எப்படிப் பெறுவது?", a: "சமீபத்திய கட்டணங்களைப் பகிருங்கள். உங்கள் விலைப்புள்ளியில் முதலீடு, எதிர்பார்க்கும் சேமிப்பு, திருப்பிச் செலுத்தும் காலம் இருக்கும்." },
      ],
    },
    industrial: {
      eyebrow: "தொழிற்சாலை சோலார்",
      title: "தொழிற்சாலைகள், கிடங்குகளுக்கான அதிக திறன் சோலார்",
      lead: "பெரிய கூரைகளும் நிலையான பகல் சுமையும் தொழிற்சாலைகளை சோலாருக்கு மிகவும் ஏற்றதாக்குகின்றன. பெரிய நிறுவலுக்குத் தேவையான பாதுகாப்பு, ஒப்புதல்கள், ஆவணங்களுடன் பல இன்வெர்ட்டர், மூன்று கட்ட ஆலைகளை வடிவமைக்கிறோம்.",
      image: "/img/industrial.jpg",
      idealTitle: "யாருக்கு ஏற்றது",
      ideal: ["உற்பத்தி அலகுகள்", "கிடங்குகள், லாஜிஸ்டிக்ஸ் மையங்கள்", "ஜவுளி, உணவுப் பதப்படுத்தல், பொறியியல் அலகுகள்", "குளிர்பதனக் கிடங்குகள்", "தொழிற்பேட்டைகள், SIDCO அலகுகள்"],
      benefitsTitle: "தொழிற்சாலைக்காக உருவாக்கப்பட்டது",
      benefits: [
        { icon: "factory", title: "பெரிய அளவிலான வடிவமைப்பு", text: "பல மூன்று கட்ட இன்வெர்ட்டர்கள், ஸ்ட்ரிங் வடிவமைப்பு, பெரிய அமைப்புகளுக்குச் சரியான கேபிள் அளவு." },
        { icon: "rupee", title: "அதிக கட்டணத்தில் பெரிய சேமிப்பு", text: "தொழிற்சாலை மின்சாரம் விலை அதிகம்; பகல் யூனிட்களை ஈடுசெய்வது உங்கள் செலவை நேரடியாகக் குறைக்கும்." },
        { icon: "shield", title: "பாதுகாப்பு", text: "தேவையான தரத்தில் AC/DC பாதுகாப்பு, சர்ஜ் சாதனங்கள், எர்த்திங், மின்னல் பாதுகாப்பு." },
        { icon: "doc", title: "ஒப்புதல்களை நாங்கள் கவனிப்போம்", text: "நெட் மீட்டரிங் மற்றும் தேவைப்படும் இடங்களில் மின் ஆய்வக (CEIG) பாதுகாப்பு ஆய்வுக்கான ஆவணங்களைத் தயாரிக்கிறோம்." },
        { icon: "wifi", title: "ஆலை கண்காணிப்பு", text: "இன்வெர்ட்டர் வாரியான உற்பத்தித் தரவும் எச்சரிக்கைகளும்; பிரச்சினைகளை முன்கூட்டியே கண்டறியலாம்." },
        { icon: "wrench", title: "இயக்கம், பராமரிப்பு", text: "திட்டமிட்ட சுத்தம், ஆய்வு, செயல்திறன் சோதனைகள்." },
      ],
      sizesTitle: "வழக்கமான தொழிற்சாலை ஆலை அளவுகள்",
      sizesLead: "உங்கள் சுமை, கூரை பரப்பு, இணைப்பு வகையைக் கொண்டு அளவிடப்படும்.",
      sizes: [
        { label: "சிறு அலகுகள், பட்டறைகள்", value: "10 – 50 kW" },
        { label: "நடுத்தர தொழிற்சாலைகள், கிடங்குகள்", value: "50 – 112 kW" },
        { label: "பெரிய ஆலைகள் (HT இணைப்பு)", value: "112 kW-க்கு மேல்" },
      ],
      pointsTitle: "நாங்கள் கவனிப்பவை",
      points: [
        "கூரை ஆய்வு, கட்டமைப்புச் சோதனை, நிழல் பகுப்பாய்வு",
        "மூன்று கட்ட இணைப்புக்கான இன்வெர்ட்டர், ஸ்ட்ரிங் வடிவமைப்பு",
        "கேபிள், ACDB/DCDB, பாதுகாப்பு அட்டவணை",
        "தேவைப்படும் இடங்களில் CEIG ஆய்வு, நெட் மீட்டரிங் ஆவணங்கள்",
        "சோதனை, இயக்கம், வரைபடங்களுடன் முழுமையான திட்ட ஆவணத் தொகுப்பு",
      ],
      calcTitle: "உங்கள் ஆலைக்கான சேமிப்பைக் கணக்கிடுங்கள்",
      faq: [
        { q: "அளவு வரம்பு உண்டா?", a: "LT இணைப்புகளுக்கு வரம்புகள் உண்டு. பெரிய ஆலைகள் வேறு மீட்டர் விதிகளுடன் உயர் மின்னழுத்தத்தில் (HT) இணையும். உங்கள் இணைப்புக்கு எது பொருந்தும் என்று பொறியாளர் விளக்குவார்." },
        { q: "ஆய்வு தேவையா?", a: "பெரிய அமைப்புகளுக்கு மின் ஆய்வகத்தின் (CEIG) பாதுகாப்பு ஆய்வு தேவை. ஆவணங்களைத் தயாரித்து ஆய்வில் பங்கேற்கிறோம்." },
        { q: "உற்பத்தி நடக்கும்போதே வேலை செய்யலாமா?", a: "பெரும்பாலான வேலை கூரையில் நடக்கும். நிறுத்த நேரம் குறைவாக இருக்க உங்கள் பராமரிப்புக் குழுவுடன் இறுதி இணைப்பைத் திட்டமிடுகிறோம்." },
        { q: "கூரையின் வலிமை?", a: "தள ஆய்வில் கூரையையும் கட்டமைப்பையும் சரிபார்த்து அதற்கேற்ப தாங்கும் அமைப்பை வடிவமைக்கிறோம்." },
      ],
    },
  },
  products: {
    eyebrow: "அமைப்புகள் & பொருட்கள்",
    title: "சோலார் அமைப்புகளும் அவற்றின் பாகங்களும்",
    lead: "தரமான பேனல்கள், இன்வெர்ட்டர்கள், பேட்டரிகள், தாங்கும் அமைப்புகள், பாதுகாப்புச் சாதனங்களால் உருவான ஆன்-கிரிட், ஆஃப்-கிரிட், ஹைப்ரிட் அமைப்புகள். ஒவ்வொரு மாடலும் உத்தரவாதமும் உங்கள் விலைப்புள்ளியில் இருக்கும்.",
    typesTitle: "உங்கள் அமைப்பு வகையைத் தேர்ந்தெடுங்கள்",
    bestFor: "சிறந்தது",
    types: [
      { icon: "plug", title: "ஆன்-கிரிட்", text: "நெட் மீட்டருடன் கிரிட்டில் இணைந்தது. பேட்டரி இல்லை.", best: "குறைந்த முதலீட்டில் கட்டணத்தைக் குறைக்க",
        points: ["மிகவும் சிக்கனமான தேர்வு", "நெட் மீட்டரிங் மூலம் மிகை ஏற்றுமதி", "கிரிட் மின்தடையில் நின்றுவிடும் (பாதுகாப்பு விதி)"] },
      { icon: "battery", title: "ஹைப்ரிட்", text: "கிரிட் இணைப்புடன், பேக்அப்புக்கு பேட்டரிகள்.", best: "குறைந்த கட்டணமும் மின்தடையில் பேக்அப்பும்",
        points: ["மின்தடையில் தேர்ந்தெடுத்த சுமைகள் இயங்கும்", "முதலில் சோலார், பின் பேட்டரி, பின் கிரிட்", "உங்கள் பேக்அப் தேவைக்கு ஏற்ற பேட்டரி"] },
      { icon: "sun", title: "ஆஃப்-கிரிட்", text: "கிரிட் இணைப்பு இல்லாமல் பேனல்கள், பேட்டரிகள், இன்வெர்ட்டர்.", best: "பண்ணைகள், தொலைதூர இடங்கள்",
        points: ["கிரிட் இல்லாமலும் இயங்கும்", "உங்கள் சுமைக்கு ஏற்ற பேட்டரி தொகுப்பு", "பம்புகள், பண்ணை வீடுகளுக்கு ஏற்றது"] },
    ],
    partsTitle: "ஒரு அமைப்பில் என்ன இருக்கும்",
    partsLead: "நிலைபெற்ற உற்பத்தியாளர்களின் பொருட்களைப் பயன்படுத்துகிறோம். சரியான பிராண்ட், மாடல், உத்தரவாதம் விலைப்புள்ளியில் இருக்கும்.",
    parts: [
      { icon: "panel", title: "சோலார் பேனல்கள்", text: "நீண்ட செயல்திறன் உத்தரவாதத்துடன் அதிக திறன் கொண்ட மோனோ PERC, TOPCon அல்லது பைஃபேஷியல் பேனல்கள்." },
      { icon: "inverter", title: "இன்வெர்ட்டர்கள்", text: "ஆன்-கிரிட் ஸ்ட்ரிங் இன்வெர்ட்டர்கள், பேட்டரி சார்ஜிங் மற்றும் பேக்அப் கொண்ட ஹைப்ரிட் இன்வெர்ட்டர்கள்." },
      { icon: "battery", title: "பேட்டரிகள்", text: "நீண்ட ஆயுளுக்கு லித்தியம் (LFP), அல்லது பட்ஜெட் முக்கியமெனில் லெட்-ஆசிட்." },
      { icon: "ruler", title: "தாங்கும் அமைப்பு", text: "RCC, ஷீட், ஓடு கூரைகளுக்கு கால்வனைஸ்டு அல்லது அலுமினிய அமைப்புகள்." },
      { icon: "shield", title: "பாதுகாப்பு", text: "சர்ஜ் பாதுகாப்புடன் ACDB, DCDB, ஃப்யூஸ், MCB, எர்த்திங், மின்னல் தடுப்பான்." },
      { icon: "wifi", title: "கண்காணிப்பு", text: "Wi-Fi அல்லது GSM கண்காணிப்பு; உற்பத்தியை போனில் பார்க்கலாம்." },
    ],
    compareTitle: "விரைவு ஒப்பீடு",
    compareHead: ["", "ஆன்-கிரிட்", "ஹைப்ரிட்", "ஆஃப்-கிரிட்"],
    compareRows: [
      ["கிரிட் இணைப்பு", "ஆம்", "ஆம்", "இல்லை"],
      ["பேட்டரிகள்", "இல்லை", "ஆம்", "ஆம்"],
      ["மின்தடையில் இயங்குமா", "இல்லை", "ஆம் (தேர்ந்தெடுத்த சுமைகள்)", "ஆம்"],
      ["நெட் மீட்டரிங்", "ஆம்", "ஆம்", "இல்லை"],
      ["ஒப்பீட்டு முதலீடு", "குறைவு", "அதிகம்", "அதிகம்"],
    ],
    note: "எது பொருந்தும் என்று தெரியவில்லையா? நீங்கள் மின்சாரத்தை எப்படிப் பயன்படுத்துகிறீர்கள், பேக்அப் வேண்டுமா என்று சொல்லுங்கள்; பொறியாளர் சரியான அமைப்பைப் பரிந்துரைப்பார்.",
  },
  how: {
    eyebrow: "எப்படி செயல்படுகிறது",
    title: "முதல் அழைப்பு முதல் இயக்கம் வரை",
    lead: "தெளிவான படிப்படியான செயல்முறை; அடுத்து என்ன நடக்கும் என்பது எப்போதும் உங்களுக்குத் தெரியும்.",
    steps: [
      { icon: "phone", title: "இலவச ஆலோசனை", text: "உங்கள் கட்டடம் பற்றி சொல்லி, மின் கட்டண ரசீதைப் பகிருங்கள்.", time: "நாள் 1",
        points: ["இணையக் கோரிக்கை அல்லது தொலைபேசி அழைப்பு", "உங்கள் பயன்பாடு, இலக்குகளைப் புரிந்துகொள்கிறோம்", "ரசீது, கூரை புகைப்படங்கள் இணையத்தில் பதிவேற்றம்"] },
      { icon: "ruler", title: "தள ஆய்வு", text: "உங்கள் கூரையையும் வயரிங்கையும் சரிபார்க்க எங்கள் குழு வருகிறது.", time: "சில நாட்களில்",
        points: ["கூரை பரப்பு, திசை, நிழல்", "தாங்கும் அமைப்பு, கேபிள் வழி", "மீட்டர், கட்டம், அனுமதிக்கப்பட்ட சுமை"] },
      { icon: "clipboard", title: "வடிவமைப்பு & விலைப்புள்ளி", text: "அமைப்பை வடிவமைத்து விவரமான விலைப்புள்ளியை அனுப்புகிறோம்.", time: "ஆய்வுக்குப் பின்",
        points: ["உங்கள் கட்டணத்துக்கு சரியான அளவு", "ஒற்றைக் கோட்டு வரைபடம், கூரை வரைவு", "எதிர்பார்க்கும் உற்பத்தி, சேமிப்பு"] },
      { icon: "wrench", title: "நிறுவல்", text: "அமைப்பு, பேனல்கள், இன்வெர்ட்டர், பாதுகாப்புச் சாதனங்களை எங்கள் குழு நிறுவுகிறது.", time: "பெரும்பாலான வீடுகளுக்கு 1–3 நாட்கள்",
        points: ["கூரையில் பாதுகாப்பான வேலை", "நேர்த்தியான, குறியிடப்பட்ட கேபிள் வழி", "எர்த்திங், சர்ஜ் பாதுகாப்பு"] },
      { icon: "doc", title: "ஒப்புதல்கள்", text: "நெட் மீட்டரிங் விண்ணப்பம், தேவைப்படும் ஆய்வுகள்.", time: "TANGEDCO-வைப் பொறுத்தது",
        points: ["ஆவணங்களை நாங்கள் தயாரிக்கிறோம்", "பெரிய ஆலைகளுக்கு CEIG ஆய்வு", "மீட்டர் பொருத்தப்படும் வரை தொடர்ந்து கவனிக்கிறோம்"] },
      { icon: "bolt", title: "இயக்கம் & ஒப்படைப்பு", text: "சோதனை, இயக்கம், செயல்விளக்கம்.", time: "சோலாருக்கு மாறுங்கள்",
        points: ["மின்னழுத்தம், எர்த், இன்சுலேஷன் சோதனைகள்", "கண்காணிப்பு ஆப் அமைப்பு", "உத்தரவாத ஆவணங்கள், கையேடுகள் ஒப்படைப்பு"] },
    ],
    flowTitle: "உங்கள் சோலார் அமைப்பு கட்டடத்துக்கு எப்படி மின்சாரம் தருகிறது",
    readyTitle: "இவற்றைத் தயாராக வைத்திருங்கள்",
    ready: ["சமீபத்திய மின் கட்டண ரசீது (புகைப்படம் அல்லது PDF)", "உங்கள் கூரை அல்லது மொட்டைமாடி புகைப்படங்கள்", "உங்கள் மின் இணைப்பு எண்", "தெரிந்தால், கூரையின் தோராய அளவு"],
    afterTitle: "நிறுவலுக்குப் பின்",
    after: [
      { icon: "wifi", title: "கண்காணிப்பு", text: "இன்வெர்ட்டர் ஆப்பில் தினசரி உற்பத்தியைப் பாருங்கள்." },
      { icon: "wrench", title: "சேவை உதவி", text: "சந்தேகங்கள், சுத்தம் செய்யும் ஆலோசனை அல்லது சேவை வருகைக்கு அழையுங்கள்." },
      { icon: "shield", title: "உத்தரவாதம்", text: "விலைப்புள்ளி மற்றும் ஒப்படைப்பு ஆவணங்களில் உள்ளபடி பொருள் உத்தரவாதங்கள்." },
    ],
  },
  projects: {
    eyebrow: "எங்கள் திட்டங்கள்",
    title: "முடிக்கப்பட்ட நிறுவல்கள்",
    lead: "வீடுகள், தொழில்கள், தொழிற்சாலைகளுக்காக நாங்கள் வடிவமைத்து நிறுவிய கூரை அமைப்புகள்.",
    all: "அனைத்தும்",
    filters: { residential: "வீடு", commercial: "வணிகம்", industrial: "தொழிற்சாலை" },
    capacity: "திறன்", system: "அமைப்பு", result: "வாடிக்கையாளர் தெரிவித்த பலன்",
    empty: "திட்டப் புகைப்படங்கள் சேர்க்கப்படுகின்றன. உங்கள் அருகிலுள்ள குறிப்புகளுக்கு எங்களைக் கேளுங்கள்.",
    sampleTag: "மாதிரி (dev மட்டும்)",
    items: en.projects.items,
  },
  footer: {
    tagline: "தமிழ்நாட்டில் வீடுகள், தொழில்கள், தொழிற்சாலைகளுக்கான கூரை சோலார்.",
    explore: "பக்கங்கள்", company: "நிறுவனம்", contact: "தொடர்பு", rights: "அனைத்து உரிமைகளும் பாதுகாக்கப்பட்டவை.",
  },
};

// Same project list for both languages unless a Tamil list is set above.
export const site: Record<Lang, SiteContent> = { en, ta };

/** Projects visible on this build: sample entries only in `npm run dev`. */
export function visibleProjects(items: Project[]): Project[] {
  return items.filter((p) => !p.sample || import.meta.env.DEV);
}
