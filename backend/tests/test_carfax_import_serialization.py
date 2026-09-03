from datetime import date

from backend.routes.maintenance_import import serialize_import_records
from backend.services.carfax_importer import ParsedCarfaxReport, ParsedServiceRecord, make_source_record_key


def test_long_carfax_work_description_is_stored_in_notes_with_a_valid_key():
    full_description = "; ".join(["Recommended maintenance performed"] * 20)
    report = ParsedCarfaxReport(
        vin="1HGCP3F89BA028384",
        vehicle="2011 HONDA ACCORD",
        year=2011,
        make="Honda",
        model="ACCORD",
        fuel_type="gas",
        records=[
            ParsedServiceRecord(
                date_of_service=date(2025, 1, 1),
                mileage=100000,
                service_provider="Example Service",
                work_items=[full_description],
                page=1,
            )
        ],
    )

    record = serialize_import_records(report)[0]

    assert len(record["work_done"]) <= 500
    assert record["work_done"].endswith("...")
    assert full_description in record["notes"]
    assert record["source_record_key"] == make_source_record_key(
        report.vin,
        date(2025, 1, 1),
        100000,
        "Example Service",
        record["work_done"],
    )
    assert record["warnings"][-1].startswith("Work description was shortened")
