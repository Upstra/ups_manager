import unittest

from data_retriever.ups_telemetry import (
    parse_snmpget_output,
    parse_upsc_output,
    telemetry_from_nut,
    telemetry_from_snmp,
)


NUT_FULL = """battery.charge: 38
battery.runtime: 840
ups.status: OB DISCHRG
ups.load: 61
ups.realpower.nominal: 3000
ups.temperature: 31
input.voltage: 0
output.voltage: 230
output.frequency: 50
ups.mfr: APC
ups.model: Smart-UPS SRT 3000
"""


class UpsTelemetryTest(unittest.TestCase):
    def test_nut_full_output(self):
        telemetry = telemetry_from_nut(parse_upsc_output(NUT_FULL))
        self.assertTrue(telemetry["status"]["onBattery"])
        self.assertEqual(telemetry["battery"]["chargePercent"], 38)
        self.assertEqual(telemetry["load"]["realPowerW"], 1830)
        self.assertEqual(telemetry["temperatureC"], 31)
        self.assertEqual(telemetry["input"]["voltage"], 0)

    def test_nut_missing_fields_are_null(self):
        telemetry = telemetry_from_nut(parse_upsc_output("ups.status: OL\nbattery.runtime: 1500\n"))
        self.assertFalse(telemetry["status"]["onBattery"])
        self.assertIsNone(telemetry["battery"]["chargePercent"])
        self.assertIsNone(telemetry["load"]["realPowerW"])
        self.assertIsNone(telemetry["temperatureC"])

    def test_snmp_output_rebuilds_status(self):
        text = "\n".join([
            '.1.3.6.1.2.1.33.1.1.1.0 = STRING: "APC"',
            ".1.3.6.1.2.1.33.1.2.1.0 = INTEGER: 3",
            ".1.3.6.1.2.1.33.1.2.3.0 = INTEGER: 4",
            ".1.3.6.1.2.1.33.1.4.1.0 = INTEGER: 5",
            ".1.3.6.1.2.1.33.1.2.7.0 = No Such Object available on this agent at this OID",
        ])
        telemetry = telemetry_from_snmp(parse_snmpget_output(text))
        self.assertEqual(telemetry["status"]["raw"], "OB DISCHRG LB")
        self.assertTrue(telemetry["status"]["lowBattery"])
        self.assertEqual(telemetry["battery"]["runtimeSeconds"], 240)
        self.assertEqual(telemetry["device"]["manufacturer"], "APC")
        self.assertIsNone(telemetry["temperatureC"])


if __name__ == "__main__":
    unittest.main()
