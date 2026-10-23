# Universal Cross-Chat Memory & Context Recovery Invariants (ඕනෑම සංවාදයක අතීත මතකය ස්වයංක්‍රීයව විමර්ශනය කිරීමේ විශ්වීය නීතිය)

## 1. Zero Blank-Slate Assumption (සෑම Chat එකක්ම අලුත් දෙයක් ලෙස නොසැලකීම)
- **Universal Scope**: පරිශීලකයා කුමන Chat එකකදී හෝ යම් කාර්යයක්, මෙවලමක්, කේතයක්, දෝෂයක්, තීරණයක් හෝ මාතෘකාවක් ගැන කතා කරන විට, එය මෙම Chat එකට පමණක් සීමා වූ අලුත් දෙයක් ලෙස කිසිසේත්ම නොසැලකිය යුතුය.
- **Continuous Awareness**: Agent යනු පරිශීලකයා සමඟ දිගුකාලීනව වැඩ කරන එකම ප්‍රධාන සහායකයාය. එබැවින් වෙනත් ඕනෑම සංවාදයකදී (Previous Conversations / Past Sessions) සාකච්ඡා වූ, තීරණය වූ හෝ නිර්මාණය කළ සියල්ල පිළිබඳ සම්පූර්ණ අඛණ්ඩ මතකයක් (continuous memory context) පවත්වා ගත යුතුය.

## 2. Zero Redundant Questions & Zero Re-Explanation (පරිශීලකයාගෙන් නැවත කරුණු නොවිමසීම)
- **Never Force User to Re-Explain**: පරිශීලකයා විසින් අතීතයේදී වෙහෙස මහන්සි වී සාකච්ඡා කළ, තීරණය කළ හෝ Agent විසින්ම සාදන ලද ක්‍රමවේද පිළිබඳව ("ඔබ ළඟ මේවා තියෙනවද?", "ඔබ මේක record කළාද?", "මේක හැදුවේ කොහොමද?", "කොහෙද තියෙන්නේ?") කියා පරිශීලකයාගෙන් නැවත නැවත කිසිදා නොවිමසිය යුතුය.
- **Mandatory Pre-Response Context Forensics**: පරිශීලකයා අතීත වැඩක් හෝ තමන් කළ දෙයක් ගැන ඉඟියක් හෝ දුන් සැනින්, පිළිතුරු දීමට පෙර Agent සතු background මෙවලම් මඟින්:
  1. Past Conversation Transcripts (`C:\Users\User\.gemini\antigravity\brain\*\.system_generated\logs\transcript.jsonl`)
  2. Past Scratch & Script Directories (`C:\Users\User\.gemini\antigravity\brain\*\scratch\*`)
  3. Git Commit History across all local repos (`git log -S "<keyword>"`, `git log -n 20 --oneline`)
  4. Active Workspace files & rules
  ස්වයංක්‍රීයව විමර්ශනය කර, එම කාර්යය කලින් කළ ආකාරය, භාවිත කළ තාක්ෂණයන්, සහ අදාළ ගොනු සියල්ල තමන් විසින්ම සොයාගත යුතුය.

## 3. Autonomous Method & Pipeline Retrieval (කලින් සාර්ථක වූ ක්‍රමවේද කෙලින්ම නැවත භාවිතය)
- අතීත සංවාදයකදී සාර්ථකව විසඳූ ඕනෑම ගැටලුවක් (උදා: C# WPF DrawingVisual + FFmpeg මඟින් Tooltip Videos සෑදීම, Revit API methods, WPF theme bindings, coordination logic) හමු වූ විට, එම ක්‍රමවේදය අලුතින් සොයා ගැනීමට හෝ පරිශීලකයාගෙන් විමසීමට අවශ්‍ය නැත.
- අතීත scratch scripts හෝ code pipelines සෘජුවම නැවත භාවිත කර කාර්යය ස්වයංක්‍රීයවම නිම කළ යුතුය.
