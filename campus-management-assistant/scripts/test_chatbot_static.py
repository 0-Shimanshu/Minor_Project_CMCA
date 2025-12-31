import os
import sys

# Ensure project root on path
BASE = os.path.dirname(os.path.dirname(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from app.services.chatbot_static_knowledge import answer_for


TESTS = [
    ("guest", "Library timings"),
    ("guest", "library hours"),
    ("guest", "परीक्षा फॉर्म कब भरना है?"),
    ("guest", "Hostel rules"),
    ("guest", "College website"),
    ("guest", "Admission process"),
    ("guest", "Exam form last date"),
    ("guest", "परीक्षा समय सारणी"),
    ("student", "CDC placement process"),
    ("student", "Internal marks calculation"),
    ("student", "Third year exam schedule"),
    ("student", "तीसरे वर्ष की परीक्षा कब है?"),
    ("student", "Fees kab jama karni hai?"),
    ("student", "Exam registration third year"),
    ("student", "परीक्षा वेळापत्रक"),
]


def main():
    for role, q in TESTS:
        ok, ans = answer_for(q, role)
        print(f"ROLE={role} | Q={q}")
        print(f"OK={ok}")
        print(f"ANS={ans}")
        print("-")


if __name__ == "__main__":
    main()
