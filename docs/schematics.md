# Schematics

Seven sheets, one per block. Every pin has a label with its net name, so the sheets connect by name. The schematic is generated from `scripts/design.py`; see [work on the board](develop.md). Click a sheet to open it full size.

| Sheet | What is on it |
|---|---|
| [MCU](#mcu) | RP2350A, flash, crystal, core supply, USB data, BOOTSEL and RESET, SWD pads |
| [Power](#power) | USB-C, ESD, charger, power path, buck-boost, battery, sense dividers |
| [Display](#display) | FPC connector and backlight switch |
| [Audio](#audio) | MAX98357A and the speaker connector |
| [Radio](#radio) | RM2 |
| [Utility](#utility) | IMU, RTC, haptic driver, motor |
| [Buttons](#buttons) | Rubber-dome contacts |

## MCU

[![MCU sheet](schematics/mcu.svg){ loading=lazy }](schematics/mcu.svg)

## Power

[![Power sheet](schematics/power.svg){ loading=lazy }](schematics/power.svg)

## Display

[![Display sheet](schematics/display.svg){ loading=lazy }](schematics/display.svg)

## Audio

[![Audio sheet](schematics/audio.svg){ loading=lazy }](schematics/audio.svg)

## Radio

[![Radio sheet](schematics/radio.svg){ loading=lazy }](schematics/radio.svg)

## Utility

[![Utility sheet](schematics/utility.svg){ loading=lazy }](schematics/utility.svg)

## Buttons

[![Buttons sheet](schematics/buttons.svg){ loading=lazy }](schematics/buttons.svg)
