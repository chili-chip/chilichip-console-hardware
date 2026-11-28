# Open points

What is left before the first order.

| # | Point | Status |
|---|---|---|
| 1 | Finish routing | 3 connections are open at U1 (RP2350): pin 39 and pin 23 to +1V1, pin 35 (GP23) to test pad TP4. Freerouting cannot reach them because the pins around them are full. Fix by hand in KiCad (push-and-shove router), or drop TP4 since GP23 is a spare |
| 1a | Vias under the RM2 | Tented ground vias sit under the RM2 body (not under the antenna). Check this against the RM2 datasheet before ordering |
| 2 | LCSC numbers for U5, L1, L2, J3, R30 | See the [parts list](parts.md#to-source) |
| 3 | Flash stock | C97521 shows 0 in stock today |
| 4 | Charge LED light pipe | D1 at (8, 2) on the front. The casing has a 1.6 mm frosted pipe over it; check the light on the first boards |
| 5 | USB-C moved 1 mm left | Casing model: `USB_X` 19.3 → 18.3 |
| 6 | Speaker position | J4 is at the right edge above the battery. Move it when the shell has a speaker spot |
| 7 | Radio range | Panel (y 5.7 to 40.3) is clear of the antenna keep-out. Test the range on the first boards |
| 8 | Firmware board file | Same pins as main board v4 with the 2.0" TFT (`dbi_st7789_scaled`). GP24 USB sense is optional |
| 9 | EU battery rule (issue #3) | The battery is on a plug and taped, so the user can replace it |
| 10 | Production test (issue #11) | 11 test pads on the back: power rails, SWD, RUN and the spare GPIOs |
| 11 | Bring-up | Order, assemble, flash, check every block |
