# lab-collage — review log

| Draft | Found | Fix |
|---|---|---|
| snap1 (pre-render) | red dots at 7.6, 8.3 and 10.2 s (round caps on hidden strokes); progress row visible before its page; 0.9 s of empty paper at the open; tape crossing "IN A BEDROOM"; ch2 headline late | `K.draw` hides strokes until their start; the row enters with the page; hero at beat 1, headline at beat 3; tape moved; h2a at `at(4,1)+0.1` |
| v1 | a ray crossing "IE" of "COPIES."; saw-tooth ends and corner spikes on torn strips | headline and caption last in DOM; `tornPolygon` points per ~9 px of measured size, shared corners |
| v2 | nothing paid off at the end | carried cassette slaps onto the end card (ending rhymes with the zoom-through) |
| v2b | the end cassette covered the "E" of HOME | moved to (770, 455) |
| v3 | ch2 caption finished typing 0.1 s before the peel, so it was unreadable | ch2 tail pulled 1 beat earlier, peel 1 beat later: caption done ~13.5 s, peel at 14.53 s (~1 s hold); DUR 18.28 s; bed recut to 18.6 s |
| **v4** | passes | accepted draft |

**v4 measurements** (`review/v4/`, framestudy at 8 fps):
- 18.3 s, 1080×1920, 30 fps.
- Cuts at 7.5 s (zoom-through) and 15.53 s (end title), both on the 128 BPM grid (3/3).
- Motion is spiky during builds and flat in holds.

**What passes:**
- Holds: ch1 is complete by about 6.6 s; the ch2 caption holds for about 1 s before the peel.
- No reads in the top 8 % or bottom 11 %.
- Headline, year and caption are readable at 360 px (`v4/phone_strip.jpg`).
- Every sticker is a keyword: 4-TRACK, 1983, DUB, SHARE.

**Known limits:**
- The first 0.4 s shows only the page and the blue strip. The hero and the first headline letter land by 1.1 s, which is inside the 2 s rule but not instant.
- It is a draft render using software GL.
