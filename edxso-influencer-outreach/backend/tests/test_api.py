from unittest.mock import AsyncMock, patch

from app.models.influencer import Influencer
from app.models.outreach_message import OutreachMessage


def test_root_endpoint(client):
    """Test the API root welcome and status endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "EDXSO Influencer Outreach API" in data["message"]


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_and_get_influencer(client):
    """Test creating an influencer and retrieving by ID."""
    payload = {
        "name": "Jane Fitness Pro",
        "platform": "YouTube",
        "profile_url": "https://www.youtube.com/channel/UC_JANE_FITNESS_01",
        "follower_count": 15000,
        "engagement_rate": 3.2,
        "category": "Fitness",
        "content_themes": "Workout, Nutrition",
        "contact_email": "jane@example.com",
        "website": "https://janefit.com",
        "geography": "United States",
        "source_url": "https://www.youtube.com/channel/UC_JANE_FITNESS_01",
    }

    # Create influencer
    create_res = client.post("/api/influencers", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["id"] is not None
    assert created_data["name"] == payload["name"]

    # Duplicate creation on same platform & profile_url should return 409
    dup_res = client.post("/api/influencers", json=payload)
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]

    # Retrieve created influencer
    get_res = client.get(f"/api/influencers/{created_data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == payload["name"]

    # Retrieve non-existent influencer returns 404
    missing_res = client.get("/api/influencers/999999")
    assert missing_res.status_code == 404


def test_list_influencers(client, sample_qualified_influencer, sample_pending_influencer):
    """Test listing all influencers."""
    response = client.get("/api/influencers")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    names = [item["name"] for item in items]
    assert sample_qualified_influencer.name in names
    assert sample_pending_influencer.name in names


@patch("app.main.YouTubeProvider")
def test_discovery_youtube(mock_provider_class, client):
    """Test YouTube influencer discovery endpoint with mocked provider."""
    mock_instance = mock_provider_class.return_value
    mock_instance.discover_fitness_channels = AsyncMock(
        return_value=[
            {
                "name": "Discovered Channel 1",
                "platform": "YouTube",
                "profile_url": "https://www.youtube.com/channel/UC_DISCOVERED_01",
                "follower_count": 12000,
                "engagement_rate": 2.5,
                "category": "Fitness",
                "content_themes": "Workout tips",
                "contact_email": None,
                "website": None,
                "geography": "US",
                "source_url": "https://www.youtube.com/channel/UC_DISCOVERED_01",
            },
            {
                "name": "Discovered Channel 2",
                "platform": "YouTube",
                "profile_url": "https://www.youtube.com/channel/UC_DISCOVERED_02",
                "follower_count": 45000,
                "engagement_rate": 4.1,
                "category": "Fitness",
                "content_themes": "Diet and training",
                "contact_email": "collab@channel2.com",
                "website": None,
                "geography": "UK",
                "source_url": "https://www.youtube.com/channel/UC_DISCOVERED_02",
            },
        ]
    )

    response = client.post("/api/discovery/youtube?target=2")
    assert response.status_code == 200
    data = response.json()
    assert data["discovered"] == 2
    assert data["inserted"] == 2
    assert data["duplicates_skipped"] == 0

    # Running discovery again with same records should skip duplicates
    second_run = client.post("/api/discovery/youtube?target=2")
    assert second_run.status_code == 200
    second_data = second_run.json()
    assert second_data["inserted"] == 0
    assert second_data["duplicates_skipped"] == 2


@patch("app.main.YouTubeProvider")
def test_enrich_influencers(mock_provider_class, client, sample_pending_influencer):
    """Test enriching stored influencers with public metadata."""
    mock_instance = mock_provider_class.return_value
    mock_instance.get_channels = AsyncMock(
        return_value=[
            {
                "channel_id": "UC_SAM_WELLNESS_02",
                "title": "Sam Wellness",
                "description": "Yoga and wellness channel for healthy living. Contact: sam@example.com",
                "subscriber_count": 50000,
                "video_count": 120,
                "view_count": 1500000,
            }
        ]
    )

    response = client.post("/api/influencers/enrich")
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 1
    assert data["enriched"] + data["needs_review"] == 1


@patch("app.main.qualify_influencer")
@patch("app.main.YouTubeProvider")
def test_qualify_influencers(mock_provider_class, mock_qualify, client, sample_pending_influencer):
    """Test evaluating and qualifying influencers."""
    mock_qualify.return_value = {
        "id": sample_pending_influencer.id,
        "name": sample_pending_influencer.name,
        "qualification_status": "Qualified",
        "rejection_reasons": None,
        "metrics": {"followers": 50000, "engagement_rate": 4.2},
    }

    response = client.post("/api/influencers/qualify")
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 1
    assert data["qualified"] == 1
    assert data["rejected"] == 0


def test_outreach_generation_and_word_count_constraints(client, sample_qualified_influencer):
    """
    Test generating personalized outreach drafts and validating strict
    word count limits (Email: 60-90 words, Instagram DM: 15-30 words).
    """
    gen_res = client.post("/api/outreach/generate")
    assert gen_res.status_code == 200
    gen_data = gen_res.json()

    assert gen_data["qualified_influencers"] == 1
    assert gen_data["drafts_generated"] == 2
    assert gen_data["existing_drafts_skipped"] == 0

    # Retrieve generated drafts
    drafts_res = client.get("/api/outreach/drafts")
    assert drafts_res.status_code == 200
    drafts_data = drafts_res.json()
    assert drafts_data["total"] == 2

    email_draft = next(d for d in drafts_data["drafts"] if d["channel"] == "Email")
    dm_draft = next(d for d in drafts_data["drafts"] if d["channel"] == "Instagram DM")

    # Verify Email constraints
    assert email_draft["subject"] == "Potential Creator Collaboration"
    assert 60 <= email_draft["word_count"] <= 90
    assert "Alex Trainer" in email_draft["message"]

    # Verify Instagram DM constraints
    assert dm_draft["subject"] is None
    assert 15 <= dm_draft["word_count"] <= 30
    assert "Alex" in dm_draft["message"]

    # Re-running generation should skip duplicates
    rerun_res = client.post("/api/outreach/generate")
    assert rerun_res.status_code == 200
    rerun_data = rerun_res.json()
    assert rerun_data["drafts_generated"] == 0
    assert rerun_data["existing_drafts_skipped"] == 2


def test_outreach_send_simulation_and_delivery_logs(client, sample_qualified_influencer):
    """Test simulated sending, duplicate send prevention, and delivery audit logs."""
    # Generate drafts first
    client.post("/api/outreach/generate")
    drafts = client.get("/api/outreach/drafts").json()["drafts"]
    assert len(drafts) == 2
    first_draft = drafts[0]

    # Send one message
    send_res = client.post(f"/api/outreach/send/{first_draft['id']}")
    assert send_res.status_code == 200
    send_data = send_res.json()
    assert send_data["success"] is True
    assert send_data["status"] == "Sent"

    # Attempting to send again should return 409 (duplicate prevented)
    dup_send = client.post(f"/api/outreach/send/{first_draft['id']}")
    assert dup_send.status_code == 409
    assert "already been sent" in dup_send.json()["detail"]

    # Sending non-existent message returns 404
    missing_send = client.post("/api/outreach/send/999999")
    assert missing_send.status_code == 404

    # Send all remaining pending drafts
    batch_res = client.post("/api/outreach/send-pending")
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["total_processed"] == 1
    assert batch_data["sent"] == 1

    # Check delivery audit logs
    logs_res = client.get("/api/outreach/delivery-logs")
    assert logs_res.status_code == 200
    logs = logs_res.json()["logs"]
    assert len(logs) >= 2
    assert all(log["status"] == "Sent" for log in logs)


def test_csv_exports(client, sample_qualified_influencer):
    """Test streaming CSV export endpoints."""
    # Generate drafts and simulate sends to populate data
    client.post("/api/outreach/generate")
    client.post("/api/outreach/send-pending")

    # 1. Export influencers CSV
    inf_csv = client.get("/api/exports/influencers.csv")
    assert inf_csv.status_code == 200
    assert "text/csv" in inf_csv.headers["content-type"]
    assert "attachment; filename=\"influencers.csv\"" in inf_csv.headers["content-disposition"]
    assert "name,platform,profile_url" in inf_csv.text
    assert sample_qualified_influencer.name in inf_csv.text

    # 2. Export outreach messages CSV
    msg_csv = client.get("/api/exports/outreach-messages.csv")
    assert msg_csv.status_code == 200
    assert "text/csv" in msg_csv.headers["content-type"]
    assert "attachment; filename=\"outreach_messages.csv\"" in msg_csv.headers["content-disposition"]
    assert "channel,subject,message,word_count,status" in msg_csv.text
    assert "Email" in msg_csv.text

    # 3. Export delivery logs CSV
    log_csv = client.get("/api/exports/delivery-logs.csv")
    assert log_csv.status_code == 200
    assert "text/csv" in log_csv.headers["content-type"]
    assert "attachment; filename=\"delivery_logs.csv\"" in log_csv.headers["content-disposition"]
    assert "outreach_message_id,event,status" in log_csv.text
