# Masterplan Villa Placement & Typology Guardrails

## 1. Strict Villa Typology & Naming Hierarchy (ගොඩනැගිලි වර්ග නීතිය)
- Masterplan එකක Villas place කිරීමේදී පහත නාමකරණ සම්මුතීන් අකුරටම පිළිපැදිය යුතු අතර කිසිවිටෙකත් එකිනෙක පටලවා නොගත යුතුය:
  - **W-** (Water): ජලය මත / Piles මත පිහිටි Villas (`W-SB`, `W-SBL`, `W-DBL`).
  - **B-** (Beach): ගොඩබිම පිහිටි Villas (`B-SB`, `B-SBL`, `B-DBL`).
  - **S**: Single Bedroom.
  - **D**: Double Bedroom.
  - **L** (Lounge / Skydeck): ඉහළ තට්ටුවේ Skydeck Lounge එකක් සහිත Villa (තට්ටු 2).
  - **L නොමැති ඒවා** (උදා: `W-SB`, `B-SB`): Single Story (තනි තට්ටුවේ Villas).
- `W-SB` පිහිටි ස්ථානයකට කිසිදු හේතුවක් මත `W-SBL` හෝ අනෙක් අතට place නොකළ යුතුය.

## 2. Roof-First Orientation Rule (වහලය මූලික කරගත් දිශානති නීතිය)
- Villa එකක Direction (මුහුණත) තහවුරු කරගැනීමේ මූලික නිර්ණායකය වන්නේ CAD හි ඇති **Roof Lines (වහලයේ හැඩය සහ Ridge Lines)** වේ.
- Entrance එක සැමවිටම Jetty / Walkway Branch එක දෙසටත්, Roof Slope එක සහ Pool / Deck කොටස විවෘත මුහුද දෙසටත් මුහුණලා පිහිටිය යුතුය.
- CAD drawing එකේ Roof outline එක මතට Revit Villa එකේ Roof outline එක 100% ක් සමපාත වන බව තහවුරු කරගත යුතුය.

## 3. Real Footprint vs Walkway Label Guardrail
- CAD drawing වල Villa අංකය සහිත Circle හෝ Text Label (උදා: `(01)`, `W-SBL-01`) පිහිටන්නේ Walkway එක මතය.
- කිසිවිටෙකත් Text Label හෝ Circle එකේ කේන්ද්‍රය මතට Villa එකේ Origin එක Place නොකළ යුතුය.
- සැමවිටම CAD හි ඇති නියම Villa Foundation / Footprint එකෙහි පිහිටීම ගණනය කර ඒ මතට පමණක් Place කළ යුතුය.

## 4. Named Sites & Pinning Mandate
- Masterplan තුළ නැවත නැවත යෙදෙන සෑම Link Instance එකකටම:
  1. ඒ ඒ Villa අංකය නමින් **Named Site** එකක් (උදා: `location W-SBL-01`) සාදා Assign කළ යුතුය.
  2. අතින් හෝ අත්වැරදීමකින් Move වීම වැළැක්වීමට Instance එක **Pin** කළ යුතුය.
  3. Coordinates දත්ත Child RVT ගොනුවට Publish කර Save කළ යුතුය.
