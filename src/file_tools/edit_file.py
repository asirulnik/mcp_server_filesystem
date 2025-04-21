# src/file_tools/edit_file.py (Revised for Absolute Paths)

import difflib
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# REMOVED: from .path_utils import normalize_path

logger = logging.getLogger(__name__)


@dataclass
class EditOperation:
    """Represents a single edit operation."""
    old_text: str
    new_text: str


@dataclass
class EditOptions:
    """Optional formatting settings for edit operations."""
    preserve_indentation: bool = True
    normalize_whitespace: bool = True # Note: This option might be less useful now


class MatchResult:
    """Stores information about a match attempt."""
    def __init__(
        self, matched: bool, line_index: int = -1, line_count: int = 0, details: str = ""
    ):
        self.matched = matched
        self.line_index = line_index
        self.line_count = line_count
        self.details = details

    def __repr__(self) -> str:
        return (f"MatchResult(matched={self.matched}, line_index={self.line_index}, line_count={self.line_count})")


# --- Helper functions (normalize_line_endings, get_line_indentation, etc.) remain the same ---
# ... (Keep normalize_line_endings, normalize_whitespace, get_line_indentation, preserve_indentation, find_exact_match, create_unified_diff, apply_edits) ...

def normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n")

def normalize_whitespace(text: str) -> str:
    result = re.sub(r"[ \t]+", " ", text)
    result = "\n".join(line.strip() for line in result.split("\n"))
    return result

def get_line_indentation(line: str) -> str:
    match = re.match(r"^(\s*)", line)
    return match.group(1) if match else ""

def preserve_indentation(old_text: str, new_text: str) -> str:
    if ("- " in new_text or "* " in new_text) and ("- " in old_text or "* " in old_text):
        return new_text
    old_lines = old_text.split("\n")
    new_lines = new_text.split("\n")
    if not old_lines or not new_lines: return new_text
    base_indent = get_line_indentation(old_lines[0]) if old_lines and old_lines[0].strip() else ""
    old_indents = { i: get_line_indentation(line) for i, line in enumerate(old_lines) if line.strip() }
    new_indents = { i: get_line_indentation(line) for i, line in enumerate(new_lines) if line.strip() }
    first_new_indent_len = len(new_indents.get(0, "")) if new_indents else 0
    result_lines = []
    for i, new_line in enumerate(new_lines):
        if not new_line.strip():
            result_lines.append("")
            continue
        new_indent = new_indents.get(i, "")
        target_indent = ""
        if i < len(old_lines) and i in old_indents: target_indent = old_indents[i]
        elif i == 0: target_indent = base_indent
        elif first_new_indent_len > 0:
            curr_indent_len = len(new_indent)
            target_indent = base_indent
            for prev_i in range(i - 1, -1, -1):
                if prev_i in old_indents and prev_i in new_indents:
                    prev_old = old_indents[prev_i]
                    prev_new = new_indents[prev_i]
                    if len(prev_new) <= curr_indent_len:
                        relative_spaces = curr_indent_len - len(prev_new)
                        target_indent = prev_old + " " * relative_spaces
                        break
        else: target_indent = new_indent
        result_lines.append(target_indent + new_line.lstrip())
    return "\n".join(result_lines)

def find_exact_match(content: str, pattern: str) -> MatchResult:
    if pattern in content:
        lines_before = content[: content.find(pattern)].count("\n")
        line_count = pattern.count("\n") + 1
        return MatchResult(matched=True, line_index=lines_before, line_count=line_count, details="Exact match found")
    return MatchResult(matched=False, details="No exact match found")

def create_unified_diff(original: str, modified: str, file_path: str) -> str:
    original_lines = original.splitlines(True)
    modified_lines = modified.splitlines(True)
    diff_lines = difflib.unified_diff(original_lines, modified_lines, fromfile=f"a/{file_path}", tofile=f"b/{file_path}", lineterm="")
    return "".join(diff_lines)

def apply_edits(content: str, edits: List[EditOperation], options: Optional[EditOptions] = None) -> Tuple[str, List[Dict[str, Any]], bool]:
    if options is None: options = EditOptions()
    normalized_content = normalize_line_endings(content)
    match_results = []
    changes_made = False
    for i, edit in enumerate(edits):
        normalized_old = normalize_line_endings(edit.old_text)
        normalized_new = normalize_line_endings(edit.new_text)
        if normalized_old == normalized_new:
            match_results.append({"edit_index": i, "match_type": "skipped", "details": "No change needed - text already matches desired state"})
            continue
        if normalized_new in normalized_content and normalized_old not in normalized_content:
            match_results.append({"edit_index": i, "match_type": "skipped", "details": "Edit already applied - content already in desired state"})
            continue
        exact_match = find_exact_match(normalized_content, normalized_old)
        if exact_match.matched:
            start_pos = normalized_content.find(normalized_old)
            end_pos = start_pos + len(normalized_old)
            if options.preserve_indentation:
                normalized_new = preserve_indentation(normalized_old, normalized_new)
            normalized_content = normalized_content[:start_pos] + normalized_new + normalized_content[end_pos:]
            changes_made = True
            match_results.append({"edit_index": i, "match_type": "exact", "line_index": exact_match.line_index, "line_count": exact_match.line_count})
        else:
            match_results.append({"edit_index": i, "match_type": "failed", "details": "No exact match found"})
            logger.warning(f"Could not find exact match for edit {i}")
    return normalized_content, match_results, changes_made

# --- Main edit_file function (Modified) ---

def edit_file(
    abs_path: Path, # Changed parameter to absolute Path object
    edits: List[Dict[str, str]],
    dry_run: bool = False,
    options: Optional[Dict[str, Any]] = None,
    # REMOVED: project_dir parameter
) -> Dict[str, Any]:
    """
    Make selective edits to a file specified by an absolute Path object.

    Args:
        abs_path: Absolute Path object of the file to edit.
        edits: List of edit operations with old_text and new_text.
        dry_run: If True, only preview changes without applying them.
        options: Optional formatting settings (e.g., preserve_indentation).

    Returns:
        Dict with diff output and match information including success status.
    """
    # Path validation happens in the caller (_validate_abs_path)
    # Basic edits validation remains
    if not isinstance(edits, list): raise ValueError("Edits must be a list")

    file_path_str = str(abs_path) # Use string representation for messages/diffs

    # Validate file path exists
    if not abs_path.is_file():
        logger.error(f"File not found or not a file: {file_path_str}")
        raise FileNotFoundError(f"File not found or not a file: {file_path_str}")

    # Read file content
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error while reading {file_path_str}: {str(e)}")
        raise ValueError(f"File '{file_path_str}' contains invalid characters.") from e
    except Exception as e:
        logger.error(f"Error reading file {file_path_str}: {str(e)}")
        raise

    # Convert edits to EditOperation objects
    edit_operations = []
    for edit in edits:
        old_text = edit.get("old_text")
        new_text = edit.get("new_text")
        if old_text is None or new_text is None:
            logger.error(f"Invalid edit operation: {edit}")
            raise ValueError("Edit ops must contain 'old_text' and 'new_text'.")
        edit_operations.append(EditOperation(old_text=old_text, new_text=new_text))

    # Set up options
    edit_options = EditOptions(
        preserve_indentation=options.get("preserve_indentation", True) if options else True,
        normalize_whitespace=options.get("normalize_whitespace", True) if options else True,
    )

    # Apply edits
    match_results = [] # Ensure match_results is defined in outer scope
    try:
        modified_content, match_results, changes_made = apply_edits(
            original_content, edit_operations, edit_options
        )

        failed_matches = [r for r in match_results if r.get("match_type") == "failed"]
        already_applied = [r for r in match_results if r.get("match_type") == "skipped" and "already applied" in r.get("details", "")]

        result = {
            "match_results": match_results,
            "file_path": file_path_str, # Report the string path
            "dry_run": dry_run,
        }

        if failed_matches:
            result.update({"success": False, "error": "Failed to find exact match for one or more edits"})
            return result

        if not changes_made or (already_applied and len(already_applied) == len(edits)):
            result.update({"success": True, "diff": "", "message": "No changes needed - content already in desired state"})
            return result

        # Use string path for diff generation
        diff = create_unified_diff(original_content, modified_content, file_path_str)
        result.update({"diff": diff, "success": True})

        # Write changes if not in dry run mode
        if not dry_run and changes_made:
            try:
                # Use the absolute Path object for writing
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)
            except UnicodeEncodeError as e:
                logger.error(f"Unicode encode error while writing to {file_path_str}: {str(e)}")
                result.update({"success": False, "error": "Content contains characters that cannot be encoded."})
                return result
            except Exception as e:
                logger.error(f"Error writing to file {file_path_str}: {str(e)}")
                result.update({"success": False, "error": str(e)})
                return result

        return result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Exception in edit_file for {file_path_str}: {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "match_results": match_results if match_results else [{"edit_index": 0, "match_type": "failed", "details": f"Exception: {error_msg}"}],
            "file_path": file_path_str,
        }