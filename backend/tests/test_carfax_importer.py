from backend.services.carfax_importer import CarfaxParseError, parse_carfax_pages


SAMPLE_SERVICE_ROWS = [
    ("05/29/2011", None, "Nucar Honda of Westford", ["Pre-delivery inspection completed"]),
    ("09/30/2011", None, "Nucar Honda of Westford", ["Emissions or safety inspection performed"]),
    ("07/27/2012", 8470, "Nucar Honda of Westford", ["Recommended maintenance performed", "Oil and dlter changed"]),
    ("07/12/2013", 17228, "Nucar Honda of Westford", ["7,500 mile service performed", "Four wheel alignment performed", "Oil and dlter changed", "Tire condition and pressure checked", "Tires rotated"]),
    ("07/31/2014", 25726, "Nucar Honda of Westford", ["Cabin air dlter replaced/cleaned", "Oil and dlter changed", "Tires rotated"]),
    ("06/20/2015", 34157, "Nucar Honda of Westford", ["Recommended maintenance performed", "Transmission huid changed"]),
    ("09/14/2015", None, "Ronnie's Total Car Care", ["Emissions or safety inspection performed"]),
    ("05/12/2016", None, "Nucar Honda of Westford", ["Air dlter replaced", "Oil and dlter changed", "Tires rotated"]),
    ("09/10/2016", 42009, "Ronnie's Total Car Care", ["Emissions or safety inspection performed"]),
    ("03/16/2017", 51418, "Nucar Honda of Westford", ["Air dlter replaced", "Oil and dlter changed", "Tires rotated"]),
    ("05/06/2017", None, "Ronnie's Total Car Care", ["Brake caliper(s) replaced"]),
    ("11/09/2017", 60102, "Nucar Honda of Westford", ["Brake huid hushed/changed", "Oil and dlter changed", "Tires rotated", "Transmission huid changed"]),
    ("11/22/2017", None, "Ronnie's Total Car Care", ["Light bulb(s) replaced"]),
    ("09/25/2018", 68460, "Nucar Honda of Westford", ["Air dlter replaced", "Brakes checked", "Tires rotated"]),
    ("12/08/2018", 70812, "Ronnie's Total Car Care", ["Brakes checked", "Rear brake caliper(s) replaced", "Rear brake pads replaced"]),
    ("06/26/2019", 74523, "Nucar Honda of Westford", ["Oil and dlter changed", "Power steering huid hushed/changed"]),
    ("09/07/2019", None, "Ronnie's Total Car Care", ["Front wheel bearing(s)/hub(s) replaced", "Wheel bearing(s) serviced"]),
    ("01/31/2020", 80887, "Ronnie's Total Car Care", ["Brakes serviced", "Rear brakes serviced/adjusted"]),
    ("05/12/2020", 83213, "Nucar Honda of Westford", ["Antifreeze/coolant hushed/changed", "Oil and dlter changed", "Serpentine belt replaced", "Timing belt replaced", "Timing belt tensioner/idler replaced", "Tires rotated", "Water pump gasket replaced", "Water pump replaced"]),
    ("09/15/2020", None, "Ronnie's Total Car Care", ["Emissions or safety inspection performed"]),
    ("04/07/2021", 88411, "Ronnie's Total Car Care", ["Tire condition and pressure checked", "Tire pressure sensor replaced"]),
    ("09/14/2021", 89784, "Ronnie's Total Car Care", ["Four tires balanced", "Four tires mounted", "Tire repaired", "Wheel(s) repaired"]),
    ("02/22/2022", 90987, "Ronnie's Total Car Care", ["Brake huid hushed/changed", "Oil and dlter changed", "Transmission huid changed", "Transmission huid hushed"]),
    ("04/11/2023", None, "Ronnie's Total Car Care", ["A/C refrigerant recharged"]),
    ("10/24/2023", 94986, "Ronnie's Total Car Care", ["Alternator replaced"]),
    ("01/19/2024", None, "Lexington Toyota", ["Pre-delivery inspection completed", "Air dlter replaced", "Front brake pads replaced", "Front brake rotor(s) replaced", "Oil and dlter changed", "Rear brake pads replaced", "Rear brake rotor(s) replaced", "Tires rotated"]),
    ("08/13/2024", 97178, "Valvoline Instant Oil Change", ["Cabin air dlter replaced/cleaned", "Front wiper blades/redlls replaced", "Oil and dlter changed"]),
    ("02/01/2025", 101991, "Valvoline Instant Oil Change", ["Oil and dlter changed", "Power steering huid hushed/changed"]),
    ("12/29/2025", 108707, "Valvoline Instant Oil Change", ["Oil and dlter changed", "Tires rotated"]),
]


def sample_carfax_pages():
    lines = [
        "CARFAX Vehicle History Report for this 2011 HONDA ACCORD EX-L V6: 1HGCP3F89BA028384",
        "Recent Service Highlights",
        "12/29/2025 Oil and filter changed",
        "Detailed History",
        "09/14/2011",
        "Nucar Honda of Westford",
        "Vehicle sold",
        "09/10/2016",
        "46,284",
        "Massachusetts Inspection Station",
        "Passed safety inspection",
    ]
    for service_date, mileage, provider, work_items in SAMPLE_SERVICE_ROWS:
        lines.append(service_date)
        if mileage is not None:
            lines.append(f"{mileage:,}")
        lines.extend([provider, "Vehicle serviced", *work_items])
    lines.extend(["08/16/2026", "CARFAX Car Care", "Manufacturer Recommended Maintenance Schedules", "Glossary"])
    return ["\n".join(lines)]


def test_sample_report_parses_all_service_visits_without_inference():
    report = parse_carfax_pages(sample_carfax_pages())

    assert report.vin == "1HGCP3F89BA028384"
    assert report.vehicle == "2011 HONDA ACCORD EX-L V6"
    assert (report.year, report.make, report.model) == (2011, "Honda", "ACCORD EX-L V6")
    assert len(report.records) == 29
    assert sum(record.mileage is None for record in report.records) == 10

    may_2020 = next(record for record in report.records if record.date_of_service.isoformat() == "2020-05-12")
    assert "Timing belt replaced" in may_2020.work_items
    assert "Water pump replaced" in may_2020.work_items
    assert "Oil and filter changed" in may_2020.work_items

    jan_2024 = next(record for record in report.records if record.date_of_service.isoformat() == "2024-01-19")
    assert jan_2024.mileage is None
    assert "Front brake pads replaced" in jan_2024.work_items

    latest = report.records[-1]
    assert latest.mileage == 108707
    assert latest.work_items == ["Oil and filter changed", "Tires rotated"]
    assert all(record.work_done != "Oil and filter changed" for record in report.records[:2])


def test_parser_rejects_non_carfax_text():
    try:
        parse_carfax_pages(["Not a vehicle report"])
    except CarfaxParseError as exc:
        assert "CARFAX" in str(exc)
    else:
        raise AssertionError("Expected a parse error")


def test_layout_columns_do_not_become_service_items():
    report = parse_carfax_pages([
        "\n".join([
            "CARFAX Vehicle History Report for this 2011 HONDA ACCORD: 1HGCP3F89BA028384",
            "Detailed History",
            "07/27/2012    8,470    Nucar Honda of Westford                 Vehicle serviced",
            "                         Westford, MA                          -Recommended maintenance performed",
            "                         978-589-4200                          -Oil and filter changed",
            "Glossary",
        ])
    ])
    assert report.records[0].service_provider == "Nucar Honda of Westford"
    assert report.records[0].work_items == [
        "Recommended maintenance performed",
        "Oil and filter changed",
    ]
