"""
Script to fix the indentation in main.py for the seeding section
"""

with open("main.py", "r") as f:
    lines = f.readlines()

# Lines to indent are from line 103 (0-indexed: 102) to line 542 (0-indexed: 541)
# This is the entire try/except block that should be inside the if block
start_line = 102  # The 'try:' line after our if check
end_line = 542    # The last 'traceback.print_exc()' line

new_lines = []
for i, line in enumerate(lines):
    if start_line <= i <= end_line:
        # Add 4 spaces to the beginning if the line is not empty
        if line.strip():
            new_lines.append("    " + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open("main.py", "w") as f:
    f.writelines(new_lines)

print("✓ Fixed main.py indentation")
