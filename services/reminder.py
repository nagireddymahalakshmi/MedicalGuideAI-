from typing import List, Dict


def generate_reminders(
    medications: List[Dict]
) -> List[Dict]:
    """
    Generate reminder suggestions from extracted medications.

    The system does NOT decide medical dosage or treatment.
    It only creates reminder entries from information already provided.
    """

    reminders = []

    for medication in medications:

        reminders.append({
            "medication": medication.get("name", "Unknown medication"),
            "dose": medication.get("dose", ""),
            "reminder": (
                "Follow the timing written by your doctor or "
                "on the prescription."
            )
        })

    return reminders


def create_reminder_text(
    medication_name: str,
    dose: str,
    timing: str
) -> str:

    return (
        f"Reminder: {medication_name} {dose}. "
        f"Timing: {timing}. "
        "Follow the prescribed instructions."
    )