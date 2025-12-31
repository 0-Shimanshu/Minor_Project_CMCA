from typing import List, Dict, Tuple
import re
import unicodedata


# Public knowledge (guest + student)
PUBLIC_KNOWLEDGE: List[Dict[str, object]] = [
    {
        "keywords": [
            "library timings", "library timing", "library time", "library hours", "library",
            "lib timings", "lib hours", "opening hours", "closing time",
            "पुस्तकालय समय", "ग्रंथालय वेळ"
        ],
        "answer": "Library is open 9 AM to 8 PM.",
    },
    {
        "keywords": ["library hours"],
        "answer": "Library is open 9 AM to 8 PM.",
    },
    {
        "keywords": [
            "परीक्षा फॉर्म", "exam form", "form bharna", "exam form last date",
            "फॉर्म अंतिम तिथि", "परीक्षा फॉर्म अंतिम तिथि"
        ],
        "answer": "परीक्षा फॉर्म भरने की अंतिम तिथि 15 मार्च है।",
    },
    {
        "keywords": [
            "hostel rules", "hostel rule", "rules hostel",
            "hostel entry", "entry time", "hostel timing",
            "hostel discipline", "discipline",
            "hostel id", "id card hostel", "warden rules"
        ],
        "answer": (
            "Hostel rules: Entry time is enforced, maintain discipline, carry your ID at all times, and follow wardens' instructions."
        ),
    },
    {
        "keywords": ["college website", "official website", "website", "site", "portal", "college portal"],
        "answer": "Official college website: https://aitr.ac.in/",
    },
    {
        "keywords": [
            "admission process", "admission", "how to get admission",
            "admission procedure", "admission steps", "how to apply"
        ],
        "answer": "Admission process: Apply online, submit required documents, attend counseling as scheduled, and complete fee payment.",
    },
    {
        "keywords": ["exam form last date", "last date exam form", "form last date"],
        "answer": "Exam form last date is 15 March.",
    },
    {
        "keywords": [
            "परीक्षा समय सारणी", "परीक्षा समय सारणीी", "समय सारणी", "परीक्षा सारणी", "परीक्षा समय",
            "pariksha samay sarani", "pariksha sarani", "samay sarani",
            "exam timetable", "exam schedule notice", "timetable", "exam schedule"
        ],
        "answer": "परीक्षा समय सारणी नोटिस सेक्शन में उपलब्ध होती है।",
    },
    {
        "keywords": [
            "holiday list", "holidays", "academic calendar", "vacation schedule", "holiday", 
            "छुट्टियां", "अवकाश सूची", "शैक्षणिक कैलेंडर", "सुट्ट्या", "शैक्षणिक दिनदर्शिका"
        ],
        "answer": "Holiday list / academic calendar is available in the Notices or Academics section on the website.",
    },
    {
        "keywords": [
            "bus timing", "college bus", "bus timings", "shuttle", "transport", "bus route", "transport timetable",
            "बस समय", "बस रूट", "बस समय सारणी"
        ],
        "answer": "College transport timetable and routes are published in the Notices / Transport section.",
    },
    {
        "keywords": [
            "library rules", "book issue limit", "issue limit", "library fine", "late fee", "book return",
            "ग्रंथालय नियम", "पुस्तक जारी सीमा", "दंड"
        ],
        "answer": "Library rules: Students may issue up to 2 books for 14 days. Late return fine as per library policy displayed in the library.",
    },
    {
        "keywords": [
            "contact", "contact details", "contact info", "phone", "email", "helpdesk", "support",
            "संपर्क", "प्रशासन संपर्क", "संपर्क विवरण"
        ],
        "answer": "Contact details are available on the Contact page of the official website (see Official college website link).",
    },
    {
        "keywords": [
            "what courses are offered at acropolis institute", "courses offered", "courses at acropolis",
            "programs offered", "programs at acropolis"
        ],
        "answer": "Acropolis Institute offers undergraduate and postgraduate programs in Engineering, Management, Computer Applications, and Pharmacy.",
    },
    {
        "keywords": [
            "Acropolis Institute में कौन-कौन से कोर्स उपलब्ध हैं?", "कोर्स उपलब्ध", "कौन-कौन से कोर्स"
        ],
        "answer": "Acropolis Institute में इंजीनियरिंग, मैनेजमेंट, कंप्यूटर एप्लीकेशन और फार्मेसी के स्नातक एवं स्नातकोत्तर कोर्स उपलब्ध हैं।",
    },
    {
        "keywords": [
            "Acropolis Institute இல் எந்த பாடநெறிகள் வழங்கப்படுகின்றன?"
        ],
        "answer": "Acropolis Institute இல் பொறியியல், மேலாண்மை, கணினி பயன்பாடுகள் மற்றும் மருந்தியல் பாடநெறிகள் வழங்கப்படுகின்றன.",
    },
    {
        "keywords": [
            "Acropolis Institute లో ఏ కోర్సులు అందుబాటులో ఉన్నాయి?"
        ],
        "answer": "Acropolis Institute లో ఇంజినీరింగ్, మేనేజ్‌మెంట్, కంప్యూటర్ అప్లికేషన్స్ మరియు ఫార్మసీ కోర్సులు అందుబాటులో ఉన్నాయి.",
    },
    {
        "keywords": [
            "Acropolis Institute मध्ये कोणते कोर्स उपलब्ध आहेत?"
        ],
        "answer": "Acropolis Institute मध्ये अभियांत्रिकी, व्यवस्थापन, संगणक अनुप्रयोग आणि फार्मसी कोर्स उपलब्ध आहेत.",
    },
    {
        "keywords": [
            "what is the admission process at acropolis institute", "admission process acropolis", "acropolis admission process"
        ],
        "answer": "Admissions are based on entrance exams, merit, and counseling as per university and government guidelines.",
    },
    {
        "keywords": [
            "Acropolis Institute में प्रवेश प्रक्रिया क्या है?", "प्रवेश प्रक्रिया"
        ],
        "answer": "प्रवेश प्रक्रिया प्रवेश परीक्षा, मेरिट और काउंसलिंग पर आधारित होती है।",
    },
    {
        "keywords": [
            "Acropolis Institute இல் சேர்க்கை நடைமுறை என்ன?"
        ],
        "answer": "சேர்க்கை நடைமுறை நுழைவுத் தேர்வு, மதிப்பெண் மற்றும் கவுன்சிலிங் அடிப்படையில் நடைபெறும்.",
    },
    {
        "keywords": [
            "Acropolis Institute లో అడ్మిషన్ ప్రక్రియ ఏమిటి?"
        ],
        "answer": "అడ్మిషన్లు ఎంట్రన్స్ ఎగ్జామ్, మెరిట్ మరియు కౌన్సిలింగ్ ఆధారంగా ఉంటాయి.",
    },
    {
        "keywords": [
            "Acropolis Institute मध्ये प्रवेश प्रक्रिया काय आहे?"
        ],
        "answer": "प्रवेश प्रक्रिया प्रवेश परीक्षा, गुणवत्ता आणि काउन्सेलिंगवर आधारित आहे.",
    },
    {
        "keywords": [
            "eligibility for engineering courses at acropolis", "engineering eligibility acropolis"
        ],
        "answer": "Candidates must have completed 10+2 with Physics, Chemistry, and Mathematics.",
    },
    {
        "keywords": [
            "Acropolis Institute में इंजीनियरिंग के लिए पात्रता क्या है?", "इंजीनियरिंग पात्रता"
        ],
        "answer": "उम्मीदवारों ने भौतिकी, रसायन और गणित के साथ 10+2 पूरा किया होना चाहिए।",
    },
    {
        "keywords": [
            "Acropolis Institute இல் பொறியியல் படிப்பிற்கு தகுதி என்ன?"
        ],
        "answer": "மாணவர்கள் பிளஸ் டூவில் இயற்பியல், இரசாயனம் மற்றும் கணிதம் படித்திருக்க வேண்டும்.",
    },
    {
        "keywords": [
            "Acropolis Institute లో ఇంజినీరింగ్ అర్హత ఏమిటి?"
        ],
        "answer": "విద్యార్థులు ఫిజిక్స్, కెమిస్ట్రీ, మ్యాథ్స్‌తో 10+2 పూర్తి చేసి ఉండాలి.",
    },
    {
        "keywords": [
            "Acropolis Institute मध्ये अभियांत्रिकीसाठी पात्रता काय आहे?"
        ],
        "answer": "विद्यार्थ्यांनी भौतिकशास्त्र, रसायनशास्त्र आणि गणितासह 10+2 पूर्ण केलेले असावे.",
    },
    {
        "keywords": [
            "what is the fee structure at acropolis", "fee structure acropolis", "fees acropolis"
        ],
        "answer": "The fee structure varies by course and is decided as per university norms.",
    },
    {
        "keywords": [
            "Acropolis Institute की फीस संरचना क्या है?", "फीस संरचना"
        ],
        "answer": "फीस कोर्स के अनुसार अलग-अलग होती है और विश्वविद्यालय के नियमों के अनुसार तय की जाती है।",
    },
    {
        "keywords": [
            "Acropolis Institute இன் கட்டண அமைப்பு என்ன?"
        ],
        "answer": "பாடநெறியின் அடிப்படையில் கட்டணம் மாறுபடும்.",
    },
    {
        "keywords": [
            "Acropolis Institute ఫీజు నిర్మాణం ఏమిటి?"
        ],
        "answer": "ఫీజులు కోర్సు ఆధారంగా మారుతాయి.",
    },
    {
        "keywords": [
            "Acropolis Institute ची फी संरचना काय आहे?"
        ],
        "answer": "फी कोर्सनुसार वेगळी असते.",
    },
    {
        "keywords": [
            "does acropolis provide hostel facilities", "hostel facility acropolis"
        ],
        "answer": "Yes, separate hostel facilities are available for boys and girls.",
    },
    {
        "keywords": [
            "क्या Acropolis Institute में हॉस्टल सुविधा है?", "हॉस्टल सुविधा"
        ],
        "answer": "हाँ, लड़कों और लड़कियों के लिए अलग हॉस्टल उपलब्ध हैं।",
    },
    {
        "keywords": [
            "Acropolis Institute ஹாஸ்டல் வசதி வழங்குகிறதா?"
        ],
        "answer": "ஆம், ஆண் மற்றும் பெண் மாணவர்களுக்கு தனி ஹாஸ்டல்கள் உள்ளன.",
    },
    {
        "keywords": [
            "Acropolis Institute లో హాస్టల్ సదుపాయం ఉందా?"
        ],
        "answer": "అవును, బాలురు మరియు బాలికలకు వేర్వేరు హాస్టల్స్ ఉన్నాయి.",
    },
    {
        "keywords": [
            "Acropolis Institute मध्ये वसतिगृह सुविधा आहे का?"
        ],
        "answer": "होय, मुला-मुलींसाठी स्वतंत्र वसतिगृहे उपलब्ध आहेत.",
    },
    {
        "keywords": [
            "does acropolis institute provide placement assistance", "placement assistance acropolis", "placement support"
        ],
        "answer": "Yes, the institute has a dedicated placement cell to support students.",
    },
]


# Private knowledge (student only)
PRIVATE_KNOWLEDGE: List[Dict[str, object]] = [
    {
        "keywords": [
            "cdc placement process", "placement process", "placement cell",
            "cdc", "career development cell", "campus placement process"
        ],
        "answer": "CDC placement process: Register with the placement cell, attend pre-placement talks, complete aptitude and technical rounds, and follow interview schedules.",
    },
    {
        "keywords": [
            "revaluation", "rechecking", "reval form", "reevaluation", "copy recheck", 
            "पुनर्मूल्यांकन", "रीचेकिंग", "रीएवैल्यूएशन"
        ],
        "answer": "Revaluation: Apply within 7 days of result via the exam section; fee as per the notice.",
    },
    {
        "keywords": [
            "attendance condonation", "attendance shortage", "attendance below 75", "short attendance", "condonation",
            "उपस्थिति छूट", "उपस्थिति कमी", "75% उपस्थिति"
        ],
        "answer": "Attendance condonation: Submit application with supporting documents to the HoD for approval as per institute rules.",
    },
    {
        "keywords": [
            "backlog exam", "supplementary exam", "ATKT", "carry over", "back paper",
            "बैकलॉग", "पूरक परीक्षा", "एटीकेटी"
        ],
        "answer": "Backlog/supplementary exams: Forms and dates are published in Notices. Register before the deadline.",
    },
    {
        "keywords": [
            "id card lost", "duplicate id", "id reissue", "new id card", "identity card",
            "आईडी कार्ड", "आईडी गुम", "आईडी पुनः जारी"
        ],
        "answer": "ID card reissue: Submit a request at the admin office (FIR copy if lost). Fee as per the notice.",
    },
    {
        "keywords": [
            "internal marks calculation", "internal marks", "how internal marks",
            "internal assessment", "attendance weightage", "assignment marks"
        ],
        "answer": "Internal marks calculation: Attendance, assignments, and internal tests contribute to the final internal marks.",
    },
    {
        "keywords": [
            "third year exam schedule", "3rd year exam", "ty exam schedule",
            "third year exam timetable", "exam may", "may exam"
        ],
        "answer": "Third year exams are conducted in May.",
    },
    {
        "keywords": ["तीसरे वर्ष की परीक्षा", "third year exam kab", "ty exam kab", "तीसरे वर्ष", "मई", "परीक्षा"],
        "answer": "तीसरे वर्ष की परीक्षा मई महीने में होगी।",
    },
    {
        "keywords": [
            "fees kab jama", "fees last date", "fees notice",
            "fees jama karni", "fees deposit last date", "fees payment date", "fee notice"
        ],
        "answer": "Fees ki last date notice section me hoti hai.",
    },
    {
        "keywords": ["exam registration third year", "registration third year", "registration deadline", "third year registration"],
        "answer": "Exam registration for third year closes one month earlier.",
    },
    {
        "keywords": ["परीक्षा वेळापत्रक", "marathi timetable", "marathi exam schedule", "वेळापत्रक", "परीक्षा वेळ", "टाईमटेबल"],
        "answer": "परीक्षा वेळापत्रक पोर्टलवर उपलब्ध असते.",
    },
]


FALLBACK_ANSWER = (
    "I could not find a relevant answer. Please refer to the notices or contact the department."
)


def _normalize(text: str) -> str:
    # Unicode normalization + casefold
    t = unicodedata.normalize('NFKC', text).casefold().strip()
    # Remove zero-width characters commonly present in Indic scripts
    t = t.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
    # Replace common punctuation (including Hindi danda) with spaces
    t = re.sub(r"[\?\!\.,;:\|\u0964\u0965]", " ", t)  # \u0964=।, \u0965=॥
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t)
    return t


def _matches(query: str, keywords: List[str]) -> bool:
    q = _normalize(query)
    q_ns = q.replace(' ', '')
    for kw in keywords:
        k = _normalize(kw)
        k_ns = k.replace(' ', '')
        # Direct substring or ignoring spaces
        if k in q or k_ns in q_ns:
            return True
        # Token containment: all tokens of keyword appear in query
        k_tokens = [tok for tok in k.split(' ') if tok]
        if k_tokens and all(tok in q for tok in k_tokens):
            return True
    return False


def answer_for(query: str, role: str) -> Tuple[bool, str]:
    """
    Deterministic keyword-based matching.
    - Guest: public knowledge only
    - Student: public + private knowledge
    """
    groups = list(PUBLIC_KNOWLEDGE)
    if role == 'student':
        groups = groups + PRIVATE_KNOWLEDGE
    for item in groups:
        kws = item.get("keywords", [])
        ans = item.get("answer", "")
        if isinstance(kws, list) and _matches(query, kws):
            return True, str(ans)
    return False, FALLBACK_ANSWER
