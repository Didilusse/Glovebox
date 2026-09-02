from datetime import date

import pytest

from backend.services.carfax_importer import parse_carfax_pages


@pytest.mark.parametrize(
    ("pages", "expected"),
    [
        (
            [
                """CARFAX Vehicle History Report for this 2019 NISSAN ALTIMA 2.5 SR: 1N4BL4CV6KC118592
Detailed History
10/25/2024
65,551
Hudson Nissan of Charleston
Vehicle serviced
-Oil and elter changed
-Tires rotated
10/26/2024
65,565
Kia Country of Charleston
Vehicle serviced
-Vehicle washed/detailed
CARFAX Vehicle History Report
Page 5 of 12""",
                """CARFAX Vehicle History Report
Page 6 of 12
02/21/2025
69,853
Walmart Auto Care Center
Vehicle serviced
-Four tires mounted
-Four tires balanced
-Tire(s) replaced
-Fll tires checked
Owner 3
Purchased: 2025
Personal Vehicle
10,415 mi/yr
Glossary""",
            ],
            {
                "vin": "1N4BL4CV6KC118592",
                "vehicle": "2019 NISSAN ALTIMA 2.5 SR",
                "records": 3,
                "items": {
                    date(2024, 10, 25): ["Oil and filter changed", "Tires rotated"],
                    date(2025, 2, 21): [
                        "Four tires mounted",
                        "Four tires balanced",
                        "Tire(s) replaced",
                        "Fll tires checked",
                    ],
                },
            },
        ),
        (
            [
                """CARFAX Vehicle History Report for this 2006 TOYOTA AVALON LIMITED: 4T1BK36B56U106843
Detailed History
10/23/2018
71,242
Ira Toyota of Danvers
Vehicle serviced
-Oil and ?lter changed
-Four tires balanced
-Four tires mounted
11/20/2023
91,008
JTM Motors
Vehicle serviced
-Recommended maintenance performed
-Oil and filter changed""",
                """CARFAX Vehicle History Report
Page 8 of 10
05/18/2025
89,684
JTM Motors
Vehicle serviced
-Oil and filter changed
-Tire condition and pressure checked
Glossary""",
            ],
            {
                "vin": "4T1BK36B56U106843",
                "vehicle": "2006 TOYOTA AVALON LIMITED",
                "records": 3,
                "items": {
                    date(2018, 10, 23): [
                        "Oil and filter changed",
                        "Four tires balanced",
                        "Four tires mounted",
                    ],
                },
                "warning_date": date(2025, 5, 18),
            },
        ),
        (
            [
                """CARFAX Vehicle History Report for this 2014 TOYOTA COROLLA LE: 2T1BURHE5EC097128
Detailed History
03/23/2018
29,248
Luther Brookdale Toyota
Vehicle serviced
-Oil and Flter changed
-Tires rotated
05/01/2018
32,264
Caliber Collision Center
Vehicle serviced
-Body electrical system checked
05/20/2018
Damage Report
Damage Severity
MINOR
05/30/2018
32,636
Luther Brookdale Toyota
Vehicle serviced
-Battery/charging system checked
-Battery replaced""",
                """CARFAX Vehicle History Report
Page 6 of 12
05/17/2022
55,202
Valvoline Instant Oil Change
Vehicle serviced
-Oil and filter changed
-Cabin air filter replaced/cleaned
Glossary""",
            ],
            {
                "vin": "2T1BURHE5EC097128",
                "vehicle": "2014 TOYOTA COROLLA LE",
                "records": 4,
                "items": {
                    date(2018, 3, 23): ["Oil and filter changed", "Tires rotated"],
                    date(2022, 5, 17): [
                        "Oil and filter changed",
                        "Cabin air filter replaced/cleaned",
                    ],
                },
            },
        ),
        (
            [
                """CARFAX Vehicle History Report for this 2017 VOLKSWAGEN JETTA 1.4T SE: 3VWB67AJ1HM215576
Detailed History
09/11/2020
43,244
Audi Burlington
Vehicle serviced
-Oil and Flter changed
-Brake fluid flushed/changed
03/05/2021
49,271
Jiffy Lube
Vehicle serviced
-Oil and filter changed
-Air fiter replaced
CARFAX Vehicle History Report
Page 7 of 10""",
                """CARFAX Vehicle History Report
Page 8 of 10
03/06/2024
80,303
Colonial Volkswagen of Medford
Vehicle serviced
-Power steering juid changed
-Transmission fluid changed
Glossary""",
            ],
            {
                "vin": "3VWB67AJ1HM215576",
                "vehicle": "2017 VOLKSWAGEN JETTA 1.4T SE",
                "records": 3,
                "items": {
                    date(2020, 9, 11): [
                        "Oil and filter changed",
                        "Brake fluid flushed/changed",
                    ],
                    date(2024, 3, 6): [
                        "Power steering fluid changed",
                        "Transmission fluid changed",
                    ],
                },
            },
        ),
    ],
    ids=["nissan-altima", "toyota-avalon", "toyota-corolla", "volkswagen-jetta"],
)
def test_real_carfax_report_regressions(pages, expected):
    """Sanitized Detailed History excerpts preserve report-specific parser edge cases."""
    report = parse_carfax_pages(pages)

    assert report.vin == expected["vin"]
    assert report.vehicle == expected["vehicle"]
    assert len(report.records) == expected["records"]

    records_by_date = {record.date_of_service: record for record in report.records}
    for service_date, work_items in expected["items"].items():
        assert records_by_date[service_date].work_items == work_items

    if warning_date := expected.get("warning_date"):
        assert any("lower than the prior" in warning for warning in records_by_date[warning_date].warnings)


def test_owner_history_does_not_leak_into_the_previous_service_visit():
    pages = [
        """CARFAX Vehicle History Report for this 2019 NISSAN ALTIMA 2.5 SR: 1N4BL4CV6KC118592
Detailed History
12/10/2025
83,666
Quick Stop Tire Shop
Vehicle serviced
-Oil and filter changed
Owner 4
Purchased: 2025
Personal Vehicle
7,654 mi/yr
Glossary"""
    ]

    report = parse_carfax_pages(pages)

    assert report.records[0].work_items == ["Oil and filter changed"]
