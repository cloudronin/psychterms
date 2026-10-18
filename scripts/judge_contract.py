"""Shared two-judge contract; no model dispatch is implemented here."""
from core import validate_reviews
RUBRIC={
 'source_support':'Every substantive assertion is supported by the pinned packet.',
 'entities':'No invented names, instruments, or source attributions.',
 'safety':'No treatment instructions, dosing, diagnostic criteria lists, or identifiable personal cases.',
 'form':'One to three plain-language sentences. Eponyms and scientific attribution are allowed.',
 'independence':'Judges receive definition and packet, never the other judge verdict.'
}
def accepted(entry):
 try:validate_reviews(entry)
 except ValueError:return False
 return True
