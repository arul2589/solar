// Page copy for the public Home and About pages (English + Tamil).
// Use {name} for the installer's company name. Edit freely; no code changes needed elsewhere.
// Tamil wording should be reviewed by a native speaker before launch (see DECISIONS.md).
import type { Lang } from "./i18n";

export type Item = { icon?: string; title: string; text: string };

export type Content = {
  nav: { home: string; about: string; quote: string };
  home: {
    chips: string[];
    ctaAbout: string;
    introTitle: string;
    introText: string;
    flow: { title: string; text: string }[];
    flowNote: string;
    benefitsTitle: string;
    benefitsLead: string;
    benefits: Item[];
    systemsTitle: string;
    systemsLead: string;
    systems: Item[];
    whoTitle: string;
    who: Item[];
    savingsTitle: string;
    savingsPoints: string[];
    savingsNote: string;
    faqTitle: string;
    faq: { q: string; a: string }[];
    ctaTitle: string;
    ctaText: string;
  };
  about: {
    title: string;
    lead: string;
    whatTitle: string;
    what: Item[];
    whyTitle: string;
    why: Item[];
    processTitle: string;
    process: string[];
    safetyTitle: string;
    safety: string[];
    contactTitle: string;
    contactText: string;
    address: string;
    phone: string;
    email: string;
  };
  footer: { links: string };
};

const en: Content = {
  nav: { home: "Home", about: "About us", quote: "Get a quotation" },
  home: {
    chips: ["Homes", "Shops & offices", "Industries", "On-grid · Hybrid · Off-grid", "TANGEDCO net metering support"],
    ctaAbout: "About us",
    introTitle: "What is rooftop solar?",
    introText:
      "Solar panels on your roof turn sunlight into electricity. An inverter changes it into the power your home or business uses. During the day you use your own solar power first, so you buy fewer units from the grid and your electricity bill goes down. With a TANGEDCO net meter, extra power you do not use goes to the grid and is adjusted in your bill.",
    flow: [
      { title: "Sun", text: "Free sunlight falls on your roof every day" },
      { title: "Solar panels", text: "Turn sunlight into DC electricity" },
      { title: "Inverter", text: "Changes DC into the AC your appliances use" },
      { title: "Your building", text: "Uses solar power first, so you buy less" },
      { title: "Net meter & grid", text: "Extra power goes out; at night you draw from the grid" },
    ],
    flowNote: "A rooftop solar system works silently, with no fuel and no moving parts in the panels.",
    benefitsTitle: "How solar helps you",
    benefitsLead: "A good solar system pays you back every month, for many years.",
    benefits: [
      { icon: "💡", title: "Lower electricity bills", text: "Every unit your panels make is a unit you do not buy from the grid. Your monthly bill comes down." },
      { icon: "⚡", title: "Net metering", text: "Surplus power goes to the grid and is adjusted in your bill. At night you draw from the grid as usual." },
      { icon: "🔧", title: "Long life, low upkeep", text: "Panels usually come with a long performance warranty, often 25 years. Regular cleaning and a yearly check are normally enough." },
      { icon: "📈", title: "Less worry about tariff rises", text: "Once installed, the power from your roof costs nothing per unit, so tariff increases affect you less." },
      { icon: "🌿", title: "Clean energy", text: "Solar makes electricity without fuel or smoke, which cuts your carbon footprint." },
      { icon: "🔋", title: "Backup when needed", text: "With a hybrid or off-grid system and batteries, selected lights and fans keep running during power cuts." },
    ],
    systemsTitle: "Choose the right system",
    systemsLead: "The best option depends on how you use power and whether you want backup.",
    systems: [
      { icon: "🔌", title: "On-grid (with net meter)", text: "Connected to the grid, no batteries. The most common and most economical choice for lowering bills. It switches off during a grid power cut, for safety." },
      { icon: "🏠", title: "Hybrid", text: "Grid plus batteries. Lowers your bill and keeps chosen loads running when the power goes out." },
      { icon: "🌾", title: "Off-grid", text: "Panels, batteries and inverter without the grid. For farms, remote sites, or places with no reliable supply." },
    ],
    whoTitle: "Who is it for?",
    who: [
      { icon: "🏡", title: "Homes", text: "Single-phase and three-phase homes with a free, shade-free roof or terrace." },
      { icon: "🏪", title: "Shops, offices and institutions", text: "Daytime users such as shops, clinics, schools and offices benefit the most, because solar runs when they do." },
      { icon: "🏭", title: "Industries", text: "Larger three-phase plants with several inverters, designed to the rules for bigger installations." },
    ],
    savingsTitle: "What decides how much you save?",
    savingsPoints: [
      "How many units you use every month (your EB bill tells us)",
      "Free, shade-free roof area: roughly 9 to 10 sq m (about 100 sq ft) for each kW",
      "Roof direction and tilt: south-facing is best in India",
      "Your tariff and sanctioned load",
    ],
    savingsNote:
      "That is why we do not show a generic price. Our engineer reviews your bill and roof photos and sends a quotation made for your building. The final price is confirmed after a site visit.",
    faqTitle: "Common questions",
    faq: [
      { q: "How much roof space do I need?", a: "About 9 to 10 square metres (roughly 100 sq ft) for each kW. A 3 kW home system needs around 30 sq m (300 sq ft) of shade-free space." },
      { q: "Will it work during a power cut?", a: "An on-grid system switches off when the grid fails, which is a safety rule. If you want power during cuts, choose a hybrid or off-grid system with batteries." },
      { q: "What is net metering?", a: "A TANGEDCO arrangement where a meter records the power you import and export. Units you export are adjusted in your bill. We guide you through the documents and application." },
      { q: "Does it work on cloudy days or in rain?", a: "Yes, but the output is lower. Panels still make some power in diffused light." },
      { q: "How long do panels last?", a: "Panels are built to last 25 years or more. Your quotation states the exact warranty of the products offered." },
      { q: "How do I get a price?", a: "Fill in the request form with your EB bill and roof photos. Our engineer reviews it and emails you a quotation. The final price is confirmed after a site visit." },
    ],
    ctaTitle: "Ready to see what solar can do for you?",
    ctaText: "It takes about five minutes. Keep your EB bill handy.",
  },
  about: {
    title: "About {name}",
    lead:
      "{name} designs and installs rooftop solar systems for homes, shops and industries in Tamil Nadu. We study your electricity bill and your roof, design a system that fits, install it safely and guide you through TANGEDCO net metering.",
    whatTitle: "What we do",
    what: [
      { icon: "📐", title: "Site survey and design", text: "We check your roof, shade, load and electricity bill, then size the system and plan the wiring." },
      { icon: "🛠️", title: "Supply and installation", text: "On-grid, hybrid and off-grid systems: panels, inverter, mounting structure, cables and protection devices." },
      { icon: "📄", title: "Net metering support", text: "We help prepare the documents and application for your TANGEDCO net meter." },
      { icon: "✅", title: "Testing and handover", text: "Tests before commissioning, a demonstration for you, and warranty papers and manuals." },
      { icon: "☎️", title: "After-sales service", text: "Help with questions, cleaning advice and service visits when you need them." },
    ],
    whyTitle: "Why customers choose us",
    why: [
      { icon: "🧾", title: "Made for your bill and roof", text: "Every quotation is reviewed by an engineer. We do not send an automatic price." },
      { icon: "📋", title: "Clear, itemised quotations", text: "Panels, inverter, structure, cables, protection and GST are listed line by line." },
      { icon: "🛡️", title: "Safe installation", text: "Proper earthing, DC and AC protection, and lightning protection where it is needed." },
      { icon: "🗂️", title: "Clear paperwork", text: "Warranty details, test readings and drawings are kept for every project." },
      { icon: "🗣️", title: "English and Tamil", text: "Our website, emails and checklists are available in both languages." },
    ],
    processTitle: "How we work with you",
    process: [
      "You send a request with your EB bill and roof photos",
      "Our engineer reviews it and emails you a quotation",
      "Site visit to confirm the roof, shade and wiring route",
      "Installation of structure, panels, inverter and protection",
      "Testing, commissioning and a demonstration",
      "Net metering application and handover with warranty papers",
    ],
    safetyTitle: "Our safety and quality checks",
    safety: [
      "Polarity and string voltage checked before connecting the inverter",
      "Earthing for panels, structure and inverter, with earth resistance measured",
      "DC and AC protection boxes with surge protection",
      "Neat, labelled cable routing and corrosion-protected structure",
      "Photos and test readings recorded at every stage",
    ],
    contactTitle: "Talk to us",
    contactText: "Send a request online, or call us with any question.",
    address: "Address",
    phone: "Phone",
    email: "Email",
  },
  footer: { links: "Quick links" },
};

const ta: Content = {
  nav: { home: "முகப்பு", about: "எங்களைப் பற்றி", quote: "விலைப்புள்ளி பெற" },
  home: {
    chips: ["வீடுகள்", "கடைகள் & அலுவலகங்கள்", "தொழிற்சாலைகள்", "ஆன்-கிரிட் · ஹைப்ரிட் · ஆஃப்-கிரிட்", "TANGEDCO நெட் மீட்டரிங் உதவி"],
    ctaAbout: "எங்களைப் பற்றி",
    introTitle: "கூரை சோலார் என்றால் என்ன?",
    introText:
      "உங்கள் கூரையில் உள்ள சோலார் பேனல்கள் சூரிய ஒளியை மின்சாரமாக மாற்றுகின்றன. இன்வெர்ட்டர் அதை உங்கள் வீடு அல்லது தொழிலுக்குத் தேவையான மின்சாரமாக மாற்றுகிறது. பகலில் முதலில் உங்கள் சோலார் மின்சாரத்தையே பயன்படுத்துவதால், மின் வாரியத்திடமிருந்து வாங்கும் யூனிட்கள் குறைந்து மின் கட்டணம் குறையும். TANGEDCO நெட் மீட்டர் மூலம், பயன்படுத்தாத மிகை மின்சாரம் மின் இணைப்புக்குச் சென்று உங்கள் கட்டணத்தில் சரிசெய்யப்படும்.",
    flow: [
      { title: "சூரியன்", text: "தினமும் உங்கள் கூரையில் விழும் இலவச சூரிய ஒளி" },
      { title: "சோலார் பேனல்கள்", text: "சூரிய ஒளியை DC மின்சாரமாக மாற்றும்" },
      { title: "இன்வெர்ட்டர்", text: "DC-ஐ உங்கள் சாதனங்களுக்கான AC ஆக மாற்றும்" },
      { title: "உங்கள் கட்டடம்", text: "முதலில் சோலார் மின்சாரம் பயன்படும், வாங்கும் மின்சாரம் குறையும்" },
      { title: "நெட் மீட்டர் & கிரிட்", text: "மிகை மின்சாரம் வெளியே செல்லும்; இரவில் கிரிட்டிலிருந்து பெறலாம்" },
    ],
    flowNote: "கூரை சோலார் அமைப்பு அமைதியாக இயங்கும்; எரிபொருள் தேவையில்லை, பேனல்களில் நகரும் பாகங்கள் இல்லை.",
    benefitsTitle: "சோலார் உங்களுக்கு எப்படிப் பயன்படும்",
    benefitsLead: "நல்ல சோலார் அமைப்பு பல ஆண்டுகள் ஒவ்வொரு மாதமும் பலன் தரும்.",
    benefits: [
      { icon: "💡", title: "குறைந்த மின் கட்டணம்", text: "உங்கள் பேனல்கள் தயாரிக்கும் ஒவ்வொரு யூனிட்டையும் நீங்கள் வாங்க வேண்டியதில்லை. மாதக் கட்டணம் குறையும்." },
      { icon: "⚡", title: "நெட் மீட்டரிங்", text: "மிகை மின்சாரம் கிரிட்டுக்குச் சென்று உங்கள் கட்டணத்தில் சரிசெய்யப்படும். இரவில் வழக்கம்போல் கிரிட்டிலிருந்து பெறலாம்." },
      { icon: "🔧", title: "நீண்ட ஆயுள், குறைந்த பராமரிப்பு", text: "பேனல்களுக்கு பொதுவாக நீண்ட செயல்திறன் உத்தரவாதம் இருக்கும், பெரும்பாலும் 25 ஆண்டுகள். அவ்வப்போது சுத்தம் செய்து, ஆண்டுக்கு ஒருமுறை சோதித்தால் போதும்." },
      { icon: "📈", title: "கட்டண உயர்வு பற்றிய கவலை குறைவு", text: "நிறுவிய பின் உங்கள் கூரை மின்சாரத்துக்கு யூனிட்டுக்கு செலவு இல்லை. எனவே கட்டண உயர்வு உங்களை குறைவாகப் பாதிக்கும்." },
      { icon: "🌿", title: "சுத்தமான ஆற்றல்", text: "எரிபொருள் அல்லது புகை இல்லாமல் மின்சாரம் தயாரிப்பதால் கார்பன் தடம் குறையும்." },
      { icon: "🔋", title: "தேவையான போது பேக்அப்", text: "ஹைப்ரிட் அல்லது ஆஃப்-கிரிட் அமைப்பில் பேட்டரிகளுடன், மின்தடையின் போது தேர்ந்தெடுத்த விளக்குகள், மின்விசிறிகள் இயங்கும்." },
    ],
    systemsTitle: "சரியான அமைப்பைத் தேர்ந்தெடுங்கள்",
    systemsLead: "நீங்கள் மின்சாரத்தை எப்படிப் பயன்படுத்துகிறீர்கள், பேக்அப் வேண்டுமா என்பதைப் பொறுத்தது.",
    systems: [
      { icon: "🔌", title: "ஆன்-கிரிட் (நெட் மீட்டருடன்)", text: "கிரிட்டுடன் இணைந்தது, பேட்டரி இல்லை. கட்டணத்தைக் குறைக்க மிகவும் பொதுவான, சிக்கனமான தேர்வு. பாதுகாப்புக்காக கிரிட் மின்தடையின் போது நின்றுவிடும்." },
      { icon: "🏠", title: "ஹைப்ரிட்", text: "கிரிட்டும் பேட்டரியும். கட்டணத்தைக் குறைப்பதுடன், மின்தடையின் போது தேர்ந்தெடுத்த சுமைகளை இயக்கும்." },
      { icon: "🌾", title: "ஆஃப்-கிரிட்", text: "கிரிட் இல்லாமல் பேனல்கள், பேட்டரிகள், இன்வெர்ட்டர். பண்ணைகள், தொலைதூர இடங்கள், நம்பகமான மின்சாரம் இல்லாத இடங்களுக்கு." },
    ],
    whoTitle: "யாருக்கு ஏற்றது?",
    who: [
      { icon: "🏡", title: "வீடுகள்", text: "நிழல் இல்லாத காலி கூரை அல்லது மொட்டைமாடி உள்ள ஒற்றை கட்டம் மற்றும் மூன்று கட்ட வீடுகள்." },
      { icon: "🏪", title: "கடைகள், அலுவலகங்கள், நிறுவனங்கள்", text: "கடைகள், கிளினிக்குகள், பள்ளிகள், அலுவலகங்கள் போன்ற பகல் நேரப் பயனர்களுக்கு அதிக பலன், ஏனெனில் சோலார் அவர்கள் இயங்கும் நேரத்திலேயே இயங்கும்." },
      { icon: "🏭", title: "தொழிற்சாலைகள்", text: "பல இன்வெர்ட்டர்களுடன் கூடிய பெரிய மூன்று கட்ட ஆலைகள், பெரிய நிறுவல்களுக்கான விதிகளின்படி வடிவமைக்கப்படும்." },
    ],
    savingsTitle: "எவ்வளவு சேமிப்பு என்பதை எது தீர்மானிக்கிறது?",
    savingsPoints: [
      "நீங்கள் மாதம் எத்தனை யூனிட் பயன்படுத்துகிறீர்கள் (உங்கள் மின் கட்டண ரசீது சொல்லும்)",
      "நிழல் இல்லாத காலி கூரை பரப்பு: ஒரு kW-க்கு தோராயமாக 9 முதல் 10 ச.மீ (சுமார் 100 ச.அடி)",
      "கூரையின் திசை மற்றும் சாய்வு: இந்தியாவில் தெற்கு நோக்கியது சிறந்தது",
      "உங்கள் கட்டண வகை மற்றும் அனுமதிக்கப்பட்ட சுமை",
    ],
    savingsNote:
      "அதனால்தான் பொதுவான விலையை நாங்கள் காட்டுவதில்லை. எங்கள் பொறியாளர் உங்கள் ரசீது மற்றும் கூரை புகைப்படங்களைப் பரிசீலித்து, உங்கள் கட்டடத்துக்கான விலைப்புள்ளியை அனுப்புவார். இறுதி விலை தள ஆய்வுக்குப் பின் உறுதிசெய்யப்படும்.",
    faqTitle: "பொதுவான கேள்விகள்",
    faq: [
      { q: "எவ்வளவு கூரை இடம் தேவை?", a: "ஒரு kW-க்கு தோராயமாக 9 முதல் 10 சதுர மீட்டர் (சுமார் 100 ச.அடி). 3 kW வீட்டு அமைப்புக்கு நிழல் இல்லாத சுமார் 30 ச.மீ (300 ச.அடி) இடம் தேவை." },
      { q: "மின்தடையின் போது இயங்குமா?", a: "ஆன்-கிரிட் அமைப்பு கிரிட் செயலிழக்கும் போது பாதுகாப்பு விதிப்படி நின்றுவிடும். மின்தடையிலும் மின்சாரம் வேண்டுமெனில் பேட்டரியுடன் ஹைப்ரிட் அல்லது ஆஃப்-கிரிட் அமைப்பைத் தேர்ந்தெடுங்கள்." },
      { q: "நெட் மீட்டரிங் என்றால் என்ன?", a: "நீங்கள் பெறும் மற்றும் வெளியே அனுப்பும் மின்சாரத்தை ஒரு மீட்டர் பதிவு செய்யும் TANGEDCO ஏற்பாடு. வெளியே அனுப்பிய யூனிட்கள் உங்கள் கட்டணத்தில் சரிசெய்யப்படும். ஆவணங்கள் மற்றும் விண்ணப்பத்தில் நாங்கள் வழிகாட்டுவோம்." },
      { q: "மேகமூட்டம் அல்லது மழை நாட்களில் இயங்குமா?", a: "இயங்கும், ஆனால் உற்பத்தி குறைவாக இருக்கும். பரவிய ஒளியிலும் பேனல்கள் சிறிது மின்சாரம் தயாரிக்கும்." },
      { q: "பேனல்கள் எத்தனை ஆண்டுகள் நீடிக்கும்?", a: "பேனல்கள் 25 ஆண்டுகள் அல்லது அதற்கு மேல் நீடிக்கும்படி தயாரிக்கப்படுகின்றன. வழங்கப்படும் பொருட்களின் சரியான உத்தரவாதம் உங்கள் விலைப்புள்ளியில் இருக்கும்." },
      { q: "விலையை எப்படிப் பெறுவது?", a: "மின் கட்டண ரசீது மற்றும் கூரை புகைப்படங்களுடன் கோரிக்கைப் படிவத்தை நிரப்புங்கள். எங்கள் பொறியாளர் பரிசீலித்து விலைப்புள்ளியை மின்னஞ்சலில் அனுப்புவார். இறுதி விலை தள ஆய்வுக்குப் பின் உறுதிசெய்யப்படும்." },
    ],
    ctaTitle: "சோலார் உங்களுக்கு என்ன செய்யும் என்று பார்க்கத் தயாரா?",
    ctaText: "சுமார் ஐந்து நிமிடங்கள் ஆகும். உங்கள் மின் கட்டண ரசீதைக் கையில் வைத்திருங்கள்.",
  },
  about: {
    title: "{name} பற்றி",
    lead:
      "{name} தமிழ்நாட்டில் வீடுகள், கடைகள் மற்றும் தொழிற்சாலைகளுக்கான கூரை சோலார் அமைப்புகளை வடிவமைத்து நிறுவுகிறது. உங்கள் மின் கட்டணத்தையும் கூரையையும் ஆய்வு செய்து, பொருத்தமான அமைப்பை வடிவமைத்து, பாதுகாப்பாக நிறுவி, TANGEDCO நெட் மீட்டரிங்கில் வழிகாட்டுகிறோம்.",
    whatTitle: "நாங்கள் செய்வது",
    what: [
      { icon: "📐", title: "தள ஆய்வு மற்றும் வடிவமைப்பு", text: "உங்கள் கூரை, நிழல், சுமை, மின் கட்டணத்தைச் சரிபார்த்து, அமைப்பின் அளவை முடிவு செய்து வயரிங்கைத் திட்டமிடுகிறோம்." },
      { icon: "🛠️", title: "விநியோகம் மற்றும் நிறுவல்", text: "ஆன்-கிரிட், ஹைப்ரிட், ஆஃப்-கிரிட் அமைப்புகள்: பேனல்கள், இன்வெர்ட்டர், தாங்கும் அமைப்பு, கேபிள்கள், பாதுகாப்புச் சாதனங்கள்." },
      { icon: "📄", title: "நெட் மீட்டரிங் உதவி", text: "உங்கள் TANGEDCO நெட் மீட்டருக்கான ஆவணங்கள் மற்றும் விண்ணப்பத்தைத் தயாரிக்க உதவுகிறோம்." },
      { icon: "✅", title: "சோதனை மற்றும் ஒப்படைப்பு", text: "இயக்குவதற்கு முன் சோதனைகள், உங்களுக்குச் செயல்விளக்கம், உத்தரவாத ஆவணங்கள் மற்றும் கையேடுகள்." },
      { icon: "☎️", title: "விற்பனைக்குப் பிந்தைய சேவை", text: "சந்தேகங்களுக்கு உதவி, சுத்தம் செய்வதற்கான ஆலோசனை, தேவைப்படும்போது சேவை வருகைகள்." },
    ],
    whyTitle: "வாடிக்கையாளர்கள் எங்களை ஏன் தேர்வு செய்கிறார்கள்",
    why: [
      { icon: "🧾", title: "உங்கள் ரசீதுக்கும் கூரைக்கும் ஏற்றது", text: "ஒவ்வொரு விலைப்புள்ளியையும் பொறியாளர் பரிசீலிக்கிறார். தானியங்கி விலை அனுப்புவதில்லை." },
      { icon: "📋", title: "தெளிவான, விவரமான விலைப்புள்ளிகள்", text: "பேனல்கள், இன்வெர்ட்டர், அமைப்பு, கேபிள்கள், பாதுகாப்பு, GST ஆகியவை வரிவரியாகப் பட்டியலிடப்படும்." },
      { icon: "🛡️", title: "பாதுகாப்பான நிறுவல்", text: "சரியான எர்த்திங், DC மற்றும் AC பாதுகாப்பு, தேவைப்படும் இடங்களில் மின்னல் பாதுகாப்பு." },
      { icon: "🗂️", title: "தெளிவான ஆவணங்கள்", text: "ஒவ்வொரு திட்டத்துக்கும் உத்தரவாத விவரங்கள், சோதனை அளவீடுகள், வரைபடங்கள் பாதுகாக்கப்படும்." },
      { icon: "🗣️", title: "ஆங்கிலம் மற்றும் தமிழ்", text: "எங்கள் இணையதளம், மின்னஞ்சல்கள், சரிபார்ப்புப் பட்டியல்கள் இரு மொழிகளிலும் உள்ளன." },
    ],
    processTitle: "நாங்கள் எப்படிச் செயல்படுகிறோம்",
    process: [
      "மின் கட்டண ரசீது மற்றும் கூரை புகைப்படங்களுடன் கோரிக்கை அனுப்புகிறீர்கள்",
      "எங்கள் பொறியாளர் பரிசீலித்து விலைப்புள்ளியை மின்னஞ்சலில் அனுப்புவார்",
      "கூரை, நிழல், வயரிங் பாதையை உறுதி செய்ய தள ஆய்வு",
      "அமைப்பு, பேனல்கள், இன்வெர்ட்டர், பாதுகாப்புச் சாதனங்கள் நிறுவல்",
      "சோதனை, இயக்கம் மற்றும் செயல்விளக்கம்",
      "நெட் மீட்டரிங் விண்ணப்பம் மற்றும் உத்தரவாத ஆவணங்களுடன் ஒப்படைப்பு",
    ],
    safetyTitle: "எங்கள் பாதுகாப்பு மற்றும் தரச் சோதனைகள்",
    safety: [
      "இன்வெர்ட்டரை இணைக்கும் முன் துருவ இணைப்பு மற்றும் ஸ்ட்ரிங் மின்னழுத்தம் சரிபார்ப்பு",
      "பேனல்கள், அமைப்பு, இன்வெர்ட்டருக்கு எர்த்திங், எர்த் மின்தடை அளவீடு",
      "சர்ஜ் பாதுகாப்புடன் DC மற்றும் AC பாதுகாப்புப் பெட்டிகள்",
      "நேர்த்தியான, குறியிடப்பட்ட கேபிள் வழி மற்றும் துருப்பிடிக்காத அமைப்பு",
      "ஒவ்வொரு கட்டத்திலும் புகைப்படங்கள் மற்றும் சோதனை அளவீடுகள் பதிவு",
    ],
    contactTitle: "எங்களுடன் பேசுங்கள்",
    contactText: "இணையத்தில் கோரிக்கை அனுப்புங்கள், அல்லது ஏதேனும் கேள்விக்கு அழையுங்கள்.",
    address: "முகவரி",
    phone: "தொலைபேசி",
    email: "மின்னஞ்சல்",
  },
  footer: { links: "இணைப்புகள்" },
};

export const content: Record<Lang, Content> = { en, ta };
