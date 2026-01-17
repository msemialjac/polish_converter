"""Field and value humanization for Odoo domain conversion.

This module provides functions to convert technical Odoo field names and
dynamic references to human-readable labels.
"""

from .parser import DynamicRef


# System field labels for Odoo-aware output (ODOO-01)
SYSTEM_FIELD_LABELS = {
    'create_uid': 'Created By',
    'write_uid': 'Last Updated By',
    'create_date': 'Created On',
    'write_date': 'Last Updated On',
    'active': 'Active',
    'id': 'ID',
    'display_name': 'Display Name',
}


def get_system_field_label(field_name: str) -> str | None:
    """Get UI label for a system field.

    Args:
        field_name: The field name to check

    Returns:
        UI label if it's a system field, None otherwise
    """
    if not field_name:
        return None
    return SYSTEM_FIELD_LABELS.get(field_name)


def _humanize_segment(segment: str) -> str:
    """Humanize a single path segment.

    Handles:
    - Strip _id suffix (singularize)
    - Strip _ids suffix (pluralize)
    - Replace underscores with spaces
    - Apply title case

    Args:
        segment: A single field name segment (no dots)

    Returns:
        Humanized segment string
    """
    if not segment:
        return ""

    # Handle _ids suffix (strip and pluralize)
    if segment.endswith('_ids'):
        base = segment[:-4]  # Remove _ids
        # Humanize the base
        humanized = base.replace('_', ' ').title()
        # Simple pluralization: handle 'y' -> 'ies' for company
        if humanized.lower().endswith('y') and len(humanized) > 1:
            # Check if it's a consonant + y pattern (company -> companies)
            if len(humanized) >= 2 and humanized[-2].lower() not in 'aeiou':
                return humanized[:-1] + 'ies'
        return humanized + 's'

    # Handle _id suffix (strip, singular)
    if segment.endswith('_id') and len(segment) > 3:
        base = segment[:-3]  # Remove _id
        return base.replace('_', ' ').title()

    # Regular field: replace underscores and title case
    # Filter out empty parts from multiple underscores
    parts = [p for p in segment.split('_') if p]
    return ' '.join(p.title() for p in parts)


def humanize_field(field_name: str) -> str:
    """Convert a technical field name to a human-readable label.

    Handles:
    - Snake_case to Title Case (FIELD-01)
    - Strip _id suffix (FIELD-02)
    - Strip _ids suffix (FIELD-03)
    - Dotted paths with possessive form (FIELD-04)

    Args:
        field_name: Technical field name (e.g., 'privacy_visibility', 'project_id.name')

    Returns:
        Human-readable label (e.g., 'Privacy Visibility', "Project's Name")

    Examples:
        >>> humanize_field('privacy_visibility')
        'Privacy Visibility'
        >>> humanize_field('company_id')
        'Company'
        >>> humanize_field('group_ids')
        'Groups'
        >>> humanize_field('project_id.name')
        "Project's Name"
    """
    if not field_name:
        return ""

    # Split on dots for path handling
    segments = field_name.split('.')

    if len(segments) == 1:
        # Single segment - just humanize it
        return _humanize_segment(segments[0])

    # Multiple segments - use possessive form
    # All segments except last get 's appended
    humanized_parts = []
    for i, segment in enumerate(segments):
        humanized = _humanize_segment(segment)
        if i < len(segments) - 1:
            # Add possessive for all but last segment
            humanized_parts.append(humanized + "'s")
        else:
            humanized_parts.append(humanized)

    return ' '.join(humanized_parts)


def humanize_dynamic_ref(ref: DynamicRef) -> str:
    """Humanize a DynamicRef for pseudocode output (ODOO-02).

    Converts user references to human-readable form:
    - user.id -> "current user"
    - user.partner_id.id -> "current user's Partner"
    - user.groups_id.ids -> "current user's Groups"
    - user.company_ids -> "current user's Companies"

    Non-user references are returned unchanged.

    Args:
        ref: A DynamicRef object

    Returns:
        Human-readable string for the reference
    """
    name = ref.name

    # Only handle user.* references
    if not name.startswith('user.'):
        return str(ref)

    # Handle user.id specially
    if name == 'user.id':
        return "current user"

    # Extract the path after "user."
    rest = name[5:]  # Skip "user."

    # Split by dots
    parts = rest.split('.')

    # Handle various patterns
    if len(parts) >= 1:
        # Get the first segment (e.g., partner_id, company_ids, groups_id)
        first_segment = parts[0]

        # If ends with .id or .ids, we're accessing a relation's ID
        if len(parts) >= 2 and parts[-1] in ('id', 'ids'):
            # Use the segment before the final .id/.ids
            # e.g., user.partner_id.id -> Partner
            # e.g., user.groups_id.ids -> Groups
            base_segment = parts[-2] if len(parts) >= 2 else parts[0]
            humanized = _humanize_segment(base_segment)
            return f"current user's {humanized}"
        else:
            # Direct access like user.partner_id, user.company_ids
            humanized = _humanize_segment(first_segment)
            return f"current user's {humanized}"

    return str(ref)


def to_readable_text(text: str) -> str:
    """Return humanized text as-is for readable output.

    Previously converted spaces to underscores, but now we keep
    the human-readable format with spaces for better readability.
    Example: "current user's Partner" -> "current user's Partner"

    Args:
        text: Human-readable text with spaces

    Returns:
        The same text, preserving spaces for readability
    """
    return text
