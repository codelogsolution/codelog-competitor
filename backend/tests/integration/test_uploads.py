from app.core.config import settings
from datetime import date, timedelta


def make_csv():
    headers = (
        "competitor_name,domain,source_type,source_url,category,"
        "signal_type,signal_text,signal_date,sentiment,frequency,"
        "keyword_gap,product_area,keyword_volume,ranking_gap"
    )

    row = (
        f"Deel,deel.com,g2,https://www.g2.com/products/deel,EOR,"
        f"review_theme,Payroll support delays,{date.today().isoformat()},"
        f"negative,30,,EOR,,"
    )

    return f"{headers}\n{row}\n"


def test_successful_csv_upload(client, upload_dir):
    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "deel_reviews.csv",
                make_csv().encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["original_filename"] == "deel_reviews.csv"
    assert data["total_records"] == 1
    assert data["valid_records"] == 1
    assert data["invalid_records"] == 0

    assert (upload_dir / data["stored_filename"]).exists()


def test_delete_source_removes_original_file_but_hides_source_record(client, upload_dir):
    uploaded = client.post(
        "/api/v1/uploads",
        files={"file": ("remove_me.csv", make_csv().encode("utf-8"), "text/csv")},
    )
    assert uploaded.status_code == 200
    data = uploaded.json()
    assert (upload_dir / data["stored_filename"]).exists()

    deleted = client.delete(f"/api/v1/uploads/{data['import_id']}")
    assert deleted.status_code == 200
    assert not (upload_dir / data["stored_filename"]).exists()
    assert client.get("/api/v1/uploads").json() == []
    assert client.get(f"/api/v1/uploads/{data['import_id']}").status_code == 404
    assert "Audit history is retained" in deleted.json()["message"]


def test_unsupported_file_extension(client):
    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "reviews.txt",
                b"some text",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_missing_required_csv_column(client):
    csv_content = (
        "competitor_name,domain,source_type\n"
        "Deel,deel.com,g2\n"
    )

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "incomplete.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


def test_empty_csv_upload(client):
    response = client.post(
        "/api/v1/uploads",
        files={"file": ("empty.csv", b"", "text/csv")},
    )

    assert response.status_code == 400


def test_missing_source_url_generates_warning(client):
    csv_content = make_csv().replace(
        "https://www.g2.com/products/deel",
        "",
    )

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "missing_url.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["warning_records"] == 1
    assert data["invalid_records"] == 0
    assert any(
        "Source URL missing" in warning["message"]
        for warning in data["warnings"]
    )


def test_future_signal_date_generates_warning(client):
    future_date = (date.today() + timedelta(days=30)).isoformat()

    csv_content = make_csv().replace(
        date.today().isoformat(),
        future_date,
    )

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "future_date.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["warning_records"] == 1
    assert any(
        "Signal date is in the future" in warning["message"]
        for warning in data["warnings"]
    )


def test_oversized_upload_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "large.csv",
                b"x" * (1024 * 1024 + 1),
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert "exceeds maximum size" in response.json()["detail"]

def test_upload_accepts_csv_without_optional_columns(client):
    csv_content = (
        "competitor_name,domain,category,signal_type,signal_text,source_type\n"
        "Deel,deel.com,EOR,review_theme,Payroll support delays,g2\n"
    )

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "minimal.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_records"] == 1
    assert data["invalid_records"] == 0
    assert data["warning_records"] == 1
    assert data["records"][0]["validation_status"] == "warning"


def test_duplicate_detection_uses_four_field_identity(client):
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    csv_content = (
        "competitor_name,domain,source_type,source_url,category,"
        "signal_type,signal_text,signal_date,sentiment,frequency\n"
        f"Deel,deel.com,g2,https://www.g2.com/deel,EOR,"
        f"review_theme,Payroll support delays,{today},negative,30\n"
        f"Deel,deel.com,capterra,https://www.g2.com/deel,EOR,"
        f"review_theme, payroll   SUPPORT DELAYS ,{yesterday},negative,30\n"
    )

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "duplicate_reviews.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_records"] == 2
    assert data["valid_records"] == 1
    assert data["warning_records"] == 1
    assert any(
        "Duplicate evidence detected" in warning["message"]
        for warning in data["warnings"]
    )

def test_keyword_gap_signal_does_not_require_keyword_gap_field(client):
    csv_content = (
        "competitor_name,domain,source_type,source_url,category,"
        "signal_type,signal_text,signal_date,sentiment,frequency\n"
        "Deel,deel.com,semrush,https://www.semrush.com,EOR,"
        "keyword_gap,Organic keyword opportunity,"
        f"{date.today().isoformat()},unknown,0\n"
    )

    response = client.post(
        "/api/v1/uploads",
        files={
            "file": (
                "seo_evidence.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 1
    assert data["invalid_records"] == 0
