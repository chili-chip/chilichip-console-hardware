"""Parts and nets of the chilichip console board, one list per schematic sheet.

Each part: (ref, "lib:symbol", value, footprint, lcsc, {pin: net}).
A pin mapped to None gets a no-connect flag. Every net is a global label, so the
sheets connect by name. gen_sch.py draws the schematic and gen_pcb.py the board
from this file, so the two always match.

The GPIO map is the same as main board v3/v4 (vgc-zero-hardware docs/console/pin-map.md),
so the console firmware runs unchanged. GP23, GP24 and GP25 were inside the RP2350-Plus;
here GP24 senses USB power and GP23/GP25 are spare test pads.
"""

R0402 = "Resistor_SMD:R_0402_1005Metric"
R0603 = "Resistor_SMD:R_0603_1608Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
TP = "TestPoint:TestPoint_Pad_D1.0mm"
LOCAL = "chilichip-console"

# LCSC part numbers, checked on lcsc.com 2026-11-27. Empty = not stocked or not checked yet.
LCSC = {
    ("R", "10k"): "C25744", ("R", "1k"): "C11702", ("R", "33R"): "C25105", ("R", "27R"): "C25100",
    ("R", "5.1k"): "C25905", ("R", "3.3k"): "C25890", ("R", "100k"): "C25741", ("R", "200k"): "C25764",
    ("R", "150k"): "C25755", ("R", "470R"): "C25117", ("R", "4.7k"): "C25900", ("R", "510k"): "C23192",
    ("C", "100nF"): "C1525", ("C", "15pF"): "C1548", ("C", "4.7uF"): "C23733", ("C", "1uF"): "C52923",
    ("C", "10uF"): "C19702", ("C", "10uF 25V"): "C15850", ("C", "22uF"): "C45783", ("C", "4.7uF 16V"): "C19666",
}


def r(ref, val, a, b, fp=R0402):
    return (ref, "Device:R", val, fp, LCSC.get(("R", val), ""), {"1": a, "2": b})


def c(ref, val, a, b="GND", fp=C0402):
    return (ref, "Device:C", val, fp, LCSC.get(("C", val), ""), {"1": a, "2": b})


def tp(ref, net, label):
    return (ref, "Connector:TestPoint", label, TP, "", {"1": net})


GPIO = {
    0: "UTIL_SDA", 1: "UTIL_SCL", 2: "UTIL_INT", 3: "AUDIO_DIN", 4: "AUDIO_BCLK", 5: "AUDIO_LRCLK",
    6: "AUDIO_MODE", 7: "BTN_A", 8: "BTN_B", 9: "WIFI_ON", 10: "BTN_Y", 11: "BTN_X", 12: "BTN_SELECT",
    13: "WIFI_CS", 14: "WIFI_CLK", 15: "WIFI_DIO", 16: "BTN_DOWN", 17: "BTN_RIGHT", 18: "BTN_START",
    19: "BTN_UP", 20: "BTN_LEFT", 21: "DISP_RST", 22: "DISP_DC", 23: "GP23", 24: "VBUS_SENSE",
    25: "GP25", 26: "DISP_CLK", 27: "DISP_DIN", 28: "DISP_CS", 29: "VSYS_SENSE",
}
# RP2350A QFN-60 pin number of each GPIO
GPIO_PIN = {0: 2, 1: 3, 2: 4, 3: 5, 4: 7, 5: 8, 6: 9, 7: 10, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16,
            13: 17, 14: 18, 15: 19, 16: 27, 17: 28, 18: 29, 19: 31, 20: 32, 21: 33, 22: 34, 23: 35,
            24: 36, 25: 37, 26: 40, 27: 41, 28: 42, 29: 43}

u1 = {str(p): GPIO[g] for g, p in GPIO_PIN.items()}
u1.update({p: "+3V3" for p in ("1", "11", "20", "30", "38", "45", "44", "49", "53", "54")})
u1.update({p: "+1V1" for p in ("6", "23", "39", "50")})
u1.update({"46": "VREG_AVDD", "47": "GND", "48": "VREG_LX", "61": "GND",
           "21": "XIN", "22": "XOUT", "24": "SWCLK", "25": "SWDIO", "26": "RUN",
           "51": "USB_DM_MCU", "52": "USB_DP_MCU",
           "55": "QSPI_SD3", "56": "QSPI_SCLK", "57": "QSPI_SD0", "58": "QSPI_SD2", "59": "QSPI_SD1", "60": "QSPI_SS"})

# Sheet 1: RP2350A, flash, crystal, core supply, USB data, boot and debug.
# From Raspberry Pi's RP2350A minimal design R4 (reference/rp2350a-minimal).
MCU = [
    ("U1", "MCU_RaspberryPi:RP2350A", "RP2350A", "Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm_ThermalVias", "C42411118", u1),
    ("U2", "Memory_Flash:W25Q32JVSS", "W25Q128JVSIQ", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", "C97521",
     {"1": "QSPI_SS", "2": "QSPI_SD1", "3": "QSPI_SD2", "4": "GND", "5": "QSPI_SD0", "6": "QSPI_SCLK", "7": "QSPI_SD3", "8": "+3V3"}),
    r("R1", "10k", "+3V3", "QSPI_SS"),
    c("C1", "100nF", "+3V3"),
    ("Y1", "Device:Crystal_GND24", "12MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "C9002",
     {"1": "XIN", "2": "GND", "3": "XTAL_OUT", "4": "GND"}),
    r("R2", "1k", "XOUT", "XTAL_OUT"),
    c("C2", "15pF", "XIN"), c("C3", "15pF", "XTAL_OUT"),
    # core regulator: internal switcher, 3.3 uH inductor, 1.1 V out
    ("L1", "Device:L", "3.3uH", "Inductor_SMD:L_Abracon_AOTA-B201610S", "", {"1": "VREG_LX", "2": "+1V1"}),
    r("R3", "33R", "+3V3", "VREG_AVDD"), c("C4", "4.7uF", "VREG_AVDD"),
    c("C5", "4.7uF", "+3V3"),  # VREG_VIN
    c("C6", "4.7uF", "+1V1"), c("C7", "100nF", "+1V1"), c("C8", "100nF", "+1V1"), c("C9", "100nF", "+1V1"),
    # IOVDD, ADC_AVDD, USB_OTP_VDD, QSPI_IOVDD
    c("C10", "100nF", "+3V3"), c("C11", "100nF", "+3V3"), c("C12", "100nF", "+3V3"), c("C13", "100nF", "+3V3"),
    c("C14", "100nF", "+3V3"), c("C15", "100nF", "+3V3"), c("C16", "100nF", "+3V3"), c("C17", "10uF", "+3V3", fp=C0603),
    r("R4", "27R", "USB_DP_MCU", "USB_DP"), r("R5", "27R", "USB_DM_MCU", "USB_DM"),
    # BOOTSEL: hold while resetting to get the USB drive. RUN: reset.
    r("R6", "1k", "QSPI_SS", "BOOTSEL"),
    ("SW1", "Switch:SW_Push", "BOOTSEL", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "C318884", {"1": "BOOTSEL", "2": "GND"}),
    r("R7", "1k", "RUN_SW", "GND"),
    ("SW2", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "C318884", {"1": "RUN", "2": "RUN_SW"}),
    tp("TP1", "SWCLK", "SWCLK"), tp("TP2", "SWDIO", "SWDIO"), tp("TP3", "RUN", "RUN"),
    tp("TP4", "GP23", "GP23"), tp("TP5", "GP25", "GP25"), tp("TP6", "+1V1", "1V1"),
]

# Sheet 2: USB-C, charger, power path, 3.3 V buck-boost, battery and sense dividers.
POWER = [
    ("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND",
      "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
      "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM", "A8": None, "B8": None}),
    r("R10", "5.1k", "CC1", "GND"), r("R11", "5.1k", "CC2", "GND"),
    ("U3", "Power_Protection:USBLC6-2P6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", "C7519",
     {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "2": "GND", "5": "VBUS"}),
    c("C20", "10uF 25V", "VBUS", fp=C0805),
    # Charger: 1000 V / 3.3 kOhm = 300 mA, about 0.75 C for the 400 mAh 502540 cell
    ("U4", "Battery_Management:MCP73831-2-OT", "MCP73831T-2ACI/OT", "Package_TO_SOT_SMD:SOT-23-5", "C424093",
     {"1": "CHG_STAT", "2": "GND", "3": "VBAT", "4": "VBUS", "5": "CHG_PROG"}),
    r("R12", "3.3k", "CHG_PROG", "GND"),
    c("C21", "4.7uF 16V", "VBAT", fp=C0603),
    ("D1", "Device:LED", "Red", "LED_SMD:LED_0603_1608Metric", "C2286", {"1": "CHG_STAT", "2": "CHG_LED"}),
    r("R13", "1k", "VBUS", "CHG_LED"),
    # Power path, as on the Pico and the RP2350-Plus: USB through D2, battery through Q1 when USB is out
    ("D2", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123", "C8598", {"1": "VSYS", "2": "VBUS"}),
    ("Q1", "Transistor_FET:Q_PMOS_GSD", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "C15127", {"1": "VBUS", "2": "VSYS", "3": "VBAT"}),
    r("R14", "100k", "VBUS", "GND"),
    ("J2", "Connector_Generic:Conn_01x02", "Battery", "Connector_Molex:Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal", "C177225",
     {"1": "VBAT", "2": "GND"}),
    # 3.3 V buck-boost: keeps 3.3 V down to an almost empty cell
    ("U5", "Regulator_Switching:TPS63030DSK", "TPS63031DSKR", "Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm_ThermalVias", "",
     {"1": "+3V3", "2": "BB_L2", "3": "GND", "4": "BB_L1", "5": "VSYS", "6": "VSYS", "7": "GND", "8": "VSYS", "9": "GND",
      "10": "+3V3", "11": "GND"}),
    ("L2", "Device:L", "1.5uH", "Inductor_SMD:L_APV_ANR252012", "", {"1": "BB_L1", "2": "BB_L2"}),
    c("C22", "10uF 25V", "VSYS", fp=C0805), c("C23", "100nF", "VSYS"),
    c("C24", "22uF", "+3V3", fp=C0805), c("C25", "22uF", "+3V3", fp=C0805),
    # Battery level (ADC3) and USB power sense
    r("R15", "200k", "VSYS", "VSYS_SENSE"), r("R16", "100k", "VSYS_SENSE", "GND"),
    r("R17", "100k", "VBUS", "VBUS_SENSE"), r("R18", "150k", "VBUS_SENSE", "GND"),
    tp("TP7", "VBUS", "VBUS"), tp("TP8", "VBAT", "VBAT"), tp("TP9", "VSYS", "VSYS"),
    tp("TP10", "+3V3", "3V3"), tp("TP11", "GND", "GND"),
]

# Sheet 3: 2.0" TFT (buydisplay ER-TFT020-3, ST7789). Same circuit as the TFT display module.
DISPLAY = [
    ("J3", "Connector_Generic_MountingPin:Conn_01x14_MountingPin", "FH12-14S-0.5SH",
     "Connector_FFC-FPC:Hirose_FH12-14S-0.5SH_1x14-1MP_P0.50mm_Horizontal", "",
     {"1": None, "2": "GND", "3": "LED_K", "4": "LED_A", "5": "GND", "6": "DISP_RST", "7": "DISP_DC",
      "8": "DISP_DIN", "9": "DISP_CLK", "10": "+3V3", "11": "+3V3", "12": "DISP_CS", "13": "GND", "14": None,
      "MP": "GND"}),
    c("C30", "100nF", "+3V3"), c("C31", "4.7uF 16V", "+3V3", fp=C0603),
    r("R30", "6.8R", "+3V3", "LED_A", fp=R0603),
    ("Q2", "Transistor_FET:Q_NMOS_GSD", "AO3400A", "Package_TO_SOT_SMD:SOT-23", "C20917", {"1": "DISP_RST", "2": "GND", "3": "LED_K"}),
    r("R31", "100k", "DISP_RST", "GND"),
]

# Sheet 4: I2S amplifier. Same circuit as the audio module v1.1.1.
AUDIO = [
    ("U6", "Audio:MAX98357A", "MAX98357A", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias", "C910544",
     {"1": "AUDIO_DIN", "16": "AUDIO_BCLK", "14": "AUDIO_LRCLK", "4": "SD_MODE", "2": "GND", "3": "GND", "11": "GND",
      "15": "GND", "17": "GND", "7": "+3V3", "8": "+3V3", "9": "SPK_P", "10": "SPK_N",
      "5": None, "6": None, "12": None, "13": None}),
    r("R40", "510k", "AUDIO_MODE", "SD_MODE", fp=R0603),  # 0.54 V on SD_MODE: (L+R)/2 mono
    c("C40", "10uF", "+3V3", fp=C0603), c("C41", "100nF", "+3V3"),
    ("J4", "Connector_Generic:Conn_01x02", "Speaker", "Connector_Molex:Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal", "C177225",
     {"1": "SPK_P", "2": "SPK_N"}),
]

# Sheet 5: Raspberry Pi Radio Module 2 (CYW43439), wired like the Pico W.
RADIO = [
    ("U7", f"{LOCAL}:RPI_RMC20452T", "RM2", "RF_Module:RMC20452T", "",
     {"1": "GND", "2": None, "3": "WIFI_CLK", "4": "GND", "5": "WIFI_DIO", "6": "WIFI_DO", "7": "GND", "8": None,
      "9": "WIFI_CS", "10": "WIFI_IRQ", "11": "GND", "12": "WIFI_ON", "13": "WIFI_ON", "14": "+3V3", "15": "GND",
      "16": "+3V3", "17": None, "18": None, "19": None, "20": None, "21": "GND"}),
    r("R50", "470R", "WIFI_DIO", "WIFI_DO"), r("R51", "10k", "WIFI_DIO", "WIFI_IRQ"),
    c("C50", "10uF", "+3V3", fp=C0603), c("C51", "100nF", "+3V3"),
]

# Sheet 6: IMU, RTC and haptics. Same circuit as the utility module v2.0.0.
UTILITY = [
    ("U8", f"{LOCAL}:LSM6DS3TR-C", "LSM6DS3TR-C", "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y", "C967633",
     {"12": "+3V3", "5": "+3V3", "8": "+3V3", "4": "UTIL_INT", "13": "UTIL_SCL", "14": "UTIL_SDA",
      "1": "GND", "2": "GND", "3": "GND", "6": "GND", "7": "GND", "9": None, "10": None, "11": None}),
    c("C60", "100nF", "+3V3"), c("C61", "100nF", "+3V3"),
    ("U9", f"{LOCAL}:RV-3028-C7", "RV-3028-C7", f"{LOCAL}:MicroCrystal_C7_SON-8_1.5x3.2mm_P0.9mm", "C3019759",
     {"7": "+3V3", "2": "UTIL_INT", "3": "UTIL_SCL", "4": "UTIL_SDA", "6": "VSYS", "5": "GND", "8": "RTC_EVI", "1": None}),
    c("C62", "100nF", "+3V3"), c("C63", "100nF", "VSYS"), r("R60", "10k", "RTC_EVI", "GND"),
    ("U10", f"{LOCAL}:DRV2605L", "DRV2605L", "Package_SO:TSSOP-10_3x3mm_P0.5mm", "C527464",
     {"10": "+3V3", "5": "+3V3", "6": "+3V3", "2": "UTIL_SCL", "3": "UTIL_SDA", "4": "GND", "8": "GND",
      "1": "DRV_REG", "7": "MOT_P", "9": "MOT_N"}),
    c("C64", "1uF", "+3V3"), c("C65", "100nF", "+3V3"), c("C66", "1uF", "DRV_REG"),
    ("M1", f"{LOCAL}:Motor_ERM", "VZ43FC1B5640007L", f"{LOCAL}:Motor_ERM_SMD_Vybronics_VZ43FC1B", "", {"1": "MOT_P", "2": "MOT_N"}),
    r("R61", "4.7k", "+3V3", "UTIL_SDA"), r("R62", "4.7k", "+3V3", "UTIL_SCL"), r("R63", "10k", "+3V3", "UTIL_INT"),
]

# Sheet 7: GBA-style rubber dome pads (Pigweed Kudzu footprints, CC BY 4.0). Internal pull-ups in the RP2350.
BUTTONS = [
    ("SW10", f"{LOCAL}:AGB_DPAD", "D-pad", f"{LOCAL}:GBA_DPad", "",
     {"1": "BTN_UP", "2": "BTN_DOWN", "3": "BTN_LEFT", "4": "BTN_RIGHT", "5": "GND"}),
    ("SW11", f"{LOCAL}:AGB_AB", "B / A", f"{LOCAL}:GBA_AB", "", {"1": "BTN_B", "2": "BTN_A", "3": "GND"}),
    ("SW12", f"{LOCAL}:AGB_AB", "X / Y", f"{LOCAL}:GBA_AB", "", {"1": "BTN_X", "2": "BTN_Y", "3": "GND"}),
    ("SW13", f"{LOCAL}:AGB_SELECT_START", "Start / Select", f"{LOCAL}:GBA_StartSelect", "",
     {"1": "BTN_START", "2": "BTN_SELECT", "3": "GND"}),
]

SHEETS = [
    ("mcu", "MCU", "RP2350A, FLASH, CRYSTAL, BOOT AND DEBUG", MCU),
    ("power", "Power", "USB-C, CHARGER, POWER PATH, 3.3 V", POWER),
    ("display", "Display", "2.0 INCH TFT (ER-TFT020-3)", DISPLAY),
    ("audio", "Audio", "I2S AMPLIFIER (MAX98357A)", AUDIO),
    ("radio", "Radio", "WI-FI AND BLUETOOTH (RM2)", RADIO),
    ("utility", "Utility", "IMU, RTC AND HAPTICS", UTILITY),
    ("buttons", "Buttons", "BUTTONS", BUTTONS),
]

# Copper only, no part to buy or place (rubber-dome contacts)
NO_BOM = {"SW10", "SW11", "SW12", "SW13"}

# Nets that are rails: drawn as power symbols would be, and given a PWR_FLAG where nothing drives them.
FLAGS = ["+1V1", "VREG_AVDD", "VSYS", "VBUS", "GND"]


def all_parts():
    return [p for _, _, _, parts in SHEETS for p in parts]
