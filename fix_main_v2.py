"""
Wrap the seeding section with disable_seeding check
"""

with open("main.py", "r") as f:
    content = f.read()

# Find the seed section and wrap it
seed_start_marker = "    # Seed default users on startup\n    try:"
seed_end_marker = "        db.close()\n    except Exception as e:\n        print(f\"[ERROR] Error during user seeding: {e}\")\n        import traceback\n        traceback.print_exc()"

# Check if markers exist
if seed_start_marker not in content or seed_end_marker not in content:
    print("ERROR: Could not find seed markers in main.py")
    print("Seed start marker found:", seed_start_marker in content)
    print("Seed end marker found:", seed_end_marker in content)
    exit(1)

# Find indices
start_idx = content.find("    # Seed default users on startup")
end_idx = content.find("        traceback.print_exc()") + len("        traceback.print_exc()")

# Extract the parts
before = content[:start_idx]
seed_section = content[start_idx:end_idx]
after = content[end_idx:]

# Add the disable check before the seed section
check_code = """    # Check if seeding is enabled
    import os
    disable_seeding = os.getenv("DISABLE_SEEDING", "false").lower() == "true"
    
    if not disable_seeding:
"""

# Indent all lines in seed_section by 4 spaces
indented_seed = "\n".join("    " + line if line.strip() else line for line in seed_section.split("\n"))

# Reconstruct
new_content = before + check_code + "\n" + indented_seed + "\n" + after

with open("main.py", "w") as f:
    f.write(new_content)

print("✓ Successfully wrapped seed section with disable_seeding check")
