EXCESS_SHIFT_THRESHOLDS_HOURS = (8, 10, 12)
MAX_EXIT_NOTE_LENGTH = 500

EXIT_INCIDENT_TYPE_LABELS = {
    "descanso": "Descanso",
    "olvido": "Olvido",
    "correccion_manual": "Correccion manual",
    "otro": "Otro",
}

NO_INCIDENT_VALUES = {
    "",
    "none",
    "sin incidencia",
    "sin_incidencia",
}


def normalize_exit_note(note: str | None) -> str | None:
    clean_note = (note or "").strip()
    if not clean_note:
        return None
    if len(clean_note) > MAX_EXIT_NOTE_LENGTH:
        raise ValueError(
            f"La nota de salida no puede superar {MAX_EXIT_NOTE_LENGTH} caracteres."
        )
    return clean_note


def normalize_incident_type(incident_type: str | None) -> str | None:
    clean_type = (incident_type or "").strip().lower()
    if clean_type in NO_INCIDENT_VALUES:
        return None
    if clean_type not in EXIT_INCIDENT_TYPE_LABELS:
        raise ValueError("Tipo de incidencia no valido.")
    return clean_type


def incident_type_label(incident_type: str | None) -> str:
    clean_type = (incident_type or "").strip().lower()
    if clean_type in NO_INCIDENT_VALUES:
        return ""
    return EXIT_INCIDENT_TYPE_LABELS.get(
        clean_type,
        clean_type.replace("_", " ").capitalize(),
    )


def exceeded_shift_threshold_hours(total_seconds: int | None) -> int | None:
    if total_seconds is None:
        return None
    for threshold in reversed(EXCESS_SHIFT_THRESHOLDS_HOURS):
        if total_seconds > threshold * 3600:
            return threshold
    return None
