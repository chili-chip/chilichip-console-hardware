# Open points

What is left before the first order.

| # | Point | Status |
|---|---|---|
| 1 | Route the board | Not routed. Placement is final enough for routing; `scripts/route.py` autoroutes with Freerouting and pours ground |
| 2 | LCSC numbers for U5, L1, L2, J3, R30 | See the [parts list](parts.md#to-source) |
| 3 | Flash stock | C97521 shows 0 in stock today |
| 4 | Charge LED light hole | D1 sits in the top-left corner of the front. The shell needs a small hole or light pipe |
| 5 | USB-C moved 1 mm left | Casing model: `USB_X` 19.3 → 18.3 |
| 6 | Speaker position | J4 is at the right edge above the battery. Move it when the shell has a speaker spot |
| 7 | Panel over the antenna keep-out | 1 mm overlap in plan view. Test the range on the first boards |
| 8 | Firmware board file | Same pins as main board v4 with the 2.0" TFT (`dbi_st7789_scaled`). GP24 USB sense is optional |
| 9 | EU battery rule (issue #3) | The battery is on a plug and taped, so the user can replace it |
| 10 | Production test (issue #11) | 11 test pads on the back: power rails, SWD, RUN and the spare GPIOs |
| 11 | Bring-up | Order, assemble, flash, check every block |
