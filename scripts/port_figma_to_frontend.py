import re

with open("experiments/figma/Nexus Research Collaboration System/src/App.tsx") as f:
    content = f.read()

# 1. Add 'use client'; and ensure React imports include useEffect, useCallback
content = content.replace(
    'import { useMemo, useState, type ReactNode } from "react"',
    "'use client';\n\nimport { useEffect, useCallback, useMemo, useState, type ReactNode } from \"react\""
)

# 2. Check for any forbidden strings
forbidden = ["tiger", "tbr", "researchcircle"]
for word in forbidden:
    matches = re.findall(rf'\b{word}\b', content, re.IGNORECASE)
    if matches:
        print(f"Warning: found forbidden word '{word}': {matches}")

# Write to frontend/src/app/page.tsx
with open("frontend/src/app/page.tsx", "w") as f:
    f.write(content)

print("Successfully ported Figma App.tsx to frontend/src/app/page.tsx")
