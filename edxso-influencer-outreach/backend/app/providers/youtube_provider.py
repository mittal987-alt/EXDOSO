
from typing import Any

import httpx


YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    """Raised when a YouTube Data API request fails."""


class YouTubeProvider:
    """Client for discovering YouTube channels and collecting public statistics."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("YouTube API key is required.")

        self.api_key = api_key

    async def _get(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Send a GET request to the YouTube Data API."""

        request_params = {
            **params,
            "key": self.api_key,
        }

        timeout = httpx.Timeout(60.0, connect=15.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    f"{YOUTUBE_API_BASE}/{endpoint}",
                    params=request_params,
                )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get(
                        "message",
                        response.text,
                    )
                except ValueError:
                    error_message = response.text

                raise YouTubeAPIError(
                    f"YouTube API returned HTTP {response.status_code}: "
                    f"{error_message}"
                )

            try:
                return response.json()
            except ValueError as exc:
                raise YouTubeAPIError(
                    "YouTube API returned an invalid JSON response."
                ) from exc

        except httpx.TimeoutException as exc:
            raise YouTubeAPIError(
                f"YouTube API request timed out: {exc}"
            ) from exc

        except httpx.RequestError as exc:
            raise YouTubeAPIError(
                f"Could not connect to YouTube API: {exc}"
            ) from exc

    async def search_channels(
        self,
        query: str,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Search YouTube for channels matching a query."""

        if not query.strip():
            return []

        max_results = max(1, min(max_results, 50))

        data = await self._get(
            "search",
            {
                "part": "snippet",
                "type": "channel",
                "q": query,
                "maxResults": max_results,
                "regionCode": "IN",
                "relevanceLanguage": "en",
            },
        )

        results = []

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            channel_id = item.get("id", {}).get("channelId")

            if not channel_id:
                continue

            results.append(
                {
                    "channel_id": channel_id,
                    "title": snippet.get("title", "Not Found"),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt"),
                    "thumbnail": (
                        snippet.get("thumbnails", {})
                        .get("default", {})
                        .get("url")
                    ),
                }
            )

        return results

    async def get_channels(
        self,
        channel_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Retrieve channel details in batches of up to 50."""

        unique_ids = list(dict.fromkeys(channel_ids))
        results = []

        for start in range(0, len(unique_ids), 50):
            batch = unique_ids[start : start + 50]

            if not batch:
                continue

            data = await self._get(
                "channels",
                {
                    "part": "snippet,statistics,contentDetails",
                    "id": ",".join(batch),
                    "maxResults": 50,
                },
            )

            results.extend(data.get("items", []))

        return results

    async def get_uploads_playlist_id(
        self,
        channel_id: str,
    ) -> str | None:
        """Return the channel's uploads playlist ID, if available."""

        if not channel_id:
            return None

        data = await self._get(
            "channels",
            {
                "part": "contentDetails",
                "id": channel_id,
            },
        )

        items = data.get("items", [])

        if not items:
            return None

        content_details = items[0].get("contentDetails", {})
        related_playlists = content_details.get("relatedPlaylists", {})

        return related_playlists.get("uploads")

    async def get_recent_video_stats(
        self,
        channel_id: str,
        max_videos: int = 10,
    ) -> dict[str, Any]:
        """
        Calculate recent video statistics.

        Engagement-rate proxy:
            (likes + comments) / views * 100

        Only videos with a public view count are used in the calculation.
        This is a proxy, not a complete measure of audience engagement.
        """

        empty_result = {
            "video_count": 0,
            "average_views": None,
            "engagement_rate": None,
        }

        if not channel_id:
            return empty_result

        # Step 1: Get the channel's uploads playlist.
        try:
            uploads_playlist_id = await self.get_uploads_playlist_id(
                channel_id
            )
        except YouTubeAPIError as exc:
            # Do not silently ignore authentication, quota, or server errors.
            # A 404 for this individual channel is treated as unavailable data.
            if "HTTP 404" in str(exc):
                return empty_result
            raise

        if not uploads_playlist_id:
            return empty_result

        max_videos = max(1, min(max_videos, 50))

        # Step 2: Get recent videos from the uploads playlist.
        try:
            playlist_data = await self._get(
                "playlistItems",
                {
                    "part": "contentDetails",
                    "playlistId": uploads_playlist_id,
                    "maxResults": max_videos,
                },
            )
        except YouTubeAPIError as exc:
            if "HTTP 404" in str(exc):
                return empty_result
            raise

        video_ids = []

        for item in playlist_data.get("items", []):
            video_id = (
                item.get("contentDetails", {}).get("videoId")
            )

            if video_id:
                video_ids.append(video_id)

        if not video_ids:
            return empty_result

        # Step 3: Retrieve public statistics for the recent videos.
        video_data = await self._get(
            "videos",
            {
                "part": "statistics",
                "id": ",".join(video_ids),
                "maxResults": 50,
            },
        )

        views_list: list[int] = []
        engagement_rates: list[float] = []

        for video in video_data.get("items", []):
            statistics = video.get("statistics", {})

            # Private or unavailable view counts cannot be evaluated.
            if "viewCount" not in statistics:
                continue

            try:
                views = int(statistics["viewCount"])
            except (TypeError, ValueError):
                continue

            views_list.append(views)

            # Public like/comment counts may be missing.
            # Missing values are not treated as verified engagement data.
            if "likeCount" not in statistics:
                continue

            try:
                likes = int(statistics["likeCount"])
            except (TypeError, ValueError):
                continue

            try:
                comments = int(statistics.get("commentCount", 0))
            except (TypeError, ValueError):
                comments = 0

            if views > 0:
                rate = ((likes + comments) / views) * 100
                engagement_rates.append(rate)

        average_views = (
            round(sum(views_list) / len(views_list), 2)
            if views_list
            else None
        )

        engagement_rate = (
            round(
                sum(engagement_rates) / len(engagement_rates),
                2,
            )
            if engagement_rates
            else None
        )

        return {
            "video_count": len(video_ids),
            "average_views": average_views,
            "engagement_rate": engagement_rate,
        }

    async def discover_fitness_channels(
        self,
        target: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Discover fitness-related YouTube channels.

        Results come from the YouTube Data API. This method does not
        invent follower counts, engagement rates, or contact emails.
        """

        target = max(1, target)

        search_queries = [
            "fitness creator India",
            "workout trainer India",
            "fitness influencer India",
            "nutrition fitness India",
        ]

        discovered: dict[str, dict[str, Any]] = {}

        # Search across several relevant phrases to reduce dependence
        # on one query.
        for query in search_queries:
            remaining = target - len(discovered)

            if remaining <= 0:
                break

            search_results = await self.search_channels(
                query=query,
                max_results=min(50, max(remaining, 10)),
            )

            for result in search_results:
                channel_id = result["channel_id"]
                discovered.setdefault(channel_id, result)

                if len(discovered) >= target:
                    break

        if not discovered:
            return []

        channel_ids = list(discovered.keys())[:target]
        channel_details = await self.get_channels(channel_ids)

        records = []

        for channel in channel_details:
            snippet = channel.get("snippet", {})
            statistics = channel.get("statistics", {})
            channel_id = channel.get("id")

            if not channel_id:
                continue

            subscriber_count = statistics.get("subscriberCount")

            try:
                follower_count = (
                    int(subscriber_count)
                    if subscriber_count is not None
                    else None
                )
            except (TypeError, ValueError):
                follower_count = None

            description = snippet.get("description", "").strip()

            records.append(
                {
                    "name": snippet.get("title") or "Not Found",
                    "platform": "YouTube",
                    "profile_url": (
                        f"https://www.youtube.com/channel/{channel_id}"
                    ),
                    "follower_count": follower_count,
                    "engagement_rate": None,
                    "category": "Fitness",
                    "content_themes": description or "Not Found",
                    "contact_email": "Not Found",
                    "website": None,
                    "geography": "India",
                    "source_url": (
                        f"https://www.youtube.com/channel/{channel_id}"
                    ),
                    "qualification_status": "Pending",
                    "rejection_reasons": None,
                    "email_verified": False,
                }
            )

        return records
